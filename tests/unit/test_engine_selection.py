"""
Tests for LaTeX engine selection functionality.

This module tests the engine selection logic that determines which LaTeX
engine (tectonic, pdflatex, xelatex, lualatex) to use based on:
- Command-line arguments (highest priority)
- Environment variables (LATEX_ENGINE)
- Configuration file (converter.json)
- Default value (tectonic)
"""

import pytest
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# These imports will FAIL until implementation exists (RED phase)
from convert import get_latex_engine, load_converter_config


class TestGetLatexEngine:
    """Test suite for get_latex_engine function."""

    def test_get_latex_engine_cli_flag_takes_precedence(
        self, clean_env, converter_config_path
    ):
        """
        Test that CLI argument takes precedence over all other sources.

        Given: CLI arg="pdflatex", env="tectonic", config="xelatex"
        When: get_latex_engine is called with CLI arg
        Then: Returns "pdflatex"
        """
        # Set up environment and config
        os.environ["LATEX_ENGINE"] = "tectonic"
        config = {"latex_engine": "xelatex"}
        with open(converter_config_path, "w") as f:
            json.dump(config, f)

        result = get_latex_engine(
            cli_engine="pdflatex", config_path=converter_config_path
        )

        assert result == "pdflatex"

    def test_get_latex_engine_env_var_when_no_cli(
        self, clean_env, converter_config_path
    ):
        """
        Test that environment variable is used when no CLI argument.

        Given: No CLI arg, env="xelatex", config="pdflatex"
        When: get_latex_engine is called without CLI arg
        Then: Returns "xelatex"
        """
        # Set up environment and config
        os.environ["LATEX_ENGINE"] = "xelatex"
        config = {"latex_engine": "pdflatex"}
        with open(converter_config_path, "w") as f:
            json.dump(config, f)

        result = get_latex_engine(cli_engine=None, config_path=converter_config_path)

        assert result == "xelatex"

    def test_get_latex_engine_env_var_case_insensitive(self, clean_env):
        """
        Test that environment variable is case-insensitive.

        Given: env="TECTONIC" (uppercase)
        When: get_latex_engine is called
        Then: Returns "tectonic" (lowercase)
        """
        os.environ["LATEX_ENGINE"] = "TECTONIC"

        result = get_latex_engine(cli_engine=None)

        assert result == "tectonic"

    def test_get_latex_engine_config_file_when_no_cli_no_env(
        self, clean_env, converter_config_path
    ):
        """
        Test that config file is used when no CLI arg or env var.

        Given: No CLI arg, no env var, config="lualatex"
        When: get_latex_engine is called
        Then: Returns "lualatex"
        """
        config = {"latex_engine": "lualatex"}
        with open(converter_config_path, "w") as f:
            json.dump(config, f)

        result = get_latex_engine(cli_engine=None, config_path=converter_config_path)

        assert result == "lualatex"

    def test_get_latex_engine_config_file_not_found_uses_default(self, clean_env):
        """
        Test that default is used when config file doesn't exist.

        Given: No CLI arg, no env var, no config file
        When: get_latex_engine is called
        Then: Returns "tectonic" (default)
        """
        result = get_latex_engine(
            cli_engine=None, config_path="/nonexistent/converter.json"
        )

        assert result == "tectonic"

    def test_get_latex_engine_default_is_tectonic(self, clean_env):
        """
        Test that default engine is tectonic.

        Given: No CLI arg, no env var, no config
        When: get_latex_engine is called with no parameters
        Then: Returns "tectonic"
        """
        result = get_latex_engine()

        assert result == "tectonic"

    def test_get_latex_engine_invalid_engine_raises_error(self, clean_env):
        """
        Test that invalid engine name raises ValueError.

        Given: CLI arg="invalid_engine"
        When: get_latex_engine is called
        Then: ValueError is raised with helpful message
        """
        with pytest.raises(
            ValueError,
            match=r"Invalid LaTeX engine 'invalid_engine'\. Valid engines: tectonic, pdflatex, xelatex, lualatex",
        ):
            get_latex_engine(cli_engine="invalid_engine")

    def test_get_latex_engine_validates_all_sources(self, clean_env):
        """
        Test that validation occurs regardless of source.

        Given: env="bad_engine"
        When: get_latex_engine is called
        Then: ValueError is raised
        """
        os.environ["LATEX_ENGINE"] = "bad_engine"

        with pytest.raises(ValueError, match="Invalid LaTeX engine"):
            get_latex_engine(cli_engine=None)

    def test_get_latex_engine_invalid_config_value_raises_error(
        self, clean_env, converter_config_path
    ):
        """
        Test that invalid engine in config file raises ValueError.

        Given: Config file with invalid engine value
        When: get_latex_engine is called
        Then: ValueError is raised with helpful message
        """
        config = {"latex_engine": "bad_engine"}
        with open(converter_config_path, "w") as f:
            json.dump(config, f)

        with pytest.raises(ValueError, match="Invalid LaTeX engine"):
            get_latex_engine(cli_engine=None, config_path=converter_config_path)

    def test_get_latex_engine_all_valid_engines_accepted(self, clean_env):
        """
        Test that all valid engine names are accepted.

        Given: Each valid engine name
        When: get_latex_engine is called
        Then: Engine name is returned without error
        """
        valid_engines = ["tectonic", "pdflatex", "xelatex", "lualatex"]

        for engine in valid_engines:
            result = get_latex_engine(cli_engine=engine)
            assert result == engine

    def test_get_latex_engine_whitespace_handling(self, clean_env):
        """
        Test that whitespace in engine name is handled.

        Given: CLI arg=" tectonic " (with spaces)
        When: get_latex_engine is called
        Then: Returns "tectonic" (stripped)
        """
        result = get_latex_engine(cli_engine=" tectonic ")

        assert result == "tectonic"

    def test_get_latex_engine_empty_string_cli_treated_as_not_provided(self, clean_env):
        """
        Test that empty string CLI argument is treated as not provided.

        Given: CLI arg="" (empty string), env="pdflatex"
        When: get_latex_engine is called
        Then: Falls back to env var (returns "pdflatex")
        """
        os.environ["LATEX_ENGINE"] = "pdflatex"

        result = get_latex_engine(cli_engine="")

        assert result == "pdflatex"


class TestLoadConverterConfig:
    """Test suite for load_converter_config function."""

    def test_load_converter_config_valid_json(self, converter_config_path):
        """
        Test loading valid JSON configuration file.

        Given: Valid converter.json with latex_engine setting
        When: load_converter_config is called
        Then: Configuration dictionary is returned
        """
        config = {"latex_engine": "tectonic", "syntax_highlighting": "idiomatic"}
        with open(converter_config_path, "w") as f:
            json.dump(config, f)

        result = load_converter_config(converter_config_path)

        assert result == config
        assert result["latex_engine"] == "tectonic"

    def test_load_converter_config_missing_file_returns_empty(self):
        """
        Test that missing config file returns empty dict.

        Given: Non-existent config file path
        When: load_converter_config is called
        Then: Empty dictionary is returned (no exception)
        """
        result = load_converter_config("/nonexistent/converter.json")

        assert result == {}

    def test_load_converter_config_invalid_json_returns_empty(self, temp_dir):
        """
        Test that invalid JSON returns empty dict.

        Given: Config file with malformed JSON
        When: load_converter_config is called
        Then: Empty dictionary is returned (graceful handling)
        """
        invalid_json_path = temp_dir / "invalid.json"
        with open(invalid_json_path, "w") as f:
            f.write("{ invalid json here }")

        result = load_converter_config(invalid_json_path)

        assert result == {}

    def test_load_converter_config_empty_file_returns_empty(self, temp_dir):
        """
        Test that empty config file returns empty dict.

        Given: Empty config file
        When: load_converter_config is called
        Then: Empty dictionary is returned
        """
        empty_config_path = temp_dir / "empty.json"
        with open(empty_config_path, "w") as f:
            f.write("")

        result = load_converter_config(empty_config_path)

        assert result == {}

    def test_load_converter_config_minimal_valid_json(self, temp_dir):
        """
        Test loading minimal valid JSON (empty object).

        Given: Config file with {}
        When: load_converter_config is called
        Then: Empty dictionary is returned
        """
        minimal_config_path = temp_dir / "minimal.json"
        with open(minimal_config_path, "w") as f:
            f.write("{}")

        result = load_converter_config(minimal_config_path)

        assert result == {}


"""
Test Summary
============
Total Tests: 17
- Happy Path: 6
- Edge Cases: 7
- Error Conditions: 4

Coverage Areas:
- CLI argument priority
- Environment variable handling
- Config file fallback
- Default value (tectonic)
- Engine validation (CLI, env, config)
- Case-insensitive handling
- Whitespace trimming
- Empty string CLI handling
- Config loading (valid/invalid/missing)
- Graceful error handling
- Specific error message formatting

Expected Behavior:
- These tests will FAIL (RED phase) until get_latex_engine() and
  load_converter_config() are implemented in convert.py
- Tests define the contract for the new functions
- Implementation should make all tests pass (GREEN phase)
"""
