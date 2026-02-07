"""Integration tests for Unicode character rendering."""

import subprocess
import pytest


class TestUnicodeRendering:
    """Test suite for Unicode character rendering in PDF output."""

    @pytest.fixture
    def markdown_with_unicode(self, tmp_path):
        """Create markdown file containing various Unicode characters."""
        content = """---
title: "Unicode Test"
author: "Test Author"
date: "2025-01-01"
---

# Unicode Character Test

This document tests Unicode characters that caused warnings…

## Punctuation Tests

- Ellipsis: Wait… what happened?
- Right single quote: It's working now
- Left/right double quotes: "Hello," she said.
- Em dash: word—another word
- En dash: pages 1–10

## Expected Behavior

All characters above should render without "Missing character" warnings.
"""
        md_file = tmp_path / "unicode_test.md"
        md_file.write_text(content, encoding="utf-8")
        return md_file

    def test_tectonic_renders_unicode_without_warnings(
        self, markdown_with_unicode, tmp_path
    ):
        """
        Test that Tectonic renders Unicode characters without 'Missing character' warnings.

        Given: Markdown file containing Unicode punctuation (…, ', ", —, –)
        When: Converted to PDF using Tectonic engine
        Then: No 'Missing character' warnings in stderr output
        """
        output_pdf = tmp_path / "output.pdf"

        result = subprocess.run(
            [
                "python",
                "convert.py",
                str(markdown_with_unicode),
                str(output_pdf),
                "--engine",
                "tectonic",
            ],
            capture_output=True,
            text=True,
            cwd="/workspaces/cosai-whitepaper-converter",
        )

        # This assertion will FAIL with current code (T1 encoding)
        combined_output = result.stdout + result.stderr
        assert "Missing character" not in combined_output, (
            f"Unicode characters not rendered properly. Warnings found:\n{combined_output}"
        )
        assert output_pdf.exists(), "PDF was not created"
        assert output_pdf.stat().st_size > 0, "PDF file is empty"
        assert result.returncode == 0, (
            f"Conversion failed with code {result.returncode}"
        )
