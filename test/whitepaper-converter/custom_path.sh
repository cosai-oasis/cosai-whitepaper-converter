#!/bin/bash
# Test: Custom install path for converter
# Verifies that converter can be installed to a user-specified path
set -e

# shellcheck source=/dev/null
source dev-container-features-test-lib

# Verify converter installed at custom path
check "convert.py at custom path" test -f /opt/cosai/convert.py
check "assets at custom path" test -f /opt/cosai/assets/cosai-template.tex
check "cosai.sty at custom path" test -f /opt/cosai/assets/cosai.sty
check "config.json at custom path" test -f /opt/cosai/assets/config.json
check "puppeteerConfig.json at custom path" test -f /opt/cosai/assets/puppeteerConfig.json
check "cosai-logo.png at custom path" test -f /opt/cosai/assets/cosai-logo.png
check "background.pdf at custom path" test -f /opt/cosai/assets/background.pdf
check "CoSAI(Light).pdf at custom path" test -f "/opt/cosai/assets/CoSAI(Light).pdf"
check "requirements.txt at custom path" test -f /opt/cosai/requirements.txt
check "package.json at custom path" test -f /opt/cosai/package.json

# Verify wrapper script exists and is executable
check "cosai-convert wrapper exists" command -v cosai-convert
check "cosai-convert is executable" test -x /usr/local/bin/cosai-convert
check "wrapper points to custom path" bash -c "grep '/opt/cosai' /usr/local/bin/cosai-convert"
check "wrapper sets PYTHONPATH" bash -c "grep 'PYTHONPATH' /usr/local/bin/cosai-convert"
check "frontmatter in bundled lib" python3 -c "import sys; sys.path.insert(0, '/opt/cosai/lib'); import frontmatter"
check "wrapper imports frontmatter without error" bash -c "cosai-convert 2>&1 | head -5 | grep -qv ModuleNotFoundError"

# Verify COSAI_CONVERTER_PATH points to custom path
check "COSAI_CONVERTER_PATH points to custom path" bash -c ". /etc/profile.d/cosai-converter.sh && test \"\${COSAI_CONVERTER_PATH}\" = '/opt/cosai'"

# Verify NOT at default path
check "not at default path" test ! -f /usr/local/lib/cosai-converter/convert.py

# Verify system dependencies still installed (tectonic is default)
check "tectonic installed" command -v tectonic
check "pandoc installed" command -v pandoc

reportResults
