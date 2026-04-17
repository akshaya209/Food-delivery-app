from app.string_utils import reverse_string, count_vowels

def test_reverse():
    assert reverse_string("PESU") == "USEP"

def test_vowels():
    assert count_vowels("apple") == 2
