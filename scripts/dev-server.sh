#!/bin/bash
# Development Server Script for MCP Browser
# Starts the MCP server with hot reload and development features

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Development configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env.development"
LOG_DIR="${PROJECT_ROOT}/tmp/logs"
PID_FILE="${PROJECT_ROOT}/tmp/dev-server.pid"

echo -e "${BLUE}🚀 Starting MCP Browser Development Server${NC}"
echo -e "${BLUE}Project Root: ${PROJECT_ROOT}${NC}"

# Create directories
mkdir -p "${LOG_DIR}"
mkdir -p "${PROJECT_ROOT}/tmp"

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}📄 Loading development environment from ${ENV_FILE}${NC}"
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo -e "${YELLOW}⚠️  Development environment file not found, using defaults${NC}"
fi

# Check if server is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Development server already running (PID: $OLD_PID)${NC}"
        echo -e "${YELLOW}Stopping existing server...${NC}"
        kill "$OLD_PID" 2>/dev/null || true
        sleep 2
    fi
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping development server...${NC}"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        kill "$PID" 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start development server with hot reload
echo -e "${GREEN}🔄 Starting server with hot reload...${NC}"
echo -e "${BLUE}Environment: Development${NC}"
echo -e "${BLUE}Debug Mode: ${MCP_DEBUG:-true}${NC}"
echo -e "${BLUE}Log Level: ${MCP_LOG_LEVEL:-DEBUG}${NC}"
echo -e "${BLUE}Port Range: ${MCP_PORT_RANGE_START:-8875}-${MCP_PORT_RANGE_END:-8895}${NC}"

# Check if watchdog is available for file watching
if command -v watchdog-run >/dev/null 2>&1; then
    echo -e "${GREEN}📡 Using watchdog for hot reload${NC}"

    # Start server with watchdog for auto-reload
    cd "$PROJECT_ROOT"
    watchdog-run \
        --patterns="*.py;*.json;*.js" \
        --ignore-patterns="__pycache__;*.pyc;.git;tmp;logs" \
        --ignore-directories \
        python -m src.cli.main start --debug &

    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"

elif command -v entr >/dev/null 2>&1; then
    echo -e "${GREEN}📡 Using entr for hot reload${NC}"

    # Start server with entr for auto-reload
    cd "$PROJECT_ROOT"
    find src extension -name "*.py" -o -name "*.js" -o -name "*.json" | \
    entr -r python -m src.cli.main start --debug &

    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"

else
    echo -e "${YELLOW}⚠️  No file watcher found (watchdog or entr), running without hot reload${NC}"
    echo -e "${YELLOW}Install with: pip install watchdog or brew install entr${NC}"

    # Start server without hot reload
    cd "$PROJECT_ROOT"
    python -m src.cli.main start --debug &

    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"
fi

echo -e "${GREEN}✅ Development server started (PID: $SERVER_PID)${NC}"
echo -e "${BLUE}📊 Server Status:${NC}"
echo -e "${BLUE}  - WebSocket: ws://localhost:${MCP_PORT:-8875}${NC}"
echo -e "${BLUE}  - Logs: ${LOG_DIR}${NC}"
echo -e "${BLUE}  - PID File: ${PID_FILE}${NC}"

echo -e "\n${YELLOW}📌 Development Instructions:${NC}"
echo -e "${YELLOW}  1. Load Chrome extension from: ./extension/${NC}"
echo -e "${YELLOW}  2. Navigate to chrome://extensions/ and enable Developer Mode${NC}"
echo -e "${YELLOW}  3. Click 'Load unpacked' and select the extension folder${NC}"
echo -e "${YELLOW}  4. Configure Claude Code with MCP server${NC}"

echo -e "\n${GREEN}🎯 Ready for development! Press Ctrl+C to stop.${NC}"

# Wait for server process
wait $SERVER_PID