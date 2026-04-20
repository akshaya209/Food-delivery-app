"""
app/inventory.py
================
Food Delivery App — Stock & Inventory Management
Depends on: db, notification  (NOT on menu/cart/order)
"""

from app.db import get_db_connection
from datetime import datetime

LOW_STOCK_THRESHOLD = 5  # notify when stock drops at or below this


class InventoryError(Exception):
    pass


def initialise_inventory(restaurant_id: str) -> dict:
    """Create an empty inventory record for a restaurant."""
    db = get_db_connection()
    inv = {
        "restaurant_id": restaurant_id,
        "items": {},
        "created_at": datetime.utcnow().isoformat(),
    }
    db["inventory"][restaurant_id] = inv
    return inv


def _get_or_init(restaurant_id: str) -> dict:
    db = get_db_connection()
    if restaurant_id not in db["inventory"]:
        initialise_inventory(restaurant_id)
    return db["inventory"][restaurant_id]


def set_stock(restaurant_id: str, item_id: str, quantity: int) -> dict:
    """Set absolute stock quantity for an item."""
    inv = _get_or_init(restaurant_id)
    inv["items"][item_id] = {
        "quantity": quantity,
        "updated_at": datetime.utcnow().isoformat(),
    }
    db = get_db_connection()
    db["inventory"][restaurant_id] = inv
    return inv


def get_stock(restaurant_id: str, item_id: str) -> int:
    """Return current stock count for an item (0 if unknown)."""
    inv = _get_or_init(restaurant_id)
    entry = inv["items"].get(item_id)
    return entry["quantity"] if entry else 0


def decrement_stock(restaurant_id: str, item_id: str, quantity: int) -> int:
    """Reduce stock by quantity.  Raises InventoryError if stock would go negative."""
    current = get_stock(restaurant_id, item_id)
    if current < quantity:
        raise InventoryError(
            f"Insufficient stock for {item_id}: have {current}, requested {quantity}"
        )
    new_qty = current - quantity
    set_stock(restaurant_id, item_id, new_qty)

    # Low-stock notification
    if new_qty <= LOW_STOCK_THRESHOLD:
        _send_low_stock_notification(restaurant_id, item_id, new_qty)

    return new_qty


def check_item_availability(restaurant_id: str, item_id: str) -> bool:
    """Return True if item has stock > 0."""
    return get_stock(restaurant_id, item_id) > 0


def _send_low_stock_notification(restaurant_id: str, item_id: str, qty: int) -> None:
    """Store a low-stock notification record in the DB."""
    db = get_db_connection()
    import uuid
    notif_id = f"ntf_{uuid.uuid4().hex[:8]}"
    notif = {
        "id": notif_id,
        "recipient_id": restaurant_id,
        "type": "low_stock",
        "body": f"Low stock alert: item {item_id} has {qty} remaining.",
        "is_read": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    db["notifications"].setdefault(restaurant_id, []).append(notif)
