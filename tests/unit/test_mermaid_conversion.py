"""
Tests for Mermaid diagram SVG conversion functionality.

This module tests the SVG-based Mermaid conversion pipeline:
- Mermaid code is converted to SVG using mermaid-cli
- SVG output provides better accessibility (selectable/searchable text)
- Pandoc handles SVG→PDF conversion automatically via rsvg-convert

Implementation Requirements:
- convert.py provides convert_mermaid_to_svg() function
- Function returns (svg_filename, title) tuple
- SVG files are named diagram_X.svg where X is the index
- Title is extracted from YAML frontmatter if present
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from convert import convert_mermaid_to_svg


class TestConvertMermaidToSvg:
    """Test suite for Mermaid to SVG conversion."""

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_produces_svg_output(
        self, mock_subprocess, mock_open, mock_remove, mock_exists
    ):
        """
        Test that convert_mermaid_to_svg produces SVG file.

        Given: Valid mermaid code
        When: convert_mermaid_to_svg is called
        Then: Returns SVG filename with .svg extension
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""

        svg_file, title = convert_mermaid_to_svg(mermaid_code, 0)

        assert svg_file == "diagram_0.svg"
        assert svg_file.endswith(".svg")

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_calls_mmdc_with_svg_output(
        self, mock_subprocess, mock_open, mock_remove, mock_exists
    ):
        """
        Test that mmdc is called with SVG output file.

        Given: Valid mermaid code
        When: convert_mermaid_to_svg is called
        Then: mmdc command specifies .svg output file
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""

        convert_mermaid_to_svg(mermaid_code, 0)

        # Verify mmdc was called with SVG output
        mmdc_call = mock_subprocess.call_args_list[0]
        cmd = mmdc_call[0][0]

        assert "-o" in cmd
        output_idx = cmd.index("-o")
        assert cmd[output_idx + 1] == "diagram_0.svg"

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_extracts_title_from_frontmatter(
        self, mock_subprocess, mock_open, mock_remove, mock_exists
    ):
        """
        Test that title is extracted from YAML frontmatter.

        Given: Mermaid code with YAML frontmatter containing title
        When: convert_mermaid_to_svg is called
        Then: Returns the title from frontmatter
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """---
title: "Architecture Diagram"
---
graph TD
    A[Start] --> B[End]
"""

        svg_file, title = convert_mermaid_to_svg(mermaid_code, 0)

        assert svg_file == "diagram_0.svg"
        assert title == "Architecture Diagram"

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_returns_none_title_when_missing(
        self, mock_subprocess, mock_open, mock_remove, mock_exists
    ):
        """
        Test that None is returned for title when not in frontmatter.

        Given: Mermaid code without title in frontmatter
        When: convert_mermaid_to_svg is called
        Then: Returns None for title
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""

        svg_file, title = convert_mermaid_to_svg(mermaid_code, 0)

        assert svg_file == "diagram_0.svg"
        assert title is None

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_uses_correct_index_in_filename(
        self, mock_subprocess, mock_open, mock_remove, mock_exists
    ):
        """
        Test that diagram index is used in SVG filename.

        Given: Different index values
        When: convert_mermaid_to_svg is called with various indices
        Then: SVG filename includes the correct index
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""

        for index in [0, 1, 5, 42]:
            svg_file, _ = convert_mermaid_to_svg(mermaid_code, index)
            assert svg_file == f"diagram_{index}.svg"

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_only_calls_mmdc_once(
        self, mock_subprocess, mock_open, mock_remove, mock_exists
    ):
        """
        Test that only mmdc is called (no pdfcrop for SVG).

        Given: Valid mermaid code
        When: convert_mermaid_to_svg is called
        Then: Only one subprocess call is made (mmdc)
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""

        convert_mermaid_to_svg(mermaid_code, 0)

        # Only mmdc should be called, no pdfcrop
        assert mock_subprocess.call_count == 1

        mmdc_call = mock_subprocess.call_args_list[0]
        cmd = mmdc_call[0][0]
        assert "npx" in cmd
        assert "@mermaid-js/mermaid-cli" in cmd


class TestConvertMermaidToSvgErrors:
    """Test error handling for Mermaid to SVG conversion."""

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_handles_mmdc_failure(
        self, mock_subprocess, mock_open, mock_remove, mock_exists
    ):
        """
        Test error handling when mmdc command fails.

        Given: mmdc command fails with error
        When: convert_mermaid_to_svg is called
        Then: Returns (None, None)
        """
        mock_exists.return_value = True

        error = subprocess.CalledProcessError(1, "mmdc")
        error.stderr = b"Mermaid syntax error"
        mock_subprocess.side_effect = error

        mermaid_code = """graph TD
    INVALID SYNTAX
"""

        svg_file, title = convert_mermaid_to_svg(mermaid_code, 0)

        assert svg_file is None
        assert title is None

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_cleans_up_mmd_file_on_error(
        self, mock_subprocess, mock_open, mock_remove, mock_exists
    ):
        """
        Test that temporary .mmd file is cleaned up even on error.

        Given: mmdc command fails
        When: convert_mermaid_to_svg is called
        Then: Temporary .mmd file is removed
        """
        mock_exists.return_value = True

        error = subprocess.CalledProcessError(1, "mmdc")
        error.stderr = b"Error"
        mock_subprocess.side_effect = error

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""

        convert_mermaid_to_svg(mermaid_code, 0)

        # Verify os.remove was called for cleanup
        mock_remove.assert_called()


class TestConvertMermaidToSvgCommand:
    """Test mmdc command construction for SVG output."""

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_includes_config_file(
        self, mock_subprocess, mock_open, mock_remove, mock_exists
    ):
        """
        Test that mmdc command includes config file.

        Given: Valid mermaid code
        When: convert_mermaid_to_svg is called
        Then: mmdc command includes -c flag with config.json
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""

        convert_mermaid_to_svg(mermaid_code, 0)

        mmdc_call = mock_subprocess.call_args_list[0]
        cmd = mmdc_call[0][0]

        assert "-c" in cmd
        config_idx = cmd.index("-c")
        assert "config.json" in cmd[config_idx + 1]

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_includes_puppeteer_config(
        self, mock_subprocess, mock_open, mock_remove, mock_exists
    ):
        """
        Test that mmdc command includes puppeteer config.

        Given: Valid mermaid code
        When: convert_mermaid_to_svg is called
        Then: mmdc command includes -p flag with puppeteerConfig.json
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""

        convert_mermaid_to_svg(mermaid_code, 0)

        mmdc_call = mock_subprocess.call_args_list[0]
        cmd = mmdc_call[0][0]

        assert "-p" in cmd
        puppeteer_idx = cmd.index("-p")
        assert "puppeteerConfig.json" in cmd[puppeteer_idx + 1]

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_no_pdffit_flag_for_svg(
        self, mock_subprocess, mock_open, mock_remove, mock_exists
    ):
        """
        Test that SVG output does not use -f (pdfFit) flag.

        Given: Valid mermaid code
        When: convert_mermaid_to_svg is called
        Then: mmdc command does NOT include -f flag (not applicable for SVG)
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""

        convert_mermaid_to_svg(mermaid_code, 0)

        mmdc_call = mock_subprocess.call_args_list[0]
        cmd = mmdc_call[0][0]

        # -f flag is only for PDF output, should not be present for SVG
        assert "-f" not in cmd


"""
Test Summary
============
Total Tests: 12

Coverage Areas:
- SVG file output format and naming
- Title extraction from YAML frontmatter
- mmdc command construction
- Error handling (mmdc failure)
- Cleanup of temporary files
- No pdfcrop dependency (single subprocess call)
- No -f flag for SVG output

Test Categories:
1. TestConvertMermaidToSvg (6 tests)
   - Basic SVG conversion behavior
   - Return values (svg_filename, title)
   - Index handling in filenames

2. TestConvertMermaidToSvgErrors (2 tests)
   - mmdc failure handling
   - Cleanup on error

3. TestConvertMermaidToSvgCommand (4 tests)
   - mmdc command structure
   - Config file inclusion
   - No PDF-specific flags
"""
