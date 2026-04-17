from app.review import add_review

def test_add_review():
    assert add_review("A",5)["rating"] == 5
