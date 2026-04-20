"""
app/order.py
============
Food Delivery App — Order Lifecycle Management
Depends on: db  (no circular imports)
"""

from app.db import get_db_connection
from datetime import datetime
import uuid


class OrderError(Exception):
    pass


def create_order(user, items):
    """Create a new order. user can be a user_id str or dict."""
    if not items:
        raise ValueError("Empty order")
    return {
        "user": user,
        "items": items,
        "status": "created",
    }


def cancel_order(order):
    return "cancelled"


def update_order(order, items):
    order["items"] = items
    return order


def place_order(user_id: str, restaurant_id: str, items: list,
                delivery_address: dict, payment_method: str = "cod") -> dict:
    """Create a full order record in the DB."""
    if not items:
        raise OrderError("Cannot place an empty order")
    db = get_db_connection()
    order_id = f"ord_{uuid.uuid4().hex[:10]}"
    order = {
        "id": order_id,
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "items": items,
        "delivery_address": delivery_address,
        "payment_method": payment_method,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }
    db["orders"][order_id] = order
    return order


def get_order(order_id: str) -> dict:
    """Fetch an order by ID."""
    db = get_db_connection()
    order = db["orders"].get(order_id)
    if not order:
        raise OrderError(f"Order {order_id} not found")
    return order


def update_order_status(order_id: str, status: str) -> dict:
    """Update the status of an order."""
    valid = {"pending", "confirmed", "preparing", "ready_for_pickup",
             "out_for_delivery", "delivered", "cancelled", "failed"}
    if status not in valid:
        raise OrderError(f"Invalid order status: {status}")
    db = get_db_connection()
    order = db["orders"].get(order_id)
    if not order:
        raise OrderError(f"Order {order_id} not found")
    order["status"] = status
    order["updated_at"] = datetime.utcnow().isoformat()
    db["orders"][order_id] = order
    return order


def get_user_orders(user_id: str) -> list:
    """Return all orders for a user, newest first."""
    db = get_db_connection()
    orders = [o for o in db["orders"].values() if o.get("user_id") == user_id]
    return sorted(orders, key=lambda o: o["created_at"], reverse=True)
