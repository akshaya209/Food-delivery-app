"""
tests/test_db.py
================
Tests for app/db_utils.py
Dependency chain: db_utils (standalone, no app imports)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db_utils import format_query, build_insert_query, paginate, sanitize_string


def test_query_generation():
    expected = "SELECT * FROM users WHERE id = 101;"
    assert format_query("users", 101) == expected


def test_build_insert_query():
    q = build_insert_query("orders", {"user_id": "u1", "total": 300})
    assert "INSERT INTO orders" in q
    assert "user_id" in q


def test_paginate_first_page():
    items = list(range(25))
    result = paginate(items, page=1, page_size=10)
    assert result["items"] == list(range(10))
    assert result["total_pages"] == 3


def test_paginate_last_page():
    items = list(range(25))
    result = paginate(items, page=3, page_size=10)
    assert result["items"] == [20, 21, 22, 23, 24]


def test_sanitize_string_removes_sql_chars():
    dirty = "'; DROP TABLE users; --"
    clean = sanitize_string(dirty)
    assert "'" not in clean
    assert ";" not in clean
    assert "--" not in clean
