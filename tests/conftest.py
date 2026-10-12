"""
Shared pytest fixtures for the Ad-to-Sale Attribution System.

Every test runs against an isolated temporary SQLite database so the live
attribution.db on disk is never touched.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import app.config as config_module
from app.database import init_db


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_attribution.db")

    # app.database binds DATABASE_PATH at import time via
    # "from app.config import DATABASE_PATH", so patching app.config alone
    # does nothing. Patch the value where it is actually read.
    import app.database as database_module
    import app.services.analytics_store as analytics_store_module

    monkeypatch.setattr(config_module, "DATABASE_PATH", db_path)
    monkeypatch.setattr(database_module, "DATABASE_PATH", db_path)
    monkeypatch.setattr(analytics_store_module, "DATABASE_PATH", db_path)
    init_db()
    return db_path


@pytest.fixture()
def sample_click(temp_db):
    """One pending WhatsApp click log for matching tests."""
    from app.database import save_click_log

    payload = {
        "session_token": "HC-1791780000000-11111",
        "fbclid": "IwAR_test_fbclid_11111",
        "fbclid_ts": 1791780000000,
        "utm_source": "facebook",
        "utm_medium": "paid_social",
        "utm_campaign": "chandelier_deals",
        "utm_content": "video_ad_1",
        "channel": "WhatsApp",
        "brand": "Home Cartel",
        "landing_page": "https://home-cartel.myshopify.com",
        "referrer": "https://m.facebook.com",
        "timestamp": "2026-10-12T08:00:00+08:00",
    }
    assert save_click_log(payload)
    return payload


@pytest.fixture()
def zendesk_ticket():
    """A minimal Zendesk ticket shape as returned by the Search API."""
    return {
        "id": 1001,
        "requester_id": 501,
        "subject": "How much for the crystal chandelier?",
        "description": "Magkano po yung crystal chandelier?",
        "tags": ["rfq_detected", "brand_home_cartel"],
        "custom_fields": [
            {"id": 17953452223503, "value": "HC-1791780000000-11111"},
            {"id": 17953492031119, "value": "IwAR_test_fbclid_11111"},
            {"id": 17953470092687, "value": "chandelier_deals"},
            {"id": 17953470454671, "value": "facebook"},
            {"id": 17953481428751, "value": "WhatsApp"},
        ],
        "created_at": "2026-10-12T08:05:00Z",
        "via": {"channel": "whatsapp"},
    }
