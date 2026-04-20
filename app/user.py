"""
app/user.py
===========
Food Delivery App — User Profile & Account Management
"""

from app.db import get_db_connection
from app.notification import send_notification
import hashlib
import re
from datetime import datetime


class UserNotFoundError(Exception):
    pass


class UserValidationError(Exception):
    pass


def create_user(email: str, name: str, phone: str, password: str) -> dict:
    """Create a new user account. Returns user dict on success."""
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise UserValidationError(f"Invalid email: {email}")
    if len(password) < 8:
        raise UserValidationError("Password must be at least 8 characters")
    if not re.match(r"^\+?\d{10,15}$", phone):
        raise UserValidationError(f"Invalid phone: {phone}")

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user = {
        "id": f"usr_{hashlib.md5(email.encode()).hexdigest()[:8]}",
        "email": email,
        "name": name,
        "phone": phone,
        "password_hash": password_hash,
        "created_at": datetime.utcnow().isoformat(),
        "is_active": True,
        "loyalty_points": 0,
    }
    db = get_db_connection()
    db["users"][user["id"]] = user
    send_notification(user["id"], "welcome", {"name": name})
    return user


def get_user_by_id(user_id: str) -> dict:
    """Fetch user by ID. Raises UserNotFoundError if not found."""
    db = get_db_connection()
    user = db["users"].get(user_id)
    if not user:
        raise UserNotFoundError(f"User {user_id} not found")
    return user


def get_user_by_email(email: str) -> dict:
    """Fetch user by email address."""
    db = get_db_connection()
    for user in db["users"].values():
        if user["email"] == email:
            return user
    raise UserNotFoundError(f"No user with email {email}")


def update_user_profile(user_id: str, updates: dict) -> dict:
    """Update mutable user fields (name, phone, address)."""
    allowed_fields = {"name", "phone", "address", "profile_picture"}
    user = get_user_by_id(user_id)
    for key, value in updates.items():
        if key in allowed_fields:
            user[key] = value
    user["updated_at"] = datetime.utcnow().isoformat()
    db = get_db_connection()
    db["users"][user_id] = user
    return user


def deactivate_user(user_id: str) -> bool:
    """Soft-delete a user account."""
    user = get_user_by_id(user_id)
    user["is_active"] = False
    user["deactivated_at"] = datetime.utcnow().isoformat()
    db = get_db_connection()
    db["users"][user_id] = user
    send_notification(user_id, "account_deactivated", {})
    return True


def add_loyalty_points(user_id: str, points: int) -> int:
    """Add loyalty points to a user's account. Returns new total."""
    user = get_user_by_id(user_id)
    user["loyalty_points"] = user.get("loyalty_points", 0) + points
    db = get_db_connection()
    db["users"][user_id] = user
    return user["loyalty_points"]


def get_user_addresses(user_id: str) -> list:
    """Return all saved delivery addresses for a user."""
    user = get_user_by_id(user_id)
    return user.get("addresses", [])


def add_user_address(user_id: str, address: dict) -> list:
    """Add a delivery address to the user's saved addresses."""
    required = {"label", "street", "city", "pincode"}
    if not required.issubset(address.keys()):
        raise UserValidationError(f"Address missing fields: {required - address.keys()}")
    user = get_user_by_id(user_id)
    addresses = user.get("addresses", [])
    address["id"] = f"addr_{len(addresses) + 1}"
    addresses.append(address)
    user["addresses"] = addresses
    db = get_db_connection()
    db["users"][user_id] = user
    return addresses
