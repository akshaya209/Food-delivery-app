"""
app/review.py
=============
Food Delivery App — Restaurant Reviews & Ratings
Depends on: db, restaurant, notification
"""

from app.db import get_db_connection
from datetime import datetime
import uuid


class ReviewError(Exception):
    pass


def post_review(user_id: str, restaurant_id: str, rating: int,
                comment: str, order_id: str = None) -> dict:
    """Post a review for a restaurant."""
    if not (1 <= rating <= 5):
        raise ReviewError("Rating must be between 1 and 5")

    db = get_db_connection()
    review_id = f"rev_{uuid.uuid4().hex[:8]}"
    review = {
        "id": review_id,
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "rating": rating,
        "comment": comment,
        "order_id": order_id,
        "created_at": datetime.utcnow().isoformat(),
    }
    db["reviews"][review_id] = review

    # Update restaurant aggregate rating
    _update_restaurant_rating(restaurant_id)

    # Notify restaurant owner
    rest = db["restaurants"].get(restaurant_id, {})
    owner_id = rest.get("owner_id")
    if owner_id:
        db["notifications"].setdefault(owner_id, []).append({
            "id": f"ntf_{uuid.uuid4().hex[:8]}",
            "recipient_id": owner_id,
            "type": "review_posted",
            "body": f"New {rating}-star review on your restaurant.",
            "is_read": False,
            "created_at": datetime.utcnow().isoformat(),
        })

    return review


def get_review(review_id: str) -> dict:
    """Fetch a review by ID."""
    db = get_db_connection()
    review = db["reviews"].get(review_id)
    if not review:
        raise ReviewError(f"Review {review_id} not found")
    return review


def get_restaurant_reviews(restaurant_id: str) -> list:
    """Return all reviews for a restaurant, newest first."""
    db = get_db_connection()
    reviews = [r for r in db["reviews"].values()
               if r["restaurant_id"] == restaurant_id]
    return sorted(reviews, key=lambda r: r["created_at"], reverse=True)


def get_user_reviews(user_id: str) -> list:
    """Return all reviews by a user."""
    db = get_db_connection()
    return [r for r in db["reviews"].values() if r["user_id"] == user_id]


def delete_review(review_id: str, user_id: str) -> bool:
    """Delete a review. Only the author can delete their own review."""
    review = get_review(review_id)
    if review["user_id"] != user_id:
        raise ReviewError(f"No permission to delete review {review_id}")
    db = get_db_connection()
    del db["reviews"][review_id]
    _update_restaurant_rating(review["restaurant_id"])
    return True


def add_review(user, rating):
    """Legacy stub for backward compatibility."""
    return {"user": user, "rating": rating}


def get_reviews():
    """Legacy stub for backward compatibility."""
    return []


def _update_restaurant_rating(restaurant_id: str) -> None:
    """Recalculate and persist aggregate rating for a restaurant."""
    db = get_db_connection()
    reviews = [r for r in db["reviews"].values()
               if r["restaurant_id"] == restaurant_id]
    if not reviews:
        avg = 0.0
    else:
        avg = sum(r["rating"] for r in reviews) / len(reviews)

    rest = db["restaurants"].get(restaurant_id)
    if rest:
        rest["rating"] = round(avg, 2)
        rest["total_reviews"] = len(reviews)
        db["restaurants"][restaurant_id] = rest
