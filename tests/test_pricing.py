from app.pricing import calculate_total, apply_discount

def test_calculate_total():
    items = [{"price": 100}, {"price": 200}]
    assert calculate_total(items) == 300

def test_apply_discount():
    # Test with two arguments (total, discount_rate)
    # 200 - (200 * 0.1) = 180
    assert apply_discount(200, 0.1) == 180
    
    # Test with only one argument (uses default 0.1)
    # 100 - (100 * 0.1) = 90
    assert apply_discount(100) == 90

    # Test with multiple extra arguments (should still work and ignore them)
    assert apply_discount(200, 0.5, "extra", True) == 100
