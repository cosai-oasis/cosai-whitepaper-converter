#!/usr/bin/env bash
#
# install.sh - Devcontainer feature entry point for CoSAI Whitepaper Converter
#
# This script is called by devcontainer CLI when the feature is installed.
# It maps devcontainer environment variables to install-deps.sh format and
# delegates installation to the main installation script.
#
# Exit codes:
#   0 - Success
#   1 - General error (file not found, invalid configuration)
#
# Environment Variable Flow:
# - Devcontainer passes options as: LATEXENGINE, SKIPCHROMIUM, SKIPPYTHON, SKIPNODE
# - This script maps them to: LATEX_ENGINE, SKIP_CHROMIUM, SKIP_PYTHON, SKIP_NODE
# - Then calls the install-deps.sh script which uses the underscored format

set -e

# Map devcontainer options to install-deps.sh environment variables
# Devcontainer passes camelCase options as UPPERCASE without underscores

# Validate LaTeX engine against allowed values
LATEX_ENGINE_CANDIDATE="${LATEXENGINE:-tectonic}"
case "${LATEX_ENGINE_CANDIDATE}" in
    tectonic|pdflatex|xelatex|lualatex)
        export LATEX_ENGINE="${LATEX_ENGINE_CANDIDATE}"
        ;;
    *)
        echo "Error: Invalid LATEX_ENGINE value: '${LATEX_ENGINE_CANDIDATE}'" >&2
        echo "Allowed values: tectonic, pdflatex, xelatex, lualatex" >&2
        exit 1
        ;;
esac

export SKIP_CHROMIUM="${SKIPCHROMIUM:-false}"
export SKIP_PYTHON="${SKIPPYTHON:-false}"
export SKIP_NODE="${SKIPNODE:-false}"

# Determine the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find install-deps.sh - check multiple locations:
# 1. Bundled in feature directory (for published feature / devcontainer CLI testing)
# 2. Repo structure (for local development)
if [ -f "${SCRIPT_DIR}/scripts/install-deps.sh" ]; then
    # Scripts bundled in feature directory
    INSTALL_DEPS_SCRIPT="${SCRIPT_DIR}/scripts/install-deps.sh"
elif [ -f "${SCRIPT_DIR}/../../scripts/install-deps.sh" ]; then
    # Repo structure: src/whitepaper-converter/install.sh -> scripts/install-deps.sh
    INSTALL_DEPS_SCRIPT="$(cd "${SCRIPT_DIR}/../.." && pwd)/scripts/install-deps.sh"
else
    echo "Error: install-deps.sh not found" >&2
    echo "Searched locations:" >&2
    echo "  - ${SCRIPT_DIR}/scripts/install-deps.sh (bundled)" >&2
    echo "  - ${SCRIPT_DIR}/../../scripts/install-deps.sh (repo)" >&2
    echo "" >&2
    echo "Possible causes:" >&2
    echo "  - Feature installed outside of the repository" >&2
    echo "  - Scripts not bundled in published feature" >&2
    echo "  - Incomplete git clone" >&2
    exit 1
fi

# Make sure the script is executable
chmod +x "${INSTALL_DEPS_SCRIPT}"

# Normalize boolean values (handle both true and "true" string formats)
# Devcontainer may pass booleans as actual booleans or strings
normalize_boolean() {
    local var_name="$1"
    local var_value="${!var_name}"

    if [ "${var_value}" = "true" ] || [ "${var_value}" = true ]; then
        export "${var_name}"="true"
    else
        export "${var_name}"="false"
    fi
}

normalize_boolean "SKIP_CHROMIUM"
normalize_boolean "SKIP_PYTHON"
normalize_boolean "SKIP_NODE"

# Call the main installation script
echo "Installing CoSAI Whitepaper Converter dependencies..."
echo "  LaTeX Engine: ${LATEX_ENGINE}"
echo "  Skip Chromium: ${SKIP_CHROMIUM}"
echo "  Skip Python: ${SKIP_PYTHON}"
echo "  Skip Node: ${SKIP_NODE}"

"${INSTALL_DEPS_SCRIPT}"

# ============================================================================
# Converter Installation
# ============================================================================

# Map installPath option (devcontainer passes as INSTALLPATH)
INSTALL_PATH="${INSTALLPATH:-/usr/local/lib/cosai-converter}"

# Validate install path (must be absolute, safe characters only)
if [[ ! "${INSTALL_PATH}" =~ ^/[a-zA-Z0-9/_.-]+$ ]]; then
    echo "Error: Invalid installPath '${INSTALL_PATH}'" >&2
    echo "Path must be absolute and contain only alphanumeric, dash, underscore, dot, and slash characters" >&2
    exit 1
fi

# Find converter files (bundled first, then repo root)
CONVERTER_DIR=""
if [ -f "${SCRIPT_DIR}/converter/convert.py" ]; then
    CONVERTER_DIR="${SCRIPT_DIR}/converter"
elif [ -f "${SCRIPT_DIR}/../../convert.py" ]; then
    CONVERTER_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
fi

if [ -n "${CONVERTER_DIR}" ]; then
    echo "Installing converter to ${INSTALL_PATH}..."

    # Create install directory and copy files
    mkdir -p "${INSTALL_PATH}/assets"
    cp "${CONVERTER_DIR}/convert.py" "${INSTALL_PATH}/"

    # Copy assets explicitly (avoids glob issues with special filenames)
    if [ -d "${CONVERTER_DIR}/assets" ]; then
        for asset in config.json puppeteerConfig.json cosai-template.tex cosai.sty \
                     cosai-logo.png background.pdf "CoSAI(Light).pdf"; do
            if [ -f "${CONVERTER_DIR}/assets/${asset}" ]; then
                cp "${CONVERTER_DIR}/assets/${asset}" "${INSTALL_PATH}/assets/"
            fi
        done
    fi

    # Overwrite bundled puppeteerConfig.json with the freshly generated one.
    # configure-chromium.sh (called by install-deps.sh) writes a platform-correct
    # config to SCRIPT_DIR/assets/. The bundled copy may have a stale hardcoded
    # executablePath from the build environment.
    if [ -f "${SCRIPT_DIR}/assets/puppeteerConfig.json" ]; then
        cp "${SCRIPT_DIR}/assets/puppeteerConfig.json" "${INSTALL_PATH}/assets/"
    fi

    # Copy dependency files if available
    for f in requirements.txt package.json; do
        if [ -f "${CONVERTER_DIR}/${f}" ]; then
            cp "${CONVERTER_DIR}/${f}" "${INSTALL_PATH}/"
        fi
    done

    # Install Python dependencies into bundled lib directory.
    # This ensures frontmatter is importable even when a different Python
    # (e.g. mise-managed) is on the user's PATH at runtime.
    if [ -f "${INSTALL_PATH}/requirements.txt" ]; then
        python_exe=""
        if command -v python3 >/dev/null 2>&1; then
            python_exe="python3"
        elif command -v python3.12 >/dev/null 2>&1; then
            python_exe="python3.12"
        fi

        if [ -n "$python_exe" ]; then
            mkdir -p "${INSTALL_PATH}/lib"
            if ! $python_exe -m pip install --target "${INSTALL_PATH}/lib" \
                    -r "${INSTALL_PATH}/requirements.txt" 2>/dev/null; then
                if ! $python_exe -m pip install --target "${INSTALL_PATH}/lib" \
                        --break-system-packages \
                        -r "${INSTALL_PATH}/requirements.txt" 2>&1; then
                    echo "Warning: Failed to bundle Python dependencies to ${INSTALL_PATH}/lib" >&2
                fi
            fi
        else
            echo "Warning: python3 not found, cannot bundle Python dependencies" >&2
            echo "  frontmatter must be installed system-wide for converter to work" >&2
        fi
    fi

    # Create wrapper script
    # PYTHONPATH ensures bundled dependencies (frontmatter) are found
    # regardless of which Python interpreter is active at runtime
    cat > /usr/local/bin/cosai-convert << WRAPPER_EOF
#!/usr/bin/env bash
export PYTHONPATH="${INSTALL_PATH}/lib\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 "${INSTALL_PATH}/convert.py" "\$@"
WRAPPER_EOF
    chmod +x /usr/local/bin/cosai-convert

    # Export COSAI_CONVERTER_PATH via profile.d
    echo "export COSAI_CONVERTER_PATH=\"${INSTALL_PATH}\"" > /etc/profile.d/cosai-converter.sh

    echo "Converter installed to ${INSTALL_PATH}"
    echo "  Wrapper: /usr/local/bin/cosai-convert"
    echo "  Path variable: COSAI_CONVERTER_PATH=${INSTALL_PATH}"
else
    echo "Warning: Converter files not found, skipping converter installation" >&2
    echo "  Dependencies were installed successfully" >&2
    echo "  To use the converter, clone the repository or install convert.py manually" >&2
fi

# Export success indicator (persisted via containerEnv in devcontainer-feature.json)
export COSAI_CONVERTER_INSTALLED="true"

echo "CoSAI Whitepaper Converter feature installed successfully!"
