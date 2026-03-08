#!/bin/bash
# Dependency verification script for CoSAI Whitepaper Converter
# Checks all required dependencies with version validation

# Track failures (don't exit early - check everything)
FAILURES=0

# Determine project root (script lives at scripts/verify-deps.sh)
# Use bash parameter expansion instead of dirname for portability
_verify_script_path="${BASH_SOURCE[0]}"
_verify_script_dir="$(cd "${_verify_script_path%/*}" && pwd)"
VERIFY_PROJECT_ROOT="$(cd "$_verify_script_dir/.." 2>/dev/null && pwd)" || VERIFY_PROJECT_ROOT=""

# Helper function to extract version number from string
# Usage: extract_version "Python 3.14.0" -> "3.14.0"
#        extract_version "pandoc 3.8.2.1" -> "3.8.2.1"
extract_version() {
    local input="$1"
    local result=""

    # Remove leading non-digit characters and extract version pattern
    # Supports X.Y, X.Y.Z, and X.Y.Z.W (e.g. Pandoc 3.8.2.1)
    if [[ "$input" =~ ([0-9]+\.[0-9]+(\.[0-9]+){0,2}) ]]; then
        result="${BASH_REMATCH[1]}"
    fi

    echo "$result"
}

# Helper function to extract first line from multi-line string
get_first_line() {
    local input="$1"
    echo "${input%%$'\n'*}"
}

# Helper function to check version comparison
# Usage: version_ge "actual_version" "required_version"
# Returns 0 if actual >= required, 1 otherwise
# Supports up to 4-part versions (X.Y.Z.W), e.g. "3.8.2.1"
version_ge() {
    local actual="$1"
    local required="$2"

    # Split versions into arrays using IFS
    local IFS='.'
    local -a actual_parts=($actual)
    local -a required_parts=($required)

    # Compare up to 4 parts
    local i
    for i in 0 1 2 3; do
        local a="${actual_parts[$i]:-0}"
        local r="${required_parts[$i]:-0}"
        # Remove any non-numeric characters
        a="${a//[!0-9]/}"
        r="${r//[!0-9]/}"
        [ -z "$a" ] && a=0
        [ -z "$r" ] && r=0

        if [ "$a" -gt "$r" ]; then
            return 0
        elif [ "$a" -lt "$r" ]; then
            return 1
        fi
    done

    # All parts equal
    return 0
}

# Check Python 3.12+
# Honor SKIP_PYTHON environment variable
if [ "${SKIP_PYTHON:-false}" = "true" ]; then
    echo "[~] Python check skipped (SKIP_PYTHON=true)"
else
    # Clear shell hash table to pick up newly installed binaries
    hash -r 2>/dev/null || true

    # Check multiple Python paths (prefer python3.12 if available)
    PYTHON_CMD=""
    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
    elif [ -x "/usr/local/bin/python3.12" ]; then
        PYTHON_CMD="/usr/local/bin/python3.12"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    fi

    if [ -n "$PYTHON_CMD" ]; then
        python_version=$($PYTHON_CMD --version 2>&1)
        if [ $? -eq 0 ]; then
            # Extract version from "Python 3.14.0" format
            python_ver=$(extract_version "$python_version")
            if [ -n "$python_ver" ]; then
                if version_ge "$python_ver" "3.12"; then
                    echo "[✓] Python $python_ver (requires 3.12+)"
                else
                    echo "[✗] Python $python_ver (requires 3.12+) - version too low"
                    FAILURES=$((FAILURES + 1))
                fi
            else
                echo "[✗] Python version could not be determined"
                FAILURES=$((FAILURES + 1))
            fi
        else
            echo "[✗] Python command failed"
            FAILURES=$((FAILURES + 1))
        fi
    else
        echo "[✗] Python not found (requires 3.12+)"
        FAILURES=$((FAILURES + 1))
    fi
fi

# Check Node.js 20+
# Honor SKIP_NODE environment variable
if [ "${SKIP_NODE:-false}" = "true" ]; then
    echo "[~] Node.js check skipped (SKIP_NODE=true)"
else
    if command -v node &> /dev/null; then
        node_version=$(node --version 2>&1)
        if [ $? -eq 0 ]; then
            # Extract version from "v20.10.0" format
            node_ver=$(extract_version "$node_version")
            if [ -n "$node_ver" ]; then
                if version_ge "$node_ver" "20.0"; then
                    echo "[✓] Node.js $node_ver (requires 20+)"
                else
                    echo "[✗] Node.js $node_ver (requires 20+) - version too low"
                    FAILURES=$((FAILURES + 1))
                fi
            else
                echo "[✗] Node.js version could not be determined"
                FAILURES=$((FAILURES + 1))
            fi
        else
            echo "[✗] Node.js command failed"
            FAILURES=$((FAILURES + 1))
        fi
    else
        echo "[✗] Node.js not found (requires 20+)"
        FAILURES=$((FAILURES + 1))
    fi
fi

# Check Pandoc 3.9+ (3.9 adds +alerts extension for GFM callouts)
if command -v pandoc &> /dev/null; then
    pandoc_version=$(pandoc --version 2>&1)
    if [ $? -eq 0 ]; then
        # Extract version from "pandoc 3.1.11" format (first line only)
        pandoc_first_line=$(get_first_line "$pandoc_version")
        pandoc_ver=$(extract_version "$pandoc_first_line")
        if [ -n "$pandoc_ver" ]; then
            if version_ge "$pandoc_ver" "3.9"; then
                echo "[✓] Pandoc $pandoc_ver (requires 3.9+)"
            else
                echo "[✗] Pandoc $pandoc_ver (requires 3.9+) - version too low"
                FAILURES=$((FAILURES + 1))
            fi
        else
            echo "[✗] Pandoc version could not be determined"
            FAILURES=$((FAILURES + 1))
        fi
    else
        echo "[✗] Pandoc command failed"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo "[✗] Pandoc not found (requires 3.9+)"
    FAILURES=$((FAILURES + 1))
fi

# Detect LaTeX engine
# Priority: LATEX_ENGINE env var > converter_config.json > default (tectonic)
LATEX_ENGINE="${LATEX_ENGINE:-}"

if [ -z "$LATEX_ENGINE" ] && [ -f "converter_config.json" ]; then
    # Read config file content using bash
    config_content=""
    if [ -r "converter_config.json" ]; then
        while IFS= read -r line || [ -n "$line" ]; do
            config_content+="$line"
        done < "converter_config.json"
    fi

    # Look for "latex_engine": "value" pattern
    if [[ "$config_content" =~ \"latex_engine\"[[:space:]]*:[[:space:]]*\"([^\"]+)\" ]]; then
        LATEX_ENGINE_TMP="${BASH_REMATCH[1]}"
        # Validate that the result is a valid engine name
        # Valid engines: tectonic, pdflatex, xelatex, lualatex
        case "$LATEX_ENGINE_TMP" in
            tectonic|pdflatex|xelatex|lualatex)
                LATEX_ENGINE="$LATEX_ENGINE_TMP"
                ;;
        esac
    fi

    # If bash parsing failed and python is available, try Python
    if [ -z "$LATEX_ENGINE" ] && command -v python3 &> /dev/null; then
        LATEX_ENGINE_TMP=$(python3 -c "import json; data=json.load(open('converter_config.json')); print(data.get('latex_engine', ''))" 2>/dev/null || echo "")
        # Validate that the result is a valid engine name (not a version string or error)
        case "$LATEX_ENGINE_TMP" in
            tectonic|pdflatex|xelatex|lualatex)
                LATEX_ENGINE="$LATEX_ENGINE_TMP"
                ;;
        esac
    fi
fi

# Default to tectonic if still empty
if [ -z "$LATEX_ENGINE" ]; then
    LATEX_ENGINE="tectonic"
fi

# Check LaTeX engine
if command -v "$LATEX_ENGINE" &> /dev/null; then
    engine_version=$("$LATEX_ENGINE" --version 2>&1)
    if [ $? -eq 0 ]; then
        # Extract version number if present
        engine_first_line=$(get_first_line "$engine_version")
        engine_ver=$(extract_version "$engine_first_line")
        if [ -n "$engine_ver" ]; then
            echo "[✓] $LATEX_ENGINE $engine_ver"
        else
            # Some engines may not have clear version format
            echo "[✓] $LATEX_ENGINE available"
        fi
    else
        echo "[✗] $LATEX_ENGINE command failed"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo "[✗] $LATEX_ENGINE not found"
    FAILURES=$((FAILURES + 1))
fi

# Check Chromium configuration
# Use configure-chromium.sh --check if available
# Honor SKIP_CHROMIUM environment variable
CHROMIUM_CHECK_PASSED=0

if [ "${SKIP_CHROMIUM:-false}" = "true" ]; then
    echo "[~] Chromium check skipped (SKIP_CHROMIUM=true)"
    CHROMIUM_CHECK_PASSED=1
else
    # Find configure-chromium.sh (try multiple locations)
    CHROMIUM_SCRIPT=""
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    for path in "$SCRIPT_DIR/configure-chromium.sh" "scripts/configure-chromium.sh" "./configure-chromium.sh"; do
        if [ -f "$path" ]; then
            CHROMIUM_SCRIPT="$path"
            break
        fi
    done

    if [ -n "$CHROMIUM_SCRIPT" ]; then
        # Run configure-chromium.sh --check to verify chromium is configured
        if [ -x "$CHROMIUM_SCRIPT" ]; then
            if "$CHROMIUM_SCRIPT" --check &> /dev/null; then
                echo "[✓] Chromium configured"
                CHROMIUM_CHECK_PASSED=1
            else
                echo "[✗] Chromium not configured"
                FAILURES=$((FAILURES + 1))
            fi
        else
            # Try with bash if not executable
            if bash "$CHROMIUM_SCRIPT" --check &> /dev/null; then
                echo "[✓] Chromium configured"
                CHROMIUM_CHECK_PASSED=1
            else
                echo "[✗] Chromium not configured"
                FAILURES=$((FAILURES + 1))
            fi
        fi
    elif command -v chromium &> /dev/null || command -v chromium-browser &> /dev/null; then
        echo "[✓] Chromium available"
        CHROMIUM_CHECK_PASSED=1
    else
        # If configure-chromium.sh doesn't exist and chromium is not in PATH,
        # we still need to report on Chromium status
        echo "[✗] Chromium not found"
        FAILURES=$((FAILURES + 1))
    fi
fi

# Check python-frontmatter package
# Honor SKIP_PYTHON environment variable
# Check .venv first (non-root installs use venv), then fall back to system pip
if [ "${SKIP_PYTHON:-false}" = "true" ]; then
    echo "[~] python-frontmatter check skipped (SKIP_PYTHON=true)"
else
    # Try venv pip first, then system pip
    pip_cmd=""
    if [ -n "$VERIFY_PROJECT_ROOT" ] && [ -x "$VERIFY_PROJECT_ROOT/.venv/bin/pip" ]; then
        pip_cmd="$VERIFY_PROJECT_ROOT/.venv/bin/pip"
    elif command -v python3 &> /dev/null; then
        pip_cmd="python3 -m pip"
    elif [ -x /usr/local/bin/python3.12 ]; then
        pip_cmd="/usr/local/bin/python3.12 -m pip"
    elif command -v python3.12 &> /dev/null; then
        pip_cmd="python3.12 -m pip"
    elif command -v pip3 &> /dev/null; then
        pip_cmd="pip3"
    fi

    if [ -n "$pip_cmd" ]; then
        pip_output=$($pip_cmd show python-frontmatter 2>&1)
        if [ $? -eq 0 ]; then
            # Extract version from pip show output
            # Look for "Version: X.Y.Z" line
            fm_version=""
            while IFS= read -r line; do
                if [[ "$line" =~ ^Version:[[:space:]]*(.+)$ ]]; then
                    fm_version="${BASH_REMATCH[1]}"
                    # Trim whitespace
                    fm_version="${fm_version#"${fm_version%%[![:space:]]*}"}"
                    fm_version="${fm_version%"${fm_version##*[![:space:]]}"}"
                    break
                fi
            done <<< "$pip_output"

            if [ -n "$fm_version" ]; then
                echo "[✓] python-frontmatter $fm_version"
            else
                echo "[✓] python-frontmatter installed"
            fi
        else
            echo "[✗] python-frontmatter not found"
            FAILURES=$((FAILURES + 1))
        fi
    else
        echo "[✗] pip not found (cannot verify python-frontmatter)"
        FAILURES=$((FAILURES + 1))
    fi
fi

# Check rsvg-convert
if command -v rsvg-convert &> /dev/null; then
    rsvg_version=$(rsvg-convert --version 2>&1)
    if [ $? -eq 0 ]; then
        # Extract version from output
        rsvg_ver=$(extract_version "$rsvg_version")
        if [ -n "$rsvg_ver" ]; then
            echo "[✓] rsvg-convert $rsvg_ver"
        else
            echo "[✓] rsvg-convert available"
        fi
    else
        echo "[✗] rsvg-convert command failed"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo "[✗] rsvg-convert not found"
    FAILURES=$((FAILURES + 1))
fi

# Check mermaid-cli (local node_modules or global install)
# Does NOT auto-download — verify-deps.sh must be idempotent and non-modifying
# NOTE: convert.py invokes mermaid-cli via 'npx -y @mermaid-js/mermaid-cli', which
# finds local node_modules/.bin/mmdc automatically if present (npx resolution order)
# Honor SKIP_NODE environment variable (mermaid-cli requires Node.js)
if [ "${SKIP_NODE:-false}" = "true" ]; then
    echo "[~] mermaid-cli check skipped (SKIP_NODE=true)"
else
    mermaid_found=false

    # Check local node_modules first (from npm install in project root)
    if [ -n "$VERIFY_PROJECT_ROOT" ] && [ -x "$VERIFY_PROJECT_ROOT/node_modules/.bin/mmdc" ]; then
        mermaid_check=$("$VERIFY_PROJECT_ROOT/node_modules/.bin/mmdc" --version 2>&1)
        if [ $? -eq 0 ]; then
            mermaid_ver=$(extract_version "$mermaid_check")
            if [ -n "$mermaid_ver" ]; then
                echo "[✓] mermaid-cli $mermaid_ver"
            else
                echo "[✓] mermaid-cli available"
            fi
            mermaid_found=true
        fi
    fi

    # Check global install
    if [ "$mermaid_found" = "false" ] && command -v mmdc &> /dev/null; then
        mermaid_check=$(mmdc --version 2>&1)
        if [ $? -eq 0 ]; then
            mermaid_ver=$(extract_version "$mermaid_check")
            if [ -n "$mermaid_ver" ]; then
                echo "[✓] mermaid-cli $mermaid_ver"
            else
                echo "[✓] mermaid-cli available"
            fi
            mermaid_found=true
        fi
    fi

    if [ "$mermaid_found" = "false" ]; then
        echo "[✗] mermaid-cli not found (install via 'npm install' or 'npm install -g @mermaid-js/mermaid-cli')"
        FAILURES=$((FAILURES + 1))
    fi
fi

# Exit with appropriate code
if [ $FAILURES -eq 0 ]; then
    exit 0
else
    exit 1
fi
