"""
tests/test_inventory.py
=======================
Tests for app/inventory.py
Dependency chain: inventory → db, notification
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db, get_db_connection
from app.restaurant import register_restaurant
from app.inventory import (
    initialise_inventory, set_stock, get_stock,
    decrement_stock, check_item_availability, InventoryError,
)


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def rest(clean):
    return register_restaurant(
        "Inv Resto", "owner_inv", "Chinese",
        {"street": "9 Inv Rd", "city": "Hyderabad", "pincode": "500001",
         "lat": 17.38, "lng": 78.48},
        {"open": "10:00", "close": "22:00"},
    )


def test_initialise_inventory_creates_empty_record(rest):
    inv = initialise_inventory(rest["id"])
    assert inv["restaurant_id"] == rest["id"]
    assert inv["items"] == {}


def test_set_stock_stores_quantity(rest):
    set_stock(rest["id"], "item_001", 50)
    stock = get_stock(rest["id"], "item_001")
    assert stock == 50


def test_set_stock_overwrites_previous(rest):
    set_stock(rest["id"], "item_001", 50)
    set_stock(rest["id"], "item_001", 30)
    assert get_stock(rest["id"], "item_001") == 30


def test_get_stock_zero_for_unknown_item(rest):
    stock = get_stock(rest["id"], "item_unknown")
    assert stock == 0


def test_decrement_stock_reduces_count(rest):
    set_stock(rest["id"], "item_002", 20)
    decrement_stock(rest["id"], "item_002", 5)
    assert get_stock(rest["id"], "item_002") == 15


def test_decrement_stock_below_zero_raises(rest):
    set_stock(rest["id"], "item_003", 3)
    with pytest.raises(InventoryError, match="Insufficient"):
        decrement_stock(rest["id"], "item_003", 10)


def test_check_item_availability_true_when_in_stock(rest):
    set_stock(rest["id"], "item_004", 5)
    assert check_item_availability(rest["id"], "item_004") is True


def test_check_item_availability_false_when_out_of_stock(rest):
    set_stock(rest["id"], "item_005", 0)
    assert check_item_availability(rest["id"], "item_005") is False


def test_check_item_availability_false_for_unknown(rest):
    assert check_item_availability(rest["id"], "item_ghost") is False


def test_set_stock_sends_low_stock_notification(rest):
    """Inventory should notify when stock drops to threshold."""
    set_stock(rest["id"], "item_006", 100)
    decrement_stock(rest["id"], "item_006", 97)
    db = get_db_connection()
    all_notifs = []
    for notifs in db["notifications"].values():
        all_notifs.extend(notifs)
    low_stock_notifs = [n for n in all_notifs if "stock" in n.get("type", "")]
    assert len(low_stock_notifs) >= 1


def test_inventory_initialised_on_restaurant_creation(clean):
    rest = register_restaurant(
        "Auto Inv", "owner_ai", "Mexican",
        {"street": "1 Auto", "city": "Pune", "pincode": "411001",
         "lat": 18.52, "lng": 73.86},
        {"open": "09:00", "close": "21:00"},
    )
    db = get_db_connection()
    assert rest["id"] in db["inventory"]
