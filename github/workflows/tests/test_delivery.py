import pytest
from app.delivery import estimate_time

def test_estimate_time():
    assert estimate_time(10) == 50

def test_invalid_distance():
    with pytest.raises(ValueError):
        estimate_time(-5)
