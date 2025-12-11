#!/bin/bash

# Safari Extension Creation Script for MCP Browser
# This script automates the conversion of the Chrome extension to Safari format
# using Apple's safari-web-extension-converter tool

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/masa/Projects/mcp-browser"
CHROME_EXT_DIR="$PROJECT_ROOT/mcp-browser-extension"
SAFARI_EXT_DIR="$PROJECT_ROOT/mcp-browser-extension-safari"
APP_NAME="MCP Browser"
BUNDLE_ID="com.mcpbrowser.extension"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   MCP Browser - Safari Extension Converter${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}[1/7]${NC} Checking prerequisites..."

# Check if Xcode Command Line Tools are installed
if ! xcode-select -p &> /dev/null; then
    echo -e "${RED}✗ Xcode Command Line Tools not found${NC}"
    echo ""
    echo "Install them with:"
    echo "  xcode-select --install"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Xcode Command Line Tools found${NC}"

# Check if safari-web-extension-converter exists
if ! xcrun --find safari-web-extension-converter &> /dev/null; then
    echo -e "${RED}✗ safari-web-extension-converter not found${NC}"
    echo ""
    echo "This tool requires:"
    echo "  - macOS Big Sur (11.0) or later"
    echo "  - Xcode 13.0 or later (download from Mac App Store)"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ safari-web-extension-converter found${NC}"

# Check if Chrome extension directory exists
if [ ! -d "$CHROME_EXT_DIR" ]; then
    echo -e "${RED}✗ Chrome extension directory not found: $CHROME_EXT_DIR${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Chrome extension directory found${NC}"

# Check Safari version
SAFARI_VERSION=$(defaults read /Applications/Safari.app/Contents/Info CFBundleShortVersionString 2>/dev/null || echo "Unknown")
echo -e "${GREEN}✓ Safari version: $SAFARI_VERSION${NC}"

if [[ $(echo "$SAFARI_VERSION" | cut -d. -f1) -lt 17 ]]; then
    echo -e "${YELLOW}⚠ Safari 17+ recommended for full MV3 support (you have $SAFARI_VERSION)${NC}"
fi

echo ""

# Backup existing Safari extension if it exists
if [ -d "$SAFARI_EXT_DIR" ]; then
    echo -e "${YELLOW}[2/7]${NC} Backing up existing Safari extension..."
    BACKUP_DIR="${SAFARI_EXT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    mv "$SAFARI_EXT_DIR" "$BACKUP_DIR"
    echo -e "${GREEN}✓ Backed up to: $BACKUP_DIR${NC}"
else
    echo -e "${YELLOW}[2/7]${NC} No existing Safari extension found (skipping backup)"
fi
echo ""

# Create Safari extension resources directory
echo -e "${YELLOW}[3/7]${NC} Creating Safari extension structure..."
mkdir -p "$SAFARI_EXT_DIR/Resources"
echo -e "${GREEN}✓ Created: $SAFARI_EXT_DIR/Resources${NC}"
echo ""

# Copy web extension files
echo -e "${YELLOW}[4/7]${NC} Copying web extension files..."

# Copy all necessary files
echo "  • Copying manifest.json (Safari-compatible version)..."
cp "$PROJECT_ROOT/mcp-browser-extension-safari-resources/manifest.json" "$SAFARI_EXT_DIR/Resources/"

echo "  • Copying background.js (Safari-compatible version)..."
cp "$PROJECT_ROOT/mcp-browser-extension-safari-resources/background.js" "$SAFARI_EXT_DIR/Resources/"

echo "  • Copying content.js..."
cp "$CHROME_EXT_DIR/content.js" "$SAFARI_EXT_DIR/Resources/"

echo "  • Copying popup files..."
cp "$PROJECT_ROOT/mcp-browser-extension-safari-resources/popup.html" "$SAFARI_EXT_DIR/Resources/"
cp "$PROJECT_ROOT/mcp-browser-extension-safari-resources/popup.js" "$SAFARI_EXT_DIR/Resources/"

echo "  • Copying Readability.js..."
cp "$CHROME_EXT_DIR/Readability.js" "$SAFARI_EXT_DIR/Resources/"

echo "  • Copying icons..."
cp "$CHROME_EXT_DIR"/icon-*.png "$SAFARI_EXT_DIR/Resources/"

echo -e "${GREEN}✓ All web extension files copied${NC}"
echo ""

# Run safari-web-extension-converter
echo -e "${YELLOW}[5/7]${NC} Running safari-web-extension-converter..."
echo ""

# Create temporary directory for conversion
TEMP_CONV_DIR=$(mktemp -d)

# Run the converter
xcrun safari-web-extension-converter \
    "$SAFARI_EXT_DIR/Resources" \
    --project-location "$TEMP_CONV_DIR" \
    --app-name "$APP_NAME" \
    --bundle-identifier "$BUNDLE_ID" \
    --swift \
    --force \
    || {
        echo -e "${RED}✗ Conversion failed${NC}"
        echo ""
        echo "Try running manually:"
        echo "  xcrun safari-web-extension-converter \\"
        echo "    \"$SAFARI_EXT_DIR/Resources\" \\"
        echo "    --project-location \"$SAFARI_EXT_DIR\" \\"
        echo "    --app-name \"$APP_NAME\" \\"
        echo "    --bundle-identifier \"$BUNDLE_ID\" \\"
        echo "    --swift"
        exit 1
    }

# Move converted project to final location
echo "  • Moving Xcode project to final location..."
mv "$TEMP_CONV_DIR"/* "$SAFARI_EXT_DIR/" 2>/dev/null || true
rm -rf "$TEMP_CONV_DIR"

echo -e "${GREEN}✓ Conversion completed successfully${NC}"
echo ""

# Verify structure
echo -e "${YELLOW}[6/7]${NC} Verifying Safari extension structure..."

REQUIRED_FILES=(
    "$SAFARI_EXT_DIR/Resources/manifest.json"
    "$SAFARI_EXT_DIR/Resources/background.js"
    "$SAFARI_EXT_DIR/Resources/content.js"
    "$SAFARI_EXT_DIR/Resources/popup.html"
    "$SAFARI_EXT_DIR/Resources/popup.js"
    "$SAFARI_EXT_DIR/Resources/Readability.js"
)

ALL_PRESENT=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $(basename "$file")"
    else
        echo -e "${RED}✗${NC} $(basename "$file") - MISSING"
        ALL_PRESENT=false
    fi
done

if [ "$ALL_PRESENT" = false ]; then
    echo -e "${RED}Some required files are missing!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All required files present${NC}"
echo ""

# Create README for Safari extension
echo -e "${YELLOW}[7/7]${NC} Creating Safari extension README..."

cat > "$SAFARI_EXT_DIR/README.md" << 'EOF'
# MCP Browser - Safari Extension

This is the Safari version of the MCP Browser extension.

## Quick Start

### Option 1: Using Xcode (Recommended)

1. Open the Xcode project:
   ```bash
   open "MCP Browser.xcodeproj"
   ```

2. In Xcode:
   - Select "MCP Browser" scheme
   - Click Run (⌘R)
   - The app will launch and install the extension

3. In Safari:
   - Go to Safari → Settings → Extensions
   - Enable "MCP Browser Extension"
   - (Optional) Click "Always Allow on Every Website" for automatic console capture

4. For development:
   - Enable: Safari → Settings → Advanced → Show Develop menu
   - Enable: Develop → Allow Unsigned Extensions

### Option 2: Build from Command Line

```bash
# Build the app
xcodebuild -scheme "MCP Browser" -configuration Debug

# Run the app
open "build/Build/Products/Debug/MCP Browser.app"
```

## Testing

1. **Start the MCP server** (if not already running):
   ```bash
   cd /Users/masa/Projects/mcp-browser
   python -m mcp_server_browser
   ```

2. **Open Safari** and navigate to any website

3. **Check console capture**:
   - Open Web Inspector on the page (right-click → Inspect Element)
   - Type: `console.log('test message')`
   - Message should appear in your MCP server logs

4. **Debug the extension**:
   - Safari → Develop → Web Extension Background Pages → MCP Browser Extension
   - View console logs, network requests, etc.

## Project Structure

```
mcp-browser-extension-safari/
├── MCP Browser/              # macOS app wrapper
│   ├── ContentView.swift     # App UI
│   ├── AppDelegate.swift     # App lifecycle
│   └── Info.plist           # App configuration
├── MCP Browser Extension/    # Safari extension
│   └── Resources/           # Web extension files
│       ├── manifest.json    # Extension manifest
│       ├── background.js    # Background service worker
│       ├── content.js       # Content script
│       ├── popup.html       # Extension popup
│       ├── popup.js         # Popup logic
│       └── Readability.js   # Content extraction
└── MCP Browser.xcodeproj    # Xcode project
```

## Safari-Specific Notes

### Manifest V3 Support

Safari 17+ fully supports Manifest V3 including:
- Service workers for background scripts
- `action` API (replaces `browser_action`)
- Modern permissions model

For Safari 14-16, some features may have limited support.

### API Compatibility

This extension uses cross-browser compatible code:

```javascript
// Works in both Chrome and Safari
const browserAPI = typeof browser !== 'undefined' ? browser : chrome;
```

### WebSocket Connections

Safari requires proper capabilities for WebSocket:
- ✓ Already configured in the Xcode project
- ✓ "Outgoing Connections (Client)" enabled
- ✓ Localhost connections allowed

### Debugging

- **Background script**: Develop → Web Extension Background Pages
- **Content script**: Regular Web Inspector on the page
- **Extension console**: Check background pages for errors

## Code Signing

### Development (Free)

Already configured for development signing:
1. Select your team in Xcode
2. Xcode handles signing automatically
3. Enable "Allow unsigned extensions" in Safari

### Distribution

For public distribution, you need:
1. Paid Apple Developer account ($99/year)
2. Developer ID certificate
3. App notarization

See [docs/SAFARI_EXTENSION.md](../docs/SAFARI_EXTENSION.md) for full details.

## Common Issues

### Extension doesn't appear in Safari

1. Make sure the app is running (check menubar/Dock)
2. Enable in Safari Settings → Extensions
3. Allow unsigned extensions (Develop menu)
4. Restart Safari

### WebSocket connection fails

1. Check that MCP server is running
2. Verify port range (8875-8895)
3. Check Console.app for sandbox errors
4. Ensure capabilities are enabled in Xcode

### Content script not injecting

1. Grant permissions in Safari
2. Check manifest.json matches patterns
3. View errors in Safari Web Inspector
4. Try reloading the extension

## Documentation

Full Safari extension documentation:
- [Safari Extension Guide](../docs/SAFARI_EXTENSION.md)
- [Apple's Safari Extensions](https://developer.apple.com/documentation/safariservices/safari_web_extensions)

## Support

For issues or questions:
- Check the main documentation
- Open an issue on GitHub
- Review Apple Developer Forums
EOF

echo -e "${GREEN}✓ README created${NC}"
echo ""

# Success summary
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   ✓ Safari Extension Created Successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Extension Location:${NC}"
echo "  $SAFARI_EXT_DIR"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. ${YELLOW}Open the Xcode project:${NC}"
echo "   open \"$SAFARI_EXT_DIR/MCP Browser.xcodeproj\""
echo ""
echo "2. ${YELLOW}Configure code signing in Xcode:${NC}"
echo "   • Select the app target"
echo "   • Go to Signing & Capabilities"
echo "   • Select your development team"
echo "   • Enable 'Automatically manage signing'"
echo ""
echo "3. ${YELLOW}Run the extension:${NC}"
echo "   • Click Run (⌘R) in Xcode"
echo "   • The app will launch and install the extension"
echo ""
echo "4. ${YELLOW}Enable in Safari:${NC}"
echo "   • Safari → Settings → Extensions"
echo "   • Enable 'MCP Browser Extension'"
echo "   • Develop → Allow Unsigned Extensions"
echo ""
echo "5. ${YELLOW}Test the extension:${NC}"
echo "   • Start your MCP server"
echo "   • Open any website in Safari"
echo "   • Check console messages are captured"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  • Safari setup: docs/SAFARI_EXTENSION.md"
echo "  • Extension README: mcp-browser-extension-safari/README.md"
echo ""
echo -e "${GREEN}Happy developing! 🎉${NC}"
echo ""
