import pytest
from unittest.mock import patch, MagicMock
from app.services import zoho_creator_service
from app.database import get_connection, save_click_log, save_customer_identity

def test_normalize_phone():
    assert zoho_creator_service.normalize_phone("+639955805699") == "9955805699"
    assert zoho_creator_service.normalize_phone("09955805699") == "9955805699"
    assert zoho_creator_service.normalize_phone("+63-908-413-6502") == "9084136502"
    assert zoho_creator_service.normalize_phone("9955805699") == "9955805699"
    assert zoho_creator_service.normalize_phone("") == ""
    # Hardened tests for malformed live Zoho prefixes
    assert zoho_creator_service.normalize_phone("+63-09178389270") == "9178389270"
    assert zoho_creator_service.normalize_phone("+63-+639052126300") == "9052126300"
    assert zoho_creator_service.normalize_phone("09175563077") == "9175563077"

def test_find_matching_session_by_estimate_number(temp_db):
    save_click_log({
        "session_token": "HC-TEST-EST-MATCH",
        "fbclid": "fbclid_est_123",
        "utm_campaign": "test_promo",
        "channel": "WhatsApp",
        "brand": "Home Cartel"
    })
    with get_connection() as conn:
        conn.cursor().execute(
            "UPDATE click_logs SET zoho_estimate_num = 'QUO-99999' WHERE session_token = 'HC-TEST-EST-MATCH'"
        )
        conn.commit()

    match = zoho_creator_service.find_matching_session(estimate_number="QUO-99999")
    assert match is not None
    assert match["session_token"] == "HC-TEST-EST-MATCH"

def test_find_matching_session_by_phone(temp_db):
    session_token = "HC-TEST-PHONE-MATCH"
    save_click_log({
        "session_token": session_token,
        "fbclid": "fbclid_phone_123",
        "channel": "WhatsApp",
        "brand": "Home Cartel"
    })
    save_customer_identity("phone", "9175551234", session_token, "Home Cartel")

    match = zoho_creator_service.find_matching_session(phone="+63 917 555 1234")
    assert match is not None
    assert match["session_token"] == session_token

def test_find_matching_session_channel_agnostic(temp_db):
    session_token = "HC-TEST-WHATSAPP-MATCH"
    save_click_log({
        "session_token": session_token,
        "fbclid": "fbclid_wa_999",
        "channel": "WhatsApp",
        "brand": "Home Cartel"
    })
    # Saved with channel 'whatsapp'
    save_customer_identity("whatsapp", "9178389270", session_token, "Home Cartel")

    # Order arrives with malformed Zoho phone '+63-09178389270'
    match = zoho_creator_service.find_matching_session(phone="+63-09178389270")
    assert match is not None
    assert match["session_token"] == session_token
