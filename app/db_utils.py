"""
app/db_utils.py
===============
Food Delivery App — Database Query Utilities
Depends on: nothing (pure utility functions, no app imports)
"""


def format_query(table: str, record_id) -> str:
    """Generate a simple SELECT query string."""
    return f"SELECT * FROM {table} WHERE id = {record_id};"


def build_insert_query(table: str, data: dict) -> str:
    """Build an INSERT SQL statement from a dict of column→value pairs."""
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    return f"INSERT INTO {table} ({columns}) VALUES ({placeholders});"


def build_update_query(table: str, data: dict, where_col: str, where_val) -> str:
    """Build an UPDATE SQL statement."""
    set_clause = ", ".join(f"{k} = ?" for k in data.keys())
    return f"UPDATE {table} SET {set_clause} WHERE {where_col} = {where_val!r};"


def sanitize_string(value: str) -> str:
    """Remove common SQL injection characters from a string."""
    for ch in ("'", '"', ";", "--", "/*", "*/"):
        value = value.replace(ch, "")
    return value.strip()


def paginate(items: list, page: int = 1, page_size: int = 10) -> dict:
    """Return a paginated slice of a list."""
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }
