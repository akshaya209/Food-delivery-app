"""
app/restaurant.py
=================
Food Delivery App — Restaurant Registration & Management
"""

from app.db import get_db_connection
from app.inventory import initialise_inventory
from app.notification import send_notification
from datetime import datetime


class RestaurantNotFoundError(Exception):
    pass


class RestaurantClosedError(Exception):
    pass


def register_restaurant(name: str, owner_id: str, cuisine: str,
                        address: dict, operating_hours: dict) -> dict:
    """Register a new restaurant on the platform."""
    db = get_db_connection()
    rid = f"rst_{len(db['restaurants']) + 1:04d}"
    restaurant = {
        "id": rid,
        "name": name,
        "owner_id": owner_id,
        "cuisine": cuisine,
        "address": address,
        "operating_hours": operating_hours,
        "rating": 0.0,
        "total_reviews": 0,
        "is_open": True,
        "is_verified": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    db["restaurants"][rid] = restaurant
    initialise_inventory(rid)
    send_notification(owner_id, "restaurant_registered", {"restaurant_id": rid})
    return restaurant


def get_restaurant(restaurant_id: str) -> dict:
    """Fetch restaurant by ID."""
    db = get_db_connection()
    r = db["restaurants"].get(restaurant_id)
    if not r:
        raise RestaurantNotFoundError(f"Restaurant {restaurant_id} not found")
    return r


def update_restaurant(restaurant_id: str, updates: dict) -> dict:
    """Update restaurant details (name, address, hours, etc.)."""
    allowed = {"name", "cuisine", "address", "operating_hours", "is_open"}
    r = get_restaurant(restaurant_id)
    for k, v in updates.items():
        if k in allowed:
            r[k] = v
    r["updated_at"] = datetime.utcnow().isoformat()
    db = get_db_connection()
    db["restaurants"][restaurant_id] = r
    return r


def list_restaurants(city: str = None, cuisine: str = None,
                     open_only: bool = True) -> list:
    """Return restaurants filtered by city and/or cuisine."""
    db = get_db_connection()
    results = list(db["restaurants"].values())
    if open_only:
        results = [r for r in results if r.get("is_open")]
    if city:
        results = [r for r in results
                   if r.get("address", {}).get("city", "").lower() == city.lower()]
    if cuisine:
        results = [r for r in results
                   if r.get("cuisine", "").lower() == cuisine.lower()]
    return results


def update_restaurant_rating(restaurant_id: str, new_rating: float,
                              total_reviews: int) -> dict:
    """Recompute and store the restaurant's average rating."""
    r = get_restaurant(restaurant_id)
    r["rating"] = round(new_rating, 2)
    r["total_reviews"] = total_reviews
    db = get_db_connection()
    db["restaurants"][restaurant_id] = r
    return r


def close_restaurant(restaurant_id: str) -> bool:
    """Temporarily close a restaurant (e.g. off-hours or emergency)."""
    r = get_restaurant(restaurant_id)
    r["is_open"] = False
    db = get_db_connection()
    db["restaurants"][restaurant_id] = r
    return True


def verify_restaurant(restaurant_id: str) -> bool:
    """Admin: mark a restaurant as verified."""
    r = get_restaurant(restaurant_id)
    r["is_verified"] = True
    db = get_db_connection()
    db["restaurants"][restaurant_id] = r
    return True
