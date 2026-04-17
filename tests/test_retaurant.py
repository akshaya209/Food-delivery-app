from app.restaurant import list_restaurants

def test_restaurants():
    assert len(list_restaurants()) > 0