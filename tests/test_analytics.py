"""
tests/test_analytics.py
========================
Tests for app/analytics.py
Dependency chain: analytics → db
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db, get_db_connection
from app.analytics import (
    record_event, get_events_by_type, get_revenue_summary,
    get_top_restaurants, get_order_volume_by_day,
)


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


def test_record_event_appends_to_log(clean):
    record_event("test_event", {"key": "val"})
    db = get_db_connection()
    assert len(db["analytics_events"]) == 1


def test_record_event_stores_type_and_payload(clean):
    record_event("order_placed", {"order_id": "o1", "total": 350.0})
    db = get_db_connection()
    event = db["analytics_events"][0]
    assert event["type"] == "order_placed"
    assert event["payload"]["order_id"] == "o1"


def test_record_event_adds_timestamp(clean):
    record_event("ping", {})
    db = get_db_connection()
    assert "timestamp" in db["analytics_events"][0]


def test_get_events_by_type_filters(clean):
    record_event("order_placed", {"order_id": "o1"})
    record_event("payment_success", {"payment_id": "p1"})
    record_event("order_placed", {"order_id": "o2"})
    events = get_events_by_type("order_placed")
    assert len(events) == 2
    assert all(e["type"] == "order_placed" for e in events)


def test_get_events_by_type_empty(clean):
    events = get_events_by_type("nonexistent_event")
    assert events == []


def test_get_revenue_summary_sums_correctly(clean):
    record_event("payment_success", {"payment_id": "p1", "amount": 300.0})
    record_event("payment_success", {"payment_id": "p2", "amount": 450.0})
    record_event("payment_failed", {"payment_id": "p3"})
    summary = get_revenue_summary()
    assert summary["total_revenue"] == 750.0
    assert summary["successful_payments"] == 2


def test_get_revenue_summary_empty(clean):
    summary = get_revenue_summary()
    assert summary["total_revenue"] == 0.0
    assert summary["successful_payments"] == 0


def test_get_top_restaurants_returns_sorted(clean):
    record_event("order_placed", {"restaurant_id": "rst_A", "total": 300.0})
    record_event("order_placed", {"restaurant_id": "rst_A", "total": 200.0})
    record_event("order_placed", {"restaurant_id": "rst_B", "total": 100.0})
    top = get_top_restaurants(limit=2)
    assert top[0]["restaurant_id"] == "rst_A"
    assert top[0]["order_count"] == 2


def test_get_order_volume_by_day(clean):
    record_event("order_placed", {"order_id": "o1", "restaurant_id": "r1", "total": 200.0})
    record_event("order_placed", {"order_id": "o2", "restaurant_id": "r1", "total": 300.0})
    volume = get_order_volume_by_day()
    assert isinstance(volume, dict)
    total_orders = sum(v["count"] for v in volume.values())
    assert total_orders == 2


def test_multiple_event_types_recorded_independently(clean):
    for _ in range(3):
        record_event("order_placed", {"restaurant_id": "r1", "total": 100.0})
    for _ in range(2):
        record_event("payment_success", {"amount": 100.0})
    assert len(get_events_by_type("order_placed")) == 3
    assert len(get_events_by_type("payment_success")) == 2
