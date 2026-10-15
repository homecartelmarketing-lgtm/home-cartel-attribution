"""Endpoint tests for the hardened server (Phase 4)."""

import hashlib
import hmac
import json

from fastapi.testclient import TestClient

import app.config as config_module
from app.server import app, _verify_zoho_signature


def test_health_endpoint(temp_db):
    config_module.DATABASE_PATH  # noqa - module must load
    from app import server

    with TestClient(server.app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "online"


def test_click_log_endpoint(temp_db):
    from app import server

    payload = {
        "session_token": "HC-1791780000000-22222",
        "fbclid": "IwAR_x",
        "channel": "Messenger",
        "brand": "Home Cartel",
    }
    with TestClient(server.app) as client:
        resp = client.post("/webhook/click-log", json=payload)
    assert resp.status_code == 200
    assert resp.json()["session_token"] == payload["session_token"]


def test_zoho_webhook_rejects_unsigned_when_secret_set(temp_db, monkeypatch):
    """Missing signature is rejected outright when a secret is configured."""
    from app import server

    monkeypatch.setattr(server, "ZOHO_WEBHOOK_SECRET", "test-secret-12345")

    body = {"salesorder": {"salesorder_id": "SO-1", "total": 100}}
    with TestClient(server.app) as client:
        resp = client.post("/webhook/zoho-sales-order", json=body)
    assert resp.status_code == 403


def test_zoho_webhook_accepts_valid_hmac(temp_db, monkeypatch):
    from app import server

    secret = "test-secret-12345"
    monkeypatch.setattr(server, "ZOHO_WEBHOOK_SECRET", secret)

    body = {
        "salesorder": {
            "salesorder_id": "SO-HMAC-1",
            "total": 5000.0,
            "custom_fields": [
                {"label": "Session Token", "value": ""},
                {"label": "FB Click ID", "value": ""},
            ],
        }
    }
    raw = json.dumps(body).encode("utf-8")
    signature = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()

    with TestClient(server.app) as client:
        resp = client.post(
            "/webhook/zoho-sales-order",
            content=raw,
            headers={
                "Content-Type": "application/json",
                "X-Zoho-Webhook-Signature": signature,
            },
        )
    # Empty token means "skipped", not "rejected" - the signature passed.
    assert resp.status_code == 200
    assert resp.json()["status"] == "skipped"


def test_zoho_webhook_rejects_tampered_hmac(temp_db, monkeypatch):
    from app import server

    monkeypatch.setattr(server, "ZOHO_WEBHOOK_SECRET", "test-secret-12345")

    with TestClient(server.app) as client:
        resp = client.post(
            "/webhook/zoho-sales-order",
            json={"salesorder": {"salesorder_id": "SO-X"}},
            headers={"X-Zoho-Webhook-Signature": "0" * 64},
        )
    assert resp.status_code == 403


def test_clicks_api_no_fanout(temp_db, sample_click):
    """One click joined against two audit rows still returns one row."""
    from app.database import log_conversion
    from app import server

    log_conversion("SO-A", "HC-1791780000000-11111", "IwAR_test_fbclid_11111", 1000.0, "success")
    log_conversion("SO-B", "HC-1791780000000-11111", "IwAR_test_fbclid_11111", 2000.0, "success")

    with TestClient(server.app) as client:
        resp = client.get("/api/clicks")
    assert resp.status_code == 200
    # Only one click row carries our token; it must appear exactly once.
    matches = [c for c in resp.json()["clicks"] if c["session_token"] == sample_click["session_token"]]
    assert len(matches) == 1


def test_analytics_sync_endpoint(temp_db):
    from app import server

    with TestClient(server.app) as client:
        resp = client.post(
            "/webhook/analytics-sync",
            json={"brand": "Home Cartel", "date": "2026-10-12", "sessions": 120, "inquiries": 9},
        )
    assert resp.status_code == 200
    assert resp.json()["recorded"]["sessions"] == 120


def test_alerts_endpoint(temp_db):
    from app import server
    from app.services import alert_engine

    with TestClient(server.app) as client:
        resp = client.get("/api/alerts")
    assert resp.status_code == 200
    assert "alerts" in resp.json()
