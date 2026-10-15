"""
Auth tests: login page, JWT cookie flow, rate limiting, protected routes.
temp_db fixture (conftest) disables auth by default; these tests
re-enable it explicitly via monkeypatch on BOTH config and auth modules.
"""
import pytest
from fastapi.testclient import TestClient

import app.config as config_module
import app.auth as auth_module
from app.server import app


@pytest.fixture()
def auth_env(temp_db, monkeypatch):
    secret = "test-secret-key-for-pytest-only-1234567890"
    pw_hash = auth_module.hash_password("correct-horse")
    monkeypatch.setattr(config_module, "AUTH_ENABLED", True)
    monkeypatch.setattr(auth_module, "AUTH_ENABLED", True)
    monkeypatch.setattr(config_module, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(auth_module, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(config_module, "ADMIN_PASSWORD_HASH", pw_hash)
    monkeypatch.setattr(auth_module, "ADMIN_PASSWORD_HASH", pw_hash)
    monkeypatch.setattr(config_module, "AUTH_SECRET_KEY", secret)
    monkeypatch.setattr(auth_module, "AUTH_SECRET_KEY", secret)
    auth_module._LOGIN_ATTEMPTS.clear()
    return {"username": "admin", "password": "correct-horse"}


def _login(client, username="admin", password="correct-horse"):
    return client.post("/login", data={"username": username, "password": password})


def test_login_page_renders(auth_env):
    with TestClient(app) as client:
        resp = client.get("/login")
    assert resp.status_code == 200
    assert "Sign in" in resp.text
    assert 'action="/login"' in resp.text


def test_dashboard_redirects_to_login_when_anonymous(auth_env):
    with TestClient(app) as client:
        resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/login"


def test_api_requires_auth_when_anonymous(auth_env):
    with TestClient(app) as client:
        assert client.get("/api/clicks").status_code == 401
        assert client.get("/api/alerts").status_code == 401


def test_login_success_sets_cookie_and_opens_dashboard(auth_env):
    with TestClient(app) as client:
        resp = _login(client)
        assert resp.status_code == 200  # followed 303 -> /dashboard
        assert "hc_session" in client.cookies
        assert "Ad Attribution" in resp.text


def test_login_wrong_password_rejected(auth_env):
    with TestClient(app) as client:
        resp = _login(client, password="wrong-password")
    assert resp.status_code == 401
    assert "Invalid username or password" in resp.text
    assert "hc_session" not in client.cookies


def test_login_rate_limited_after_5_failures(auth_env):
    with TestClient(app) as client:
        for _ in range(5):
            r = _login(client, password="nope")
            assert r.status_code == 401
        blocked = _login(client, password="nope")
        assert blocked.status_code == 429
        assert "Too many attempts" in blocked.text


def test_logout_clears_session(auth_env):
    with TestClient(app) as client:
        _login(client)
        assert "hc_session" in client.cookies
        resp = client.post("/logout", follow_redirects=False)
        assert resp.status_code == 303
        assert resp.headers["location"] == "/login"


def test_public_endpoints_stay_open(auth_env):
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        payload = {
            "session_token": "HC-AUTH-TEST-1",
            "channel": "WhatsApp",
            "brand": "Home Cartel",
        }
        r = client.post("/webhook/click-log", json=payload)
        assert r.status_code == 200


def test_root_redirects_to_login_when_anonymous(auth_env):
    with TestClient(app) as client:
        resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/login"


def test_root_goes_to_dashboard_when_authenticated(auth_env):
    with TestClient(app) as client:
        _login(client)
        resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/dashboard"


def test_health_stays_public(auth_env):
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "online"
