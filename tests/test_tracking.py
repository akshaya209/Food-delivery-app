"""
tests/test_tracking.py
======================
Tests for app/tracking.py
Dependency chain: tracking -> delivery, order, notification, db
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db, get_db_connection
from app.order import place_order
from app.delivery import assign_delivery_agent
from app.tracking import (
    get_order_tracking, update_agent_location,
    mark_order_picked_up, mark_order_delivered,
)


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def live_delivery(clean):
    order = place_order(
        "usr_001", "rst_001",
        [{"name": "Pizza", "price": 200.0}],
        {"street": "1 Main", "city": "Delhi", "pincode": "110001",
         "lat": 28.6, "lng": 77.2},
    )
    delivery = assign_delivery_agent(
        order["id"],
        {"lat": 28.61, "lng": 77.21},
        {"lat": 28.6, "lng": 77.2},
    )
    return {"order": order, "delivery": delivery}


def test_get_order_tracking_returns_snapshot(live_delivery):
    tracking = get_order_tracking(live_delivery["order"]["id"])
    assert tracking["order_id"] == live_delivery["order"]["id"]
    assert "delivery" in tracking
    assert "timeline" in tracking


def test_update_agent_location(live_delivery):
    delivery = update_agent_location(live_delivery["delivery"]["id"], 28.62, 77.22)
    assert delivery["current_location"]["lat"] == 28.62
    assert delivery["current_location"]["lng"] == 77.22


def test_mark_order_picked_up(live_delivery):
    delivery = mark_order_picked_up(live_delivery["delivery"]["id"])
    assert delivery["status"] == "picked_up"


def test_mark_order_delivered(live_delivery):
    mark_order_picked_up(live_delivery["delivery"]["id"])
    delivery = mark_order_delivered(live_delivery["delivery"]["id"])
    assert delivery["status"] == "delivered"


def test_tracking_timeline_has_steps(live_delivery):
    tracking = get_order_tracking(live_delivery["order"]["id"])
    assert len(tracking["timeline"]) >= 3
