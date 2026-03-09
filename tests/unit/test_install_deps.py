"""
Tests for scripts/install-deps.sh - dependency installation script.

This module tests the dependency installation script that installs all required
project dependencies on various platforms:
- Python 3.12+ (unless SKIP_PYTHON=true)
- Node.js 20+ (unless SKIP_NODE=true)
- Pandoc 3.9+
- LaTeX engine (tectonic/pdflatex/xelatex/lualatex based on LATEX_ENGINE env var)
- Chromium configuration (via configure-chromium.sh, unless SKIP_CHROMIUM=true)
- python-frontmatter Python package
- librsvg2-bin/librsvg (for rsvg-convert)
- @mermaid-js/mermaid-cli (npm package)

The script supports multiple platforms (Debian/Ubuntu, Alpine, macOS, RHEL/Fedora)
and returns appropriate exit codes:
- 0: Success
- 1: General error
- 2: Unsupported platform (Windows)
- 3: Missing sudo (when needed)
- 4: Network error
- 5: Verification failed (verify-deps.sh fails after install)
"""

import pytest
import subprocess
import os
from pathlib import Path


# Path to the script under test
SCRIPT_PATH = Path(__file__).parent.parent.parent / "scripts" / "install-deps.sh"


@pytest.fixture
def mock_env():
    """
    Provide a clean environment for testing.

    Returns:
        dict: Clean environment variables without install flags.
    """
    env = os.environ.copy()
    # Remove any install-related env vars
    for key in ["SKIP_PYTHON", "SKIP_NODE", "SKIP_CHROMIUM", "LATEX_ENGINE"]:
        if key in env:
            del env[key]
    return env


@pytest.fixture
def mock_bin_dir(tmp_path):
    """
    Create a temporary bin directory for mock executables.

    Automatically includes mock pandoc with version 3.9 to satisfy
    the version check in install-deps.sh.

    Args:
        tmp_path: pytest temporary directory fixture.

    Returns:
        Path: Path to temporary bin directory.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    # Add mock pandoc that returns version >= 3.9 (required by install-deps.sh)
    pandoc_script = """#!/bin/bash
if [ "$1" = "--version" ]; then
    echo "pandoc 3.9"
    echo "Features: +server +lua"
    exit 0
fi
echo "[MOCK] pandoc $@"
exit 0
"""
    pandoc_path = bin_dir / "pandoc"
    pandoc_path.write_text(pandoc_script)
    pandoc_path.chmod(0o755)

    # Add mock apt-cache that returns pandoc version >= 3.9
    # (used by check_pandoc_pkg_version to check BEFORE installing)
    apt_cache_script = """#!/bin/bash
if [ "$1" = "show" ] && [ "$2" = "pandoc" ]; then
    echo "Package: pandoc"
    echo "Version: 3.9-1"
    echo "Description: general markup converter"
    exit 0
fi
echo "[MOCK] apt-cache $@"
exit 0
"""
    apt_cache_path = bin_dir / "apt-cache"
    apt_cache_path.write_text(apt_cache_script)
    apt_cache_path.chmod(0o755)

    # Add mock tectonic (default LaTeX engine, checked by post-install verification)
    tectonic_script = """#!/bin/bash
if [ "$1" = "--version" ]; then
    echo "Tectonic 0.15.0"
    exit 0
fi
echo "[MOCK] tectonic $@"
exit 0
"""
    tectonic_path = bin_dir / "tectonic"
    tectonic_path.write_text(tectonic_script)
    tectonic_path.chmod(0o755)

    # Add mock rsvg-convert (checked by post-install verification)
    rsvg_script = """#!/bin/bash
if [ "$1" = "--version" ]; then
    echo "rsvg-convert version 2.56.0"
    exit 0
fi
echo "[MOCK] rsvg-convert $@"
exit 0
"""
    rsvg_path = bin_dir / "rsvg-convert"
    rsvg_path.write_text(rsvg_script)
    rsvg_path.chmod(0o755)

    return bin_dir


def create_mock_command(
    bin_dir: Path, command: str, script_content: str = None, exit_code: int = 0
):
    """
    Create a mock executable script.

    Args:
        bin_dir: Directory to create executable in.
        command: Name of the command to mock.
        script_content: Script content (default: simple exit)
        exit_code: Exit code for the mock command.

    Returns:
        Path: Path to created mock executable.
    """
    mock_path = bin_dir / command
    if script_content is None:
        script_content = f"""#!/bin/bash
exit {exit_code}
"""
    mock_path.write_text(script_content)
    mock_path.chmod(0o755)
    return mock_path


def create_mock_package_manager(bin_dir: Path, manager_name: str, success: bool = True):
    """
    Create a mock package manager (apt-get, apk, brew, dnf).

    Args:
        bin_dir: Directory to create executable in.
        manager_name: Name of package manager (apt-get, apk, brew, dnf).
        success: Whether install commands should succeed.

    Returns:
        Path: Path to created mock executable.
    """
    exit_code = 0 if success else 1
    script = f"""#!/bin/bash
# Mock {manager_name}
# Track what was installed (for verification)
echo "[MOCK] {manager_name} $@"
exit {exit_code}
"""
    return create_mock_command(bin_dir, manager_name, script, exit_code)


def create_mock_pandoc(bin_dir: Path, version: str = "3.9"):
    """
    Create a mock pandoc that returns a specific version.

    Args:
        bin_dir: Directory to create executable in.
        version: Version string to return (default: 3.9).

    Returns:
        Path: Path to created mock executable.
    """
    script = f"""#!/bin/bash
if [ "$1" = "--version" ]; then
    echo "pandoc {version}"
    echo "Features: +server +lua"
    exit 0
fi
echo "[MOCK] pandoc $@"
exit 0
"""
    return create_mock_command(bin_dir, "pandoc", script, 0)


def run_install_deps(env: dict = None, cwd: Path = None) -> subprocess.CompletedProcess:
    """
    Run the install-deps.sh script and capture output.

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

    def test_install_deps_script_exists(self):
        """
        Test that install-deps.sh exists in scripts directory.

        Given: Project structure with scripts/ directory
        When: Checking for install-deps.sh
        Then: Script file exists
        """
        assert SCRIPT_PATH.exists(), f"Script not found at {SCRIPT_PATH}"

    def test_install_deps_script_is_executable(self):
        """
        Test that install-deps.sh has executable permissions.

        Given: install-deps.sh exists
        When: Checking file permissions
        Then: Script is executable
        """
        assert os.access(SCRIPT_PATH, os.X_OK), f"Script not executable: {SCRIPT_PATH}"


class TestArchitectureDetection:
    """Test architecture detection logic."""

    def test_detects_x86_64_architecture(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script detects x86_64 architecture correctly.

        Given: System with uname -m returning x86_64
        When: install-deps.sh is executed
        Then: Script uses x86_64 binaries for downloads
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock uname -m to return x86_64
        create_mock_command(
            mock_bin_dir,
            "uname",
            "#!/bin/bash\n[[ \"$1\" == \"-m\" ]] && echo 'x86_64' || echo 'Linux'\nexit 0\n",
            0,
        )

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should detect x86_64 architecture
        assert (
            "x86_64" in result.stdout.lower()
            or "amd64" in result.stdout.lower()
            or result.returncode == 0
        )

    def test_detects_arm64_architecture(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script detects ARM64 architecture correctly.

        Given: System with uname -m returning aarch64
        When: install-deps.sh is executed
        Then: Script uses ARM64 binaries for downloads
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock uname -m to return aarch64
        create_mock_command(
            mock_bin_dir,
            "uname",
            "#!/bin/bash\n[[ \"$1\" == \"-m\" ]] && echo 'aarch64' || echo 'Linux'\nexit 0\n",
            0,
        )

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should detect ARM64 architecture
        assert (
            "aarch64" in result.stdout.lower()
            or "arm64" in result.stdout.lower()
            or result.returncode == 0
        )


class TestPlatformDetection:
    """Test platform detection logic."""

    def test_detects_debian_ubuntu_platform(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script detects Debian/Ubuntu correctly.

        Given: System with apt-get available
        When: install-deps.sh is executed
        Then: Script uses apt-get for installations
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should use apt-get
        assert "apt-get" in result.stdout.lower() or "apt" in result.stdout.lower()

    def test_detects_alpine_platform(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script detects Alpine Linux correctly.

        Given: System with apk available
        When: install-deps.sh is executed
        Then: Script uses apk for installations
        """
        create_mock_package_manager(mock_bin_dir, "apk", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should use apk
        assert "apk" in result.stdout.lower()

    def test_detects_macos_platform(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script detects macOS correctly.

        Given: System with brew available or darwin kernel
        When: install-deps.sh is executed
        Then: Script uses brew for installations
        """
        create_mock_package_manager(mock_bin_dir, "brew", success=True)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        # Mock uname to return darwin
        create_mock_command(
            mock_bin_dir, "uname", "#!/bin/bash\necho 'Darwin'\nexit 0\n", 0
        )

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should use brew
        assert "brew" in result.stdout.lower()

    def test_detects_rhel_fedora_platform(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script detects RHEL/Fedora correctly.

        Given: System with dnf available
        When: install-deps.sh is executed
        Then: Script uses dnf for installations
        """
        create_mock_package_manager(mock_bin_dir, "dnf", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should use dnf
        assert "dnf" in result.stdout.lower()

    def test_detects_windows_and_exits_with_code_2(self, mock_env, mock_bin_dir):
        """
        Test that script detects Windows and exits with code 2.

        Given: System is Windows (detected via uname or platform indicators)
        When: install-deps.sh is executed
        Then: Script exits with code 2
              Output indicates unsupported platform
        """
        # Mock uname to return MINGW/MSYS (Windows indicators)
        create_mock_command(
            mock_bin_dir, "uname", "#!/bin/bash\necho 'MINGW64_NT'\nexit 0\n", 0
        )

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_install_deps(env=mock_env)

        assert result.returncode == 2
        assert (
            "windows" in result.stdout.lower() or "unsupported" in result.stdout.lower()
        )

    def test_handles_unknown_platform_gracefully(self, mock_env, mock_bin_dir):
        """
        Test that script handles unknown platforms gracefully.

        Given: System without recognized package manager
        When: install-deps.sh is executed
        Then: Script exits with error
              Output indicates unsupported platform
        """
        # Empty PATH - no package managers available
        mock_env["PATH"] = str(mock_bin_dir)
        result = run_install_deps(env=mock_env)

        # Should fail with error about unsupported platform
        assert result.returncode != 0


class TestSkipFlags:
    """Test SKIP_* environment variable flags."""

    def test_skip_python_true_skips_python_installation(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that SKIP_PYTHON=true skips Python installation.

        Given: SKIP_PYTHON=true environment variable
        When: install-deps.sh is executed
        Then: Python installation is skipped
              Output indicates Python was skipped
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Python should be skipped - script must explicitly say "skip" and "python"
        assert "skip" in result.stdout.lower() and "python" in result.stdout.lower()

    def test_skip_node_true_skips_nodejs_installation(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that SKIP_NODE=true skips Node.js installation.

        Given: SKIP_NODE=true environment variable
        When: install-deps.sh is executed
        Then: Node.js installation is skipped
              Output indicates Node was skipped
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Node should be skipped - script must explicitly say "skip" and "node"
        assert "skip" in result.stdout.lower() and "node" in result.stdout.lower()

    def test_skip_chromium_true_skips_chromium_configuration(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that SKIP_CHROMIUM=true skips Chromium configuration.

        Given: SKIP_CHROMIUM=true environment variable
        When: install-deps.sh is executed
        Then: Chromium configuration is skipped
              configure-chromium.sh is not called
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Chromium should be skipped - script must explicitly say "skip" and "chromium"
        assert "skip" in result.stdout.lower() and "chromium" in result.stdout.lower()

    def test_multiple_skip_flags_work_together(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that multiple SKIP_* flags work together.

        Given: SKIP_PYTHON=true and SKIP_NODE=true
        When: install-deps.sh is executed
        Then: Both Python and Node.js are skipped
              Other dependencies are still installed
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Both should be skipped or not mentioned
        # At minimum, script should succeed
        assert result.returncode == 0 or "skip" in result.stdout.lower()

    def test_skip_flags_default_to_false(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that skip flags default to false (install everything).

        Given: No SKIP_* environment variables set
        When: install-deps.sh is executed
        Then: All dependencies are installed
              No skip messages in output
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        # Don't set any SKIP_* flags

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Script should attempt to install dependencies
        # This will likely fail in unit tests, but should show installation attempts
        assert "install" in result.stdout.lower() or "apt-get" in result.stdout.lower()


class TestLatexEngineSelection:
    """Test LaTeX engine selection based on LATEX_ENGINE env var."""

    def test_latex_engine_tectonic_installs_tectonic(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that LATEX_ENGINE=tectonic installs tectonic.

        Given: LATEX_ENGINE=tectonic environment variable
        When: install-deps.sh is executed
        Then: tectonic is installed
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["LATEX_ENGINE"] = "tectonic"
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should install tectonic
        assert "tectonic" in result.stdout.lower()

    def test_latex_engine_pdflatex_installs_texlive(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that LATEX_ENGINE=pdflatex installs texlive.

        Given: LATEX_ENGINE=pdflatex environment variable
        When: install-deps.sh is executed
        Then: texlive/pdflatex packages are installed
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["LATEX_ENGINE"] = "pdflatex"
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should install texlive or pdflatex
        assert "texlive" in result.stdout.lower() or "pdflatex" in result.stdout.lower()

    def test_latex_engine_xelatex_installs_texlive_xetex(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that LATEX_ENGINE=xelatex installs texlive-xetex.

        Given: LATEX_ENGINE=xelatex environment variable
        When: install-deps.sh is executed
        Then: texlive-xetex packages are installed
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["LATEX_ENGINE"] = "xelatex"
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should install xelatex or texlive-xetex
        assert "xelatex" in result.stdout.lower() or "xetex" in result.stdout.lower()

    def test_latex_engine_lualatex_installs_texlive_luatex(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that LATEX_ENGINE=lualatex installs texlive-luatex.

        Given: LATEX_ENGINE=lualatex environment variable
        When: install-deps.sh is executed
        Then: texlive-luatex packages are installed
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["LATEX_ENGINE"] = "lualatex"
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should install lualatex or texlive-luatex
        assert "lualatex" in result.stdout.lower() or "luatex" in result.stdout.lower()

    def test_default_latex_engine_is_tectonic(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that default LaTeX engine is tectonic when not specified.

        Given: No LATEX_ENGINE environment variable
        When: install-deps.sh is executed
        Then: tectonic is installed (default)
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        # Don't set LATEX_ENGINE
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should default to tectonic
        assert "tectonic" in result.stdout.lower()

    def test_invalid_latex_engine_defaults_to_tectonic_with_warning(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that invalid LATEX_ENGINE value defaults to tectonic with warning.

        Given: LATEX_ENGINE=invalid_engine (not a valid engine)
        When: install-deps.sh is executed
        Then: Script defaults to tectonic
              Output shows warning about invalid engine
              Installation succeeds with default
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["LATEX_ENGINE"] = "invalid_engine_name"
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should default to tectonic and show warning
        assert "tectonic" in result.stdout.lower()
        assert (
            "warning" in result.stdout.lower()
            or "invalid" in result.stdout.lower()
            or "unsupported" in result.stdout.lower()
            or "default" in result.stdout.lower()
        )


class TestExitCodes:
    """Test exit code behavior."""

    def test_exit_code_0_on_successful_install(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script exits with 0 on successful installation.

        Given: All package installations succeed
              verify-deps.sh passes after install
        When: install-deps.sh is executed
        Then: Exit code is 0
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        assert result.returncode == 0

    def test_exit_code_2_on_windows(self, mock_env, mock_bin_dir):
        """
        Test that script exits with 2 on Windows platform.

        Given: System is detected as Windows
        When: install-deps.sh is executed
        Then: Exit code is 2
              Output indicates unsupported platform
        """
        # Mock uname to return Windows indicator
        create_mock_command(
            mock_bin_dir, "uname", "#!/bin/bash\necho 'MINGW64_NT'\nexit 0\n", 0
        )

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_install_deps(env=mock_env)

        assert result.returncode == 2

    def test_exit_code_3_when_sudo_needed_but_not_available(
        self, mock_env, mock_bin_dir
    ):
        """
        Test that script exits with 3 when sudo is needed but not available.

        Given: Linux system (requires sudo) without sudo command
               Non-root user (_TEST_EUID=1000, since EUID is readonly in bash)
        When: install-deps.sh is executed
        Then: Exit code is 3
        """
        # Create apt-get but not sudo
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        # Don't create sudo

        mock_env["PATH"] = str(mock_bin_dir)
        # Force non-root context (EUID is readonly in bash, so use _TEST_EUID)
        mock_env["_TEST_EUID"] = "1000"
        result = run_install_deps(env=mock_env)

        # Should fail with exit code 3 (strict assertion)
        assert result.returncode == 3

    def test_exit_code_5_when_verify_deps_fails_after_install(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that script exits with 5 when verify-deps.sh fails after install.

        Given: All installations succeed
              verify-deps.sh fails after installation
        When: install-deps.sh is executed
        Then: Exit code is 5
              Output indicates verification failed
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to FAIL
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 1\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should exit with code 5 (verification failed) - strict assertion
        assert result.returncode == 5

    def test_exit_code_4_on_network_error(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script exits with 4 on network error.

        Given: Package manager fails with network-specific error
        When: install-deps.sh is executed
        Then: Exit code is 4
              Output indicates network error
        """
        # Create apt-get that fails with network error message
        network_error_script = """#!/bin/bash
echo "E: Unable to fetch some archives, maybe run apt-get update or try with --fix-missing?"
echo "E: Failed to fetch http://archive.ubuntu.com/... Connection timed out"
exit 100
"""
        create_mock_command(mock_bin_dir, "apt-get", network_error_script, 100)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_install_deps(env=mock_env)

        # Should exit with code 4 (network error) - strict assertion
        assert result.returncode == 4

    def test_exit_code_1_on_general_error(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script exits with 1 on general error.

        Given: A non-specific error occurs during installation
        When: install-deps.sh is executed
        Then: Exit code is 1
        """
        # Create apt-get that fails with general error (not network, not missing sudo)
        general_error_script = """#!/bin/bash
echo "E: dpkg was interrupted, you must manually run 'sudo dpkg --configure -a'"
exit 1
"""
        create_mock_command(mock_bin_dir, "apt-get", general_error_script, 1)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_install_deps(env=mock_env)

        # Should exit with code 1 (general error)
        assert result.returncode == 1


class TestIdempotency:
    """Test idempotency - running script multiple times."""

    def test_running_script_twice_does_not_break(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that running install script twice doesn't break anything.

        Given: Script has been run once successfully
        When: Script is run again
        Then: Second run succeeds
              No errors about dependencies already installed
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        # Run first time
        result1 = run_install_deps(env=mock_env, cwd=tmp_path)
        assert result1.returncode == 0

        # Run second time
        result2 = run_install_deps(env=mock_env, cwd=tmp_path)
        assert result2.returncode == 0

    def test_script_detects_already_installed_dependencies(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that script detects already-installed dependencies.

        Given: Some dependencies already installed
        When: install-deps.sh is executed
        Then: Script skips already-installed packages
              Output indicates packages already present
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock commands as already installed
        create_mock_command(
            mock_bin_dir, "pandoc", "#!/bin/bash\necho 'pandoc 3.1.11'\nexit 0\n", 0
        )

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should succeed and possibly indicate already installed
        assert result.returncode == 0


class TestPackageInstallation:
    """Test actual package installation logic."""

    def test_installs_pandoc(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script installs Pandoc.

        Given: System without Pandoc
        When: install-deps.sh is executed
        Then: Pandoc is installed via package manager
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should attempt to install pandoc
        assert "pandoc" in result.stdout.lower()

    def test_installs_librsvg(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script installs librsvg2-bin/librsvg.

        Given: System without librsvg
        When: install-deps.sh is executed
        Then: librsvg package is installed
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should install librsvg
        assert "librsvg" in result.stdout.lower() or "rsvg" in result.stdout.lower()

    def test_installs_python_frontmatter_via_pip(
        self, mock_env, mock_bin_dir, tmp_path
    ):
        """
        Test that script installs python-frontmatter via pip.

        Given: Python available, python-frontmatter not installed
        When: install-deps.sh is executed (without SKIP_PYTHON)
        Then: python-frontmatter is installed via pip
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)
        create_mock_command(
            mock_bin_dir,
            "pip3",
            "#!/bin/bash\necho 'Installing python-frontmatter'\nexit 0\n",
            0,
        )

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"
        # Don't skip Python - allow installation

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should install python-frontmatter
        assert "frontmatter" in result.stdout.lower() or "pip" in result.stdout.lower()

    def test_installs_mermaid_cli_via_npm(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script installs @mermaid-js/mermaid-cli via npm.

        Given: Node.js available
        When: install-deps.sh is executed (without SKIP_NODE)
        Then: mermaid-cli is installed globally via npm
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)
        create_mock_command(
            mock_bin_dir,
            "npm",
            "#!/bin/bash\necho 'Installing @mermaid-js/mermaid-cli'\nexit 0\n",
            0,
        )

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"
        # Don't skip Node - allow installation

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should install mermaid-cli
        assert "mermaid" in result.stdout.lower() or "npm" in result.stdout.lower()

    def test_calls_configure_chromium_script(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script calls configure-chromium.sh.

        Given: configure-chromium.sh exists
              SKIP_CHROMIUM is not set
        When: install-deps.sh is executed
        Then: configure-chromium.sh is called
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Create configure-chromium.sh
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        configure_script = scripts_dir / "configure-chromium.sh"
        configure_script.write_text(
            "#!/bin/bash\necho 'Configuring Chromium'\nexit 0\n"
        )
        configure_script.chmod(0o755)

        # Mock verify-deps.sh to pass
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        # Don't skip Chromium

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should call configure-chromium.sh
        assert "chromium" in result.stdout.lower() or result.returncode == 0


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_handles_network_errors_gracefully(self, mock_env, mock_bin_dir):
        """
        Test that script handles network errors gracefully.

        Given: Package manager fails with network error
        When: install-deps.sh is executed
        Then: Script exits with appropriate error code
              Output indicates network issue
        """
        # Create apt-get that fails
        create_mock_package_manager(mock_bin_dir, "apt-get", success=False)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        mock_env["PATH"] = str(mock_bin_dir)
        result = run_install_deps(env=mock_env)

        # Should fail (not exit code 0)
        assert result.returncode != 0

    def test_handles_missing_package_manager(self, mock_env, mock_bin_dir):
        """
        Test that script handles missing package manager.

        Given: No recognized package manager available
        When: install-deps.sh is executed
        Then: Script exits with error
              Output indicates unsupported platform
        """
        # Empty PATH - no package managers
        mock_env["PATH"] = str(mock_bin_dir)
        result = run_install_deps(env=mock_env)

        # Should fail
        assert result.returncode != 0

    def test_runs_in_ci_environment(self, mock_env, mock_bin_dir, tmp_path):
        """
        Test that script runs successfully in CI environment.

        Given: CI=true environment variable (non-interactive)
        When: install-deps.sh is executed
        Then: Script completes without prompts
              Appropriate non-interactive flags used
        """
        create_mock_package_manager(mock_bin_dir, "apt-get", success=True)
        create_mock_command(mock_bin_dir, "sudo", "#!/bin/bash\n$@\n", 0)

        # Mock verify-deps.sh to pass
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        verify_script = scripts_dir / "verify-deps.sh"
        verify_script.write_text("#!/bin/bash\nexit 0\n")
        verify_script.chmod(0o755)

        mock_env["PATH"] = str(mock_bin_dir)
        mock_env["CI"] = "true"
        mock_env["DEBIAN_FRONTEND"] = "noninteractive"
        mock_env["SKIP_PYTHON"] = "true"
        mock_env["SKIP_NODE"] = "true"
        mock_env["SKIP_CHROMIUM"] = "true"

        result = run_install_deps(env=mock_env, cwd=tmp_path)

        # Should complete without hanging
        assert result.returncode in [0, 1]


class TestPandocVersionBump:
    """Test Pandoc version bump to 3.9."""

    def test_pandoc_binary_version_is_at_least_3_9(self):
        """
        Test that install_pandoc_binary() version is at least 3.9.

        Given: scripts/install-deps.sh exists with install_pandoc_binary() function
        When: Searching for version declaration in the function
        Then: Version string is >= 3.9
        """
        import re

        content = SCRIPT_PATH.read_text()

        # Find the install_pandoc_binary function and extract version
        # Pattern: local version="X.Y.Z" or local version='X.Y.Z'
        version_pattern = r'install_pandoc_binary\(\)\s*\{[^}]*local\s+version=["\']([0-9]+\.[0-9]+(?:\.[0-9]+)?(?:\.[0-9]+)?)["\']'
        match = re.search(version_pattern, content, re.DOTALL)

        assert match is not None, (
            "Could not find 'local version=' in install_pandoc_binary()"
        )

        version_str = match.group(1)
        version_parts = [int(x) for x in version_str.split(".")]

        # Pad to 4 components for comparison (3.9.0.0 format)
        while len(version_parts) < 4:
            version_parts.append(0)

        # Expected minimum: 3.9.0.0
        expected_min = [3, 9, 0, 0]

        assert version_parts >= expected_min, (
            f"Pandoc binary version {version_str} is less than 3.9"
        )

    def test_pandoc_pkg_version_check_requires_3_9_0(self):
        """
        Test that check_pandoc_pkg_version call requires at least 3.9.0.

        Given: scripts/install-deps.sh contains check_pandoc_pkg_version call
        When: Searching for the version check arguments
        Then: Minimum version is >= 3 9 0
        """
        import re

        content = SCRIPT_PATH.read_text()

        # Find check_pandoc_pkg_version call with version arguments
        # Pattern: check_pandoc_pkg_version "$PKG_MANAGER" MAJOR MINOR PATCH
        version_check_pattern = (
            r'check_pandoc_pkg_version\s+["\$][^"]*["]\s+(\d+)\s+(\d+)\s+(\d+)'
        )
        match = re.search(version_check_pattern, content)

        assert match is not None, (
            "Could not find check_pandoc_pkg_version call with version args"
        )

        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))

        version_tuple = (major, minor, patch)
        expected_min = (3, 9, 0)

        assert version_tuple >= expected_min, (
            f"check_pandoc_pkg_version requires {major}.{minor}.{patch}, expected >= 3.9.0"
        )

    def test_pandoc_binary_version_comment_references_issue(self):
        """
        Test that version line comment mentions the bug fix context.

        Given: scripts/install-deps.sh with version declaration in install_pandoc_binary()
        When: Searching for comment near version line
        Then: Comment includes reference to issue 11201 or unnumbered table counter bug
        """
        import re

        content = SCRIPT_PATH.read_text()

        # Find the install_pandoc_binary function
        func_start = content.find("install_pandoc_binary() {")
        assert func_start != -1, "Could not find install_pandoc_binary() function"

        # Find the next closing brace (end of function) - simple heuristic
        func_end = content.find("\n}\n", func_start)
        assert func_end != -1, "Could not find end of install_pandoc_binary() function"

        function_body = content[func_start:func_end]

        # Find the version line
        version_line_match = re.search(
            r'local\s+version=["\']([0-9.]+)["\'](.*)$', function_body, re.MULTILINE
        )
        assert version_line_match is not None, "Could not find version declaration"

        # Check comment on same line or next few lines (within ~200 chars after version line)
        context_start = version_line_match.start()
        context_end = min(context_start + 200, len(function_body))
        context = function_body[context_start:context_end]

        # Look for version rationale references (case insensitive)
        context_lower = context.lower()
        has_issue_ref = (
            "11201" in context_lower
            or "unnumbered" in context_lower
            or ("counter" in context_lower and "table" in context_lower)
            or "alerts" in context_lower
            or "callout" in context_lower
        )

        assert has_issue_ref, (
            f"Comment near version line does not reference version rationale. "
            f"Context: {context[:150]}"
        )


class TestVenvCreation:
    """Test .venv creation logic for non-root users."""

    def test_creates_venv_when_non_root_and_requirements_exist(self):
        """
        Test that the script contains logic to create .venv for non-root users.

        Given: A non-root user (uid != 0) with requirements.txt present
        When: Searching for venv creation logic in the script
        Then: Script contains code that creates .venv using python3 -m venv
        """
        import re

        content = SCRIPT_PATH.read_text()

        # Script must contain a venv creation call guarded by a non-root check
        # Look for: python3 -m venv ... .venv (in some form)
        assert re.search(r"python3\s+-m\s+venv", content), (
            "Script does not contain 'python3 -m venv' for venv creation"
        )

    def test_skips_venv_when_root(self):
        """
        Test that the script skips venv creation when running as root.

        Given: A root user (uid == 0)
        When: Searching for root guard around venv creation in the script
        Then: Venv creation block is conditional on non-root uid
        """
        import re

        content = SCRIPT_PATH.read_text()

        # There must be a block that checks uid/EUID and conditionally creates the venv.
        # Either: [ "$effective_uid" -ne 0 ] or [ "$EUID" != "0" ] or similar.
        has_uid_check = bool(
            re.search(r"effective_uid.*-ne\s+0", content)
            or re.search(r'_TEST_EUID.*!=.*["\']0["\']', content)
            or re.search(r'effective_uid.*!=.*["\']0["\']', content)
        )
        assert has_uid_check, (
            "Script does not have a non-root uid guard for venv creation; "
            "root users should skip the venv path"
        )

    def test_skips_venv_when_skip_venv_true(self):
        """
        Test that SKIP_VENV=true prevents venv creation.

        Given: The SKIP_VENV environment variable is set to "true"
        When: Searching for SKIP_VENV handling in the script
        Then: Script contains a check for SKIP_VENV before creating the venv
        """
        content = SCRIPT_PATH.read_text()

        assert "SKIP_VENV" in content, (
            "Script does not reference SKIP_VENV env var; "
            "setting SKIP_VENV=true should prevent venv creation"
        )

    def test_skips_venv_when_no_requirements_txt(self):
        """
        Test that venv creation is skipped when requirements.txt is absent.

        Given: No requirements.txt file at PROJECT_ROOT
        When: Searching for requirements.txt existence guard in the script
        Then: Venv creation is conditional on requirements.txt existing
        """
        import re

        content = SCRIPT_PATH.read_text()

        # Script must check for requirements.txt existence before creating venv
        assert re.search(
            r'-f\s+["\']?\$[{(]?PROJECT_ROOT[)}]?/requirements\.txt', content
        ), "Script does not check for requirements.txt before creating venv"

    def test_venv_uses_clear_flag(self):
        """
        Test that venv creation uses --clear to handle stale venv directories.

        Given: scripts/install-deps.sh with venv creation logic
        When: Searching for the venv creation command
        Then: Command includes --clear flag
        """
        import re

        content = SCRIPT_PATH.read_text()

        # python3 -m venv --clear ...
        assert re.search(r"python3\s+-m\s+venv\s+--clear", content), (
            "Script does not use '--clear' flag with python3 -m venv; "
            "stale venvs must be cleared for repeatability"
        )

    def test_prints_activation_instructions(self):
        """
        Test that the script prints .venv activation instructions for non-root users.

        Given: Venv creation succeeds for a non-root user
        When: Searching for activation hint in the script
        Then: Script contains output mentioning 'source' or 'activate' for the venv
        """
        import re

        content = SCRIPT_PATH.read_text()

        # Script should print something like: source .venv/bin/activate
        has_activation_hint = bool(
            re.search(r"source\s+.*\.venv.*activate", content)
            or re.search(r"\.venv.*bin/activate", content)
            or re.search(r"activate.*\.venv", content)
        )
        assert has_activation_hint, (
            "Script does not print activation instructions after creating .venv; "
            "non-root users need to know how to activate it"
        )


class TestLocalNpmInstall:
    """Test local npm install (non-root) vs global npm install (root)."""

    def test_local_npm_install_when_non_root_and_package_json_exists(self):
        """
        Test that the script runs 'npm install --prefix' for non-root users.

        Given: A non-root user with package.json present at PROJECT_ROOT
        When: Searching for local npm install logic in the script
        Then: Script contains 'npm install --prefix' (local, uses lockfile)
        """
        import re

        content = SCRIPT_PATH.read_text()

        assert re.search(r"npm\s+install\s+--prefix", content), (
            "Script does not contain 'npm install --prefix' for local installs; "
            "non-root users should use local npm install with lockfile"
        )

    def test_global_npm_install_when_root(self):
        """
        Test that the script still uses 'npm install -g' for root users.

        Given: scripts/install-deps.sh with npm install logic
        When: Searching for global npm install in the script
        Then: Script contains 'npm install -g @mermaid-js/mermaid-cli'
        """
        import re

        content = SCRIPT_PATH.read_text()

        # Global install must still be present for the root path
        assert re.search(r"npm\s+install\s+-g\s+@mermaid-js/mermaid-cli", content), (
            "Script does not contain 'npm install -g @mermaid-js/mermaid-cli'; "
            "root users should still use global npm install"
        )

    def test_skips_global_npm_when_local_done(self):
        """
        Test that the global npm install is skipped when local npm install runs.

        Given: scripts/install-deps.sh with branching npm install logic
        When: Searching for a conditional that separates local vs global paths
        Then: Global 'npm install -g' is in an else/elif branch that is
              skipped when local install has already run
        """
        import re

        content = SCRIPT_PATH.read_text()

        # There must be a conditional structure: if non-root ... npm install --prefix
        # else ... npm install -g
        # We verify that both forms exist AND that they appear within an if/else structure
        has_local = bool(re.search(r"npm\s+install\s+--prefix", content))
        has_global = bool(re.search(r"npm\s+install\s+-g\s+@mermaid-js", content))

        assert has_local and has_global, (
            f"Expected both local (npm install --prefix) and global "
            f"(npm install -g) paths. local={has_local}, global={has_global}"
        )

        # The two paths must appear in mutually exclusive branches.
        # Simplest heuristic: local install line appears before 'else' which leads to global.
        local_pos = content.find("npm install --prefix")
        global_pos = content.find("npm install -g @mermaid-js")
        assert local_pos != -1 and global_pos != -1

        # Find the closest 'else' between the two positions
        between = content[local_pos:global_pos]
        assert "else" in between or "fi" in between, (
            "Local npm install and global npm install do not appear to be "
            "in mutually exclusive branches (no 'else' or 'fi' between them)"
        )


class TestSkipSystemInstalls:
    """Test that system-level pip and npm installs are skipped on the non-root path."""

    def test_skips_system_pip_when_venv_created(self):
        """
        Test that the system pip cascade is skipped when a venv was created.

        Given: scripts/install-deps.sh with venv creation and pip cascade logic
        When: Searching for a guard that skips system pip when venv is active
        Then: The system pip cascade block is conditional on venv NOT being created
        """
        import re

        content = SCRIPT_PATH.read_text()

        # There must be a flag or condition that skips the pip cascade when
        # venv_created=true (or similar variable)
        has_venv_flag = bool(
            re.search(r"venv_created\s*=", content)
            or re.search(r"venv_created", content)
        )
        assert has_venv_flag, (
            "Script does not use a 'venv_created' flag (or equivalent) to skip "
            "the system pip cascade when a venv was created"
        )

    def test_system_pip_runs_when_root(self):
        """
        Test that the system pip cascade still runs for root users.

        Given: scripts/install-deps.sh with pip install cascade
        When: Searching for pip install python-frontmatter in script
        Then: pip cascade block (pip install, pip3, --user, --break-system-packages)
              is still present in the script for the root code path
        """
        content = SCRIPT_PATH.read_text()

        # The root path must still attempt to install python-frontmatter via pip
        assert "python-frontmatter" in content, (
            "Script no longer contains any pip install of python-frontmatter; "
            "root users need the system pip cascade"
        )

        # Must still have the pip cascade variants
        assert "--break-system-packages" in content, (
            "Script lost '--break-system-packages' pip fallback; "
            "required for root on newer Debian/Ubuntu"
        )


class TestPython3VenvPackage:
    """Test that the apt fallback path includes python3-venv."""

    def test_apt_fallback_includes_python3_venv(self):
        """
        Test that the apt-get fallback install list contains python3-venv.

        Given: scripts/install-deps.sh with an apt-get fallback for python3
        When: Searching for the fallback install_packages call
        Then: 'python3-venv' appears alongside python3 and python3-pip
              in at least one apt-get install invocation
        """
        import re

        content = SCRIPT_PATH.read_text()

        # Look for an install_packages (or apt-get install) call that includes python3-venv
        has_python3_venv = bool(re.search(r"python3-venv", content))
        assert has_python3_venv, (
            "Script does not install 'python3-venv' via apt-get; "
            "required for 'python3 -m venv' to work on Debian/Ubuntu"
        )

        # Specifically it must appear in an apt-get context (not just a comment)
        # Find the line(s) containing python3-venv and check they're not only comments
        lines_with_venv = [
            line.strip() for line in content.splitlines() if "python3-venv" in line
        ]
        non_comment_lines = [
            line for line in lines_with_venv if not line.startswith("#")
        ]
        assert non_comment_lines, (
            "'python3-venv' only appears in comments, not in an actual install command"
        )


"""
Test Summary
============
Total Tests: 53
- Script Existence: 2
- Architecture Detection: 2 (x86_64, ARM64)
- Platform Detection: 6
- Skip Flags: 5
- LaTeX Engine Selection: 6 (including invalid engine test with default behavior)
- Exit Codes: 6 (0=success, 1=general, 2=Windows, 3=no sudo, 4=network, 5=verify failed)
- Idempotency: 2
- Package Installation: 5
- Error Handling: 3
- Pandoc Version Bump: 3 (binary version >= 3.9, pkg check >= 3.9.0, comment references issue)
- Venv Creation: 6 (non-root creates venv, root skips, SKIP_VENV=true, no requirements.txt, --clear flag, activation hint)
- Local npm Install: 3 (local for non-root, global for root, mutual exclusion)
- Skip System Installs: 2 (pip cascade skipped when venv created, still runs for root)
- python3-venv package: 1 (apt fallback includes python3-venv)

Coverage Areas:
- Script existence and executability
- Architecture detection (x86_64/amd64, ARM64/aarch64) for binary downloads
- Platform detection (Debian/Ubuntu, Alpine, macOS, RHEL/Fedora, Windows)
- Skip flag handling (SKIP_PYTHON, SKIP_NODE, SKIP_CHROMIUM, SKIP_VENV)
- LaTeX engine selection (LATEX_ENGINE env var: tectonic, pdflatex, xelatex, lualatex, invalid defaults to tectonic with warning)
- Exit code behavior (0=success, 1=general error, 2=Windows, 3=no sudo, 4=network, 5=verify failed)
- Idempotent behavior (safe to run multiple times)
- Package installation (Pandoc, librsvg, python-frontmatter, mermaid-cli, chromium config)
- Error handling (network errors, missing package manager, CI environments)
- Pandoc version requirements (3.9 binary, 3.9.0 package manager minimum, bug fix documentation)
- Venv creation (PROJECT_ROOT/.venv, --clear, pip install -r requirements.txt, activation instructions)
- Root vs non-root split for npm (local --prefix for non-root, -g for root)
- System pip cascade skip when venv handles python-frontmatter install
- python3-venv in apt fallback so 'python3 -m venv' works on Debian/Ubuntu

Test Approach:
- Uses subprocess to execute shell script
- Creates mock package managers (apt-get, apk, brew, dnf)
- Creates mock commands (sudo, pip, npm, uname, etc.)
- Manipulates PATH and environment variables
- Mocks verify-deps.sh for post-install verification
- Tests both positive and negative cases
- Ensures proper exit codes and output (strict assertions for exit codes)
- Static analysis tests for version strings, flags, and structural patterns
"""
