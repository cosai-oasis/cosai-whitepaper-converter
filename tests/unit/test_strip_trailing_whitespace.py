"""
Tests for strip_trailing_whitespace function.

This module tests the whitespace stripping functionality that removes
trailing whitespace from each line while preserving Markdown hard line
breaks (2+ trailing spaces) and line structure.
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
        Test trailing space handling from single line.

        Given: A single line with 3 trailing spaces (Markdown hard break)
        When: strip_trailing_whitespace is called
        Then: Exactly 2 trailing spaces are preserved (hard break normalized)
        """
        text = "Hello World   "
        expected = "Hello World  "

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
        Test trailing whitespace handling from multiple lines.

        Given: Multiple lines with varying trailing whitespace
        When: strip_trailing_whitespace is called
        Then: Hard breaks (2+ spaces) preserved, tabs stripped, line structure preserved
        """
        text = "Line 1   \nLine 2\t\t\nLine 3  \n"
        expected = "Line 1  \nLine 2\nLine 3  "

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

    def test_strip_trailing_whitespace_preserves_internal_spaces(self):
        """
        Test that internal spaces within lines are preserved.

        Given: Lines with spaces between words and trailing spaces
        When: strip_trailing_whitespace is called
        Then: Internal spaces preserved, hard breaks preserved
        """
        text = "Hello   World   \nFoo  Bar  "
        expected = "Hello   World  \nFoo  Bar  "

        result = strip_trailing_whitespace(text)

        assert result == expected

    def test_preserves_hard_line_break_two_trailing_spaces(self):
        """
        Given: A line ending with exactly two trailing spaces (Markdown hard break)
        When: strip_trailing_whitespace is called
        Then: Exactly two trailing spaces are preserved
        """
        text = "First line  \nSecond line"
        expected = "First line  \nSecond line"

        result = strip_trailing_whitespace(text)

        assert result == expected

    def test_preserves_hard_line_break_more_than_two_trailing_spaces(self):
        """
        Given: A line ending with more than two trailing spaces
        When: strip_trailing_whitespace is called
        Then: Exactly two trailing spaces are preserved (normalized)
        """
        text = "First line     \nSecond line"
        expected = "First line  \nSecond line"

        result = strip_trailing_whitespace(text)

        assert result == expected

    def test_strips_single_trailing_space(self):
        """
        Given: A line ending with exactly one trailing space (not a hard break)
        When: strip_trailing_whitespace is called
        Then: The single trailing space is stripped
        """
        text = "Not a break \nNext line"
        expected = "Not a break\nNext line"

        result = strip_trailing_whitespace(text)

        assert result == expected

    def test_hard_break_with_leading_whitespace(self):
        """
        Given: An indented line ending with two trailing spaces
        When: strip_trailing_whitespace is called
        Then: Leading whitespace preserved, two trailing spaces preserved
        """
        text = "    Indented line  \nNext"
        expected = "    Indented line  \nNext"

        result = strip_trailing_whitespace(text)

        assert result == expected

    def test_multiple_hard_breaks_in_text(self):
        """
        Given: Multiple lines with hard breaks mixed with normal lines
        When: strip_trailing_whitespace is called
        Then: Hard breaks preserved, normal trailing whitespace stripped
        """
        text = "Line A  \nLine B   \nLine C \nLine D  "
        expected = "Line A  \nLine B  \nLine C\nLine D  "

        result = strip_trailing_whitespace(text)

        assert result == expected
