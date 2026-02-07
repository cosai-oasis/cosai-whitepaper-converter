#!/bin/bash
# Test: Default installation (all components enabled with tectonic engine)
# This is the required default test script for devcontainer features test CLI
set -e

# shellcheck source=/dev/null
source dev-container-features-test-lib

# Verify tectonic (default LaTeX engine)
check "tectonic installed" command -v tectonic
check "tectonic works" tectonic --version

# Verify pandoc
check "pandoc installed" command -v pandoc
check "pandoc works" pandoc --version

# Verify python3
check "python3 installed" command -v python3
check "python3 works" python3 --version

# Verify node
check "node installed" command -v node
check "node works" node --version

# Verify npm
check "npm installed" command -v npm
check "npm works" npm --version

# Note: Chromium check skipped - ARM64 uses Playwright bundled chromium which
# isn't a system binary. The skipChromium test validates the skip behavior.

# Verify mermaid-cli is available via npx
check "mermaid-cli available" npx --yes @mermaid-js/mermaid-cli --version

# Verify python-frontmatter is installed
check "python-frontmatter installed" python3 -c "import frontmatter"

# Verify environment variable (set via containerEnv)
check "COSAI_CONVERTER_INSTALLED set" test "${COSAI_CONVERTER_INSTALLED}" = "true"

# Verify pdflatex is NOT installed (should only have tectonic)
check "pdflatex not installed" bash -c "! command -v pdflatex"

reportResults
