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

# Verify converter installation
check "convert.py installed" test -f /usr/local/lib/cosai-converter/convert.py
check "converter assets exist" test -f /usr/local/lib/cosai-converter/assets/cosai-template.tex
check "cosai.sty exists" test -f /usr/local/lib/cosai-converter/assets/cosai.sty
check "config.json exists" test -f /usr/local/lib/cosai-converter/assets/config.json
check "cosai-logo.png exists" test -f /usr/local/lib/cosai-converter/assets/cosai-logo.png
check "puppeteerConfig.json exists" test -f /usr/local/lib/cosai-converter/assets/puppeteerConfig.json
check "background.pdf exists" test -f /usr/local/lib/cosai-converter/assets/background.pdf
check "CoSAI(Light).pdf exists" test -f "/usr/local/lib/cosai-converter/assets/CoSAI(Light).pdf"
check "requirements.txt installed" test -f /usr/local/lib/cosai-converter/requirements.txt
check "package.json installed" test -f /usr/local/lib/cosai-converter/package.json
check "cosai-convert wrapper exists" command -v cosai-convert
check "cosai-convert is executable" test -x /usr/local/bin/cosai-convert
check "wrapper points to default path" bash -c "grep '/usr/local/lib/cosai-converter' /usr/local/bin/cosai-convert"
check "wrapper sets PYTHONPATH" bash -c "grep 'PYTHONPATH' /usr/local/bin/cosai-convert"
check "frontmatter in bundled lib" python3 -c "import sys; sys.path.insert(0, '/usr/local/lib/cosai-converter/lib'); import frontmatter"
check "wrapper imports frontmatter without error" bash -c "cosai-convert 2>&1 | head -5 | grep -qv ModuleNotFoundError"
check "COSAI_CONVERTER_PATH set" bash -c ". /etc/profile.d/cosai-converter.sh && test -n \"\${COSAI_CONVERTER_PATH}\""

# End-to-end conversion test: mermaid diagram → PDF
# This catches ARM64 chromium issues and rendering pipeline failures
TICK='```'
cat > /tmp/test-mermaid.md << TESTEOF
---
title: "Test"
author: "CI"
date: "2025-01-01"
---
# Test

${TICK}mermaid
graph TD
    A[Start] --> B[End]
${TICK}
TESTEOF

check "mermaid conversion succeeds" cosai-convert /tmp/test-mermaid.md /tmp/test-output.pdf
check "output PDF exists and is non-empty" test -s /tmp/test-output.pdf

reportResults
