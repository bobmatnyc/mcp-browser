#!/usr/bin/env bash
# Test MCP Browser Installation and Functionality

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "══════════════════════════════════════════════════════════"
echo "           MCP Browser Installation Test                   "
echo "══════════════════════════════════════════════════════════"
echo ""

# Test 1: Check installation
echo -e "${BLUE}[Test 1]${NC} Checking installation..."
if [ -x "./mcp-browser" ]; then
    echo -e "  ${GREEN}✓${NC} mcp-browser command exists"
else
    echo -e "  ✗ mcp-browser command not found"
    exit 1
fi

if [ -d ".venv" ]; then
    echo -e "  ${GREEN}✓${NC} Virtual environment exists"
else
    echo -e "  ✗ Virtual environment not found"
    exit 1
fi

if [ -d "$HOME/.mcp-browser" ]; then
    echo -e "  ${GREEN}✓${NC} Home directory exists"
else
    echo -e "  ✗ Home directory not found"
    exit 1
fi

echo ""

# Test 2: Show version
echo -e "${BLUE}[Test 2]${NC} Version information..."
./mcp-browser version
echo ""

# Test 3: Start server
echo -e "${BLUE}[Test 3]${NC} Starting server..."
./mcp-browser start
sleep 2
echo ""

# Test 4: Check status
echo -e "${BLUE}[Test 4]${NC} Server status..."
./mcp-browser status | head -20
echo ""

# Test 5: Check logs
echo -e "${BLUE}[Test 5]${NC} Recent logs..."
./mcp-browser logs 5
echo ""

# Test 6: Test MCP mode (background)
echo -e "${BLUE}[Test 6]${NC} Testing MCP stdio mode..."
timeout 2 ./mcp-browser mcp < /dev/null 2>&1 | head -5 || true
echo ""

# Test 7: Clean stop
echo -e "${BLUE}[Test 7]${NC} Stopping server..."
./mcp-browser stop
echo ""

echo "══════════════════════════════════════════════════════════"
echo -e "        ${GREEN}✓ All tests completed successfully${NC}         "
echo "══════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "1. Install Chrome extension from: ./extension/"
echo "2. Configure Claude Code with: ./setup-claude-code.sh"
echo "3. Start using MCP Browser with: ./mcp-browser start"