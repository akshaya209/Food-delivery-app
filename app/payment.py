"""
app/payment.py
==============
Food Delivery App — Payment Processing
Depends on: cart, user, order (for post-payment), notification, analytics
"""

from app.db import get_db_connection
from app.user import get_user_by_id
from app.cart import get_cart_total, clear_cart
from app.notification import send_notification
from app.analytics import record_event
from datetime import datetime
import uuid


class PaymentError(Exception):
    pass


class InsufficientFundsError(PaymentError):
    pass


class PaymentGatewayError(PaymentError):
    pass


SUPPORTED_METHODS = {"card", "upi", "wallet", "cod", "net_banking"}


def initiate_payment(user_id: str, restaurant_id: str,
                     method: str, metadata: dict = None) -> dict:
    """Create a pending payment record for a cart."""
    if method not in SUPPORTED_METHODS:
        raise PaymentError(f"Unsupported payment method: {method}")

    user = get_user_by_id(user_id)
    amount = get_cart_total(user_id, restaurant_id)

    if amount <= 0:
        raise PaymentError("Cart is empty — cannot initiate payment")

    payment_id = f"pay_{uuid.uuid4().hex[:10]}"
    payment = {
        "id": payment_id,
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "amount": amount,
        "method": method,
        "status": "pending",
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat(),
    }
    db = get_db_connection()
    db["payments"][payment_id] = payment
    record_event("payment_initiated", {"user_id": user_id, "amount": amount, "method": method})
    return payment


def process_payment(payment_id: str) -> dict:
    """Simulate gateway call and mark payment success/failure."""
    db = get_db_connection()
    payment = db["payments"].get(payment_id)
    if not payment:
        raise PaymentError(f"Payment {payment_id} not found")
    if payment["status"] != "pending":
        raise PaymentError(f"Payment already in state: {payment['status']}")

    # Simulate gateway — real impl would call Razorpay/Stripe here
    gateway_success = _call_payment_gateway(payment)

    if gateway_success:
        payment["status"] = "success"
        payment["completed_at"] = datetime.utcnow().isoformat()
        send_notification(payment["user_id"], "payment_success",
                          {"amount": payment["amount"], "payment_id": payment_id})
        record_event("payment_success", {"payment_id": payment_id,
                                         "amount": payment["amount"]})
        # Clear cart on success
        clear_cart(payment["user_id"], payment["restaurant_id"])
    else:
        payment["status"] = "failed"
        send_notification(payment["user_id"], "payment_failed",
                          {"amount": payment["amount"]})
        record_event("payment_failed", {"payment_id": payment_id})

    db["payments"][payment_id] = payment
    return payment


def get_payment(payment_id: str) -> dict:
    """Fetch payment record by ID."""
    db = get_db_connection()
    payment = db["payments"].get(payment_id)
    if not payment:
        raise PaymentError(f"Payment {payment_id} not found")
    return payment


def get_user_payment_history(user_id: str) -> list:
    """Return all payments for a user, sorted by date descending."""
    db = get_db_connection()
    payments = [p for p in db["payments"].values() if p["user_id"] == user_id]
    return sorted(payments, key=lambda p: p["created_at"], reverse=True)


def refund_payment(payment_id: str, reason: str) -> dict:
    """Initiate a refund for a completed payment."""
    from app.refund import create_refund
    payment = get_payment(payment_id)
    if payment["status"] != "success":
        raise PaymentError(f"Cannot refund payment in state: {payment['status']}")
    refund = create_refund(payment_id, payment["amount"], reason)
    payment["refund_id"] = refund["id"]
    payment["status"] = "refunded"
    db = get_db_connection()
    db["payments"][payment_id] = payment
    send_notification(payment["user_id"], "refund_initiated",
                      {"refund_id": refund["id"], "amount": payment["amount"]})
    return refund


def validate_card(card_number: str, expiry: str, cvv: str) -> bool:
    """Luhn check + basic format validation for card payments."""
    card_number = card_number.replace(" ", "")
    if not card_number.isdigit() or len(card_number) not in (15, 16):
        return False
    # Luhn algorithm
    total = 0
    reverse = card_number[::-1]
    for i, digit in enumerate(reverse):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _call_payment_gateway(payment: dict) -> bool:
    """Mock gateway call. Returns True for non-COD payments under ₹50000."""
    if payment["method"] == "cod":
        return True
    return payment["amount"] < 50000
