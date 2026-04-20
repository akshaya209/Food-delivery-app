"""
tests/test_support.py
=====================
Tests for app/support.py
Dependency chain: support → db, user, order, notification
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db, get_db_connection
from app.user import create_user
from app.support import (
    open_ticket, get_ticket, reply_to_ticket,
    close_ticket, get_user_tickets, SupportError,
)


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def user(clean):
    return create_user("support@test.com", "Support User", "+910000000040", "pass1234")


def test_open_ticket_creates_record(user):
    ticket = open_ticket(user["id"], "order_issue", "My order never arrived", "ord_001")
    assert ticket["user_id"] == user["id"]
    assert ticket["category"] == "order_issue"
    assert ticket["status"] == "open"
    assert "id" in ticket


def test_get_ticket_returns_record(user):
    ticket = open_ticket(user["id"], "payment_issue", "Charged twice", "ord_002")
    fetched = get_ticket(ticket["id"])
    assert fetched["id"] == ticket["id"]


def test_get_ticket_nonexistent_raises(user):
    with pytest.raises(SupportError):
        get_ticket("tkt_nonexistent")


def test_reply_to_ticket_appends_message(user):
    ticket = open_ticket(user["id"], "general", "Question about app", None)
    updated = reply_to_ticket(ticket["id"], "support_agent_01",
                              "Hello! How can we help?", is_agent=True)
    assert len(updated["messages"]) >= 1
    assert updated["messages"][-1]["text"] == "Hello! How can we help?"


def test_reply_to_ticket_notifies_user(user):
    ticket = open_ticket(user["id"], "general", "Help", None)
    reply_to_ticket(ticket["id"], "support_agent_01", "We're on it!", is_agent=True)
    db = get_db_connection()
    notifs = db["notifications"].get(user["id"], [])
    assert any(n["type"] == "support_reply" for n in notifs)


def test_user_can_reply_to_ticket(user):
    ticket = open_ticket(user["id"], "general", "Need help", None)
    reply_to_ticket(ticket["id"], "support_agent_01", "Please describe the issue", is_agent=True)
    updated = reply_to_ticket(ticket["id"], user["id"], "The app crashed", is_agent=False)
    user_msgs = [m for m in updated["messages"] if not m["is_agent"]]
    assert len(user_msgs) >= 1


def test_close_ticket_changes_status(user):
    ticket = open_ticket(user["id"], "resolved", "All good now", None)
    closed = close_ticket(ticket["id"])
    assert closed["status"] == "closed"
    assert "closed_at" in closed


def test_close_already_closed_ticket_raises(user):
    ticket = open_ticket(user["id"], "resolved", "Done", None)
    close_ticket(ticket["id"])
    with pytest.raises(SupportError, match="already closed"):
        close_ticket(ticket["id"])


def test_get_user_tickets_returns_all(user):
    open_ticket(user["id"], "order_issue", "Problem 1", "ord_003")
    open_ticket(user["id"], "payment_issue", "Problem 2", "ord_004")
    tickets = get_user_tickets(user["id"])
    assert len(tickets) == 2


def test_get_user_tickets_empty_for_new_user(clean):
    user2 = create_user("new@test.com", "New", "+910000000041", "pass1234")
    tickets = get_user_tickets(user2["id"])
    assert tickets == []


def test_ticket_has_created_at_timestamp(user):
    ticket = open_ticket(user["id"], "general", "When did I order?", None)
    assert "created_at" in ticket


def test_reply_to_closed_ticket_raises(user):
    ticket = open_ticket(user["id"], "done", "Resolved", None)
    close_ticket(ticket["id"])
    with pytest.raises(SupportError, match="closed"):
        reply_to_ticket(ticket["id"], "agent", "Late reply", is_agent=True)
