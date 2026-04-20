"""
app/analytics.py
================
Food Delivery App — Analytics & Event Tracking
Depends on: db  (NO cross-imports to user/order/payment)
"""

from app.db import get_db_connection
from datetime import datetime


class AnalyticsError(Exception):
    pass


def record_event(event_type: str, payload: dict) -> dict:
    """Append an analytics event to the log."""
    db = get_db_connection()
    event = {
        "type": event_type,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat(),
    }
    db["analytics_events"].append(event)
    return event


def get_events_by_type(event_type: str) -> list:
    """Return all events matching a given type."""
    db = get_db_connection()
    return [e for e in db["analytics_events"] if e["type"] == event_type]


def get_revenue_summary() -> dict:
    """Aggregate revenue from payment_success events."""
    events = get_events_by_type("payment_success")
    total = sum(e["payload"].get("amount", 0.0) for e in events)
    return {
        "total_revenue": round(total, 2),
        "successful_payments": len(events),
    }


def get_top_restaurants(limit: int = 5) -> list:
    """Return restaurants ranked by order count."""
    events = get_events_by_type("order_placed")
    counts: dict = {}
    revenue: dict = {}
    for e in events:
        rid = e["payload"].get("restaurant_id")
        if not rid:
            continue
        counts[rid] = counts.get(rid, 0) + 1
        revenue[rid] = revenue.get(rid, 0.0) + e["payload"].get("total", 0.0)

    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [
        {
            "restaurant_id": rid,
            "order_count": cnt,
            "total_revenue": round(revenue.get(rid, 0.0), 2),
        }
        for rid, cnt in ranked[:limit]
    ]


def get_order_volume_by_day() -> dict:
    """Return order count per day (YYYY-MM-DD)."""
    events = get_events_by_type("order_placed")
    volume: dict = {}
    for e in events:
        day = e["timestamp"][:10]
        if day not in volume:
            volume[day] = {"count": 0, "revenue": 0.0}
        volume[day]["count"] += 1
        volume[day]["revenue"] += e["payload"].get("total", 0.0)
    return volume
