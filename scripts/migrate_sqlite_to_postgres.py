"""
Migrate records from local SQLite (attribution.db) to PostgreSQL.
Usage:
    python scripts/migrate_sqlite_to_postgres.py [DATABASE_URL]
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DATABASE_PATH, BASE_DIR

def migrate():
    sqlite_path = Path(DATABASE_PATH)
    if not sqlite_path.exists():
        sqlite_path = BASE_DIR / "attribution.db"
    if not sqlite_path.exists():
        print(f"[-] SQLite database not found at {sqlite_path}")
        return

    db_url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DATABASE_URL")
    if not db_url:
        print("[-] Error: DATABASE_URL not provided and not set in environment.")
        print("    Run: python scripts/migrate_sqlite_to_postgres.py postgresql://user:pass@host:port/db")
        return

    import psycopg2
    from psycopg2.extras import execute_batch

    if db_url.startswith("postgres://"):
        db_url = "postgresql://" + db_url[len("postgres://"):]

    print(f"[*] Connecting to SQLite: {sqlite_path}")
    sq_conn = sqlite3.connect(sqlite_path)
    sq_conn.row_factory = sqlite3.Row

    print(f"[*] Connecting to PostgreSQL...")
    pg_conn = psycopg2.connect(db_url)
    pg_conn.autocommit = True

    tables_to_sync = [
        "click_logs",
        "customer_identities",
        "conversions_audit",
        "meta_campaign_catalog",
        "meta_campaign_spend",
    ]

    for table in tables_to_sync:
        try:
            sq_cursor = sq_conn.cursor()
            sq_cursor.execute(f"SELECT * FROM {table}")
            rows = [dict(r) for r in sq_cursor.fetchall()]
            if not rows:
                print(f"[-] {table}: 0 rows in SQLite, skipping.")
                continue

            cols = list(rows[0].keys())
            col_names = ", ".join(cols)
            placeholders = ", ".join(["%s"] * len(cols))

            conflict_col = "session_token" if table == "click_logs" else ("campaign_name" if table == "meta_campaign_spend" else "id")
            insert_sql = f"""
                INSERT INTO {table} ({col_names})
                VALUES ({placeholders})
                ON CONFLICT ({conflict_col}) DO NOTHING
            """

            values = [[r[c] for c in cols] for r in rows]
            with pg_conn.cursor() as pg_cursor:
                execute_batch(pg_cursor, insert_sql, values)
            print(f"[+] {table}: synced {len(rows)} rows into PostgreSQL.")
        except Exception as e:
            print(f"[!] Error syncing {table}: {e}")

    sq_conn.close()
    pg_conn.close()
    print("[+] Migration finished.")

if __name__ == "__main__":
    migrate()
