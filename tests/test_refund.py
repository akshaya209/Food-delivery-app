"""
tests/test_refund.py
====================
Tests for app/refund.py
Dependency chain: refund → db, notification, analytics
Also exercises: payment → refund (integration path)
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db, get_db_connection
from app.user import create_user
from app.restaurant import register_restaurant
from app.inventory import set_stock
from app.menu import add_menu_item
from app.cart import add_to_cart
from app.payment import initiate_payment, process_payment
from app.refund import (
    create_refund, get_refund, process_refund,
    list_refunds_for_payment, RefundError,
)


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def paid_payment(clean):
    user = create_user("refund@test.com", "Refunder", "+910000000020", "pass1234")
    rest = register_restaurant(
        "Refund Resto", "owner_r", "Italian",
        {"street": "1 Refund St", "city": "Delhi", "pincode": "110001", "lat": 28.6, "lng": 77.2},
        {"open": "10:00", "close": "22:00"},
    )
    item = add_menu_item(rest["id"], {
        "name": "Pasta", "price": 200.0, "category": "Main", "description": "Al dente pasta",
    })
    set_stock(rest["id"], item["id"], 20)
    add_to_cart(user["id"], rest["id"], item["id"], quantity=1)
    payment = initiate_payment(user["id"], rest["id"], "upi")
    processed = process_payment(payment["id"])
    return {"payment": processed, "user": user}


def test_create_refund_record(paid_payment):
    refund = create_refund(paid_payment["payment"]["id"], 200.0, "Item not delivered")
    assert refund["payment_id"] == paid_payment["payment"]["id"]
    assert refund["amount"] == 200.0
    assert refund["status"] == "pending"
    assert refund["reason"] == "Item not delivered"


def test_create_refund_stores_in_db(paid_payment):
    refund = create_refund(paid_payment["payment"]["id"], 200.0, "Wrong order")
    db = get_db_connection()
    assert refund["id"] in db["refunds"]


def test_get_refund_returns_record(paid_payment):
    refund = create_refund(paid_payment["payment"]["id"], 200.0, "Test")
    fetched = get_refund(refund["id"])
    assert fetched["id"] == refund["id"]


def test_get_refund_nonexistent_raises(paid_payment):
    with pytest.raises(RefundError):
        get_refund("rfnd_nonexistent")


def test_process_refund_marks_completed(paid_payment):
    refund = create_refund(paid_payment["payment"]["id"], 200.0, "Test")
    processed = process_refund(refund["id"])
    assert processed["status"] == "completed"
    assert "processed_at" in processed


def test_process_refund_sends_notification(paid_payment):
    refund = create_refund(paid_payment["payment"]["id"], 200.0, "Test")
    process_refund(refund["id"])
    db = get_db_connection()
    uid = paid_payment["user"]["id"]
    types = [n["type"] for n in db["notifications"].get(uid, [])]
    assert "refund_initiated" in types or "refund_completed" in types


def test_process_refund_already_processed_raises(paid_payment):
    refund = create_refund(paid_payment["payment"]["id"], 200.0, "Test")
    process_refund(refund["id"])
    with pytest.raises(RefundError, match="already"):
        process_refund(refund["id"])


def test_list_refunds_for_payment(paid_payment):
    pid = paid_payment["payment"]["id"]
    create_refund(pid, 100.0, "Partial refund")
    refunds = list_refunds_for_payment(pid)
    assert len(refunds) >= 1
    assert all(r["payment_id"] == pid for r in refunds)


def test_refund_amount_cannot_exceed_payment(paid_payment):
    with pytest.raises(RefundError, match="exceed"):
        create_refund(paid_payment["payment"]["id"], 99999.0, "Greedy")


def test_refund_records_analytics_event(paid_payment):
    refund = create_refund(paid_payment["payment"]["id"], 200.0, "Test")
    process_refund(refund["id"])
    db = get_db_connection()
    events = [e["type"] for e in db["analytics_events"]]
    assert any("refund" in e for e in events)
