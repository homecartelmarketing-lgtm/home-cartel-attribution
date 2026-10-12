"""Tests for the RFQ -> Zoho estimate wiring (Phase 2)."""

from app.database import get_connection
from app.services import rfq_service


def test_ticket_without_token_is_skipped(temp_db, zendesk_ticket):
    """Untracked inquiries are skipped, never sent to Zoho."""
    ticket = dict(zendesk_ticket)
    ticket["custom_fields"] = []  # no token anywhere
    ticket["description"] = "No session token here."

    result = rfq_service.process_rfq_ticket(ticket)

    assert result["status"] == "skipped"
    assert "token" in result["reason"].lower()


def test_local_estimate_dedup(temp_db, sample_click, zendesk_ticket, monkeypatch):
    """A token already quoted locally is skipped without any Zoho call."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE click_logs SET zoho_estimate_num = 'EST-001' WHERE session_token = ?",
            ("HC-1791780000000-11111",),
        )
        conn.commit()

    monkeypatch.setattr(
        rfq_service.zoho_service, "check_existing_estimate",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not reach Zoho")),
    )

    result = rfq_service.process_rfq_ticket(zendesk_ticket)

    assert result["status"] == "skipped"
    assert "locally" in result["reason"].lower()


def test_full_rfq_flow(temp_db, sample_click, zendesk_ticket, monkeypatch):
    """An RFQ ticket produces an estimate and advances the click log."""
    from app.services import zoho_service

    monkeypatch.setattr(
        zoho_service, "check_existing_estimate", lambda *a, **k: False
    )
    monkeypatch.setattr(
        zoho_service, "create_draft_estimate",
        lambda **kwargs: {
            "status": "success",
            "estimate": {
                "estimate_number": "EST-TEST-042",
                "estimate_id": "ESTID-1",
            },
        },
    )
    monkeypatch.setattr(
        rfq_service, "add_internal_note", lambda *a, **k: True
    )
    monkeypatch.setattr(
        rfq_service, "_requester_contact",
        lambda ticket: {"name": "Test Customer", "email": "t@example.com", "phone": "+639171234567"},
    )
    monkeypatch.setattr(
        rfq_service, "send_rfq_notification",
        lambda **kwargs: {"status": "sent"},
    )
    monkeypatch.setattr(rfq_service, "add_ticket_tags", lambda *a, **k: True)
    monkeypatch.setattr(
        rfq_service, "enrich_ticket_tracking", lambda *a, **k: True
    )

    result = rfq_service.process_rfq_ticket(zendesk_ticket)

    assert result["status"] == "processed"
    assert result["estimate_number"] == "EST-TEST-042"

    with get_connection() as conn:
        row = conn.execute(
            "SELECT zoho_estimate_num, status FROM click_logs WHERE session_token = ?",
            ("HC-1791780000000-11111",),
        ).fetchone()
    assert row["zoho_estimate_num"] == "EST-TEST-042"
    assert row["status"] == "quoted"


def test_ticket_with_created_tag_is_skipped(temp_db, zendesk_ticket):
    ticket = dict(zendesk_ticket)
    ticket["tags"] = ["rfq_detected", rfq_service.ESTIMATE_CREATED_TAG]

    result = rfq_service.process_rfq_ticket(ticket)
    assert result["status"] == "skipped"
