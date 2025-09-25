#!/bin/bash
# Development Extension Script for MCP Browser
# Loads the Chrome extension and optionally opens Chrome with development profile

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Development configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXTENSION_PATH="${PROJECT_ROOT}/extension"
CHROME_PROFILE_DIR="${PROJECT_ROOT}/tmp/chrome-dev-profile"
ENV_FILE="${PROJECT_ROOT}/.env.development"

echo -e "${BLUE}🌐 MCP Browser Extension Development${NC}"

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Create Chrome development profile directory
mkdir -p "$CHROME_PROFILE_DIR"

# Validate extension directory
if [ ! -d "$EXTENSION_PATH" ]; then
    echo -e "${RED}❌ Extension directory not found: $EXTENSION_PATH${NC}"
    exit 1
fi

if [ ! -f "$EXTENSION_PATH/manifest.json" ]; then
    echo -e "${RED}❌ manifest.json not found in extension directory${NC}"
    exit 1
fi

echo -e "${GREEN}📁 Extension Path: $EXTENSION_PATH${NC}"
echo -e "${GREEN}👤 Chrome Profile: $CHROME_PROFILE_DIR${NC}"

# Function to find Chrome executable
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

# Parse command line arguments
AUTO_OPEN=${1:-${ENABLE_BROWSER_AUTO_OPEN:-true}}
SHOW_INSTRUCTIONS_ONLY=false

if [ "$1" = "--instructions-only" ] || [ "$1" = "-i" ]; then
    SHOW_INSTRUCTIONS_ONLY=true
    AUTO_OPEN=false
fi

# Show manual instructions
show_manual_instructions() {
    echo -e "\n${YELLOW}📋 Manual Extension Loading Instructions:${NC}"
    echo -e "${YELLOW}1. Open Google Chrome${NC}"
    echo -e "${YELLOW}2. Navigate to: chrome://extensions/${NC}"
    echo -e "${YELLOW}3. Enable 'Developer mode' (toggle in top-right)${NC}"
    echo -e "${YELLOW}4. Click 'Load unpacked'${NC}"
    echo -e "${YELLOW}5. Select folder: ${EXTENSION_PATH}${NC}"
    echo -e "${YELLOW}6. The extension should now appear in your extensions list${NC}"
    echo -e "${YELLOW}7. Click the extension icon to see connection status${NC}"
    echo ""
    echo -e "${BLUE}🔧 Extension Details:${NC}"
    echo -e "${BLUE}  - Name: $(grep '"name"' "$EXTENSION_PATH/manifest.json" | cut -d'"' -f4)${NC}"
    echo -e "${BLUE}  - Version: $(grep '"version"' "$EXTENSION_PATH/manifest.json" | cut -d'"' -f4)${NC}"
    echo -e "${BLUE}  - Manifest: v$(grep '"manifest_version"' "$EXTENSION_PATH/manifest.json" | cut -d':' -f2 | tr -d ' ,')"
}

# Show instructions only mode
if [ "$SHOW_INSTRUCTIONS_ONLY" = true ]; then
    show_manual_instructions
    exit 0
fi

# Try to auto-open Chrome with extension
if [ "$AUTO_OPEN" = "true" ]; then
    CHROME_EXECUTABLE=$(find_chrome)

    if [ $? -eq 0 ] && [ -n "$CHROME_EXECUTABLE" ]; then
        echo -e "${GREEN}🚀 Found Chrome at: $CHROME_EXECUTABLE${NC}"
        echo -e "${GREEN}📂 Opening Chrome with development profile...${NC}"

        # Chrome arguments for development
        CHROME_ARGS=(
            "--user-data-dir=$CHROME_PROFILE_DIR"
            "--load-extension=$EXTENSION_PATH"
            "--disable-extensions-except=$EXTENSION_PATH"
            "--disable-web-security"
            "--disable-features=TranslateUI"
            "--disable-ipc-flooding-protection"
            "--enable-logging=stderr"
            "--log-level=0"
            "--new-window"
        )

        # Add test URL if specified
        if [ -n "$DEV_TEST_URL" ]; then
            CHROME_ARGS+=("$DEV_TEST_URL")
        else
            CHROME_ARGS+=("chrome://extensions/")
        fi

        echo -e "${BLUE}🔧 Chrome Arguments:${NC}"
        printf "${BLUE}  %s${NC}\n" "${CHROME_ARGS[@]}"

        # Launch Chrome
        "$CHROME_EXECUTABLE" "${CHROME_ARGS[@]}" &
        CHROME_PID=$!

        echo -e "${GREEN}✅ Chrome launched with extension (PID: $CHROME_PID)${NC}"
        echo -e "${GREEN}📱 Extension should be automatically loaded${NC}"

        # Wait a moment for Chrome to start
        sleep 3

        # Verify Chrome process is running
        if kill -0 $CHROME_PID 2>/dev/null; then
            echo -e "${GREEN}🎯 Chrome is running with development profile${NC}"
            echo -e "${BLUE}💡 To reload extension: chrome://extensions/ > Reload button${NC}"
        else
            echo -e "${YELLOW}⚠️  Chrome process may have exited, check manually${NC}"
        fi

    else
        echo -e "${YELLOW}⚠️  Chrome executable not found${NC}"
        echo -e "${YELLOW}Set CHROME_EXECUTABLE_PATH in .env.development or install Chrome${NC}"
        show_manual_instructions
    fi
else
    echo -e "${BLUE}🔧 Auto-open disabled${NC}"
    show_manual_instructions
fi

# Show development tips
echo -e "\n${GREEN}💡 Development Tips:${NC}"
echo -e "${GREEN}  - Open Chrome DevTools to see console messages${NC}"
echo -e "${GREEN}  - Check extension popup for connection status${NC}"
echo -e "${GREEN}  - Use background page DevTools for extension debugging${NC}"
echo -e "${GREEN}  - Monitor WebSocket connections in Network tab${NC}"

# Check if MCP server is running
if curl -s "http://localhost:${MCP_PORT:-8875}" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ MCP server is running on port ${MCP_PORT:-8875}${NC}"
else
    echo -e "${YELLOW}⚠️  MCP server not detected on port ${MCP_PORT:-8875}${NC}"
    echo -e "${YELLOW}Run: make dev-server or scripts/dev-server.sh${NC}"
fi

echo -e "\n${GREEN}🎉 Extension development setup complete!${NC}"