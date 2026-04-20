"""
app/cart.py
===========
Food Delivery App — Shopping Cart Management
"""

from app.db import get_db_connection
from app.menu import get_menu_item, MenuItemNotFoundError
from app.user import get_user_by_id
from app.coupon import apply_coupon, CouponError
from datetime import datetime


class CartError(Exception):
    pass


def get_or_create_cart(user_id: str, restaurant_id: str) -> dict:
    """Return the user's active cart for a restaurant, or create one."""
    get_user_by_id(user_id)
    db = get_db_connection()
    cart_id = f"cart_{user_id}_{restaurant_id}"
    if cart_id not in db["carts"]:
        db["carts"][cart_id] = {
            "id": cart_id,
            "user_id": user_id,
            "restaurant_id": restaurant_id,
            "items": [],
            "coupon_code": None,
            "discount": 0.0,
            "subtotal": 0.0,
            "created_at": datetime.utcnow().isoformat(),
        }
    return db["carts"][cart_id]


def add_to_cart(user_id: str, restaurant_id: str,
                item_id: str, quantity: int = 1) -> dict:
    """Add or increment an item in the cart."""
    if quantity < 1:
        raise CartError("Quantity must be at least 1")
    item = get_menu_item(restaurant_id, item_id)
    cart = get_or_create_cart(user_id, restaurant_id)

    for line in cart["items"]:
        if line["item_id"] == item_id:
            line["quantity"] += quantity
            line["line_total"] = round(line["quantity"] * item["price"], 2)
            _recalculate(cart)
            return cart

    cart["items"].append({
        "item_id": item_id,
        "name": item["name"],
        "price": item["price"],
        "quantity": quantity,
        "line_total": round(quantity * item["price"], 2),
    })
    _recalculate(cart)
    db = get_db_connection()
    db["carts"][cart["id"]] = cart
    return cart


def remove_from_cart(user_id: str, restaurant_id: str, item_id: str) -> dict:
    """Remove a line item from the cart."""
    cart = get_or_create_cart(user_id, restaurant_id)
    cart["items"] = [l for l in cart["items"] if l["item_id"] != item_id]
    _recalculate(cart)
    db = get_db_connection()
    db["carts"][cart["id"]] = cart
    return cart


def update_cart_quantity(user_id: str, restaurant_id: str,
                         item_id: str, quantity: int) -> dict:
    """Set exact quantity for a cart line item. 0 removes it."""
    if quantity == 0:
        return remove_from_cart(user_id, restaurant_id, item_id)
    item = get_menu_item(restaurant_id, item_id)
    cart = get_or_create_cart(user_id, restaurant_id)
    for line in cart["items"]:
        if line["item_id"] == item_id:
            line["quantity"] = quantity
            line["line_total"] = round(quantity * item["price"], 2)
    _recalculate(cart)
    db = get_db_connection()
    db["carts"][cart["id"]] = cart
    return cart


def apply_coupon_to_cart(user_id: str, restaurant_id: str,
                         coupon_code: str) -> dict:
    """Validate and apply a coupon to the cart."""
    cart = get_or_create_cart(user_id, restaurant_id)
    discount = apply_coupon(coupon_code, cart["subtotal"], user_id)
    cart["coupon_code"] = coupon_code
    cart["discount"] = discount
    _recalculate(cart)
    db = get_db_connection()
    db["carts"][cart["id"]] = cart
    return cart


def clear_cart(user_id: str, restaurant_id: str) -> bool:
    """Empty the cart after order placement."""
    db = get_db_connection()
    cart_id = f"cart_{user_id}_{restaurant_id}"
    if cart_id in db["carts"]:
        del db["carts"][cart_id]
    return True


def get_cart_total(user_id: str, restaurant_id: str) -> float:
    """Return the final payable amount for the cart."""
    cart = get_or_create_cart(user_id, restaurant_id)
    return round(cart["subtotal"] - cart.get("discount", 0.0), 2)


def _recalculate(cart: dict) -> None:
    """Recompute subtotal in-place."""
    cart["subtotal"] = round(sum(l["line_total"] for l in cart["items"]), 2)
