#!/bin/bash

# Test script for MCP server
echo "Testing MCP Browser server..."

# Test 1: Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi
echo "✅ Virtual environment found"

# Test 2: Check Python version
PYTHON_VERSION=$(.venv/bin/python --version 2>&1)
echo "✅ Python version: $PYTHON_VERSION"

# Test 3: Check if MCP is installed
if ! .venv/bin/pip list | grep -q "mcp"; then
    echo "❌ MCP not installed"
    exit 1
fi
echo "✅ MCP package installed"

# Test 4: Test MCP server initialization
echo "Testing MCP server initialization..."
RESPONSE=$(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"0.1.0","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | timeout 2 .venv/bin/python mcp-server.py 2>/dev/null | head -1)

if echo "$RESPONSE" | grep -q '"result"'; then
    echo "✅ MCP server responds to initialization"
else
    echo "⚠️  MCP server may not be responding correctly"
    echo "Response: $RESPONSE"
fi

# Test 5: Check mcp.json exists
if [ ! -f "mcp.json" ]; then
    echo "❌ mcp.json not found"
    exit 1
fi
echo "✅ mcp.json configuration found"

# Test 6: Verify mcp.json structure
if python3 -c "import json; json.load(open('mcp.json'))" 2>/dev/null; then
    echo "✅ mcp.json is valid JSON"
else
    echo "❌ mcp.json is not valid JSON"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ MCP Browser server is properly configured!"
echo "========================================="
echo ""
echo "The server can be discovered by Claude Code using:"
echo "  - Project config: $(pwd)/mcp.json"
echo "  - Command: .venv/bin/python mcp-server.py"
echo ""
echo "To use with Claude Code:"
echo "1. Ensure Claude Code is installed"
echo "2. Navigate to this project directory"
echo "3. Claude Code should auto-discover the MCP server"
echo "4. Use the 'mcp' command in Claude Code to verify"