"""
Database Management (SQLite & PostgreSQL Dual Engine)
Ad-to-Sale Attribution System
Stores click logs, customer channel mappings, CAPI conversion audit records,
and persistent CSV import run & error history across GitHub pushes.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from app.config import DATABASE_PATH, DATABASE_URL, IS_POSTGRES

class PostgresCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query: str, params=None):
        # Convert SQLite ? placeholders to PostgreSQL %s placeholders
        pg_query = query.replace("?", "%s")
        if "INTEGER PRIMARY KEY AUTOINCREMENT" in pg_query:
            pg_query = pg_query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        if "INSERT OR REPLACE INTO" in pg_query:
            # Normalize to standard PostgreSQL ON CONFLICT if encountered
            pass
        if params is not None:
            return self._cursor.execute(pg_query, params)
        return self._cursor.execute(pg_query)

    def fetchone(self):
        row = self._cursor.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [dict(r) for r in rows]

    def __iter__(self):
        return iter(self._cursor)


class PostgresConnectionWrapper:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        from psycopg2.extras import RealDictCursor
        return PostgresCursorWrapper(self._conn.cursor(cursor_factory=RealDictCursor))

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self._conn.rollback()
        else:
            self._conn.commit()
        self._conn.close()


def get_connection():
    if IS_POSTGRES:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        return PostgresConnectionWrapper(conn)
    else:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass
        conn.row_factory = sqlite3.Row
        return conn


def init_db():
    """Create attribution and audit tables if they do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Click logs table (F1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS click_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_token TEXT UNIQUE NOT NULL,
                fbclid TEXT,
                fbclid_ts INTEGER,
                utm_source TEXT,
                utm_medium TEXT,
                utm_campaign TEXT,
                utm_content TEXT,
                channel TEXT NOT NULL,
                brand TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                zendesk_ticket_id INTEGER,
                landing_page TEXT,
                referrer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Schema migrations for existing databases
        for col, col_type in [
            ("landing_page", "TEXT"),
            ("referrer", "TEXT"),
            ("rfq_detected", "INTEGER DEFAULT 0"),
            ("zoho_estimate_num", "TEXT"),
            ("zoho_salesorder_id", "TEXT"),
            ("sales_amount", "REAL DEFAULT 0"),
            ("capi_status", "TEXT")
        ]:
            try:
                cursor.execute(f"ALTER TABLE click_logs ADD COLUMN {col} {col_type}")
            except Exception:
                pass

        # 2. Customer identity store (F10)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_identities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,
                identifier TEXT NOT NULL,
                session_token TEXT NOT NULL,
                brand TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(channel, identifier, brand)
            )
        """)
        
        # 3. Conversions audit log & deduplication (F8)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversions_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                salesorder_id TEXT UNIQUE NOT NULL,
                session_token TEXT,
                fbclid TEXT,
                total REAL,
                currency TEXT DEFAULT 'PHP',
                status TEXT,
                meta_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. Meta campaign spend table
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

        # 5. Meta campaign catalog table
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

        # 6. Persistent CSV Import Runs audit table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS import_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size_bytes INTEGER DEFAULT 0,
                file_hash TEXT,
                status TEXT NOT NULL,
                total_rows INTEGER DEFAULT 0,
                successful_rows INTEGER DEFAULT 0,
                failed_rows INTEGER DEFAULT 0,
                total_spend_detected REAL DEFAULT 0.0,
                error_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        # 7. Persistent CSV Import Row Errors audit table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS import_row_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                row_number INTEGER NOT NULL,
                raw_row_data TEXT,
                field_name TEXT,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# --- Click Log Operations ---

def save_click_log(payload: Dict[str, Any]) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO click_logs (
                    session_token, fbclid, fbclid_ts, utm_source, utm_medium,
                    utm_campaign, utm_content, channel, brand, status,
                    landing_page, referrer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                ON CONFLICT(session_token) DO UPDATE SET
                    fbclid = excluded.fbclid,
                    channel = excluded.channel,
                    brand = excluded.brand,
                    landing_page = excluded.landing_page,
                    referrer = excluded.referrer
            """, (
                payload.get("session_token"),
                payload.get("fbclid", ""),
                payload.get("fbclid_ts"),
                payload.get("utm_source", ""),
                payload.get("utm_medium", ""),
                payload.get("utm_campaign", ""),
                payload.get("utm_content", ""),
                payload.get("channel", "WhatsApp"),
                payload.get("brand", "Home Cartel"),
                payload.get("landing_page", ""),
                payload.get("referrer", "")
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"[-] DB Error saving click log: {e}")
            return False

def get_pending_clicks(brand: str = None, channel: str = None, minutes: int = 60) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM click_logs WHERE status = 'pending' AND created_at >= datetime('now', ?)"
        params = [f"-{minutes} minutes"]
        if brand:
            query += " AND brand = ?"
            params.append(brand)
        if channel:
            query += " AND channel = ?"
            params.append(channel)
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def mark_click_matched(session_token: str, ticket_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE click_logs 
            SET status = 'inquired', zendesk_ticket_id = ?
            WHERE session_token = ?
        """, (ticket_id, session_token))
        conn.commit()

def update_click_zendesk(session_token: str, ticket_id: int):
    mark_click_matched(session_token, ticket_id)

def update_click_rfq(session_token: str, estimate_num: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE click_logs 
            SET status = 'quoted', rfq_detected = 1, zoho_estimate_num = ?
            WHERE session_token = ?
        """, (estimate_num, session_token))
        conn.commit()

def update_click_sale(session_token: str, salesorder_id: str, amount: float, capi_status: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE click_logs 
            SET status = 'converted', zoho_salesorder_id = ?, sales_amount = ?, capi_status = ?
            WHERE session_token = ?
        """, (salesorder_id, amount, capi_status, session_token))
        conn.commit()

# --- Customer Identity Store Operations (F10) ---

def save_customer_identity(channel: str, identifier: str, session_token: str, brand: str):
    if not identifier:
        return
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customer_identities (channel, identifier, session_token, brand, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(channel, identifier, brand) DO UPDATE SET
                session_token = excluded.session_token,
                updated_at = CURRENT_TIMESTAMP
        """, (channel.lower(), identifier.strip(), session_token, brand))
        conn.commit()

def lookup_customer_session_token(channel: str, identifier: str, brand: str) -> Optional[str]:
    if not identifier:
        return None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_token FROM customer_identities
            WHERE channel = ? AND identifier = ? AND brand = ?
        """, (channel.lower(), identifier.strip(), brand))
        row = cursor.fetchone()
        return row["session_token"] if row else None

# --- Conversions Audit & Deduplication (F8) ---

def is_sales_order_processed(salesorder_id: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM conversions_audit WHERE salesorder_id = ?", (str(salesorder_id),))
        return cursor.fetchone() is not None

def log_conversion(salesorder_id: str, session_token: str, fbclid: str, total: float, status: str, meta_response: str = ""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversions_audit (
                salesorder_id, session_token, fbclid, total, currency, status, meta_response
            ) VALUES (?, ?, ?, ?, 'PHP', ?, ?)
            ON CONFLICT(salesorder_id) DO UPDATE SET
                session_token = excluded.session_token,
                fbclid = excluded.fbclid,
                total = excluded.total,
                status = excluded.status,
                meta_response = excluded.meta_response
        """, (str(salesorder_id), session_token, fbclid, total, status, meta_response))
        conn.commit()


# --- Persistent CSV Import Run & Error Operations ---

def create_import_run(run_id: str, filename: str, file_type: str, file_size_bytes: int = 0, file_hash: str = "") -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO import_runs (
                run_id, filename, file_type, file_size_bytes, file_hash, status,
                total_rows, successful_rows, failed_rows, created_at
            ) VALUES (?, ?, ?, ?, ?, 'processing', 0, 0, 0, CURRENT_TIMESTAMP)
        """, (run_id, filename, file_type, file_size_bytes, file_hash))
        conn.commit()
        return True

def finish_import_run(run_id: str, status: str, total_rows: int, successful_rows: int, failed_rows: int, total_spend: float = 0.0, error_summary: str = "") -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE import_runs SET
                status = ?,
                total_rows = ?,
                successful_rows = ?,
                failed_rows = ?,
                total_spend_detected = ?,
                error_summary = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE run_id = ?
        """, (status, total_rows, successful_rows, failed_rows, total_spend, error_summary, run_id))
        conn.commit()
        return True

def record_import_row_error(run_id: str, row_number: int, raw_row_data: str, field_name: str, error_type: str, error_message: str, conn=None) -> bool:
    if conn is not None:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO import_row_errors (
                run_id, row_number, raw_row_data, field_name, error_type, error_message, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (run_id, row_number, str(raw_row_data)[:1000], field_name, error_type, str(error_message)[:1000]))
        return True

    with get_connection() as c:
        cursor = c.cursor()
        cursor.execute("""
            INSERT INTO import_row_errors (
                run_id, row_number, raw_row_data, field_name, error_type, error_message, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (run_id, row_number, str(raw_row_data)[:1000], field_name, error_type, str(error_message)[:1000]))
        c.commit()
        return True

def get_import_history(limit: int = 50) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM import_runs ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]

def get_import_run_errors(run_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM import_row_errors WHERE run_id = ? ORDER BY row_number ASC", (run_id,))
        return [dict(r) for r in cursor.fetchall()]

