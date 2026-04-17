from app.loyalty import add_points

def test_points():
    assert add_points("A",10) == 20
