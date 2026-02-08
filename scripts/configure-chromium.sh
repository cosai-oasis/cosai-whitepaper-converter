#!/bin/bash
# Configure Chrome/Chromium for Mermaid diagram rendering via Puppeteer
# Usage: ./configure-chromium.sh [--auto] [--install-playwright] [--help]

set -e

# =============================================================================
# Platform Detection and Chrome Configuration
# =============================================================================

# Detect platform for Chrome/Chromium configuration
detect_platform() {
    local os=$(uname -s)
    local arch=$(uname -m)

    case "$os" in
        Darwin*) PLATFORM="mac" ;;
        MINGW*|CYGWIN*|MSYS*) PLATFORM="windows" ;;
        Linux*)
            case "$arch" in
                aarch64|arm64) PLATFORM="linux-arm64" ;;
                *) PLATFORM="linux-x64" ;;
            esac ;;
        *) PLATFORM="unknown" ;;
    esac

    echo "🔍 Detected platform: $PLATFORM"
}

# Get the project root directory (where assets/ is located)
get_project_root() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # If we're in scripts/, go up one level
    if [[ "$(basename "$script_dir")" == "scripts" ]]; then
        PROJECT_ROOT="$(dirname "$script_dir")"
    else
        # Assume we're already in project root
        PROJECT_ROOT="$script_dir"
    fi

    # Verify assets/ directory exists
    if [[ ! -d "$PROJECT_ROOT/assets" ]]; then
        echo "⚠️  Warning: assets/ directory not found at $PROJECT_ROOT/assets"
        echo "   Creating it..."
        mkdir -p "$PROJECT_ROOT/assets"
    fi
}

# Global install location for Playwright browsers (used when installing as root)
_PLAYWRIGHT_GLOBAL_PATH="/usr/local/share/playwright"

# Search known Playwright browser paths for a chromium binary.
# Checks /ms-playwright (devcontainer), global install path,
# $PLAYWRIGHT_BROWSERS_PATH, and $HOME/.cache/ms-playwright.
# Prefers headless_shell over chrome.
# Returns path via stdout (use in command substitution).
_search_playwright_binary() {
    local BROWSER_PATHS="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}"

    # Also check the global path used by devcontainer
    if [[ -d "/ms-playwright" ]]; then
        BROWSER_PATHS="/ms-playwright:$BROWSER_PATHS"
    fi

    # Also check the system-wide install location (used when installed as root)
    if [[ -d "$_PLAYWRIGHT_GLOBAL_PATH" ]]; then
        BROWSER_PATHS="$_PLAYWRIGHT_GLOBAL_PATH:$BROWSER_PATHS"
    fi

    local CHROME_EXEC=""
    for browser_path in ${BROWSER_PATHS//:/ }; do
        [[ ! -d "$browser_path" ]] && continue
        if [[ -z "$CHROME_EXEC" ]]; then
            CHROME_EXEC=$(find "$browser_path" -name "headless_shell" -type f 2>/dev/null | head -1)
        fi
        if [[ -z "$CHROME_EXEC" ]]; then
            CHROME_EXEC=$(find "$browser_path" -name "chrome" -type f 2>/dev/null | head -1)
        fi
    done

    echo "$CHROME_EXEC"
}

# Find Playwright's Chromium installation
find_playwright_chromium() {
    echo "📦 Checking for Playwright Chromium..."
    if ! npx --version </dev/null &>/dev/null; then
        echo "❌ npx not found. Please install Node.js first."
        exit 1
    fi

    # Search for existing chromium binary first
    local playwright_path
    playwright_path=$(_search_playwright_binary)

    # If binary not found and we're allowed to install, do so
    if [[ -z "$playwright_path" || ! -x "$playwright_path" ]] && [[ "$INSTALL_PLAYWRIGHT" == "true" ]]; then
        # When running as root (e.g., during Docker build), install to a globally
        # accessible location so non-root users can access the browser at runtime.
        # Without this, Playwright installs to /root/.cache/ms-playwright/ which
        # is inaccessible to non-root users due to /root/ having mode 700.
        if [[ "${EUID:-$(id -u)}" == "0" ]]; then
            export PLAYWRIGHT_BROWSERS_PATH="$_PLAYWRIGHT_GLOBAL_PATH"
            echo "   Installing to global path: $PLAYWRIGHT_BROWSERS_PATH"
        fi
        echo "   Playwright Chromium binary not found. Installing..."
        if ! npx playwright install chromium --with-deps </dev/null; then
            echo "❌ Failed to install Playwright Chromium"
            echo "   Exiting..."
            exit 1
        fi
        echo "✅ Playwright Chromium installed"
        # Search again after installation
        playwright_path=$(_search_playwright_binary)
    fi

    if [[ -n "$playwright_path" && -x "$playwright_path" ]]; then
        CHROMIUM_PATH="$playwright_path"
        echo "✅ Found Playwright Chromium at: $playwright_path"
    else
        echo "   Playwright Chromium not found."
        echo "   Please install Playwright manually or run:"
        echo "   $0 --install-playwright"
        CHROMIUM_PATH=""
    fi
}

# Find system-installed Chromium
find_system_chromium() {
    # Try common system chromium locations
    local system_paths=(
        "/usr/bin/chromium"
        "/usr/bin/chromium-browser"
        "/snap/bin/chromium"
        "/usr/bin/google-chrome"
    )

    for path in "${system_paths[@]}"; do
        if [[ -x "$path" ]]; then
            CHROMIUM_PATH="$path"
            echo "✅ Found system Chromium at: $path"
            return
        fi
    done

    echo "⚠️  No system Chromium found in standard locations"
    echo "   You may need to install chromium: sudo apt install chromium-browser"
    CHROMIUM_PATH=""
}

# Configure Chrome/Chromium path based on platform and user preference
configure_chromium_path() {
    local chromium_path=""

    case "$PLATFORM" in
        "mac"|"windows"|"linux-x64")
            if [[ "$AUTO_MODE" == "true" ]]; then
                echo "✅ Using automatic Chrome detection (auto mode)"
                chromium_path=""
            else
                echo ""
                echo "🌐 Chrome Configuration"
                echo "For most users, mermaid-cli can use its bundled Chrome automatically."
                echo ""
                echo "Options:"
                echo "  1) Use automatic Chrome detection (recommended)"
                echo "  2) Specify custom Chrome/Chromium path"
                echo ""
                read -p "Choose option (1-2) [1]: " chrome_choice
                chrome_choice=${chrome_choice:-1}

                case "$chrome_choice" in
                    1)
                        echo "✅ Using automatic Chrome detection"
                        chromium_path=""
                        ;;
                    2)
                        echo ""
                        read -p "Enter full path to Chrome/Chromium executable: " custom_path
                        if [[ -x "$custom_path" ]]; then
                            chromium_path="$custom_path"
                            echo "✅ Using custom Chrome at: $custom_path"
                        else
                            echo "⚠️  Warning: Path '$custom_path' not found or not executable"
                            echo "   Falling back to automatic detection"
                            chromium_path=""
                        fi
                        ;;
                    *)
                        echo "Invalid choice. Using automatic detection."
                        chromium_path=""
                        ;;
                esac
            fi
            ;;

        "linux-arm64")
            if [[ "$AUTO_MODE" == "true" ]]; then
                echo "🤖 Auto mode: Using Playwright Chromium for ARM64 Linux"
                find_playwright_chromium
                chromium_path="$CHROMIUM_PATH"
            else
                echo ""
                echo "🚨 ARM64 Linux Detected"
                echo "Chrome/Chrome-for-testing are not available for ARM64 Linux from Google."
                echo "You need to provide an alternative Chromium installation."
                echo ""
                echo "Options:"
                echo "  1) Use Playwright's Chromium (recommended)"
                echo "  2) Use system-installed Chromium"
                echo "  3) Specify custom Chromium path"
                echo ""
                read -p "Choose option (1-3) [1]: " arm_choice
                arm_choice=${arm_choice:-1}

                case "$arm_choice" in
                    1)
                        find_playwright_chromium
                        chromium_path="$CHROMIUM_PATH"
                        ;;
                    2)
                        find_system_chromium
                        chromium_path="$CHROMIUM_PATH"
                        ;;
                    3)
                        echo ""
                        read -p "Enter full path to Chromium executable: " custom_path
                        if [[ -x "$custom_path" ]]; then
                            chromium_path="$custom_path"
                            echo "✅ Using custom Chromium at: $custom_path"
                        else
                            echo "❌ Error: Path '$custom_path' not found or not executable"
                            echo "   SVG generation will likely fail without a valid Chromium path"
                            chromium_path="$custom_path"  # Keep it anyway, user might fix later
                        fi
                        ;;
                    *)
                        echo "Invalid choice. Using Playwright Chromium option."
                        find_playwright_chromium
                        chromium_path="$CHROMIUM_PATH"
                        ;;
                esac
            fi
            ;;

        "unknown")
            echo "⚠️  Unknown platform. Chrome configuration may not work correctly."
            echo "   You may need to manually configure the executablePath in assets/puppeteerConfig.json."
            chromium_path=""
            ;;
    esac

    CHROMIUM_PATH="$chromium_path"
}

configure_puppeteer_config() {
    local config_path="$PROJECT_ROOT/assets/puppeteerConfig.json"

    if [[ -n "$CHROMIUM_PATH" ]]; then
        # Write config with executablePath
        cat <<EOF > "$config_path"
{
    "defaultViewport": null,
    "executablePath": "$CHROMIUM_PATH",
    "args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
}
EOF
        echo "✅ Wrote puppeteer config to: $config_path"
        echo "   Set executablePath to: $CHROMIUM_PATH"
    else
        # Write config without executablePath (auto-detection)
        cat <<EOF > "$config_path"
{
    "defaultViewport": null,
    "args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
}
EOF
        echo "✅ Wrote puppeteer config to: $config_path"
        echo "   Using automatic Chrome detection"
    fi
}

# Check if chromium is configured (for verify-deps.sh)
check_chromium_configured() {
    get_project_root
    local config_path="$PROJECT_ROOT/assets/puppeteerConfig.json"

    # Check if config file exists
    if [[ ! -f "$config_path" ]]; then
        echo "Chromium not configured: puppeteerConfig.json not found"
        exit 1
    fi

    # Try to extract executablePath from config
    local exec_path=""
    if command -v python3 &>/dev/null; then
        exec_path=$(python3 -c "import json; print(json.load(open('$config_path')).get('executablePath', ''))" 2>/dev/null || echo "")
    elif command -v node &>/dev/null; then
        exec_path=$(node -e "console.log(require('$config_path').executablePath || '')" 2>/dev/null || echo "")
    else
        # Fall back to grep parsing
        exec_path=$(grep -o '"executablePath"[[:space:]]*:[[:space:]]*"[^"]*"' "$config_path" 2>/dev/null | sed 's/.*:.*"\([^"]*\)".*/\1/' || echo "")
    fi

    # If executablePath is set, verify it exists
    if [[ -n "$exec_path" ]]; then
        if [[ -x "$exec_path" ]]; then
            echo "Chromium configured: $exec_path"
            exit 0
        else
            echo "Chromium not configured: executable not found at $exec_path"
            exit 1
        fi
    else
        # No executablePath means auto-detection mode
        # This is valid for mac/windows/linux-x64
        echo "Chromium configured: auto-detection mode"
        exit 0
    fi
}

# Parse command line arguments
INSTALL_PLAYWRIGHT=true
AUTO_MODE=false
CHECK_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --check)
            CHECK_MODE=true
            shift
            ;;
        --auto)
            AUTO_MODE=true
            shift
            ;;
        --install-playwright)
            INSTALL_PLAYWRIGHT=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--auto] [--install-playwright] [--check]"
            echo ""
            echo "Configure Chrome/Chromium for Mermaid diagram rendering."
            echo ""
            echo "Options:"
            echo "  --auto                  Non-interactive mode (for CI/devcontainer)"
            echo "                          Uses auto-detection on most platforms,"
            echo "                          Playwright Chromium on ARM64 Linux"
            echo "  --install-playwright    Automatically install Playwright Chromium"
            echo "                          if not found (for ARM64 Linux)"
            echo "  --check                 Check if Chromium is configured (for verify-deps.sh)"
            echo "                          Returns exit code 0 if configured, 1 if not"
            echo "  --help, -h              Show this help message"
            echo ""
            echo "This script configures Puppeteer to find Chrome/Chromium for rendering"
            echo "Mermaid diagrams. The configuration is written to assets/puppeteerConfig.json."
            echo ""
            echo "Platform behavior:"
            echo "  - Mac/Windows/Linux x64: Auto-detection works (recommended)"
            echo "  - ARM64 Linux: Requires Playwright Chromium or system Chromium"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Handle --check mode
if [[ "$CHECK_MODE" == "true" ]]; then
    check_chromium_configured
fi

# Main execution
get_project_root
echo "📁 Project root: $PROJECT_ROOT"

detect_platform
configure_chromium_path
configure_puppeteer_config

echo ""
echo "🎉 Configuration complete!"
