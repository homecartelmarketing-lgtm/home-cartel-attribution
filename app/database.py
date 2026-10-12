"""
Database Management (SQLite)
Ad-to-Sale Attribution System
Stores click logs, customer channel mappings, and CAPI conversion audit records.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from app.config import DATABASE_PATH

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create attribution tables if they do not exist."""
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
            INSERT OR REPLACE INTO conversions_audit (
                salesorder_id, session_token, fbclid, total, currency, status, meta_response
            ) VALUES (?, ?, ?, ?, 'PHP', ?, ?)
        """, (str(salesorder_id), session_token, fbclid, total, status, meta_response))
        conn.commit()
