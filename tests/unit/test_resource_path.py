"""
Tests for --resource-path flag functionality in convert.py.

This module tests the resource path behavior including:
- Inclusion of --resource-path flag in pandoc command
- Resource path set to input file's directory
- Handling of nested input file paths
- Fallback to '.' for bare filenames without directory component
"""

import os
from unittest.mock import MagicMock, patch

from convert import main


class TestResourcePathPandocCommand:
    """Tests for --resource-path flag in pandoc command."""

    def test_pandoc_cmd_includes_resource_path(self, tmp_path):
        """
        Test that pandoc command includes --resource-path flag.

        Given: convert.py called with an input file
        When: Pandoc command is constructed
        Then: --resource-path flag is present in the command
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf)]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run", return_value=MagicMock(returncode=0)
                    ) as mock_run:
                        main()

                        # Find the PDF generation call (not the .tex generation call)
                        pdf_call = None
                        for call_args in mock_run.call_args_list:
                            cmd = (
                                call_args[0][0]
                                if call_args[0]
                                else call_args[1].get("cmd", [])
                            )
                            if "-o" in cmd and cmd[cmd.index("-o") + 1].endswith(
                                ".pdf"
                            ):
                                pdf_call = cmd
                                break

                        assert pdf_call is not None, (
                            "PDF generation pandoc call not found"
                        )

                        # Check that --resource-path flag is present
                        resource_path_flags = [
                            arg
                            for arg in pdf_call
                            if arg.startswith("--resource-path=")
                        ]
                        assert len(resource_path_flags) > 0, (
                            "--resource-path flag not found in pandoc command"
                        )

    def test_resource_path_matches_input_file_directory(self, tmp_path):
        """
        Test that resource path equals the input file's directory.

        Given: convert.py called with input file at /path/to/input.md
        When: Pandoc command is constructed
        Then: --resource-path value equals os.path.dirname(os.path.abspath(input_file))
        """
        output_pdf = tmp_path / "output.pdf"
        input_file = "input.md"
        test_args = ["convert.py", input_file, str(output_pdf)]

        expected_resource_path = os.path.dirname(os.path.abspath(input_file)) or "."

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run", return_value=MagicMock(returncode=0)
                    ) as mock_run:
                        main()

                        # Find the PDF generation call
                        pdf_call = None
                        for call_args in mock_run.call_args_list:
                            cmd = (
                                call_args[0][0]
                                if call_args[0]
                                else call_args[1].get("cmd", [])
                            )
                            if "-o" in cmd and cmd[cmd.index("-o") + 1].endswith(
                                ".pdf"
                            ):
                                pdf_call = cmd
                                break

                        assert pdf_call is not None, (
                            "PDF generation pandoc call not found"
                        )

                        # Extract --resource-path value
                        resource_path_arg = None
                        for arg in pdf_call:
                            if arg.startswith("--resource-path="):
                                resource_path_arg = arg.split("=", 1)[1]
                                break

                        assert resource_path_arg is not None, (
                            "--resource-path flag not found"
                        )
                        assert resource_path_arg == expected_resource_path, (
                            f"Expected --resource-path={expected_resource_path}, "
                            f"got --resource-path={resource_path_arg}"
                        )

    def test_resource_path_with_nested_input_file(self, tmp_path):
        """
        Test that resource path works correctly with nested input file path.

        Given: convert.py called with input file at docs/paper.md
        When: Pandoc command is constructed
        Then: --resource-path value equals the absolute path to docs/
        """
        output_pdf = tmp_path / "output.pdf"
        input_file = "docs/paper.md"
        test_args = ["convert.py", input_file, str(output_pdf)]

        expected_resource_path = os.path.dirname(os.path.abspath(input_file))

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run", return_value=MagicMock(returncode=0)
                    ) as mock_run:
                        main()

                        # Find the PDF generation call
                        pdf_call = None
                        for call_args in mock_run.call_args_list:
                            cmd = (
                                call_args[0][0]
                                if call_args[0]
                                else call_args[1].get("cmd", [])
                            )
                            if "-o" in cmd and cmd[cmd.index("-o") + 1].endswith(
                                ".pdf"
                            ):
                                pdf_call = cmd
                                break

                        assert pdf_call is not None, (
                            "PDF generation pandoc call not found"
                        )

                        # Extract --resource-path value
                        resource_path_arg = None
                        for arg in pdf_call:
                            if arg.startswith("--resource-path="):
                                resource_path_arg = arg.split("=", 1)[1]
                                break

                        assert resource_path_arg is not None, (
                            "--resource-path flag not found"
                        )
                        assert resource_path_arg == expected_resource_path, (
                            f"Expected --resource-path={expected_resource_path}, "
                            f"got --resource-path={resource_path_arg}"
                        )

    def test_resource_path_uses_dot_for_bare_filename(self, tmp_path):
        """
        Test that resource path falls back to '.' when dirname is empty.

        Given: convert.py called where os.path.dirname returns empty string
        When: Pandoc command is constructed
        Then: --resource-path value equals '.' (current directory fallback)
        """
        output_pdf = tmp_path / "output.pdf"
        input_file = "paper.md"
        test_args = ["convert.py", input_file, str(output_pdf)]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    # Mock dirname to return empty string to test the or '.' fallback
                    with patch("convert.os.path.dirname", return_value=""):
                        with patch(
                            "convert.subprocess.run",
                            return_value=MagicMock(returncode=0),
                        ) as mock_run:
                            main()

                            # Find the PDF generation call
                            pdf_call = None
                            for call_args in mock_run.call_args_list:
                                cmd = (
                                    call_args[0][0]
                                    if call_args[0]
                                    else call_args[1].get("cmd", [])
                                )
                                if "-o" in cmd and cmd[cmd.index("-o") + 1].endswith(
                                    ".pdf"
                                ):
                                    pdf_call = cmd
                                    break

                            assert pdf_call is not None, (
                                "PDF generation pandoc call not found"
                            )

                            # Extract --resource-path value
                            resource_path_arg = None
                            for arg in pdf_call:
                                if arg.startswith("--resource-path="):
                                    resource_path_arg = arg.split("=", 1)[1]
                                    break

                            assert resource_path_arg is not None, (
                                "--resource-path flag not found"
                            )
                            assert resource_path_arg == ".", (
                                f"Expected --resource-path=., "
                                f"got --resource-path={resource_path_arg}"
                            )
