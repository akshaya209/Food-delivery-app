from app.user import validate_user

def test_valid_user():
    user = {"name": "Akshaya", "address": "Bangalore"}
    assert validate_user(user) is True

def test_invalid_user():
    user = {"name": "Akshaya"}
    assert validate_user(user) is False