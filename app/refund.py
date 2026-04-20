"""
app/refund.py
=============
Food Delivery App — Refund Processing
Depends on: db, notification, analytics  (NOT on cart/user/order)
"""

from app.db import get_db_connection
from app.analytics import record_event
from datetime import datetime
import uuid


class RefundError(Exception):
    pass


def create_refund(payment_id: str, amount: float, reason: str) -> dict:
    """Create a pending refund record for a payment."""
    db = get_db_connection()
    payment = db["payments"].get(payment_id)
    if not payment:
        raise RefundError(f"Payment {payment_id} not found")
    if amount > payment["amount"]:
        raise RefundError(
            f"Refund amount {amount} cannot exceed payment amount {payment['amount']}"
        )

    refund_id = f"rfnd_{uuid.uuid4().hex[:10]}"
    refund = {
        "id": refund_id,
        "payment_id": payment_id,
        "user_id": payment.get("user_id"),
        "amount": amount,
        "reason": reason,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }
    db["refunds"][refund_id] = refund
    record_event("refund_created", {"refund_id": refund_id, "payment_id": payment_id,
                                    "amount": amount})
    return refund


def get_refund(refund_id: str) -> dict:
    """Fetch a refund by ID."""
    db = get_db_connection()
    refund = db["refunds"].get(refund_id)
    if not refund:
        raise RefundError(f"Refund {refund_id} not found")
    return refund


def process_refund(refund_id: str) -> dict:
    """Process a pending refund (mark as completed)."""
    refund = get_refund(refund_id)
    if refund["status"] != "pending":
        raise RefundError(f"Refund {refund_id} is already {refund['status']}")

    refund["status"] = "completed"
    refund["processed_at"] = datetime.utcnow().isoformat()

    db = get_db_connection()
    db["refunds"][refund_id] = refund

    # Notify user
    user_id = refund.get("user_id")
    if user_id:
        _notify_refund(user_id, refund_id, refund["amount"])

    record_event("refund_processed",
                 {"refund_id": refund_id, "amount": refund["amount"]})
    return refund


def list_refunds_for_payment(payment_id: str) -> list:
    """Return all refunds for a given payment."""
    db = get_db_connection()
    return [r for r in db["refunds"].values()
            if r["payment_id"] == payment_id]


def _notify_refund(user_id: str, refund_id: str, amount: float) -> None:
    """Store a refund notification in the DB."""
    db = get_db_connection()
    import uuid as _uuid
    notif_id = f"ntf_{_uuid.uuid4().hex[:8]}"
    notif = {
        "id": notif_id,
        "recipient_id": user_id,
        "type": "refund_initiated",
        "body": f"Refund of ₹{amount} has been processed. ID: {refund_id}",
        "is_read": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    db["notifications"].setdefault(user_id, []).append(notif)
