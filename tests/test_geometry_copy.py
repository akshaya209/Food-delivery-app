from app.geometry import area_of_circle, perimeter_of_square

def test_circle_area():
    assert area_of_circle(1) == 3.141592653589793

def test_square_perimeter():
    assert perimeter_of_square(5) == 20
