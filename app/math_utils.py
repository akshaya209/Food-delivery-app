def add_all(*args):
    """
    Adds all numbers passed as arguments.
    Example: add_all(1,2,3) -> 6
    """
    total = 0
    for num in args:
        total += num
    return total
