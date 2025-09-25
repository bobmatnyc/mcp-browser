#!/bin/bash
# setup-path.sh - Add mcp-browser bin directory to PATH
# Source this file to use the local development version of mcp-browser

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Export PATH with our bin directory
export PATH="$SCRIPT_DIR:$PATH"

echo "✅ mcp-browser development version added to PATH"
echo "   You can now run 'mcp-browser' from anywhere in this shell session"
echo ""
echo "To make this permanent, add this line to your ~/.bashrc or ~/.zshrc:"
echo "   export PATH=\"$SCRIPT_DIR:\$PATH\""
echo ""
echo "Or use direnv (recommended):"
echo "   brew install direnv"
echo "   direnv allow $SCRIPT_DIR/.."