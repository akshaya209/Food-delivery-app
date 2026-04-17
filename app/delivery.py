def estimate_time(distance):
    if distance < 0:
        raise ValueError("Invalid distance")
    return distance * 5   # FIXED

def assign_driver(order):
    return "driver_assigned"

def track_order(order_id):
    return "on_the_way"
