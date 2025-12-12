# Browser Extensions

This directory contains browser extensions for Chrome, Firefox, and Safari.

## Directory Structure

```
src/extensions/
├── chrome/              # Chrome MV3 extension (primary)
│   ├── manifest.json
│   ├── background-enhanced.js
│   ├── content.js
│   ├── popup-enhanced.html
│   ├── popup-enhanced.js
│   ├── Readability.js
│   └── icons/
├── firefox/             # Firefox MV2 extension (adapted from Chrome)
│   ├── manifest.json
│   ├── background-enhanced.js
│   ├── content.js
│   ├── popup-enhanced.html
│   ├── popup-enhanced.js
│   ├── Readability.js
│   └── icons/
├── safari/              # Safari extension resources
│   ├── manifest.json
│   ├── background.js
│   ├── popup.html
│   ├── popup.js
│   └── icons/
└── shared/              # Shared assets
    ├── Readability.js   # Mozilla Readability library
    └── icons/           # Icon files (all sizes and states)
```

## Browser-Specific Differences

### Chrome (Manifest V3)
- **Service Worker**: `background-enhanced.js`
- **API Namespace**: `chrome.*`
- **Popup**: Enhanced UI with connection status

### Firefox (Manifest V2)
- **Background Scripts**: `background-enhanced.js` (persistent)
- **API Namespace**: `browser.*` (with `chrome.*` polyfill)
- **Manifest Version**: 2 (Firefox doesn't fully support MV3 yet)
- **Popup**: Same enhanced UI as Chrome

### Safari
- **Manifest Version**: 3 (via safari-web-extension-converter)
- **Conversion**: Uses Apple's `xcrun safari-web-extension-converter`
- **Distribution**: Through Xcode project

## Building Extensions

Use the build script to package extensions:

```bash
# Build Chrome extension
python3 scripts/build_extension.py build --browser chrome

# Build Firefox extension
python3 scripts/build_extension.py build --browser firefox

# Build Safari extension
python3 scripts/build_extension.py build --browser safari

# Build all browsers
python3 scripts/build_extension.py build --browser chrome && \
python3 scripts/build_extension.py build --browser firefox && \
python3 scripts/build_extension.py build --browser safari
```

## Syncing Extensions

To sync shared assets and update Firefox from Chrome source:

```bash
python3 scripts/sync_extensions.py
```

This script:
1. Copies shared assets (icons, Readability.js) to all extension directories
2. Converts Chrome MV3 manifest to Firefox MV2 format
3. Validates all extensions have required files

## Development Workflow

### 1. Primary Development (Chrome)
All development happens in `src/extensions/chrome/`:
- Edit `background-enhanced.js`, `content.js`, `popup-enhanced.js`
- Test in Chrome via `chrome://extensions` → Load unpacked

### 2. Sync to Firefox
Run sync script to update Firefox extension:
```bash
python3 scripts/sync_extensions.py
```

### 3. Test Firefox
Load `src/extensions/firefox/` in Firefox:
- Open `about:debugging#/runtime/this-firefox`
- Click "Load Temporary Add-on"
- Select `manifest.json` from `src/extensions/firefox/`

### 4. Safari Conversion
Safari requires Xcode project conversion:
```bash
xcrun safari-web-extension-converter src/extensions/safari/
```

## Manifest Differences

### Chrome MV3
```json
{
  "manifest_version": 3,
  "background": {
    "service_worker": "background-enhanced.js"
  },
  "action": { ... },
  "host_permissions": [...]
}
```

### Firefox MV2
```json
{
  "manifest_version": 2,
  "background": {
    "scripts": ["background-enhanced.js"],
    "persistent": true
  },
  "browser_action": { ... },
  "permissions": [...],  // includes host_permissions
  "browser_specific_settings": {
    "gecko": {
      "id": "mcp-browser@anthropic.com",
      "strict_min_version": "109.0"
    }
  }
}
```

## Installation Instructions

### Chrome
1. Open `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `src/extensions/chrome/`

### Firefox
1. Open `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Navigate to `src/extensions/firefox/`
4. Select `manifest.json`

### Safari
1. Convert extension: `xcrun safari-web-extension-converter src/extensions/safari/`
2. Open generated Xcode project
3. Build and run in Xcode
4. Enable extension in Safari preferences

## Legacy Directories

The following directories are kept for backward compatibility:
- `mcp-browser-extension/` - Original Chrome extension (enhanced)
- `mcp-browser-extension-firefox/` - Original Firefox extension
- `mcp-browser-extension-safari-resources/` - Original Safari resources

**Note**: New development should use `src/extensions/` directories.

## Migration Notes

### From `mcp-browser-extension/` to `src/extensions/chrome/`
The Chrome extension has been moved from the root `mcp-browser-extension/` directory to `src/extensions/chrome/`. The build script (`scripts/build_extension.py`) now builds from the new location.

### Setup Command Update
The `mcp-browser setup` command should be updated to reference `src/extensions/chrome/` instead of `mcp-browser-extension/`.

## Version Management

Extension versions are synced with the main project version in `pyproject.toml`:
- **Current Version**: 2.2.1
- **Build Script**: Automatically syncs versions across manifests
- **Release Process**: Use `python3 scripts/build_extension.py release --bump [patch|minor|major]`

## Contributing

When making changes to extensions:
1. Edit files in `src/extensions/chrome/` (primary source)
2. Run `python3 scripts/sync_extensions.py` to update Firefox
3. Test in both Chrome and Firefox
4. Update Safari manually if needed
5. Commit changes to `src/extensions/` directories

## Related Commands

```bash
# Sync extensions
python3 scripts/sync_extensions.py

# Build specific browser
python3 scripts/build_extension.py build --browser chrome

# Get version info
python3 scripts/build_extension.py info --browser chrome

# Clean dist directory
python3 scripts/build_extension.py clean

# Sync versions with project
python3 scripts/build_extension.py sync --browser chrome
```
