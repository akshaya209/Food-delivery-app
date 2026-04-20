"""
tests/test_loyalty.py
=====================
Tests for app/loyalty.py
Dependency chain: loyalty → user → db, notification
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db, get_db_connection
from app.user import create_user
from app.loyalty import (
    get_loyalty_balance, earn_points, redeem_points,
    get_transaction_history, apply_referral_bonus, LoyaltyError,
)


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def user(clean):
    return create_user("loyal@test.com", "Loyal User", "+910000000010", "pass1234")


@pytest.fixture
def user2(clean):
    return create_user("loyal2@test.com", "Loyal Two", "+910000000011", "pass1234")


def test_initial_balance_is_zero(user):
    bal = get_loyalty_balance(user["id"])
    assert bal["points"] == 0
    assert bal["can_redeem"] is False


def test_earn_points_from_order(user):
    points = earn_points(user["id"], 300.0, "ord_001")
    assert points == 30  # 1 point per ₹10


def test_earn_points_updates_balance(user):
    earn_points(user["id"], 500.0, "ord_002")
    bal = get_loyalty_balance(user["id"])
    assert bal["points"] == 50


def test_earn_points_rupee_value(user):
    earn_points(user["id"], 1000.0, "ord_003")
    bal = get_loyalty_balance(user["id"])
    assert bal["rupee_value"] == 25.0  # 100 pts * ₹0.25


def test_can_redeem_after_enough_points(user):
    earn_points(user["id"], 1000.0, "ord_004")
    bal = get_loyalty_balance(user["id"])
    assert bal["can_redeem"] is True


def test_redeem_points_returns_discount(user):
    earn_points(user["id"], 2000.0, "ord_005")
    discount = redeem_points(user["id"], 100)
    assert discount == 25.0


def test_redeem_points_deducts_balance(user):
    earn_points(user["id"], 2000.0, "ord_006")
    redeem_points(user["id"], 100)
    bal = get_loyalty_balance(user["id"])
    assert bal["points"] == 100  # 200 earned - 100 redeemed


def test_redeem_below_minimum_raises(user):
    earn_points(user["id"], 2000.0, "ord_007")
    with pytest.raises(LoyaltyError, match="Minimum"):
        redeem_points(user["id"], 50)


def test_redeem_more_than_balance_raises(user):
    earn_points(user["id"], 100.0, "ord_008")  # only 10 points
    with pytest.raises(LoyaltyError, match="Insufficient"):
        redeem_points(user["id"], 500)


def test_transaction_history_records_earn(user):
    earn_points(user["id"], 500.0, "ord_009")
    history = get_transaction_history(user["id"])
    assert len(history) >= 1
    earn_txn = next(t for t in history if t["type"] == "earn")
    assert earn_txn["points"] == 50


def test_transaction_history_records_redeem(user):
    earn_points(user["id"], 2000.0, "ord_010")
    redeem_points(user["id"], 100)
    history = get_transaction_history(user["id"])
    types = [t["type"] for t in history]
    assert "redeem" in types


def test_referral_bonus_awards_both_users(user, user2):
    result = apply_referral_bonus(user["id"], user2["id"])
    assert result["referrer_points"] == 50
    assert result["referred_points"] == 25
    bal_referrer = get_loyalty_balance(user["id"])
    bal_referred = get_loyalty_balance(user2["id"])
    assert bal_referrer["points"] == 50
    assert bal_referred["points"] == 25


def test_earn_sends_notification(user):
    earn_points(user["id"], 500.0, "ord_011")
    db = get_db_connection()
    notifs = db["notifications"].get(user["id"], [])
    types = [n["type"] for n in notifs]
    assert "loyalty_earned" in types


def test_zero_order_earns_no_points(user):
    points = earn_points(user["id"], 5.0, "ord_012")  # less than ₹10
    assert points == 0
