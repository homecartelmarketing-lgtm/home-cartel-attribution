"""Tests for the Zoho OAuth token service (Phase 1)."""

import time

import pytest

from app.services import zoho_auth_service
from app.services.zoho_auth_service import ZohoAuthError


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


def _valid_token_response():
    return FakeResponse(200, {
        "access_token": "TOKEN-ABC-123",
        "expires_in": 3600,
        "api_domain": "https://www.zohoapis.com",
    })


def test_refresh_token_missing_raises(monkeypatch):
    """A brand without a refresh token raises instead of failing silently."""
    monkeypatch.setattr(
        zoho_auth_service, "get_brand_config", lambda brand: {"zoho_refresh_token": ""}
    )
    zoho_auth_service.clear_cache()
    with pytest.raises(ZohoAuthError):
        zoho_auth_service.get_access_token("Home Cartel")


def test_token_cached_until_expiry(monkeypatch):
    """The token is fetched once and reused until it expires."""
    calls = []

    def fake_post(url, data=None, timeout=None):
        calls.append(data)
        return _valid_token_response()

    monkeypatch.setattr(zoho_auth_service.requests, "post", fake_post)
    monkeypatch.setattr(
        zoho_auth_service,
        "get_brand_config",
        lambda brand: {"zoho_refresh_token": "REFRESH-1"},
    )
    monkeypatch.setattr(zoho_auth_service, "ZOHO_CLIENT_ID", "CID")
    monkeypatch.setattr(zoho_auth_service, "ZOHO_CLIENT_SECRET", "CSECRET")
    zoho_auth_service.clear_cache()

    first = zoho_auth_service.get_access_token("Home Cartel")
    second = zoho_auth_service.get_access_token("Home Cartel")

    assert first == "TOKEN-ABC-123"
    assert second == "TOKEN-ABC-123"
    assert len(calls) == 1, "token endpoint must be hit only once while cached"


def test_token_refreshed_after_expiry(monkeypatch):
    """An expired cached token forces a fresh grant."""
    responses = [
        FakeResponse(200, {"access_token": "OLD", "expires_in": 3600}),
        FakeResponse(200, {"access_token": "NEW", "expires_in": 3600}),
    ]

    def fake_post(url, data=None, timeout=None):
        return responses.pop(0)

    monkeypatch.setattr(zoho_auth_service.requests, "post", fake_post)
    monkeypatch.setattr(
        zoho_auth_service,
        "get_brand_config",
        lambda brand: {"zoho_refresh_token": "REFRESH-2"},
    )
    zoho_auth_service.clear_cache()

    zoho_auth_service.get_access_token("Home Cartel")

    # Push the cached token past its expiry.
    from app.services.zoho_auth_service import _token_cache

    _token_cache["REFRESH-2"]["expires_at"] = time.time() - 1

    refreshed = zoho_auth_service.get_access_token("Home Cartel")
    assert refreshed == "NEW"


def test_error_response_raises(monkeypatch):
    """A rejected grant raises ZohoAuthError with context."""
    monkeypatch.setattr(
        zoho_auth_service.requests, "post",
        lambda url, data=None, timeout=None: FakeResponse(400, {"error": "invalid_client"}),
    )
    monkeypatch.setattr(
        zoho_auth_service,
        "get_brand_config",
        lambda brand: {"zoho_refresh_token": "REFRESH-3"},
    )
    zoho_auth_service.clear_cache()

    with pytest.raises(ZohoAuthError):
        zoho_auth_service.get_access_token("Home Cartel")


def test_resolve_org_id_missing(monkeypatch):
    monkeypatch.setattr(
        zoho_auth_service, "get_brand_config", lambda brand: {"zoho_org_id": ""}
    )
    with pytest.raises(ZohoAuthError):
        zoho_auth_service.resolve_org_id("Home Cartel")
