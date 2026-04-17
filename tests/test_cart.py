from app.cart import add_item

def test_cart():
    assert add_item([],1) == [1]
