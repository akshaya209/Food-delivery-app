"""
tests/test_payment.py
=====================
Tests for app/payment.py
Dependency chain: payment -> cart, user, notification, analytics, db
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db
from app.user import create_user
from app.restaurant import register_restaurant
from app.inventory import set_stock
from app.menu import add_menu_item
from app.cart import add_to_cart
from app.payment import (
    initiate_payment, process_payment, get_payment,
    get_user_payment_history, validate_card, PaymentError,
)


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def pending(clean):
    user = create_user("pay@test.com", "Payer", "+910000000003", "pass1234")
    rest = register_restaurant(
        "Pay Resto", "owner_p", "Italian",
        {"street": "1 Pay St", "city": "Bengaluru", "pincode": "560001",
         "lat": 12.97, "lng": 77.59},
        {"open": "10:00", "close": "22:00"},
    )
    item = add_menu_item(rest["id"], {
        "name": "Margherita", "price": 250.0,
        "category": "Pizza", "description": "Classic pizza",
    })
    set_stock(rest["id"], item["id"], 10)
    add_to_cart(user["id"], rest["id"], item["id"], quantity=1)
    payment = initiate_payment(user["id"], rest["id"], "upi")
    return {"user": user, "rest": rest, "payment": payment}


def test_initiate_payment_creates_record(pending):
    p = pending["payment"]
    assert p["status"] == "pending"
    assert p["amount"] == 250.0
    assert p["method"] == "upi"


def test_process_payment_succeeds(pending):
    processed = process_payment(pending["payment"]["id"])
    assert processed["status"] == "success"


def test_process_payment_clears_cart(pending):
    process_payment(pending["payment"]["id"])
    from app.cart import get_or_create_cart
    cart = get_or_create_cart(pending["user"]["id"], pending["rest"]["id"])
    assert cart["items"] == []


def test_process_payment_idempotent_raises(pending):
    process_payment(pending["payment"]["id"])
    with pytest.raises(PaymentError):
        process_payment(pending["payment"]["id"])


def test_get_payment_by_id(pending):
    fetched = get_payment(pending["payment"]["id"])
    assert fetched["id"] == pending["payment"]["id"]


def test_get_payment_nonexistent_raises(clean):
    with pytest.raises(PaymentError):
        get_payment("pay_nonexistent")


def test_unsupported_method_raises(clean):
    user = create_user("m@test.com", "M", "+910000000004", "pass1234")
    rest = register_restaurant(
        "R", "o", "Indian",
        {"street": "x", "city": "y", "pincode": "100001", "lat": 0, "lng": 0},
        {"open": "08:00", "close": "20:00"},
    )
    item = add_menu_item(rest["id"], {"name": "X", "price": 100.0,
                                      "category": "C", "description": "D"})
    set_stock(rest["id"], item["id"], 5)
    add_to_cart(user["id"], rest["id"], item["id"])
    with pytest.raises(PaymentError, match="Unsupported"):
        initiate_payment(user["id"], rest["id"], "bitcoin")


def test_validate_card_valid():
    assert validate_card("4111111111111111", "12/26", "123") is True


def test_validate_card_invalid():
    assert validate_card("1234567890123456", "12/26", "999") is False


def test_payment_history(pending):
    process_payment(pending["payment"]["id"])
    history = get_user_payment_history(pending["user"]["id"])
    assert len(history) >= 1
