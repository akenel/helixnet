"""
This is a simple sanity check test file.

Run this first to confirm that:
1. Pytest is installed and accessible within your development environment.
2. Pytest can discover and run test functions.

It purposefully does NOT use any database fixtures or application dependencies.

To run this file:
pytest app/tests/test_simple_sanity.py
(Adjust path if needed)
"""


# Test 1: Simple assertion check
def test_numbers_add_up():
    """Confirms basic Python arithmetic works as expected."""
    # Arrange
    a = 5
    b = 3
    # Act
    result = a + b
    # Assert
    assert result == 8


# Test 2: List operations check
def test_list_length_and_content():
    """Confirms basic list operations work."""
    # Arrange
    my_list = [10, 20, 30]
    # Act & Assert
    assert len(my_list) == 3
    assert 20 in my_list
    assert my_list[0] == 10


# Test 3: String manipulation (a happy-path example)
def test_string_capitalization():
    """Tests basic string methods."""
    assert "hello world".upper() == "HELLO WORLD"
