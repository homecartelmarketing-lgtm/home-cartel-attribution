"""
Meta Campaign Catalog Importer
Imports campaign, ad set, and ad creative structure from Meta bulk export.
"""

import csv
import sqlite3
import os
from typing import Dict, Any

DB_PATH = "attribution.db"
CSV_PATH = "export_20261012_1519.csv"

def init_campaign_table():
    conn = sqlite3.connect(DB_PATH)
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

def import_campaign_catalog():
    init_campaign_table()
    if not os.path.exists(CSV_PATH):
        print(f"[-] CSV file not found: {CSV_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    count = 0
    with open(CSV_PATH, "r", encoding="utf-16", errors="ignore") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            cid = row.get("Campaign ID") or ""
            cname = row.get("Campaign Name") or ""
            cstatus = row.get("Campaign Status") or ""
            cobj = row.get("Campaign Objective") or ""
            asid = row.get("Ad Set ID") or ""
            asname = row.get("Ad Set Name") or ""
            adid = row.get("Ad ID") or ""
            adname = row.get("Ad Name") or ""
            headline = row.get("Post Click Item Headline") or ""
            link = row.get("Link Object ID") or ""

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
    print(f"[+] Successfully imported {count} campaigns & ads into meta_campaign_catalog table.")

if __name__ == "__main__":
    import_campaign_catalog()
