"""
Shared test fixtures and configuration for pytest.

This module provides common fixtures used across test suites, including:
- Temporary file handling
- Sample markdown content
- Mock configuration
- Environment variable management
"""

import os
import pytest
import tempfile
import json
from pathlib import Path


def pytest_configure(config):
    """Apply default marker expression when -m is not specified on the CLI.

    Allows explicit override: ``pytest -m integration`` or ``pytest -m ""``.
    """
    m_provided = any(
        arg == "-m" or arg.startswith("-m=") or arg.startswith("--markexpr")
        for arg in config.invocation_params.args
    )
    if not m_provided:
        config.option.markexpr = "not integration and not slow"


@pytest.fixture
def temp_dir():
    """
    Provide a temporary directory for test files.

    Yields:
        Path: Temporary directory path that is cleaned up after test.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown_content():
    """
    Provide sample markdown content for testing.

    Returns:
        str: Sample markdown with various elements (headers, lists, code blocks).
    """
    return """# Test Document

This is a test document.

## Section 1

Some content here.

- Item 1
- Item 2
- Item 3

## Section 2

More content.
"""


@pytest.fixture
def sample_mermaid_code():
    """
    Provide sample Mermaid diagram code.

    Returns:
        str: Valid Mermaid diagram code.
    """
    return """graph TD
    A[Start] --> B[Process]
    B --> C[End]
"""


@pytest.fixture
def sample_mermaid_with_title():
    """
    Provide sample Mermaid diagram with frontmatter title.

    Returns:
        str: Mermaid diagram with YAML frontmatter title.
    """
    return """---
title: "Sample Diagram Title"
---
graph TD
    A[Start] --> B[Process]
    B --> C[End]
"""


@pytest.fixture
def converter_config_path(temp_dir):
    """
    Provide path to converter config file.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        Path: Path to converter.json config file.
    """
    return temp_dir / "converter.json"


@pytest.fixture
def valid_converter_config(converter_config_path):
    """
    Create a valid converter.json config file.

    Args:
        converter_config_path: Path to config file.

    Returns:
        dict: Configuration dictionary.
    """
    config = {"latex_engine": "tectonic", "syntax_highlighting": "idiomatic"}
    with open(converter_config_path, "w") as f:
        json.dump(config, f)
    return config


@pytest.fixture
def clean_env():
    """
    Provide clean environment without LATEX_ENGINE variable.

    Saves current environment, removes LATEX_ENGINE if present,
    then restores original environment after test.
    """
    original_value = os.environ.get("LATEX_ENGINE")
    if "LATEX_ENGINE" in os.environ:
        del os.environ["LATEX_ENGINE"]

    yield

    # Restore original value
    if original_value is not None:
        os.environ["LATEX_ENGINE"] = original_value
    elif "LATEX_ENGINE" in os.environ:
        del os.environ["LATEX_ENGINE"]
