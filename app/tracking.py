"""
app/tracking.py
===============
Food Delivery App — Real-time Order & Delivery Tracking
Depends on: delivery, order, notification
"""

from app.db import get_db_connection
from app.delivery import get_delivery, get_delivery_by_order, update_delivery_status
from app.order import get_order, update_order_status
from app.notification import send_notification
from datetime import datetime


class TrackingError(Exception):
    pass


def get_order_tracking(order_id: str) -> dict:
    """Return combined order + delivery tracking snapshot."""
    order = get_order(order_id)
    try:
        delivery = get_delivery_by_order(order_id)
    except Exception:
        delivery = None

    return {
        "order_id": order_id,
        "order_status": order["status"],
        "estimated_delivery_minutes": order.get("estimated_delivery_minutes"),
        "delivery": {
            "id": delivery["id"] if delivery else None,
            "agent_name": delivery.get("agent_name") if delivery else None,
            "status": delivery["status"] if delivery else "not_assigned",
            "current_location": delivery.get("current_location") if delivery else None,
            "distance_km": delivery.get("distance_km") if delivery else None,
        },
        "timeline": _build_timeline(order, delivery),
        "last_updated": datetime.utcnow().isoformat(),
    }


def update_agent_location(delivery_id: str, lat: float, lng: float) -> dict:
    """Push a new GPS location for a delivery agent."""
    delivery = get_delivery(delivery_id)
    location = {"lat": lat, "lng": lng, "timestamp": datetime.utcnow().isoformat()}
    delivery["current_location"] = location

    db = get_db_connection()
    db.setdefault("deliveries", {})[delivery_id] = delivery

    # Notify customer
    order = get_order(delivery["order_id"])
    send_notification(order["user_id"], "agent_location_update",
                      {"delivery_id": delivery_id, "lat": lat, "lng": lng})
    return delivery


def mark_order_picked_up(delivery_id: str) -> dict:
    """Agent has picked up the order from the restaurant."""
    delivery = update_delivery_status(delivery_id, "picked_up")
    update_order_status(delivery["order_id"], "out_for_delivery")
    order = get_order(delivery["order_id"])
    send_notification(order["user_id"], "order_picked_up",
                      {"delivery_id": delivery_id})
    return delivery


def mark_order_delivered(delivery_id: str) -> dict:
    """Agent has delivered the order to the customer."""
    delivery = update_delivery_status(delivery_id, "delivered")
    update_order_status(delivery["order_id"], "delivered")
    order = get_order(delivery["order_id"])
    send_notification(order["user_id"], "order_delivered",
                      {"order_id": delivery["order_id"]})
    return delivery


def get_agent_active_delivery(agent_id: str) -> dict:
    """Return the current active delivery for an agent."""
    db = get_db_connection()
    for d in db.get("deliveries", {}).values():
        if d["agent_id"] == agent_id and d["status"] not in ("delivered", "failed"):
            return d
    raise TrackingError(f"No active delivery for agent {agent_id}")


def _build_timeline(order: dict, delivery: dict) -> list:
    """Build a step-by-step timeline of the order's progress."""
    steps = [
        {"step": "Order Placed", "done": True,
         "time": order.get("created_at")},
        {"step": "Payment Confirmed", "done": order["status"] != "pending",
         "time": order.get("created_at")},
        {"step": "Restaurant Preparing",
         "done": order["status"] in ("preparing", "ready_for_pickup",
                                     "out_for_delivery", "delivered"),
         "time": order.get("preparing_at")},
        {"step": "Out for Delivery",
         "done": order["status"] in ("out_for_delivery", "delivered"),
         "time": delivery.get("picked_up_at") if delivery else None},
        {"step": "Delivered",
         "done": order["status"] == "delivered",
         "time": delivery.get("delivered_at") if delivery else None},
    ]
    return steps
