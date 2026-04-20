"""
app/support.py
==============
Food Delivery App — Customer Support Ticket System
Depends on: db, user, notification  (NOT on cart/payment/delivery)
"""

from app.db import get_db_connection
from app.user import get_user_by_id
from datetime import datetime
import uuid


class SupportError(Exception):
    pass


VALID_CATEGORIES = {
    "order_issue", "payment_issue", "delivery_issue",
    "general", "refund_request", "resolved", "done",
}


def open_ticket(user_id: str, category: str, description: str,
                order_id: str = None) -> dict:
    """Open a new support ticket."""
    get_user_by_id(user_id)  # validates user exists

    db = get_db_connection()
    ticket_id = f"tkt_{uuid.uuid4().hex[:10]}"
    ticket = {
        "id": ticket_id,
        "user_id": user_id,
        "category": category,
        "description": description,
        "order_id": order_id,
        "status": "open",
        "messages": [],
        "created_at": datetime.utcnow().isoformat(),
    }
    db["support_tickets"][ticket_id] = ticket
    return ticket


def get_ticket(ticket_id: str) -> dict:
    """Fetch a ticket by ID."""
    db = get_db_connection()
    ticket = db["support_tickets"].get(ticket_id)
    if not ticket:
        raise SupportError(f"Ticket {ticket_id} not found")
    return ticket


def reply_to_ticket(ticket_id: str, sender_id: str, text: str,
                    is_agent: bool = False) -> dict:
    """Append a message to a ticket thread."""
    ticket = get_ticket(ticket_id)
    if ticket["status"] == "closed":
        raise SupportError(f"Ticket {ticket_id} is closed — cannot reply")

    message = {
        "sender_id": sender_id,
        "text": text,
        "is_agent": is_agent,
        "created_at": datetime.utcnow().isoformat(),
    }
    ticket["messages"].append(message)
    ticket["updated_at"] = datetime.utcnow().isoformat()

    db = get_db_connection()
    db["support_tickets"][ticket_id] = ticket

    # Notify the user when an agent replies
    if is_agent:
        _notify_user(ticket["user_id"], ticket_id, text)

    return ticket


def close_ticket(ticket_id: str) -> dict:
    """Close a support ticket."""
    ticket = get_ticket(ticket_id)
    if ticket["status"] == "closed":
        raise SupportError(f"Ticket {ticket_id} is already closed")
    ticket["status"] = "closed"
    ticket["closed_at"] = datetime.utcnow().isoformat()
    db = get_db_connection()
    db["support_tickets"][ticket_id] = ticket
    return ticket


def get_user_tickets(user_id: str) -> list:
    """Return all tickets for a given user."""
    db = get_db_connection()
    return [t for t in db["support_tickets"].values()
            if t["user_id"] == user_id]


def _notify_user(user_id: str, ticket_id: str, message_text: str) -> None:
    """Store a support-reply notification in the DB."""
    db = get_db_connection()
    import uuid as _uuid
    notif_id = f"ntf_{_uuid.uuid4().hex[:8]}"
    notif = {
        "id": notif_id,
        "recipient_id": user_id,
        "type": "support_reply",
        "body": f"New reply on ticket {ticket_id}: {message_text[:100]}",
        "is_read": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    db["notifications"].setdefault(user_id, []).append(notif)
