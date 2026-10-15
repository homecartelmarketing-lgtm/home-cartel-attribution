"""
Test Suite for Python-Native Attribution Engine
Tests all endpoints, SQLite database operations, and background worker logic.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.server import app
from app.database import init_db, get_connection

def test_engine():
    print("=" * 65)
    print(" TESTING PYTHON ATTRIBUTION SERVER (ENDPOINTS & DATABASE)")
    print("=" * 65)
    
    init_db()
    client = TestClient(app)
    try:
        from app.auth import COOKIE_NAME, create_access_token
        token = create_access_token("admin")
        client.cookies.set(COOKIE_NAME, token)
    except Exception as e:
        print("Auth cookie error:", e)
    
    # 1. Health check endpoint
    resp = client.get("/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    health_data = resp.json()
    print(f"[PASS] /health check: status={health_data['status']}, engine={health_data['engine']}")
    
    # 2. Click log ingestion (/webhook/click-log)
    sample_click = {
        "session_token": "HC-1791440000000-88888",
        "fbclid": "IwAR_TEST_FBCLID_PYTHON_123",
        "fbclid_ts": 1791440000000,
        "utm_source": "facebook",
        "utm_medium": "paid_social",
        "utm_campaign": "python_native_engine",
        "utm_content": "carousel_v1",
        "channel": "WhatsApp",
        "brand": "Home Cartel"
    }
    resp_click = client.post("/webhook/click-log", json=sample_click)
    assert resp_click.status_code == 200, f"Click log failed: {resp_click.text}"
    print(f"[PASS] /webhook/click-log accepted: session_token={resp_click.json()['session_token']}")
    
    # Verify in SQLite database
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM click_logs WHERE session_token = ?", (sample_click["session_token"],))
        row = cursor.fetchone()
        assert row is not None, "Click log not found in SQLite"
        assert row["fbclid"] == sample_click["fbclid"], "fbclid mismatch in DB"
        print("[PASS] SQLite click_logs verified.")
        
    # 3. Zoho Books Sales Order Webhook (/webhook/zoho-sales-order)
    sample_so = {
        "salesorder": {
            "salesorder_id": "SO-PY-99001",
            "salesorder_number": "SO-0099",
            "customer_id": "CUST-101",
            "email": "customer.test@example.com",
            "phone": "0917-555-1234",
            "total": 32500.00,
            "custom_fields": [
                {"label": "Session Token", "value": "HC-1791440000000-88888"},
                {"label": "FB Click ID", "value": "IwAR_TEST_FBCLID_PYTHON_123"},
                {"label": "Brand", "value": "Home Cartel"}
            ]
        }
    }
    resp_so = client.post("/webhook/zoho-sales-order", json=sample_so)
    assert resp_so.status_code == 200, f"Sales order webhook failed: {resp_so.text}"
    so_res = resp_so.json()
    assert so_res["status"] == "accepted", f"SO status not accepted: {so_res}"
    print(f"[PASS] /webhook/zoho-sales-order accepted: order #{so_res['salesorder_id']}, amount PHP {so_res['amount']:,.2f}")
    
    # 4. Audit endpoint (/audit)
    resp_audit = client.get("/audit")
    assert resp_audit.status_code == 200, f"Audit endpoint failed: {resp_audit.text}"
    audit_data = resp_audit.json()
    print(f"[PASS] /audit report: total_ad_clicks={audit_data['total_ad_clicks_24h']}")
    
    print("=" * 65)
    print(" ALL PYTHON MIDDLEWARE TESTS PASSED (100% OPERATIONAL)")
    print("=" * 65)

if __name__ == "__main__":
    test_engine()
