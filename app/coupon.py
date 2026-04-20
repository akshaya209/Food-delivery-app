"""
app/coupon.py
=============
Food Delivery App — Coupon & Discount Management
Depends on: db
"""

from app.db import get_db_connection
from datetime import datetime


class CouponError(Exception):
    pass


def create_coupon(code: str, discount_type: str, value: float,
                  min_order: float = 0, max_uses: int = 100,
                  expiry: str = None, restaurant_id: str = None) -> dict:
    """Create a new coupon code."""
    if discount_type not in ("flat", "percent"):
        raise CouponError("discount_type must be 'flat' or 'percent'")
    if discount_type == "percent" and not (0 < value <= 100):
        raise CouponError("Percent discount must be between 0 and 100")

    db = get_db_connection()
    coupon = {
        "code": code.upper(),
        "discount_type": discount_type,
        "value": value,
        "min_order": min_order,
        "max_uses": max_uses,
        "uses_remaining": max_uses,
        "expiry": expiry,
        "restaurant_id": restaurant_id,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
    }
    db["coupons"][code.upper()] = coupon
    return coupon


def apply_coupon(code: str, order_amount: float, user_id: str) -> float:
    """Validate coupon and return discount amount."""
    db = get_db_connection()
    coupon = db["coupons"].get(code.upper())
    if not coupon:
        raise CouponError(f"Coupon '{code}' does not exist")
    if not coupon.get("is_active"):
        raise CouponError(f"Coupon '{code}' is inactive")
    if coupon["uses_remaining"] <= 0:
        raise CouponError(f"Coupon '{code}' has no remaining uses")
    if coupon["expiry"] and coupon["expiry"] < datetime.utcnow().isoformat():
        raise CouponError(f"Coupon '{code}' has expired")
    if order_amount < coupon["min_order"]:
        raise CouponError(
            f"Minimum order ₹{coupon['min_order']} required for coupon '{code}'"
        )

    if coupon["discount_type"] == "flat":
        discount = min(coupon["value"], order_amount)
    else:
        discount = round(order_amount * coupon["value"] / 100, 2)

    # Deduct a use
    coupon["uses_remaining"] -= 1
    db["coupons"][code.upper()] = coupon
    return discount


def deactivate_coupon(code: str) -> bool:
    """Deactivate a coupon so it can no longer be used."""
    db = get_db_connection()
    coupon = db["coupons"].get(code.upper())
    if not coupon:
        raise CouponError(f"Coupon '{code}' not found")
    coupon["is_active"] = False
    db["coupons"][code.upper()] = coupon
    return True


def get_coupon(code: str) -> dict:
    """Fetch coupon details."""
    db = get_db_connection()
    coupon = db["coupons"].get(code.upper())
    if not coupon:
        raise CouponError(f"Coupon '{code}' not found")
    return coupon


def list_active_coupons(restaurant_id: str = None) -> list:
    """List all active coupons, optionally for a specific restaurant."""
    db = get_db_connection()
    coupons = [c for c in db["coupons"].values() if c.get("is_active")]
    if restaurant_id:
        coupons = [c for c in coupons
                   if c.get("restaurant_id") in (None, restaurant_id)]
    return coupons
