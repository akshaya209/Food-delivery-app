"""
tests/test_delivery.py
======================
Tests for app/delivery.py
Dependency chain: delivery -> db, notification, analytics
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db, get_db_connection
from app.delivery import (
    assign_delivery_agent, update_delivery_status,
    get_delivery, register_delivery_agent, DeliveryError,
)


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


def test_assign_delivery_creates_record(clean):
    delivery = assign_delivery_agent(
        "ord_001",
        {"lat": 12.97, "lng": 77.59},
        {"lat": 13.00, "lng": 77.62},
    )
    assert delivery["order_id"] == "ord_001"
    assert delivery["status"] == "assigned"
    assert "id" in delivery


def test_assign_delivery_uses_registered_agent(clean):
    agent = register_delivery_agent("Raju", "+910000000099", "bike")
    delivery = assign_delivery_agent(
        "ord_002",
        {"lat": 12.97, "lng": 77.59},
        {"lat": 13.00, "lng": 77.62},
    )
    assert delivery["agent_id"] == agent["id"]


def test_update_delivery_status(clean):
    delivery = assign_delivery_agent(
        "ord_003",
        {"lat": 0, "lng": 0},
        {"lat": 0.01, "lng": 0.01},
    )
    updated = update_delivery_status(delivery["id"], "picked_up")
    assert updated["status"] == "picked_up"


def test_update_invalid_status_raises(clean):
    delivery = assign_delivery_agent(
        "ord_004",
        {"lat": 0, "lng": 0},
        {"lat": 0, "lng": 0},
    )
    with pytest.raises(DeliveryError):
        update_delivery_status(delivery["id"], "teleported")


def test_get_delivery_by_id(clean):
    delivery = assign_delivery_agent("ord_005", {"lat": 0, "lng": 0}, {"lat": 0, "lng": 0})
    fetched = get_delivery(delivery["id"])
    assert fetched["id"] == delivery["id"]


def test_get_delivery_nonexistent_raises(clean):
    with pytest.raises(DeliveryError):
        get_delivery("dlv_nonexistent")


def test_delivery_marks_agent_busy(clean):
    agent = register_delivery_agent("Priya", "+910000000098", "cycle")
    delivery = assign_delivery_agent("ord_006", {"lat": 0, "lng": 0}, {"lat": 0, "lng": 0})
    db = get_db_connection()
    assert not db["delivery_agents"][agent["id"]]["is_available"]


def test_delivery_frees_agent_on_delivered(clean):
    agent = register_delivery_agent("Suresh", "+910000000097", "bike")
    delivery = assign_delivery_agent("ord_007", {"lat": 0, "lng": 0}, {"lat": 0, "lng": 0})
    update_delivery_status(delivery["id"], "delivered")
    db = get_db_connection()
    assert db["delivery_agents"][agent["id"]]["is_available"]
