"""
Unit tests for Meta Ads CSV Importer & Live Sync Endpoint.
Tests spend parsing, catalog parsing, auto-format detection, and FastAPI upload handler.
"""

import io
import pytest
from fastapi.testclient import TestClient

from app.server import app
from import_meta_spend import import_spend_content
from import_campaign_catalog import import_catalog_content


SAMPLE_SPEND_CSV = """Campaign name,Reporting starts,Reporting ends,Campaign delivery,Ad set budget,Amount spent (PHP),Impressions,Reach,Link clicks,CPC (cost per link click) (PHP),CTR (link click-through rate),Results,Cost per results
"Summer Promo 2026",2026-10-01,2026-10-12,active,"5,000.00","2,450.50",15200,9800,340,7.21,2.24,15,163.37
"Lighting Chandelier Sale",2026-10-01,2026-10-12,active,10000,"₱8,900.00",42000,28000,810,10.99,1.93,42,211.90
"FR Stores Promo",2026-10-01,2026-10-12,active,2000,"1,200.00",6000,4500,90,13.33,1.50,4,300.00
"""

SAMPLE_CATALOG_TSV = "Campaign ID\tCampaign Name\tCampaign Status\tCampaign Objective\tAd Set ID\tAd Set Name\tAd ID\tAd Name\tPost Click Item Headline\tLink Object ID\n120210001\tSummer Promo 2026\tACTIVE\tOUTCOME_SALES\t238510001\tBroad 25-45\t64910001\tCreative Video 1\tModern Pendant Lights\thttps://homecartel.net/products/pendant\n"


def test_import_spend_content_success(temp_db):
    res = import_spend_content(SAMPLE_SPEND_CSV)
    assert res["status"] == "success"
    assert res["type"] == "campaign_spend"
    assert res["rows_processed"] == 3
    assert res["total_spend"] > 10000
    assert res["active_campaigns"] == 3


def test_import_spend_content_empty(temp_db):
    res = import_spend_content("")
    assert res["status"] == "error"
    assert res["rows_processed"] == 0


def test_import_catalog_content_success(temp_db):
    res = import_catalog_content(SAMPLE_CATALOG_TSV)
    assert res["status"] == "success"
    assert res["type"] == "campaign_catalog"
    assert res["rows_processed"] == 1


def test_import_catalog_content_empty(temp_db):
    res = import_catalog_content("")
    assert res["status"] == "error"
    assert res["rows_processed"] == 0


def test_upload_meta_csv_endpoint_spend(temp_db):
    with TestClient(app) as client:
        file_obj = io.BytesIO(SAMPLE_SPEND_CSV.encode("utf-8"))
        resp = client.post(
            "/api/upload-meta-csv",
            files={"file": ("meta_campaign_spend.csv", file_obj, "text/csv")}
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["type"] == "campaign_spend"
    assert data["rows_processed"] == 3
    assert "alerts_summary" in data


def test_upload_meta_csv_endpoint_catalog_tsv(temp_db):
    with TestClient(app) as client:
        file_obj = io.BytesIO(SAMPLE_CATALOG_TSV.encode("utf-8"))
        resp = client.post(
            "/api/upload-meta-csv",
            files={"file": ("export_20261012.tsv", file_obj, "text/tab-separated-values")}
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["type"] == "campaign_catalog"
    assert data["rows_processed"] == 1


def test_upload_meta_csv_endpoint_empty_file(temp_db):
    with TestClient(app) as client:
        file_obj = io.BytesIO(b"")
        resp = client.post(
            "/api/upload-meta-csv",
            files={"file": ("empty.csv", file_obj, "text/csv")}
        )
    assert resp.status_code == 400


def test_upload_meta_csv_endpoint_unrecognized(temp_db):
    with TestClient(app) as client:
        file_obj = io.BytesIO(b"id,name,unknown_column\n1,test,val\n")
        resp = client.post(
            "/api/upload-meta-csv",
            files={"file": ("random.csv", file_obj, "text/csv")}
        )
    assert resp.status_code == 400
    assert "Unrecognized Meta export format" in resp.json()["detail"]


def test_dashboard_contains_import_modal(temp_db):
    with TestClient(app) as client:
        resp = client.get("/dashboard")
    assert resp.status_code == 200
    html = resp.text
    for tag in [
        "btn-open-import",
        "importModal",
        "dropZone",
        "metaFileInput",
        "fileSelectedCard",
        "btn-submit-upload",
        "openImportModal",
        "submitMetaImport",
        "Upload &amp; Sync Dashboard",
    ]:
        assert tag in html, f"Missing {tag} in dashboard html"

