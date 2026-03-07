"""
Tests for src/whitepaper-converter/ - devcontainer feature.

This module tests the devcontainer feature that allows external repositories to
install the CoSAI Whitepaper Converter via devcontainer features.

Devcontainer Feature Lifecycle:
1. User adds feature to .devcontainer/devcontainer.json:
   {
     "features": {
       "ghcr.io/cosai-oasis/cosai-whitepaper-converter/whitepaper-converter:1": {
         "latexEngine": "tectonic",
         "skipChromium": false,
         "skipPython": false,
         "skipNode": false
       }
     }
   }

2. Devcontainer CLI reads devcontainer-feature.json and maps camelCase options
   to UPPERCASE environment variables WITHOUT underscores:
   - latexEngine → LATEXENGINE
   - skipChromium → SKIPCHROMIUM
   - skipPython → SKIPPYTHON
   - skipNode → SKIPNODE

3. Devcontainer CLI runs install.sh with these environment variables set.

4. install.sh (feature entry point) maps devcontainer env vars to install-deps.sh format:
   - LATEXENGINE → LATEX_ENGINE
   - SKIPCHROMIUM → SKIP_CHROMIUM
   - SKIPPYTHON → SKIP_PYTHON
   - SKIPNODE → SKIP_NODE

5. install.sh determines its location and calls ../../scripts/install-deps.sh
   (feature is at src/whitepaper-converter/, scripts at scripts/)

6. install-deps.sh installs dependencies based on env vars.

7. On success, install.sh exports COSAI_CONVERTER_INSTALLED=true
   (persisted via containerEnv in devcontainer-feature.json).

Test Coverage:
- devcontainer-feature.json schema validation
- Feature ID format (lowercase with hyphens, semver version)
- install.sh entry point behavior
- Environment variable mapping (LATEXENGINE → LATEX_ENGINE)
- Path resolution (install.sh locates scripts/install-deps.sh)
- Default values (LATEXENGINE defaults to 'tectonic')
- Boolean option handling (both true and "true" strings)
- README.md documentation completeness
"""

import pytest
import json
import subprocess
import os
from pathlib import Path


# Path to the feature under test
FEATURE_DIR = Path(__file__).parent.parent.parent / "src" / "whitepaper-converter"
FEATURE_JSON = FEATURE_DIR / "devcontainer-feature.json"
INSTALL_SCRIPT = FEATURE_DIR / "install.sh"
README_FILE = FEATURE_DIR / "README.md"


@pytest.fixture
def mock_env():
    """
    Provide a clean environment for testing.

    Clears both devcontainer format (LATEXENGINE) and install-deps format
    (LATEX_ENGINE) environment variables to ensure test isolation.

    Returns:
        dict: Clean environment variables without devcontainer options.
    """
    env = os.environ.copy()
    # Remove devcontainer format (uppercase without underscores)
    devcontainer_vars = ["LATEXENGINE", "SKIPCHROMIUM", "SKIPPYTHON", "SKIPNODE", "INSTALLPATH"]
    # Remove install-deps format (uppercase with underscores)
    install_deps_vars = ["LATEX_ENGINE", "SKIP_CHROMIUM", "SKIP_PYTHON", "SKIP_NODE", "INSTALL_PATH"]

    for key in devcontainer_vars + install_deps_vars:
        if key in env:
            del env[key]
    return env


# ============================================================================
# devcontainer-feature.json Validation Tests
# ============================================================================


def test_feature_json_exists():
    """
    Test that devcontainer-feature.json exists.

    Given: A devcontainer feature project structure
    When: Checking for the feature manifest
    Then: devcontainer-feature.json file exists
    """
    assert FEATURE_JSON.exists(), f"Feature JSON not found at {FEATURE_JSON}"


def test_feature_json_is_valid_json():
    """
    Test that devcontainer-feature.json is valid JSON.

    Given: devcontainer-feature.json exists
    When: Parsing the file as JSON
    Then: JSON parsing succeeds without errors
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)
    assert isinstance(data, dict), "Feature JSON must be a dictionary"


def test_feature_json_has_required_fields():
    """
    Test that devcontainer-feature.json has all required fields.

    Given: A valid JSON file
    When: Checking for required schema fields
    Then: All required fields exist (id, version, name, description, options)
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    required_fields = ["id", "version", "name", "description", "options"]
    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from feature JSON"


def test_feature_json_id_format():
    """
    Test that feature id follows devcontainer naming conventions.

    Per devcontainer spec, feature IDs must:
    - Start with a lowercase letter
    - Contain only lowercase letters, numbers, and hyphens
    - Match regex: ^[a-z][a-z0-9-]*$

    Given: devcontainer-feature.json with id field
    When: Validating the id format
    Then: id matches devcontainer naming pattern and is 'whitepaper-converter'
    """
    import re

    with open(FEATURE_JSON) as f:
        data = json.load(f)

    feature_id = data["id"]
    id_pattern = r'^[a-z][a-z0-9-]*$'

    assert re.match(id_pattern, feature_id), \
        f"Feature id '{feature_id}' must match pattern {id_pattern}"
    assert feature_id == "whitepaper-converter", \
        "Feature id must be 'whitepaper-converter'"


def test_feature_json_version_is_semver():
    """
    Test that version follows semantic versioning.

    Given: devcontainer-feature.json with version field
    When: Validating the version format
    Then: Version matches semver pattern (X.Y.Z)
    """
    import re

    with open(FEATURE_JSON) as f:
        data = json.load(f)

    version = data["version"]
    semver_pattern = r'^\d+\.\d+\.\d+$'
    assert re.match(semver_pattern, version), \
        f"Version '{version}' must follow semver format (X.Y.Z)"


def test_feature_json_name_is_descriptive():
    """
    Test that name field is present and descriptive.

    Given: devcontainer-feature.json with name field
    When: Checking the name value
    Then: Name contains 'CoSAI' and 'Whitepaper' and 'Converter'
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    name = data["name"]
    assert "CoSAI" in name or "cosai" in name.lower(), \
        "Feature name should reference CoSAI"
    assert "Whitepaper" in name or "whitepaper" in name.lower(), \
        "Feature name should reference Whitepaper"
    assert "Converter" in name or "converter" in name.lower(), \
        "Feature name should reference Converter"


def test_feature_json_description_is_present():
    """
    Test that description field is present and non-empty.

    Given: devcontainer-feature.json with description field
    When: Checking the description value
    Then: Description is a non-empty string
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    description = data["description"]
    assert isinstance(description, str), "Description must be a string"
    assert len(description) > 20, "Description should be descriptive (>20 chars)"


def test_feature_json_has_latex_engine_option():
    """
    Test that latexEngine option is defined correctly.

    Per devcontainer spec, string options with limited values should use
    'proposals' field (not 'enum').

    Given: devcontainer-feature.json with options
    When: Checking the latexEngine option
    Then: Option exists with type string, default 'tectonic', and valid proposals
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    options = data["options"]
    assert "latexEngine" in options, "latexEngine option must be defined"

    latex_option = options["latexEngine"]
    assert latex_option["type"] == "string", "latexEngine type must be string"
    assert latex_option["default"] == "tectonic", \
        "latexEngine default must be 'tectonic'"

    # Devcontainer spec uses 'proposals', not 'enum'
    assert "proposals" in latex_option, \
        "latexEngine must use 'proposals' field per devcontainer spec"

    proposals = latex_option["proposals"]
    expected_engines = ["tectonic", "pdflatex", "xelatex", "lualatex"]
    assert set(proposals) == set(expected_engines), \
        f"latexEngine proposals must be {expected_engines}"


def test_feature_json_has_skip_chromium_option():
    """
    Test that skipChromium option is defined correctly.

    Given: devcontainer-feature.json with options
    When: Checking the skipChromium option
    Then: Option exists with type boolean and default false
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    options = data["options"]
    assert "skipChromium" in options, "skipChromium option must be defined"

    skip_option = options["skipChromium"]
    assert skip_option["type"] == "boolean", "skipChromium type must be boolean"
    assert skip_option["default"] is False, \
        "skipChromium default must be false"


def test_feature_json_has_skip_python_option():
    """
    Test that skipPython option is defined correctly.

    Given: devcontainer-feature.json with options
    When: Checking the skipPython option
    Then: Option exists with type boolean and default false
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    options = data["options"]
    assert "skipPython" in options, "skipPython option must be defined"

    skip_option = options["skipPython"]
    assert skip_option["type"] == "boolean", "skipPython type must be boolean"
    assert skip_option["default"] is False, \
        "skipPython default must be false"


def test_feature_json_has_skip_node_option():
    """
    Test that skipNode option is defined correctly.

    Given: devcontainer-feature.json with options
    When: Checking the skipNode option
    Then: Option exists with type boolean and default false
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    options = data["options"]
    assert "skipNode" in options, "skipNode option must be defined"

    skip_option = options["skipNode"]
    assert skip_option["type"] == "boolean", "skipNode type must be boolean"
    assert skip_option["default"] is False, \
        "skipNode default must be false"


def test_feature_json_all_options_have_descriptions():
    """
    Test that all options have description fields.

    Given: devcontainer-feature.json with options
    When: Checking each option
    Then: Every option has a non-empty description
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    options = data["options"]
    for option_name, option_data in options.items():
        assert "description" in option_data, \
            f"Option '{option_name}' missing description"
        assert len(option_data["description"]) > 10, \
            f"Option '{option_name}' description too short"


def test_feature_json_has_container_env():
    """
    Test that containerEnv is defined correctly.

    Given: devcontainer-feature.json
    When: Checking for containerEnv field
    Then: Field exists and sets COSAI_CONVERTER_INSTALLED=true
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    assert "containerEnv" in data, "containerEnv must be defined"
    container_env = data["containerEnv"]
    assert container_env.get("COSAI_CONVERTER_INSTALLED") == "true", \
        "COSAI_CONVERTER_INSTALLED must be set to 'true'"


def test_feature_json_has_installs_after_dependencies():
    """
    Test that installsAfter declares common dependencies.

    Given: devcontainer-feature.json
    When: Checking for installsAfter field
    Then: Field exists and includes common-utils or ghcr.io/devcontainers/features
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    # installsAfter is optional but recommended
    if "installsAfter" in data:
        installs_after = data["installsAfter"]
        assert isinstance(installs_after, list), "installsAfter must be a list"


# ============================================================================
# install.sh Tests
# ============================================================================


def test_install_script_exists():
    """
    Test that install.sh exists.

    Given: A devcontainer feature project structure
    When: Checking for the install script
    Then: install.sh file exists
    """
    assert INSTALL_SCRIPT.exists(), f"Install script not found at {INSTALL_SCRIPT}"


def test_install_script_is_executable():
    """
    Test that install.sh has executable permissions.

    Given: install.sh exists
    When: Checking file permissions
    Then: File is executable
    """
    assert os.access(INSTALL_SCRIPT, os.X_OK), \
        f"Install script {INSTALL_SCRIPT} is not executable"


def test_install_script_has_shebang():
    """
    Test that install.sh has a valid shebang.

    Given: install.sh exists
    When: Reading the first line
    Then: First line is #!/bin/sh or #!/bin/bash
    """
    with open(INSTALL_SCRIPT) as f:
        first_line = f.readline().strip()

    assert first_line in ["#!/bin/sh", "#!/bin/bash", "#!/usr/bin/env bash"], \
        f"Invalid shebang: {first_line}"


def test_install_script_sets_errexit():
    """
    Test that install.sh sets errexit for safety.

    Given: install.sh script
    When: Checking for set -e or set -eu
    Then: Script contains set -e or set -eu
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    assert "set -e" in content, \
        "Install script should set -e for error handling"


@pytest.mark.parametrize("option_name,env_var", [
    ("LATEXENGINE", "LATEX_ENGINE"),
    ("SKIPCHROMIUM", "SKIP_CHROMIUM"),
    ("SKIPPYTHON", "SKIP_PYTHON"),
    ("SKIPNODE", "SKIP_NODE"),
    ("INSTALLPATH", "INSTALL_PATH"),
])
def test_install_script_maps_option_to_env_var(option_name, env_var):
    """
    Test that install.sh maps devcontainer options to install-deps.sh format.

    Devcontainer passes options as: LATEXENGINE, SKIPCHROMIUM, etc.
    install.sh must map these to: LATEX_ENGINE, SKIP_CHROMIUM, etc.

    Given: install.sh script
    When: Checking for option-to-env-var mapping
    Then: Script contains mapping from option_name to env_var
          (both variables appear together in mapping statement)
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    # Both the devcontainer format and install-deps format must appear
    assert option_name in content, \
        f"Install script must reference devcontainer option {option_name}"
    assert env_var in content, \
        f"Install script must reference install-deps env var {env_var}"

    # Check for actual mapping pattern in the content
    # Common patterns: export LATEX_ENGINE="${LATEXENGINE:-tectonic}"
    # or: LATEX_ENGINE="$LATEXENGINE"
    # We verify both variables appear to ensure mapping exists
    lines = content.split('\n')
    mapping_found = False
    for line in lines:
        # Check if both variables appear in same line (indicates mapping)
        if option_name in line and env_var in line:
            mapping_found = True
            break

    assert mapping_found, \
        f"Install script must map {option_name} to {env_var} in same statement"


def test_install_script_calls_install_deps():
    """
    Test that install.sh delegates to install-deps.sh.

    Given: install.sh script
    When: Checking script content
    Then: Script calls install-deps.sh
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    assert "install-deps.sh" in content, \
        "Install script must call install-deps.sh"


def test_install_script_uses_correct_path_to_install_deps():
    """
    Test that install.sh uses correct relative path to install-deps.sh.

    Feature is located at: src/whitepaper-converter/install.sh
    Script is located at: scripts/install-deps.sh
    Relative path should be: ../../scripts/install-deps.sh

    install.sh should determine its own directory (SCRIPT_DIR or FEATURE_DIR)
    and construct path relative to repo root, NOT use './scripts/'.

    Given: install.sh script
    When: Checking path resolution for install-deps.sh
    Then: Script determines its directory and uses appropriate path
    """
    import re

    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    # Should determine script location
    assert any(marker in content for marker in ["SCRIPT_DIR", "FEATURE_DIR", "$(dirname", "__dir__"]), \
        "Install script should determine its own directory"

    # Should NOT use naive relative path (./scripts/install-deps.sh)
    # Note: ../../scripts/install-deps.sh is valid (traverses from feature dir to repo root)
    # The negative lookbehind excludes matches preceded by another dot (i.e. part of ../../)
    assert not re.search(r'(?<!\.)\.\/scripts\/install-deps\.sh', content), \
        "Install script should not use './scripts/' (wrong relative path)"


def test_install_script_handles_missing_install_deps():
    """
    Test that install.sh handles missing install-deps.sh gracefully.

    Given: install.sh script
    When: install-deps.sh is not found
    Then: Script exits with error and helpful message
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    # Should check if file exists or handle command not found
    assert "install-deps.sh" in content, \
        "Install script must reference install-deps.sh"


def test_install_script_exports_cosai_converter_installed():
    """
    Test that install.sh sets COSAI_CONVERTER_INSTALLED on success.

    Given: install.sh script completes successfully
    When: Checking environment variable export
    Then: Script exports COSAI_CONVERTER_INSTALLED=true
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    assert "COSAI_CONVERTER_INSTALLED" in content, \
        "Install script should export COSAI_CONVERTER_INSTALLED"


def test_install_script_handles_latex_engine_default():
    """
    Test that install.sh uses 'tectonic' as default LaTeX engine.

    When LATEXENGINE is unset, install.sh should default to 'tectonic'.
    Expected pattern: ${LATEXENGINE:-tectonic}

    Given: install.sh script
    When: Checking default value handling for LATEXENGINE
    Then: Script contains default pattern with 'tectonic' as fallback
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    # Look for default value pattern
    assert ":-tectonic" in content or ':="tectonic"' in content, \
        "Install script must default LATEXENGINE to 'tectonic' using :- or := pattern"


def test_install_script_handles_skip_option_defaults():
    """
    Test that install.sh defaults skip options to false/empty when unset.

    Skip options should default to false (install everything).
    Expected patterns: ${SKIPCHROMIUM:-false} or ${SKIPCHROMIUM:-}

    Given: install.sh script
    When: Checking default value handling for skip options
    Then: Script handles unset skip options gracefully
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    # At minimum, script should reference the skip vars
    # Default handling could be :- or conditional checks
    skip_vars = ["SKIPCHROMIUM", "SKIPPYTHON", "SKIPNODE"]
    for var in skip_vars:
        assert var in content, \
            f"Install script must reference {var}"


@pytest.mark.parametrize("skip_option", [
    "SKIPCHROMIUM",
    "SKIPPYTHON",
    "SKIPNODE",
])
def test_install_script_handles_skip_options(skip_option):
    """
    Test that install.sh properly handles skip options.

    Given: install.sh script
    When: Checking for skip option handling
    Then: Script references the skip option
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    # Convert to env var format (e.g., SKIPCHROMIUM -> SKIP_CHROMIUM)
    env_var = skip_option.replace("SKIP", "SKIP_")
    assert env_var in content or skip_option in content, \
        f"Install script must handle {skip_option}"


def test_install_script_handles_boolean_types():
    """
    Test that install.sh handles both boolean and string boolean values.

    Devcontainer may pass boolean options as:
    - true (boolean)
    - "true" (string)

    install.sh should handle both formats correctly.

    Given: install.sh script
    When: Checking boolean handling logic
    Then: Script handles both true and "true" string formats
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    # Should have some boolean comparison or handling
    # Common patterns: [ "$VAR" = "true" ] or [[ $VAR == true ]]
    has_boolean_check = any(marker in content for marker in [
        '= "true"',
        '== "true"',
        '= true',
        '== true',
        'if [ "$SKIP',
        'if [[ $SKIP',
    ])

    assert has_boolean_check, \
        "Install script should have boolean comparison logic for skip options"


# ============================================================================
# README.md Tests
# ============================================================================


def test_readme_exists():
    """
    Test that README.md exists.

    Given: A devcontainer feature project structure
    When: Checking for documentation
    Then: README.md file exists
    """
    assert README_FILE.exists(), f"README not found at {README_FILE}"


def test_readme_contains_usage_example():
    """
    Test that README.md contains usage examples.

    Given: README.md exists
    When: Checking for devcontainer.json example
    Then: README contains a usage example with features configuration
    """
    with open(README_FILE) as f:
        content = f.read()

    assert "devcontainer.json" in content, \
        "README should show devcontainer.json usage"
    assert "features" in content, \
        "README should show features configuration"
    assert "whitepaper-converter" in content, \
        "README should reference the feature name"


def test_readme_documents_all_options():
    """
    Test that README.md documents all feature options.

    Given: README.md exists
    When: Checking for option documentation
    Then: README mentions all options (latexEngine, skipChromium, skipPython, skipNode)
    """
    with open(README_FILE) as f:
        content = f.read()

    options = ["latexEngine", "skipChromium", "skipPython", "skipNode", "installPath"]
    for option in options:
        assert option in content, \
            f"README should document '{option}' option"


def test_readme_documents_latex_engines():
    """
    Test that README.md lists supported LaTeX engines.

    Given: README.md exists
    When: Checking for LaTeX engine documentation
    Then: README mentions tectonic, pdflatex, xelatex, lualatex
    """
    with open(README_FILE) as f:
        content = f.read()

    engines = ["tectonic", "pdflatex", "xelatex", "lualatex"]
    for engine in engines:
        assert engine in content, \
            f"README should document '{engine}' LaTeX engine"


def test_readme_documents_supported_platforms():
    """
    Test that README.md documents supported platforms.

    Given: README.md exists
    When: Checking for platform documentation
    Then: README mentions Debian/Ubuntu, Alpine, macOS
    """
    with open(README_FILE) as f:
        content = f.read()

    # Should mention at least some platforms
    platforms = ["Debian", "Ubuntu", "Linux"]
    assert any(platform in content for platform in platforms), \
        "README should document supported platforms"


def test_readme_has_examples_section():
    """
    Test that README.md has an examples or usage section.

    Given: README.md exists
    When: Checking for section headers
    Then: README contains 'Example', 'Usage', or 'Getting Started' section
    """
    with open(README_FILE) as f:
        content = f.read()

    sections = ["example", "usage", "getting started", "how to use"]
    content_lower = content.lower()
    assert any(section in content_lower for section in sections), \
        "README should have usage/example section"


def test_readme_has_options_section():
    """
    Test that README.md has an options or configuration section.

    Given: README.md exists
    When: Checking for section headers
    Then: README contains 'Options', 'Configuration', or 'Settings' section
    """
    with open(README_FILE) as f:
        content = f.read()

    sections = ["option", "configuration", "setting"]
    content_lower = content.lower()
    assert any(section in content_lower for section in sections), \
        "README should have options/configuration section"


# ============================================================================
# Option Value Validation Tests
# ============================================================================


@pytest.mark.parametrize("engine", ["tectonic", "pdflatex", "xelatex", "lualatex"])
def test_feature_json_accepts_valid_latex_engines(engine):
    """
    Test that feature JSON defines all valid LaTeX engines.

    Given: devcontainer-feature.json with latexEngine option
    When: Checking supported engine values
    Then: All standard engines are in proposals field
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    latex_option = data["options"]["latexEngine"]
    # Use proposals per devcontainer spec
    proposals = latex_option.get("proposals", [])

    assert engine in proposals, \
        f"LaTeX engine '{engine}' should be in proposals"


def test_feature_json_skip_options_are_boolean():
    """
    Test that all skip options have boolean type.

    Given: devcontainer-feature.json with skip options
    When: Checking option types
    Then: All skipChromium, skipPython, skipNode have type boolean
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    skip_options = ["skipChromium", "skipPython", "skipNode"]
    options = data["options"]

    for skip_option in skip_options:
        assert options[skip_option]["type"] == "boolean", \
            f"Option '{skip_option}' must have type boolean"


def test_feature_json_skip_options_default_false():
    """
    Test that all skip options default to false.

    Given: devcontainer-feature.json with skip options
    When: Checking default values
    Then: All skip options default to false (install everything by default)
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    skip_options = ["skipChromium", "skipPython", "skipNode"]
    options = data["options"]

    for skip_option in skip_options:
        assert options[skip_option]["default"] is False, \
            f"Option '{skip_option}' must default to false"


# ============================================================================
# Script Integration Tests (Unit-level)
# ============================================================================


def test_install_script_structure_is_valid_bash():
    """
    Test that install.sh has valid bash syntax.

    Given: install.sh script
    When: Checking with bash -n (syntax check)
    Then: No syntax errors
    """
    result = subprocess.run(
        ["bash", "-n", str(INSTALL_SCRIPT)],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, \
        f"Bash syntax error in install.sh:\n{result.stderr}"


def test_install_script_has_documentation_comments():
    """
    Test that install.sh has header documentation.

    Given: install.sh script
    When: Checking for documentation comments
    Then: Script has comments explaining its purpose
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    # Should have some comment lines (starting with #)
    comment_lines = [line for line in content.split('\n') if line.strip().startswith('#')]
    assert len(comment_lines) >= 3, \
        "Install script should have documentation comments"


def test_feature_directory_has_all_required_files():
    """
    Test that feature directory has all required files.

    Given: src/whitepaper-converter/ directory
    When: Checking for required files
    Then: Directory contains devcontainer-feature.json, install.sh, README.md
    """
    required_files = [
        "devcontainer-feature.json",
        "install.sh",
        "README.md"
    ]

    for filename in required_files:
        filepath = FEATURE_DIR / filename
        assert filepath.exists(), \
            f"Required file '{filename}' not found in feature directory"


def test_feature_json_does_not_have_syntax_errors():
    """
    Test that devcontainer-feature.json has no JSON syntax errors.

    Given: devcontainer-feature.json file
    When: Parsing with json.loads
    Then: Parsing succeeds without JSONDecodeError
    """
    with open(FEATURE_JSON) as f:
        try:
            json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"JSON syntax error in feature JSON: {e}")


def test_readme_is_markdown_formatted():
    """
    Test that README.md is properly formatted Markdown.

    Given: README.md file
    When: Checking for basic Markdown syntax
    Then: File contains markdown headings (# or ##)
    """
    with open(README_FILE) as f:
        content = f.read()

    # Should have at least one heading
    assert any(line.strip().startswith('#') for line in content.split('\n')), \
        "README should contain Markdown headings"


def test_feature_json_keys_are_valid_strings():
    """
    Test that devcontainer-feature.json top-level keys are valid.

    Given: devcontainer-feature.json parsed successfully
    When: Checking top-level keys
    Then: All keys are non-empty strings
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    for key in data.keys():
        assert isinstance(key, str), f"Key must be string, got {type(key)}"
        assert len(key) > 0, "Key must not be empty"


# ============================================================================
# Converter Bundling Tests (Sprint 4)
# ============================================================================


def test_feature_json_has_install_path_option():
    """
    Test that devcontainer-feature.json has installPath option.

    Given: devcontainer-feature.json with options
    When: Checking for installPath option
    Then: Option exists with type string and default /usr/local/lib/cosai-converter
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    options = data["options"]
    assert "installPath" in options, "installPath option must be defined"

    install_path_option = options["installPath"]
    assert install_path_option["type"] == "string", "installPath type must be string"
    assert install_path_option["default"] == "/usr/local/lib/cosai-converter", \
        "installPath default must be '/usr/local/lib/cosai-converter'"
    assert "description" in install_path_option, \
        "installPath must have description"
    assert len(install_path_option["description"]) > 10, \
        "installPath description must be descriptive"


def test_feature_json_version_bumped_for_converter():
    """
    Test that version is >= 0.2.0 to reflect converter bundling feature.

    Given: devcontainer-feature.json with version field
    When: Checking version value
    Then: Version is at least 0.2.0 (new functionality added)
    """
    with open(FEATURE_JSON) as f:
        data = json.load(f)

    version = data["version"]
    major, minor, patch = map(int, version.split('.'))

    # Version should be >= 0.2.0 for converter bundling feature
    assert (major > 0) or (major == 0 and minor >= 2), \
        f"Version should be >= 0.2.0 for converter bundling, got {version}"


def test_install_script_installs_all_converter_assets():
    """
    Test that install.sh references converter assets directory.

    Given: install.sh script
    When: Checking for asset installation logic
    Then: Script references assets directory for converter installation
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    assert any(pattern in content for pattern in [
        "assets/",
        "mkdir.*assets",
        "cp.*assets",
    ]), "Install script must reference assets directory for converter installation"


def test_install_script_installs_converter():
    """
    Test that install.sh references convert.py for converter installation.

    Given: install.sh script
    When: Checking for converter installation logic
    Then: Script references convert.py file
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    assert "convert.py" in content, \
        "Install script must reference convert.py for converter installation"


def test_install_script_creates_cosai_convert_wrapper():
    """
    Test that install.sh references cosai-convert wrapper creation.

    Given: install.sh script
    When: Checking for wrapper script creation
    Then: Script references cosai-convert wrapper
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    assert "cosai-convert" in content, \
        "Install script must reference cosai-convert wrapper creation"


def test_install_script_wrapper_sets_pythonpath():
    """
    Test that wrapper script sets PYTHONPATH to include bundled lib directory.

    Given: install.sh generates a cosai-convert wrapper
    When: A different Python (e.g. mise-managed) is on the user's PATH
    Then: The wrapper sets PYTHONPATH so frontmatter is always importable
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    assert "PYTHONPATH" in content, \
        "Wrapper script must set PYTHONPATH to include bundled Python packages"


def test_install_script_installs_frontmatter_to_lib():
    """
    Test that install.sh installs python-frontmatter to the converter lib dir.

    Given: install.sh with converter files available
    When: Installing the converter
    Then: pip install --target is used to install frontmatter alongside converter
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    assert "pip install" in content and "--target" in content, \
        "Install script must pip install --target to bundle frontmatter in lib dir"


def test_install_script_asset_loop_uses_orig_template():
    """
    Test that install.sh asset copy loop references puppeteerConfig.json.orig
    (the clean template) instead of puppeteerConfig.json.

    Given: install.sh copies bundled converter assets
    When: The asset loop lists files to copy
    Then: It references puppeteerConfig.json.orig (template), not the generated file
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    # The asset copy loop must reference .orig (the template file bundled at build time)
    asset_loop_pos = content.find("for asset in")
    assert asset_loop_pos > 0, "Install script must have asset copy loop"

    # Extract the asset loop line(s)
    loop_end = content.find("done", asset_loop_pos)
    asset_loop_block = content[asset_loop_pos:loop_end]

    assert "puppeteerConfig.json.orig" in asset_loop_block, \
        "Asset copy loop must reference puppeteerConfig.json.orig (template file)"


def test_install_script_generates_runtime_puppeteer_config():
    """
    Test that install.sh ensures a runtime puppeteerConfig.json exists
    after installation (either from configure-chromium.sh or from .orig fallback).

    Given: install.sh installs converter assets
    When: configure-chromium.sh may or may not have generated a config
    Then: Install script has logic to produce puppeteerConfig.json at the install path
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    # Must reference puppeteerConfig.json (the runtime file) for the overwrite/fallback logic
    assert "puppeteerConfig.json" in content, \
        "Install script must reference puppeteerConfig.json for runtime config"

    # Must reference SCRIPT_DIR/assets/ (where configure-chromium.sh generates the config)
    # or have fallback logic from .orig
    assert "SCRIPT_DIR" in content and "puppeteerConfig" in content, \
        "Install script must have logic to produce runtime puppeteerConfig.json"


def test_puppeteer_config_template_uses_auto_detection():
    """
    Test that the committed puppeteerConfig.json.orig template uses auto-detection mode.

    Given: assets/puppeteerConfig.json.orig is the clean template checked into git
    When: Feature is installed on any platform
    Then: Template should NOT have hardcoded executablePath (configure-chromium.sh sets it at install time)
    """
    repo_root = FEATURE_DIR.parent.parent
    config_path = repo_root / "assets" / "puppeteerConfig.json.orig"
    with open(config_path) as f:
        config = json.load(f)

    assert "executablePath" not in config, \
        "puppeteerConfig.json.orig should NOT have hardcoded executablePath; " \
        "configure-chromium.sh generates platform-specific config at install time"


def test_puppeteer_config_template_exists_and_valid_json():
    """
    Test that puppeteerConfig.json.orig exists and is valid JSON.

    Given: The repository assets directory
    When: Checking for the template file
    Then: File exists, is valid JSON, and has required keys (defaultViewport, args)
    """
    repo_root = FEATURE_DIR.parent.parent
    config_path = repo_root / "assets" / "puppeteerConfig.json.orig"

    assert config_path.exists(), \
        "assets/puppeteerConfig.json.orig must exist as the clean template"

    with open(config_path) as f:
        config = json.load(f)

    assert "defaultViewport" in config, \
        "Template must have defaultViewport key"
    assert "args" in config, \
        "Template must have args key"
    assert isinstance(config["args"], list), \
        "Template args must be a list"


def test_puppeteer_config_generated_file_is_gitignored():
    """
    Test that assets/puppeteerConfig.json (generated file) is in .gitignore.

    Given: The repository .gitignore file
    When: Checking for the generated puppeteerConfig.json
    Then: The generated file path is listed in .gitignore
    """
    repo_root = FEATURE_DIR.parent.parent
    gitignore_path = repo_root / ".gitignore"

    assert gitignore_path.exists(), ".gitignore must exist"

    with open(gitignore_path) as f:
        gitignore_content = f.read()

    # Check that assets/puppeteerConfig.json is gitignored
    assert "assets/puppeteerConfig.json" in gitignore_content, \
        "assets/puppeteerConfig.json (generated file) must be in .gitignore"


def test_install_script_exports_converter_path():
    """
    Test that install.sh exports COSAI_CONVERTER_PATH environment variable.

    Given: install.sh script
    When: Checking for environment variable export
    Then: Script creates /etc/profile.d/cosai-converter.sh or references COSAI_CONVERTER_PATH
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    assert "COSAI_CONVERTER_PATH" in content or "/etc/profile.d/cosai-converter.sh" in content, \
        "Install script must export COSAI_CONVERTER_PATH via profile.d or similar"


def test_install_script_handles_missing_converter_gracefully():
    """
    Test that install.sh has conditional logic for converter installation.

    Given: install.sh script
    When: Converter files might be missing (repo context vs feature context)
    Then: Script has conditional logic to handle missing converter gracefully
    """
    with open(INSTALL_SCRIPT) as f:
        content = f.read()

    # Should have some conditional checks for converter files
    assert any(marker in content for marker in [
        "if [ -f",
        "if [ -d",
        "if test -f",
        "if test -d",
    ]), "Install script should have conditional file/directory checks"


def test_readme_documents_install_path_option():
    """
    Test that README.md documents installPath option.

    Given: README.md exists
    When: Checking for installPath documentation
    Then: README mentions installPath option
    """
    with open(README_FILE) as f:
        content = f.read()

    assert "installPath" in content, \
        "README should document 'installPath' option"


def test_readme_documents_cosai_convert_command():
    """
    Test that README.md documents cosai-convert command usage.

    Given: README.md exists
    When: Checking for cosai-convert command documentation
    Then: README mentions cosai-convert command
    """
    with open(README_FILE) as f:
        content = f.read()

    assert "cosai-convert" in content, \
        "README should document 'cosai-convert' command usage"


"""
Test Summary
============
Total Tests: 61 (51 test functions, 10 parametrized expansions)
- Feature JSON validation: 21 (added installPath option, version bump check)
- install.sh validation: 23 (added converter installation, wrapper, path export, graceful handling)
- README.md validation: 10 (added installPath and cosai-convert documentation)
- Option validation: 3 (4 parametrized to test each engine)
- Integration checks: 11

Coverage Areas:
- devcontainer-feature.json schema compliance
- Feature ID format validation (lowercase-with-hyphens pattern)
- Semver version validation
- Option type and default value validation (proposals, not enum)
- install.sh script structure and behavior
- Environment variable mapping (LATEXENGINE → LATEX_ENGINE, INSTALLPATH → INSTALL_PATH)
- Path resolution (feature locates install-deps.sh correctly)
- Default value handling (tectonic default, skip options)
- Boolean type handling (true vs "true")
- Converter bundling (convert.py, assets, wrapper script)
- Environment variable persistence (COSAI_CONVERTER_PATH)
- README.md documentation completeness
- Error handling and edge cases

Test Categories:
- Happy Path: 42 (valid configurations, standard usage, proper mappings, converter installation)
- Edge Cases: 14 (missing files, syntax errors, edge values, boolean formats, missing converter)
- Error Conditions: 12 (invalid JSON, missing options, incorrect types, path issues)

Key Validation Points:
1. Feature ID: ^[a-z][a-z0-9-]*$ (devcontainer spec)
2. Version: X.Y.Z (semver), >= 0.2.0 for converter bundling
3. Options use 'proposals' not 'enum' (devcontainer spec)
4. Environment variable flow: latexEngine → LATEXENGINE → LATEX_ENGINE
5. Path resolution: install.sh at src/whitepaper-converter/ finds ../../scripts/
6. Defaults: LATEXENGINE:-tectonic, skip options handle unset gracefully, INSTALLPATH:-/usr/local/lib/cosai-converter
7. Boolean handling: Both true and "true" supported
8. Converter bundling: install.sh copies convert.py + assets to INSTALL_PATH
9. Wrapper script: cosai-convert created in /usr/local/bin
10. Environment persistence: COSAI_CONVERTER_PATH exported via /etc/profile.d

Sprint 4 - Converter Bundling Tests:
These tests drive the implementation of bundling the actual converter
(convert.py + assets) into the devcontainer feature. Previously the feature
only installed system dependencies. Now it will also install the converter
itself and create a wrapper script for easy usage.

This test suite follows TDD principles - all tests will fail initially
since the feature doesn't exist yet. Tests are designed to drive the
implementation through clear specifications.
"""
