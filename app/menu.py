"""
app/menu.py
===========
Food Delivery App — Menu & Item Management
"""

from app.db import get_db_connection
from app.restaurant import get_restaurant, RestaurantNotFoundError
from app.inventory import check_item_availability
from datetime import datetime


class MenuItemNotFoundError(Exception):
    pass


def add_menu_item(restaurant_id: str, item: dict) -> dict:
    """Add an item to a restaurant's menu."""
    get_restaurant(restaurant_id)  # validates restaurant exists
    required = {"name", "price", "category", "description"}
    if not required.issubset(item.keys()):
        raise ValueError(f"Menu item missing required fields: {required - item.keys()}")

    db = get_db_connection()
    menu = db["menus"].setdefault(restaurant_id, {})
    item_id = f"item_{restaurant_id}_{len(menu) + 1:04d}"
    item = {
        **item,
        "id": item_id,
        "restaurant_id": restaurant_id,
        "is_available": True,
        "created_at": datetime.utcnow().isoformat(),
    }
    menu[item_id] = item
    return item


def get_menu(restaurant_id: str, category: str = None) -> list:
    """Return all menu items for a restaurant, optionally filtered by category."""
    get_restaurant(restaurant_id)
    db = get_db_connection()
    items = list(db["menus"].get(restaurant_id, {}).values())
    if category:
        items = [i for i in items if i.get("category", "").lower() == category.lower()]
    # Filter out items with no stock
    available = []
    for item in items:
        if item.get("is_available") and check_item_availability(restaurant_id, item["id"]):
            available.append(item)
    return available


def get_menu_item(restaurant_id: str, item_id: str) -> dict:
    """Fetch a single menu item."""
    db = get_db_connection()
    item = db["menus"].get(restaurant_id, {}).get(item_id)
    if not item:
        raise MenuItemNotFoundError(f"Item {item_id} not found in {restaurant_id}")
    return item


def update_menu_item(restaurant_id: str, item_id: str, updates: dict) -> dict:
    """Update price, description, or availability of a menu item."""
    item = get_menu_item(restaurant_id, item_id)
    allowed = {"name", "price", "description", "is_available", "category", "image_url"}
    for k, v in updates.items():
        if k in allowed:
            item[k] = v
    item["updated_at"] = datetime.utcnow().isoformat()
    db = get_db_connection()
    db["menus"][restaurant_id][item_id] = item
    return item


def remove_menu_item(restaurant_id: str, item_id: str) -> bool:
    """Remove a menu item permanently."""
    db = get_db_connection()
    menu = db["menus"].get(restaurant_id, {})
    if item_id not in menu:
        raise MenuItemNotFoundError(f"Item {item_id} not in {restaurant_id}")
    del menu[item_id]
    return True


def get_all_categories(restaurant_id: str) -> list:
    """Return distinct categories offered by a restaurant."""
    db = get_db_connection()
    items = db["menus"].get(restaurant_id, {}).values()
    return list({i["category"] for i in items if "category" in i})
