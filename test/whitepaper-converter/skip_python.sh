#!/bin/bash
# Test: skipPython option
set -e

# shellcheck source=/dev/null
source dev-container-features-test-lib

# Verify python-frontmatter is NOT installed
# Note: We check for frontmatter (our pip package), not python3 itself,
# because the base image may ship with python3 pre-installed.
check "python-frontmatter not installed" bash -c "! python3 -c 'import frontmatter' 2>/dev/null"

# Verify other components ARE installed (pandoc, latex, node)
check "pandoc installed" command -v pandoc
check "node installed" command -v node

# Verify tectonic (default engine)
check "tectonic installed" command -v tectonic

reportResults
