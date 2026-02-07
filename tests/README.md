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
│   └── test_full_conversion.py    # Full conversion pipeline tests
└── unit/                          # Unit tests
    ├── __init__.py
    ├── test_engine_selection.py   # LaTeX engine selection tests
    ├── test_extract_mermaid_title.py  # Mermaid title extraction tests
    └── test_strip_trailing_whitespace.py  # Whitespace handling tests
```

## Test Categories

### Unit Tests (`tests/unit/`)

Fast, isolated tests that verify individual functions and components:

- **test_engine_selection.py**: Tests for `get_latex_engine()` and `load_converter_config()`
  - Priority-based engine selection (CLI > env > config > default)
  - Validation and error handling
  - Edge cases and whitespace handling

- **test_extract_mermaid_title.py**: Tests for `extract_mermaid_title()`
  - YAML frontmatter parsing
  - CoSAI theme application
  - Title extraction and removal

- **test_strip_trailing_whitespace.py**: Tests for `strip_trailing_whitespace()`
  - Whitespace removal from line ends
  - Line ending preservation
  - Edge cases

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

Current coverage: **68%** (41 tests passing)

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

- Python 3.10+
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
