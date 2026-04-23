def is_voucher_valid(code, min_spend, current_total):
    if code.startswith("SAVE") and current_total >= min_spend:
        return True
    return False
