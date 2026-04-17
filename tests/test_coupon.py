from app.coupon import apply_coupon

def test_coupon():
    assert apply_coupon(100) == 90
