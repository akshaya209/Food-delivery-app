def create_order(user, items):
    if not items:
        raise ValueError("No items in order")
    return {"user": user, "items": items, "status": "created"}