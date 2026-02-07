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

# Export success indicator (persisted via containerEnv in devcontainer-feature.json)
export COSAI_CONVERTER_INSTALLED="true"

echo "CoSAI Whitepaper Converter feature installed successfully!"
