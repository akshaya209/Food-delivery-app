def calculate_total(items):
    return sum(item["price"] for item in items)

def apply_discount(*args):
    """
    Applies a discount using variable arguments.
    args[0] = total price (required)
    args[1] = discount rate (optional, defaults to 0.1)
    """
    if not args:
        return 0
    
    total = args[0]
    # Use args[1] if provided, otherwise default to 0.1
    discount_rate = args[1] if len(args) > 1 else 0.1
    
    return total * (1 - discount_rate)

def add_tax(total):
    return total * 1.05
