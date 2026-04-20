"""
app/db.py
=========
Food Delivery App — In-memory database (simulates SQL/NoSQL store).
All app modules import this to read/write shared state.
"""

_DB: dict = {
    "users": {},
    "restaurants": {},
    "menus": {},
    "carts": {},
    "orders": {},
    "payments": {},
    "deliveries": {},
    "coupons": {},
    "loyalty_ledger": {},
    "reviews": {},
    "notifications": {},
    "inventory": {},
    "search_index": {},
    "analytics_events": [],
    "support_tickets": {},
    "refunds": {},
}


def get_db_connection() -> dict:
    """Return the singleton in-memory DB."""
    return _DB


def reset_db() -> None:
    """Reset all tables — used in tests."""
    for key in _DB:
        if isinstance(_DB[key], dict):
            _DB[key].clear()
        elif isinstance(_DB[key], list):
            _DB[key].clear()
