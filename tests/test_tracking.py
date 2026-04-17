from app.tracking import get_location, update_status

def test_location():
    assert "lat" in get_location(1)

def test_status():
    assert update_status(1) == "moving"
