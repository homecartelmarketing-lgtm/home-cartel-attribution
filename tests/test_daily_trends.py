"""
Daily breakdown import and the week-over-week trend checks
(Creative Fatigue, Expensive Ads, Delivery Problem).
"""

import io
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.server import app
from app.services import alert_engine
from import_meta_spend import detect_report_kind, import_daily_content, import_spend_content

HEADER = (
    "Reporting starts,Reporting ends,Campaign name,Campaign delivery,"
    "Amount spent (PHP),Impressions,Reach,Link clicks\n"
)

# Campaigns are measured up to the last complete day, so build the data to end
# yesterday relative to the machine date.
END = date.today() - timedelta(days=1)


def _daily_csv(plan):
    """plan: {campaign: callable(days_ago) -> (spend, impressions, link_clicks)}; 45 days."""
    lines = [HEADER]
    for name, fn in plan.items():
        for ago in range(44, -1, -1):
            day = (END - timedelta(days=ago)).isoformat()
            spend, imp, clicks = fn(ago)
            lines.append(f'{day},{day},"{name}",active,{spend},{imp},{imp // 2},{clicks}\n')
    return "".join(lines)


def _summary_csv(names):
    lines = [
        "Reporting starts,Reporting ends,Campaign name,Campaign delivery,"
        "Amount spent (PHP),Impressions,Reach,Link clicks,CTR (link click-through rate)\n"
    ]
    for n in names:
        lines.append(f'{END - timedelta(days=44)},{END},"{n}",active,1000,10000,9000,200,2.0\n')
    return "".join(lines)


STEADY = lambda ago: (100, 5000, 100)  # 2% CTR, cpc 1.0


def test_detect_report_kind():
    daily = _daily_csv({"A": STEADY})
    assert detect_report_kind(daily) == "daily"
    assert detect_report_kind(_summary_csv(["A", "B"])) == "summary"


def test_daily_import_is_idempotent(temp_db):
    csv_text = _daily_csv({"A": STEADY, "B": STEADY})
    first = import_daily_content(csv_text)
    assert first["status"] == "success"
    assert first["rows_processed"] == 90
    assert first["campaigns"] == 2 and first["days"] == 45
    again = import_daily_content(csv_text)
    assert again["rows_processed"] == 90

    from app.database import get_connection
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM meta_campaign_daily")
        assert cur.fetchone()[0] == 90


def test_daily_import_does_not_touch_summary_table(temp_db):
    import_spend_content(_summary_csv(["A"]))
    import_daily_content(_daily_csv({"A": STEADY}))
    from app.database import get_connection
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT amount_spent FROM meta_campaign_spend WHERE campaign_name = 'A'")
        assert cur.fetchone()[0] == 1000


def _eval(plan):
    import_spend_content(_summary_csv(list(plan)))
    import_daily_content(_daily_csv(plan))
    result = alert_engine.evaluate_campaign_spend_alerts()
    return {e["campaign_name"]: e for e in result["evaluations"]}, result


def test_steady_campaign_raises_no_trend_alert(temp_db):
    evals, result = _eval({"Steady": STEADY})
    assert evals["Steady"]["alerts"] == [a for a in evals["Steady"]["alerts"] if not a.get("detail")]
    assert result["daily_window"]["trend_checks"] is True


def test_ctr_drop_fires_creative_fatigue_levels(temp_db):
    # last 7 days: clicks fall; the 7 days before stay at 100 clicks (2% CTR)
    plan = {
        "Watch": lambda ago: (100, 5000, 78 if ago < 7 else 100),     # -22%
        "Warning": lambda ago: (100, 5000, 65 if ago < 7 else 100),   # -35%
        "Critical": lambda ago: (100, 5000, 50 if ago < 7 else 100),  # -50%
    }
    evals, _ = _eval(plan)

    def fatigue(name):
        return [a for a in evals[name]["alerts"] if a["parameter"] == "Creative Fatigue"]

    assert fatigue("Watch")[0]["level"] == "WATCH"
    assert fatigue("Warning")[0]["level"] == "WARNING"
    assert fatigue("Critical")[0]["level"] == "CRITICAL"
    assert "CTR fell" in fatigue("Critical")[0]["detail"]


def test_cpc_rise_against_30_day_average(temp_db):
    # spend per click is 1.0 before the last week; 1.6 (+60%) and 1.35 (+35%) after
    plan = {
        "Pricey": lambda ago: (160, 5000, 100) if ago < 7 else (100, 5000, 100),
        "Dearer": lambda ago: (135, 5000, 100) if ago < 7 else (100, 5000, 100),
    }
    evals, _ = _eval(plan)

    def expensive(name):
        return [a for a in evals[name]["alerts"] if a["parameter"] == "Expensive Ads"]

    assert expensive("Pricey")[0]["level"] == "CRITICAL"
    assert expensive("Dearer")[0]["level"] == "WARNING"


def test_delivery_problem_needs_spend_to_hold_steady(temp_db):
    plan = {
        "Stuck": lambda ago: (100, 3000, 60) if ago < 7 else (100, 5000, 100),     # imp -40%, spend flat
        "Paused": lambda ago: (20, 3000, 60) if ago < 7 else (100, 5000, 100),     # spend -80%: not a fault
    }
    evals, _ = _eval(plan)
    stuck = [a for a in evals["Stuck"]["alerts"] if a["parameter"] == "Delivery Problem"]
    paused = [a for a in evals["Paused"]["alerts"] if a["parameter"] == "Delivery Problem"]
    assert stuck and stuck[0]["level"] == "CRITICAL"
    assert not paused


def test_today_partial_day_is_ignored(temp_db):
    # a half-finished "today" row must not look like a drop
    import_spend_content(_summary_csv(["Late"]))
    base = _daily_csv({"Late": STEADY})
    today = date.today().isoformat()
    partial = f'{today},{today},"Late",active,5,200,100,2\n'
    import_daily_content(base + partial)
    result = alert_engine.evaluate_campaign_spend_alerts()
    late = next(e for e in result["evaluations"] if e["campaign_name"] == "Late")
    assert late["trend"]["period_end"] == END.isoformat()
    assert not [a for a in late["alerts"] if a.get("detail")]


def test_no_daily_data_means_no_trend_checks(temp_db):
    import_spend_content(_summary_csv(["A"]))
    result = alert_engine.evaluate_campaign_spend_alerts()
    assert result["daily_window"]["trend_checks"] is False
    assert result["evaluations"][0]["trend"] is None


def test_upload_endpoint_routes_daily_and_summary(temp_db):
    with TestClient(app) as client:
        summary = client.post(
            "/api/upload-meta-csv",
            files={"file": ("spend.csv", io.BytesIO(_summary_csv(["A"]).encode()), "text/csv")},
        )
        daily = client.post(
            "/api/upload-meta-csv",
            files={"file": ("daily.csv", io.BytesIO(_daily_csv({"A": STEADY}).encode()), "text/csv")},
        )
    assert summary.json()["type"] == "campaign_spend"
    body = daily.json()
    assert daily.status_code == 200
    assert body["type"] == "campaign_daily"
    assert body["rows_processed"] == 45
    assert body["days"] == 45
    assert "new_alerts" in body
