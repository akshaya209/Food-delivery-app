from app.voucher import is_voucher_valid

def test_voucher_logic():
    assert is_voucher_valid("SAVE10", 500, 600) is True
    assert is_voucher_valid("SAVE10", 500, 400) is False
