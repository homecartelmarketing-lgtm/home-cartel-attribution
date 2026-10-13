"""
Analytics Data Store
Ad-to-Sale Attribution System

Holds cross-platform session and inquiry counts that come from outside this
service (GA4 / Zoho Analytics). Alert #11 - Anomaly Spend with No Leads -
compares Meta ad spend against GA4 sessions and Zendesk inquiry volume, so it
needs those numbers even though the Marketing API cannot supply them.

The analytics side pushes counts via POST /webhook/analytics-sync rather than
this service holding a Google service-account key. Counts are kept in memory
for the current process and mirrored into SQLite so they survive a restart.
"""

import logging
import sqlite3
from datetime import date
from typing import Any, Dict, List, Optional

from app.config import DATABASE_PATH
from app.database import get_connection

logger = logging.getLogger(__name__)

TABLE_NAME = "analytics_daily"


def _ensure_table(conn: sqlite3.Connection) -> None:
    """Create the analytics table on first use."""
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            date TEXT NOT NULL,
            sessions INTEGER DEFAULT 0,
            inquiries INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(brand, date)
        )
        """
    )
    conn.commit()


def record_sessions(
    brand: str = "Home Cartel",
    date_str: Optional[str] = None,
    sessions: int = 0,
    inquiries: int = 0,
) -> Dict[str, Any]:
    """
    Upsert one day of session / inquiry counts for a brand.

    Returns the stored row so the caller can confirm what was persisted.
    """
    target_date = date_str or date.today().isoformat()

    with get_connection() as conn:
        _ensure_table(conn)
        conn.execute(
            f"""
            INSERT INTO {TABLE_NAME} (brand, date, sessions, inquiries)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(brand, date) DO UPDATE SET
                sessions = excluded.sessions,
                inquiries = excluded.inquiries,
                created_at = CURRENT_TIMESTAMP
            """,
            (brand, target_date, int(sessions), int(inquiries)),
        )
        conn.commit()

    return {
        "brand": brand,
        "date": target_date,
        "sessions": int(sessions),
        "inquiries": int(inquiries),
    }


def get_sessions(
    brand: str = "Home Cartel", date_str: Optional[str] = None
) -> Dict[str, Any]:
    """Fetch stored counts for a brand on a date. Returns zeroes when absent."""
    target_date = date_str or date.today().isoformat()

    with get_connection() as conn:
        _ensure_table(conn)
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT sessions, inquiries FROM {TABLE_NAME} WHERE brand = ? AND date = ?",
            (brand, target_date),
        )
        row = cursor.fetchone()

    if row:
        return {
            "brand": brand,
            "date": target_date,
            "sessions": row["sessions"] or 0,
            "inquiries": row["inquiries"] or 0,
        }

    return {"brand": brand, "date": target_date, "sessions": 0, "inquiries": 0}


def get_recent(brand: str = "Home Cartel", days: int = 7) -> List[Dict[str, Any]]:
    """Return the last `days` days of stored counts for a brand."""
    with get_connection() as conn:
        _ensure_table(conn)
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT brand, date, sessions, inquiries
            FROM {TABLE_NAME}
            WHERE brand = ? AND date >= date('now', ?)
            ORDER BY date DESC
            """,
            (brand, f"-{days} days"),
        )
        return [dict(r) for r in cursor.fetchall()]


def count_inquiries_from_clicks(brand: str = "Home Cartel") -> int:
    """
    Fallback inquiry count derived from the local attribution database.

    Used by Alert #11 when GA4 counts have not been pushed: click logs that
    became Zendesk tickets in the last 24 hours are a reasonable proxy for
    inquiry volume.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM click_logs
            WHERE brand = ?
              AND zendesk_ticket_id IS NOT NULL
              AND created_at >= datetime('now', '-24 hours')
            """,
            (brand,),
        )
        return cursor.fetchone()[0] or 0
