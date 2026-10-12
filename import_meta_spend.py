"""
Meta Campaign Spend Importer
Parses exported Meta Ads performance table data and saves to SQLite.
"""

import csv
import sqlite3
import os
from app.config import DATABASE_PATH

DB_PATH = DATABASE_PATH
CSV_PATH = os.path.join(os.path.dirname(__file__), "meta_campaign_spend.csv")

def init_spend_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta_campaign_spend (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporting_starts TEXT,
            reporting_ends TEXT,
            campaign_name TEXT UNIQUE NOT NULL,
            status TEXT,
            budget REAL DEFAULT 0,
            amount_spent REAL DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            reach INTEGER DEFAULT 0,
            link_clicks INTEGER DEFAULT 0,
            cpc REAL DEFAULT 0,
            ctr REAL DEFAULT 0,
            results INTEGER DEFAULT 0,
            cost_per_result REAL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def import_spend(csv_file: str = CSV_PATH):
    init_spend_table()
    if not os.path.exists(csv_file):
        print(f"[-] File not found: {csv_file}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    count = 0
    total_spent = 0.0

    with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cname = (row.get("Campaign name") or "").strip()
            if not cname:
                continue

            def parse_float(val):
                try:
                    return float(str(val).replace(",", "").strip())
                except (ValueError, TypeError):
                    return 0.0

            def parse_int(val):
                try:
                    return int(float(str(val).replace(",", "").strip()))
                except (ValueError, TypeError):
                    return 0

            spent = parse_float(row.get("Amount spent (PHP)"))
            budget = parse_float(row.get("Ad set budget"))
            impr = parse_int(row.get("Impressions"))
            reach = parse_int(row.get("Reach"))
            clicks = parse_int(row.get("Link clicks"))
            cpc = parse_float(row.get("CPC (cost per link click) (PHP)"))
            ctr = parse_float(row.get("CTR (link click-through rate)"))
            results = parse_int(row.get("Results"))
            cost_per_res = parse_float(row.get("Cost per results"))

            cursor.execute("""
                INSERT INTO meta_campaign_spend (
                    reporting_starts, reporting_ends, campaign_name, status,
                    budget, amount_spent, impressions, reach, link_clicks,
                    cpc, ctr, results, cost_per_result, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(campaign_name) DO UPDATE SET
                    reporting_starts = excluded.reporting_starts,
                    reporting_ends = excluded.reporting_ends,
                    status = excluded.status,
                    budget = excluded.budget,
                    amount_spent = excluded.amount_spent,
                    impressions = excluded.impressions,
                    reach = excluded.reach,
                    link_clicks = excluded.link_clicks,
                    cpc = excluded.cpc,
                    ctr = excluded.ctr,
                    results = excluded.results,
                    cost_per_result = excluded.cost_per_result,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                row.get("Reporting starts", ""),
                row.get("Reporting ends", ""),
                cname,
                row.get("Campaign delivery", ""),
                budget, spent, impr, reach, clicks, cpc, ctr, results, cost_per_res
            ))
            count += 1
            total_spent += spent

    conn.commit()
    conn.close()
    print(f"[+] Successfully loaded {count} campaigns. Total Ad Spend: PHP {total_spent:,.2f}")

if __name__ == "__main__":
    import_spend()
