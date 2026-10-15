"""
Meta Campaign Spend Importer
Parses exported Meta Ads performance table data and saves to SQLite / PostgreSQL.
Tracks persistent import runs and row-level errors across GitHub pushes.
"""

import csv
import hashlib
import json
import os
import uuid
from datetime import datetime
from typing import Optional

from app.database import (
    get_connection,
    init_db,
    create_import_run,
    finish_import_run,
    record_import_row_error,
)

CSV_PATH = os.path.join(os.path.dirname(__file__), "meta_campaign_spend.csv")

def init_spend_table():
    init_db()

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


def import_spend_content(csv_text: str, filename: str = "meta_campaign_spend.csv", run_id: Optional[str] = None) -> dict:
    """
    Parse CSV content and upsert rows into meta_campaign_spend.
    Supports flexible column naming across Meta Ads Manager export formats.
    Records audit history and row-level errors in import_runs and import_row_errors.
    """
    init_spend_table()
    run_id = run_id or f"spend_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    file_bytes = csv_text.encode("utf-8", errors="ignore") if csv_text else b""
    file_hash = hashlib.sha256(file_bytes).hexdigest() if file_bytes else ""
    file_size = len(file_bytes)

    create_import_run(run_id, filename, "campaign_spend", file_size, file_hash)

    if not csv_text or not csv_text.strip():
        finish_import_run(run_id, "failed", 0, 0, 0, 0.0, "Empty CSV content")
        return {
            "status": "error",
            "type": "campaign_spend",
            "run_id": run_id,
            "message": "Empty CSV content",
            "rows_processed": 0,
            "rows_failed": 0,
            "total_spend": 0.0,
            "active_campaigns": 0,
        }

    import io
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        finish_import_run(run_id, "failed", 0, 0, 0, 0.0, "No valid CSV headers found")
        return {
            "status": "error",
            "type": "campaign_spend",
            "run_id": run_id,
            "message": "No valid CSV headers found",
            "rows_processed": 0,
            "rows_failed": 0,
            "total_spend": 0.0,
            "active_campaigns": 0,
        }

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

    count = 0
    failed_count = 0
    total_spent = 0.0
    active_count = 0

    with get_connection() as conn:
        cursor = conn.cursor()

        for idx, row in enumerate(reader, start=2):
            try:
                cname = get_val(row, "Campaign name", "Campaign Name", "campaign_name")
                if not cname or not str(cname).strip():
                    record_import_row_error(
                        run_id, idx, json.dumps(row, ensure_ascii=False),
                        "Campaign name", "MISSING_CAMPAIGN_NAME", "Row is missing a valid Campaign Name",
                        conn=conn
                    )
                    failed_count += 1
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
            except Exception as e:
                record_import_row_error(
                    run_id, idx, json.dumps(row, ensure_ascii=False),
                    "general", "ROW_PROCESSING_EXCEPTION", str(e),
                    conn=conn
                )
                failed_count += 1

        conn.commit()

    total_rows = count + failed_count
    final_status = "completed" if failed_count == 0 and count > 0 else ("partial_failure" if count > 0 else "failed")
    summary = f"Processed {count} rows successfully, {failed_count} failed."
    finish_import_run(run_id, final_status, total_rows, count, failed_count, total_spent, summary)

    return {
        "status": "success" if count > 0 else "error",
        "type": "campaign_spend",
        "run_id": run_id,
        "rows_processed": count,
        "rows_failed": failed_count,
        "total_spend": round(total_spent, 2),
        "active_campaigns": active_count,
        "message": f"Successfully loaded {count} campaigns. Total Ad Spend: PHP {total_spent:,.2f}" if count > 0 else f"Failed to load campaigns: {failed_count} row errors."
    }


def _field_getter(fieldnames):
    field_map = {fn.strip().lower(): fn for fn in fieldnames if fn}

    def get_val(row: dict, *candidates: str):
        for cand in candidates:
            actual_key = field_map.get(cand.lower())
            if actual_key is not None:
                v = row.get(actual_key)
                if v is not None and str(v).strip() != "":
                    return v
        return None

    return get_val


def detect_report_kind(csv_text: str) -> str:
    """
    "daily" when the report has one row per campaign per day (Meta breakdown
    By Time > Day: every row starts and ends on the same date, over at least two
    dates). Anything else is the usual one-row-per-campaign summary.
    """
    import io
    try:
        reader = csv.DictReader(io.StringIO(csv_text))
        if not reader.fieldnames:
            return "summary"
        get_val = _field_getter(reader.fieldnames)
        total = 0
        same_day = 0
        days = set()
        for row in reader:
            starts = str(get_val(row, "Reporting starts", "reporting_starts", "Day") or "").strip()
            ends = str(get_val(row, "Reporting ends", "reporting_ends", "Day") or "").strip()
            if not starts:
                continue
            total += 1
            if starts == ends:
                same_day += 1
                days.add(starts)
        if total and same_day / total >= 0.9 and len(days) >= 2:
            return "daily"
    except Exception:
        pass
    return "summary"


def import_daily_content(csv_text: str, filename: str = "dailybreakdown.csv", run_id: Optional[str] = None) -> dict:
    """
    Save a daily breakdown report (one row per campaign per day) into
    meta_campaign_daily. Re-uploading the same campaign and day updates that row,
    and days that are not in the file are left alone.
    """
    import io
    init_spend_table()
    run_id = run_id or f"daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    file_bytes = csv_text.encode("utf-8", errors="ignore") if csv_text else b""
    file_hash = hashlib.sha256(file_bytes).hexdigest() if file_bytes else ""
    create_import_run(run_id, filename, "campaign_daily", len(file_bytes), file_hash)

    def fail(message: str) -> dict:
        finish_import_run(run_id, "failed", 0, 0, 0, 0.0, message)
        return {
            "status": "error", "type": "campaign_daily", "run_id": run_id, "message": message,
            "rows_processed": 0, "rows_failed": 0, "total_spend": 0.0,
            "campaigns": 0, "days": 0, "first_day": None, "last_day": None,
        }

    if not csv_text or not csv_text.strip():
        return fail("Empty CSV content")
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        return fail("No valid CSV headers found")
    get_val = _field_getter(reader.fieldnames)

    count = 0
    failed_count = 0
    total_spent = 0.0
    campaigns = set()
    days = set()

    with get_connection() as conn:
        cursor = conn.cursor()
        for idx, row in enumerate(reader, start=2):
            try:
                cname = str(get_val(row, "Campaign name", "Campaign Name", "campaign_name") or "").strip()
                day = str(get_val(row, "Reporting starts", "reporting_starts", "Day") or "").strip()
                if not cname:
                    record_import_row_error(
                        run_id, idx, json.dumps(row, ensure_ascii=False),
                        "Campaign name", "MISSING_CAMPAIGN_NAME", "Row is missing a valid Campaign Name", conn=conn
                    )
                    failed_count += 1
                    continue
                try:
                    day = datetime.strptime(day[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
                except ValueError:
                    record_import_row_error(
                        run_id, idx, json.dumps(row, ensure_ascii=False),
                        "Reporting starts", "INVALID_DATE", "Row has no valid date (expected YYYY-MM-DD)", conn=conn
                    )
                    failed_count += 1
                    continue

                spent = _parse_float(get_val(row, "Amount spent (PHP)", "Amount spent", "Amount Spent", "amount_spent", "Spend", "spend"))
                impr = _parse_int(get_val(row, "Impressions", "impressions"))
                reach = _parse_int(get_val(row, "Reach", "reach"))
                clicks = _parse_int(get_val(row, "Link clicks", "Link Clicks", "link_clicks", "Clicks (all)"))
                raw_status = str(get_val(row, "Campaign delivery", "Delivery", "Status", "status") or "active").strip().lower()
                status = "inactive" if raw_status in ["inactive", "paused", "off", "completed", "deleted"] else "active"

                cursor.execute("""
                    INSERT INTO meta_campaign_daily (
                        campaign_name, report_date, status, amount_spent, impressions, reach, link_clicks, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(campaign_name, report_date) DO UPDATE SET
                        status = excluded.status,
                        amount_spent = excluded.amount_spent,
                        impressions = excluded.impressions,
                        reach = excluded.reach,
                        link_clicks = excluded.link_clicks,
                        updated_at = CURRENT_TIMESTAMP
                """, (cname, day, status, spent, impr, reach, clicks))
                count += 1
                total_spent += spent
                campaigns.add(cname)
                days.add(day)
            except Exception as e:
                record_import_row_error(
                    run_id, idx, json.dumps(row, ensure_ascii=False),
                    "general", "ROW_PROCESSING_EXCEPTION", str(e), conn=conn
                )
                failed_count += 1
        conn.commit()

    final_status = "completed" if failed_count == 0 and count > 0 else ("partial_failure" if count > 0 else "failed")
    finish_import_run(run_id, final_status, count + failed_count, count, failed_count, total_spent,
                      f"Processed {count} daily rows successfully, {failed_count} failed.")
    first_day = min(days) if days else None
    last_day = max(days) if days else None
    return {
        "status": "success" if count > 0 else "error",
        "type": "campaign_daily",
        "run_id": run_id,
        "rows_processed": count,
        "rows_failed": failed_count,
        "total_spend": round(total_spent, 2),
        "campaigns": len(campaigns),
        "days": len(days),
        "first_day": first_day,
        "last_day": last_day,
        "message": (
            f"Successfully loaded {count} daily rows for {len(campaigns)} campaigns ({first_day} to {last_day})."
            if count > 0 else f"Failed to load daily rows: {failed_count} row errors."
        ),
    }


def import_spend(csv_file: str = CSV_PATH):
    if not os.path.exists(csv_file):
        print(f"[-] File not found: {csv_file}")
        return {"status": "error", "message": f"File not found: {csv_file}"}

    with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    res = import_spend_content(content, filename=os.path.basename(csv_file))
    print(f"[+] {res.get('message')}")
    return res


if __name__ == "__main__":
    import_spend()


