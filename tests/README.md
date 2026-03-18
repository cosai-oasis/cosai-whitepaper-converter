# Test Suite for CoSAI Whitepaper Converter

This directory contains comprehensive tests for the CoSAI Whitepaper Converter project, following Test-Driven Development (TDD) principles.

## Test Structure

```
tests/
├── __init__.py                     # Test package initialization
├── conftest.py                     # Shared pytest fixtures
├── README.md                       # This file
├── fixtures/                       # Test data files
│   └── sample_markdown.md
├── integration/                    # Integration tests
│   ├── __init__.py
│   ├── test_devcontainer_feature.py  # Devcontainer feature tests
│   └── test_full_conversion.py    # Full conversion pipeline tests
└── unit/                          # Unit tests
    ├── __init__.py
    ├── test_asset_paths.py        # Asset path resolution tests
    ├── test_callout_support.py    # GFM callout support tests
    ├── test_debug_flag.py         # Debug mode CLI tests
    ├── test_devcontainer_feature.py  # Devcontainer feature unit tests
    ├── test_engine_selection.py   # LaTeX engine selection tests
    ├── test_error_handling.py     # Error handling tests
    ├── test_extract_mermaid_title.py  # Mermaid title extraction tests
    ├── test_figure_refs.py        # Figure reference auto-numbering tests
    ├── test_font_rendering.py     # Font rendering tests
    ├── test_install_deps.py       # Install script tests
    ├── test_mermaid_conversion.py # Mermaid diagram conversion tests
    ├── test_resource_path.py      # Resource path tests
    ├── test_strip_blockquote_prefix.py  # Blockquote prefix tests
    ├── test_strip_html_comment_attributes.py  # HTML comment attribute tests
    ├── test_strip_trailing_whitespace.py  # Whitespace handling tests
    ├── test_temp_file_cleanup.py  # Temp file cleanup tests
    ├── test_toc_stripping.py      # TOC stripping tests
    ├── test_unicode_normalization.py  # Unicode normalization tests
    └── test_verify_deps.py        # Dependency verification tests
```

## Test Categories

### Unit Tests (`tests/unit/`)

Fast, isolated tests that verify individual functions and components:

- **test_engine_selection.py**: LaTeX engine selection priority (CLI > env > config > default)
- **test_extract_mermaid_title.py**: Mermaid YAML frontmatter parsing, CoSAI theme, title extraction
- **test_strip_trailing_whitespace.py**: Whitespace removal, line ending preservation
- **test_figure_refs.py**: Figure reference auto-numbering, registry building, link rewriting, validation
- **test_toc_stripping.py**: TOC section removal (H1-H4 headings, bold text variants)
- **test_strip_html_comment_attributes.py**: HTML comment unwrapping for Pandoc attributes
- **test_debug_flag.py**: Debug mode CLI flag and intermediate file saving
- **test_mermaid_conversion.py**: Mermaid diagram to SVG conversion
- **test_unicode_normalization.py**: Unicode character handling for LaTeX engines
- **test_error_handling.py**: Error scenarios and ConversionError diagnostics
- **test_callout_support.py**: GFM callout syntax support
- **test_asset_paths.py**: Asset and template path resolution
- **test_font_rendering.py**: Font rendering configuration
- **test_resource_path.py**: Resource path resolution
- **test_strip_blockquote_prefix.py**: Blockquote prefix handling
- **test_temp_file_cleanup.py**: Temporary file lifecycle
- **test_install_deps.py**: Install script validation
- **test_verify_deps.py**: Dependency verification script
- **test_devcontainer_feature.py**: Devcontainer feature unit tests

### Integration Tests (`tests/integration/`)

Tests that verify the complete conversion pipeline:

- **test_full_conversion.py**: End-to-end conversion tests
  - Full conversion with different LaTeX engines
  - Environment variable integration
  - Configuration file integration
  - CLI argument priority
  - Metadata handling
  - Error scenarios

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Only Unit Tests

```bash
pytest tests/unit/
```

### Run Only Integration Tests

```bash
pytest -m integration
```

### Skip Integration Tests

```bash
pytest -m "not integration"
```

### Run Specific Test File

```bash
pytest tests/integration/test_full_conversion.py
```

### Run Specific Test Function

```bash
pytest tests/integration/test_full_conversion.py::test_conversion_with_tectonic_engine
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage Report

```bash
# Terminal report
pytest --cov=convert --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=convert --cov-report=html
open htmlcov/index.html
```

### Run with Coverage for Specific Test Type

```bash
# Unit test coverage
pytest tests/unit/ --cov=convert --cov-report=term

# Integration test coverage
pytest -m integration --cov=convert --cov-report=term
```

## Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.integration`: Integration tests (slower, may have dependencies)
- `@pytest.mark.unit`: Unit tests (fast, isolated)
- `@pytest.mark.skipif`: Conditional tests based on system capabilities

## Coverage Targets

- **Overall**: 80% minimum
- **Critical modules**: 90%+ (engine selection, config loading)
- **Utility functions**: 85%+ (markdown processing, whitespace handling)

Run `pytest --cov=convert --cov-report=term-missing` to see current coverage.

## Test Development Workflow

Following strict TDD principles:

1. **RED**: Write failing tests first
   ```bash
   pytest tests/unit/test_new_feature.py  # Should fail
   ```

2. **GREEN**: Implement minimal code to pass tests
   ```bash
   # Edit convert.py
   pytest tests/unit/test_new_feature.py  # Should pass
   ```

3. **REFACTOR**: Improve code while keeping tests green
   ```bash
   pytest tests/  # All tests should still pass
   ```

## Fixtures

Common test fixtures are defined in `conftest.py`:

- `temp_dir`: Temporary directory for test files
- `sample_markdown_content`: Sample markdown text
- `sample_mermaid_code`: Sample Mermaid diagram
- `sample_mermaid_with_title`: Mermaid with frontmatter title
- `converter_config_path`: Path to config file
- `valid_converter_config`: Valid config dictionary
- `clean_env`: Clean environment without LATEX_ENGINE

Integration test fixtures:

- `integration_temp_dir`: Temporary directory for integration tests
- `sample_markdown_file`: Complete markdown file for conversion
- `converter_config_file`: Config file for integration testing

## System Requirements for Tests

### Required

- Python 3.12+
- pytest
- pytest-cov

### Optional (for full integration tests)

- **tectonic**: Required for default engine tests (installed in devcontainer)
- **pdflatex**: Optional, tests will be skipped if not available
- **pandoc**: Required for conversion tests (installed in devcontainer)

Tests automatically skip when dependencies are missing using `@pytest.mark.skipif`.

## CI/CD Integration

### Quick Test Suite (for CI)

```bash
# Fast tests only (skip integration)
pytest -m "not integration" --cov=convert --cov-report=xml
```

### Full Test Suite (for release)

```bash
# All tests including integration
pytest --cov=convert --cov-report=xml --cov-report=html
```

## Writing New Tests

### Test Naming Convention

```python
def test_<function>_<scenario>_<expected_outcome>():
    """
    Clear description of what is being tested.

    Given: Initial conditions
    When: Action taken
    Then: Expected outcome
    """
```

### Test Organization

1. **Unit tests**: One test file per module function
2. **Integration tests**: Group by feature or user journey
3. **Fixtures**: Add to `conftest.py` if used across multiple files

### Example Unit Test

```python
def test_function_name_with_valid_input_succeeds():
    """
    Test that function_name works with valid input.

    Given: Valid input parameters
    When: function_name is called
    Then: Returns expected result
    """
    # Arrange
    input_data = "test input"
    expected = "test output"

    # Act
    result = function_name(input_data)

    # Assert
    assert result == expected
```

### Example Integration Test

```python
@pytest.mark.integration
def test_full_conversion_succeeds(sample_markdown_file, integration_temp_dir):
    """
    Test complete conversion from markdown to PDF.

    Given: A valid markdown file
    When: Full conversion is run
    Then: PDF is created successfully
    """
    output_pdf = integration_temp_dir / "output.pdf"

    # Mock subprocess for testing
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        # Run conversion
        result = convert_markdown_to_pdf(
            str(sample_markdown_file),
            str(output_pdf)
        )

    # Verify
    assert result is True
    assert mock_run.called
```

## Debugging Tests

### Run Single Test with Debugging

```bash
pytest tests/integration/test_full_conversion.py::test_name -vv -s
```

### Show Print Statements

```bash
pytest -s
```

### Stop on First Failure

```bash
pytest -x
```

### Show Local Variables on Failure

```bash
pytest -l
```

### Drop to Debugger on Failure

```bash
pytest --pdb
```

## Known Test Limitations

1. **pdflatex tests**: Skipped if pdflatex not installed
2. **Integration tests**: Mock subprocess calls to avoid full PDF generation
3. **Mermaid tests**: Mock external mermaid-cli calls in unit tests

## Test Maintenance

- Update tests when requirements change
- Add tests for bug fixes (TDD for bugs)
- Maintain 80%+ coverage target
- Review test failures in CI/CD
- Keep test execution time under 1 minute for full suite

## Support

For questions about tests:
- Review existing tests for examples
- Check `conftest.py` for available fixtures
- Consult CLAUDE.md for TDD workflow
- Run `pytest --markers` to see all available markers
