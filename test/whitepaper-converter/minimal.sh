#!/bin/bash
# Test: Minimal install (all skip flags enabled)
set -e

# shellcheck source=/dev/null
source dev-container-features-test-lib

# Verify only pandoc and latex are installed
check "pandoc installed" command -v pandoc
check "tectonic installed" command -v tectonic

# Verify optional components are NOT installed
check "python3 not installed" bash -c "! command -v python3"
check "node not installed" bash -c "! command -v node"
check "chromium not installed" bash -c "! command -v chromium"

reportResults
