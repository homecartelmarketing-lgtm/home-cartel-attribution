"""
RFQ Detection & Draft Estimate Service
Ad-to-Sale Attribution System

Implements Workflow 3 of the handoff document (section 3.9.3):

    Zendesk ticket tagged 'rfq_detected'
      -> deduplication check against existing estimates (T22)
      -> resolve / create the Zoho Books contact
      -> create a pre-populated draft estimate shell
      -> write the estimate number back to the click log
      -> annotate the ticket and notify the brand's sales inbox

Triggered by the background poller, or on demand via POST /webhook/zendesk-rfq.
"""

import logging
from typing import Any, Dict, List

from app.config import (
    ZD_FIELD_SESSION_TOKEN,
    ZD_FIELD_FBCLID,
    ZD_FIELD_UTM_SOURCE,
    ZD_FIELD_UTM_CAMPAIGN,
    ZD_FIELD_UTM_CONTENT,
    ZD_FIELD_CONTACT_CHANNEL,
    ZD_FIELD_ATTRIBUTION_CONFIDENCE,
    get_brand_config,
)
from app.database import get_connection, update_click_rfq
from app.services import zoho_service
from app.services.zendesk_service import (
    search_recent_tickets,
    enrich_ticket_tracking,
    add_internal_note,
    add_ticket_tags,
    get_user_details,
    extract_token_from_email_text,
)
from app.services.email_service import send_rfq_notification

logger = logging.getLogger(__name__)

# Tag added once an estimate exists, so the poller skips the ticket next run.
ESTIMATE_CREATED_TAG = "rfq_estimate_created"

# Only consider tickets from the last 7 days to bound API usage.
RFQ_LOOKBACK_DAYS = 7

PRIMARY_BRAND = "Home Cartel"


def _resolve_ticket_tracking(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pull attribution tracking values off a Zendesk ticket.

    Tolerates both numeric field IDs (live Zendesk) and string field keys, and
    falls back to regex-extracting the token from the description for email
    channels where no custom field is populated.
    """
    raw_fields = ticket.get("custom_fields", []) or []
    cf_map: Dict[Any, Any] = {}
    for f in raw_fields:
        if not isinstance(f, dict):
            continue
        cf_map[f.get("id")] = f.get("value")
        if f.get("key"):
            cf_map[f["key"]] = f.get("value")

    def pick(*keys: Any) -> str:
        for k in keys:
            if k in cf_map and cf_map[k] not in (None, ""):
                return str(cf_map[k])
        return ""

    session_token = pick(
        ZD_FIELD_SESSION_TOKEN, str(ZD_FIELD_SESSION_TOKEN), "hc_session_token"
    )

    if not session_token:
        session_token = extract_token_from_email_text(ticket.get("description") or "") or ""

    brand = ticket.get("brand") or PRIMARY_BRAND
    if brand.lower() in ("none", "null", "n/a"):
        brand = PRIMARY_BRAND

    return {
        "session_token": session_token,
        "fbclid": pick(ZD_FIELD_FBCLID, str(ZD_FIELD_FBCLID), "hc_fbclid"),
        "utm_source": pick(ZD_FIELD_UTM_SOURCE, str(ZD_FIELD_UTM_SOURCE), "hc_utm_source"),
        "utm_campaign": pick(ZD_FIELD_UTM_CAMPAIGN, str(ZD_FIELD_UTM_CAMPAIGN), "hc_utm_campaign"),
        "utm_content": pick(ZD_FIELD_UTM_CONTENT, str(ZD_FIELD_UTM_CONTENT), "hc_utm_content"),
        "channel": pick(ZD_FIELD_CONTACT_CHANNEL, str(ZD_FIELD_CONTACT_CHANNEL), "hc_contact_channel") or "WhatsApp",
        "confidence": pick(ZD_FIELD_ATTRIBUTION_CONFIDENCE, "hc_attribution_confidence"),
        "brand": brand,
    }


def _requester_contact(ticket: Dict[str, Any]) -> Dict[str, str]:
    """Fetch the requester's name, email and phone from Zendesk."""
    info = {
        "name": ticket.get("requester_name") or "Valued Customer",
        "email": "",
        "phone": "",
    }
    requester_id = ticket.get("requester_id")
    if requester_id:
        user = get_user_details(requester_id) or {}
        info["name"] = user.get("name") or info["name"]
        info["email"] = user.get("email") or ""
        info["phone"] = user.get("phone") or ""
    return info


def _click_log_has_estimate(session_token: str) -> bool:
    """True when this session token already produced an estimate (local dedup)."""
    if not session_token:
        return False
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT zoho_estimate_num FROM click_logs
            WHERE session_token = ? AND zoho_estimate_num IS NOT NULL
              AND zoho_estimate_num != ''
            """,
            (session_token,),
        )
        return cursor.fetchone() is not None


def process_rfq_ticket(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a Zoho Books draft estimate for a single rfq_detected ticket.

    Returns a result dict with a "status" key: processed | skipped | failed
    """
    ticket_id = ticket.get("id")
    tags = ticket.get("tags") or []

    if ESTIMATE_CREATED_TAG in tags:
        return {"status": "skipped", "ticket_id": ticket_id, "reason": "Estimate already created"}

    tracking = _resolve_ticket_tracking(ticket)
    session_token = tracking["session_token"]

    if not session_token:
        return {
            "status": "skipped",
            "ticket_id": ticket_id,
            "reason": "Ticket has no session token (untracked inquiry)",
        }

    # Deduplication: local record first (cheap), then Zoho (authoritative).
    if _click_log_has_estimate(session_token):
        return {"status": "skipped", "ticket_id": ticket_id, "reason": "Estimate already recorded locally"}

    if zoho_service.check_existing_estimate(session_token, brand=tracking["brand"]):
        return {"status": "skipped", "ticket_id": ticket_id, "reason": "Estimate already exists in Zoho Books"}

    contact = _requester_contact(ticket)
    brand_cfg = get_brand_config(tracking["brand"])

    result = zoho_service.create_draft_estimate(
        customer_name=contact["name"],
        tracking_fields={
            **tracking,
            "ticket_id": ticket_id,
            "customer_email": contact["email"],
            "customer_phone": contact["phone"],
        },
        brand=tracking["brand"],
    )

    if result.get("status") != "success":
        return {
            "status": "failed",
            "ticket_id": ticket_id,
            "reason": result.get("message") or result.get("response") or "Zoho estimate creation failed",
        }

    estimate = result.get("estimate", {})
    estimate_number = estimate.get("estimate_number") or estimate.get("estimate_id") or "draft"
    estimate_id = estimate.get("estimate_id") or ""
    estimate_url = (
        f"https://books.zoho.com/app#/estimates/{estimate_id}" if estimate_id
        else "https://books.zoho.com/app#/estimates"
    )

    # Persist on the click log so the dashboard funnel advances to "Quoted".
    update_click_rfq(session_token, str(estimate_number))

    # Backfill any tracking fields the matcher had not yet populated.
    fields_to_update: Dict[Any, Any] = {}
    if tracking["fbclid"]:
        fields_to_update[ZD_FIELD_FBCLID] = tracking["fbclid"]
    if tracking["utm_source"]:
        fields_to_update[ZD_FIELD_UTM_SOURCE] = tracking["utm_source"]
    if tracking["utm_campaign"]:
        fields_to_update[ZD_FIELD_UTM_CAMPAIGN] = tracking["utm_campaign"]
    if fields_to_update:
        enrich_ticket_tracking(ticket_id, fields_to_update)

    add_internal_note(
        ticket_id,
        f"Zoho Books draft estimate {estimate_number} auto-created.\n"
        f"Session Token: {session_token}\n"
        f"Open: {estimate_url}\n"
        "Agent: add products and send the quotation.",
    )
    add_ticket_tags(ticket_id, [ESTIMATE_CREATED_TAG])

    send_rfq_notification(
        brand=tracking["brand"],
        customer_name=contact["name"],
        channel=tracking["channel"],
        ticket_id=ticket_id,
        estimate_url=estimate_url,
        session_token=session_token,
        to_email=brand_cfg.get("sales_email"),
    )

    logger.info(
        "RFQ ticket #%s -> estimate %s (token %s, brand %s)",
        ticket_id, estimate_number, session_token, tracking["brand"],
    )

    return {
        "status": "processed",
        "ticket_id": ticket_id,
        "session_token": session_token,
        "estimate_number": estimate_number,
        "brand": tracking["brand"],
    }


def process_rfq_tickets(limit: int = 25) -> List[Dict[str, Any]]:
    """
    Scan recent Zendesk tickets for the rfq_detected tag and create estimates.

    Called by the background poller. Never raises - each ticket is handled
    independently so one failure cannot stop the sweep.
    """
    results: List[Dict[str, Any]] = []
    try:
        tickets = search_recent_tickets(
            query=f"type:ticket tags:rfq_detected created>{RFQ_LOOKBACK_DAYS}days",
            limit=limit,
        )
    except Exception as e:
        logger.error("RFQ sweep could not query Zendesk: %s", e)
        return results

    for ticket in tickets:
        try:
            results.append(process_rfq_ticket(ticket))
        except Exception as e:
            logger.exception("RFQ processing failed for ticket %s: %s", ticket.get("id"), e)
            results.append(
                {"status": "failed", "ticket_id": ticket.get("id"), "reason": str(e)}
            )

    processed = sum(1 for r in results if r["status"] == "processed")
    if results:
        logger.info(
            "RFQ sweep: %d ticket(s) examined, %d estimate(s) created",
            len(results), processed,
        )

    return results
