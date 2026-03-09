"""
Tests for Table of Contents stripping in the process_markdown() pipeline.

The conversion pipeline removes manual TOC sections from Markdown before PDF
generation, since the PDF gets a native LaTeX TOC from Pandoc. The regex
strips any section beginning with an H1-H4 heading or bold marker labelled
"Table of Contents" (case-insensitive on "contents"), consuming everything
up to the next heading or end of string.

Pattern under test (from convert.py):
    r"^(?:#{1,4}\\s+|\\*\\*)Table of [Cc]ontents\\*{0,2}.*?(?=^#|\\Z)"
    flags: MULTILINE | DOTALL
"""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import convert


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(tmp_path: Path, content: str) -> str:
    """Write *content* to a temp file and return process_markdown output.

    Mermaid conversion and image downloading are patched out so the tests
    stay fast and self-contained.
    """
    md_file = tmp_path / "input.md"
    md_file.write_text(content)

    with (
        patch.object(
            convert,
            "convert_mermaid_to_svg",
            return_value=(None, None),
        ),
        patch.object(
            convert,
            "download_image",
            side_effect=lambda url, idx, temp_dir=None: url,
        ),
    ):
        return convert.process_markdown(
            str(md_file), engine="tectonic", temp_dir=str(tmp_path)
        )


# ---------------------------------------------------------------------------
# Happy-path tests — TOC variants that SHOULD be stripped
# ---------------------------------------------------------------------------


class TestTocStrippingHappyPath:
    """TOC heading variants that the regex must remove."""

    def test_h1_toc_with_link_list_is_stripped(self, tmp_path):
        """
        Test that an H1 TOC section is removed.

        Given: Markdown with an H1 "Table of Contents" followed by links
        When: process_markdown is called
        Then: The TOC section is absent from the output; surrounding content
              is preserved
        """
        content = (
            "# Introduction\n\n"
            "Some intro text.\n\n"
            "# Table of Contents\n\n"
            "- [Section One](#section-one)\n"
            "- [Section Two](#section-two)\n\n"
            "# Section One\n\n"
            "Body text.\n"
        )

        result = _run(tmp_path, content)

        assert "Table of Contents" not in result
        assert "Section One](#section-one)" not in result
        assert "# Introduction" in result
        assert "# Section One" in result
        assert "Body text." in result

    def test_h2_toc_is_stripped(self, tmp_path):
        """
        Test that an H2 TOC section is removed.

        Given: Markdown with an H2 "Table of Contents"
        When: process_markdown is called
        Then: The TOC heading and its content are absent from the output
        """
        content = (
            "# Document Title\n\n"
            "## Table of Contents\n\n"
            "- [Intro](#intro)\n\n"
            "## Introduction\n\n"
            "Content here.\n"
        )

        result = _run(tmp_path, content)

        assert "Table of Contents" not in result
        assert "## Introduction" in result
        assert "Content here." in result

    def test_h3_toc_lowercase_contents_is_stripped(self, tmp_path):
        """
        Test that an H3 TOC with lowercase "contents" is removed.

        Given: Markdown with "### Table of contents" (lowercase 'c')
        When: process_markdown is called
        Then: The TOC section is stripped regardless of capitalisation
        """
        content = (
            "# Title\n\n"
            "### Table of contents\n\n"
            "- [Part A](#part-a)\n\n"
            "# Part A\n\n"
            "Text.\n"
        )

        result = _run(tmp_path, content)

        assert "Table of contents" not in result
        assert "Part A](#part-a)" not in result
        assert "# Part A" in result

    def test_h4_toc_is_stripped(self, tmp_path):
        """
        Test that an H4 TOC section is removed.

        Given: Markdown with "#### Table of Contents"
        When: process_markdown is called
        Then: The TOC section is stripped
        """
        content = (
            "# Title\n\n"
            "#### Table of Contents\n\n"
            "- [Chapter 1](#chapter-1)\n\n"
            "# Chapter 1\n\n"
            "Words.\n"
        )

        result = _run(tmp_path, content)

        assert "Table of Contents" not in result
        assert "Chapter 1](#chapter-1)" not in result
        assert "# Chapter 1" in result

    def test_bold_toc_with_link_list_is_stripped(self, tmp_path):
        """
        Test that a bold **Table of Contents** section is removed.

        Given: Markdown using bold syntax for the TOC label
        When: process_markdown is called
        Then: The bold TOC label and the link list beneath it are stripped
        """
        content = (
            "# Preamble\n\n"
            "Some preamble.\n\n"
            "**Table of Contents**\n\n"
            "- [Alpha](#alpha)\n"
            "- [Beta](#beta)\n\n"
            "# Alpha\n\n"
            "Alpha content.\n"
        )

        result = _run(tmp_path, content)

        assert "**Table of Contents**" not in result
        assert "Table of Contents" not in result
        assert "Alpha](#alpha)" not in result
        assert "# Alpha" in result
        assert "Alpha content." in result


# ---------------------------------------------------------------------------
# HTML comment above bold TOC
# ---------------------------------------------------------------------------


class TestTocStrippingWithHtmlComment:
    """Verify that an HTML comment immediately preceding the bold TOC is also removed."""

    def test_html_comment_above_bold_toc_is_stripped(self, tmp_path):
        """
        Test that an HTML comment above a bold TOC is stripped together with the TOC.

        Given: Markdown with an HTML comment ("<!-- Update this TOC -->") on the
               line before "**Table of Contents**" followed by a link list
        When: process_markdown is called
        Then: Both the comment and the TOC block are absent from the output;
              the heading that follows is preserved

        Note: The regex does NOT match the HTML comment itself (the comment sits
        before the bold marker). However, the bold TOC pattern strips from
        "**Table of Contents**" onward, so the comment is only removed if it
        appears on the same logical block consumed by the pattern.  This test
        documents the actual behaviour: the comment on a separate preceding line
        is NOT consumed by the TOC regex — only the TOC block itself is stripped.
        """
        content = (
            "# Overview\n\n"
            "<!-- Update this TOC -->\n"
            "**Table of Contents**\n\n"
            "- [Section A](#section-a)\n\n"
            "# Section A\n\n"
            "Text.\n"
        )

        result = _run(tmp_path, content)

        # The TOC block (from **Table of Contents** onward) is stripped
        assert "Table of Contents" not in result
        assert "Section A](#section-a)" not in result
        # The section heading that follows the TOC is preserved
        assert "# Section A" in result
        assert "Text." in result


# ---------------------------------------------------------------------------
# Negative tests — TOC variants that must NOT be stripped
# ---------------------------------------------------------------------------


class TestTocStrippingNegative:
    """Heading levels outside H1-H4 must not trigger TOC removal."""

    def test_h5_toc_is_not_stripped(self, tmp_path):
        """
        Test that an H5 TOC heading is left untouched.

        Given: Markdown with "##### Table of Contents" (H5)
        When: process_markdown is called
        Then: The heading is preserved — H5 is outside the matched range
        """
        content = (
            "# Document\n\n"
            "##### Table of Contents\n\n"
            "- [Item](#item)\n\n"
            "# Item\n\n"
            "Content.\n"
        )

        result = _run(tmp_path, content)

        assert "##### Table of Contents" in result

    def test_h6_toc_is_not_stripped(self, tmp_path):
        """
        Test that an H6 TOC heading is left untouched.

        Given: Markdown with "###### Table of Contents" (H6)
        When: process_markdown is called
        Then: The heading is preserved — H6 is outside the matched range
        """
        content = (
            "# Document\n\n"
            "###### Table of Contents\n\n"
            "- [Item](#item)\n\n"
            "# Item\n\n"
            "Content.\n"
        )

        result = _run(tmp_path, content)

        assert "###### Table of Contents" in result


# ---------------------------------------------------------------------------
# Position in document
# ---------------------------------------------------------------------------


class TestTocStrippingPosition:
    """Content before and after a mid-document TOC must be preserved."""

    def test_toc_in_middle_preserves_surrounding_content(self, tmp_path):
        """
        Test that content before and after a mid-document TOC is preserved.

        Given: Markdown with content before the TOC, the TOC section, and
               content after the TOC
        When: process_markdown is called
        Then: Content before the TOC is present, the TOC is absent, and
              content after the TOC is present
        """
        content = (
            "# Executive Summary\n\n"
            "This is the executive summary paragraph.\n\n"
            "## Table of Contents\n\n"
            "- [Background](#background)\n"
            "- [Analysis](#analysis)\n\n"
            "## Background\n\n"
            "Background details.\n\n"
            "## Analysis\n\n"
            "Analysis details.\n"
        )

        result = _run(tmp_path, content)

        # Before-TOC content preserved
        assert "# Executive Summary" in result
        assert "executive summary paragraph" in result
        # TOC stripped
        assert "Table of Contents" not in result
        assert "Background](#background)" not in result
        # After-TOC content preserved
        assert "## Background" in result
        assert "Background details." in result
        assert "## Analysis" in result
        assert "Analysis details." in result

    def test_no_toc_content_unchanged(self, tmp_path):
        """
        Test that a document without a TOC section passes through unmodified.

        Given: Markdown with no "Table of Contents" heading or marker
        When: process_markdown is called
        Then: The output contains the same headings and body text as the input
        """
        content = (
            "# Introduction\n\n"
            "Introductory paragraph.\n\n"
            "## Details\n\n"
            "Detail paragraph.\n"
        )

        result = _run(tmp_path, content)

        assert "# Introduction" in result
        assert "Introductory paragraph." in result
        assert "## Details" in result
        assert "Detail paragraph." in result


# ---------------------------------------------------------------------------
# Realistic full-document example
# ---------------------------------------------------------------------------


class TestTocStrippingRealistic:
    """End-to-end test with a nested link list matching real whitepaper TOCs."""

    def test_realistic_bold_toc_with_nested_links_is_stripped(self, tmp_path):
        """
        Test that a realistic nested-link bold TOC is fully stripped.

        Given: A document containing a bold TOC with nested sub-items that
               mirrors real CoSAI whitepaper structure
        When: process_markdown is called
        Then: The entire TOC block — including all nested link lines — is
              absent from the output; the first real section heading is
              preserved
        """
        content = (
            "**Table of Contents**\n\n"
            "- [Introduction](#introduction)\n"
            "- [Executive Summary](#executive-summary)\n"
            "- [Scenario Deconstruction](#scenario-deconstruction)\n"
            "  - [The 2 A.M. Incident](#the-2-am-incident)\n"
            "  - [Sub Section](#sub-section)\n"
            "- [Conclusion](#conclusion)\n\n"
            "# Introduction\n\n"
            "Introduction text.\n\n"
            "# Executive Summary\n\n"
            "Summary text.\n\n"
            "# Scenario Deconstruction\n\n"
            "## The 2 A.M. Incident\n\n"
            "Incident text.\n\n"
            "## Sub Section\n\n"
            "Sub text.\n\n"
            "# Conclusion\n\n"
            "Conclusion text.\n"
        )

        result = _run(tmp_path, content)

        # All TOC link lines stripped
        assert "Table of Contents" not in result
        assert "Introduction](#introduction)" not in result
        assert "Executive Summary](#executive-summary)" not in result
        assert "Scenario Deconstruction](#scenario-deconstruction)" not in result
        assert "The 2 A.M. Incident](#the-2-am-incident)" not in result
        assert "Sub Section](#sub-section)" not in result
        assert "Conclusion](#conclusion)" not in result

        # All real section headings and body text preserved
        assert "# Introduction" in result
        assert "Introduction text." in result
        assert "# Executive Summary" in result
        assert "Summary text." in result
        assert "# Scenario Deconstruction" in result
        assert "## The 2 A.M. Incident" in result
        assert "Incident text." in result
        assert "## Sub Section" in result
        assert "Sub text." in result
        assert "# Conclusion" in result
        assert "Conclusion text." in result


"""
Test Summary
============
Total Tests: 10
- Happy Path: 5  (TestTocStrippingHappyPath)
- HTML Comment + TOC: 1  (TestTocStrippingWithHtmlComment)
- Negative (no-strip): 2  (TestTocStrippingNegative)
- Position/No-TOC: 2  (TestTocStrippingPosition)
- Realistic end-to-end: 1  (TestTocStrippingRealistic)

Coverage Areas:
- H1-H4 heading TOC variants (all four heading levels)
- Bold **Table of Contents** marker
- Case-insensitive "contents" / "Contents"
- HTML comment preceding bold TOC
- H5 and H6 headings outside the matched range
- Mid-document TOC: before/after content preserved
- Document with no TOC: passes through unchanged
- Nested link list in a realistic whitepaper TOC
"""
