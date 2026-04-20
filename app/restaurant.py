"""
app/restaurant.py
=================
Food Delivery App — Restaurant Registration & Management
Depends on: db, notification, inventory  (NOT on cart/order/payment)
"""

from app.db import get_db_connection
from datetime import datetime
import uuid


class RestaurantNotFoundError(Exception):
    pass


class RestaurantError(Exception):
    pass


def register_restaurant(
    name: str,
    owner_id: str,
    cuisine: str,
    address: dict,
    hours: dict,
) -> dict:
    """Register a new restaurant and initialise its inventory."""
    required_addr = {"street", "city", "pincode", "lat", "lng"}
    if not required_addr.issubset(address.keys()):
        raise RestaurantError(
            f"Address missing fields: {required_addr - address.keys()}"
        )

    db = get_db_connection()
    restaurant_id = f"rst_{uuid.uuid4().hex[:8]}"
    restaurant = {
        "id": restaurant_id,
        "name": name,
        "owner_id": owner_id,
        "cuisine": cuisine,
        "address": address,
        "hours": hours,
        "is_open": True,
        "rating": 0.0,
        "total_reviews": 0,
        "created_at": datetime.utcnow().isoformat(),
    }
    db["restaurants"][restaurant_id] = restaurant

    # Initialise empty inventory for this restaurant
    from app.inventory import initialise_inventory
    initialise_inventory(restaurant_id)

    # Notify owner
    from app.notification import send_notification
    send_notification(owner_id, "restaurant_registered",
                      {"restaurant_id": restaurant_id})

    return restaurant


def get_restaurant(restaurant_id: str) -> dict:
    """Fetch restaurant by ID."""
    db = get_db_connection()
    rest = db["restaurants"].get(restaurant_id)
    if not rest:
        raise RestaurantNotFoundError(f"Restaurant {restaurant_id} not found")
    return rest


def update_restaurant(restaurant_id: str, updates: dict) -> dict:
    """Update mutable restaurant fields."""
    allowed = {"name", "cuisine", "address", "hours", "is_open"}
    rest = get_restaurant(restaurant_id)
    for k, v in updates.items():
        if k in allowed:
            rest[k] = v
    rest["updated_at"] = datetime.utcnow().isoformat()
    db = get_db_connection()
    db["restaurants"][restaurant_id] = rest
    return rest


def list_restaurants(city: str = None, cuisine: str = None) -> list:
    """List all active restaurants, optionally filtered."""
    db = get_db_connection()
    rests = list(db["restaurants"].values())
    if city:
        rests = [r for r in rests
                 if r["address"].get("city", "").lower() == city.lower()]
    if cuisine:
        rests = [r for r in rests
                 if r.get("cuisine", "").lower() == cuisine.lower()]
    return rests


def update_restaurant_rating(restaurant_id: str, new_rating: float,
                              total_reviews: int) -> dict:
    """Update aggregated rating on the restaurant record."""
    rest = get_restaurant(restaurant_id)
    rest["rating"] = round(new_rating, 2)
    rest["total_reviews"] = total_reviews
    db = get_db_connection()
    db["restaurants"][restaurant_id] = rest
    return rest
