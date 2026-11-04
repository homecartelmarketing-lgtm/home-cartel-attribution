"""
Unit & integration tests for cumulative monthly ads metrics.
Validates database migration, dynamic aggregation formulas, zero-division safeguards,
and month-level summaries.
"""

import pytest
from app.database import (
    get_connection,
    init_db,
    get_cumulative_monthly_campaign_metrics,
)


def test_meta_campaign_daily_columns_exist(temp_db):
    """Verify all new metric columns exist in meta_campaign_daily table."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(meta_campaign_daily)")
        cols = {row["name"] for row in cursor.fetchall()}
        expected = {
            "campaign_name", "report_date", "status", "amount_spent",
            "impressions", "reach", "link_clicks", "clicks_all",
            "landing_page_views", "results", "cost_per_result", "cpm", "frequency"
        }
        for col in expected:
            assert col in cols, f"Column {col} missing from meta_campaign_daily"


def test_cumulative_monthly_calculation_and_formulas(temp_db):
    """
    Verify cumulative rate metrics (CPC, CTR, CPM, Cost per Result)
    are calculated using true cumulative sums and not arithmetic daily averages.
    """
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        # Insert 3 days in October 2026 for Campaign A:
        # Day 1: Spend 100, Impressions 2000, Link Clicks 40, All Clicks 60, Results 2, Reach 1500, LPV 30
        # Day 2: Spend 200, Impressions 3000, Link Clicks 60, All Clicks 90, Results 3, Reach 2200, LPV 50
        # Day 3: Spend 300, Impressions 5000, Link Clicks 100, All Clicks 150, Results 5, Reach 3500, LPV 80
        # Total: Spend 600, Impressions 10,000, Link Clicks 200, All Clicks 300, Results 10, LPV 160, Max Reach 3500
        # Expected:
        #   cpc = 600 / 200 = 3.0
        #   ctr = (200 / 10000) * 100 = 2.0%
        #   cpm = (600 / 10000) * 1000 = 60.0
        #   cpc_all = 600 / 300 = 2.0
        #   ctr_all = (300 / 10000) * 100 = 3.0%
        #   cost_per_result = 600 / 10 = 60.0
        #   cost_per_lpv = 600 / 160 = 3.75
        #   frequency = 10000 / 3500 = 2.86
        rows = [
            ("Campaign A", "2026-10-01", "active", 100.0, 2000, 1500, 40, 60, 30, 2, 50.0, 50.0, 1.33),
            ("Campaign A", "2026-10-02", "active", 200.0, 3000, 2200, 60, 90, 50, 3, 66.67, 66.67, 1.36),
            ("Campaign A", "2026-10-03", "active", 300.0, 5000, 3500, 100, 150, 80, 5, 60.0, 60.0, 1.43),
            # Campaign B in September 2026 (Different month)
            ("Campaign B", "2026-09-15", "active", 150.0, 3000, 2500, 50, 70, 40, 1, 150.0, 50.0, 1.20),
        ]
        for r in rows:
            cursor.execute("""
                INSERT INTO meta_campaign_daily (
                    campaign_name, report_date, status, amount_spent, impressions, reach,
                    link_clicks, clicks_all, landing_page_views, results, cost_per_result,
                    cpm, frequency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, r)
        conn.commit()

    # Query all months
    res_all = get_cumulative_monthly_campaign_metrics()
    assert "2026-10" in res_all["available_months"]
    assert "2026-09" in res_all["available_months"]

    # Filter to October 2026
    res_oct = get_cumulative_monthly_campaign_metrics(month="2026-10")
    assert res_oct["selected_month"] == "2026-10"
    assert len(res_oct["campaigns"]) == 1

    camp_a = res_oct["campaigns"][0]
    assert camp_a["campaign_name"] == "Campaign A"
    assert camp_a["report_month"] == "2026-10"
    assert camp_a["days_active"] == 3
    assert camp_a["total_spend"] == 600.0
    assert camp_a["total_impressions"] == 10000
    assert camp_a["total_link_clicks"] == 200
    assert camp_a["total_clicks_all"] == 300
    assert camp_a["total_results"] == 10
    assert camp_a["total_landing_page_views"] == 160
    assert camp_a["cpc"] == 3.0
    assert camp_a["ctr"] == 2.0
    assert camp_a["cpm"] == 60.0
    assert camp_a["cpc_all"] == 2.0
    assert camp_a["ctr_all"] == 3.0
    assert camp_a["cost_per_result"] == 60.0
    assert camp_a["cost_per_lpv"] == 3.75
    assert camp_a["frequency"] == 2.86

    # Test summary totals for October
    summary = res_oct["summary"]
    assert summary["total_spend"] == 600.0
    assert summary["total_impressions"] == 10000
    assert summary["total_link_clicks"] == 200
    assert summary["blended_cpc"] == 3.0
    assert summary["blended_ctr"] == 2.0
    assert summary["blended_cpm"] == 60.0
    assert summary["total_results"] == 10
    assert summary["blended_cost_per_result"] == 60.0


def test_zero_division_safeguards(temp_db):
    """Verify zero division is safely handled when clicks or impressions are 0."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO meta_campaign_daily (
                campaign_name, report_date, status, amount_spent, impressions, reach,
                link_clicks, clicks_all, landing_page_views, results, cost_per_result,
                cpm, frequency
            ) VALUES ('Zero Clicks Campaign', '2026-10-10', 'active', 250.0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        """)
        conn.commit()

    res = get_cumulative_monthly_campaign_metrics(month="2026-10")
    assert len(res["campaigns"]) == 1
    c = res["campaigns"][0]
    assert c["total_spend"] == 250.0
    assert c["cpc"] == 0.0
    assert c["ctr"] == 0.0
    assert c["cpm"] == 0.0
    assert c["cost_per_result"] == 0.0


def test_daily_import_parses_all_metrics(temp_db):
    """Verify import_daily_content parses all rich columns into meta_campaign_daily."""
    from import_meta_spend import import_daily_content
    csv_content = (
        '"Reporting starts","Reporting ends","Campaign name","Campaign delivery","Amount spent (PHP)",'
        '"Impressions","Reach","Link clicks","Clicks (all)","Landing page views","Results","Cost per results",'
        '"CPM (cost per 1,000 impressions) (PHP)","Frequency"\n'
        '2026-10-15,2026-10-15,"Broad Sales",active,500.0,10000,8000,200,300,150,5,100.0,50.0,1.25\n'
    )
    res = import_daily_content(csv_content)
    assert res["status"] == "success"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meta_campaign_daily WHERE campaign_name = 'Broad Sales'")
        row = cursor.fetchone()
        assert row is not None
        assert row["amount_spent"] == 500.0
        assert row["impressions"] == 10000
        assert row["reach"] == 8000
        assert row["link_clicks"] == 200
        assert row["clicks_all"] == 300
        assert row["landing_page_views"] == 150
        assert row["results"] == 5
        assert row["cost_per_result"] == 100.0
        assert row["cpm"] == 50.0
        assert row["frequency"] == 1.25


def test_api_campaigns_monthly_endpoint(temp_db):
    """Verify GET /api/campaigns/monthly endpoint returns monthly cumulative metrics."""
    from fastapi.testclient import TestClient
    from app.server import app
    from import_meta_spend import import_daily_content

    csv_content = (
        '"Reporting starts","Reporting ends","Campaign name","Campaign delivery","Amount spent (PHP)",'
        '"Impressions","Reach","Link clicks","Clicks (all)","Landing page views","Results","Cost per results",'
        '"CPM (cost per 1,000 impressions) (PHP)","Frequency"\n'
        '2026-10-15,2026-10-15,"Broad Sales",active,500.0,10000,8000,200,300,150,5,100.0,50.0,1.25\n'
    )
    import_daily_content(csv_content)

    with TestClient(app) as client:
        resp = client.get("/api/campaigns/monthly?month=2026-10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["selected_month"] == "2026-10"
        assert len(data["campaigns"]) >= 1
        broad_sales = next((c for c in data["campaigns"] if c["campaign_name"] == "Broad Sales"), None)
        assert broad_sales is not None
        assert broad_sales["cpc"] == 2.5
        assert broad_sales["ctr"] == 2.0


def test_dashboard_renders_monthly_panel(temp_db):
    """Verify /dashboard HTML contains the Monthly Cumulative Ads view panel and controls."""
    from fastapi.testclient import TestClient
    from app.server import app

    with TestClient(app) as client:
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        html = resp.text
        assert 'id="panel-v-monthly"' in html
        assert 'id="monthly-selector"' in html
        assert 'id="monthly-table-body"' in html
        assert 'Monthly Cumulative Ads Performance' in html
        assert 'exportMonthlyMetricsCsv' in html
