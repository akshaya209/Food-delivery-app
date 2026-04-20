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


TEMPLATES = {
    "welcome":                "Welcome to FoodDash, {name}! Start ordering now.",
    "order_confirmed":        "Your order #{order_id} is confirmed. Total: ₹{total}",
    "order_preparing":        "Restaurant is preparing your order #{order_id}",
    "order_out_for_delivery": "Your order #{order_id} is on the way!",
    "order_delivered":        "Order #{order_id} delivered. Enjoy your meal!",
    "order_cancelled":        "Order #{order_id} has been cancelled.",
    "payment_success":        "Payment of ₹{amount} received for order #{payment_id}",
    "payment_failed":         "Payment failed. Please retry.",
    "refund_initiated":       "Refund of ₹{amount} initiated. ID: {refund_id}",
    "loyalty_earned":         "You earned {points} points! Total: {new_total}",
    "loyalty_redeemed":       "Redeemed {points} pts for ₹{discount} discount.",
    "agent_location_update":  "Your delivery agent is near you.",
    "order_picked_up":        "Agent picked up your order. On the way!",
    "new_order":              "New order #{order_id} received!",
    "account_deactivated":    "Your account has been deactivated.",
    "restaurant_registered":  "Restaurant #{restaurant_id} is registered!",
    "referral_bonus":         "You earned {points} referral bonus points!",
    "new_delivery_assigned":  "New delivery #{delivery_id} assigned to you.",
    "review_posted":          "A new review has been posted for your restaurant.",
    "support_reply":          "Support has replied to your ticket.",
}

_URGENT_TYPES = {"payment_failed", "order_cancelled", "account_deactivated"}
_SILENT_TYPES = {"agent_location_update"}


def _resolve_channel(template_key: str) -> str:
    if template_key in _URGENT_TYPES:
        return "sms"
    if template_key in _SILENT_TYPES:
        return "push_silent"
    return "push"


def send_notification(
    recipient_id: str,
    template_key: str,
    context: dict,
    channels: list = None,
) -> dict:
    """Render a template and store it. Returns the notification record."""
    channel = _resolve_channel(template_key)
    template = TEMPLATES.get(template_key, template_key)
    try:
        body = template.format(**context)
    except KeyError:
        body = template

    notif_id = f"ntf_{uuid.uuid4().hex[:8]}"
    notification = {
        "id": notif_id,
        "recipient_id": recipient_id,
        "type": template_key,
        "body": body,
        "channel": channel,
        "is_read": False,
        "created_at": datetime.utcnow().isoformat(),
    }

    db = get_db_connection()
    db["notifications"].setdefault(recipient_id, []).append(notification)
    return notification


def get_notifications(user_id: str, unread_only: bool = False) -> list:
    """Return notifications for a user, sorted newest-first."""
    db = get_db_connection()
    notifs = list(db.get("notifications", {}).get(user_id, []))
    if unread_only:
        notifs = [n for n in notifs if not n["is_read"]]
    return sorted(notifs, key=lambda n: n["created_at"], reverse=True)


def get_unread_notifications(user_id: str) -> list:
    """Alias: return unread notifications for a user."""
    return get_notifications(user_id, unread_only=True)


def get_unread_count(user_id: str) -> int:
    """Return count of unread notifications."""
    return len(get_notifications(user_id, unread_only=True))


def mark_as_read(user_id: str, notification_id: str) -> bool:
    """Mark a single notification as read. Returns False if not found."""
    db = get_db_connection()
    notifs = db.get("notifications", {}).get(user_id, [])
    for n in notifs:
        if n["id"] == notification_id:
            n["is_read"] = True
            return True
    return False


def mark_all_read(user_id: str) -> int:
    """Mark all notifications for a user as read. Returns count updated."""
    db = get_db_connection()
    notifs = db.get("notifications", {}).get(user_id, [])
    count = 0
    for n in notifs:
        if not n["is_read"]:
            n["is_read"] = True
            count += 1
    return count


def get_notification_history(user_id: str, limit: int = 20) -> list:
    """Return recent notifications for a user."""
    return get_notifications(user_id)[:limit]


def _dispatch(channel: str, recipient_id: str, body: str) -> None:
    pass
