"""
tests/test_cart.py
==================
Tests for app/cart.py
Dependency chain: cart -> db, menu, user, coupon
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db
from app.user import create_user
from app.restaurant import register_restaurant
from app.inventory import set_stock
from app.menu import add_menu_item
from app.cart import (
    add_to_cart, remove_from_cart, get_or_create_cart,
    update_cart_quantity, get_cart_total, clear_cart, CartError,
)


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def setup(clean):
    user = create_user("cart@test.com", "Cart User", "+910000000002", "pass1234")
    rest = register_restaurant(
        "Cart Resto", "owner_c", "Indian",
        {"street": "1 Cart St", "city": "Mumbai", "pincode": "400001",
         "lat": 19.07, "lng": 72.87},
        {"open": "10:00", "close": "22:00"},
    )
    item = add_menu_item(rest["id"], {
        "name": "Paneer Tikka", "price": 150.0,
        "category": "Starter", "description": "Grilled paneer",
    })
    set_stock(rest["id"], item["id"], 20)
    return {"user": user, "rest": rest, "item": item}


def test_add_to_cart_creates_cart(setup):
    cart = add_to_cart(setup["user"]["id"], setup["rest"]["id"],
                       setup["item"]["id"], quantity=2)
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 2


def test_add_to_cart_increments_existing(setup):
    add_to_cart(setup["user"]["id"], setup["rest"]["id"], setup["item"]["id"], 1)
    cart = add_to_cart(setup["user"]["id"], setup["rest"]["id"], setup["item"]["id"], 2)
    assert cart["items"][0]["quantity"] == 3


def test_cart_subtotal_calculated(setup):
    cart = add_to_cart(setup["user"]["id"], setup["rest"]["id"],
                       setup["item"]["id"], quantity=3)
    assert cart["subtotal"] == 450.0


def test_remove_from_cart(setup):
    add_to_cart(setup["user"]["id"], setup["rest"]["id"], setup["item"]["id"])
    cart = remove_from_cart(setup["user"]["id"], setup["rest"]["id"], setup["item"]["id"])
    assert cart["items"] == []


def test_get_cart_total(setup):
    add_to_cart(setup["user"]["id"], setup["rest"]["id"], setup["item"]["id"], 2)
    total = get_cart_total(setup["user"]["id"], setup["rest"]["id"])
    assert total == 300.0


def test_add_zero_quantity_raises(setup):
    with pytest.raises(CartError):
        add_to_cart(setup["user"]["id"], setup["rest"]["id"],
                    setup["item"]["id"], quantity=0)


def test_update_quantity_to_zero_removes_item(setup):
    add_to_cart(setup["user"]["id"], setup["rest"]["id"], setup["item"]["id"], 3)
    cart = update_cart_quantity(setup["user"]["id"], setup["rest"]["id"],
                                setup["item"]["id"], 0)
    assert cart["items"] == []


def test_clear_cart(setup):
    add_to_cart(setup["user"]["id"], setup["rest"]["id"], setup["item"]["id"])
    result = clear_cart(setup["user"]["id"], setup["rest"]["id"])
    assert result is True
