from app.auth import login

def test_login():
    assert login("user")
