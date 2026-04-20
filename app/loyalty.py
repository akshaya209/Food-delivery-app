"""
app/loyalty.py
==============
Food Delivery App — Loyalty Points & Rewards Program
Depends on: user, db, notification
"""

from app.db import get_db_connection
from app.user import get_user_by_id, add_loyalty_points
from app.notification import send_notification
from datetime import datetime


class LoyaltyError(Exception):
    pass


POINTS_TO_RUPEES = 0.25   # 1 point = ₹0.25
MIN_REDEEM_POINTS = 100


def get_loyalty_balance(user_id: str) -> dict:
    """Return current loyalty point balance and rupee equivalent."""
    user = get_user_by_id(user_id)
    points = user.get("loyalty_points", 0)
    return {
        "user_id": user_id,
        "points": points,
        "rupee_value": round(points * POINTS_TO_RUPEES, 2),
        "can_redeem": points >= MIN_REDEEM_POINTS,
    }


def earn_points(user_id: str, order_total: float, order_id: str) -> int:
    """Award points for a completed order. 1 point per ₹10 spent."""
    points = int(order_total // 10)
    if points > 0:
        new_total = add_loyalty_points(user_id, points)
        _log_transaction(user_id, "earn", points, f"order:{order_id}")
        send_notification(user_id, "loyalty_earned",
                          {"points": points, "new_total": new_total})
        return points
    return 0


def redeem_points(user_id: str, points_to_redeem: int) -> float:
    """
    Redeem loyalty points for a cart discount.
    Returns the rupee discount amount.
    """
    if points_to_redeem < MIN_REDEEM_POINTS:
        raise LoyaltyError(
            f"Minimum {MIN_REDEEM_POINTS} points required to redeem"
        )
    user = get_user_by_id(user_id)
    available = user.get("loyalty_points", 0)
    if points_to_redeem > available:
        raise LoyaltyError(
            f"Insufficient points: have {available}, requested {points_to_redeem}"
        )

    # Deduct points
    add_loyalty_points(user_id, -points_to_redeem)
    discount = round(points_to_redeem * POINTS_TO_RUPEES, 2)
    _log_transaction(user_id, "redeem", -points_to_redeem, f"discount:₹{discount}")
    send_notification(user_id, "loyalty_redeemed",
                      {"points": points_to_redeem, "discount": discount})
    return discount


def get_transaction_history(user_id: str) -> list:
    """Return all loyalty point transactions for a user."""
    db = get_db_connection()
    ledger = db.get("loyalty_ledger", {})
    return ledger.get(user_id, [])


def apply_referral_bonus(referrer_id: str, referred_id: str) -> dict:
    """Award bonus points for a successful referral."""
    REFERRER_BONUS = 50
    REFERRED_BONUS = 25
    add_loyalty_points(referrer_id, REFERRER_BONUS)
    add_loyalty_points(referred_id, REFERRED_BONUS)
    _log_transaction(referrer_id, "referral_bonus", REFERRER_BONUS,
                     f"referred:{referred_id}")
    _log_transaction(referred_id, "referral_welcome", REFERRED_BONUS,
                     f"referred_by:{referrer_id}")
    send_notification(referrer_id, "referral_bonus",
                      {"points": REFERRER_BONUS})
    return {"referrer_points": REFERRER_BONUS, "referred_points": REFERRED_BONUS}


def _log_transaction(user_id: str, txn_type: str,
                     points: int, reference: str) -> None:
    """Append a transaction to the loyalty ledger."""
    db = get_db_connection()
    ledger = db.setdefault("loyalty_ledger", {})
    ledger.setdefault(user_id, []).append({
        "type": txn_type,
        "points": points,
        "reference": reference,
        "timestamp": datetime.utcnow().isoformat(),
    })
