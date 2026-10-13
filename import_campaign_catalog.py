"""
Meta Campaign Catalog Importer
Imports campaign, ad set, and ad creative structure from Meta bulk export into SQLite / PostgreSQL.
Tracks persistent import runs and row-level errors across GitHub pushes.
"""

import csv
import hashlib
import io
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from app.database import (
    get_connection,
    init_db,
    create_import_run,
    finish_import_run,
    record_import_row_error,
)

CSV_PATH = "export_20261012_1519.csv"

def init_campaign_table():
    init_db()

def import_catalog_content(content: str, filename: str = "campaign_catalog.tsv", run_id: Optional[str] = None) -> Dict[str, Any]:
    """Import campaign catalog from string content with automatic delimiter detection and error audit logging."""
    init_campaign_table()
    run_id = run_id or f"catalog_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    file_bytes = content.encode("utf-8", errors="ignore") if content else b""
    file_hash = hashlib.sha256(file_bytes).hexdigest() if file_bytes else ""
    file_size = len(file_bytes)

    create_import_run(run_id, filename, "campaign_catalog", file_size, file_hash)

    if not content or not content.strip():
        finish_import_run(run_id, "failed", 0, 0, 0, 0.0, "Empty catalog content")
        return {"status": "error", "message": "Empty catalog content", "run_id": run_id, "rows_processed": 0, "rows_failed": 0}

    # Detect delimiter (\t or ,)
    first_line = content.splitlines()[0] if content.splitlines() else ""
    delimiter = "\t" if "\t" in first_line else ","

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    if not reader.fieldnames:
        finish_import_run(run_id, "failed", 0, 0, 0, 0.0, "No valid headers found in catalog export")
        return {"status": "error", "message": "No valid headers found in catalog export", "run_id": run_id, "rows_processed": 0, "rows_failed": 0}

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

    count = 0
    failed_count = 0

    with get_connection() as conn:
        cursor = conn.cursor()

        for idx, row in enumerate(reader, start=2):
            try:
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
                    record_import_row_error(
                        run_id, idx, json.dumps(row, ensure_ascii=False),
                        "Campaign ID / Ad ID", "MISSING_PRIMARY_KEYS", "Row is missing both Campaign ID and Ad ID",
                        conn=conn
                    )
                    failed_count += 1
                    continue

                cursor.execute("""
                    INSERT INTO meta_campaign_catalog (
                        campaign_id, campaign_name, campaign_status, campaign_objective,
                        adset_id, adset_name, ad_id, ad_name, headline, link_url, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(campaign_id, adset_id, ad_id) DO UPDATE SET
                        campaign_name = excluded.campaign_name,
                        campaign_status = excluded.campaign_status,
                        adset_name = excluded.adset_name,
                        ad_name = excluded.ad_name,
                        headline = excluded.headline,
                        link_url = excluded.link_url,
                        updated_at = CURRENT_TIMESTAMP
                """, (cid, cname, cstatus, cobj, asid, asname, adid, adname, headline, link))
                count += 1
            except Exception as e:
                record_import_row_error(
                    run_id, idx, json.dumps(row, ensure_ascii=False),
                    "general", "CATALOG_ROW_ERROR", str(e),
                    conn=conn
                )
                failed_count += 1

        conn.commit()

    total_rows = count + failed_count
    final_status = "completed" if failed_count == 0 and count > 0 else ("partial_failure" if count > 0 else "failed")
    summary = f"Imported {count} catalog records successfully, {failed_count} failed."
    finish_import_run(run_id, final_status, total_rows, count, failed_count, 0.0, summary)

    return {
        "status": "success" if count > 0 else "error",
        "type": "campaign_catalog",
        "run_id": run_id,
        "rows_processed": count,
        "rows_failed": failed_count,
        "message": f"Successfully imported {count} catalog records into meta_campaign_catalog." if count > 0 else f"Failed to import catalog: {failed_count} errors."
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

    res = import_catalog_content(content, filename=os.path.basename(csv_file))
    print(f"[+] {res.get('message')}")
    return res

if __name__ == "__main__":
    import_campaign_catalog()


