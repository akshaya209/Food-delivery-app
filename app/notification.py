"""
app/notification.py
===================
Food Delivery App — Notification Dispatch (push, SMS, email)
Depends on: db
"""

from app.db import get_db_connection
from datetime import datetime
import uuid


class NotificationError(Exception):
    pass


NOTIFICATION_CHANNELS = {"push", "sms", "email", "in_app"}

TEMPLATES = {
    "welcome":               "Welcome to FoodDash, {name}! Start ordering now.",
    "order_confirmed":       "Your order #{order_id} is confirmed. Total: ₹{total}",
    "order_preparing":       "Restaurant is preparing your order #{order_id}",
    "order_out_for_delivery":"Your order #{order_id} is on the way!",
    "order_delivered":       "Order #{order_id} delivered. Enjoy your meal!",
    "order_cancelled":       "Order #{order_id} has been cancelled.",
    "payment_success":       "Payment of ₹{amount} received for order #{payment_id}",
    "payment_failed":        "Payment failed. Please retry.",
    "refund_initiated":      "Refund of ₹{amount} initiated. ID: {refund_id}",
    "loyalty_earned":        "You earned {points} points! Total: {new_total}",
    "loyalty_redeemed":      "Redeemed {points} pts for ₹{discount} discount.",
    "agent_location_update": "Your delivery agent is near you.",
    "order_picked_up":       "Agent picked up your order. On the way!",
    "new_order":             "New order #{order_id} received!",
    "account_deactivated":   "Your account has been deactivated.",
    "restaurant_registered": "Restaurant #{restaurant_id} is registered!",
    "referral_bonus":        "You earned {points} referral bonus points!",
    "new_delivery_assigned": "New delivery #{delivery_id} assigned to you.",
}


def send_notification(recipient_id: str, template_key: str,
                      context: dict, channels: list = None) -> dict:
    """
    Render a template and dispatch to one or more channels.
    Stores in DB for in-app retrieval.
    """
    if channels is None:
        channels = ["in_app"]

    unknown = set(channels) - NOTIFICATION_CHANNELS
    if unknown:
        raise NotificationError(f"Unknown channel(s): {unknown}")

    template = TEMPLATES.get(template_key, template_key)
    try:
        body = template.format(**context)
    except KeyError:
        body = template  # fall back to raw template if context is incomplete

    notif_id = f"ntf_{uuid.uuid4().hex[:8]}"
    notification = {
        "id": notif_id,
        "recipient_id": recipient_id,
        "template": template_key,
        "body": body,
        "channels": channels,
        "is_read": False,
        "created_at": datetime.utcnow().isoformat(),
    }

    db = get_db_connection()
    db["notifications"][notif_id] = notification

    # In a real system each channel dispatches async
    for channel in channels:
        _dispatch(channel, recipient_id, body)

    return notification


def get_unread_notifications(user_id: str) -> list:
    """Return unread notifications for a user."""
    db = get_db_connection()
    return [n for n in db["notifications"].values()
            if n["recipient_id"] == user_id and not n["is_read"]]


def mark_as_read(notification_id: str) -> bool:
    """Mark a single notification as read."""
    db = get_db_connection()
    notif = db["notifications"].get(notification_id)
    if not notif:
        raise NotificationError(f"Notification {notification_id} not found")
    notif["is_read"] = True
    db["notifications"][notification_id] = notif
    return True


def mark_all_read(user_id: str) -> int:
    """Mark all notifications for a user as read. Returns count updated."""
    db = get_db_connection()
    count = 0
    for notif in db["notifications"].values():
        if notif["recipient_id"] == user_id and not notif["is_read"]:
            notif["is_read"] = True
            count += 1
    return count


def get_notification_history(user_id: str, limit: int = 20) -> list:
    """Return recent notifications for a user."""
    db = get_db_connection()
    notifs = [n for n in db["notifications"].values()
              if n["recipient_id"] == user_id]
    return sorted(notifs, key=lambda n: n["created_at"], reverse=True)[:limit]


def _dispatch(channel: str, recipient_id: str, body: str) -> None:
    """Stub for actual channel dispatch (FCM, Twilio, SES, etc.)."""
    pass  # Real implementation would call external APIs
