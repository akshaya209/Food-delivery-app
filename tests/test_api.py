from app.api import get_status_code

def test_api_health():
    assert get_status_code("/health") == 200

def test_api_not_found():
    assert get_status_code("/invalid") == 404
