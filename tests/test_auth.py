"""
tests/test_auth.py
==================
Tests for app/auth.py
Dependency chain: auth -> user -> db, notification
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db
from app.user import create_user
from app.auth import login, logout, verify_token, AuthenticationError, TokenExpiredError


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def user(clean):
    return create_user("auth@test.com", "Auth User", "+910000000001", "securepass")


def test_login_returns_token(user):
    result = login("auth@test.com", "securepass")
    assert "token" in result
    assert result["user_id"] == user["id"]


def test_login_wrong_password_raises(user):
    with pytest.raises(AuthenticationError):
        login("auth@test.com", "wrongpassword")


def test_login_unknown_email_raises(clean):
    with pytest.raises(AuthenticationError):
        login("nobody@test.com", "pass")


def test_verify_token_returns_user_id(user):
    result = login("auth@test.com", "securepass")
    user_id = verify_token(result["token"])
    assert user_id == user["id"]


def test_logout_invalidates_token(user):
    result = login("auth@test.com", "securepass")
    logged_out = logout(result["token"])
    assert logged_out is True
    with pytest.raises(AuthenticationError):
        verify_token(result["token"])
