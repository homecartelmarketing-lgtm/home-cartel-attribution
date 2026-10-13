"""
Unit tests for PostgreSQL Cursor and Row compatibility wrappers.
Ensures SQLite-style indexing (row[0]), key access (row['col']), dict(row),
and date function translations work identically under PostgreSQL emulation.
"""
from unittest.mock import MagicMock
from app.database import PostgresRow, PostgresCursorWrapper


def test_postgres_row_index_and_key_access():
    desc = [MagicMock(name="count"), MagicMock(name="total_revenue")]
    desc[0].name = "count"
    desc[1].name = "total_revenue"
    vals = (12, 45000.50)

    row = PostgresRow(desc, vals)

    # Test tuple index access (matches sqlite3.Row)
    assert row[0] == 12
    assert row[1] == 45000.50

    # Test key access
    assert row["count"] == 12
    assert row["total_revenue"] == 45000.50

    # Test dict conversion
    d = dict(row)
    assert d == {"count": 12, "total_revenue": 45000.50}

    # Test get method
    assert row.get("count") == 12
    assert row.get("missing", 0) == 0


def test_postgres_row_from_dict():
    raw_dict = {"total_clicks": 99, "ad_spend": 1234.5}
    row = PostgresRow(None, raw_dict)

    assert row[0] == 99
    assert row[1] == 1234.5
    assert row["total_clicks"] == 99
    assert row["ad_spend"] == 1234.5
    assert dict(row) == raw_dict


def test_postgres_cursor_wrapper_query_translation():
    mock_cursor = MagicMock()
    wrapper = PostgresCursorWrapper(mock_cursor)

    # Placeholders
    wrapper.execute("SELECT * FROM click_logs WHERE session_token = ? AND id = ?", ("t1", 1))
    mock_cursor.execute.assert_called_with(
        "SELECT * FROM click_logs WHERE session_token = %s AND id = %s",
        ("t1", 1)
    )

    # Primary key autoincrement
    wrapper.execute("CREATE TABLE foo (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
    mock_cursor.execute.assert_called_with("CREATE TABLE foo (id SERIAL PRIMARY KEY, name TEXT)")

    # datetime SQLite translation
    wrapper.execute("SELECT * FROM click_logs WHERE created_at >= datetime('now', '-24 hours')")
    called_sql = mock_cursor.execute.call_args[0][0]
    assert "INTERVAL '24 hours'" in called_sql
