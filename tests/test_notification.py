"""
tests/test_notification.py
===========================
Tests for app/notification.py
Dependency chain: notification → db
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db, get_db_connection
from app.notification import (
    send_notification, get_notifications, mark_as_read,
    mark_all_read, get_unread_count,
)


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


def test_send_notification_creates_record(clean):
    notif = send_notification("usr_001", "welcome", {"name": "Test"})
    assert notif["recipient_id"] == "usr_001"
    assert notif["type"] == "welcome"
    assert notif["is_read"] is False
    assert "id" in notif


def test_send_notification_resolves_template(clean):
    notif = send_notification("usr_001", "payment_success", {"amount": 350})
    assert "350" in notif["body"]


def test_send_notification_unknown_type(clean):
    notif = send_notification("usr_001", "custom_event", {})
    assert notif["type"] == "custom_event"


def test_get_notifications_returns_all(clean):
    send_notification("usr_002", "welcome", {})
    send_notification("usr_002", "order_confirmed", {"order_id": "ord_001"})
    notifs = get_notifications("usr_002")
    assert len(notifs) == 2


def test_get_notifications_unread_only(clean):
    notif = send_notification("usr_003", "welcome", {})
    send_notification("usr_003", "order_confirmed", {"order_id": "ord_002"})
    mark_as_read("usr_003", notif["id"])
    unread = get_notifications("usr_003", unread_only=True)
    assert len(unread) == 1


def test_get_notifications_empty_for_new_user(clean):
    notifs = get_notifications("usr_nobody")
    assert notifs == []


def test_mark_as_read_returns_true(clean):
    notif = send_notification("usr_004", "welcome", {})
    result = mark_as_read("usr_004", notif["id"])
    assert result is True


def test_mark_as_read_marks_correct_notif(clean):
    n1 = send_notification("usr_005", "welcome", {})
    n2 = send_notification("usr_005", "order_confirmed", {"order_id": "o1"})
    mark_as_read("usr_005", n1["id"])
    all_notifs = get_notifications("usr_005")
    n1_state = next(n for n in all_notifs if n["id"] == n1["id"])
    n2_state = next(n for n in all_notifs if n["id"] == n2["id"])
    assert n1_state["is_read"] is True
    assert n2_state["is_read"] is False


def test_mark_as_read_nonexistent_returns_false(clean):
    result = mark_as_read("usr_006", "notif_ghost")
    assert result is False


def test_mark_all_read_returns_count(clean):
    send_notification("usr_007", "welcome", {})
    send_notification("usr_007", "loyalty_earned", {"points": 10, "new_total": 10})
    send_notification("usr_007", "order_confirmed", {"order_id": "o2"})
    count = mark_all_read("usr_007")
    assert count == 3


def test_mark_all_read_clears_unread(clean):
    send_notification("usr_008", "welcome", {})
    mark_all_read("usr_008")
    assert get_unread_count("usr_008") == 0


def test_get_unread_count_accurate(clean):
    send_notification("usr_009", "welcome", {})
    send_notification("usr_009", "order_confirmed", {"order_id": "o3"})
    assert get_unread_count("usr_009") == 2


def test_notifications_sorted_newest_first(clean):
    import time
    send_notification("usr_010", "welcome", {})
    time.sleep(0.01)
    send_notification("usr_010", "order_confirmed", {"order_id": "o4"})
    notifs = get_notifications("usr_010")
    assert notifs[0]["type"] == "order_confirmed"


def test_urgent_notifications_use_sms_channel(clean):
    notif = send_notification("usr_011", "payment_failed", {})
    assert "sms" in notif["channel"]


def test_silent_notifications_use_push_silent(clean):
    notif = send_notification("usr_011", "agent_location_update", {})
    assert notif["channel"] == "push_silent"
