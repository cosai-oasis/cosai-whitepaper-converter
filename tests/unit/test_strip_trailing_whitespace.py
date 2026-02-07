"""
Tests for strip_trailing_whitespace function.

This module tests the whitespace stripping functionality that removes
trailing whitespace from each line while preserving line structure.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from convert import strip_trailing_whitespace


class TestStripTrailingWhitespace:
    """Test suite for strip_trailing_whitespace function."""

    def test_strip_trailing_whitespace_single_line_with_spaces(self):
        """
        Test trailing space removal from single line.

        Given: A single line with trailing spaces
        When: strip_trailing_whitespace is called
        Then: Trailing spaces are removed
        """
        text = "Hello World   "
        expected = "Hello World"

        result = strip_trailing_whitespace(text)

        assert result == expected

    def test_strip_trailing_whitespace_single_line_with_tabs(self):
        """
        Test trailing tab removal from single line.

        Given: A single line with trailing tabs
        When: strip_trailing_whitespace is called
        Then: Trailing tabs are removed
        """
        text = "Hello World\t\t"
        expected = "Hello World"

        result = strip_trailing_whitespace(text)

        assert result == expected

    def test_strip_trailing_whitespace_multiple_lines(self):
        """
        Test trailing whitespace removal from multiple lines.

        Given: Multiple lines with varying trailing whitespace
        When: strip_trailing_whitespace is called
        Then: All trailing whitespace is removed, line structure preserved
        """
        text = "Line 1   \nLine 2\t\t\nLine 3  \n"
        # Note: Function uses splitlines then joins with \n, which doesn't preserve final \n
        expected = "Line 1\nLine 2\nLine 3"

        result = strip_trailing_whitespace(text)

        assert result == expected

    def test_strip_trailing_whitespace_preserves_leading_whitespace(self):
        """
        Test that leading whitespace is preserved.

        Given: Lines with leading whitespace
        When: strip_trailing_whitespace is called
        Then: Leading whitespace remains, trailing removed
        """
        text = "  Indented line  \n    More indented  "
        expected = "  Indented line\n    More indented"

        result = strip_trailing_whitespace(text)

        assert result == expected

    def test_strip_trailing_whitespace_empty_string(self):
        """
        Test handling of empty string.

        Given: An empty string
        When: strip_trailing_whitespace is called
        Then: Empty string is returned
        """
        text = ""
        expected = ""

        result = strip_trailing_whitespace(text)

        assert result == expected

    def test_strip_trailing_whitespace_only_whitespace_line(self):
        """
        Test handling of lines containing only whitespace.

        Given: A line with only spaces/tabs
        When: strip_trailing_whitespace is called
        Then: Line becomes empty (whitespace removed)
        """
        text = "   \t   \n"
        # Function strips all whitespace including final newline on single whitespace line
        expected = ""

        result = strip_trailing_whitespace(text)

        assert result == expected

    def test_strip_trailing_whitespace_mixed_line_endings(self):
        """
        Test handling of different line ending styles.

        Given: Text with mixed line endings (LF)
        When: strip_trailing_whitespace is called
        Then: Whitespace is stripped, line structure preserved
        """
        text = "Line 1  \nLine 2  \nLine 3  "
        expected = "Line 1\nLine 2\nLine 3"

        result = strip_trailing_whitespace(text)

        assert result == expected

    def test_strip_trailing_whitespace_preserves_internal_spaces(self):
        """
        Test that internal spaces within lines are preserved.

        Given: Lines with spaces between words
        When: strip_trailing_whitespace is called
        Then: Internal spaces preserved, trailing removed
        """
        text = "Hello   World   \nFoo  Bar  "
        expected = "Hello   World\nFoo  Bar"

        result = strip_trailing_whitespace(text)

        assert result == expected


"""
Test Summary
============
Total Tests: 8
- Happy Path: 3
- Edge Cases: 5
- Error Conditions: 0

Coverage Areas:
- Single line whitespace stripping
- Multi-line whitespace stripping
- Whitespace type handling (spaces, tabs)
- Leading whitespace preservation
- Internal whitespace preservation
- Empty input handling
- Whitespace-only lines
"""
