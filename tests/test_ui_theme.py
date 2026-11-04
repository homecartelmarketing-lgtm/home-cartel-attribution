"""
Test Suite for Dashboard UI/UX Pro Redesign & Live Theme Switcher
Verifies that /dashboard includes ui-ux-pro-max design system tokens,
the theme switcher controls, and scoped theme architecture.
"""

from fastapi.testclient import TestClient
from app.server import app


def test_dashboard_contains_theme_switcher():
    """Verify that the dashboard HTML includes the theme switcher pill and buttons."""
    with TestClient(app) as client:
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        html = resp.text

        # Verify theme switcher container and buttons exist
        assert 'class="theme-switcher-pill"' in html
        assert 'id="btn-theme-modern"' in html
        assert 'id="btn-theme-classic"' in html
        assert 'setDashboardTheme' in html


def test_dashboard_contains_ui_ux_pro_max_tokens():
    """Verify that the dashboard contains ui-ux-pro-max tokens from MASTER.md."""
    with TestClient(app) as client:
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        html = resp.text

        # Verify font imports
        assert 'Fira+Code' in html or 'Fira+Sans' in html

        # Verify scoped modern-pro CSS rules
        assert 'body[data-theme="modern-pro"]' in html
        assert '#1e40af' in html.lower()  # Primary blue
        assert '#f8fafc' in html.lower()  # Background slate
        assert 'font-variant-numeric: tabular-nums' in html
