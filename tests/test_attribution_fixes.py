import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from app.services import zoho_creator_service
from app.database import (
    get_connection,
    save_click_log,
    save_customer_identity,
    lookup_customer_by_phone,
    migrate_normalize_identities,
    init_db
)
from app.services.meta_capi_service import send_purchase_event

def test_hardened_normalize_phone():
    # Test all variations of Philippine phone numbers
    assert zoho_creator_service.normalize_phone("+63-09178389270") == "9178389270"
    assert zoho_creator_service.normalize_phone("+63-+639052126300") == "9052126300"
    assert zoho_creator_service.normalize_phone("09175563077") == "9175563077"
    assert zoho_creator_service.normalize_phone("+639955805699") == "9955805699"
    assert zoho_creator_service.normalize_phone("+63-908-413-6502") == "9084136502"
    assert zoho_creator_service.normalize_phone("0917-504-3200") == "9175043200"
    assert zoho_creator_service.normalize_phone("9175043200") == "9175043200"
    assert zoho_creator_service.normalize_phone("") == ""
    assert zoho_creator_service.normalize_phone(None) == ""

def test_migrate_normalize_identities_safeguards(temp_db):
    # Insert dirty records
    with get_connection() as conn:
        cursor = conn.cursor()
        # Phone number with +63
        cursor.execute(
            "INSERT INTO customer_identities (channel, identifier, session_token, brand) VALUES (?, ?, ?, ?)",
            ("whatsapp", "+639171234567", "HC-WA-1", "Home Cartel")
        )
        # Messenger PSID containing numbers but also letters/symbols (should remain untouched)
        cursor.execute(
            "INSERT INTO customer_identities (channel, identifier, session_token, brand) VALUES (?, ?, ?, ?)",
            ("messenger", "psid_9876543210_abc", "HC-MS-1", "Home Cartel")
        )
        # Email address (should remain untouched)
        cursor.execute(
            "INSERT INTO customer_identities (channel, identifier, session_token, brand) VALUES (?, ?, ?, ?)",
            ("email", "buyer9171234567@gmail.com", "HC-EM-1", "Home Cartel")
        )
        conn.commit()

    migrate_normalize_identities()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT channel, identifier, session_token FROM customer_identities")
        rows = {r["channel"]: r["identifier"] for r in cursor.fetchall()}

    assert rows["whatsapp"] == "9171234567"  # Normalized to 10 digits
    assert rows["messenger"] == "psid_9876543210_abc"  # Untouched
    assert rows["email"] == "buyer9171234567@gmail.com"  # Untouched

def test_channel_agnostic_phone_matching(temp_db):
    token = "HC-SESSION-CROSS-CHANNEL"
    save_click_log({
        "session_token": token,
        "fbclid": "fbclid_cross_chan_1",
        "channel": "WhatsApp",
        "brand": "Home Cartel"
    })
    # Saved under 'viber' or 'whatsapp'
    save_customer_identity("viber", "9179998888", token, "Home Cartel")

    # Match by phone using lookup_customer_by_phone
    matched_token = lookup_customer_by_phone("+63-09179998888")
    assert matched_token == token

    # Match via find_matching_session
    match = zoho_creator_service.find_matching_session(phone="+63-+639179998888")
    assert match is not None
    assert match["session_token"] == token

def test_meta_capi_blank_token_vs_populated(temp_db, monkeypatch):
    monkeypatch.setattr("app.services.meta_capi_service.META_DATASET_ID", "236624173955711")
    monkeypatch.setattr("app.services.meta_capi_service.META_TEST_EVENT_CODE", "TEST20793")

    # 1. Blank META_ACCESS_TOKEN: should record as attributed in conversions_audit with status failed_missing_credentials
    res_blank = send_purchase_event(
        salesorder_id="SO-TEST-CAPI-BLANK",
        total_amount=5000.0,
        email="test@homecartel.ph",
        phone="09171234567",
        fbclid="fbclid_test_blank",
        brand="Home Cartel",
        dataset_id="236624173955711",
        access_token="",
        session_token="HC-TOKEN-BLANK"
    )
    assert res_blank["status"] == "error"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conversions_audit WHERE salesorder_id = 'SO-TEST-CAPI-BLANK'")
        row = cursor.fetchone()
        assert row is not None
        assert row["session_token"] == "HC-TOKEN-BLANK"
        assert row["fbclid"] == "fbclid_test_blank"
        assert row["status"] == "failed_missing_credentials"

    # 2. Populated META_ACCESS_TOKEN with mock: should dispatch test_event_code="TEST20793"
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"events_received": 1}'
        mock_resp.json.return_value = {"events_received": 1}
        mock_post.return_value = mock_resp

        res_live = send_purchase_event(
            salesorder_id="SO-TEST-CAPI-LIVE",
            total_amount=15000.0,
            email="live@homecartel.ph",
            phone="09179998888",
            fbclid="fbclid_test_live",
            brand="Home Cartel",
            dataset_id="236624173955711",
            access_token="EAAB_TEST_TOKEN",
            session_token="HC-TOKEN-LIVE"
        )
        assert res_live["status"] == "success"
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload.get("test_event_code") == "TEST20793"
        assert payload["data"][0]["user_data"]["ph"] != ""


def test_capi_retry_pending_credentials(temp_db, monkeypatch):
    from app.services.meta_capi_service import retry_pending_capi_conversions
    from app.database import update_click_sale, log_conversion, is_sales_order_processed

    # 1. Setup a click log and conversion in pending state
    token = "HC-RETRY-TOKEN-1"
    so_id = "SO-RETRY-999"
    save_click_log({"session_token": token, "fbclid": "fbclid_retry_999", "channel": "WhatsApp", "brand": "Home Cartel"})
    save_customer_identity("phone", "9171234567", token, "Home Cartel")
    update_click_sale(token, so_id, 25000.0, "pending_credentials")
    log_conversion(so_id, token, "fbclid_retry_999", 25000.0, "failed_missing_credentials", "Missing token")

    # 2. When META_ACCESS_TOKEN is not set, retry is skipped
    monkeypatch.setenv("META_ACCESS_TOKEN", "")
    res_skip = retry_pending_capi_conversions()
    assert res_skip["status"] == "skipped"

    # 3. When META_ACCESS_TOKEN is set and Meta API returns 200, updates to 'sent'
    monkeypatch.setenv("META_ACCESS_TOKEN", "EAAB_LIVE_TEST_TOKEN")
    monkeypatch.setattr("app.services.meta_capi_service.META_DATASET_ID", "236624173955711")

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"events_received": 1}'
        mock_resp.json.return_value = {"events_received": 1}
        mock_post.return_value = mock_resp

        res_retry = retry_pending_capi_conversions()
        assert res_retry["status"] == "ok"
        assert res_retry["retried"] == 1
        assert res_retry["success"] == 1

        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT status FROM conversions_audit WHERE salesorder_id = ?", (so_id,))
            assert c.fetchone()["status"] == "sent"

            c.execute("SELECT capi_status FROM click_logs WHERE session_token = ?", (token,))
            assert c.fetchone()["capi_status"] == "sent"


def test_re_evaluate_unattributed_orders(temp_db):
    from app.database import is_sales_order_processed, log_conversion

    so_id = "SO-UNATTR-101"
    log_conversion(so_id, "", "", 12000.0, "unattributed", "No match yet")

    # Unattributed orders return False so sync_paid_sales_orders does not skip them
    assert is_sales_order_processed(so_id) is False

    # Once attributed/sent, returns True to prevent duplicate dispatch
    log_conversion(so_id, "HC-TOKEN-101", "fbclid_101", 12000.0, "sent", "Sent to Meta")
    assert is_sales_order_processed(so_id) is True

