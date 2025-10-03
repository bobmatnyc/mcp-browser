#!/bin/bash
# Full Development Environment Script for MCP Browser
# Starts both MCP server and Chrome extension in development mode

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Development configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
TMP_DIR="$PROJECT_ROOT/tmp"
ENV_FILE="$PROJECT_ROOT/.env.development"

echo -e "${PURPLE}🎯 MCP Browser Full Development Environment${NC}"
echo -e "${PURPLE}==========================================${NC}"

# Create necessary directories
mkdir -p "$TMP_DIR"

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}📄 Loading development environment${NC}"
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo -e "${YELLOW}⚠️  Creating default development environment${NC}"
    cp "$PROJECT_ROOT/.env.development" "$ENV_FILE" 2>/dev/null || true
fi

# PID files for tracking processes
SERVER_PID_FILE="$TMP_DIR/dev-server.pid"
CHROME_PID_FILE="$TMP_DIR/chrome-dev.pid"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down development environment...${NC}"

    # Stop Chrome
    if [ -f "$CHROME_PID_FILE" ]; then
        CHROME_PID=$(cat "$CHROME_PID_FILE")
        if kill -0 "$CHROME_PID" 2>/dev/null; then
            echo -e "${YELLOW}  Stopping Chrome (PID: $CHROME_PID)${NC}"
            kill "$CHROME_PID" 2>/dev/null || true
        fi
        rm -f "$CHROME_PID_FILE"
    fi

    # Stop MCP server
    if [ -f "$SERVER_PID_FILE" ]; then
        SERVER_PID=$(cat "$SERVER_PID_FILE")
        if kill -0 "$SERVER_PID" 2>/dev/null; then
            echo -e "${YELLOW}  Stopping MCP Server (PID: $SERVER_PID)${NC}"
            kill "$SERVER_PID" 2>/dev/null || true
        fi
        rm -f "$SERVER_PID_FILE"
    fi

    echo -e "${GREEN}✅ Development environment stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Function to check if process is running
is_running() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        kill -0 "$pid" 2>/dev/null
        return $?
    fi
    return 1
}

# Pre-flight checks
echo -e "${BLUE}🔍 Pre-flight Checks${NC}"

# Check Python
if ! command -v python >/dev/null 2>&1; then
    echo -e "${RED}❌ Python not found${NC}"
    exit 1
fi
echo -e "${GREEN}  ✅ Python: $(python --version)${NC}"

# Check if project is installed
if ! python -c "import src.cli.main" >/dev/null 2>&1; then
    echo -e "${YELLOW}  ⚠️  Project not installed, running: pip install -e .${NC}"
    pip install -e . || {
        echo -e "${RED}❌ Failed to install project${NC}"
        exit 1
    }
fi
echo -e "${GREEN}  ✅ Project package available${NC}"

# Check extension files
if [ ! -f "$PROJECT_ROOT/src/extension/manifest.json" ]; then
    echo -e "${RED}❌ Extension manifest.json not found${NC}"
    exit 1
fi
echo -e "${GREEN}  ✅ Extension files present${NC}"

# Stop any existing processes
echo -e "\n${BLUE}🧹 Cleaning up existing processes${NC}"
if is_running "$SERVER_PID_FILE"; then
    OLD_SERVER_PID=$(cat "$SERVER_PID_FILE")
    echo -e "${YELLOW}  Stopping existing MCP server (PID: $OLD_SERVER_PID)${NC}"
    kill "$OLD_SERVER_PID" 2>/dev/null || true
    sleep 2
fi

if is_running "$CHROME_PID_FILE"; then
    OLD_CHROME_PID=$(cat "$CHROME_PID_FILE")
    echo -e "${YELLOW}  Stopping existing Chrome (PID: $OLD_CHROME_PID)${NC}"
    kill "$OLD_CHROME_PID" 2>/dev/null || true
    sleep 2
fi

# Start MCP Server
echo -e "\n${BLUE}🚀 Starting MCP Server${NC}"
cd "$PROJECT_ROOT"

# Start server in background
if command -v watchdog-run >/dev/null 2>&1; then
    echo -e "${GREEN}  📡 Using watchdog for hot reload${NC}"
    watchdog-run \
        --patterns="*.py;*.json;*.js" \
        --ignore-patterns="__pycache__;*.pyc;.git;tmp;logs" \
        --ignore-directories \
        python -m src.cli.main start --debug &
else
    echo -e "${YELLOW}  🔄 Starting without hot reload (install watchdog for auto-reload)${NC}"
    python -m src.cli.main start --debug &
fi

SERVER_PID=$!
echo $SERVER_PID > "$SERVER_PID_FILE"
echo -e "${GREEN}  ✅ MCP Server started (PID: $SERVER_PID)${NC}"

# Wait for server to start
echo -e "${BLUE}  ⏳ Waiting for server to initialize...${NC}"
sleep 5

# Check if server is responding
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if nc -z localhost ${MCP_PORT:-8875} 2>/dev/null; then
        echo -e "${GREEN}  ✅ Server is responding on port ${MCP_PORT:-8875}${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -e "${YELLOW}  ⏳ Retry $RETRY_COUNT/$MAX_RETRIES - waiting for server...${NC}"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}  ❌ Server failed to start properly${NC}"
    cleanup
    exit 1
fi

# Start Chrome with Extension
echo -e "\n${BLUE}🌐 Starting Chrome with Extension${NC}"

# Find Chrome executable
find_chrome() {
    local chrome_paths=(
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"
        "/Applications/Chromium.app/Contents/MacOS/Chromium"
        "/usr/bin/google-chrome"
        "/usr/bin/chromium-browser"
        "/usr/bin/google-chrome-stable"
        "$CHROME_EXECUTABLE_PATH"
    )

    for chrome_path in "${chrome_paths[@]}"; do
        if [ -n "$chrome_path" ] && [ -x "$chrome_path" ]; then
            echo "$chrome_path"
            return 0
        fi
    done
    return 1
}

CHROME_EXECUTABLE=$(find_chrome)
if [ $? -eq 0 ] && [ -n "$CHROME_EXECUTABLE" ]; then
    CHROME_PROFILE_DIR="$TMP_DIR/chrome-dev-profile"
    mkdir -p "$CHROME_PROFILE_DIR"

    echo -e "${GREEN}  🚀 Found Chrome: $CHROME_EXECUTABLE${NC}"

    # Chrome arguments
    CHROME_ARGS=(
        "--user-data-dir=$CHROME_PROFILE_DIR"
        "--load-extension=$PROJECT_ROOT/extension"
        "--disable-extensions-except=$PROJECT_ROOT/extension"
        "--disable-web-security"
        "--disable-features=TranslateUI"
        "--disable-ipc-flooding-protection"
        "--new-window"
        "chrome://extensions/"
    )

    # Launch Chrome
    "$CHROME_EXECUTABLE" "${CHROME_ARGS[@]}" &
    CHROME_PID=$!
    echo $CHROME_PID > "$CHROME_PID_FILE"

    echo -e "${GREEN}  ✅ Chrome launched (PID: $CHROME_PID)${NC}"
    sleep 3

    # Verify Chrome is running
    if kill -0 $CHROME_PID 2>/dev/null; then
        echo -e "${GREEN}  ✅ Chrome is running with development profile${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Chrome may have exited, check manually${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️  Chrome not found, load extension manually${NC}"
fi

# Show status
echo -e "\n${PURPLE}📊 Development Environment Status${NC}"
echo -e "${PURPLE}=================================${NC}"
echo -e "${GREEN}🖥️  MCP Server: Running on port ${MCP_PORT:-8875}${NC}"
echo -e "${GREEN}📱 Chrome Extension: Loaded${NC}"
echo -e "${GREEN}📁 Project Root: $PROJECT_ROOT${NC}"
echo -e "${GREEN}📂 Logs: $TMP_DIR/logs${NC}"
echo -e "${GREEN}🔧 Profile: $TMP_DIR/chrome-dev-profile${NC}"

echo -e "\n${BLUE}🎯 Development URLs:${NC}"
echo -e "${BLUE}  - WebSocket Server: ws://localhost:${MCP_PORT:-8875}${NC}"
echo -e "${BLUE}  - Chrome Extensions: chrome://extensions/${NC}"
echo -e "${BLUE}  - Extension Popup: Click the extension icon${NC}"

echo -e "\n${YELLOW}💡 Development Tips:${NC}"
echo -e "${YELLOW}  - Extension auto-reloads on file changes${NC}"
echo -e "${YELLOW}  - Server has hot reload enabled${NC}"
echo -e "${YELLOW}  - Check console for WebSocket connections${NC}"
echo -e "${YELLOW}  - Use Ctrl+C to stop everything${NC}"

echo -e "\n${GREEN}🎉 Full development environment is ready!${NC}"
echo -e "${GREEN}Press Ctrl+C to stop all services${NC}"

# Keep the script running and monitor processes
while true; do
    # Check if server is still running
    if ! is_running "$SERVER_PID_FILE"; then
        echo -e "${RED}💥 MCP Server stopped unexpectedly${NC}"
        cleanup
        exit 1
    fi

    # Check if Chrome is still running (optional)
    if [ -f "$CHROME_PID_FILE" ] && ! is_running "$CHROME_PID_FILE"; then
        echo -e "${YELLOW}⚠️  Chrome closed by user${NC}"
        rm -f "$CHROME_PID_FILE"
    fi

    sleep 5
done