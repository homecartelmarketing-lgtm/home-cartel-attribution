"""Tests for channel-aware ticket matching (Phase 3)."""

from datetime import datetime, timedelta, timezone

from app.services import ticket_matcher


def _iso(minutes_ago=0):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()


def test_email_token_regex_wins(sample_click, zendesk_ticket):
    """A token embedded in the email body outranks every other signal."""
    ticket = dict(zendesk_ticket)
    ticket["description"] = "Hi, please quote. Ref: HC-1791780000000-99999. Thanks."

    match = ticket_matcher.match_ticket_to_click(ticket, sample_click, 17953452223503)

    assert match is not None
    assert match["session_token"] == "HC-1791780000000-99999"
    assert match["confidence"] == ticket_matcher.CONFIDENCE_HIGH


def test_whatsapp_repeat_customer_resolves(temp_db, sample_click, zendesk_ticket, monkeypatch):
    """A known phone number maps back to the stored session token."""
    from app.database import save_customer_identity

    save_customer_identity(
        "whatsapp", "+639171234567", "HC-1791780000000-11111", "Home Cartel"
    )

    from app.services import zendesk_service

    # ticket_matcher binds the function at import time, so the patch must
    # target the reference it actually calls, not the module it came from.
    monkeypatch.setattr(
        ticket_matcher, "get_user_details",
        lambda user_id: {"phone": "+639171234567", "name": "Test Customer"},
    )

    ticket = dict(zendesk_ticket)
    ticket["description"] = "Hello, I want to order again."
    ticket["created_at"] = _iso(minutes_ago=300)  # outside the time window

    match = ticket_matcher.match_ticket_to_click(ticket, sample_click, 17953452223503)

    assert match is not None
    assert match["session_token"] == "HC-1791780000000-11111"
    assert match["confidence"] == ticket_matcher.CONFIDENCE_HIGH


def test_time_window_fallback(sample_click, zendesk_ticket):
    """A genuinely recent ticket with no identity falls back to time window."""
    ticket = dict(zendesk_ticket)
    ticket["description"] = "Hello, I saw your ad."
    ticket["requester_id"] = None  # no identity resolution possible

    click = dict(sample_click)
    click["created_at"] = _iso(minutes_ago=5)
    ticket["created_at"] = _iso(minutes_ago=2)

    match = ticket_matcher.match_ticket_to_click(ticket, click, 17953452223503)

    assert match is not None
    assert match["session_token"] == click["session_token"]
    assert match["confidence"] == ticket_matcher.CONFIDENCE_LOW


def test_stale_ticket_does_not_match(sample_click, zendesk_ticket):
    """The old behaviour - claiming any ticket with a created_at - must not match."""
    ticket = dict(zendesk_ticket)
    ticket["description"] = "Hello from last week."
    ticket["requester_id"] = None

    click = dict(sample_click)
    click["created_at"] = _iso(minutes_ago=10080)  # 7 days ago
    ticket["created_at"] = _iso(minutes_ago=10070)  # 10 minutes later, still stale

    match = ticket_matcher.match_ticket_to_click(ticket, click, 17953452223503)
    assert match is None


def test_ticket_with_existing_token_is_detected(zendesk_ticket):
    assert ticket_matcher.ticket_has_token(zendesk_ticket, 17953452223503)

    untracked = dict(zendesk_ticket)
    untracked["custom_fields"] = [{"id": 17953452223503, "value": ""}]
    assert not ticket_matcher.ticket_has_token(untracked, 17953452223503)


def test_record_match_identity_persists(temp_db):
    ticket_matcher.record_match_identity(
        {"session_token": "HC-1791780000000-11111", "identifier": "+639171234567"},
        "WhatsApp",
        "Home Cartel",
    )

    from app.database import lookup_customer_session_token

    assert (
        lookup_customer_session_token("whatsapp", "+639171234567", "Home Cartel")
        == "HC-1791780000000-11111"
    )
