"""
Tests for strip_blockquote_prefix function.

This module tests the blockquote prefix stripping logic that removes `> ` (or bare
`>`) prefixes from Mermaid diagram content extracted from Markdown blockquotes.

Without this function, a fenced code block nested inside a Markdown blockquote
retains `> ` on every line, causing mermaid-cli to fail with UnknownDiagramError
when it tries to parse `> flowchart LR`.

The function applies a conservative all-or-nothing rule: prefixes are only stripped
when every non-empty line starts with `>`, so non-blockquoted content is never
accidentally corrupted.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import convert  # noqa: E402
from convert import strip_blockquote_prefix  # noqa: E402 (not yet implemented)


class TestStripBlockquotePrefixHappyPath:
    """Happy-path tests: all non-empty lines carry a `> ` prefix."""

    def test_strip_blockquote_prefix_all_lines_with_space_returns_clean_text(self):
        """
        Test that `> ` prefixes are removed from every line.

        Given: Mermaid content where every line starts with `> `
        When: strip_blockquote_prefix is called
        Then: The `> ` prefix is stripped from each line, leaving clean diagram text
        """
        text = "> flowchart LR\n> A --> B"
        expected = "flowchart LR\nA --> B"

        result = strip_blockquote_prefix(text)

        assert result == expected

    def test_strip_blockquote_prefix_bare_gt_on_blank_lines_returns_empty_lines(self):
        """
        Test that bare `>` on blank blockquote continuation lines becomes an empty line.

        Given: Mermaid content with `> ` on diagram lines and bare `>` on blank lines
        When: strip_blockquote_prefix is called
        Then: `> ` is stripped from diagram lines and bare `>` becomes an empty string
        """
        text = "> flowchart LR\n>\n> A --> B"
        expected = "flowchart LR\n\nA --> B"

        result = strip_blockquote_prefix(text)

        assert result == expected

    def test_strip_blockquote_prefix_frontmatter_block_returns_clean_yaml(self):
        """
        Test that YAML frontmatter wrapped in blockquote markers is fully stripped.

        Given: A Mermaid block with YAML frontmatter where every line starts with `> `
        When: strip_blockquote_prefix is called
        Then: All `> ` prefixes are removed, leaving valid YAML + diagram text
        """
        text = "> ---\n> config:\n>   theme: neutral\n> ---\n> flowchart LR"
        expected = "---\nconfig:\n  theme: neutral\n---\nflowchart LR"

        result = strip_blockquote_prefix(text)

        assert result == expected

    def test_strip_blockquote_prefix_indentation_preserved_after_stripping(self):
        """
        Test that indentation within diagram lines is preserved after prefix removal.

        Given: Mermaid content where diagram lines have leading spaces after `> `
        When: strip_blockquote_prefix is called
        Then: `> ` is removed but the following spaces (indentation) are kept intact
        """
        text = "> flowchart LR\n>     A --> B"
        expected = "flowchart LR\n    A --> B"

        result = strip_blockquote_prefix(text)

        assert result == expected

    def test_strip_blockquote_prefix_single_line_returns_stripped_line(self):
        """
        Test stripping when the input is a single blockquoted line.

        Given: A single line starting with `> `
        When: strip_blockquote_prefix is called
        Then: The `> ` prefix is removed and the remaining text is returned
        """
        text = "> flowchart LR"
        expected = "flowchart LR"

        result = strip_blockquote_prefix(text)

        assert result == expected

    def test_strip_blockquote_prefix_mixed_gt_styles_all_prefixed_returns_stripped(
        self,
    ):
        """
        Test that both `> ` and bare `>content` are treated as valid prefixes.

        Given: A block where some lines use `> ` and others use `>` with no space
        When: strip_blockquote_prefix is called
        Then: Both prefix forms are stripped, content after `>` is preserved
        """
        text = ">flowchart LR\n> A --> B"
        expected = "flowchart LR\nA --> B"

        result = strip_blockquote_prefix(text)

        assert result == expected


class TestStripBlockquotePrefixPassthrough:
    """Passthrough tests: function must return input unchanged when stripping is unsafe."""

    def test_strip_blockquote_prefix_no_prefix_returns_unchanged(self):
        """
        Test that plain (non-blockquoted) content is returned unchanged.

        Given: Mermaid content with no `> ` prefix on any line
        When: strip_blockquote_prefix is called
        Then: The text is returned exactly as-is (no mutation)
        """
        text = "flowchart LR\nA --> B"
        expected = "flowchart LR\nA --> B"

        result = strip_blockquote_prefix(text)

        assert result == expected

    def test_strip_blockquote_prefix_partial_blockquote_returns_unchanged(self):
        """
        Test that partially-blockquoted content is returned unchanged (safety rule).

        Given: Content where only some non-empty lines start with `> `
        When: strip_blockquote_prefix is called
        Then: The text is returned unchanged to avoid corrupting mixed content
        """
        text = "> flowchart LR\nA --> B"
        expected = "> flowchart LR\nA --> B"

        result = strip_blockquote_prefix(text)

        assert result == expected

    def test_strip_blockquote_prefix_mixed_prefix_and_plain_returns_unchanged(self):
        """
        Test that a multi-line block mixing prefixed and plain lines is not modified.

        Given: A three-line block where the middle line lacks the `> ` prefix
        When: strip_blockquote_prefix is called
        Then: The full text is returned unchanged
        """
        text = "> flowchart LR\nA --> B\n> C --> D"
        expected = "> flowchart LR\nA --> B\n> C --> D"

        result = strip_blockquote_prefix(text)

        assert result == expected


class TestStripBlockquotePrefixEdgeCases:
    """Edge-case tests: empty inputs, whitespace-only lines, boundary conditions."""

    def test_strip_blockquote_prefix_empty_string_returns_empty_string(self):
        """
        Test that an empty string is handled without error.

        Given: An empty string
        When: strip_blockquote_prefix is called
        Then: An empty string is returned
        """
        result = strip_blockquote_prefix("")

        assert result == ""

    def test_strip_blockquote_prefix_only_newlines_returns_unchanged(self):
        """
        Test that a string containing only newlines is returned unchanged.

        Given: A string with only newline characters (no non-empty lines)
        When: strip_blockquote_prefix is called
        Then: The original string is returned unchanged
        """
        text = "\n\n"
        expected = "\n\n"

        result = strip_blockquote_prefix(text)

        assert result == expected

    def test_strip_blockquote_prefix_bare_gt_only_lines_returns_empty_lines(self):
        """
        Test a block where every line is a bare `>` (empty blockquote lines).

        Given: Multiple lines each containing only `>`
        When: strip_blockquote_prefix is called
        Then: Each line becomes empty after the `>` is stripped
        """
        text = ">\n>\n>"
        expected = "\n\n"

        result = strip_blockquote_prefix(text)

        assert result == expected

    def test_strip_blockquote_prefix_gt_without_space_single_content_line(self):
        """
        Test bare `>content` (no space after `>`) is treated as a valid blockquote prefix.

        Given: A line starting with `>` immediately followed by content (no space)
        When: strip_blockquote_prefix is called
        Then: The leading `>` is stripped and the rest of the content is preserved
        """
        text = ">flowchart LR\n>A --> B"
        expected = "flowchart LR\nA --> B"

        result = strip_blockquote_prefix(text)

        assert result == expected


class TestStripBlockquotePrefixIntegration:
    """Integration tests for blockquoted Mermaid handling in process_markdown."""

    def test_process_markdown_strips_blockquote_prefix_before_mermaid_conversion(
        self, tmp_path
    ):
        """
        Test that process_markdown strips `> ` prefixes from blockquoted Mermaid blocks
        before the content is passed to convert_mermaid_to_svg.

        Given: A Markdown file containing a Mermaid block nested inside a blockquote
        When: process_markdown is called with a mocked convert_mermaid_to_svg
        Then: The mock receives content with no `> ` prefixes
        """
        # Create a Markdown file with a blockquoted mermaid block
        md_content = "# Diagram\n\n```mermaid\n> flowchart LR\n>     A --> B\n```\n"
        md_file = tmp_path / "input.md"
        md_file.write_text(md_content)

        captured_calls = []

        def fake_convert(mermaid_code, index, temp_dir=None):
            captured_calls.append(mermaid_code)
            return (f"diagram_{index}.svg", None)

        with patch.object(convert, "convert_mermaid_to_svg", side_effect=fake_convert):
            convert.process_markdown(str(md_file), engine=None, temp_dir=str(tmp_path))

        assert len(captured_calls) == 1, "convert_mermaid_to_svg should be called once"
        received = captured_calls[0]

        blockquoted_lines = [ln for ln in received.splitlines() if ln.startswith("> ")]
        assert blockquoted_lines == [], (
            f"Blockquote prefix `> ` should have been stripped before passing to "
            f"convert_mermaid_to_svg, but these lines still have it:\n{blockquoted_lines}"
        )
        assert "flowchart LR" in received
        assert "A --> B" in received

    def test_process_markdown_does_not_strip_plain_mermaid_blocks(self, tmp_path):
        """
        Test that process_markdown leaves non-blockquoted Mermaid blocks unchanged.

        Given: A Markdown file with a plain (non-blockquoted) Mermaid block
        When: process_markdown is called
        Then: The content passed to convert_mermaid_to_svg is unmodified
        """
        md_content = "# Diagram\n\n```mermaid\nflowchart LR\n    A --> B\n```\n"
        md_file = tmp_path / "input.md"
        md_file.write_text(md_content)

        captured_calls = []

        def fake_convert(mermaid_code, index, temp_dir=None):
            captured_calls.append(mermaid_code)
            return (f"diagram_{index}.svg", None)

        with patch.object(convert, "convert_mermaid_to_svg", side_effect=fake_convert):
            convert.process_markdown(str(md_file), engine=None, temp_dir=str(tmp_path))

        assert len(captured_calls) == 1
        received = captured_calls[0]

        assert "flowchart LR" in received
        assert "    A --> B" in received

    def test_process_markdown_handles_blockquoted_mermaid_with_frontmatter(
        self, tmp_path
    ):
        """
        Test that process_markdown correctly strips a blockquoted Mermaid block that
        also contains YAML frontmatter.

        Given: A Markdown file with a blockquoted Mermaid block containing YAML
               frontmatter captured via `> ` blockquote markers
        When: process_markdown is called
        Then: The content passed to convert_mermaid_to_svg has no `> ` prefixes and
              the diagram type keyword is present unmodified
        """
        md_content = (
            "```mermaid\n"
            "> ---\n"
            "> title: My Diagram\n"
            "> ---\n"
            "> flowchart LR\n"
            ">     A --> B\n"
            "```\n"
        )
        md_file = tmp_path / "input.md"
        md_file.write_text(md_content)

        captured_calls = []

        def fake_convert(mermaid_code, index, temp_dir=None):
            captured_calls.append(mermaid_code)
            return (f"diagram_{index}.svg", "My Diagram")

        with patch.object(convert, "convert_mermaid_to_svg", side_effect=fake_convert):
            convert.process_markdown(str(md_file), engine=None, temp_dir=str(tmp_path))

        assert len(captured_calls) == 1
        received = captured_calls[0]

        blockquoted_lines = [ln for ln in received.splitlines() if ln.startswith("> ")]
        assert blockquoted_lines == [], (
            "Blockquote prefixes must be stripped before calling convert_mermaid_to_svg"
        )
        assert "flowchart LR" in received


"""
Test Summary
============
Total Tests: 16
- Happy Path: 6  (TestStripBlockquotePrefixHappyPath)
- Passthrough / Safety: 3  (TestStripBlockquotePrefixPassthrough)
- Edge Cases: 4  (TestStripBlockquotePrefixEdgeCases)
- Integration: 3  (TestStripBlockquotePrefixIntegration — via process_markdown mock)

Coverage Areas:
- Stripping `> ` prefix from all non-empty lines
- Handling bare `>` (blockquote continuation / blank lines)
- Preserving indentation after prefix removal
- Safety rule: no stripping when not all non-empty lines are prefixed
- Empty string input
- Whitespace-only / newline-only inputs
- YAML frontmatter inside a blockquoted Mermaid block
- Integration: process_markdown passes clean content to convert_mermaid_to_svg
- Integration: non-blockquoted blocks are not modified
"""
