from app.pricing import calculate_total, apply_discount

def test_calculate_total():
    items = [{"price": 100}, {"price": 200}]
    assert calculate_total(items) == 300

def test_apply_discount():
    assert apply_discount(200, 0.1) == 180
