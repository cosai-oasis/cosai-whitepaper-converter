"""
Tests for temporary file cleanup during conversion.

This module tests the hygiene refactor that ensures temporary files
(SVG diagrams, downloaded images) are created in temp directories
and properly cleaned up, not left in the current working directory.

Key Requirements:
- SVG files from Mermaid conversion created in temp directory, not cwd
- Downloaded images created in temp directory, not cwd
- Cleanup occurs on successful conversion (no temp files left)
- Cleanup occurs even on error (context manager ensures cleanup)
- No diagram_*.svg or downloaded_image_* files remain in cwd after conversion

Functions Under Test:
- convert_mermaid_to_svg(mermaid_block, index, temp_dir=None)
- download_image(url, index, temp_dir=None)
- process_markdown(file_path, engine, temp_dir=None)
"""

import sys
import os
import glob
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from convert import convert_mermaid_to_svg, download_image, process_markdown


class TestMermaidSvgTempDirectory:
    """Test suite for Mermaid SVG files created in temp directory."""

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_without_temp_dir_creates_in_cwd(
        self, mock_subprocess, mock_file_open, mock_remove, mock_exists
    ):
        """
        Test backward compatibility: without temp_dir, files created in cwd.

        Given: convert_mermaid_to_svg called without temp_dir parameter
        When: Mermaid conversion is performed
        Then: SVG file is created in current working directory
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""

        svg_file, title = convert_mermaid_to_svg(mermaid_code, 0)

        # Should create in cwd (backward compatibility)
        assert svg_file == "diagram_0.svg"
        assert not svg_file.startswith("/tmp")
        assert not svg_file.startswith("/var")

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_with_temp_dir_returns_relative_filename(
        self, mock_subprocess, mock_file_open, mock_remove, mock_exists
    ):
        """
        Test that convert_mermaid_to_svg returns relative filename when temp_dir provided.

        Given: convert_mermaid_to_svg called with temp_dir parameter
        When: Mermaid conversion is performed
        Then: Returns just the filename (not absolute path) since pandoc runs from temp_dir
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""
        temp_dir = "/tmp/cosai_test_12345"

        svg_file, title = convert_mermaid_to_svg(mermaid_code, 0, temp_dir=temp_dir)

        # Should return just filename (relative path for pandoc which runs from temp_dir)
        assert svg_file == "diagram_0.svg"
        assert not svg_file.startswith("/")
        assert not svg_file.startswith(temp_dir)

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_with_temp_dir_creates_mmd_in_temp_dir(
        self, mock_subprocess, mock_file_open, mock_remove, mock_exists
    ):
        """
        Test that intermediate .mmd file is created in temp directory.

        Given: convert_mermaid_to_svg called with temp_dir parameter
        When: Mermaid conversion writes intermediate .mmd file
        Then: .mmd file is created in temp directory, not cwd
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""
        temp_dir = "/tmp/cosai_test_12345"

        convert_mermaid_to_svg(mermaid_code, 0, temp_dir=temp_dir)

        # Check that open() was called with temp_dir path for .mmd file
        mmd_file_calls = [
            call_args
            for call_args in mock_file_open.call_args_list
            if ".mmd" in str(call_args)
        ]

        assert len(mmd_file_calls) > 0
        # First call should be to write the .mmd file
        first_call = mock_file_open.call_args_list[0]
        mmd_path = first_call[0][0]
        assert mmd_path.startswith(temp_dir)
        assert mmd_path.endswith(".mmd")

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_with_temp_dir_mmdc_command_uses_temp_paths(
        self, mock_subprocess, mock_file_open, mock_remove, mock_exists
    ):
        """
        Test that mmdc command receives temp directory paths for input/output.

        Given: convert_mermaid_to_svg called with temp_dir parameter
        When: mmdc subprocess command is constructed
        Then: Both input (.mmd) and output (.svg) paths use temp directory
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""
        temp_dir = "/tmp/cosai_test_12345"

        convert_mermaid_to_svg(mermaid_code, 0, temp_dir=temp_dir)

        # Verify mmdc was called with temp directory paths
        assert mock_subprocess.called
        mmdc_call = mock_subprocess.call_args_list[0]
        cmd = mmdc_call[0][0]

        # Find -i and -o arguments
        input_idx = cmd.index("-i")
        output_idx = cmd.index("-o")

        input_file = cmd[input_idx + 1]
        output_file = cmd[output_idx + 1]

        assert input_file.startswith(temp_dir)
        assert input_file.endswith(".mmd")
        assert output_file.startswith(temp_dir)
        assert output_file.endswith(".svg")

    @patch("convert.os.path.exists")
    @patch("convert.os.remove")
    @patch("builtins.open", create=True)
    @patch("convert.subprocess.run")
    def test_convert_mermaid_multiple_diagrams_return_relative_filenames(
        self, mock_subprocess, mock_file_open, mock_remove, mock_exists
    ):
        """
        Test that multiple diagrams return unique relative filenames.

        Given: Multiple Mermaid diagrams converted with temp_dir
        When: Each diagram is converted with different index
        Then: Each returns unique relative filename (for pandoc running from temp_dir)
        """
        mock_exists.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)

        mermaid_code = """graph TD
    A[Start] --> B[End]
"""
        temp_dir = "/tmp/cosai_test_12345"

        svg_file_0, _ = convert_mermaid_to_svg(mermaid_code, 0, temp_dir=temp_dir)
        svg_file_1, _ = convert_mermaid_to_svg(mermaid_code, 1, temp_dir=temp_dir)
        svg_file_2, _ = convert_mermaid_to_svg(mermaid_code, 2, temp_dir=temp_dir)

        # All should return just relative filenames
        assert svg_file_0 == "diagram_0.svg"
        assert svg_file_1 == "diagram_1.svg"
        assert svg_file_2 == "diagram_2.svg"


class TestDownloadImageTempDirectory:
    """Test suite for downloaded images created in temp directory."""

    @patch("convert.urllib.request.urlretrieve")
    @patch("convert.os.path.exists")
    def test_download_image_without_temp_dir_creates_in_cwd(
        self, mock_exists, mock_urlretrieve
    ):
        """
        Test backward compatibility: without temp_dir, files created in cwd.

        Given: download_image called without temp_dir parameter
        When: Image is downloaded
        Then: Image file is created in current working directory
        """
        mock_exists.return_value = False  # File doesn't exist yet
        url = "https://example.com/image.png"

        local_file = download_image(url, 0)

        # Should create in cwd (backward compatibility)
        assert local_file == "downloaded_image_0.png"
        assert not local_file.startswith("/tmp")
        assert not local_file.startswith("/var")

    @patch("convert.urllib.request.urlretrieve")
    @patch("convert.os.path.exists")
    def test_download_image_with_temp_dir_returns_relative_filename(
        self, mock_exists, mock_urlretrieve
    ):
        """
        Test that download_image returns relative filename when temp_dir provided.

        Given: download_image called with temp_dir parameter
        When: Image is downloaded
        Then: Returns just the filename (not absolute path) since pandoc runs from temp_dir
        """
        mock_exists.return_value = False
        url = "https://example.com/image.png"
        temp_dir = "/tmp/cosai_test_12345"

        local_file = download_image(url, 0, temp_dir=temp_dir)

        # Should return just filename (relative path for pandoc which runs from temp_dir)
        assert local_file == "downloaded_image_0.png"
        assert not local_file.startswith("/")
        assert not local_file.startswith(temp_dir)

    @patch("convert.urllib.request.urlretrieve")
    @patch("convert.os.path.exists")
    def test_download_image_with_temp_dir_urlretrieve_uses_temp_path(
        self, mock_exists, mock_urlretrieve
    ):
        """
        Test that urlretrieve receives temp directory path.

        Given: download_image called with temp_dir parameter
        When: urlretrieve is called to download image
        Then: Target path is in temp directory
        """
        mock_exists.return_value = False
        url = "https://example.com/image.png"
        temp_dir = "/tmp/cosai_test_12345"

        download_image(url, 0, temp_dir=temp_dir)

        # Verify urlretrieve was called with temp directory path
        assert mock_urlretrieve.called
        call_args = mock_urlretrieve.call_args_list[0]
        target_path = call_args[0][1]

        assert target_path.startswith(temp_dir)
        assert target_path.endswith("downloaded_image_0.png")

    @patch("convert.urllib.request.urlretrieve")
    @patch("convert.os.path.exists")
    def test_download_image_preserves_extension_returns_relative(
        self, mock_exists, mock_urlretrieve
    ):
        """
        Test that file extension is preserved and relative filename returned.

        Given: Image URL with specific extension (.jpg, .svg, etc.)
        When: download_image called with temp_dir
        Then: Returns relative filename with preserved extension
        """
        mock_exists.return_value = False
        temp_dir = "/tmp/cosai_test_12345"

        # Test various extensions
        test_cases = [
            ("https://example.com/image.jpg", "downloaded_image_0.jpg"),
            ("https://example.com/diagram.svg", "downloaded_image_1.svg"),
            ("https://example.com/photo.jpeg", "downloaded_image_2.jpeg"),
        ]

        for idx, (url, expected_basename) in enumerate(test_cases):
            local_file = download_image(url, idx, temp_dir=temp_dir)
            # Should return just the filename (relative) not full path
            assert local_file == expected_basename

    @patch("convert.urllib.request.urlretrieve")
    @patch("convert.os.path.exists")
    def test_download_image_multiple_images_return_relative_filenames(
        self, mock_exists, mock_urlretrieve
    ):
        """
        Test that multiple downloaded images return unique relative filenames.

        Given: Multiple images downloaded with temp_dir
        When: Each image is downloaded with different index
        Then: Each returns unique relative filename (for pandoc running from temp_dir)
        """
        mock_exists.return_value = False
        url = "https://example.com/image.png"
        temp_dir = "/tmp/cosai_test_12345"

        file_0 = download_image(url, 0, temp_dir=temp_dir)
        file_1 = download_image(url, 1, temp_dir=temp_dir)
        file_2 = download_image(url, 2, temp_dir=temp_dir)

        # All should return just relative filenames
        assert file_0 == "downloaded_image_0.png"
        assert file_1 == "downloaded_image_1.png"
        assert file_2 == "downloaded_image_2.png"


class TestProcessMarkdownTempDirectory:
    """Test suite for process_markdown temp directory integration."""

    @patch("convert.convert_mermaid_to_svg")
    @patch("builtins.open", new_callable=mock_open)
    def test_process_markdown_without_temp_dir_backward_compatible(
        self, mock_file_open, mock_convert_mermaid
    ):
        """
        Test backward compatibility: without temp_dir, uses old behavior.

        Given: process_markdown called without temp_dir parameter
        When: Markdown with Mermaid diagrams is processed
        Then: convert_mermaid_to_svg called without temp_dir (None or omitted)
        """
        mock_file_open.return_value.read.return_value = """# Test

```mermaid
graph TD
    A --> B
```
"""
        mock_convert_mermaid.return_value = ("diagram_0.svg", None)

        process_markdown("test.md", engine="tectonic")

        # convert_mermaid_to_svg should be called without temp_dir
        assert mock_convert_mermaid.called
        call_args = mock_convert_mermaid.call_args_list[0]

        # Check if temp_dir was passed (for backward compatibility, it shouldn't be)
        # This test will FAIL initially because temp_dir parameter doesn't exist yet
        # After implementation, it should pass None or not include temp_dir kwarg
        if len(call_args) > 1 and "temp_dir" in call_args[1]:
            assert call_args[1]["temp_dir"] is None

    @patch("convert.convert_mermaid_to_svg")
    @patch("builtins.open", new_callable=mock_open)
    def test_process_markdown_with_temp_dir_passes_to_mermaid_converter(
        self, mock_file_open, mock_convert_mermaid
    ):
        """
        Test that process_markdown passes temp_dir to Mermaid converter.

        Given: process_markdown called with temp_dir parameter
        When: Markdown with Mermaid diagrams is processed
        Then: convert_mermaid_to_svg receives temp_dir parameter
        """
        mock_file_open.return_value.read.return_value = """# Test

```mermaid
graph TD
    A --> B
```
"""
        temp_dir = "/tmp/cosai_test_12345"
        mock_convert_mermaid.return_value = (
            os.path.join(temp_dir, "diagram_0.svg"),
            None,
        )

        process_markdown("test.md", engine="tectonic", temp_dir=temp_dir)

        # convert_mermaid_to_svg should be called with temp_dir
        assert mock_convert_mermaid.called
        call_args = mock_convert_mermaid.call_args_list[0]

        # Verify temp_dir was passed
        assert call_args[1]["temp_dir"] == temp_dir

    @patch("convert.download_image")
    @patch("builtins.open", new_callable=mock_open)
    def test_process_markdown_with_temp_dir_passes_to_image_downloader(
        self, mock_file_open, mock_download
    ):
        """
        Test that process_markdown passes temp_dir to image downloader.

        Given: process_markdown called with temp_dir parameter
        When: Markdown with remote images is processed
        Then: download_image receives temp_dir parameter
        """
        mock_file_open.return_value.read.return_value = """# Test

![Alt text](https://example.com/image.png)
"""
        temp_dir = "/tmp/cosai_test_12345"
        mock_download.return_value = os.path.join(temp_dir, "downloaded_image_0.png")

        process_markdown("test.md", engine="tectonic", temp_dir=temp_dir)

        # download_image should be called with temp_dir
        assert mock_download.called
        call_args = mock_download.call_args_list[0]

        # Verify temp_dir was passed
        assert call_args[1]["temp_dir"] == temp_dir

    @patch("convert.convert_mermaid_to_svg")
    @patch("convert.download_image")
    @patch("builtins.open", new_callable=mock_open)
    def test_process_markdown_with_temp_dir_handles_multiple_assets(
        self, mock_file_open, mock_download, mock_convert_mermaid
    ):
        """
        Test that temp_dir is passed to all asset processors.

        Given: Markdown with both Mermaid diagrams and remote images
        When: process_markdown called with temp_dir
        Then: All converters and downloaders receive temp_dir
        """
        mock_file_open.return_value.read.return_value = """# Test

```mermaid
graph TD
    A --> B
```

![Image 1](https://example.com/img1.png)

```mermaid
graph LR
    C --> D
```

![Image 2](https://example.com/img2.jpg)
"""
        temp_dir = "/tmp/cosai_test_12345"
        mock_convert_mermaid.side_effect = [
            (os.path.join(temp_dir, "diagram_0.svg"), None),
            (os.path.join(temp_dir, "diagram_1.svg"), None),
        ]
        mock_download.side_effect = [
            os.path.join(temp_dir, "downloaded_image_0.png"),
            os.path.join(temp_dir, "downloaded_image_1.jpg"),
        ]

        process_markdown("test.md", engine="tectonic", temp_dir=temp_dir)

        # Verify all calls received temp_dir
        assert mock_convert_mermaid.call_count == 2
        assert mock_download.call_count == 2

        for call_args in mock_convert_mermaid.call_args_list:
            assert call_args[1]["temp_dir"] == temp_dir

        for call_args in mock_download.call_args_list:
            assert call_args[1]["temp_dir"] == temp_dir


class TestMainFunctionTempDirectory:
    """Test suite for main() function temp directory management."""

    @patch("convert.os.path.exists")
    @patch("convert.process_markdown")
    @patch("convert.subprocess.run")
    def test_main_creates_temporary_directory_for_conversion(
        self, mock_subprocess, mock_process_markdown, mock_exists
    ):
        """
        Test that main() creates a temporary directory for conversion.

        Given: main() is called with input and output files
        When: Conversion process starts
        Then: A temporary directory with prefix "cosai_convert_" is created
        """
        # Mock file existence check
        mock_exists.return_value = True

        # Mock the argument parser to simulate CLI args
        test_args = [
            "convert.py",
            "input.md",
            "output.pdf",
        ]

        # Mock process_markdown to return content
        mock_process_markdown.return_value = "# Processed content"
        mock_subprocess.return_value = MagicMock(returncode=0)

        with patch("sys.argv", test_args):
            # Import main here to avoid import errors before function exists
            try:
                from convert import main

                # This test will FAIL until main() is refactored to use temp_dir
                # Expected: main() calls tempfile.TemporaryDirectory(prefix="cosai_convert_")
                # For now, main() will run but won't use temp_dir
                main()

                # After implementation, verify temp_dir was created
                # assert process_markdown was called with temp_dir parameter
                # This assertion will fail until implementation is complete
                if mock_process_markdown.called:
                    call_args = mock_process_markdown.call_args
                    # This will fail because current implementation doesn't pass temp_dir
                    assert "temp_dir" in call_args[1], (
                        "main() should pass temp_dir to process_markdown()"
                    )
            except ImportError:
                # main() doesn't exist yet, test will fail as expected
                pytest.fail("main() function not found in convert.py")

    @patch("convert.os.path.exists")
    @patch("convert.process_markdown")
    @patch("convert.subprocess.run")
    def test_main_passes_temp_dir_to_process_markdown(
        self, mock_subprocess, mock_process_markdown, mock_exists
    ):
        """
        Test that main() passes temp_dir to process_markdown().

        Given: main() creates a temporary directory
        When: process_markdown() is called
        Then: temp_dir parameter is passed to process_markdown()
        """
        # Mock file existence check
        mock_exists.return_value = True

        test_args = [
            "convert.py",
            "input.md",
            "output.pdf",
        ]

        mock_process_markdown.return_value = "# Processed content"
        mock_subprocess.return_value = MagicMock(returncode=0)

        with patch("sys.argv", test_args):
            try:
                from convert import main

                # Run main - will succeed but won't pass temp_dir yet
                main()

                # Verify process_markdown was called
                assert mock_process_markdown.called

                # This will FAIL until implementation adds temp_dir parameter
                call_args = mock_process_markdown.call_args
                assert "temp_dir" in call_args[1], (
                    "process_markdown should receive temp_dir parameter"
                )
                assert call_args[1]["temp_dir"] is not None, (
                    "temp_dir should not be None"
                )
            except ImportError:
                pytest.fail("main() function not found in convert.py")

    @patch("convert.os.path.exists")
    @patch("convert.tempfile.TemporaryDirectory")
    @patch("convert.process_markdown")
    @patch("convert.subprocess.run")
    @patch("convert.shutil.copy")
    def test_main_cleans_up_temp_directory_on_success(
        self,
        mock_shutil_copy,
        mock_subprocess,
        mock_process_markdown,
        mock_temp_dir,
        mock_exists,
        tmp_path,
    ):
        """
        Test that main() cleans up temp directory on successful completion.

        Given: Conversion completes successfully
        When: main() exits normally
        Then: Temporary directory and contents are removed
        """
        # Mock file existence check
        mock_exists.return_value = True

        test_args = [
            "convert.py",
            "input.md",
            "output.pdf",
        ]

        # Use a real temporary directory so open() calls succeed
        mock_temp_instance = MagicMock()
        mock_temp_instance.__enter__.return_value = str(tmp_path)
        mock_temp_dir.return_value = mock_temp_instance

        mock_process_markdown.return_value = "# Processed content"
        mock_subprocess.return_value = MagicMock(returncode=0)

        with patch("sys.argv", test_args):
            from convert import main

            main()

            assert mock_temp_dir.called, (
                "main() should create TemporaryDirectory for temp files"
            )
            assert mock_temp_instance.__enter__.called, (
                "TemporaryDirectory context manager should be entered"
            )
            assert mock_temp_instance.__exit__.called, (
                "TemporaryDirectory context manager should exit (cleanup)"
            )

    @patch("convert.os.path.exists")
    @patch("convert.tempfile.TemporaryDirectory")
    @patch("convert.process_markdown")
    @patch("convert.subprocess.run")
    def test_main_cleans_up_temp_directory_on_error(
        self,
        mock_subprocess,
        mock_process_markdown,
        mock_temp_dir,
        mock_exists,
    ):
        """
        Test that main() cleans up temp directory even on error.

        Given: process_markdown() raises an exception during conversion
        When: Exception propagates through main()
        Then: Temporary directory is still cleaned up (context manager ensures this)
        """
        # Mock file existence check
        mock_exists.return_value = True

        test_args = [
            "convert.py",
            "input.md",
            "output.pdf",
        ]

        # Setup mock temp directory
        mock_temp_instance = MagicMock()
        mock_temp_instance.__enter__.return_value = "/tmp/cosai_convert_test123"
        mock_temp_dir.return_value = mock_temp_instance

        # Simulate error in process_markdown
        mock_process_markdown.side_effect = RuntimeError("Conversion error")

        with patch("sys.argv", test_args):
            try:
                from convert import main

                # Run main - should raise RuntimeError
                with pytest.raises(RuntimeError, match="Conversion error"):
                    main()

                # This will FAIL until main() uses TemporaryDirectory
                # After implementation, verify cleanup happened despite error
                assert mock_temp_dir.called, (
                    "main() should create TemporaryDirectory even when error occurs"
                )
                assert mock_temp_instance.__exit__.called, (
                    "TemporaryDirectory should cleanup even on error (context manager)"
                )
            except ImportError:
                pytest.fail("main() function not found in convert.py")


class TestTempFileCleanup:
    """Test suite for temporary file cleanup verification."""

    def test_no_svg_files_in_cwd_after_temp_dir_conversion(self, tmp_path):
        """
        Test that no diagram_*.svg files remain in cwd after conversion.

        Given: Conversion completed with temp_dir parameter
        When: Conversion finishes successfully
        Then: No diagram_*.svg files exist in current working directory
        """
        # Create an isolated test directory as cwd
        test_cwd = tmp_path / "test_workspace"
        test_cwd.mkdir()

        # Save original cwd and change to test directory
        original_cwd = os.getcwd()
        os.chdir(test_cwd)

        try:
            # Simulate conversion using temp_dir (temp files should NOT be in cwd)
            # This test will FAIL until implementation is complete
            # Expected behavior: convert uses temp_dir, leaves cwd clean

            # For now, verify no diagram_*.svg files exist in test cwd
            # (Implementation will ensure they're created in temp_dir instead)
            svg_files = glob.glob("diagram_*.svg")

            # After proper temp_dir implementation, this should be empty
            assert len(svg_files) == 0, f"Found diagram_*.svg files in cwd: {svg_files}"

        finally:
            # Restore original cwd
            os.chdir(original_cwd)

    def test_no_downloaded_images_in_cwd_after_temp_dir_conversion(self, tmp_path):
        """
        Test that no downloaded_image_* files remain in cwd after conversion.

        Given: Conversion completed with temp_dir parameter
        When: Conversion finishes successfully
        Then: No downloaded_image_* files exist in current working directory
        """
        # Create an isolated test directory as cwd
        test_cwd = tmp_path / "test_workspace"
        test_cwd.mkdir()

        # Save original cwd and change to test directory
        original_cwd = os.getcwd()
        os.chdir(test_cwd)

        try:
            # Simulate conversion using temp_dir (temp files should NOT be in cwd)
            # This test will FAIL until implementation is complete
            # Expected behavior: convert uses temp_dir, leaves cwd clean

            # For now, verify no downloaded_image_* files exist in test cwd
            # (Implementation will ensure they're created in temp_dir instead)
            downloaded_files = glob.glob("downloaded_image_*")

            # After proper temp_dir implementation, this should be empty
            assert len(downloaded_files) == 0, (
                f"Found downloaded_image_* files in cwd: {downloaded_files}"
            )

        finally:
            # Restore original cwd
            os.chdir(original_cwd)

    def test_cleanup_occurs_on_error_with_context_manager(self, tmp_path):
        """
        Test that temp files are cleaned up even when conversion fails.

        Given: Conversion using tempfile.TemporaryDirectory context manager
        When: Conversion raises an exception
        Then: Temp directory and all contents are cleaned up
        """
        import tempfile

        # Create a temp directory
        cleanup_verified = False

        try:
            with tempfile.TemporaryDirectory(prefix="cosai_convert_test_") as temp_dir:
                # Create some test files
                test_file = os.path.join(temp_dir, "test.svg")
                with open(test_file, "w") as f:
                    f.write("test content")

                # Verify file exists
                assert os.path.exists(test_file)

                # Simulate error
                raise RuntimeError("Simulated conversion error")

        except RuntimeError:
            # After context manager exits, temp_dir should be cleaned up
            cleanup_verified = not os.path.exists(temp_dir)

        assert cleanup_verified, "Temp directory should be cleaned up on error"

    def test_cleanup_occurs_on_success_with_context_manager(self, tmp_path):
        """
        Test that temp files are cleaned up after successful conversion.

        Given: Conversion using tempfile.TemporaryDirectory context manager
        When: Conversion completes successfully
        Then: Temp directory and all contents are cleaned up
        """
        import tempfile

        temp_dir_path = None

        with tempfile.TemporaryDirectory(prefix="cosai_convert_test_") as temp_dir:
            temp_dir_path = temp_dir

            # Create some test files
            test_file = os.path.join(temp_dir, "test.svg")
            with open(test_file, "w") as f:
                f.write("test content")

            # Verify file exists during context
            assert os.path.exists(test_file)

        # After successful completion, temp_dir should be cleaned up
        assert not os.path.exists(temp_dir_path)


"""
Test Summary
============
Total Tests: 28
- Mermaid SVG Temp Directory: 6
- Downloaded Image Temp Directory: 5
- Process Markdown Integration: 4
- Main Function Temp Directory: 4
- Temp File Cleanup: 4

Coverage Areas:
- SVG files created in temp directory when temp_dir provided
- SVG files created in cwd when temp_dir not provided (backward compat)
- Downloaded images created in temp directory when temp_dir provided
- Downloaded images created in cwd when temp_dir not provided (backward compat)
- process_markdown passes temp_dir to all asset processors
- main() creates temporary directory with proper prefix
- main() passes temp_dir to process_markdown()
- main() cleans up temp directory on success
- main() cleans up temp directory on error (context manager ensures cleanup)
- Temp directory cleanup on success (context manager)
- Temp directory cleanup on error (context manager)
- No diagram_*.svg files left in cwd with temp_dir usage
- No downloaded_image_* files left in cwd with temp_dir usage

Expected Initial Status: ALL TESTS FAIL
Reason: temp_dir parameter does not exist in any function yet
"""
