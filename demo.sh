#!/usr/bin/env bash
# MCP Browser Demo Script - Shows the complete workflow

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}     MCP Browser - Project Setup Demo          ${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Step 1: Check pipx
echo -e "${GREEN}Step 1: Checking pipx installation...${NC}"
if command -v pipx &> /dev/null; then
    echo "✓ pipx is installed"
else
    echo -e "${YELLOW}pipx not found. Installing pipx...${NC}"
    echo "Please run: python3 -m pip install --user pipx"
    echo "Then run: pipx ensurepath"
    exit 1
fi
echo ""

# Step 2: Install mcp-browser (simulation)
echo -e "${GREEN}Step 2: Install mcp-browser with pipx${NC}"
echo "In production, run: pipx install mcp-browser"
echo "For development, run: pipx install ."
echo ""

# Step 3: Create a test project
echo -e "${GREEN}Step 3: Creating test project directory${NC}"
TEST_PROJECT="/tmp/mcp-browser-test-project"
rm -rf "$TEST_PROJECT"
mkdir -p "$TEST_PROJECT"
cd "$TEST_PROJECT"
echo "Created test project at: $TEST_PROJECT"
echo ""

# Step 4: Initialize extension
echo -e "${GREEN}Step 4: Initialize project extension${NC}"
echo "This would run: mcp-browser init"
echo "It creates: .mcp-browser/extension/ in your project"
mkdir -p .mcp-browser/extension
echo "✓ Extension directory created"
echo ""

# Step 5: Show dashboard URL
echo -e "${GREEN}Step 5: Start server with dashboard${NC}"
echo "Run: mcp-browser start"
echo "This will:"
echo "  - Start MCP server on stdio"
echo "  - Start WebSocket server on ports 8875-8895"
echo "  - Start dashboard on http://localhost:8080"
echo ""

# Step 6: Extension installation
echo -e "${GREEN}Step 6: Install Chrome Extension${NC}"
echo "1. Open dashboard: http://localhost:8080"
echo "2. Click 'Install Extension'"
echo "3. Follow the guided installation steps"
echo "4. The extension will connect automatically"
echo ""

# Step 7: Test console logging
echo -e "${GREEN}Step 7: Test Console Logging${NC}"
echo "1. Open test page: http://localhost:8080/test-page"
echo "2. Click buttons to generate console logs"
echo "3. View logs in the dashboard"
echo "4. Query logs via Claude Code MCP tools"
echo ""

# Step 8: Claude Code Integration
echo -e "${GREEN}Step 8: Configure Claude Code${NC}"
echo "Add to Claude Code's MCP settings:"
cat << 'CONFIG'
{
  "mcpServers": {
    "mcp-browser": {
      "command": "mcp-browser",
      "args": ["mcp"],
      "env": {}
    }
  }
}
CONFIG
echo ""

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}           Demo Setup Complete!                ${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo "Project directory: $TEST_PROJECT"
echo "Extension path: $TEST_PROJECT/.mcp-browser/extension/"
echo ""
echo "Next steps:"
echo "1. Install via pipx: pipx install ."
echo "2. Navigate to your project"
echo "3. Run: mcp-browser init"
echo "4. Run: mcp-browser start"
echo "5. Open: http://localhost:8080"
echo ""
