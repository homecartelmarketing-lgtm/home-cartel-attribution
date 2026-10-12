"""
Email Notification Service
Ad-to-Sale Attribution System

Stdlib-only SMTP sender used for RFQ notifications (Workflow 3), the daily
attribution audit email (Workflow 5) and Part 3 ad-performance alerts.

When SMTP_HOST is not configured the service degrades to a no-op that logs
the message instead of raising, so the attribution pipeline never breaks in a
development environment.
"""

import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Any, Dict, List, Optional

from app.config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_USE_TLS,
    SMTP_FROM,
    ALERT_RECIPIENTS,
)

# One retry protects against transient SMTP failures without hanging a
# background job for long.
MAX_ATTEMPTS = 2


class EmailError(Exception):
    """Raised when an email could not be delivered."""


def is_configured() -> bool:
    """True when outbound email can actually be sent."""
    return bool(SMTP_HOST and SMTP_FROM)


def _build_message(
    subject: str,
    body_text: str,
    recipients: List[str],
    body_html: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Home Cartel Attribution", SMTP_FROM))
    msg["To"] = ", ".join(recipients)
    if reply_to:
        msg["Reply-To"] = reply_to

    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))

    return msg


def send_email(
    subject: str,
    body_text: str,
    recipients: Optional[List[str]] = None,
    body_html: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a plain text (and optionally HTML) email.

    Returns {"status": "sent"} on success, {"status": "skipped"} when SMTP is
    unconfigured, or {"status": "failed", ...} with the error detail.
    """
    to_addresses = [r for r in (recipients or ALERT_RECIPIENTS) if r]
    if not to_addresses:
        return {"status": "skipped", "reason": "No recipients configured"}

    if not is_configured():
        print(
            f"[email] SMTP not configured. Would have sent '{subject}' "
            f"to {', '.join(to_addresses)}"
        )
        return {"status": "skipped", "reason": "SMTP not configured"}

    msg = _build_message(subject, body_text, to_addresses, body_html, reply_to)
    context = ssl.create_default_context()

    last_error: Optional[str] = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
                server.ehlo()
                if SMTP_USE_TLS:
                    server.starttls(context=context)
                    server.ehlo()
                if SMTP_USER and SMTP_PASSWORD:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, to_addresses, msg.as_string())

            print(f"[email] Sent '{subject}' to {', '.join(to_addresses)}")
            return {"status": "sent", "recipients": to_addresses}
        except Exception as e:
            last_error = str(e)
            print(f"[-] Email send failed (attempt {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt < MAX_ATTEMPTS:
                time.sleep(2)

    return {"status": "failed", "error": last_error}


def send_rfq_notification(
    brand: str,
    customer_name: str,
    channel: str,
    ticket_id: Any,
    estimate_url: str,
    session_token: str,
    to_email: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Notify the brand's sales team that a draft estimate was auto-created
    (Workflow 3, Step 6 of section 3.9.3).
    """
    subject = f"New RFQ — {brand} — {customer_name} — {channel}"

    body_text = (
        f"New RFQ detected for {brand}.\n\n"
        f"Customer Name:  {customer_name}\n"
        f"Channel:        {channel}\n"
        f"Zendesk Ticket: #{ticket_id}\n"
        f"Zoho Estimate:  {estimate_url}\n"
        f"Session Token:  {session_token}\n\n"
        "A draft estimate shell has been created in Zoho Books with all tracking "
        "fields populated. Add the products and send the quotation.\n"
    )

    body_html = f"""
    <html><body style="font-family:Arial,Helvetica,sans-serif;color:#222;">
      <h2 style="margin-bottom:4px;">New RFQ — {brand}</h2>
      <p style="color:#666;margin-top:0;">Auto-created from Zendesk inquiry #{ticket_id}</p>
      <table cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
        <tr><td><strong>Customer</strong></td><td>{customer_name}</td></tr>
        <tr><td><strong>Channel</strong></td><td>{channel}</td></tr>
        <tr><td><strong>Zendesk Ticket</strong></td><td>#{ticket_id}</td></tr>
        <tr><td><strong>Session Token</strong></td><td><code>{session_token}</code></td></tr>
      </table>
      <p><a href="{estimate_url}"
            style="background:#b38b4d;color:#fff;padding:10px 18px;text-decoration:none;
                   border-radius:4px;display:inline-block;">Open Draft Estimate in Zoho Books</a></p>
      <p style="color:#666;font-size:12px;">
        Add the products and send the quotation. Do not edit the tracking custom fields.</p>
    </body></html>
    """

    return send_email(
        subject=subject,
        body_text=body_text,
        recipients=[to_email] if to_email else None,
        body_html=body_html,
    )
