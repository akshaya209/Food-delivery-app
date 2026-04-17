from app.payment import process_payment, refund, payment_status

def test_process_payment():
    assert process_payment(100) == "success"

def test_refund():
    assert refund(50) == "refunded"

def test_status():
    assert payment_status(1) == "completed"

def test_payment_positive():
    assert process_payment(10) == "success"

def test_refund_positive():
    assert refund(10) == "refunded"
