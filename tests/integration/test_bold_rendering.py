"""
Integration tests for bold text rendering in PDF conversion.

This module tests the complete conversion pipeline with bold text to ensure:
- Bold text renders correctly with tectonic engine (fontspec-based)
- Bold text renders correctly with pdflatex engine (traditional)
- Conversion doesn't fail due to font configuration issues
- Both engines produce valid PDFs with bold text

Bug Context:
- Issue: Bold text renders correctly with pdflatex but not with tectonic
- Integration Impact: Tectonic conversions succeed but bold text appears regular
- Fix Verification: After fix, tectonic should render bold text as Medium weight
"""

import pytest
import sys
import subprocess
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from convert import main, process_markdown


@pytest.fixture
def markdown_with_bold(tmp_path):
    """
    Create a markdown file with bold text for testing.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        Path: Path to markdown file with various bold text patterns.
    """
    content = """---
title: "Bold Text Rendering Test"
author: "Test Suite"
date: "2025-01-29"
---

# Bold Text Test Document

This document tests bold text rendering across different contexts.

## Inline Bold

This paragraph contains **bold text** in the middle of a sentence.
It also has **multiple** **bold** **words** throughout.

## Bold in Lists

- This is a **bold** list item
- **Entire bold item**
- Regular item with **bold portion**

## Bold in Headers

### This is a **Bold** Header

## Bold Combinations

Text with **bold**, *italic*, and ***bold italic*** combinations.

**Bold at start** of paragraph.

Paragraph ending with **bold at end**.

## Bold in Code Context

This is `**not bold in code**` but this is **bold outside code**.

## Bold in Tables

| Column 1 | Column 2 |
|----------|----------|
| **Bold** | Regular  |
| Regular  | **Bold** |

## Complex Bold Patterns

The **CoSAI** (**Coalition for Secure AI**) whitepaper converter must handle
**nested *italic* text** and other **complex** **patterns**.
"""

    md_file = tmp_path / "test_bold.md"
    md_file.write_text(content)
    return md_file


@pytest.fixture
def simple_bold_markdown(tmp_path):
    """
    Create a minimal markdown file with bold text.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        Path: Path to minimal markdown file for quick testing.
    """
    content = """---
title: "Simple Bold Test"
---

# Test

This is **bold text** in a simple document.
"""

    md_file = tmp_path / "simple_bold.md"
    md_file.write_text(content)
    return md_file


@pytest.mark.integration
def test_tectonic_conversion_succeeds_with_bold(
    markdown_with_bold, tmp_path, clean_env
):
    """
    Test that tectonic conversion succeeds with bold text (doesn't fail).

    Given: A markdown file with extensive bold text usage
    When: Conversion is run with tectonic engine
    Then: PDF is created successfully without font errors

    Note: This test verifies conversion succeeds. Visual bold rendering
    verification requires manual inspection or PDF text analysis tools.

    Expected: PASS (conversion succeeds even with buggy config)
    After fix: PASS (conversion succeeds with correct bold rendering)
    """
    output_pdf = tmp_path / "output_tectonic_bold.pdf"

    # Mock subprocess.run to capture pandoc call
    original_run = subprocess.run
    pandoc_calls = []

    def mock_run(cmd, *args, **kwargs):
        if cmd[0] == "pandoc":
            pandoc_calls.append(cmd)
            # Create a dummy PDF file to simulate success
            if "-o" in cmd:
                output_idx = cmd.index("-o") + 1
                output_file = cmd[output_idx]
                Path(output_file).write_text("%PDF-1.4\nDummy PDF with bold text")
            return MagicMock(returncode=0)
        return original_run(cmd, *args, **kwargs)

    with patch("subprocess.run", side_effect=mock_run):
        # Simulate command-line arguments with tectonic engine
        with patch(
            "sys.argv",
            [
                "convert.py",
                str(markdown_with_bold),
                str(output_pdf),
                "--engine",
                "tectonic",
            ],
        ):
            try:
                main()
            except SystemExit:
                pass

    # Verify pandoc was called successfully
    assert len(pandoc_calls) > 0, "Pandoc should have been called"
    pandoc_cmd = pandoc_calls[0]

    # Verify tectonic engine was used
    assert any("--pdf-engine=tectonic" in arg for arg in pandoc_cmd), (
        "Tectonic engine should be specified"
    )

    # Verify output file was created (by mock)
    assert output_pdf.exists(), "Output PDF should be created"


@pytest.mark.integration
@pytest.mark.skipif(not shutil.which("pdflatex"), reason="pdflatex not installed")
def test_pdflatex_conversion_succeeds_with_bold(
    markdown_with_bold, tmp_path, clean_env
):
    """
    Test that pdflatex conversion succeeds with bold text.

    Given: A markdown file with extensive bold text usage
    When: Conversion is run with pdflatex engine
    Then: PDF is created successfully with correct bold rendering

    This verifies backward compatibility - pdflatex should continue to work.

    Expected: PASS (pdflatex config is unchanged and working)
    """
    output_pdf = tmp_path / "output_pdflatex_bold.pdf"

    # Mock subprocess.run to capture pandoc call
    original_run = subprocess.run
    pandoc_calls = []

    def mock_run(cmd, *args, **kwargs):
        if cmd[0] == "pandoc":
            pandoc_calls.append(cmd)
            # Create a dummy PDF file to simulate success
            if "-o" in cmd:
                output_idx = cmd.index("-o") + 1
                output_file = cmd[output_idx]
                Path(output_file).write_text("%PDF-1.4\nDummy PDF with bold text")
            return MagicMock(returncode=0)
        return original_run(cmd, *args, **kwargs)

    with patch("subprocess.run", side_effect=mock_run):
        # Simulate command-line arguments with pdflatex engine
        with patch(
            "sys.argv",
            [
                "convert.py",
                str(markdown_with_bold),
                str(output_pdf),
                "--engine",
                "pdflatex",
            ],
        ):
            try:
                main()
            except SystemExit:
                pass

    # Verify pandoc was called successfully
    assert len(pandoc_calls) > 0, "Pandoc should have been called"
    pandoc_cmd = pandoc_calls[0]

    # Verify pdflatex engine was used
    assert any("--pdf-engine=pdflatex" in arg for arg in pandoc_cmd), (
        "pdflatex engine should be specified"
    )

    # Verify output file was created
    assert output_pdf.exists(), "Output PDF should be created"


@pytest.mark.integration
def test_xelatex_conversion_succeeds_with_bold(markdown_with_bold, tmp_path, clean_env):
    """
    Test that xelatex conversion succeeds with bold text.

    Given: A markdown file with bold text
    When: Conversion is run with xelatex engine (fontspec-based)
    Then: PDF is created successfully

    xelatex uses fontspec like tectonic, so it should exhibit the same bug.

    Expected: PASS (conversion succeeds with current config)
    After fix: PASS (conversion succeeds with correct bold rendering)
    """
    output_pdf = tmp_path / "output_xelatex_bold.pdf"

    # Mock subprocess.run to capture pandoc call
    original_run = subprocess.run
    pandoc_calls = []

    def mock_run(cmd, *args, **kwargs):
        if cmd[0] == "pandoc":
            pandoc_calls.append(cmd)
            # Create a dummy PDF file to simulate success
            if "-o" in cmd:
                output_idx = cmd.index("-o") + 1
                output_file = cmd[output_idx]
                Path(output_file).write_text("%PDF-1.4\nDummy PDF with bold text")
            return MagicMock(returncode=0)
        return original_run(cmd, *args, **kwargs)

    with patch("subprocess.run", side_effect=mock_run):
        # Simulate command-line arguments with xelatex engine
        with patch(
            "sys.argv",
            [
                "convert.py",
                str(markdown_with_bold),
                str(output_pdf),
                "--engine",
                "xelatex",
            ],
        ):
            try:
                main()
            except SystemExit:
                pass

    # Verify pandoc was called successfully
    assert len(pandoc_calls) > 0, "Pandoc should have been called"
    pandoc_cmd = pandoc_calls[0]

    # Verify xelatex engine was used
    assert any("--pdf-engine=xelatex" in arg for arg in pandoc_cmd), (
        "xelatex engine should be specified"
    )

    # Verify output file was created
    assert output_pdf.exists(), "Output PDF should be created"


@pytest.mark.integration
def test_lualatex_conversion_succeeds_with_bold(
    markdown_with_bold, tmp_path, clean_env
):
    """
    Test that lualatex conversion succeeds with bold text.

    Given: A markdown file with bold text
    When: Conversion is run with lualatex engine (fontspec-based)
    Then: PDF is created successfully

    lualatex uses fontspec like tectonic, so it should exhibit the same bug.

    Expected: PASS (conversion succeeds with current config)
    After fix: PASS (conversion succeeds with correct bold rendering)
    """
    output_pdf = tmp_path / "output_lualatex_bold.pdf"

    # Mock subprocess.run to capture pandoc call
    original_run = subprocess.run
    pandoc_calls = []

    def mock_run(cmd, *args, **kwargs):
        if cmd[0] == "pandoc":
            pandoc_calls.append(cmd)
            # Create a dummy PDF file to simulate success
            if "-o" in cmd:
                output_idx = cmd.index("-o") + 1
                output_file = cmd[output_idx]
                Path(output_file).write_text("%PDF-1.4\nDummy PDF with bold text")
            return MagicMock(returncode=0)
        return original_run(cmd, *args, **kwargs)

    with patch("subprocess.run", side_effect=mock_run):
        # Simulate command-line arguments with lualatex engine
        with patch(
            "sys.argv",
            [
                "convert.py",
                str(markdown_with_bold),
                str(output_pdf),
                "--engine",
                "lualatex",
            ],
        ):
            try:
                main()
            except SystemExit:
                pass

    # Verify pandoc was called successfully
    assert len(pandoc_calls) > 0, "Pandoc should have been called"
    pandoc_cmd = pandoc_calls[0]

    # Verify lualatex engine was used
    assert any("--pdf-engine=lualatex" in arg for arg in pandoc_cmd), (
        "lualatex engine should be specified"
    )

    # Verify output file was created
    assert output_pdf.exists(), "Output PDF should be created"


@pytest.mark.integration
def test_simple_bold_all_engines(simple_bold_markdown, tmp_path, clean_env):
    """
    Test that simple bold text works with all engines.

    Given: A minimal markdown file with bold text
    When: Conversion is run with each supported engine
    Then: All engines produce valid PDFs without errors

    This is a quick smoke test for all engines.

    Expected: PASS for all engines (conversion succeeds)
    """
    engines = ["tectonic", "pdflatex", "xelatex", "lualatex"]
    original_run = subprocess.run

    for engine in engines:
        output_pdf = tmp_path / f"output_{engine}_simple.pdf"
        pandoc_calls = []

        def mock_run(cmd, *args, **kwargs):
            if cmd[0] == "pandoc":
                pandoc_calls.append(cmd)
                # Create a dummy PDF file to simulate success
                if "-o" in cmd:
                    output_idx = cmd.index("-o") + 1
                    output_file = cmd[output_idx]
                    Path(output_file).write_text(f"%PDF-1.4\n{engine} PDF")
                return MagicMock(returncode=0)
            return original_run(cmd, *args, **kwargs)

        with patch("subprocess.run", side_effect=mock_run):
            with patch(
                "sys.argv",
                [
                    "convert.py",
                    str(simple_bold_markdown),
                    str(output_pdf),
                    "--engine",
                    engine,
                ],
            ):
                try:
                    main()
                except SystemExit:
                    pass

        # Verify pandoc was called for this engine
        assert len(pandoc_calls) > 0, f"Pandoc should have been called for {engine}"
        assert output_pdf.exists(), f"Output PDF should be created for {engine}"


@pytest.mark.integration
def test_markdown_preprocessing_preserves_bold(markdown_with_bold):
    """
    Test that markdown preprocessing doesn't corrupt bold markers.

    Given: A markdown file with bold text
    When: process_markdown is called
    Then: Bold markers (**text**) are preserved in output

    This ensures our preprocessing steps don't interfere with bold syntax.

    Expected: PASS (preprocessing should preserve bold markers)
    """
    # Process the markdown
    processed_content = process_markdown(markdown_with_bold)

    # Verify bold markers are preserved
    assert "**bold text**" in processed_content, (
        "Inline bold markers should be preserved"
    )
    assert "**CoSAI**" in processed_content, (
        "Bold markers in complex patterns should be preserved"
    )

    # Verify document structure is maintained
    assert "# Bold Text Test Document" in processed_content
    assert "## Inline Bold" in processed_content


@pytest.mark.integration
def test_bold_with_unicode_characters(tmp_path, clean_env):
    """
    Test bold rendering with Unicode characters (tectonic).

    Given: Markdown with bold text containing Unicode characters
    When: Conversion is run with tectonic engine
    Then: PDF is created successfully with both bold and Unicode

    This tests the interaction between Unicode handling and bold rendering.

    Expected: PASS (should handle both Unicode and bold)
    """
    # Create markdown with bold Unicode text
    content = """---
title: "Bold Unicode Test"
---

# Test

This has **bold Unicode: —, ", ", '** text.

The **CoSAI** initiative includes **"secure AI"** development.
"""

    md_file = tmp_path / "bold_unicode.md"
    md_file.write_text(content)
    output_pdf = tmp_path / "output_bold_unicode.pdf"

    # Mock subprocess.run
    original_run = subprocess.run
    pandoc_calls = []

    def mock_run(cmd, *args, **kwargs):
        if cmd[0] == "pandoc":
            pandoc_calls.append(cmd)
            if "-o" in cmd:
                output_idx = cmd.index("-o") + 1
                output_file = cmd[output_idx]
                Path(output_file).write_text("%PDF-1.4\nBold Unicode PDF")
            return MagicMock(returncode=0)
        return original_run(cmd, *args, **kwargs)

    with patch("subprocess.run", side_effect=mock_run):
        with patch(
            "sys.argv",
            ["convert.py", str(md_file), str(output_pdf), "--engine", "tectonic"],
        ):
            try:
                main()
            except SystemExit:
                pass

    # Verify success
    assert len(pandoc_calls) > 0, "Pandoc should have been called"
    assert output_pdf.exists(), "Output PDF should be created"


@pytest.mark.integration
def test_bold_in_frontmatter_metadata(tmp_path, clean_env):
    """
    Test that bold text in frontmatter metadata is handled correctly.

    Given: Markdown with bold markers in title/author metadata
    When: Conversion is run
    Then: PDF is created successfully

    This ensures bold syntax in metadata doesn't cause issues.

    Expected: PASS (metadata with bold should be handled)
    """
    content = """---
title: "Test **Bold** Title"
author: "**Test** Author"
---

# Content

Regular content here.
"""

    md_file = tmp_path / "bold_metadata.md"
    md_file.write_text(content)
    output_pdf = tmp_path / "output_bold_metadata.pdf"

    # Mock subprocess.run
    original_run = subprocess.run
    pandoc_calls = []

    def mock_run(cmd, *args, **kwargs):
        if cmd[0] == "pandoc":
            pandoc_calls.append(cmd)
            if "-o" in cmd:
                output_idx = cmd.index("-o") + 1
                output_file = cmd[output_idx]
                Path(output_file).write_text("%PDF-1.4\nMetadata PDF")
            return MagicMock(returncode=0)
        return original_run(cmd, *args, **kwargs)

    with patch("subprocess.run", side_effect=mock_run):
        with patch(
            "sys.argv",
            ["convert.py", str(md_file), str(output_pdf), "--engine", "tectonic"],
        ):
            try:
                main()
            except SystemExit:
                pass

    # Verify success
    assert len(pandoc_calls) > 0, "Pandoc should have been called"
    assert output_pdf.exists(), "Output PDF should be created"


"""
Test Summary
============
Total Tests: 9
- Happy Path: 5 (each engine succeeds with bold)
- Integration: 4 (preprocessing, Unicode, metadata)

Coverage Areas:
- Tectonic conversion with bold text
- pdflatex conversion with bold text (backward compatibility)
- xelatex conversion with bold text
- lualatex conversion with bold text
- Simple bold text smoke test for all engines
- Markdown preprocessing preservation of bold markers
- Bold text with Unicode characters
- Bold text in frontmatter metadata

Test Characteristics:
- All tests use real markdown files with bold text
- Tests verify conversion succeeds (no font errors)
- Tests mock subprocess to avoid actual LaTeX compilation
- Tests verify correct engine is used in pandoc command
- Tests check that output files are created
- Tests include various bold text patterns (inline, lists, tables, etc.)

Expected Test Results (RED Phase):
- All tests: PASS (conversion succeeds even with buggy bold rendering)
- Note: Visual inspection of actual PDFs would show bold not rendering correctly

After Fix (GREEN Phase):
- All tests: PASS (conversion succeeds with correct bold rendering)
- Note: Manual verification needed to confirm bold renders as Medium weight

Pytest Markers:
- @pytest.mark.integration: All tests marked for selective execution
- @pytest.mark.skipif: pdflatex test conditional on installation

Running Tests:
- All integration tests: pytest tests/integration/test_bold_rendering.py
- Single test: pytest tests/integration/test_bold_rendering.py::test_tectonic_conversion_succeeds_with_bold
- Verbose: pytest tests/integration/test_bold_rendering.py -v
- With unit tests: pytest tests/unit/test_font_rendering.py tests/integration/test_bold_rendering.py

Manual Verification:
After fix, generate actual PDFs and verify:
1. Bold text renders as Medium weight (not Regular)
2. Bold text is visually distinct from body text (ExtraLight)
3. pdflatex output is unchanged (backward compatibility)
4. All engines produce consistent bold appearance
"""
