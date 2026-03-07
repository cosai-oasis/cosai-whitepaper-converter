"""
Tests for scripts/verify-deps.sh - dependency verification script.

This module tests the dependency verification script that validates all required
project dependencies are installed with correct versions:
- Python 3.12+
- Node.js 18+
- Pandoc 3.9+
- LaTeX engine (tectonic/pdflatex/xelatex/lualatex based on config)
- Chromium (via configure-chromium.sh)
- python-frontmatter Python package
- rsvg-convert (from librsvg2-bin, used by Pandoc for SVG→PDF conversion)
- mermaid-cli (via npx @mermaid-js/mermaid-cli)

The script outputs status messages with [✓] for success and [✗] for failures,
and returns exit code 0 for success or 1 for any failures.
"""

import pytest
import subprocess
import os
import json
from pathlib import Path


# Path to the script under test
SCRIPT_PATH = Path(__file__).parent.parent.parent / "scripts" / "verify-deps.sh"


@pytest.fixture
def mock_env():
    """
    Provide a clean environment for testing.

    Returns:
        dict: Clean environment variables without LATEX_ENGINE.
    """
    env = os.environ.copy()
    if "LATEX_ENGINE" in env:
        del env["LATEX_ENGINE"]
    return env


@pytest.fixture
def mock_bin_dir(tmp_path):
    """
    Create a temporary bin directory for mock executables.

    Args:
        tmp_path: pytest temporary directory fixture.

    Returns:
        Path: Path to temporary bin directory.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    return bin_dir


@pytest.fixture
def mock_config_dir(tmp_path):
    """
    Create a temporary directory for config files.

    Args:
        tmp_path: pytest temporary directory fixture.

    Returns:
        Path: Path to temporary config directory.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


def create_mock_command(
    bin_dir: Path, command: str, version_output: str, exit_code: int = 0
):
    """
    Create a mock executable that outputs a specific version string.

    Args:
        bin_dir: Directory to create executable in.
        command: Name of the command to mock.
        version_output: Output to return when called with --version or -v.
        exit_code: Exit code for the mock command.

    Returns:
        Path: Path to created mock executable.
    """
    mock_path = bin_dir / command
    script_content = f"""#!/bin/bash
echo "{version_output}"
exit {exit_code}
"""
    mock_path.write_text(script_content)
    mock_path.chmod(0o755)
    return mock_path


def run_verify_deps(env: dict = None, cwd: Path = None) -> subprocess.CompletedProcess:
    """
    Run the verify-deps.sh script and capture output.

    Args:
        env: Environment variables to use.
        cwd: Working directory for script execution.

    Returns:
        CompletedProcess: Result containing stdout, stderr, and returncode.
    """
    result = subprocess.run(
        [str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd or Path.cwd(),
    )
    return result


class TestScriptExistence:
    """Test that the script exists and is executable."""

    def test_verify_deps_script_exists(self):
        """
        Test that verify-deps.sh exists in scripts directory.

        Given: Project structure with scripts/ directory
        When: Checking for verify-deps.sh
        Then: Script file exists
        """
        assert SCRIPT_PATH.exists(), f"Script not found at {SCRIPT_PATH}"

    def test_verify_deps_script_is_executable(self):
        """
        Test that verify-deps.sh has executable permissions.

        Given: verify-deps.sh exists
        When: Checking file permissions
        Then: Script is executable
        """
        assert os.access(SCRIPT_PATH, os.X_OK), f"Script not executable: {SCRIPT_PATH}"


class TestMissingDependencies:
    """Test detection of missing dependencies."""

    def test_detects_missing_python(self, mock_env, mock_bin_dir):
        """
        Test that script detects missing Python installation.

        Given: PATH with no python3 executable
        When: verify-deps.sh is executed
        Then: Output shows [✗] Python not found
              Exit code is 1
        """
        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert result.returncode == 1
        assert "[✗]" in result.stdout
        assert "Python" in result.stdout or "python" in result.stdout.lower()
        assert (
            "not found" in result.stdout.lower() or "missing" in result.stdout.lower()
        )

    def test_detects_missing_nodejs(self, mock_env, mock_bin_dir):
        """
        Test that script detects missing Node.js installation.

        Given: PATH with no node executable
        When: verify-deps.sh is executed
        Then: Output shows [✗] Node.js not found
              Exit code is 1
        """
        # Create Python but not Node
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert result.returncode == 1
        assert "[✗]" in result.stdout
        assert "Node" in result.stdout or "node" in result.stdout.lower()

    def test_detects_missing_pandoc(self, mock_env, mock_bin_dir):
        """
        Test that script detects missing Pandoc installation.

        Given: PATH with no pandoc executable
        When: verify-deps.sh is executed
        Then: Output shows [✗] Pandoc not found
              Exit code is 1
        """
        # Create Python and Node but not Pandoc
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert result.returncode == 1
        assert "[✗]" in result.stdout
        assert "Pandoc" in result.stdout or "pandoc" in result.stdout.lower()

    def test_detects_missing_latex_engine(self, mock_env, mock_bin_dir):
        """
        Test that script detects missing LaTeX engine.

        Given: PATH with no tectonic executable (default engine)
        When: verify-deps.sh is executed
        Then: Output shows [✗] tectonic not found
              Exit code is 1
        """
        # Create all dependencies except LaTeX engine
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert result.returncode == 1
        assert "[✗]" in result.stdout
        assert "tectonic" in result.stdout.lower()

    def test_returns_exit_code_1_when_any_dependency_missing(
        self, mock_env, mock_bin_dir
    ):
        """
        Test that script returns exit code 1 when any dependency is missing.

        Given: One or more dependencies missing
        When: verify-deps.sh is executed
        Then: Exit code is 1
        """
        # Empty PATH - all dependencies missing
        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert result.returncode == 1


class TestVersionValidation:
    """Test validation of dependency versions."""

    def test_python_version_312_passes(self, mock_env, mock_bin_dir):
        """
        Test that Python 3.12.x passes version validation.

        Given: Python 3.12.0 installed
        When: verify-deps.sh is executed
        Then: Python check shows [✓]
              Output shows "requires 3.12+"
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.12.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        # Mock configure-chromium.sh check
        scripts_dir = mock_bin_dir.parent / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        configure_script = scripts_dir / "configure-chromium.sh"
        configure_script.write_text("#!/bin/bash\nexit 0\n")
        configure_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env, cwd=mock_bin_dir.parent)

        # Should pass for Python
        assert "Python 3.12" in result.stdout
        assert "requires 3.12+" in result.stdout

    def test_python_version_314_passes(self, mock_env, mock_bin_dir):
        """
        Test that Python 3.14.x passes version validation.

        Given: Python 3.14.0 installed
        When: verify-deps.sh is executed
        Then: Python check shows [✓]
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert "Python 3.14" in result.stdout

    def test_python_version_311_fails(self, mock_env, mock_bin_dir):
        """
        Test that Python 3.11.x fails version validation.

        Given: Python 3.11.0 installed (below minimum 3.12)
        When: verify-deps.sh is executed
        Then: Output shows [✗] for Python
              Output indicates version too low
              Exit code is 1
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.11.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert result.returncode == 1
        assert "[✗]" in result.stdout
        assert "3.11" in result.stdout
        assert (
            "version too low" in result.stdout.lower()
            or "requires 3.12+" in result.stdout
        )

    def test_python_version_2x_fails(self, mock_env, mock_bin_dir):
        """
        Test that Python 2.x fails version validation.

        Given: Python 2.7.x installed
        When: verify-deps.sh is executed
        Then: Output shows [✗] for Python
              Exit code is 1
        """
        create_mock_command(mock_bin_dir, "python3", "Python 2.7.18", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert result.returncode == 1
        assert "[✗]" in result.stdout
        assert "2.7" in result.stdout

    def test_nodejs_version_18_passes(self, mock_env, mock_bin_dir):
        """
        Test that Node.js 18.x passes version validation.

        Given: Node.js v18.0.0 installed
        When: verify-deps.sh is executed
        Then: Node.js check shows [✓]
              Output shows "requires 18+"
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v18.0.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert "Node" in result.stdout and "18" in result.stdout
        assert "requires 18+" in result.stdout

    def test_nodejs_version_20_passes(self, mock_env, mock_bin_dir):
        """
        Test that Node.js 20.x passes version validation.

        Given: Node.js v20.10.0 installed
        When: verify-deps.sh is executed
        Then: Node.js check shows [✓]
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert "Node" in result.stdout and "20" in result.stdout

    def test_nodejs_version_16_fails(self, mock_env, mock_bin_dir):
        """
        Test that Node.js 16.x fails version validation.

        Given: Node.js v16.0.0 installed (below minimum 18)
        When: verify-deps.sh is executed
        Then: Output shows [✗] for Node.js
              Output indicates version too low
              Exit code is 1
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v16.0.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert result.returncode == 1
        assert "[✗]" in result.stdout
        assert "16" in result.stdout
        assert (
            "version too low" in result.stdout.lower()
            or "requires 18+" in result.stdout
        )

    def test_pandoc_version_39_passes(self, mock_env, mock_bin_dir):
        """
        Test that Pandoc 3.9 passes version validation.

        Given: Pandoc 3.9 installed (minimum required version)
        When: verify-deps.sh is executed
        Then: Pandoc check shows [✓]
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert "[✓]" in result.stdout
        assert "Pandoc 3.9" in result.stdout
        assert "requires 3.9+" in result.stdout

    def test_pandoc_version_310_passes(self, mock_env, mock_bin_dir):
        """
        Test that Pandoc 3.10 passes version validation.

        Given: Pandoc 3.10 installed (above 3.9 minimum)
        When: verify-deps.sh is executed
        Then: Pandoc check shows [✓]
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.10", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert "[✓]" in result.stdout
        assert "Pandoc 3.10" in result.stdout

    def test_pandoc_version_3821_fails(self, mock_env, mock_bin_dir):
        """
        Test that Pandoc 3.8.2.1 fails against 3.9 minimum.

        Given: Pandoc 3.8.2.1 installed (below 3.9 minimum)
        When: verify-deps.sh is executed
        Then: Pandoc check shows [✗] version too low
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.8.2.1", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert "[✗]" in result.stdout
        assert "version too low" in result.stdout.lower()

    def test_pandoc_version_383_fails(self, mock_env, mock_bin_dir):
        """
        Test that Pandoc 3.8.3 fails against 3.9 minimum.

        Given: Pandoc 3.8.3 installed (below 3.9 minimum)
        When: verify-deps.sh is executed
        Then: Pandoc check shows [✗] version too low
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.8.3", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert "[✗]" in result.stdout
        assert "version too low" in result.stdout.lower()

    def test_pandoc_version_30_fails(self, mock_env, mock_bin_dir):
        """
        Test that Pandoc 3.0.0 fails version validation.

        Given: Pandoc 3.0.0 installed (below 3.9 minimum)
        When: verify-deps.sh is executed
        Then: Pandoc check shows [✗] version too low
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.0.0", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert "[✗]" in result.stdout
        assert "Pandoc 3.0" in result.stdout
        assert "version too low" in result.stdout.lower()

    def test_pandoc_version_311_fails(self, mock_env, mock_bin_dir):
        """
        Test that Pandoc 3.1.11 fails version validation.

        Given: Pandoc 3.1.11 installed (below 3.9 minimum)
        When: verify-deps.sh is executed
        Then: Pandoc check shows [✗] version too low
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.1.11", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert "[✗]" in result.stdout
        assert "Pandoc 3.1.11" in result.stdout
        assert "version too low" in result.stdout.lower()

    def test_pandoc_version_2x_fails(self, mock_env, mock_bin_dir):
        """
        Test that Pandoc 2.x fails version validation.

        Given: Pandoc 2.19.2 installed (below 3.9 minimum)
        When: verify-deps.sh is executed
        Then: Output shows [✗] for Pandoc
              Output indicates version too low
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 2.19.2", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert result.returncode == 1
        assert "[✗]" in result.stdout
        assert "2.19" in result.stdout
        assert "version too low" in result.stdout.lower()


class TestOutputFormat:
    """Test output formatting of dependency checks."""

    def test_success_marker_for_valid_dependencies(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that [✓] marker appears for all valid dependencies.

        Given: All dependencies installed with valid versions
        When: verify-deps.sh is executed
        Then: Output contains [✓] markers
              No [✗] markers present
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        # Mock python-frontmatter check
        create_mock_command(mock_bin_dir, "pip3", "frontmatter (1.1.0)", 0)

        # Mock rsvg-convert
        create_mock_command(
            mock_bin_dir, "rsvg-convert", "rsvg-convert version 2.54.5", 0
        )

        # Mock npx for mermaid-cli
        npx_script = mock_bin_dir / "npx"
        npx_script.write_text("""#!/bin/bash
echo "0.10.3"
exit 0
""")
        npx_script.chmod(0o755)

        # Mock chromium check
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        configure_script = scripts_dir / "configure-chromium.sh"
        configure_script.write_text("#!/bin/bash\nexit 0\n")
        configure_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env, cwd=tmp_path)

        # Count success markers (should be at least 8: Python, Node, Pandoc, LaTeX, package, rsvg, mermaid, chromium)
        success_count = result.stdout.count("[✓]")
        assert success_count >= 8, (
            f"Expected at least 8 success markers, got {success_count}"
        )

        # No failure markers
        assert "[✗]" not in result.stdout

    def test_failure_marker_for_invalid_dependencies(self, mock_env, mock_bin_dir):
        """
        Test that [✗] marker appears for invalid or missing dependencies.

        Given: One or more dependencies missing or invalid versions
        When: verify-deps.sh is executed
        Then: Output contains [✗] markers for failed checks
        """
        # Only create Python with old version
        create_mock_command(mock_bin_dir, "python3", "Python 3.11.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        # Should have failure markers
        assert "[✗]" in result.stdout
        failure_count = result.stdout.count("[✗]")
        assert failure_count >= 1, "Expected at least one failure marker"

    def test_version_numbers_appear_in_output(self, mock_env, mock_bin_dir):
        """
        Test that detected version numbers appear in output.

        Given: Dependencies with specific versions installed
        When: verify-deps.sh is executed
        Then: Output contains the detected version numbers
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        # Check for version numbers in output
        assert "3.14" in result.stdout, "Python version should appear"
        assert "20.10" in result.stdout, "Node.js version should appear"
        assert "3.9" in result.stdout, "Pandoc version should appear"
        assert "0.15.0" in result.stdout, "Tectonic version should appear"

    def test_requirement_strings_appear_in_output(self, mock_env, mock_bin_dir):
        """
        Test that requirement strings appear in output.

        Given: Dependencies being validated
        When: verify-deps.sh is executed
        Then: Output contains requirement indicators (e.g., "requires 3.12+")
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        # Check for requirement strings
        assert "requires 3.12+" in result.stdout, "Python requirement should appear"
        assert "requires 18+" in result.stdout, "Node.js requirement should appear"
        assert "requires 3.9+" in result.stdout, "Pandoc requirement should appear"


class TestExitCodes:
    """Test exit code behavior."""

    def test_exit_code_0_when_all_pass(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script exits with 0 when all dependencies are valid.

        Given: All dependencies installed with valid versions
        When: verify-deps.sh is executed
        Then: Exit code is 0
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        # Mock python-frontmatter check
        create_mock_command(mock_bin_dir, "pip3", "frontmatter (1.1.0)", 0)

        # Mock rsvg-convert
        create_mock_command(
            mock_bin_dir, "rsvg-convert", "rsvg-convert version 2.54.5", 0
        )

        # Mock npx for mermaid-cli
        npx_script = mock_bin_dir / "npx"
        npx_script.write_text("""#!/bin/bash
echo "0.10.3"
exit 0
""")
        npx_script.chmod(0o755)

        # Mock configure-chromium.sh --check to return success
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        configure_script = scripts_dir / "configure-chromium.sh"
        configure_script.write_text("#!/bin/bash\nexit 0\n")
        configure_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env, cwd=tmp_path)

        # When all dependencies are valid, should return 0
        # Note: This will fail in RED phase until script is implemented
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

    def test_exit_code_1_when_any_fail(self, mock_env, mock_bin_dir):
        """
        Test that script exits with 1 when any dependency fails.

        Given: One or more dependencies invalid or missing
        When: verify-deps.sh is executed
        Then: Exit code is 1
        """
        # Create valid Python but missing Node.js
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"


class TestLatexEngineDetection:
    """Test LaTeX engine detection based on configuration."""

    def test_detects_tectonic_by_default(self, mock_env, mock_bin_dir):
        """
        Test that script checks for tectonic when no config specified.

        Given: No LATEX_ENGINE env var, no converter_config.json
        When: verify-deps.sh is executed
        Then: Output checks for tectonic (default engine)
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert "tectonic" in result.stdout.lower()

    def test_detects_engine_from_env_var(self, mock_env, mock_bin_dir):
        """
        Test that script checks for engine specified in LATEX_ENGINE env var.

        Given: LATEX_ENGINE=pdflatex
        When: verify-deps.sh is executed
        Then: Output checks for pdflatex instead of tectonic
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(
            mock_bin_dir, "pdflatex", "pdfTeX 3.141592653-2.6-1.40.24", 0
        )

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["LATEX_ENGINE"] = "pdflatex"
        result = run_verify_deps(env=mock_env)

        assert "pdflatex" in result.stdout.lower()

    def test_detects_engine_from_config_file(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script checks for engine specified in converter_config.json.

        Given: converter_config.json with latex_engine="xelatex"
        When: verify-deps.sh is executed from project root
        Then: Output checks for xelatex
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(
            mock_bin_dir, "xelatex", "XeTeX 3.141592653-2.6-0.999995", 0
        )

        # Create converter_config.json
        config_file = tmp_path / "converter_config.json"
        config = {"latex_engine": "xelatex"}
        with open(config_file, "w") as f:
            json.dump(config, f)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env, cwd=tmp_path)

        assert "xelatex" in result.stdout.lower()

    def test_env_var_takes_precedence_over_config_file(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that LATEX_ENGINE env var takes precedence over config file.

        Given: LATEX_ENGINE=lualatex and converter_config.json with xelatex
        When: verify-deps.sh is executed
        Then: Output checks for lualatex (from env var)
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "lualatex", "LuaTeX, Version 1.16.0", 0)

        # Create converter_config.json with different engine
        config_file = tmp_path / "converter_config.json"
        config = {"latex_engine": "xelatex"}
        with open(config_file, "w") as f:
            json.dump(config, f)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["LATEX_ENGINE"] = "lualatex"
        result = run_verify_deps(env=mock_env, cwd=tmp_path)

        assert "lualatex" in result.stdout.lower()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_malformed_version_strings_gracefully(self, mock_env, mock_bin_dir):
        """
        Test that script handles malformed version strings without crashing.

        Given: Command returns unexpected version format
        When: verify-deps.sh is executed
        Then: Script completes without error
              Output indicates issue with version detection
        """
        # Create commands with unusual version output
        create_mock_command(mock_bin_dir, "python3", "Python version unknown", 0)
        create_mock_command(mock_bin_dir, "node", "node-development-build", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        # Script should complete (not crash)
        assert result.returncode in [0, 1], "Script should not crash"

        # Output should exist
        assert len(result.stdout) > 0, "Script should produce output"

    def test_handles_command_execution_failure(self, mock_env, mock_bin_dir):
        """
        Test that script handles commands that fail to execute.

        Given: Command exists but returns non-zero exit code
        When: verify-deps.sh is executed
        Then: Script handles the error gracefully
        """
        # Create command that exits with error
        create_mock_command(
            mock_bin_dir, "python3", "Error: cannot determine version", 1
        )

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        # Script should not crash
        assert result.returncode in [0, 1]
        assert len(result.stdout) > 0

    def test_runs_successfully_in_ci_environment(self, mock_env, mock_bin_dir):
        """
        Test that script runs in CI-like environment (non-interactive).

        Given: Non-interactive shell environment
        When: verify-deps.sh is executed
        Then: Script completes successfully
              No interactive prompts
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        # Simulate CI environment
        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["CI"] = "true"
        mock_env["DEBIAN_FRONTEND"] = "noninteractive"

        result = run_verify_deps(env=mock_env)

        # Should complete without hanging
        assert result.returncode in [0, 1]
        assert len(result.stdout) > 0

    def test_handles_missing_converter_config_file(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that script handles missing converter_config.json gracefully.

        Given: No converter_config.json file exists
        When: verify-deps.sh is executed
        Then: Script defaults to tectonic
              Script completes without error
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        # Ensure no config file exists
        config_file = tmp_path / "converter_config.json"
        if config_file.exists():
            config_file.unlink()

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env, cwd=tmp_path)

        # Should default to tectonic
        assert "tectonic" in result.stdout.lower()


class TestChromiumConfiguration:
    """Test Chromium/configure-chromium.sh verification."""

    def test_checks_chromium_configured(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script verifies Chromium configuration.

        Given: configure-chromium.sh exists and passes
        When: verify-deps.sh is executed
        Then: Output shows [✓] Chromium configured
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        # Create mock configure-chromium.sh that succeeds
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        configure_script = scripts_dir / "configure-chromium.sh"
        configure_script.write_text("#!/bin/bash\nexit 0\n")
        configure_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env, cwd=tmp_path)

        assert "Chromium" in result.stdout or "chromium" in result.stdout.lower()

    def test_detects_chromium_not_configured(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script detects when Chromium is not configured.

        Given: configure-chromium.sh fails or doesn't exist
        When: verify-deps.sh is executed
        Then: Output shows [✗] Chromium not configured
              Exit code is 1
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        # Create mock configure-chromium.sh that fails
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        configure_script = scripts_dir / "configure-chromium.sh"
        configure_script.write_text("#!/bin/bash\nexit 1\n")
        configure_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env, cwd=tmp_path)

        assert result.returncode == 1
        assert "[✗]" in result.stdout


class TestPythonPackageVerification:
    """Test verification of python-frontmatter package."""

    def test_checks_python_frontmatter_installed(self, mock_env, mock_bin_dir):
        """
        Test that script verifies python-frontmatter package is installed.

        Given: python-frontmatter package installed
        When: verify-deps.sh is executed
        Then: Output shows [✓] python-frontmatter
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        # Mock pip show or python -m pip show
        pip_output = """Name: python-frontmatter
Version: 1.1.0
Summary: Parse and manage posts with YAML frontmatter
"""
        create_mock_command(mock_bin_dir, "pip3", pip_output, 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert "frontmatter" in result.stdout.lower()

    def test_detects_python_frontmatter_missing(self, mock_env, mock_bin_dir):
        """
        Test that script detects when python-frontmatter is not installed.

        Given: python-frontmatter package not installed
        When: verify-deps.sh is executed
        Then: Output shows [✗] python-frontmatter not found
              Exit code is 1
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        # Mock pip that returns error for missing package
        create_mock_command(
            mock_bin_dir, "pip3", "Package not found: python-frontmatter", 1
        )

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert result.returncode == 1
        assert "[✗]" in result.stdout


class TestRsvgConvertVerification:
    """Test verification of rsvg-convert (from librsvg2-bin)."""

    def test_checks_rsvg_convert_installed(self, mock_env, mock_bin_dir):
        """
        Test that script verifies rsvg-convert is installed.

        Given: rsvg-convert installed (from librsvg2-bin)
        When: verify-deps.sh is executed
        Then: Output shows [✓] rsvg-convert
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)
        create_mock_command(
            mock_bin_dir, "rsvg-convert", "rsvg-convert version 2.54.5", 0
        )

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert (
            "rsvg-convert" in result.stdout.lower() or "rsvg" in result.stdout.lower()
        )

    def test_detects_rsvg_convert_missing(self, mock_env, mock_bin_dir):
        """
        Test that script detects when rsvg-convert is not installed.

        Given: rsvg-convert not installed (librsvg2-bin missing)
        When: verify-deps.sh is executed
        Then: Output shows [✗] rsvg-convert not found
              Exit code is 1
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)
        # rsvg-convert not created - simulating missing dependency

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert result.returncode == 1
        assert "[✗]" in result.stdout


class TestMermaidCliVerification:
    """Test verification of mermaid-cli (via npx)."""

    def test_checks_mermaid_cli_available(self, mock_env, mock_bin_dir):
        """
        Test that script verifies mermaid-cli is available via npx.

        Given: @mermaid-js/mermaid-cli installed and available via npx
        When: verify-deps.sh is executed
        Then: Output shows [✓] mermaid-cli
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        # Mock npx that can run mermaid-cli
        npx_script = mock_bin_dir / "npx"
        npx_script.write_text("""#!/bin/bash
if [[ "$*" == *"mmdc"* ]] || [[ "$*" == *"mermaid"* ]]; then
    echo "0.10.3"
    exit 0
fi
echo "Command not found"
exit 1
""")
        npx_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert "mermaid" in result.stdout.lower() or "mmdc" in result.stdout.lower()

    def test_detects_mermaid_cli_missing(self, mock_env, mock_bin_dir):
        """
        Test that script detects when mermaid-cli is not installed.

        Given: @mermaid-js/mermaid-cli not installed
        When: verify-deps.sh is executed
        Then: Output shows [✗] mermaid-cli not found
              Exit code is 1
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        # Mock npx that fails for mermaid-cli
        npx_script = mock_bin_dir / "npx"
        npx_script.write_text("""#!/bin/bash
echo "npx: command not found: mmdc"
exit 1
""")
        npx_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env)

        assert result.returncode == 1
        assert "[✗]" in result.stdout


class TestMalformedConfig:
    """Test handling of malformed configuration files."""

    def test_handles_malformed_config_json_gracefully(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that script handles malformed converter_config.json gracefully.

        Given: converter_config.json contains invalid JSON
        When: verify-deps.sh is executed
        Then: Script completes without crashing
              Script defaults to tectonic
        """
        create_mock_command(mock_bin_dir, "python3", "Python 3.14.0", 0)
        create_mock_command(mock_bin_dir, "node", "v20.10.0", 0)
        create_mock_command(mock_bin_dir, "pandoc", "pandoc 3.9", 0)
        create_mock_command(mock_bin_dir, "tectonic", "0.15.0", 0)

        # Create malformed converter_config.json
        config_file = tmp_path / "converter_config.json"
        config_file.write_text("{ invalid json content }")

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_verify_deps(env=mock_env, cwd=tmp_path)

        # Script should not crash - should complete with some exit code
        assert result.returncode in [0, 1]
        # Should default to tectonic when config is invalid
        assert "tectonic" in result.stdout.lower()


"""
Test Summary
============
Total Tests: 42
- Script Existence: 2
- Missing Dependencies: 5
- Version Validation: 12
- Output Format: 4
- Exit Codes: 2
- LaTeX Engine Detection: 4
- Edge Cases: 5
- Chromium Configuration: 2
- Python Package Verification: 2
- rsvg-convert Verification: 2
- Mermaid CLI Verification: 2
- Malformed Config Handling: 1

Coverage Areas:
- Script existence and executability
- Missing dependency detection (Python, Node.js, Pandoc, LaTeX engines, rsvg-convert)
- Version validation (minimum versions: Python 3.12+, Node.js 18+, Pandoc 3.9+)
- Output formatting ([✓] success markers, [✗] failure markers, version numbers)
- Exit code behavior (0 for success, 1 for any failures)
- LaTeX engine detection (env var, config file, default to tectonic)
- Edge case handling (malformed versions, command failures, CI environments)
- Chromium configuration verification
- Python package verification (python-frontmatter)
- rsvg-convert verification (from librsvg2-bin, used by Pandoc for SVG→PDF)
- Mermaid CLI verification (via npx @mermaid-js/mermaid-cli)
- Malformed configuration file handling

Test Approach:
- Uses subprocess to execute shell script
- Creates mock executables in temporary bin directories
- Manipulates PATH environment to control command availability
- Creates mock version outputs for version validation tests
- Tests both positive and negative cases for each validation
- Ensures proper exit codes and output formatting

Note: All tests are expected to FAIL initially (RED phase of TDD).
The script scripts/verify-deps.sh does not exist yet.
"""
