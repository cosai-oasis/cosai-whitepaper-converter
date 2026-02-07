#!/bin/bash
# Test: pdflatex LaTeX engine
set -e

# shellcheck source=/dev/null
source dev-container-features-test-lib

# Verify pdflatex is installed
check "pdflatex installed" command -v pdflatex
check "pdflatex works" pdflatex --version

# Verify pandoc (always installed)
check "pandoc installed" command -v pandoc
check "pandoc works" pandoc --version

# Verify python3 (default behavior)
check "python3 installed" command -v python3
check "python3 works" python3 --version

# Verify node (default behavior)
check "node installed" command -v node
check "node works" node --version


# Verify tectonic is NOT installed (different engine selected)
check "tectonic not installed" bash -c "! command -v tectonic"

reportResults
