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


def test_section_264_alert_rules_table():
    """Verify Section 2.6.4 table configuration contains all 11 rules with proper fields."""
    rules = alert_engine.SECTION_264_ALERT_RULES
    assert len(rules) == 11

    levels = {r["level"] for r in rules}
    assert levels == {"WATCH", "WARNING", "CRITICAL"}

    for r in rules:
        assert "parameter" in r
        assert "trigger_condition" in r
        assert "required_action" in r
        assert "source" in r
        assert "routing" in r


def test_database_campaign_spend_evaluation():
    """Evaluate Section 2.6.4 alerts on database campaigns with mandatory FR Stores exclusion."""
    summary = alert_engine.evaluate_campaign_spend_alerts("Home Cartel")

    assert summary["overall_status"] in ["WATCH", "WARNING", "CRITICAL", "HEALTHY"]
    assert "counts" in summary
    assert "evaluations" in summary

    # Ensure no FR Stores campaigns are present in evaluated campaigns
    for ev in summary["evaluations"]:
        assert "FR Stores" not in ev["campaign_name"]

    # Check that WATCH alert is triggered for IG Magnetic Lights (Frequency 2.96 > 2.5)
    watch_alerts = [a for a in summary["alerts"] if a["level"] == "WATCH"]
    assert len(watch_alerts) >= 1
    magnetic = next(
        (a for a in watch_alerts if "Magnetic Track Lights" in a["campaign_name"]), None
    )
    assert magnetic is not None
    assert magnetic["parameter"] == "Audience Saturation"
    assert "Monitor closely" in magnetic["required_action"]


def test_campaign_evaluation_exposes_thresholds():
    """Dashboard Ad Health charts draw their lines from the same thresholds the alerts use."""
    summary = alert_engine.evaluate_campaign_spend_alerts("Home Cartel")
    th = summary["thresholds"]

    assert th["frequency"] == {"watch": 2.5, "warning": 3.5, "critical": 4.5}
    assert th["ctr"] == {"warning": 0.67, "critical": 0.43}
    # CPC percentiles are reference points only, not alert triggers (PDF 2.6.3).
    assert th["cpc_reference"] == {"p75": 16.31, "p90": 26.48}
    assert "cpc" not in th


def test_api_alerts_endpoint(temp_db):
    """Test GET /api/alerts returns HTTP 200 with complete Section 2.6.4 structure."""
    from fastapi.testclient import TestClient
    from app.server import app

    client = TestClient(app)
    res = client.get("/api/alerts")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "counts" in data
    assert "overall_status" in data
    assert "alerts" in data
    assert "evaluations" in data
    assert len(data["rules_reference"]) == 11



def _insert_campaign(conn, name, *, impressions, reach, ctr, cpc, spend,
                     status="active", starts="2026-09-12", ends="2026-10-11"):
    conn.execute(
        """
        INSERT INTO meta_campaign_spend
            (reporting_starts, reporting_ends, campaign_name, status, amount_spent,
             impressions, reach, link_clicks, cpc, ctr, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 100, ?, ?, '2026-10-14 08:11:30')
        """,
        (starts, ends, name, status, spend, impressions, reach, cpc, ctr),
    )


def test_high_cpc_alone_does_not_raise_expensive_ads_alert(temp_db):
    """CPC percentiles are reference only; Expensive Ads needs a per-ad 30-day baseline."""
    from app.database import get_connection

    with get_connection() as conn:
        _insert_campaign(conn, "Costly Campaign", impressions=1000, reach=900,
                         ctr=1.5, cpc=40.0, spend=5000)
        conn.commit()

    summary = alert_engine.evaluate_campaign_spend_alerts("Home Cartel")
    assert summary["overall_status"] == "HEALTHY"
    assert not [a for a in summary["alerts"] if a["parameter"] == "Expensive Ads"]


def test_evaluation_reports_csv_provenance_and_sop(temp_db):
    from app.database import get_connection

    with get_connection() as conn:
        _insert_campaign(conn, "Saturated Campaign", impressions=5000, reach=1000,
                         ctr=1.5, cpc=3.0, spend=2000)
        _insert_campaign(conn, "FR Stores - Reach - Geo-Targeted", impressions=5000,
                         reach=1000, ctr=0.04, cpc=3.0, spend=900)
        conn.commit()

    summary = alert_engine.evaluate_campaign_spend_alerts("Home Cartel")
    assert summary["data_source"] == "meta_csv_import"
    assert summary["data_as_of"] == "2026-10-14 08:11:30"
    assert summary["window"] == {"start": "2026-09-12", "end": "2026-10-11"}

    # FR Stores is excluded; the saturated campaign is CRITICAL with its SOP attached.
    assert [e["campaign_name"] for e in summary["evaluations"]] == ["Saturated Campaign"]
    ev = summary["evaluations"][0]
    assert ev["level"] == "CRITICAL"
    assert ev["sop"]["title"].startswith("Audience Saturation")
    assert any("Do not simply lower the budget" in s for s in ev["sop"]["steps"])


def test_alert_routing_by_severity(monkeypatch):
    monkeypatch.setattr(alert_engine, "ALERT_RECIPIENTS", ["monitor@x.com"])
    monkeypatch.setattr(alert_engine, "ALERT_BRAND_TEAM_RECIPIENTS", ["team@x.com"])
    monkeypatch.setattr(alert_engine, "ALERT_OWNER_RECIPIENTS", ["owner@x.com", "monitor@x.com"])
    monkeypatch.setattr(alert_engine, "get_brand_config", lambda brand: {})

    assert alert_engine.recipients_for_severity("Home Cartel", "WATCH") == ["monitor@x.com"]
    assert alert_engine.recipients_for_severity("Home Cartel", "WARNING") == [
        "monitor@x.com", "team@x.com"]
    assert alert_engine.recipients_for_severity("Home Cartel", "CRITICAL") == [
        "monitor@x.com", "team@x.com", "owner@x.com"]


def test_daily_digest_goes_to_monitor_and_owner(temp_db, monkeypatch):
    from app.database import get_connection

    with get_connection() as conn:
        _insert_campaign(conn, "Saturated <Campaign>", impressions=3000, reach=1000,
                         ctr=1.5, cpc=3.0, spend=2000)
        conn.commit()

    sent = {}

    def fake_send_email(subject, body_text, body_html=None, recipients=None):
        sent.update(subject=subject, text=body_text, html=body_html, recipients=recipients)
        return {"status": "sent"}

    monkeypatch.setattr(alert_engine, "send_email", fake_send_email)
    monkeypatch.setattr(alert_engine, "ALERT_RECIPIENTS", ["monitor@x.com"])
    monkeypatch.setattr(alert_engine, "ALERT_OWNER_RECIPIENTS", ["owner@x.com"])
    monkeypatch.setattr(alert_engine, "get_brand_config", lambda brand: {})

    result = alert_engine.send_daily_ad_health_digest("Home Cartel")

    assert result["status"] == "sent"
    assert sent["subject"].startswith("Daily Digest — Home Cartel —")
    assert sent["recipients"] == ["monitor@x.com", "owner@x.com"]
    assert "WATCH" in sent["text"] and "Saturated <Campaign>" in sent["text"]
    assert "Saturated &lt;Campaign&gt;" in sent["html"]


def _fake_mailer(monkeypatch, sent, status="sent"):
    def fake_send_email(subject, body_text, body_html=None, recipients=None):
        sent.append({"subject": subject, "text": body_text, "html": body_html, "recipients": recipients})
        return {"status": status} if status != "skipped" else {"status": "skipped", "reason": "No recipients configured"}

    monkeypatch.setattr(alert_engine, "send_email", fake_send_email)
    monkeypatch.setattr(alert_engine, "ALERT_RECIPIENTS", ["monitor@x.com"])
    monkeypatch.setattr(alert_engine, "ALERT_BRAND_TEAM_RECIPIENTS", ["team@x.com"])
    monkeypatch.setattr(alert_engine, "ALERT_OWNER_RECIPIENTS", ["owner@x.com"])
    monkeypatch.setattr(alert_engine, "get_brand_config", lambda brand: {})


def _set_campaign_reach(conn, name, impressions, reach):
    conn.execute(
        "UPDATE meta_campaign_spend SET impressions = ?, reach = ? WHERE campaign_name = ?",
        (impressions, reach, name),
    )
    conn.commit()


def test_notify_emails_only_new_or_escalated_campaigns(temp_db, monkeypatch):
    from app.database import get_connection

    sent = []
    _fake_mailer(monkeypatch, sent)
    with get_connection() as conn:
        _insert_campaign(conn, "Saturated Campaign", impressions=3000, reach=1000,
                         ctr=1.5, cpc=3.0, spend=2000)
        _insert_campaign(conn, "Fine Campaign", impressions=1200, reach=1000,
                         ctr=1.5, cpc=3.0, spend=500)
        conn.commit()

    # First run: the WATCH campaign is new -> monitoring person only.
    first = alert_engine.notify_ad_health_changes("Home Cartel")
    assert [a["campaign_name"] for a in first["new_alerts"]] == ["Saturated Campaign"]
    assert first["new_alerts"][0]["level"] == "WATCH"
    assert first["new_alerts"][0]["previous_level"] == "HEALTHY"
    assert first["emails_sent"] == 1
    assert sent[-1]["recipients"] == ["monitor@x.com"]
    assert sent[-1]["subject"].startswith("[WATCH] — Home Cartel — Audience Saturation")
    assert "Saturated Campaign" in sent[-1]["text"]

    # Unchanged data: nothing to say.
    again = alert_engine.notify_ad_health_changes("Home Cartel")
    assert again["new_alerts"] == []
    assert len(sent) == 1

    # Escalation to CRITICAL: emailed to monitor + brand team + owner.
    with get_connection() as conn:
        _set_campaign_reach(conn, "Saturated Campaign", 6000, 1000)
    escalated = alert_engine.notify_ad_health_changes("Home Cartel")
    assert [(a["level"], a["previous_level"]) for a in escalated["new_alerts"]] == [("CRITICAL", "WATCH")]
    assert sent[-1]["recipients"] == ["monitor@x.com", "team@x.com", "owner@x.com"]
    assert escalated["new_alerts"][0]["sop"]["title"].startswith("Audience Saturation")

    # Improvement is silent, but a later relapse is emailed again.
    with get_connection() as conn:
        _set_campaign_reach(conn, "Saturated Campaign", 1200, 1000)
    assert alert_engine.notify_ad_health_changes("Home Cartel")["new_alerts"] == []
    with get_connection() as conn:
        _set_campaign_reach(conn, "Saturated Campaign", 6000, 1000)
    assert len(alert_engine.notify_ad_health_changes("Home Cartel")["new_alerts"]) == 1
    assert len(sent) == 3


def test_notify_reports_when_email_is_skipped(temp_db, monkeypatch):
    from app.database import get_connection

    sent = []
    _fake_mailer(monkeypatch, sent, status="skipped")
    with get_connection() as conn:
        _insert_campaign(conn, "Saturated Campaign", impressions=6000, reach=1000,
                         ctr=1.5, cpc=3.0, spend=2000)
        conn.commit()

    result = alert_engine.notify_ad_health_changes("Home Cartel")
    assert result["emails_sent"] == 0
    assert result["new_alerts"][0]["email_status"] == "skipped"
    assert result["new_alerts"][0]["email_detail"] == "No recipients configured"


def test_csv_upload_returns_new_alerts_and_emails(temp_db, monkeypatch):
    import io
    from fastapi.testclient import TestClient
    from app.server import app

    sent = []
    _fake_mailer(monkeypatch, sent)
    csv_text = "\n".join([
        "Campaign name,Reporting starts,Reporting ends,Campaign delivery,Ad set budget,"
        "Amount spent (PHP),Impressions,Reach,Link clicks,CPC (cost per link click) (PHP),"
        "CTR (link click-through rate),Results,Cost per results",
        "Saturated Promo,2026-10-01,2026-10-12,active,5000,2450.50,50000,10000,900,2.72,1.80,15,163.37",
        "Healthy Promo,2026-10-01,2026-10-12,active,5000,1000,12000,10000,200,5.00,1.67,5,200",
    ])
    with TestClient(app) as client:
        resp = client.post(
            "/api/upload-meta-csv",
            files={"file": ("meta_campaign_spend.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")},
        )
    assert resp.status_code == 200
    data = resp.json()
    # The seeded baseline data may add its own WATCH campaign; assert on ours.
    names = {a["campaign_name"]: a for a in data["new_alerts"]}
    assert "Healthy Promo" not in names
    assert names["Saturated Promo"]["level"] == "CRITICAL"
    assert data["emails_sent"] == len(data["new_alerts"]) == len(sent)
    critical_mail = next(m for m in sent if "Saturated Promo" in m["text"])
    assert critical_mail["recipients"] == ["monitor@x.com", "team@x.com", "owner@x.com"]
