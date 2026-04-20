"""
tests/test_coupon.py
====================
Tests for app/coupon.py
Dependency chain: coupon → db
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db
from app.coupon import (
    create_coupon, apply_coupon, deactivate_coupon,
    get_coupon, list_active_coupons, CouponError,
)


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


def test_create_flat_coupon(clean):
    c = create_coupon("FLAT50", "flat", 50.0, min_order=200.0)
    assert c["code"] == "FLAT50"
    assert c["discount_type"] == "flat"
    assert c["value"] == 50.0
    assert c["is_active"] is True


def test_create_percent_coupon(clean):
    c = create_coupon("PCT20", "percent", 20.0)
    assert c["discount_type"] == "percent"
    assert c["value"] == 20.0


def test_create_invalid_discount_type(clean):
    with pytest.raises(CouponError, match="discount_type"):
        create_coupon("BAD", "cashback", 10.0)


def test_create_percent_over_100(clean):
    with pytest.raises(CouponError, match="Percent"):
        create_coupon("OVER", "percent", 150.0)


def test_apply_flat_coupon_returns_correct_discount(clean):
    create_coupon("FLAT30", "flat", 30.0, min_order=100.0)
    discount = apply_coupon("FLAT30", 300.0, "usr_001")
    assert discount == 30.0


def test_apply_percent_coupon(clean):
    create_coupon("PCT10", "percent", 10.0)
    discount = apply_coupon("PCT10", 500.0, "usr_001")
    assert discount == 50.0


def test_apply_coupon_below_min_order(clean):
    create_coupon("MINORD", "flat", 50.0, min_order=500.0)
    with pytest.raises(CouponError, match="Minimum order"):
        apply_coupon("MINORD", 100.0, "usr_001")


def test_apply_coupon_nonexistent_raises(clean):
    with pytest.raises(CouponError, match="does not exist"):
        apply_coupon("FAKE99", 200.0, "usr_001")


def test_apply_coupon_decrements_uses(clean):
    create_coupon("USES3", "flat", 10.0, max_uses=3)
    apply_coupon("USES3", 100.0, "usr_001")
    apply_coupon("USES3", 100.0, "usr_002")
    apply_coupon("USES3", 100.0, "usr_003")
    with pytest.raises(CouponError, match="no remaining uses"):
        apply_coupon("USES3", 100.0, "usr_004")


def test_apply_inactive_coupon_raises(clean):
    create_coupon("INACT", "flat", 20.0)
    deactivate_coupon("INACT")
    with pytest.raises(CouponError, match="inactive"):
        apply_coupon("INACT", 200.0, "usr_001")


def test_deactivate_coupon(clean):
    create_coupon("KILL", "flat", 10.0)
    result = deactivate_coupon("KILL")
    assert result is True
    c = get_coupon("KILL")
    assert c["is_active"] is False


def test_deactivate_nonexistent_raises(clean):
    with pytest.raises(CouponError):
        deactivate_coupon("GHOST")


def test_flat_coupon_capped_at_order_amount(clean):
    create_coupon("BIGFLAT", "flat", 1000.0)
    discount = apply_coupon("BIGFLAT", 50.0, "usr_001")
    assert discount == 50.0  # cannot exceed order amount


def test_list_active_coupons(clean):
    create_coupon("A1", "flat", 10.0)
    create_coupon("A2", "percent", 5.0)
    create_coupon("DEAD", "flat", 5.0)
    deactivate_coupon("DEAD")
    active = list_active_coupons()
    codes = [c["code"] for c in active]
    assert "A1" in codes
    assert "A2" in codes
    assert "DEAD" not in codes


def test_list_coupons_for_restaurant(clean):
    create_coupon("RST1", "flat", 20.0, restaurant_id="rst_001")
    create_coupon("GLOBAL", "percent", 5.0)
    coupons = list_active_coupons(restaurant_id="rst_001")
    codes = [c["code"] for c in coupons]
    assert "RST1" in codes
    assert "GLOBAL" in codes  # global coupons always included


def test_coupon_code_stored_uppercased(clean):
    create_coupon("lower", "flat", 5.0)
    c = get_coupon("LOWER")
    assert c["code"] == "LOWER"
