"""
app/delivery.py
===============
Food Delivery App — Delivery Agent Assignment & Tracking
Depends on: db, notification, analytics
"""

from app.db import get_db_connection
from app.notification import send_notification
from app.analytics import record_event
from datetime import datetime
import uuid
import math


class DeliveryError(Exception):
    pass


def assign_delivery_agent(order_id: str, pickup_address: dict,
                           drop_address: dict) -> dict:
    """Find nearest available agent and assign the delivery."""
    db = get_db_connection()
    agents = db.get("delivery_agents", {})
    available = [a for a in agents.values() if a.get("is_available")]

    if not available:
        # Create a mock agent if none exist (dev/test scenario)
        agent_id = f"agt_{uuid.uuid4().hex[:6]}"
        agent = {"id": agent_id, "name": "Auto Agent", "is_available": True,
                 "lat": 0.0, "lng": 0.0, "rating": 4.5}
        db.setdefault("delivery_agents", {})[agent_id] = agent
        available = [agent]

    # Pick nearest agent (simplified: first available)
    agent = available[0]

    delivery_id = f"dlv_{uuid.uuid4().hex[:10]}"
    distance_km = _haversine(
        pickup_address.get("lat", 0), pickup_address.get("lng", 0),
        drop_address.get("lat", 0), drop_address.get("lng", 0)
    )
    estimated_minutes = max(10, int(distance_km * 3))

    delivery = {
        "id": delivery_id,
        "order_id": order_id,
        "agent_id": agent["id"],
        "agent_name": agent["name"],
        "pickup_address": pickup_address,
        "drop_address": drop_address,
        "distance_km": round(distance_km, 2),
        "estimated_minutes": estimated_minutes,
        "status": "assigned",
        "created_at": datetime.utcnow().isoformat(),
    }
    db.setdefault("deliveries", {})[delivery_id] = delivery

    # Mark agent as busy
    agent["is_available"] = False
    agent["current_delivery"] = delivery_id
    db["delivery_agents"][agent["id"]] = agent

    send_notification(agent["id"], "new_delivery_assigned",
                      {"delivery_id": delivery_id, "order_id": order_id})
    record_event("delivery_assigned",
                 {"delivery_id": delivery_id, "agent_id": agent["id"]})
    return delivery


def update_delivery_status(delivery_id: str, status: str,
                            location: dict = None) -> dict:
    """Update delivery status and optionally current location."""
    valid_statuses = {"assigned", "picked_up", "in_transit",
                      "arrived", "delivered", "failed"}
    if status not in valid_statuses:
        raise DeliveryError(f"Invalid delivery status: {status}")

    db = get_db_connection()
    deliveries = db.get("deliveries", {})
    delivery = deliveries.get(delivery_id)
    if not delivery:
        raise DeliveryError(f"Delivery {delivery_id} not found")

    delivery["status"] = status
    if location:
        delivery["current_location"] = location
    delivery["updated_at"] = datetime.utcnow().isoformat()

    if status == "delivered":
        delivery["delivered_at"] = datetime.utcnow().isoformat()
        # Free up the agent
        agent = db.get("delivery_agents", {}).get(delivery["agent_id"])
        if agent:
            agent["is_available"] = True
            agent.pop("current_delivery", None)
            db["delivery_agents"][agent["id"]] = agent

    deliveries[delivery_id] = delivery
    record_event("delivery_status_change",
                 {"delivery_id": delivery_id, "status": status})
    return delivery


def get_delivery(delivery_id: str) -> dict:
    """Fetch delivery record."""
    db = get_db_connection()
    delivery = db.get("deliveries", {}).get(delivery_id)
    if not delivery:
        raise DeliveryError(f"Delivery {delivery_id} not found")
    return delivery


def get_delivery_by_order(order_id: str) -> dict:
    """Find the delivery record for a given order."""
    db = get_db_connection()
    for d in db.get("deliveries", {}).values():
        if d["order_id"] == order_id:
            return d
    raise DeliveryError(f"No delivery found for order {order_id}")


def register_delivery_agent(name: str, phone: str, vehicle: str) -> dict:
    """Onboard a new delivery agent."""
    db = get_db_connection()
    agent_id = f"agt_{uuid.uuid4().hex[:6]}"
    agent = {
        "id": agent_id, "name": name, "phone": phone,
        "vehicle": vehicle, "is_available": True,
        "rating": 5.0, "deliveries_completed": 0,
        "lat": 0.0, "lng": 0.0,
        "created_at": datetime.utcnow().isoformat(),
    }
    db.setdefault("delivery_agents", {})[agent_id] = agent
    return agent


def _haversine(lat1, lon1, lat2, lon2) -> float:
    """Distance in km between two (lat, lon) pairs."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
