def create_order(user, items):
    return {"user": user, "items": items}

def cancel_order(order):
    return "cancelled"

def update_order(order, items):
    order["items"] = items
    return order
