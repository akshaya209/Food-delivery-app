"""
app/auth.py
===========
Food Delivery App — Authentication & Session Management
"""

import hashlib
import hmac
import time
from datetime import datetime, timedelta

from app.user import get_user_by_email, UserNotFoundError
from app.db import get_db_connection

SECRET_KEY = "greenops-food-delivery-secret"
TOKEN_TTL_SECONDS = 3600  # 1 hour


class AuthenticationError(Exception):
    pass


class TokenExpiredError(Exception):
    pass


def _make_token(user_id: str, expiry: float) -> str:
    payload = f"{user_id}:{expiry}"
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def login(email: str, password: str) -> dict:
    """Authenticate user and return session token."""
    try:
        user = get_user_by_email(email)
    except UserNotFoundError:
        raise AuthenticationError("Invalid email or password")

    if not user.get("is_active", True):
        raise AuthenticationError("Account is deactivated")

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if user["password_hash"] != password_hash:
        raise AuthenticationError("Invalid email or password")

    expiry = time.time() + TOKEN_TTL_SECONDS
    token = _make_token(user["id"], expiry)

    db = get_db_connection()
    db.setdefault("sessions", {})[token] = {
        "user_id": user["id"],
        "created_at": datetime.utcnow().isoformat(),
        "expiry": expiry,
    }
    return {"token": token, "user_id": user["id"], "expires_at": expiry}


def logout(token: str) -> bool:
    """Invalidate a session token."""
    db = get_db_connection()
    sessions = db.get("sessions", {})
    if token in sessions:
        del sessions[token]
        return True
    return False


def verify_token(token: str) -> str:
    """Verify token and return user_id. Raises on invalid/expired."""
    db = get_db_connection()
    session = db.get("sessions", {}).get(token)
    if not session:
        raise AuthenticationError("Invalid or unknown token")
    if time.time() > session["expiry"]:
        del db["sessions"][token]
        raise TokenExpiredError("Token has expired — please log in again")
    return session["user_id"]


def refresh_token(token: str) -> dict:
    """Issue a new token before expiry."""
    user_id = verify_token(token)
    logout(token)
    expiry = time.time() + TOKEN_TTL_SECONDS
    new_token = _make_token(user_id, expiry)
    db = get_db_connection()
    db.setdefault("sessions", {})[new_token] = {
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "expiry": expiry,
    }
    return {"token": new_token, "user_id": user_id, "expires_at": expiry}


def change_password(user_id: str, old_password: str, new_password: str) -> bool:
    """Change a user's password after verifying the old one."""
    from app.user import get_user_by_id
    user = get_user_by_id(user_id)
    old_hash = hashlib.sha256(old_password.encode()).hexdigest()
    if user["password_hash"] != old_hash:
        raise AuthenticationError("Incorrect current password")
    if len(new_password) < 8:
        raise AuthenticationError("New password must be at least 8 characters")
    user["password_hash"] = hashlib.sha256(new_password.encode()).hexdigest()
    db = get_db_connection()
    db["users"][user_id] = user
    return True


def require_auth(token: str) -> str:
    """Decorator helper — validates token, returns user_id."""
    return verify_token(token)
