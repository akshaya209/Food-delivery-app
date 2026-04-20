"""
tests/test_search.py
====================
Tests for app/search.py
Dependency chain: search → db, restaurant, menu
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import reset_db
from app.restaurant import register_restaurant
from app.menu import add_menu_item
from app.inventory import set_stock
from app.search import (
    search_restaurants, search_dishes, index_restaurant,
    index_menu_item, SearchError,
)


@pytest.fixture(autouse=True)
def clean():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def populated(clean):
    r1 = register_restaurant(
        "Taj Biryani", "owner_s1", "Indian",
        {"street": "1 MG", "city": "Chennai", "pincode": "600001",
         "lat": 13.08, "lng": 80.27},
        {"open": "10:00", "close": "23:00"},
    )
    r2 = register_restaurant(
        "Dragon Wok", "owner_s2", "Chinese",
        {"street": "5 Anna", "city": "Chennai", "pincode": "600002",
         "lat": 13.09, "lng": 80.28},
        {"open": "11:00", "close": "22:00"},
    )
    item1 = add_menu_item(r1["id"], {
        "name": "Chicken Biryani", "price": 220.0,
        "category": "Rice", "description": "Aromatic basmati rice with chicken",
    })
    item2 = add_menu_item(r2["id"], {
        "name": "Fried Rice", "price": 150.0,
        "category": "Rice", "description": "Classic Chinese fried rice",
    })
    set_stock(r1["id"], item1["id"], 30)
    set_stock(r2["id"], item2["id"], 20)
    index_restaurant(r1)
    index_restaurant(r2)
    index_menu_item(r1["id"], item1)
    index_menu_item(r2["id"], item2)
    return {"r1": r1, "r2": r2, "item1": item1, "item2": item2}


def test_search_restaurants_by_name(populated):
    results = search_restaurants("Biryani")
    names = [r["name"] for r in results]
    assert "Taj Biryani" in names


def test_search_restaurants_by_cuisine(populated):
    results = search_restaurants("Chinese")
    names = [r["name"] for r in results]
    assert "Dragon Wok" in names


def test_search_restaurants_case_insensitive(populated):
    results = search_restaurants("biryani")
    assert len(results) >= 1


def test_search_restaurants_no_results(populated):
    results = search_restaurants("Sushi Nonexistent XYZ")
    assert results == []


def test_search_dishes_by_name(populated):
    results = search_dishes("Biryani")
    names = [r["name"] for r in results]
    assert "Chicken Biryani" in names


def test_search_dishes_by_keyword(populated):
    results = search_dishes("rice")
    assert len(results) >= 2  # both items have "rice"


def test_search_dishes_returns_restaurant_info(populated):
    results = search_dishes("Chicken Biryani")
    assert len(results) >= 1
    assert "restaurant_id" in results[0]


def test_search_restaurants_by_city(populated):
    results = search_restaurants("Chennai")
    assert len(results) >= 2


def test_search_empty_query(populated):
    with pytest.raises(SearchError, match="empty"):
        search_restaurants("")


def test_search_dishes_empty_query(populated):
    with pytest.raises(SearchError):
        search_dishes("")


def test_index_restaurant_adds_to_index(clean):
    r = register_restaurant(
        "Index Test", "own", "Korean",
        {"street": "1 K", "city": "Mumbai", "pincode": "400001",
         "lat": 19.07, "lng": 72.87},
        {"open": "10:00", "close": "22:00"},
    )
    index_restaurant(r)
    results = search_restaurants("Index Test")
    assert len(results) >= 1
