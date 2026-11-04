"""
Test Suite for Dashboard UI/UX Pro Redesign
Verifies that /dashboard directly uses the ui-ux-pro-max design system tokens,
sets modern-pro theme on body by default, and does not display an extra theme switcher pill.
"""

from fastapi.testclient import TestClient
from app.server import app


def test_dashboard_uses_modern_pro_by_default():
    """Verify that the dashboard HTML applies modern-pro directly without extra switcher buttons."""
    with TestClient(app) as client:
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        html = resp.text

        # Verify body has modern-pro set directly
        assert '<body data-theme="modern-pro">' in html

        # Verify theme switcher pill is removed
        assert 'class="theme-switcher-pill"' not in html
        assert 'id="btn-theme-classic"' not in html


def test_dashboard_contains_ui_ux_pro_max_tokens():
    """Verify that the dashboard contains ui-ux-pro-max tokens from MASTER.md."""
    with TestClient(app) as client:
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        html = resp.text

        # Verify font imports
        assert 'Fira+Code' in html or 'Fira+Sans' in html

        # Verify modern-pro CSS rules & color tokens
        assert 'body[data-theme="modern-pro"]' in html
        assert '#1e40af' in html.lower()  # Primary blue
        assert '#f8fafc' in html.lower()  # Background slate
        assert 'font-variant-numeric: tabular-nums' in html
