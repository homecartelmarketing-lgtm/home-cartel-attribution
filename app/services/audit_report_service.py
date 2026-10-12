"""
Daily Attribution Audit Report Service
Ad-to-Sale Attribution System

Implements Workflow 5 of the handoff document (section 3.9.5): every morning,
sweep for tickets still missing tracking data after 24 hours and email a
summary with the full funnel counts.

Also backs the on-demand GET /audit endpoint.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from app.config import APP_TIMEZONE, ALERT_RECIPIENTS
from app.database import get_connection
from app.services.email_service import send_email

logger = logging.getLogger(__name__)

# Tracking gap above this percentage flips the report to ATTENTION_NEEDED.
TRACKING_GAP_THRESHOLD_PCT = 20.0


def _local_now() -> datetime:
    """Current time in the application timezone (PHT)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(APP_TIMEZONE))
    except Exception:
        return datetime.now()


def compute_daily_audit() -> Dict[str, Any]:
    """
    Computes 24h health metrics across all attribution stages (F11).
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Total ad clicks in 24 hours
        cursor.execute(
            "SELECT COUNT(*) FROM click_logs WHERE created_at >= datetime('now', '-24 hours')"
        )
        total_clicks = cursor.fetchone()[0] or 0

        # 2. Inquiries linked to Zendesk in 24 hours
        cursor.execute(
            "SELECT COUNT(*) FROM click_logs "
            "WHERE zendesk_ticket_id IS NOT NULL AND created_at >= datetime('now', '-24 hours')"
        )
        inquiries = cursor.fetchone()[0] or 0

        # 3. RFQ detected or estimate created
        cursor.execute(
            "SELECT COUNT(*) FROM click_logs "
            "WHERE (rfq_detected = 1 OR (zoho_estimate_num IS NOT NULL AND zoho_estimate_num != '')) "
            "AND created_at >= datetime('now', '-24 hours')"
        )
        rfqs = cursor.fetchone()[0] or 0

        # 4. Paid CAPI conversions in 24 hours
        cursor.execute(
            "SELECT COUNT(*), COALESCE(SUM(total), 0) FROM conversions_audit "
            "WHERE created_at >= datetime('now', '-24 hours')"
        )
        row = cursor.fetchone()
        conversions = row[0] or 0
        revenue = row[1] or 0.0

        # 5. Breakdown of CAPI outcomes, so failures surface in the email.
        cursor.execute(
            "SELECT status, COUNT(*) FROM conversions_audit "
            "WHERE created_at >= datetime('now', '-24 hours') GROUP BY status"
        )
        status_breakdown = {r[0] or "unknown": r[1] for r in cursor.fetchall()}

    gap_rate = 0.0
    if total_clicks > 0:
        missing_count = max(0, total_clicks - inquiries)
        gap_rate = round((missing_count / total_clicks) * 100, 1)

    status = "HEALTHY" if gap_rate <= TRACKING_GAP_THRESHOLD_PCT else "ATTENTION_NEEDED"

    return {
        "date": _local_now().strftime("%Y-%m-%d"),
        "total_ad_clicks_24h": total_clicks,
        "total_tickets_linked_24h": inquiries,
        "rfq_detected_count": rfqs,
        "capi_events_sent_24h": conversions,
        "attributed_revenue_php_24h": revenue,
        "tracking_gap_percentage": gap_rate,
        "status": status,
        "conversion_status_breakdown": status_breakdown,
        "audit_timestamp": _local_now().isoformat(),
    }


def find_unmatched_tickets(limit: int = 25) -> List[Dict[str, Any]]:
    """
    Return click logs older than 24h that never became a Zendesk ticket.

    This is the Workflow 5 "error sweep": unattributed clicks are the signal
    that a redirect page, matching rule, or channel routing is broken.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, session_token, channel, brand, created_at
            FROM click_logs
            WHERE (zendesk_ticket_id IS NULL OR zendesk_ticket_id = '')
              AND created_at < datetime('now', '-24 hours')
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(r) for r in cursor.fetchall()]


def render_audit_email(report: Dict[str, Any], unmatched: List[Dict[str, Any]]) -> Dict[str, str]:
    """Render the daily audit report as plain text and HTML."""
    date = report.get("date", "")
    status = report.get("status", "UNKNOWN")
    colour = "#2e7d32" if status == "HEALTHY" else "#c62828"

    rows = [
        ("Ad clicks (24h)", report.get("total_ad_clicks_24h", 0)),
        ("Zendesk tickets linked (24h)", report.get("total_tickets_linked_24h", 0)),
        ("RFQs detected / quoted (24h)", report.get("rfq_detected_count", 0)),
        ("CAPI conversions sent (24h)", report.get("capi_events_sent_24h", 0)),
        (
            "Attributed revenue (24h)",
            f"PHP {float(report.get('attributed_revenue_php_24h', 0)):,.2f}",
        ),
        ("Tracking gap", f"{report.get('tracking_gap_percentage', 0)}%"),
    ]

    text_lines = [
        f"Daily Attribution Audit - {date}",
        f"Status: {status}",
        "",
    ]
    text_lines += [f"{label}: {value}" for label, value in rows]

    html_rows = "".join(
        f"<tr><td style='padding:6px 12px;'>{label}</td>"
        f"<td style='padding:6px 12px;text-align:right;'><strong>{value}</strong></td></tr>"
        for label, value in rows
    )

    if unmatched:
        text_lines += ["", f"Unattributed clicks (>24h): {len(unmatched)}"]
        for c in unmatched[:10]:
            text_lines.append(
                f"  - {c['session_token']} | {c.get('channel')} | "
                f"{c.get('brand')} | {c.get('created_at')}"
            )

        html_unmatched = "".join(
            f"<tr><td style='padding:4px 10px;'><code>{c['session_token']}</code></td>"
            f"<td style='padding:4px 10px;'>{c.get('channel')}</td>"
            f"<td style='padding:4px 10px;'>{c.get('brand')}</td>"
            f"<td style='padding:4px 10px;'>{c.get('created_at')}</td></tr>"
            for c in unmatched[:10]
        )
        unmatched_html = f"""
        <h3 style="color:#c62828;">Unattributed clicks older than 24h: {len(unmatched)}</h3>
        <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
          <tr style="background:#f5f5f5;">
            <th align="left" style="padding:6px 10px;">Session Token</th>
            <th align="left" style="padding:6px 10px;">Channel</th>
            <th align="left" style="padding:6px 10px;">Brand</th>
            <th align="left" style="padding:6px 10px;">Created</th>
          </tr>
          {html_unmatched}
        </table>
        <p style="font-size:12px;color:#666;">
          These clicks never became a Zendesk ticket. Check the redirect pages and
          the matching rules.</p>
        """
    else:
        unmatched_html = "<p style='color:#2e7d32;'>No unattributed clicks older than 24h.</p>"

    html = f"""
    <html><body style="font-family:Arial,Helvetica,sans-serif;color:#222;">
      <h2 style="margin-bottom:2px;">Daily Attribution Audit &mdash; {date}</h2>
      <p style="margin-top:0;color:{colour};"><strong>Status: {status}</strong></p>
      <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
        {html_rows}
      </table>
      {unmatched_html}
    </body></html>
    """

    return {
        "text": "\n".join(text_lines),
        "html": html,
        "subject": f"[AUDIT] Ad-to-Sale Attribution - {date} - {status}",
    }


def send_daily_audit_email(recipients: List[str] = None) -> Dict[str, Any]:
    """Compute the audit report and email it. Safe to call from the scheduler."""
    report = compute_daily_audit()
    unmatched = find_unmatched_tickets()
    rendered = render_audit_email(report, unmatched)

    result = send_email(
        subject=rendered["subject"],
        body_text=rendered["text"],
        body_html=rendered["html"],
        recipients=recipients or ALERT_RECIPIENTS,
    )

    logger.info("Daily audit email result: %s", result.get("status"))
    return {**report, "email_status": result.get("status")}
