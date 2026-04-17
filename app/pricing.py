def calculate_total(items):
    # FIX: handle dict input
    return sum(item["price"] for item in items)

def apply_discount(total):
    return total * 0.9

def add_tax(total):
    return total * 1.05
