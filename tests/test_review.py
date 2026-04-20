"""
tests/test_review.py
====================
Tests for app/review.py
Dependency chain: review → db, user, restaurant, order
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db, get_db_connection
from app.user import create_user
from app.restaurant import register_restaurant, get_restaurant
from app.review import (
    post_review, get_review, get_restaurant_reviews,
    get_user_reviews, delete_review, ReviewError,
)


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def setup(clean):
    user = create_user("reviewer@test.com", "Reviewer", "+910000000030", "pass1234")
    rest = register_restaurant(
        "Review Resto", "owner_rv", "Thai",
        {"street": "5 Review Ave", "city": "Bengaluru", "pincode": "560001",
         "lat": 12.97, "lng": 77.59},
        {"open": "11:00", "close": "23:00"},
    )
    return {"user": user, "rest": rest}


def test_post_review_creates_record(setup):
    review = post_review(
        user_id=setup["user"]["id"],
        restaurant_id=setup["rest"]["id"],
        rating=4,
        comment="Great food!",
        order_id="ord_001",
    )
    assert review["rating"] == 4
    assert review["comment"] == "Great food!"
    assert "id" in review


def test_post_review_invalid_rating(setup):
    with pytest.raises(ReviewError, match="Rating must be"):
        post_review(setup["user"]["id"], setup["rest"]["id"], 6, "Too good")


def test_post_review_updates_restaurant_rating(setup):
    post_review(setup["user"]["id"], setup["rest"]["id"], 4, "Nice")
    post_review(setup["user"]["id"], setup["rest"]["id"], 2, "Meh", "ord_002")
    rest = get_restaurant(setup["rest"]["id"])
    assert rest["rating"] == 3.0
    assert rest["total_reviews"] == 2


def test_get_review_by_id(setup):
    review = post_review(setup["user"]["id"], setup["rest"]["id"], 5, "Amazing!")
    fetched = get_review(review["id"])
    assert fetched["id"] == review["id"]


def test_get_review_nonexistent_raises(setup):
    with pytest.raises(ReviewError):
        get_review("rev_nonexistent")


def test_get_restaurant_reviews(setup):
    post_review(setup["user"]["id"], setup["rest"]["id"], 3, "OK", "o1")
    post_review(setup["user"]["id"], setup["rest"]["id"], 5, "WOW", "o2")
    reviews = get_restaurant_reviews(setup["rest"]["id"])
    assert len(reviews) == 2


def test_get_restaurant_reviews_sorted_by_date(setup):
    import time
    post_review(setup["user"]["id"], setup["rest"]["id"], 3, "First", "o3")
    time.sleep(0.01)
    post_review(setup["user"]["id"], setup["rest"]["id"], 5, "Second", "o4")
    reviews = get_restaurant_reviews(setup["rest"]["id"])
    assert reviews[0]["comment"] == "Second"


def test_get_user_reviews(setup):
    post_review(setup["user"]["id"], setup["rest"]["id"], 4, "Good")
    reviews = get_user_reviews(setup["user"]["id"])
    assert len(reviews) == 1
    assert reviews[0]["user_id"] == setup["user"]["id"]


def test_delete_review(setup):
    review = post_review(setup["user"]["id"], setup["rest"]["id"], 3, "Decent")
    result = delete_review(review["id"], setup["user"]["id"])
    assert result is True
    with pytest.raises(ReviewError):
        get_review(review["id"])


def test_delete_review_wrong_user_raises(setup):
    review = post_review(setup["user"]["id"], setup["rest"]["id"], 3, "Decent")
    with pytest.raises(ReviewError, match="permission"):
        delete_review(review["id"], "usr_intruder")


def test_review_triggers_restaurant_notification(setup):
    post_review(setup["user"]["id"], setup["rest"]["id"], 5, "Excellent!")
    db = get_db_connection()
    owner_notifs = db["notifications"].get("owner_rv", [])
    assert any(n["type"] == "review_posted" for n in owner_notifs)
