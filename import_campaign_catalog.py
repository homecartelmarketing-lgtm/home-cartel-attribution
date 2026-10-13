"""
Meta Campaign Catalog Importer
Imports campaign, ad set, and ad creative structure from Meta bulk export.
"""

import csv
import io
import sqlite3
import os
from typing import Dict, Any
from app.config import DATABASE_PATH

def get_db_path() -> str:
    import app.config as cfg
    return getattr(cfg, "DATABASE_PATH", DATABASE_PATH)

CSV_PATH = "export_20261012_1519.csv"

def init_campaign_table():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta_campaign_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id TEXT,
            campaign_name TEXT,
            campaign_status TEXT,
            campaign_objective TEXT,
            adset_id TEXT,
            adset_name TEXT,
            ad_id TEXT,
            ad_name TEXT,
            headline TEXT,
            link_url TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(campaign_id, adset_id, ad_id)
        )
    """)
    conn.commit()
    conn.close()

def import_catalog_content(content: str) -> Dict[str, Any]:
    """Import campaign catalog from string content with automatic delimiter detection."""
    init_campaign_table()
    if not content or not content.strip():
        return {"status": "error", "message": "Empty catalog content", "rows_processed": 0}

    # Detect delimiter (\t or ,)
    first_line = content.splitlines()[0] if content.splitlines() else ""
    delimiter = "\t" if "\t" in first_line else ","

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    if not reader.fieldnames:
        return {"status": "error", "message": "No valid headers found in catalog export", "rows_processed": 0}

    field_map = {fn.strip().lower(): fn for fn in reader.fieldnames if fn}

    def get_val(row: dict, *candidates: str):
        for cand in candidates:
            cand_l = cand.lower()
            if cand_l in field_map:
                actual_key = field_map[cand_l]
                v = row.get(actual_key)
                if v is not None and str(v).strip() != "":
                    return str(v).strip()
        return ""

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    count = 0

    for row in reader:
        cid = get_val(row, "Campaign ID", "campaign_id", "Campaign id")
        cname = get_val(row, "Campaign Name", "campaign_name", "Campaign name")
        cstatus = get_val(row, "Campaign Status", "campaign_status", "Status")
        cobj = get_val(row, "Campaign Objective", "campaign_objective", "Objective")
        asid = get_val(row, "Ad Set ID", "adset_id", "Ad set id")
        asname = get_val(row, "Ad Set Name", "adset_name", "Ad set name")
        adid = get_val(row, "Ad ID", "ad_id", "Ad id")
        adname = get_val(row, "Ad Name", "ad_name", "Ad name")
        headline = get_val(row, "Post Click Item Headline", "Headline", "headline")
        link = get_val(row, "Link Object ID", "link_url", "Link URL")

        if not cid and not adid:
            continue

        cursor.execute("""
            INSERT INTO meta_campaign_catalog (
                campaign_id, campaign_name, campaign_status, campaign_objective,
                adset_id, adset_name, ad_id, ad_name, headline, link_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(campaign_id, adset_id, ad_id) DO UPDATE SET
                campaign_name = excluded.campaign_name,
                campaign_status = excluded.campaign_status,
                adset_name = excluded.adset_name,
                ad_name = excluded.ad_name,
                headline = excluded.headline
        """, (cid, cname, cstatus, cobj, asid, asname, adid, adname, headline, link))
        count += 1

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "type": "campaign_catalog",
        "rows_processed": count,
        "message": f"Successfully imported {count} catalog records into meta_campaign_catalog."
    }

def import_campaign_catalog(csv_file: str = CSV_PATH):
    if not os.path.exists(csv_file):
        print(f"[-] CSV file not found: {csv_file}")
        return {"status": "error", "message": f"File not found: {csv_file}"}

    # Meta bulk exports often use utf-16 with BOM or utf-8
    content = ""
    for enc in ["utf-16", "utf-8", "latin-1"]:
        try:
            with open(csv_file, "r", encoding=enc, errors="ignore") as f:
                content = f.read()
            if "Campaign" in content:
                break
        except Exception:
            continue

    res = import_catalog_content(content)
    print(f"[+] {res.get('message')}")
    return res

if __name__ == "__main__":
    import_campaign_catalog()

