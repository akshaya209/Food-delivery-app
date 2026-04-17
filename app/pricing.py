def calculate_total(items):
    return sum(item["price"] for item in items)

def apply_discount(total, discount_rate=0.1):  # FIXED
    return total * (1 - discount_rate)

def add_tax(total):
    return total * 1.05
