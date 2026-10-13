"""
Meta Campaign Spend Importer
Parses exported Meta Ads performance table data and saves to SQLite.
"""

import csv
import sqlite3
import os
from app.config import DATABASE_PATH

def get_db_path() -> str:
    import app.config as cfg
    return getattr(cfg, "DATABASE_PATH", DATABASE_PATH)

CSV_PATH = os.path.join(os.path.dirname(__file__), "meta_campaign_spend.csv")

def init_spend_table():
    conn = sqlite3.connect(get_db_path())
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

def _parse_float(val) -> float:
    if val is None:
        return 0.0
    s = str(val).replace(",", "").replace("PHP", "").replace("₱", "").replace("$", "").strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _parse_int(val) -> int:
    if val is None:
        return 0
    s = str(val).replace(",", "").replace("PHP", "").replace("₱", "").replace("$", "").strip()
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def import_spend_content(csv_text: str) -> dict:
    """
    Parse CSV content and upsert rows into meta_campaign_spend.
    Supports flexible column naming across Meta Ads Manager export formats.
    """
    init_spend_table()
    if not csv_text or not csv_text.strip():
        return {
            "status": "error",
            "message": "Empty CSV content",
            "rows_processed": 0,
            "total_spend": 0.0,
            "active_campaigns": 0,
        }

    import io
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        return {
            "status": "error",
            "message": "No valid CSV headers found",
            "rows_processed": 0,
            "total_spend": 0.0,
            "active_campaigns": 0,
        }

    # Normalize fieldnames map for case-insensitive lookup
    field_map = {fn.strip().lower(): fn for fn in reader.fieldnames if fn}

    def get_val(row: dict, *candidates: str):
        for cand in candidates:
            cand_l = cand.lower()
            if cand_l in field_map:
                actual_key = field_map[cand_l]
                v = row.get(actual_key)
                if v is not None and str(v).strip() != "":
                    return v
        return None

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    count = 0
    total_spent = 0.0
    active_count = 0

    for row in reader:
        cname = get_val(row, "Campaign name", "Campaign Name", "campaign_name")
        if not cname or not str(cname).strip():
            continue
        cname = str(cname).strip()

        spent = _parse_float(get_val(row, "Amount spent (PHP)", "Amount spent", "Amount Spent", "amount_spent", "Spend", "spend"))
        budget = _parse_float(get_val(row, "Ad set budget", "Budget", "budget"))
        impr = _parse_int(get_val(row, "Impressions", "impressions"))
        reach = _parse_int(get_val(row, "Reach", "reach"))
        clicks = _parse_int(get_val(row, "Link clicks", "Link Clicks", "link_clicks", "Clicks (all)"))
        cpc = _parse_float(get_val(row, "CPC (cost per link click) (PHP)", "CPC (cost per link click)", "CPC", "cpc"))
        ctr = _parse_float(get_val(row, "CTR (link click-through rate)", "CTR", "ctr"))
        results = _parse_int(get_val(row, "Results", "results"))
        cost_per_res = _parse_float(get_val(row, "Cost per results", "Cost per result", "cost_per_result"))
        raw_status = str(get_val(row, "Campaign delivery", "Delivery", "Status", "status") or "active").strip().lower()

        # If CPC or CTR was not directly calculated in export, compute it
        if cpc == 0.0 and clicks > 0 and spent > 0:
            cpc = round(spent / clicks, 2)
        if ctr == 0.0 and impr > 0 and clicks > 0:
            ctr = round((clicks / impr) * 100, 4)

        status = "inactive" if raw_status in ["inactive", "paused", "off", "completed", "deleted"] else "active"
        if status == "active":
            active_count += 1

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
            str(get_val(row, "Reporting starts", "Reporting Starts", "reporting_starts") or ""),
            str(get_val(row, "Reporting ends", "Reporting Ends", "reporting_ends") or ""),
            cname,
            status,
            budget, spent, impr, reach, clicks, cpc, ctr, results, cost_per_res
        ))
        count += 1
        total_spent += spent

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "type": "campaign_spend",
        "rows_processed": count,
        "total_spend": round(total_spent, 2),
        "active_campaigns": active_count,
        "message": f"Successfully loaded {count} campaigns. Total Ad Spend: PHP {total_spent:,.2f}"
    }


def import_spend(csv_file: str = CSV_PATH):
    if not os.path.exists(csv_file):
        print(f"[-] File not found: {csv_file}")
        return {"status": "error", "message": f"File not found: {csv_file}"}

    with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    res = import_spend_content(content)
    print(f"[+] {res.get('message')}")
    return res


if __name__ == "__main__":
    import_spend()

