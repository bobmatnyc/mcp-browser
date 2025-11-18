#!/usr/bin/env bash
# Update Homebrew tap formula with new version and SHA256
#
# Usage:
#   ./scripts/update_homebrew_tap.sh 2.0.10

set -euo pipefail

VERSION="${1:-}"

if [ -z "$VERSION" ]; then
    echo "ERROR: Version required"
    echo "Usage: $0 <version>"
    exit 1
fi

echo "Updating Homebrew tap for version $VERSION..."

# Wait for PyPI to propagate (may take a few minutes)
echo "Waiting for PyPI to propagate new version..."
sleep 10

# Fetch package info from PyPI
PYPI_URL="https://pypi.org/pypi/mcp-browser/$VERSION/json"
echo "Fetching package info from $PYPI_URL..."

# Download package metadata
PACKAGE_JSON=$(curl -sL "$PYPI_URL" || echo "")

if [ -z "$PACKAGE_JSON" ]; then
    echo "ERROR: Could not fetch package info from PyPI"
    echo "PyPI may not have propagated yet. Please wait a few minutes and try again."
    exit 1
fi

# Extract SHA256 from the source distribution (.tar.gz)
SHA256=$(echo "$PACKAGE_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for url_data in data['urls']:
    if url_data['packagetype'] == 'sdist':
        print(url_data['digests']['sha256'])
        break
")

if [ -z "$SHA256" ]; then
    echo "ERROR: Could not extract SHA256 from PyPI response"
    exit 1
fi

echo "Found SHA256: $SHA256"
echo ""
echo "✅ Package published successfully to PyPI"
echo ""
echo "To update Homebrew tap:"
echo "1. Clone/update your homebrew tap repository"
echo "2. Update the formula with:"
echo "   - version: $VERSION"
echo "   - sha256: $SHA256"
echo ""
echo "Example formula update:"
echo "  url \"https://files.pythonhosted.org/packages/source/m/mcp-browser/mcp-browser-${VERSION}.tar.gz\""
echo "  sha256 \"$SHA256\""
