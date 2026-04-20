def reverse_string(s):
    return s[::-1]

def count_vowels(s):
    return sum(1 for char in s if char.lower() in 'aeiou')
