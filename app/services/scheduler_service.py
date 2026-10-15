"""
Background Poller & Audit Scheduler Service
Ad-to-Sale Attribution System

Single daemon thread running every POLL_INTERVAL_SECONDS that performs, in
order, each isolated so one failure cannot stop the others:

  1. match_pending_clicks()   - link ad clicks to Zendesk tickets (F2 / F3)
  2. process_rfq_tickets()    - create Zoho estimates for RFQs  (Workflow 3)
  3. run_scheduled_audit()    - email the daily audit report    (Workflow 5)
  4. run_alert_checks()       - evaluate Part 3 ad alerts

Each stage catches its own exceptions; a crashed stage is logged and the loop
continues on the next interval.
"""

import logging
import re
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.config import APP_TIMEZONE, DAILY_AUDIT_TIME, DAILY_DIGEST_TIME

from app.database import (
    get_connection,
    get_pending_clicks,
    update_click_zendesk,
    save_customer_identity,
    update_click_rfq,
)
from app.services.zendesk_service import (
    search_recent_tickets,
    enrich_ticket_tracking,
    fetch_recent_tickets,
    get_user_details,
    get_ticket_comments,
)
from app.services import ticket_matcher
from app.services import rfq_service
from app.services import audit_report_service
from app.services import alert_engine
from app.services import zoho_creator_service
from app.services import meta_capi_service
from app.services.zoho_creator_service import normalize_phone
from app.config import (
    ZD_FIELD_SESSION_TOKEN,
    ZD_FIELD_FBCLID,
    ZD_FIELD_UTM_CAMPAIGN,
    ZD_FIELD_UTM_SOURCE,
    ZD_FIELD_CONTACT_CHANNEL,
    ZD_FIELD_ATTRIBUTION_CONFIDENCE,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scheduler")

_daemon_started = False
_daemon_lock = threading.Lock()


def match_pending_clicks():
    """
    Looks for recent open Zendesk tickets and correlates them with pending ad
    clicks (F2 / F3).

    Delegates the actual matching decision to ticket_matcher, which scores each
    ticket/click pair by confidence. A ticket that already carries a session
    token is never overwritten.
    """
    pending = get_pending_clicks(minutes=60)
    if not pending:
        return

    recent_tickets = search_recent_tickets(query="type:ticket status:open created>1hour", limit=50)
    if not recent_tickets:
        return

    for click in pending:
        session_token = click.get("session_token")
        channel = click.get("channel") or "WhatsApp"
        brand = click.get("brand") or "Home Cartel"

        for ticket in recent_tickets:
            ticket_id = ticket.get("id")

            # Never overwrite a token that is already populated (T10 / Rule 3).
            if ticket_matcher.ticket_has_token(ticket, ZD_FIELD_SESSION_TOKEN):
                continue

            match = ticket_matcher.match_ticket_to_click(
                ticket, click, ZD_FIELD_SESSION_TOKEN
            )
            if not match or not match.get("session_token"):
                continue

            matched_token = match["session_token"]
            confidence = match.get("confidence") or ticket_matcher.CONFIDENCE_LOW

            # Enrich the Zendesk ticket with the attribution custom fields.
            fields_to_update: Dict[Any, Any] = {
                ZD_FIELD_SESSION_TOKEN: matched_token,
                ZD_FIELD_CONTACT_CHANNEL: channel,
            }
            if click.get("fbclid"):
                fields_to_update[ZD_FIELD_FBCLID] = click["fbclid"]
            if click.get("utm_campaign"):
                fields_to_update[ZD_FIELD_UTM_CAMPAIGN] = click["utm_campaign"]
            if click.get("utm_source"):
                fields_to_update[ZD_FIELD_UTM_SOURCE] = click["utm_source"]
            # Optional field - only sent when configured in the environment.
            if ZD_FIELD_ATTRIBUTION_CONFIDENCE:
                fields_to_update[ZD_FIELD_ATTRIBUTION_CONFIDENCE] = confidence

            enrich_ticket_tracking(ticket_id, fields_to_update)

            # Only advance the originating click log when the ticket resolved
            # to that same click; a stronger match supersedes it.
            if matched_token == session_token:
                update_click_zendesk(session_token, ticket_id)

            # Store the identifier so a repeat contact resolves immediately.
            ticket_matcher.record_match_identity(match, channel, brand)

            logger.info(
                "Matched ticket #%s to token %s via %s (brand %s)",
                ticket_id, matched_token, confidence, brand,
            )
            break


def sync_zendesk_attributed_tickets(limit: int = 50) -> Dict[str, Any]:
    """
    Fetch recent Zendesk tickets that carry attribution tracking fields (session_token or fbclid).
    Upserts them into click_logs, extracts requester phone numbers and comments,
    and indexes any discovered estimate numbers (QUO-xxxxx, EST-xxxxx) or 10-digit
    PH phone numbers into customer_identities and click_logs.
    """
    tickets = fetch_recent_tickets(per_page=limit)
    if not tickets:
        return {"status": "skipped", "reason": "No tickets returned"}

    synced_clicks = 0
    synced_identities = 0
    synced_estimates = 0

    for ticket in tickets:
        ticket_id = ticket.get("id")
        custom_map = {f.get("id"): f.get("value") for f in ticket.get("custom_fields", []) if isinstance(f, dict)}

        session_token = str(custom_map.get(ZD_FIELD_SESSION_TOKEN) or "").strip()
        fbclid = str(custom_map.get(ZD_FIELD_FBCLID) or "").strip()
        utm_campaign = str(custom_map.get(ZD_FIELD_UTM_CAMPAIGN) or "").strip()
        utm_source = str(custom_map.get(ZD_FIELD_UTM_SOURCE) or "").strip()
        contact_channel = str(
            custom_map.get(ZD_FIELD_CONTACT_CHANNEL) or ticket.get("via", {}).get("channel") or "WhatsApp"
        ).strip()

        # Skip if neither session_token nor fbclid is present
        if not session_token and not fbclid:
            continue

        # If session_token is missing but fbclid is present, synthesize a ticket token
        if not session_token:
            session_token = f"HC-ZD-{ticket_id}"

        # a & b. Upsert into click_logs
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO click_logs (
                        session_token, fbclid, utm_campaign, utm_source, channel, brand, status, zendesk_ticket_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, 'Home Cartel', 'inquired', ?, ?)
                    ON CONFLICT(session_token) DO UPDATE SET
                        fbclid = CASE WHEN excluded.fbclid != '' THEN excluded.fbclid ELSE click_logs.fbclid END,
                        utm_campaign = CASE WHEN excluded.utm_campaign != '' THEN excluded.utm_campaign ELSE click_logs.utm_campaign END,
                        utm_source = CASE WHEN excluded.utm_source != '' THEN excluded.utm_source ELSE click_logs.utm_source END,
                        zendesk_ticket_id = COALESCE(excluded.zendesk_ticket_id, click_logs.zendesk_ticket_id),
                        channel = CASE WHEN click_logs.channel = '' THEN excluded.channel ELSE click_logs.channel END
                """, (
                    session_token,
                    fbclid,
                    utm_campaign,
                    utm_source,
                    contact_channel,
                    ticket_id,
                    ticket.get("created_at")
                ))
                conn.commit()
                synced_clicks += 1
        except Exception as e:
            logger.error(f"[-] Error upserting click log for ticket #{ticket_id}: {e}")

        # c. Extract requester's phone number
        requester_id = ticket.get("requester_id")
        if requester_id:
            try:
                user = get_user_details(requester_id)
                raw_uphone = user.get("phone") or ""
                if raw_uphone:
                    norm_up = normalize_phone(raw_uphone)
                    if norm_up and len(norm_up) == 10 and norm_up.startswith("9"):
                        save_customer_identity("phone", norm_up, session_token, "Home Cartel")
                        synced_identities += 1
                        logger.info(f"[+] Mapped requester phone {norm_up} -> session {session_token}")
            except Exception as e:
                logger.error(f"[-] Error checking requester details #{requester_id}: {e}")

        # d. Scan ticket comments & description for Estimate numbers & PH phone numbers
        try:
            comments = get_ticket_comments(ticket_id, limit=30)
            text_blocks = [c.get("body") or "" for c in comments]
            if ticket.get("description"):
                text_blocks.append(ticket["description"])
            if ticket.get("subject"):
                text_blocks.append(ticket["subject"])
            full_text = " ".join(text_blocks)

            # 1) Scan for Estimate Numbers: \b(?:QUO|EST)-\d+\b
            est_matches = re.findall(r"\b(?:QUO|EST)-\d+\b", full_text, flags=re.IGNORECASE)
            for est in set(est_matches):
                est_upper = est.upper()
                update_click_rfq(session_token, est_upper)
                synced_estimates += 1
                logger.info(f"[★] Extracted Estimate {est_upper} from Ticket #{ticket_id} -> {session_token}")

            # 2) Scan for PH mobile numbers in comments
            phone_matches = re.findall(r"(?:\+?63[-\s]?|0)?9\d{2}[-\s]?\d{3}[-\s]?\d{4}\b", full_text)
            for raw_p in set(phone_matches):
                norm_p = normalize_phone(raw_p)
                if norm_p and len(norm_p) == 10 and norm_p.startswith("9"):
                    save_customer_identity("phone", norm_p, session_token, "Home Cartel")
                    synced_identities += 1
                    logger.info(f"[★] Extracted Phone {norm_p} from Ticket #{ticket_id} comments -> {session_token}")

        except Exception as e:
            logger.error(f"[-] Error parsing comments for ticket #{ticket_id}: {e}")

    logger.info(
        f"[+] Zendesk Attributed Ticket Sync completed: {synced_clicks} clicks, {synced_identities} identities, {synced_estimates} estimates."
    )
    return {
        "status": "ok",
        "synced_clicks": synced_clicks,
        "synced_identities": synced_identities,
        "synced_estimates": synced_estimates
    }


def _safe_run(stage_name: str, func, *args, **kwargs):
    """Run one pipeline stage, logging rather than propagating any failure."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.exception("Scheduler stage '%s' failed: %s", stage_name, e)
        return None


def _poller_loop(interval_seconds: int = 300):
    """
    Main scheduler loop.

    Runs every stage on each tick, then separately handles the time-of-day
    triggers (daily audit email, Part 3 alert schedules) which fire once per
    configured wall-clock time instead of every tick.
    """
    last_audit_date: Dict[str, str] = {}
    last_digest_date: Dict[str, str] = {}
    last_alert_run: Dict[str, str] = {}

    while True:
        _safe_run("match_pending_clicks", match_pending_clicks)
        _safe_run("process_rfq_tickets", rfq_service.process_rfq_tickets)
        _safe_run("sync_zendesk_attributed_tickets", sync_zendesk_attributed_tickets)
        _safe_run("sync_zoho_creator", zoho_creator_service.run_full_zoho_creator_sync)
        _safe_run("retry_pending_capi", meta_capi_service.retry_pending_capi_conversions)

        # Daily audit email - fires once per day at DAILY_AUDIT_TIME.
        try:
            now_local = datetime.now(_tz())
            today = now_local.strftime("%Y-%m-%d")
            if (
                now_local.strftime("%H:%M") >= DAILY_AUDIT_TIME
                and last_audit_date.get("date") != today
            ):
                last_audit_date["date"] = today
                _safe_run("run_daily_audit_and_email", audit_report_service.send_daily_audit_email)
        except Exception as e:
            logger.exception("Daily audit scheduling failed: %s", e)

        # Daily ad-health digest (PDF 2.6.6) - once per day at DAILY_DIGEST_TIME.
        try:
            now_local = datetime.now(_tz())
            today = now_local.strftime("%Y-%m-%d")
            if (
                now_local.strftime("%H:%M") >= DAILY_DIGEST_TIME
                and last_digest_date.get("date") != today
            ):
                last_digest_date["date"] = today
                _safe_run("send_daily_ad_health_digest", alert_engine.send_daily_ad_health_digest)
        except Exception as e:
            logger.exception("Daily digest scheduling failed: %s", e)

        time.sleep(interval_seconds)


def _tz():
    """Return the configured application timezone."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(APP_TIMEZONE)
    except Exception:
        return None


def start_poller_daemon(interval_seconds: int = 300):
    """
    Start the background scheduler thread exactly once.

    Thread-safe so repeated calls (tests, uvicorn reload) cannot spawn
    duplicate daemons.
    """
    global _daemon_started
    with _daemon_lock:
        if _daemon_started:
            return
        _daemon_started = True
        t = threading.Thread(target=_poller_loop, args=(interval_seconds,), daemon=True)
        t.start()
        print(f"[+] Background scheduler daemon started (runs every {interval_seconds}s).")


def is_daemon_running() -> bool:
    """True when the background scheduler is active. Used by tests."""
    return _daemon_started


def reset_daemon_flag():
    """Clear the started flag so a fresh daemon can be launched (tests only)."""
    global _daemon_started
    with _daemon_lock:
        _daemon_started = False


# Re-exported for backwards compatibility with app/server.py, which imports the
# audit entrypoint from this module. The implementation lives in
# audit_report_service.
def run_daily_attribution_audit() -> Dict[str, Any]:
    """Compute the 24-hour attribution health report (F11)."""
    return audit_report_service.compute_daily_audit()

