#!/bin/sh
# shellcheck shell=bash
#
# install-deps.sh - Install all project dependencies
#
# Supports: Debian/Ubuntu (apt-get), Alpine (apk), macOS (brew), RHEL/Fedora (dnf)
#
# Exit codes:
#   0 - Success
#   1 - General error
#   2 - Unsupported platform (Windows)
#   3 - Missing sudo (when needed)
#   4 - Network error
#   5 - Verification failed

# Bootstrap: Alpine doesn't have bash by default. This bootstrap runs under
# /bin/sh first, installs bash if needed, then re-execs with bash.
if [ -z "$BASH_VERSION" ]; then
    # Check if bash is available
    if [ -x /bin/bash ]; then
        exec /bin/bash "$0" "$@"
    elif [ -x /usr/bin/bash ]; then
        exec /usr/bin/bash "$0" "$@"
    else
        # Try to install bash (Alpine)
        if command -v apk >/dev/null 2>&1; then
            echo "[*] Installing bash for Alpine..."
            apk update >/dev/null 2>&1 || true
            apk add bash >/dev/null 2>&1 || {
                echo "[!] Failed to install bash"
                exit 1
            }
            exec /bin/bash "$0" "$@"
        fi
        echo "[!] Bash is required but not found"
        exit 1
    fi
fi

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[*]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Detect platform
detect_platform() {
    local uname_output
    uname_output=$(uname -s 2>/dev/null || echo "Unknown")

    # Check for Windows (using bash pattern matching instead of grep)
    case "$uname_output" in
        *MINGW*|*MSYS*|*CYGWIN*)
            log_error "Windows is not supported. Please use WSL2 or a Linux/macOS environment."
            exit 2
            ;;
    esac

    # Check for macOS
    if [ "$uname_output" = "Darwin" ]; then
        if command -v brew >/dev/null 2>&1; then
            PKG_MANAGER="brew"
            return 0
        else
            log_error "macOS detected but Homebrew is not installed. Please install Homebrew first."
            exit 1
        fi
    fi

    # Check for package managers
    if command -v apt-get >/dev/null 2>&1; then
        PKG_MANAGER="apt-get"
    elif command -v apk >/dev/null 2>&1; then
        PKG_MANAGER="apk"
    elif command -v dnf >/dev/null 2>&1; then
        PKG_MANAGER="dnf"
    else
        log_error "Unsupported platform: No recognized package manager found (apt-get, apk, dnf, or brew)"
        exit 1
    fi
}

# Check for sudo availability (Linux only)
check_sudo() {
    local pkg_manager="$1"

    # Skip sudo check for macOS (brew)
    if [ "$pkg_manager" = "brew" ]; then
        return 0
    fi

    # Check if running as root (use $EUID which is a bash variable)
    # _TEST_EUID allows tests to override EUID (which is readonly in bash)
    local effective_uid="${_TEST_EUID:-${EUID:-1000}}"
    if [ "$effective_uid" -eq 0 ] 2>/dev/null; then
        SUDO=""
        return 0
    fi

    # Check if sudo is available
    if ! command -v sudo >/dev/null 2>&1; then
        log_error "sudo is required but not available. Please install sudo or run as root."
        exit 3
    fi

    SUDO="sudo"
}

# Detect network errors in output
is_network_error() {
    local output="$1"

    # Use case pattern matching instead of grep for portability
    # Patterns for apt-get/apk/dnf/brew
    case "$output" in
        *"Connection timed out"*|*"Unable to fetch"*|*"Network unreachable"*|*"Failed to fetch"*|*"Could not resolve"*|*"Connection refused"*|\
        *"Timeout was reached"*|*"Cannot download"*|*"Failed downloading"*|\
        *"Failed to download"*|*"Connection reset"*|*"curl: ("*)
            return 0
            ;;
    esac

    return 1
}

# Log package manager command error and exit/return appropriately
log_pkg_error() {
    local exit_code="$1"
    local output="$2"
    local context="$3"

    if is_network_error "$output"; then
        log_error "Network error during $context"
        exit 4
    fi

    log_error "$context failed with exit code $exit_code"
    if [ ${#output} -gt 1000 ]; then
        log_error "Error output (truncated): ${output:0:1000}..."
    else
        log_error "Error output: $output"
    fi
}

# Install packages based on platform
install_packages() {
    local pkg_manager="$1"
    shift
    local packages=("$@")

    log_info "Installing: ${packages[*]}"

    local output
    local exit_code

    case "$pkg_manager" in
        apt-get)
            output=$($SUDO apt-get update 2>&1) || {
                exit_code=$?
                log_pkg_error "$exit_code" "$output" "apt-get update"
                return "$exit_code"
            }

            output=$($SUDO apt-get install -y "${packages[@]}" 2>&1) || {
                exit_code=$?
                log_pkg_error "$exit_code" "$output" "apt-get install"
                return "$exit_code"
            }
            ;;
        apk)
            output=$($SUDO apk update 2>&1) || {
                exit_code=$?
                log_pkg_error "$exit_code" "$output" "apk update"
                return "$exit_code"
            }

            output=$($SUDO apk add "${packages[@]}" 2>&1) || {
                exit_code=$?
                log_pkg_error "$exit_code" "$output" "apk add"
                return "$exit_code"
            }
            ;;
        brew)
            for package in "${packages[@]}"; do
                # Check if already installed
                if brew list "$package" >/dev/null 2>&1; then
                    log_info "$package is already installed"
                else
                    output=$(brew install "$package" 2>&1) || {
                        exit_code=$?
                        log_pkg_error "$exit_code" "$output" "brew install $package"
                        return "$exit_code"
                    }
                fi
            done
            ;;
        dnf)
            output=$($SUDO dnf install -y "${packages[@]}" 2>&1) || {
                exit_code=$?
                log_pkg_error "$exit_code" "$output" "dnf install"
                return "$exit_code"
            }
            ;;
    esac
}

# Get LaTeX engine (default: tectonic)
get_latex_engine() {
    local engine="${LATEX_ENGINE:-tectonic}"

    case "$engine" in
        tectonic|pdflatex|xelatex|lualatex)
            echo "$engine"
            ;;
        *)
            log_warning "Invalid LATEX_ENGINE: $engine. Defaulting to tectonic."
            echo "tectonic"
            ;;
    esac
}

# Check if package manager has Pandoc >= minimum version available
# Returns 0 if available version is sufficient, 1 otherwise
# Uses bash built-ins only for portability
check_pandoc_pkg_version() {
    local pkg_manager="$1"
    local min_major="$2"
    local min_minor="$3"
    local min_patch="$4"

    local version=""

    case "$pkg_manager" in
        apt-get)
            # Get version from apt-cache using bash built-ins only
            # Format: "Version: 3.1.1-3build2"
            local line
            while IFS= read -r line; do
                if [[ "$line" == Version:* ]]; then
                    version="${line#Version: }"  # Remove "Version: " prefix
                    version="${version%%-*}"     # Remove debian suffix "-3build2"
                    break
                fi
            done < <(apt-cache show pandoc 2>/dev/null)
            [ -z "$version" ] && return 1
            ;;
        brew)
            # Homebrew typically has recent versions, assume OK
            return 0
            ;;
        apk|dnf)
            # Alpine/Fedora - check if pandoc exists, assume version OK if available
            # (These distros typically have more recent packages)
            return 0
            ;;
        *)
            return 1
            ;;
    esac

    [ -z "$version" ] && return 1

    # Parse version components
    local major="${version%%.*}"
    local rest="${version#*.}"
    local minor="${rest%%.*}"
    local patch="${rest#*.}"
    patch="${patch%%[^0-9]*}"
    [ -z "$patch" ] && patch=0

    # Compare versions
    if [ "$major" -gt "$min_major" ] 2>/dev/null; then
        return 0
    elif [ "$major" -eq "$min_major" ] 2>/dev/null; then
        if [ "$minor" -gt "$min_minor" ] 2>/dev/null; then
            return 0
        elif [ "$minor" -eq "$min_minor" ] 2>/dev/null; then
            if [ "$patch" -ge "$min_patch" ] 2>/dev/null; then
                return 0
            fi
        fi
    fi

    return 1
}

# Check if Pandoc version meets minimum requirement
# Returns 0 if version is sufficient, 1 otherwise
# Uses bash built-ins only for portability
check_pandoc_version() {
    local min_major="$1"
    local min_minor="$2"
    local min_patch="$3"

    if ! command -v pandoc >/dev/null 2>&1; then
        return 1
    fi

    # Get first line of pandoc --version output
    local first_line
    read -r first_line < <(pandoc --version)

    # Extract version number (second word: "pandoc 3.6.4" -> "3.6.4")
    local version="${first_line#* }"  # Remove "pandoc "

    # Parse version components using bash parameter expansion
    local major="${version%%.*}"           # "3.6.4" -> "3"
    local rest="${version#*.}"             # "3.6.4" -> "6.4"
    local minor="${rest%%.*}"              # "6.4" -> "6"
    local patch="${rest#*.}"               # "6.4" -> "4"
    patch="${patch%%[^0-9]*}"              # Remove any non-numeric suffix

    # Default patch to 0 if not present
    [ -z "$patch" ] && patch=0

    # Compare versions
    if [ "$major" -gt "$min_major" ] 2>/dev/null; then
        return 0
    elif [ "$major" -eq "$min_major" ] 2>/dev/null; then
        if [ "$minor" -gt "$min_minor" ] 2>/dev/null; then
            return 0
        elif [ "$minor" -eq "$min_minor" ] 2>/dev/null; then
            if [ "$patch" -ge "$min_patch" ] 2>/dev/null; then
                return 0
            fi
        fi
    fi

    return 1
}

# Install Pandoc from GitHub releases
install_pandoc_binary() {
    local version="3.9"  # 3.9 adds alerts extension for GFM callouts

    if ! command -v curl >/dev/null 2>&1; then
        log_error "curl command not found, cannot download Pandoc binary"
        return 1
    fi

    local arch
    arch=$(uname -m)
    local os
    os=$(uname -s)

    local url=""
    local filename=""

    case "$os" in
        Linux)
            case "$arch" in
                x86_64|amd64)
                    filename="pandoc-${version}-linux-amd64.tar.gz"
                    ;;
                aarch64|arm64)
                    filename="pandoc-${version}-linux-arm64.tar.gz"
                    ;;
                *)
                    log_error "Unsupported architecture for Pandoc binary: $arch"
                    return 1
                    ;;
            esac
            ;;
        Darwin)
            case "$arch" in
                x86_64|amd64)
                    filename="pandoc-${version}-x86_64-macOS.pkg"
                    ;;
                arm64|aarch64)
                    filename="pandoc-${version}-arm64-macOS.pkg"
                    ;;
                *)
                    log_error "Unsupported architecture for Pandoc binary: $arch"
                    return 1
                    ;;
            esac
            ;;
        *)
            log_error "Unsupported OS for Pandoc binary download: $os"
            return 1
            ;;
    esac

    url="https://github.com/jgm/pandoc/releases/download/${version}/${filename}"
    local tmp_dir
    tmp_dir=$(mktemp -d)

    log_info "Downloading Pandoc ${version} for ${os}/${arch}..."

    local output
    local exit_code

    output=$(curl -fsSL "$url" -o "$tmp_dir/$filename" 2>&1) || {
        exit_code=$?
        rm -rf "$tmp_dir"
        if is_network_error "$output"; then
            log_error "Network error during Pandoc download"
            exit 4
        fi
        log_error "Failed to download Pandoc from $url"
        return "$exit_code"
    }

    case "$os" in
        Linux)
            # Extract tarball
            if tar -xzf "$tmp_dir/$filename" -C "$tmp_dir" 2>/dev/null; then
                # Install to /usr/local/bin
                $SUDO install -m 755 "$tmp_dir/pandoc-${version}/bin/pandoc" /usr/local/bin/pandoc || {
                    exit_code=$?
                    rm -rf "$tmp_dir"
                    log_error "Failed to install Pandoc to /usr/local/bin/pandoc"
                    return "$exit_code"
                }
                rm -rf "$tmp_dir"
                log_success "Pandoc ${version} installed to /usr/local/bin/pandoc"
                return 0
            else
                rm -rf "$tmp_dir"
                log_error "Failed to extract Pandoc tarball"
                return 1
            fi
            ;;
        Darwin)
            # Install .pkg using installer
            $SUDO installer -pkg "$tmp_dir/$filename" -target / || {
                exit_code=$?
                rm -rf "$tmp_dir"
                log_error "Failed to install Pandoc package"
                return "$exit_code"
            }
            rm -rf "$tmp_dir"
            log_success "Pandoc ${version} installed"
            return 0
            ;;
    esac
}

# Install tectonic binary from GitHub releases
install_tectonic_binary() {
    # Check if required commands are available
    if ! command -v uname >/dev/null 2>&1; then
        log_error "uname command not found, cannot determine architecture"
        return 1
    fi

    if ! command -v curl >/dev/null 2>&1; then
        log_error "curl command not found, cannot download tectonic binary"
        return 1
    fi

    local arch
    arch=$(uname -m)

    local libc_suffix="gnu"
    case "$arch" in
        x86_64|amd64)
            arch="x86_64"
            ;;
        aarch64|arm64)
            arch="aarch64"
            # Tectonic only provides musl builds for aarch64
            libc_suffix="musl"
            ;;
        *)
            log_error "Unsupported architecture for tectonic: $arch"
            return 1
            ;;
    esac

    local url="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-${arch}-unknown-linux-${libc_suffix}.tar.gz"
    local tmp_dir
    tmp_dir=$(mktemp -d)

    log_info "Downloading tectonic binary for ${arch}..."

    # Download and extract
    local output
    local exit_code

    output=$(curl -fsSL "$url" -o "$tmp_dir/tectonic.tar.gz" 2>&1) || {
        exit_code=$?
        rm -rf "$tmp_dir"
        if is_network_error "$output"; then
            log_error "Network error during tectonic download"
            return 4
        fi
        log_error "Failed to download tectonic from $url"
        return "$exit_code"
    }

    # Extract tarball
    if tar -xzf "$tmp_dir/tectonic.tar.gz" -C "$tmp_dir" 2>/dev/null; then
        # Install to /usr/local/bin
        $SUDO install -m 755 "$tmp_dir/tectonic" /usr/local/bin/tectonic || {
            exit_code=$?
            rm -rf "$tmp_dir"
            log_error "Failed to install tectonic to /usr/local/bin/tectonic"
            return "$exit_code"
        }
        rm -rf "$tmp_dir"
        log_success "tectonic installed to /usr/local/bin/tectonic"
        return 0
    else
        rm -rf "$tmp_dir"
        log_error "Failed to extract tectonic tarball"
        return 1
    fi
}

# Install LaTeX engine
install_latex_engine() {
    local pkg_manager="$1"
    local engine="$2"

    log_info "Installing LaTeX engine: $engine"

    case "$engine" in
        tectonic)
            case "$pkg_manager" in
                apt-get)
                    # Try to install tectonic from package manager, otherwise download binary
                    if apt-cache show tectonic >/dev/null 2>&1; then
                        install_packages "$pkg_manager" tectonic
                    else
                        log_info "tectonic not available in apt repositories, downloading binary from GitHub"
                        install_tectonic_binary || log_warning "Failed to install tectonic binary, will rely on system install or manual setup"
                    fi
                    ;;
                apk)
                    if apk search tectonic 2>/dev/null | grep -q "^tectonic"; then
                        install_packages "$pkg_manager" tectonic
                    else
                        log_info "tectonic not available in apk repositories, downloading binary from GitHub"
                        install_tectonic_binary || log_warning "Failed to install tectonic binary, will rely on system install or manual setup"
                    fi
                    ;;
                brew)
                    install_packages "$pkg_manager" tectonic
                    ;;
                dnf)
                    if dnf search tectonic 2>/dev/null | grep -q "tectonic"; then
                        install_packages "$pkg_manager" tectonic
                    else
                        log_info "tectonic not available in dnf repositories, downloading binary from GitHub"
                        install_tectonic_binary || log_warning "Failed to install tectonic binary, will rely on system install or manual setup"
                    fi
                    ;;
            esac
            ;;
        pdflatex)
            case "$pkg_manager" in
                apt-get)
                    install_packages "$pkg_manager" texlive-latex-base texlive-latex-extra texlive-fonts-extra
                    ;;
                apk)
                    install_packages "$pkg_manager" texlive texlive-latex-extra
                    ;;
                brew)
                    install_packages "$pkg_manager" texlive
                    ;;
                dnf)
                    install_packages "$pkg_manager" texlive-latex texlive-collection-latexextra
                    ;;
            esac
            ;;
        xelatex)
            case "$pkg_manager" in
                apt-get)
                    install_packages "$pkg_manager" texlive-xetex
                    ;;
                apk)
                    install_packages "$pkg_manager" texlive texlive-xetex
                    ;;
                brew)
                    install_packages "$pkg_manager" texlive
                    ;;
                dnf)
                    install_packages "$pkg_manager" texlive-xetex
                    ;;
            esac
            ;;
        lualatex)
            case "$pkg_manager" in
                apt-get)
                    # Need texlive-latex-base for the lualatex symlink
                    install_packages "$pkg_manager" texlive-luatex texlive-latex-base
                    ;;
                apk)
                    install_packages "$pkg_manager" texlive texlive-luatex
                    ;;
                brew)
                    install_packages "$pkg_manager" texlive
                    ;;
                dnf)
                    install_packages "$pkg_manager" texlive-luatex
                    ;;
            esac
            ;;
    esac
}

# Install Python 3.12+ on apt-get systems
# Tries: python3.12 package, deadsnakes PPA, or fails
install_python312_apt() {
    # First check if python3.12 or newer is already available
    if command -v python3.12 >/dev/null 2>&1; then
        log_success "Python 3.12 already installed"
        return 0
    fi

    # Check if system python3 is already 3.12+
    if command -v python3 >/dev/null 2>&1; then
        local ver
        ver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        local major="${ver%%.*}"
        local minor="${ver#*.}"
        if [ "$major" -ge 3 ] && [ "$minor" -ge 12 ] 2>/dev/null; then
            log_success "Python $ver already meets requirements"
            return 0
        fi
    fi

    # Try to install python3.12 from standard repos
    log_info "Checking for Python 3.12 in repositories..."
    if apt-cache show python3.12 >/dev/null 2>&1; then
        log_info "Installing python3.12 from repositories..."
        $SUDO apt-get install -y python3.12 python3.12-venv python3-pip || {
            log_warning "Failed to install python3.12 from repos"
        }
        if command -v python3.12 >/dev/null 2>&1; then
            # Update alternatives to make python3.12 the default python3
            $SUDO update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 2>/dev/null || true
            log_success "Python 3.12 installed from repositories"
            return 0
        fi
    fi

    # Try deadsnakes PPA (Ubuntu only) - uses less disk space than building from source
    if [ -f /etc/lsb-release ] && grep -q "Ubuntu" /etc/lsb-release 2>/dev/null; then
        log_info "Adding deadsnakes PPA for Python 3.12..."
        # Clean apt cache to save disk space before installing
        $SUDO apt-get clean >/dev/null 2>&1 || true
        # Install software-properties-common for add-apt-repository
        if $SUDO apt-get install -y software-properties-common 2>&1; then
            # Clean cache after install
            $SUDO apt-get clean >/dev/null 2>&1 || true
            if $SUDO add-apt-repository -y ppa:deadsnakes/ppa 2>&1; then
                $SUDO apt-get update 2>&1 || true
                if $SUDO apt-get install -y python3.12 python3.12-venv 2>&1; then
                    # Clean cache after install
                    $SUDO apt-get clean >/dev/null 2>&1 || true
                    # Update alternatives to prefer Python 3.12
                    $SUDO update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 2>/dev/null || true
                    log_success "Python 3.12 installed from deadsnakes PPA"
                    return 0
                else
                    log_warning "Failed to install Python 3.12 from deadsnakes"
                fi
            else
                log_warning "Failed to add deadsnakes PPA"
            fi
        else
            log_warning "Failed to install software-properties-common"
        fi
    fi

    # Build Python 3.12 from source (Debian and Ubuntu fallback)
    log_info "Attempting to build Python 3.12 from source..."
    local python_version="3.12.8"
    local tmp_dir
    tmp_dir=$(mktemp -d)

    # Install build dependencies (need apt-get update first)
    $SUDO apt-get update >/dev/null 2>&1 || true
    # Note: libncurses-dev works on newer Ubuntu, libncurses5-dev on older
    $SUDO apt-get install -y build-essential zlib1g-dev libncurses-dev \
        libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev \
        libsqlite3-dev wget libbz2-dev 2>&1 || {
        log_warning "Failed to install build dependencies"
        rm -rf "$tmp_dir"
        return 1
    }

    # Download and build Python
    cd "$tmp_dir" || return 1
    if curl -fsSL "https://www.python.org/ftp/python/${python_version}/Python-${python_version}.tgz" -o python.tgz; then
        tar -xzf python.tgz
        cd "Python-${python_version}" || return 1
        ./configure --enable-optimizations --prefix=/usr/local >/dev/null 2>&1
        make -j"$(nproc)" >/dev/null 2>&1
        $SUDO make altinstall >/dev/null 2>&1
        cd /
        rm -rf "$tmp_dir"

        # Check if python3.12 was installed (use explicit path since /usr/local/bin may not be in PATH)
        if [ -x /usr/local/bin/python3.12 ]; then
            # Ensure pip is bootstrapped
            /usr/local/bin/python3.12 -m ensurepip --upgrade 2>/dev/null || true
            # Create symlinks for easier access
            $SUDO ln -sf /usr/local/bin/python3.12 /usr/bin/python3.12 2>/dev/null || true
            $SUDO ln -sf /usr/local/bin/pip3.12 /usr/bin/pip3.12 2>/dev/null || true
            $SUDO update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.12 1 2>/dev/null || true
            log_success "Python 3.12 built from source"
            return 0
        elif command -v python3.12 >/dev/null 2>&1; then
            $SUDO update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.12 1 2>/dev/null || true
            log_success "Python 3.12 built from source"
            return 0
        fi
    fi

    rm -rf "$tmp_dir"
    log_error "Failed to install Python 3.12+"
    return 1
}

# Install Node.js 18+ on apt-get systems via NodeSource
install_nodejs18_apt() {
    # Check if node 18+ is already available
    if command -v node >/dev/null 2>&1; then
        local ver
        ver=$(node --version 2>/dev/null | sed 's/^v//' || echo "0.0.0")
        local major="${ver%%.*}"
        if [ "$major" -ge 18 ] 2>/dev/null; then
            log_success "Node.js $ver already meets requirements"
            return 0
        fi
    fi

    # Install via NodeSource (Node.js 22 LTS)
    log_info "Setting up NodeSource repository for Node.js 22..."

    # NodeSource setup requires curl
    if ! command -v curl >/dev/null 2>&1; then
        $SUDO apt-get install -y curl >/dev/null 2>&1 || {
            log_error "Failed to install curl (required for NodeSource)"
            return 1
        }
    fi

    # Download NodeSource setup script and run it
    # (Using temp file to avoid pipe issues with SUDO expansion)
    local tmp_setup
    tmp_setup=$(mktemp)
    if curl -fsSL https://deb.nodesource.com/setup_22.x -o "$tmp_setup" 2>/dev/null; then
        if [ -n "$SUDO" ]; then
            $SUDO -E bash "$tmp_setup" >/dev/null 2>&1 || {
                rm -f "$tmp_setup"
                log_warning "Failed to setup NodeSource repository"
                return 1
            }
        else
            bash "$tmp_setup" >/dev/null 2>&1 || {
                rm -f "$tmp_setup"
                log_warning "Failed to setup NodeSource repository"
                return 1
            }
        fi
        rm -f "$tmp_setup"

        $SUDO apt-get install -y nodejs >/dev/null 2>&1 || {
            log_warning "Failed to install Node.js from NodeSource"
            return 1
        }
        # Clean up apt cache
        $SUDO apt-get clean >/dev/null 2>&1 || true
        if command -v node >/dev/null 2>&1; then
            local installed_ver
            installed_ver=$(node --version 2>/dev/null || echo "unknown")
            log_success "Node.js $installed_ver installed from NodeSource"
            return 0
        fi
    else
        rm -f "$tmp_setup" 2>/dev/null || true
        log_warning "Failed to download NodeSource setup script"
    fi

    log_error "Failed to install Node.js 18+"
    return 1
}

# Install essential tools needed for the rest of the installation
install_essential_tools() {
    local pkg_manager="$1"

    log_info "Installing essential tools (curl, bash)..."

    case "$pkg_manager" in
        apt-get)
            # Clean apt cache first to save disk space
            $SUDO apt-get clean >/dev/null 2>&1 || true
            $SUDO rm -rf /var/lib/apt/lists/* 2>/dev/null || true
            # Always update apt lists first
            $SUDO apt-get update >/dev/null 2>&1 || true
            # Install curl (needed for downloading binaries)
            if ! command -v curl >/dev/null 2>&1; then
                $SUDO apt-get install -y curl >/dev/null 2>&1 || {
                    log_warning "Failed to install curl, binary downloads may fail"
                }
            fi
            ;;
        apk)
            # Install bash (needed for this script) and curl (needed for downloads)
            $SUDO apk update >/dev/null 2>&1 || true
            $SUDO apk add bash curl >/dev/null 2>&1 || {
                log_warning "Failed to install bash/curl"
            }
            ;;
        dnf)
            # Install curl (needed for downloading binaries)
            if ! command -v curl >/dev/null 2>&1; then
                $SUDO dnf install -y curl >/dev/null 2>&1 || {
                    log_warning "Failed to install curl, binary downloads may fail"
                }
            fi
            ;;
        brew)
            # macOS should have curl by default
            ;;
    esac
}

# Main installation logic
main() {
    # Detect platform first (before any other output)
    # Note: detect_platform sets PKG_MANAGER variable directly to avoid
    # command substitution capturing error messages
    detect_platform

    log_info "Starting dependency installation..."
    log_info "Detected platform: $PKG_MANAGER"

    # Calculate script directory once (after platform detection)
    # Use bash parameter expansion instead of dirname for portability
    local script_path="${BASH_SOURCE[0]}"
    SCRIPT_DIR="$(cd "${script_path%/*}" && pwd)"

    # Track critical installation failures
    local install_failures=0

    # Check for sudo
    check_sudo "$PKG_MANAGER"

    # Install essential tools (curl, bash) needed for the rest of the installation
    install_essential_tools "$PKG_MANAGER"

    # Install Python 3.12+ (unless skipped)
    if [ "${SKIP_PYTHON:-false}" = "true" ]; then
        log_info "Skipping Python installation"
    else
        log_info "Installing Python 3.12+..."
        case "$PKG_MANAGER" in
            apt-get)
                # Install Python 3.12+ (standard python3 may be too old on some distros)
                install_python312_apt || {
                    log_warning "Falling back to system python3"
                    install_packages "$PKG_MANAGER" python3 python3-pip
                }
                # Ensure pip is installed
                install_packages "$PKG_MANAGER" python3-pip 2>/dev/null || true
                ;;
            apk)
                install_packages "$PKG_MANAGER" python3 py3-pip
                ;;
            brew)
                install_packages "$PKG_MANAGER" python@3.12
                ;;
            dnf)
                install_packages "$PKG_MANAGER" python3 python3-pip
                ;;
        esac
    fi

    # Install Node.js 18+ (unless skipped)
    if [ "${SKIP_NODE:-false}" = "true" ]; then
        log_info "Skipping Node.js installation"
    else
        log_info "Installing Node.js 18+..."
        case "$PKG_MANAGER" in
            apt-get)
                # Use NodeSource to get Node.js 18+ (system packages are too old)
                install_nodejs18_apt || {
                    log_warning "Falling back to system nodejs"
                    install_packages "$PKG_MANAGER" nodejs npm
                }
                ;;
            apk)
                install_packages "$PKG_MANAGER" nodejs npm
                ;;
            brew)
                install_packages "$PKG_MANAGER" node
                ;;
            dnf)
                install_packages "$PKG_MANAGER" nodejs npm
                ;;
        esac
    fi

    # Install Pandoc 3.9+ (3.9 adds +alerts extension for GFM callouts; 3.8.2.1 fixed #11201)
    log_info "Installing Pandoc 3.9+..."

    # Check if package manager has a sufficient version BEFORE installing
    if check_pandoc_pkg_version "$PKG_MANAGER" 3 9 0; then
        log_info "Package manager has Pandoc >= 3.9, installing from package manager..."
        install_packages "$PKG_MANAGER" pandoc
    else
        log_info "Package manager Pandoc is too old or unavailable, installing from GitHub releases..."
        install_pandoc_binary || {
            log_error "Failed to install Pandoc from binary"
            exit 1
        }
    fi

    # Verify Pandoc installation
    if ! command -v pandoc >/dev/null 2>&1; then
        log_error "Pandoc installation failed: pandoc binary not found in PATH"
        install_failures=$((install_failures + 1))
    fi

    # Install LaTeX engine
    LATEX_ENGINE=$(get_latex_engine)
    install_latex_engine "$PKG_MANAGER" "$LATEX_ENGINE"

    # Verify LaTeX engine installation
    if ! command -v "$LATEX_ENGINE" >/dev/null 2>&1; then
        log_error "LaTeX engine installation failed: $LATEX_ENGINE binary not found in PATH"
        install_failures=$((install_failures + 1))
    fi

    # Install librsvg
    log_info "Installing librsvg..."
    case "$PKG_MANAGER" in
        apt-get)
            install_packages "$PKG_MANAGER" librsvg2-bin
            ;;
        apk)
            install_packages "$PKG_MANAGER" librsvg
            ;;
        brew)
            install_packages "$PKG_MANAGER" librsvg
            ;;
        dnf)
            install_packages "$PKG_MANAGER" librsvg2-tools
            ;;
    esac

    # Verify librsvg installation
    if ! command -v rsvg-convert >/dev/null 2>&1; then
        log_error "librsvg installation failed: rsvg-convert binary not found in PATH"
        install_failures=$((install_failures + 1))
    fi

    # Exit early if critical dependencies failed (before installing optional
    # dependencies like python-frontmatter, mermaid-cli, and chromium)
    if [ "$install_failures" -gt 0 ]; then
        log_error "Critical dependency installation failed ($install_failures components)"
        exit 1
    fi

    # Install python-frontmatter (unless Python is skipped)
    if [ "${SKIP_PYTHON:-false}" != "true" ]; then
        log_info "Installing python-frontmatter via pip..."
        local installed=false

        # Use python3 (what tests/users will actually call) - requirement is 3.12+
        # Only fall back to specific version if python3 doesn't exist
        local python_exe=""
        if command -v python3 >/dev/null 2>&1; then
            python_exe="python3"
        elif [ -x /usr/local/bin/python3.12 ]; then
            python_exe="/usr/local/bin/python3.12"
        elif command -v python3.12 >/dev/null 2>&1; then
            python_exe="python3.12"
        fi

        if [ -n "$python_exe" ]; then
            # Ensure pip is available for this Python
            $python_exe -m ensurepip --upgrade 2>/dev/null || true

            # Try to install python-frontmatter
            if $python_exe -m pip install python-frontmatter 2>/dev/null; then
                installed=true
                log_success "python-frontmatter installed"
            elif $python_exe -m pip install --user python-frontmatter 2>/dev/null; then
                installed=true
                log_success "python-frontmatter installed (user)"
            elif $python_exe -m pip install --break-system-packages python-frontmatter 2>/dev/null; then
                installed=true
                log_success "python-frontmatter installed (break-system-packages)"
            fi
        fi

        # Fallback to pip3 if python executable method failed
        if [ "$installed" = "false" ] && command -v pip3 >/dev/null 2>&1; then
            if pip3 install python-frontmatter 2>/dev/null; then
                installed=true
                log_success "python-frontmatter installed (pip3)"
            elif pip3 install --user python-frontmatter 2>/dev/null; then
                installed=true
                log_success "python-frontmatter installed (pip3 --user)"
            elif pip3 install --break-system-packages python-frontmatter 2>/dev/null; then
                installed=true
                log_success "python-frontmatter installed (pip3 --break-system-packages)"
            fi
        fi

        if [ "$installed" = "false" ]; then
            log_warning "Failed to install python-frontmatter via pip"
        fi
    fi

    # Install @mermaid-js/mermaid-cli (unless Node is skipped)
    if [ "${SKIP_NODE:-false}" != "true" ]; then
        log_info "Installing @mermaid-js/mermaid-cli via npm..."
        if command -v npm >/dev/null 2>&1; then
            $SUDO npm install -g @mermaid-js/mermaid-cli || {
                log_warning "Failed to install @mermaid-js/mermaid-cli via npm"
            }
        else
            log_warning "npm not found, skipping mermaid-cli installation"
        fi
    fi

    # Configure Chromium (unless skipped)
    if [ "${SKIP_CHROMIUM:-false}" = "true" ]; then
        log_info "Skipping Chromium configuration"
    else
        log_info "Installing Chromium dependencies..."
        # Install Puppeteer/Playwright dependencies for headless Chrome
        case "$PKG_MANAGER" in
            apt-get)
                # Detect correct ALSA package name (Ubuntu 24.04+ uses libasound2t64)
                local alsa_pkg="libasound2"
                if ! apt-cache show libasound2 >/dev/null 2>&1 && apt-cache show libasound2t64 >/dev/null 2>&1; then
                    alsa_pkg="libasound2t64"
                fi
                # Core Chromium dependencies for Puppeteer/Playwright
                install_packages "$PKG_MANAGER" \
                    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
                    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
                    libxdamage1 libxfixes3 libxrandr2 libgbm1 "$alsa_pkg" \
                    libpango-1.0-0 libcairo2 2>/dev/null || {
                    log_warning "Some Chromium dependencies may be missing"
                }
                ;;
            apk)
                install_packages "$PKG_MANAGER" \
                    chromium nss freetype harfbuzz ca-certificates ttf-freefont 2>/dev/null || {
                    log_warning "Some Chromium dependencies may be missing"
                }
                ;;
            dnf)
                install_packages "$PKG_MANAGER" \
                    nss nspr atk at-spi2-atk cups-libs libdrm \
                    libxkbcommon libXcomposite libXdamage libXrandr \
                    mesa-libgbm alsa-lib pango cairo 2>/dev/null || {
                    log_warning "Some Chromium dependencies may be missing"
                }
                ;;
        esac

        log_info "Configuring Chromium..."
        if [ -f "$SCRIPT_DIR/configure-chromium.sh" ]; then
            "$SCRIPT_DIR/configure-chromium.sh" --auto || {
                log_warning "Chromium configuration failed or was skipped"
            }
        else
            log_warning "configure-chromium.sh not found at $SCRIPT_DIR/configure-chromium.sh"
        fi
    fi

    # Run verification
    log_info "Running verification..."

    # Check for verify-deps.sh in current directory first (for testing), then script directory
    local verify_script=""
    if [ -f "./scripts/verify-deps.sh" ]; then
        verify_script="./scripts/verify-deps.sh"
    elif [ -f "$SCRIPT_DIR/verify-deps.sh" ]; then
        verify_script="$SCRIPT_DIR/verify-deps.sh"
    fi

    if [ -n "$verify_script" ]; then
        if "$verify_script"; then
            log_success "All dependencies installed successfully"
            exit 0
        else
            log_error "Verification failed. Some dependencies may not be properly installed."
            exit 5
        fi
    else
        log_warning "verify-deps.sh not found at $SCRIPT_DIR/verify-deps.sh, skipping verification"
        log_success "Installation completed (verification skipped)"
        exit 0
    fi
}

# Run main function
main "$@"
