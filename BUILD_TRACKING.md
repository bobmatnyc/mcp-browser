# Build Tracking System

## Overview

The mcp-browser extensions now include automatic build number tracking to help developers identify which version of the extension is installed during development and testing.

## Build Number Format

Build numbers use a timestamp-based format:
```
YYYY.MM.DD.HHMM
```

**Example**: `2025.12.15.0630` = December 15, 2025 at 06:30 UTC

## Features

### 1. Automatic Generation
- Build numbers are automatically generated when running `make ext-deploy`
- Each deployment creates a unique build number based on UTC timestamp
- Build info is stored in `build-info.json` in each extension directory

### 2. Display in Extension Popup
- Open the extension popup
- Click the gear icon (⚙️) to open Technical Details
- View "Extension Version" showing: `2.2.24 (build 2025.12.15.0630)`

### 3. Debug Information
- Build number is included in clipboard when copying debug info
- Debug info shows both version and deployment timestamp
- Helps track which extension build is being tested

## Usage

### Deploy Extensions with Build Tracking
```bash
# Deploy all extensions with fresh build numbers
make ext-deploy
```

### View Build Information
1. Load extension in Chrome/Firefox
2. Click extension icon to open popup
3. Click gear icon (⚙️) in top-right
4. See "Extension Version" field with build number

### Manual Build Info Generation
```bash
# Generate build info for specific extension
python scripts/generate_build_info.py mcp-browser-extensions/chrome
```

## Implementation Details

### Files Modified
- **`scripts/generate_build_info.py`**: Build number generator
- **`Makefile`**: Integrated into `ext-deploy` target
- **`src/extensions/chrome/popup-enhanced.js`**: Loads and displays build info
- **`src/extensions/firefox/popup-enhanced.js`**: Loads and displays build info
- **`src/extensions/chrome/manifest.json`**: Allows access to `build-info.json`
- **`src/extensions/firefox/manifest.json`**: Allows access to `build-info.json`

### Generated File Structure
```json
{
  "version": "2.2.25",
  "build": "2025.12.15.0630",
  "deployed": "2025-12-15T06:30:00.123456+00:00",
  "extension": "chrome"
}
```

### How It Works

1. **During Deployment** (`make ext-deploy`):
   - Extensions are copied from `src/extensions/` to `mcp-browser-extensions/`
   - `generate_build_info.py` runs for each extension
   - Creates `build-info.json` with current timestamp

2. **In Extension Popup**:
   - JavaScript loads `build-info.json` using `chrome.runtime.getURL()`
   - Displays build number in Technical Details panel
   - Includes in debug info clipboard copy

3. **Manifest Permissions**:
   - Chrome (Manifest V3): `web_accessible_resources` allows popup to access file
   - Firefox (Manifest V2): `web_accessible_resources` array allows access

## Benefits for Development

### Track Changes During Development
- Quickly verify which extension build is installed
- Identify when changes were last deployed
- Debug issues by knowing exact deployment time

### Coordinate Across Team
- Share exact build numbers when reporting issues
- Verify everyone is testing same build
- Track build history in debug logs

### Zero Overhead
- Automatic generation during normal deployment
- No manual versioning needed
- No impact on extension performance

## Example Workflow

```bash
# 1. Make changes to extension source
vim src/extensions/chrome/background-enhanced.js

# 2. Deploy with new build number
make ext-deploy
# Output:
# ✓ Generated mcp-browser-extensions/chrome/build-info.json
#   Version: 2.2.25
#   Build: 2025.12.15.0630

# 3. Reload extension in browser
# Chrome: chrome://extensions/ → Click reload button

# 4. Verify new build is loaded
# Open popup → Click gear → Check "Extension Version"
# Should show: 2.2.24 (build 2025.12.15.0630)
```

## Future Enhancements

Potential improvements to the build tracking system:

- **Git commit hash**: Include git commit in build info
- **Change detection**: Only increment build if files changed
- **Build history**: Maintain log of all builds
- **Release vs Development**: Different build number schemes
- **CLI command**: `mcp-browser build-info` to show current build

## Troubleshooting

### Build Info Not Showing
1. Verify `build-info.json` exists in extension directory
2. Check browser console for fetch errors
3. Ensure extension was reloaded after deployment
4. Verify manifest includes `web_accessible_resources`

### Old Build Number After Deployment
1. Hard-reload extension in browser
2. Check timestamp on `build-info.json` file
3. Verify `make ext-deploy` completed successfully
4. Clear browser extension cache and reinstall

---

**Last Updated**: 2025-12-15
**Version**: 1.0
