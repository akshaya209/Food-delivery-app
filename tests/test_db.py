from app.db_utils import format_query

def test_query_generation():
    expected = "SELECT * FROM users WHERE id = 101;"
    assert format_query("users", 101) == expected
