"""
app/search.py
=============
Food Delivery App — Restaurant & Dish Search
Depends on: db  (NOT on cart/payment/delivery)
"""

from app.db import get_db_connection


class SearchError(Exception):
    pass


def search_restaurants(query: str, city: str = None) -> list:
    """Full-text search over restaurant name, cuisine, city."""
    if not query or not query.strip():
        raise SearchError("Search query cannot be empty")

    q = query.lower()
    db = get_db_connection()
    results = []
    for rest in db["restaurants"].values():
        text = " ".join([
            rest.get("name", ""),
            rest.get("cuisine", ""),
            rest.get("address", {}).get("city", ""),
        ]).lower()
        if q in text:
            if city is None or city.lower() in rest.get("address", {}).get("city", "").lower():
                results.append(rest)
    return results


def search_dishes(query: str) -> list:
    """Search menu items by name or description."""
    if not query or not query.strip():
        raise SearchError("Search query cannot be empty")

    q = query.lower()
    db = get_db_connection()
    results = []
    for restaurant_id, menu in db["menus"].items():
        for item in menu.values():
            text = " ".join([
                item.get("name", ""),
                item.get("description", ""),
                item.get("category", ""),
            ]).lower()
            if q in text:
                results.append({**item, "restaurant_id": restaurant_id})
    return results


def index_restaurant(restaurant: dict) -> bool:
    """Index a restaurant into the search index."""
    db = get_db_connection()
    rid = restaurant.get("id")
    if not rid:
        return False
    db["search_index"][f"rst_{rid}"] = {
        "type": "restaurant",
        "id": rid,
        "text": " ".join([
            restaurant.get("name", ""),
            restaurant.get("cuisine", ""),
            restaurant.get("address", {}).get("city", ""),
        ]).lower(),
    }
    return True


def index_menu_item(restaurant_id: str, item: dict) -> bool:
    """Index a menu item into the search index."""
    db = get_db_connection()
    item_id = item.get("id")
    if not item_id:
        return False
    db["search_index"][f"item_{item_id}"] = {
        "type": "menu_item",
        "id": item_id,
        "restaurant_id": restaurant_id,
        "text": " ".join([
            item.get("name", ""),
            item.get("description", ""),
            item.get("category", ""),
        ]).lower(),
    }
    return True
