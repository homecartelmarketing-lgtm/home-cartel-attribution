"""Tests for the audit report and alert engines (Phases 4 & 5)."""

from app.services import audit_report_service, alert_engine


def test_audit_computes_gap(temp_db, sample_click):
    """One click with no ticket yields a 100% tracking gap."""
    report = audit_report_service.compute_daily_audit()

    assert report["total_ad_clicks_24h"] == 1
    assert report["total_tickets_linked_24h"] == 0
    assert report["tracking_gap_percentage"] == 100.0
    assert report["status"] == "ATTENTION_NEEDED"


def test_audit_healthy_when_linked(temp_db, sample_click):
    from app.database import update_click_zendesk

    update_click_zendesk("HC-1791780000000-11111", 1001)

    report = audit_report_service.compute_daily_audit()
    assert report["tracking_gap_percentage"] == 0.0
    assert report["status"] == "HEALTHY"


def test_unmatched_sweep(temp_db, sample_click):
    from app.database import get_connection

    # Age the click past the 24h threshold.
    with get_connection() as conn:
        conn.execute(
            "UPDATE click_logs SET created_at = datetime('now', '-48 hours')"
        )
        conn.commit()

    unmatched = audit_report_service.find_unmatched_tickets()
    assert len(unmatched) == 1
    assert unmatched[0]["session_token"] == "HC-1791780000000-11111"


def test_audit_email_renders(temp_db, sample_click):
    report = audit_report_service.compute_daily_audit()
    rendered = audit_report_service.render_audit_email(report, [])

    assert "Daily Attribution Audit" in rendered["text"]
    assert "tracking_gap_percentage" not in rendered["text"]
    assert rendered["subject"].startswith("[AUDIT]")


def test_ctr_alerts_fire(monkeypatch):
    """CTR < 0.43% with >= 2,000 impressions is CRITICAL (Alert 2)."""
    monkeypatch.setattr(
        alert_engine.meta_insights_service, "get_ad_level_metrics",
        lambda brand, days=3: [
            {"ad_id": "1", "ad_name": "Bad Creative", "campaign_name": "C1",
             "ctr_pct": 0.30, "impressions": 5000, "spend": 100.0},
        ],
    )
    alert_engine.clear_cache()

    fired = alert_engine.check_ctr_alerts("Home Cartel", send=False)

    assert len(fired) == 1
    assert fired[0]["alert_id"] == 2
    assert fired[0]["severity"] == "CRITICAL"


def test_ctr_alerts_skip_low_volume(monkeypatch):
    monkeypatch.setattr(
        alert_engine.meta_insights_service, "get_ad_level_metrics",
        lambda brand, days=3: [
            {"ad_id": "1", "ad_name": "Thin Data", "campaign_name": "C1",
             "ctr_pct": 0.10, "impressions": 500, "spend": 10.0},
        ],
    )
    alert_engine.clear_cache()
    assert alert_engine.check_ctr_alerts("Home Cartel", send=False) == []


def test_fatigue_thresholds(monkeypatch):
    monkeypatch.setattr(
        alert_engine.meta_insights_service, "query_table_a_creative_fatigue",
        lambda brand: [
            {"ad_name": "Burned Out", "campaign_name": "C1", "ctr_change_pct": -45.0},
            {"ad_name": "Tiring", "campaign_name": "C1", "ctr_change_pct": -25.0},
            {"ad_name": "Fresh", "campaign_name": "C1", "ctr_change_pct": -5.0},
        ],
    )
    alert_engine.clear_cache()

    fired = alert_engine.check_creative_fatigue_alerts("Home Cartel", send=False)
    ids = sorted(a["alert_id"] for a in fired)

    assert ids == [7, 8]


def test_anomaly_spend_alert(monkeypatch, temp_db):
    """Spend > PHP 3,000 with zero inquiries fires Alert 11."""
    monkeypatch.setattr(
        alert_engine.meta_insights_service, "get_total_spend_24h",
        lambda brand: 5000.0,
    )
    alert_engine.clear_cache()

    fired = alert_engine.check_anomaly_spend_alerts("Home Cartel", send=False)
    assert len(fired) == 1
    assert fired[0]["alert_id"] == 11
    assert fired[0]["severity"] == "CRITICAL"


def test_anomaly_spend_quiet_when_leads_exist(monkeypatch, temp_db, sample_click):
    from app.database import update_click_zendesk

    update_click_zendesk("HC-1791780000000-11111", 1001)
    monkeypatch.setattr(
        alert_engine.meta_insights_service, "get_total_spend_24h",
        lambda brand: 5000.0,
    )
    alert_engine.clear_cache()

    assert alert_engine.check_anomaly_spend_alerts("Home Cartel", send=False) == []
