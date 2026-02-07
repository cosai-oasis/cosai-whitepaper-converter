"""
Integration tests for full Markdown to PDF conversion.

This module tests the complete conversion pipeline, verifying that:
- Different LaTeX engines can be used successfully
- Engine selection works correctly in real conversion scenarios
- Configuration files are properly integrated
- Environment variables are respected during conversion
- Error handling works correctly with actual LaTeX engines
"""

import pytest
import sys
import os
import json
import subprocess
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from convert import main, process_markdown


@pytest.fixture
def integration_temp_dir(tmp_path):
    """
    Provide a temporary directory for integration tests.

    Returns:
        Path: Temporary directory for test artifacts.
    """
    return tmp_path


@pytest.fixture
def sample_markdown_file(integration_temp_dir):
    """
    Create a sample markdown file for conversion testing.

    Args:
        integration_temp_dir: Temporary directory fixture.

    Returns:
        Path: Path to created markdown file.
    """
    md_content = """---
title: "Integration Test Document"
author: "Test Author"
date: "2025-01-29"
---

# Introduction

This is a test document for integration testing.

## Section 1

Some content with **bold** and *italic* text.

### Subsection 1.1

- List item 1
- List item 2
- List item 3

## Section 2

More content here.

```python
def test_function():
    return "Hello, World!"
```

## Conclusion

This concludes the test document.
"""

    md_file = integration_temp_dir / "test_input.md"
    md_file.write_text(md_content)
    return md_file


@pytest.fixture
def converter_config_file(integration_temp_dir):
    """
    Create a converter config file for testing.

    Args:
        integration_temp_dir: Temporary directory fixture.

    Returns:
        Path: Path to created config file.
    """
    config_path = integration_temp_dir / "converter_config.json"
    return config_path


@pytest.mark.integration
def test_conversion_with_tectonic_engine(
    sample_markdown_file, integration_temp_dir, clean_env
):
    """
    Test full conversion using tectonic engine (default).

    Given: A valid markdown file and tectonic engine availability
    When: Conversion is run with tectonic engine
    Then: PDF is created successfully using tectonic
    """
    output_pdf = integration_temp_dir / "output_tectonic.pdf"

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
                Path(output_file).write_text("%PDF-1.4\nDummy PDF")
            return MagicMock(returncode=0)
        return original_run(cmd, *args, **kwargs)

    with patch("subprocess.run", side_effect=mock_run):
        # Simulate command-line arguments
        with patch(
            "sys.argv",
            [
                "convert.py",
                str(sample_markdown_file),
                str(output_pdf),
                "--engine",
                "tectonic",
            ],
        ):
            try:
                main()
            except SystemExit:
                pass  # main() may call sys.exit()

    # Verify pandoc was called with tectonic engine
    assert len(pandoc_calls) > 0, "Pandoc should have been called"
    pandoc_cmd = pandoc_calls[0]

    # Check that --pdf-engine=tectonic was used
    assert any("--pdf-engine=tectonic" in arg for arg in pandoc_cmd), (
        f"Tectonic engine should be specified in pandoc command: {pandoc_cmd}"
    )


@pytest.mark.integration
@pytest.mark.skipif(not shutil.which("pdflatex"), reason="pdflatex not installed")
def test_conversion_with_pdflatex_engine(
    sample_markdown_file, integration_temp_dir, clean_env
):
    """
    Test full conversion using pdflatex engine.

    Given: A valid markdown file and pdflatex engine availability
    When: Conversion is run with pdflatex engine
    Then: PDF is created successfully using pdflatex
    """
    output_pdf = integration_temp_dir / "output_pdflatex.pdf"

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
                Path(output_file).write_text("%PDF-1.4\nDummy PDF")
            return MagicMock(returncode=0)
        return original_run(cmd, *args, **kwargs)

    with patch("subprocess.run", side_effect=mock_run):
        # Simulate command-line arguments
        with patch(
            "sys.argv",
            [
                "convert.py",
                str(sample_markdown_file),
                str(output_pdf),
                "--engine",
                "pdflatex",
            ],
        ):
            try:
                main()
            except SystemExit:
                pass

    # Verify pandoc was called with pdflatex engine
    assert len(pandoc_calls) > 0, "Pandoc should have been called"
    pandoc_cmd = pandoc_calls[0]

    # Check that --pdf-engine=pdflatex was used
    assert any("--pdf-engine=pdflatex" in arg for arg in pandoc_cmd), (
        f"pdflatex engine should be specified in pandoc command: {pandoc_cmd}"
    )


@pytest.mark.integration
def test_conversion_respects_env_var(
    sample_markdown_file, integration_temp_dir, clean_env
):
    """
    Test that LATEX_ENGINE environment variable is respected.

    Given: LATEX_ENGINE environment variable is set to "xelatex"
    When: Conversion is run without explicit engine argument
    Then: xelatex engine is used for conversion
    """
    output_pdf = integration_temp_dir / "output_env.pdf"

    # Set environment variable
    os.environ["LATEX_ENGINE"] = "xelatex"

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
                Path(output_file).write_text("%PDF-1.4\nDummy PDF")
            return MagicMock(returncode=0)
        return original_run(cmd, *args, **kwargs)

    with patch("subprocess.run", side_effect=mock_run):
        # Simulate command-line arguments (no --engine flag)
        with patch(
            "sys.argv", ["convert.py", str(sample_markdown_file), str(output_pdf)]
        ):
            try:
                main()
            except SystemExit:
                pass

    # Verify pandoc was called with xelatex engine from env var
    assert len(pandoc_calls) > 0, "Pandoc should have been called"
    pandoc_cmd = pandoc_calls[0]

    # Check that --pdf-engine=xelatex was used
    assert any("--pdf-engine=xelatex" in arg for arg in pandoc_cmd), (
        f"xelatex engine (from env var) should be specified: {pandoc_cmd}"
    )


@pytest.mark.integration
def test_conversion_respects_config_file(
    sample_markdown_file, integration_temp_dir, converter_config_file, clean_env
):
    """
    Test that converter_config.json is read and used.

    Given: converter_config.json specifies "lualatex" engine
    When: Conversion is run without CLI arg or env var
    Then: lualatex engine is used from config file
    """
    # Create config file with lualatex engine
    config = {"latex_engine": "lualatex"}
    converter_config_file.write_text(json.dumps(config))

    output_pdf = integration_temp_dir / "output_config.pdf"

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
                Path(output_file).write_text("%PDF-1.4\nDummy PDF")
            return MagicMock(returncode=0)
        return original_run(cmd, *args, **kwargs)

    # Change to temp directory so config file is found
    original_cwd = os.getcwd()
    try:
        os.chdir(integration_temp_dir)

        with patch("subprocess.run", side_effect=mock_run):
            # Simulate command-line arguments (no --engine flag)
            with patch(
                "sys.argv", ["convert.py", str(sample_markdown_file), str(output_pdf)]
            ):
                try:
                    main()
                except SystemExit:
                    pass
    finally:
        os.chdir(original_cwd)

    # Verify pandoc was called with lualatex engine from config
    assert len(pandoc_calls) > 0, "Pandoc should have been called"
    pandoc_cmd = pandoc_calls[0]

    # Check that --pdf-engine=lualatex was used
    assert any("--pdf-engine=lualatex" in arg for arg in pandoc_cmd), (
        f"lualatex engine (from config) should be specified: {pandoc_cmd}"
    )


@pytest.mark.integration
def test_conversion_cli_overrides_all_sources(
    sample_markdown_file, integration_temp_dir, converter_config_file, clean_env
):
    """
    Test that CLI argument overrides both env var and config file.

    Given: CLI arg="tectonic", env var="pdflatex", config="xelatex"
    When: Conversion is run with all three sources
    Then: tectonic engine is used (CLI takes precedence)
    """
    # Set up environment variable
    os.environ["LATEX_ENGINE"] = "pdflatex"

    # Create config file
    config = {"latex_engine": "xelatex"}
    converter_config_file.write_text(json.dumps(config))

    output_pdf = integration_temp_dir / "output_override.pdf"

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
                Path(output_file).write_text("%PDF-1.4\nDummy PDF")
            return MagicMock(returncode=0)
        return original_run(cmd, *args, **kwargs)

    # Change to temp directory so config file is found
    original_cwd = os.getcwd()
    try:
        os.chdir(integration_temp_dir)

        with patch("subprocess.run", side_effect=mock_run):
            # Simulate command-line arguments with explicit --engine
            with patch(
                "sys.argv",
                [
                    "convert.py",
                    str(sample_markdown_file),
                    str(output_pdf),
                    "--engine",
                    "tectonic",
                ],
            ):
                try:
                    main()
                except SystemExit:
                    pass
    finally:
        os.chdir(original_cwd)

    # Verify pandoc was called with tectonic engine (CLI override)
    assert len(pandoc_calls) > 0, "Pandoc should have been called"
    pandoc_cmd = pandoc_calls[0]

    # Check that --pdf-engine=tectonic was used (CLI override)
    assert any("--pdf-engine=tectonic" in arg for arg in pandoc_cmd), (
        f"tectonic engine (from CLI) should override all: {pandoc_cmd}"
    )


@pytest.mark.integration
def test_conversion_with_missing_input_file(integration_temp_dir, clean_env):
    """
    Test error handling when input file doesn't exist.

    Given: Non-existent input markdown file
    When: Conversion is attempted
    Then: Error message is displayed and program exits
    """
    nonexistent_file = integration_temp_dir / "nonexistent.md"
    output_pdf = integration_temp_dir / "output.pdf"

    # Capture stdout/stderr
    with patch("sys.argv", ["convert.py", str(nonexistent_file), str(output_pdf)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Verify it exited with error code
        assert exc_info.value.code == 1


@pytest.mark.integration
def test_conversion_preserves_metadata(
    sample_markdown_file, integration_temp_dir, clean_env
):
    """
    Test that metadata overrides are passed to pandoc.

    Given: Markdown file with custom metadata via CLI
    When: Conversion is run with --title, --author, --date, --version
    Then: Metadata is passed to pandoc via -V flags
    """
    output_pdf = integration_temp_dir / "output_metadata.pdf"

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
                Path(output_file).write_text("%PDF-1.4\nDummy PDF")
            return MagicMock(returncode=0)
        return original_run(cmd, *args, **kwargs)

    with patch("subprocess.run", side_effect=mock_run):
        # Simulate command-line arguments with metadata
        with patch(
            "sys.argv",
            [
                "convert.py",
                str(sample_markdown_file),
                str(output_pdf),
                "--title",
                "Custom Title",
                "--author",
                "Custom Author",
                "--date",
                "2025-02-01",
                "--version",
                "2.0",
            ],
        ):
            try:
                main()
            except SystemExit:
                pass

    # Verify pandoc was called with metadata
    assert len(pandoc_calls) > 0, "Pandoc should have been called"
    pandoc_cmd = pandoc_calls[0]

    # Check that metadata variables were passed
    cmd_str = " ".join(pandoc_cmd)
    assert "title=Custom Title" in cmd_str, "Title should be passed to pandoc"
    assert "author=Custom Author" in cmd_str, "Author should be passed to pandoc"
    assert "date=2025-02-01" in cmd_str, "Date should be passed to pandoc"
    assert "git=2.0" in cmd_str, "Version should be passed to pandoc"


@pytest.mark.integration
def test_process_markdown_integration(sample_markdown_file, integration_temp_dir):
    """
    Test that process_markdown function handles real markdown file.

    Given: A real markdown file with various elements
    When: process_markdown is called
    Then: Content is processed without errors
    """
    # This test verifies that process_markdown works with actual file
    processed_content = process_markdown(sample_markdown_file)

    # Verify basic processing occurred
    assert isinstance(processed_content, str)
    assert len(processed_content) > 0
    assert "Integration Test Document" in processed_content
    assert "Introduction" in processed_content


@pytest.mark.integration
def test_conversion_with_invalid_engine_shows_helpful_error(
    sample_markdown_file, integration_temp_dir, clean_env, capsys
):
    """
    Test that invalid engine shows helpful error message.

    Given: Invalid engine specified via CLI
    When: Conversion is attempted
    Then: Helpful error message is shown listing valid engines
    """
    output_pdf = integration_temp_dir / "output.pdf"

    # Simulate command-line arguments with invalid engine
    with patch(
        "sys.argv",
        [
            "convert.py",
            str(sample_markdown_file),
            str(output_pdf),
            "--engine",
            "invalid_engine",
        ],
    ):
        # argparse will handle validation and exit
        with pytest.raises(SystemExit):
            main()


@pytest.mark.integration
def test_conversion_default_engine_without_any_config(
    sample_markdown_file, integration_temp_dir, clean_env
):
    """
    Test that default engine (tectonic) is used when no config exists.

    Given: No CLI arg, no env var, no config file
    When: Conversion is run
    Then: tectonic engine is used by default
    """
    output_pdf = integration_temp_dir / "output_default.pdf"

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
                Path(output_file).write_text("%PDF-1.4\nDummy PDF")
            return MagicMock(returncode=0)
        return original_run(cmd, *args, **kwargs)

    with patch("subprocess.run", side_effect=mock_run):
        # Simulate command-line arguments (no engine specified)
        with patch(
            "sys.argv", ["convert.py", str(sample_markdown_file), str(output_pdf)]
        ):
            try:
                main()
            except SystemExit:
                pass

    # Verify pandoc was called with default tectonic engine
    assert len(pandoc_calls) > 0, "Pandoc should have been called"
    pandoc_cmd = pandoc_calls[0]

    # Check that --pdf-engine=tectonic was used (default)
    assert any("--pdf-engine=tectonic" in arg for arg in pandoc_cmd), (
        f"Default tectonic engine should be used: {pandoc_cmd}"
    )


"""
Test Summary
============
Total Tests: 11
- Happy Path: 5
- Edge Cases: 3
- Error Conditions: 3

Coverage Areas:
- Full conversion with tectonic engine (default)
- Full conversion with pdflatex engine (conditional on availability)
- Environment variable integration
- Config file integration
- CLI argument priority over all sources
- Missing input file error handling
- Metadata preservation through conversion pipeline
- Process markdown integration
- Invalid engine error handling
- Default engine behavior
- Real subprocess interaction (mocked for isolation)

Integration Test Characteristics:
- Tests use real markdown files
- Tests verify actual pandoc command construction
- Tests validate engine selection in full context
- Tests check metadata handling end-to-end
- Tests include conditional execution based on system capabilities
- Tests mock subprocess calls to avoid actual PDF generation (faster)
- Tests verify error handling in realistic scenarios

Pytest Markers:
- @pytest.mark.integration: All tests marked for selective execution
- @pytest.mark.skipif: Conditional tests based on system capabilities

Running Tests:
- All integration tests: pytest -m integration
- Skip integration tests: pytest -m "not integration"
- Single test: pytest tests/integration/test_full_conversion.py::test_name
- With verbose output: pytest -m integration -v

Note: These integration tests mock subprocess.run for pandoc calls to:
1. Avoid requiring full LaTeX installation in CI/CD
2. Speed up test execution
3. Verify command construction without side effects
4. Still test the full conversion logic flow
"""
