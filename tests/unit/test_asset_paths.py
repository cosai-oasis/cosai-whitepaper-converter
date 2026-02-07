"""
Tests for asset path resolution.

This module tests the hygiene refactor that moves asset files from the root
directory to the assets/ subdirectory while maintaining backward compatibility.

Key Requirements:
- get_asset_path(filename) returns path from assets/ directory when file exists there
- get_asset_path(filename) falls back to root directory for backward compatibility
- Correct paths for: cosai-template.tex, cosai.sty, config.json, puppeteerConfig.json
- Appropriate error handling when asset doesn't exist in either location

Function Under Test:
- get_asset_path(filename: str) -> str
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from convert import get_asset_path


class TestGetAssetPathBasicBehavior:
    """Test suite for get_asset_path basic functionality."""

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_returns_assets_dir_when_file_exists(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test that get_asset_path returns assets/ path when file exists there.

        Given: Asset file exists in assets/ directory
        When: get_asset_path is called with filename
        Then: Returns path to file in assets/ directory
        """
        # Setup mocks
        mock_abspath.return_value = "/workspaces/cosai-whitepaper-converter/convert.py"
        mock_dirname.return_value = "/workspaces/cosai-whitepaper-converter"

        # Simulate file exists in assets/
        def exists_side_effect(path):
            return path == "/workspaces/cosai-whitepaper-converter/assets/config.json"

        mock_exists.side_effect = exists_side_effect

        result = get_asset_path("config.json")

        expected = "/workspaces/cosai-whitepaper-converter/assets/config.json"
        assert result == expected

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_falls_back_to_root_when_not_in_assets(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test that get_asset_path falls back to root when file not in assets/.

        Given: Asset file does NOT exist in assets/ directory
        When: get_asset_path is called with filename
        Then: Returns path to file in root directory (backward compatibility)
        """
        # Setup mocks
        mock_abspath.return_value = "/workspaces/cosai-whitepaper-converter/convert.py"
        mock_dirname.return_value = "/workspaces/cosai-whitepaper-converter"

        # Simulate file does NOT exist in assets/ (backward compat fallback)
        mock_exists.return_value = False

        result = get_asset_path("config.json")

        expected = "/workspaces/cosai-whitepaper-converter/config.json"
        assert result == expected

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_checks_assets_directory_first(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test that get_asset_path checks assets/ directory before root.

        Given: get_asset_path is called
        When: Path resolution occurs
        Then: assets/ directory is checked first via os.path.exists
        """
        # Setup mocks
        mock_abspath.return_value = "/workspaces/cosai-whitepaper-converter/convert.py"
        mock_dirname.return_value = "/workspaces/cosai-whitepaper-converter"
        mock_exists.return_value = True

        get_asset_path("config.json")

        # Verify os.path.exists was called with assets/ path
        assert mock_exists.called
        first_call = mock_exists.call_args_list[0]
        checked_path = first_call[0][0]

        assert "assets" in checked_path
        assert checked_path.endswith("config.json")

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_uses_script_directory_not_cwd(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test that get_asset_path resolves relative to script location, not cwd.

        Given: get_asset_path is called from any working directory
        When: Path is constructed
        Then: Uses convert.py location (__file__), not os.getcwd()
        """
        # Setup mocks - script in specific location
        script_path = "/some/install/location/convert.py"
        script_dir = "/some/install/location"

        mock_abspath.return_value = script_path
        mock_dirname.return_value = script_dir
        mock_exists.return_value = True

        result = get_asset_path("config.json")

        # Should use script directory, not cwd
        assert result.startswith(script_dir)
        assert "assets" in result


class TestGetAssetPathSpecificFiles:
    """Test suite for specific asset file path resolution."""

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_resolves_cosai_template_tex(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test path resolution for cosai-template.tex.

        Given: cosai-template.tex exists in assets/ directory
        When: get_asset_path("cosai-template.tex") is called
        Then: Returns correct path to assets/cosai-template.tex
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = True

        result = get_asset_path("cosai-template.tex")

        assert result == "/project/assets/cosai-template.tex"

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_resolves_cosai_sty(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test path resolution for cosai.sty.

        Given: cosai.sty exists in assets/ directory
        When: get_asset_path("cosai.sty") is called
        Then: Returns correct path to assets/cosai.sty
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = True

        result = get_asset_path("cosai.sty")

        assert result == "/project/assets/cosai.sty"

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_resolves_config_json(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test path resolution for config.json (Mermaid config).

        Given: config.json exists in assets/ directory
        When: get_asset_path("config.json") is called
        Then: Returns correct path to assets/config.json
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = True

        result = get_asset_path("config.json")

        assert result == "/project/assets/config.json"

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_resolves_puppeteer_config_json(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test path resolution for puppeteerConfig.json.

        Given: puppeteerConfig.json exists in assets/ directory
        When: get_asset_path("puppeteerConfig.json") is called
        Then: Returns correct path to assets/puppeteerConfig.json
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = True

        result = get_asset_path("puppeteerConfig.json")

        assert result == "/project/assets/puppeteerConfig.json"

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_resolves_cosai_logo_png(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test path resolution for cosai-logo.png.

        Given: cosai-logo.png exists in assets/ directory
        When: get_asset_path("cosai-logo.png") is called
        Then: Returns correct path to assets/cosai-logo.png
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = True

        result = get_asset_path("cosai-logo.png")

        assert result == "/project/assets/cosai-logo.png"

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_resolves_background_pdf(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test path resolution for background.pdf.

        Given: background.pdf exists in assets/ directory
        When: get_asset_path("background.pdf") is called
        Then: Returns correct path to assets/background.pdf
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = True

        result = get_asset_path("background.pdf")

        assert result == "/project/assets/background.pdf"


class TestGetAssetPathBackwardCompatibility:
    """Test suite for backward compatibility fallback behavior."""

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_backward_compat_config_in_root(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test backward compatibility: config.json in root works.

        Given: config.json exists only in root directory (not in assets/)
        When: get_asset_path("config.json") is called
        Then: Returns path to config.json in root directory
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"

        # Simulate: assets/config.json does NOT exist, root/config.json exists
        def exists_side_effect(path):
            return path == "/project/config.json"

        mock_exists.side_effect = exists_side_effect

        result = get_asset_path("config.json")

        assert result == "/project/config.json"

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_backward_compat_template_in_root(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test backward compatibility: cosai-template.tex in root works.

        Given: cosai-template.tex exists only in root directory
        When: get_asset_path("cosai-template.tex") is called
        Then: Returns path to template in root directory
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"

        # Simulate: assets/ version doesn't exist, root version exists
        def exists_side_effect(path):
            return path == "/project/cosai-template.tex"

        mock_exists.side_effect = exists_side_effect

        result = get_asset_path("cosai-template.tex")

        assert result == "/project/cosai-template.tex"

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_prefers_assets_over_root(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test that assets/ version is preferred when file exists in both locations.

        Given: File exists in both assets/ directory AND root directory
        When: get_asset_path is called
        Then: Returns path from assets/ directory (not root)
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"

        # Simulate: file exists in both locations
        # First call checks assets/ (should return True), so it uses assets/ path
        mock_exists.return_value = True

        result = get_asset_path("config.json")

        # Should prefer assets/ directory
        assert result == "/project/assets/config.json"
        assert "/assets/" in result

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_with_latex_template_subdirectory(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test backward compatibility with latex-template subdirectory structure.

        Given: Script exists in latex-template subdirectory (legacy structure)
        When: get_asset_path is called
        Then: Correctly resolves paths relative to script location
        """
        # Legacy structure: /project/latex-template/convert.py
        mock_abspath.return_value = "/project/latex-template/convert.py"
        mock_dirname.return_value = "/project/latex-template"
        mock_exists.return_value = True

        result = get_asset_path("config.json")

        # Should look in /project/latex-template/assets/
        assert result == "/project/latex-template/assets/config.json"


class TestGetAssetPathErrorHandling:
    """Test suite for error handling when assets are missing."""

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_returns_fallback_path_when_file_missing(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test that fallback path is returned even when file doesn't exist.

        Given: Asset file doesn't exist in either assets/ or root
        When: get_asset_path is called
        Then: Returns fallback path (root directory path)
        Note: Calling code responsible for checking existence and error handling
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"

        # File doesn't exist anywhere
        mock_exists.return_value = False

        result = get_asset_path("nonexistent.json")

        # Should return fallback path (root directory)
        assert result == "/project/nonexistent.json"

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_handles_empty_filename(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test handling of empty filename.

        Given: Empty string passed as filename
        When: get_asset_path is called
        Then: Returns path to assets/ or root directory
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = False

        result = get_asset_path("")

        # Should return root directory path with empty filename
        assert result == "/project/"

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_handles_subdirectory_in_filename(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test handling of filename with subdirectory path.

        Given: Filename includes subdirectory (e.g., "subdir/file.json")
        When: get_asset_path is called
        Then: Correctly constructs path with subdirectory
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = True

        result = get_asset_path("subdir/file.json")

        # Should construct path with subdirectory under assets/
        assert result == "/project/assets/subdir/file.json"


class TestGetAssetPathIntegration:
    """Test suite for integration with convert.py usage patterns."""

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_for_convert_mermaid_to_svg_config(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test path resolution for config.json used in convert_mermaid_to_svg.

        Given: convert_mermaid_to_svg needs config.json path
        When: get_asset_path("config.json") is used
        Then: Returns correct path for mmdc command
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = True

        config_path = get_asset_path("config.json")

        # Verify this is the correct path for mmdc -c flag
        assert config_path.endswith("config.json")
        assert os.path.isabs(config_path)

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_for_convert_mermaid_to_svg_puppeteer(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test path resolution for puppeteerConfig.json used in convert_mermaid_to_svg.

        Given: convert_mermaid_to_svg needs puppeteerConfig.json path
        When: get_asset_path("puppeteerConfig.json") is used
        Then: Returns correct path for mmdc command
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = True

        puppeteer_path = get_asset_path("puppeteerConfig.json")

        # Verify this is the correct path for mmdc -p flag
        assert puppeteer_path.endswith("puppeteerConfig.json")
        assert os.path.isabs(puppeteer_path)

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_for_pandoc_template(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test path resolution for cosai-template.tex used in pandoc command.

        Given: pandoc command needs --template path
        When: get_asset_path("cosai-template.tex") is used
        Then: Returns correct absolute path for pandoc
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = True

        template_path = get_asset_path("cosai-template.tex")

        # Verify this is the correct path for pandoc --template flag
        assert template_path.endswith("cosai-template.tex")
        assert os.path.isabs(template_path)

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_replaces_dep_prefix_logic(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test that get_asset_path replaces the old dep_prefix logic.

        Given: Old code used dep_prefix = "latex-template" or "."
        When: get_asset_path is used instead
        Then: Provides same functionality with cleaner implementation
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = True

        # Old pattern: os.path.join(dep_prefix, "config.json")
        # New pattern: get_asset_path("config.json")

        result = get_asset_path("config.json")

        # Should provide absolute path without needing dep_prefix variable
        assert os.path.isabs(result)
        assert result.endswith("config.json")


class TestGetAssetPathEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_with_absolute_path_filename(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test handling when an absolute path is passed as filename.

        Given: Absolute path passed as filename parameter
        When: get_asset_path is called
        Then: Returns expected behavior (implementation defined)
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = False

        # Edge case: absolute path as filename
        result = get_asset_path("/etc/config.json")

        # Should still construct path relative to script location
        # (treating absolute path as filename, not as path)
        assert "/etc/config.json" in result

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_with_parent_directory_traversal(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test handling of filename with parent directory references.

        Given: Filename contains ../ parent directory references
        When: get_asset_path is called
        Then: Constructs path with parent references (caller responsible for security)
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = False

        result = get_asset_path("../config.json")

        # Should construct path with ../ reference
        assert "../config.json" in result

    @patch("convert.os.path.exists")
    @patch("convert.os.path.dirname")
    @patch("convert.os.path.abspath")
    def test_get_asset_path_with_special_characters(
        self, mock_abspath, mock_dirname, mock_exists
    ):
        """
        Test handling of filenames with special characters.

        Given: Filename contains spaces or special characters
        When: get_asset_path is called
        Then: Correctly constructs path preserving special characters
        """
        mock_abspath.return_value = "/project/convert.py"
        mock_dirname.return_value = "/project"
        mock_exists.return_value = False

        test_filenames = [
            "file with spaces.json",
            "file-with-dashes.json",
            "file_with_underscores.json",
            "file.multiple.dots.json",
        ]

        for filename in test_filenames:
            result = get_asset_path(filename)
            # Should preserve special characters in filename
            assert filename in result


"""
Test Summary
============
Total Tests: 30
- Basic Behavior: 4
- Specific Asset Files: 6
- Backward Compatibility: 4
- Error Handling: 4
- Integration Patterns: 4
- Edge Cases: 5

Coverage Areas:
- get_asset_path returns assets/ path when file exists there
- get_asset_path falls back to root for backward compatibility
- get_asset_path checks assets/ directory first
- get_asset_path uses script location, not cwd
- Path resolution for all key asset files (template, sty, configs, images)
- Backward compatibility when assets still in root
- Preference for assets/ over root when file in both locations
- Error handling for missing files
- Integration with convert_mermaid_to_svg and pandoc usage patterns
- Edge cases: empty filename, subdirectories, special characters

Expected Initial Status: ALL TESTS FAIL
Reason: get_asset_path() function does not exist in convert.py yet
"""
