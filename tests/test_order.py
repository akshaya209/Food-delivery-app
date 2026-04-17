import pytest
from app.order import create_order

def test_create_order_success():
    result = create_order("Akshaya", [{"name": "Pizza"}])
    assert result["status"] == "created"

def test_create_order_empty():
    with pytest.raises(ValueError):
        create_order("Akshaya", [])
