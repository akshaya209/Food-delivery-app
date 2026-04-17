def create_order(user, items):
    if not items:
        raise ValueError("Empty order")
    return {
        "user": user,
        "items": items,
        "status": "created"   # FIXED
    }

def cancel_order(order):
    return "cancelled"

def update_order(order, items):
    order["items"] = items
    return order
