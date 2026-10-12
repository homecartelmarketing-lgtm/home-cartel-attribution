"""
Channel-Aware Ticket Matching
Ad-to-Sale Attribution System

Matches an inbound Zendesk ticket back to the ad click that produced it
(F2 / F3). Replaces the earlier single-strategy matcher, which fell through to
"claim any ticket with a created_at" and therefore mis-attributed traffic.

Matching strategies, in descending order of confidence:

  1. Email token regex  - the session token is embedded in the email body
                          ('Ref: HC-<ts>-<rand>'). Exact, no ambiguity.
  2. Channel identity   - Messenger PSID or Viber user ID mapped to a
                          previously seen session token.
  3. Phone match        - WhatsApp requester phone mapped to a known token.
  4. Time window        - ticket created within 30 minutes of the click.
                          Lowest confidence, flagged for review.

Every match records an attribution confidence value on the Zendesk ticket so
staff can see how the link was derived.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from app.database import lookup_customer_session_token, save_customer_identity
from app.services.zendesk_service import (
    classify_channel_identity,
    extract_token_from_email_text,
    get_requester_identities,
    get_user_details,
)

# Attribution confidence values written to the Zendesk
# 'Attribution Confidence' field (see docs/zendesk_configuration_guide.md).
CONFIDENCE_HIGH = "high_channel_match"
CONFIDENCE_MEDIUM = "medium_channel_match"
CONFIDENCE_LOW = "time_window_fallback"

# A ticket created within this many minutes of a click is a plausible match.
TIME_WINDOW_MINUTES = 30


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """Parse a Zendesk ISO-8601 timestamp into an aware datetime."""
    if not ts:
        return None
    try:
        cleaned = str(ts).replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _ticket_field_value(ticket: Dict[str, Any], field_id: Any) -> str:
    """Read a custom field from a ticket, accepting int or str field IDs."""
    for f in ticket.get("custom_fields", []) or []:
        if not isinstance(f, dict):
            continue
        if f.get("id") == field_id or str(f.get("id")) == str(field_id):
            value = f.get("value")
            return str(value) if value not in (None, "") else ""
    return ""


def ticket_has_token(ticket: Dict[str, Any], session_token_field_id: int) -> bool:
    """True when the ticket already carries a session token (never overwrite)."""
    if _ticket_field_value(ticket, session_token_field_id):
        return True
    # Some Zendesk setups expose the field by key rather than numeric ID.
    for f in ticket.get("custom_fields", []) or []:
        if isinstance(f, dict) and f.get("key") == "hc_session_token" and f.get("value"):
            return True
    return False


def _match_by_email_token(ticket: Dict[str, Any]) -> Optional[str]:
    """Strategy 1: exact token embedded in the inbound email body."""
    return extract_token_from_email_text(ticket.get("description") or "")


def _match_by_channel_identity(
    ticket: Dict[str, Any],
    channel: str,
    brand: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Strategies 2 and 3: identity / phone lookup against known customers.

    Returns (session_token, identifier_to_store, confidence).
    """
    channel_lower = (channel or "").lower()
    requester_id = ticket.get("requester_id")
    if not requester_id:
        return None, None, None

    # Messenger / Viber - resolve via Zendesk channel identities (PSID etc.)
    if any(k in channel_lower for k in ("messenger", "facebook", "viber")):
        identities = get_requester_identities(requester_id)
        identifier = classify_channel_identity(identities)
        if identifier:
            token = lookup_customer_session_token(channel_lower, identifier, brand)
            if token:
                return token, identifier, CONFIDENCE_HIGH
        return None, identifier, None

    # WhatsApp / anything exposing a phone number.
    user = get_user_details(requester_id) or {}
    phone = user.get("phone") or ""
    if phone:
        token = lookup_customer_session_token(channel_lower, phone, brand)
        if token:
            return token, phone, CONFIDENCE_HIGH

    return None, phone or None, None


def _tz_now_utc() -> datetime:
    """Timezone-aware current UTC time for freshness checks."""
    return datetime.now(timezone.utc)


def _ticket_age_minutes(ticket: Dict[str, Any]) -> Optional[float]:
    """Age of a ticket in minutes, or None when it cannot be determined."""
    ticket_time = _parse_iso(ticket.get("created_at"))
    if not ticket_time:
        return None
    return abs((_tz_now_utc() - ticket_time).total_seconds()) / 60.0


def _match_by_time_window(
    ticket: Dict[str, Any], click_created_at: Optional[str]
) -> bool:
    """
    Strategy 4: the ticket must be fresh AND created near the click.

    A time-window match only makes sense for a ticket that arrived recently
    (within TIME_WINDOW_MINUTES of now) and within the same window of the ad
    click. Two stale-but-adjacent timestamps are not a match - that was the
    mis-attribution bug in the original implementation.
    """
    ticket_time = _parse_iso(ticket.get("created_at"))
    click_time = _parse_iso(click_created_at)
    if not ticket_time or not click_time:
        return False

    age_minutes = abs((_tz_now_utc() - ticket_time).total_seconds()) / 60.0
    if age_minutes > TIME_WINDOW_MINUTES:
        return False

    delta_minutes = abs((ticket_time - click_time).total_seconds()) / 60.0
    return delta_minutes <= TIME_WINDOW_MINUTES


def match_ticket_to_click(
    ticket: Dict[str, Any],
    click: Dict[str, Any],
    session_token_field_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Attempt to match one ticket to one pending click.

    Returns a match descriptor when the pair should be linked:

        {
          "session_token": str,
          "confidence": str,
          "identifier": str | None,   # persist for repeat-customer matching
        }

    Returns None when no strategy applies. The caller must still respect the
    "never overwrite an existing token" rule via ticket_has_token().
    """
    channel = click.get("channel") or "WhatsApp"
    brand = click.get("brand") or "Home Cartel"
    brand_channel = channel.lower()

    # Strategy 1 - exact token in the email body. Strongest signal; use the
    # token the customer actually sent rather than the click's own.
    email_token = _match_by_email_token(ticket)
    if email_token:
        return {
            "session_token": email_token,
            "confidence": CONFIDENCE_HIGH,
            "identifier": None,
        }

    # Strategies 2 and 3 - repeat customer already seen on this channel.
    token, identifier, confidence = _match_by_channel_identity(
        ticket, brand_channel, brand
    )
    if token:
        return {
            "session_token": token,
            "confidence": confidence or CONFIDENCE_HIGH,
            "identifier": identifier,
        }

    # Strategy 4 - time-window fallback, only when the ticket is genuinely
    # recent relative to the click.
    if _match_by_time_window(ticket, click.get("created_at")):
        return {
            "session_token": click.get("session_token"),
            "confidence": CONFIDENCE_LOW,
            "identifier": identifier,
        }

    return None


def record_match_identity(
    match: Dict[str, Any], channel: str, brand: str
) -> None:
    """
    Persist a channel identifier -> session token mapping so the next contact
    from the same person resolves immediately (F10, T28).
    """
    identifier = match.get("identifier")
    session_token = match.get("session_token")
    if not identifier or not session_token:
        return
    try:
        save_customer_identity(channel.lower(), identifier, session_token, brand)
    except Exception as e:
        print(f"[-] Could not store customer identity for {channel}: {e}")
