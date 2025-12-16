# Safari Extension Guide for MCP Browser

This guide explains how to port the MCP Browser extension to Safari. Safari extensions differ significantly from Chrome/Firefox extensions as they require a macOS app wrapper and Xcode project.

## Table of Contents

1. [Safari Extension Requirements](#safari-extension-requirements)
2. [Quick Start](#quick-start)
3. [Automated Conversion](#automated-conversion)
4. [Manual Setup](#manual-setup)
5. [Code Signing](#code-signing)
6. [Testing](#testing)
7. [Distribution](#distribution)
8. [Common Issues](#common-issues)
9. [Safari-Specific Considerations](#safari-specific-considerations)

## Safari Extension Requirements

### System Requirements

- **macOS 11.0 or later** (Big Sur or newer)
- **Xcode 13.0 or later** (free from Mac App Store)
- **Safari 14.0 or later** (Safari 17+ recommended for full MV3 support)
- **Apple Developer account** (free for development, $99/year for distribution)

### Safari Extension Architecture

Safari extensions must be packaged within a native macOS application:

```
MCP Browser.app/
├── Contents/
│   ├── MacOS/
│   │   └── MCP Browser (native app binary)
│   ├── Resources/
│   │   └── Extension.appex (Safari extension)
│   │       └── Resources/
│   │           ├── manifest.json
│   │           ├── background.js
│   │           ├── content.js
│   │           └── ... (all web extension files)
│   ├── Info.plist
│   └── ... (other app resources)
```

The native app acts as a container and can be minimal (just a simple UI explaining the extension).

## Quick Start

Use the automated script to convert the Chrome extension.

Note: the converter expects a materialized web-extension directory. Depending on your workflow, that may be:
- `mcp-browser-extension/` (created by `mcp-browser init --project`), or
- `mcp-browser-extensions/chrome/` (created by `mcp-browser setup` or `make ext-deploy`)

Update the script’s `CHROME_EXT_DIR` if your local directory name differs.

```bash
# Navigate to the project root
cd /path/to/mcp-browser

# Run the conversion script
bash scripts/create-safari-extension.sh
```

This will:
1. Check for required tools
2. Create the Safari extension directory structure
3. Convert the Chrome extension using Apple's converter tool
4. Generate the Xcode project
5. Provide next steps for manual configuration

## Automated Conversion

### Using safari-web-extension-converter

Apple provides an official tool to convert Chrome/Firefox extensions to Safari:

```bash
# Install Xcode Command Line Tools (if not already installed)
xcode-select --install

# Convert the extension (done by script)
xcrun safari-web-extension-converter \
  mcp-browser-extension \
  --project-location mcp-browser-extension-safari \
  --app-name "MCP Browser" \
  --bundle-identifier com.mcpbrowser.extension \
  --swift
```

### Conversion Tool Features

The converter:
- Creates Xcode project automatically
- Generates Swift-based macOS app wrapper
- Converts manifest.json to Safari-compatible format
- Sets up proper bundle structure
- Creates app icons and resources

### What Gets Converted

✅ **Automatically handled:**
- Manifest V3 structure
- Service workers (Safari 17+)
- Content scripts
- Permissions
- Icons
- HTML/CSS/JS files

⚠️ **Requires manual adjustment:**
- Host permissions (different syntax)
- Native messaging (if used)
- Some Chrome-specific APIs
- Code signing configuration

## Manual Setup

If you need to set up manually or customize the conversion:

### Step 1: Create Xcode Project

1. Open Xcode
2. Create new project: **File → New → Project**
3. Select **macOS → App** template
4. Configure project:
   - Product Name: `MCP Browser`
   - Bundle Identifier: `com.mcpbrowser.extension`
   - Interface: SwiftUI or Storyboard
   - Language: Swift

### Step 2: Add Safari Extension Target

1. In Xcode: **File → New → Target**
2. Select **Safari Extension**
3. Configure extension:
   - Product Name: `MCP Browser Extension`
   - Bundle Identifier: `com.mcpbrowser.extension.Extension`
   - Language: Swift

### Step 3: Copy Web Extension Resources

Copy all files from `mcp-browser-extension/` to the extension's Resources folder:

```bash
cp -r mcp-browser-extension/* \
  "mcp-browser-extension-safari/MCP Browser Extension/Resources/"
```

### Step 4: Configure manifest.json

Safari requires some manifest adjustments. The Safari-specific manifest is already in:
`mcp-browser-extension-safari/Resources/manifest.json`

Key differences from Chrome:
- Browser-specific keys must be prefixed with `browser_`
- Some permissions have different names
- Host permissions use different patterns

### Step 5: Update Background Script

Safari 17+ supports MV3 service workers, but some APIs differ. The Safari-compatible background script is in:
`mcp-browser-extension-safari/Resources/background.js`

Changes from Chrome:
- Use `browser` API namespace (Safari supports both `chrome` and `browser`)
- WebSocket connections work the same way
- Storage API is compatible

## Code Signing

### Development Signing (Free)

For local testing, use automatic signing:

1. Open project in Xcode
2. Select the app target
3. Go to **Signing & Capabilities**
4. Enable **Automatically manage signing**
5. Select your development team (free Apple ID)

### Distribution Signing ($99/year)

For distribution via App Store or direct download:

1. **Join Apple Developer Program** ($99/year)
   - https://developer.apple.com/programs/

2. **Create certificates:**
   - Developer ID Application Certificate (for direct distribution)
   - Mac App Distribution Certificate (for App Store)

3. **Configure provisioning:**
   - In Xcode: Signing & Capabilities
   - Select appropriate team and certificate
   - Enable App Sandbox and required capabilities

4. **Enable required capabilities:**
   - Outgoing Connections (Client): For WebSocket connections
   - Network (may be needed for localhost connections)

### Notarization (Required for macOS 10.14.5+)

For distribution outside App Store:

```bash
# Build and archive
xcodebuild archive -scheme "MCP Browser" \
  -archivePath "MCP Browser.xcarchive"

# Export for notarization
xcodebuild -exportArchive \
  -archivePath "MCP Browser.xcarchive" \
  -exportPath "export" \
  -exportOptionsPlist exportOptions.plist

# Submit for notarization
xcrun notarytool submit "MCP Browser.zip" \
  --apple-id "your@email.com" \
  --team-id "TEAM_ID" \
  --password "app-specific-password"

# Wait for notarization to complete (can take minutes)
xcrun notarytool wait <submission-id> --apple-id "your@email.com"

# Staple notarization ticket
xcrun stapler staple "MCP Browser.app"
```

## Testing

### Enable Developer Mode

1. Open Safari
2. **Safari → Settings → Advanced**
3. Enable **Show Develop menu in menu bar**

### Load Extension for Testing

#### Method 1: From Xcode (Recommended)

1. Open the Xcode project
2. Select the app scheme
3. Click **Run** (⌘R)
4. The app will launch and install the extension
5. In Safari: **Develop → Allow Unsigned Extensions**
6. Enable the extension in **Safari → Settings → Extensions**

#### Method 2: Build and Load Manually

```bash
# Build the app
xcodebuild -scheme "MCP Browser" \
  -configuration Debug \
  -derivedDataPath build

# Run the app
open "build/Build/Products/Debug/MCP Browser.app"
```

### Testing with Safari Technology Preview

Safari Technology Preview gets the latest features first:

1. Download from: https://developer.apple.com/safari/technology-preview/
2. Enable developer mode (same as regular Safari)
3. Test extension with latest WebExtension APIs

### Debugging

#### Safari Web Inspector

1. In Safari: **Develop → Web Extension Background Pages → MCP Browser Extension**
2. Use Console, Network, and Debugger tabs
3. Set breakpoints in background.js

#### Content Script Debugging

1. Navigate to a page where content script runs
2. **Develop → Show Web Inspector**
3. Content script logs appear in Console
4. View injected scripts in Sources/Debugger tab

#### Extension Console

View extension-specific logs:
```javascript
// In background.js or content.js
console.log('[MCP Browser]', 'Debug message');
```

Check console in: **Develop → Web Extension Background Pages**

## Distribution

### Option 1: App Store Distribution

**Advantages:**
- Trusted distribution channel
- Automatic updates
- No notarization needed
- Discoverable by users

**Steps:**

1. **Prepare for submission:**
   - Complete app metadata
   - Create app icons (all required sizes)
   - Write app description
   - Take screenshots

2. **Create App Store listing:**
   - Go to App Store Connect
   - Create new macOS app
   - Fill in all required fields

3. **Archive and upload:**
   ```bash
   # Archive in Xcode
   Product → Archive

   # Upload to App Store Connect
   Window → Organizer → Distribute App
   ```

4. **Submit for review:**
   - App Store review typically takes 1-3 days
   - Address any rejection reasons
   - Once approved, app goes live

### Option 2: Direct Distribution (Developer ID)

**Advantages:**
- Full control over distribution
- No App Store review
- Can distribute beta versions

**Requirements:**
- Paid Apple Developer account ($99/year)
- Developer ID certificate
- Notarization

**Steps:**

1. **Sign with Developer ID:**
   ```bash
   codesign --deep --force --verify --verbose \
     --sign "Developer ID Application: Your Name" \
     "MCP Browser.app"
   ```

2. **Create DMG installer:**
   ```bash
   # Create DMG for distribution
   hdiutil create -volname "MCP Browser" \
     -srcfolder "MCP Browser.app" \
     -ov -format UDZO "MCP-Browser-Safari.dmg"
   ```

3. **Notarize** (see Code Signing section)

4. **Distribute:**
   - Upload to your website
   - Share direct download link
   - Users drag app to Applications folder

### Option 3: Self-Signed (Development Only)

**For internal testing only:**

1. Users must enable **Allow unsigned extensions** in Safari
2. Requires rebuilding periodically (provisioning expiry)
3. Not suitable for public distribution

## Common Issues

### Issue: Extension Not Appearing in Safari

**Solution:**
1. Check that app is running (menubar or Dock)
2. Enable in Safari Settings → Extensions
3. Allow unsigned extensions (Develop menu)
4. Restart Safari

### Issue: WebSocket Connection Fails

**Possible causes:**

1. **App Sandbox restrictions**
   - Solution: Enable "Outgoing Connections (Client)" in capabilities
   - Or disable App Sandbox for development (not recommended for distribution)

2. **Localhost/127.0.0.1 blocked**
   - Solution: Add network entitlement
   - Or use `host_permissions` in manifest

3. **Port scanning blocked**
   - Safari may restrict rapid connection attempts
   - Implement exponential backoff in connection logic

### Issue: Content Script Not Injecting

**Solutions:**
- Verify `matches` patterns in manifest
- Check that script files are in Resources folder
- Verify `all_frames: true` for iframe support
- Check Safari console for injection errors

### Issue: Permission Denied Errors

**Solutions:**
1. Review requested permissions in manifest
2. Check App Sandbox capabilities
3. Add required entitlements in Xcode
4. For localhost: add `host_permissions`

### Issue: Extension Crashes on Startup

**Debugging steps:**
1. Check Console.app for crash logs
2. Review Safari Developer console
3. Simplify background script to isolate issue
4. Check for Safari-incompatible APIs

### Issue: Code Signing Failed

**Solutions:**
1. Verify certificate is valid and not expired
2. Check bundle identifier matches provisioning profile
3. Clean build folder: Product → Clean Build Folder
4. Try manual signing instead of automatic

## Safari-Specific Considerations

### API Differences

#### Chrome vs Safari API Namespaces

Safari supports both `chrome.*` and `browser.*` namespaces:

```javascript
// Both work in Safari
chrome.runtime.sendMessage(...)
browser.runtime.sendMessage(...)

// For cross-browser compatibility, use:
const browserAPI = typeof browser !== 'undefined' ? browser : chrome;
```

#### Promise vs Callback APIs

Safari prefers promises:

```javascript
// Chrome (callback)
chrome.tabs.query({active: true}, (tabs) => { ... });

// Safari (promise - preferred)
browser.tabs.query({active: true}).then((tabs) => { ... });

// Cross-browser
const tabs = await chrome.tabs.query({active: true});
```

### Manifest Differences

#### Host Permissions

```json
// Chrome
"host_permissions": [
  "http://localhost/*",
  "ws://localhost/*"
]

// Safari - same format, but may need additional entitlements
"host_permissions": [
  "http://localhost/*",
  "http://127.0.0.1/*",
  "ws://localhost/*",
  "ws://127.0.0.1/*"
]
```

#### Browser Action vs Action

Safari 17+ supports MV3 `action`, but older versions may need:

```json
// MV3 (Safari 17+)
"action": { ... }

// MV2 compatibility (Safari 14-16)
"browser_action": { ... }
```

### Performance Considerations

1. **Service Worker Lifecycle**
   - Safari may be more aggressive about terminating service workers
   - Implement proper state persistence
   - Use chrome.storage for state management

2. **Memory Management**
   - Safari has stricter memory limits
   - Clean up unused resources promptly
   - Monitor memory usage in Activity Monitor

3. **Battery Impact**
   - Minimize background activity
   - Use appropriate intervals for timers
   - Implement efficient WebSocket reconnection

### Content Security Policy

Safari enforces stricter CSP:

```json
"content_security_policy": {
  "extension_pages": "script-src 'self'; object-src 'self'"
}
```

Avoid:
- Inline scripts
- `eval()` and similar
- External script URLs

### Native App Requirements

The macOS wrapper app should:

1. **Provide user value:**
   - Settings/preferences UI
   - Extension status indicator
   - Quick access to features

2. **Handle lifecycle:**
   - Launch at login (optional)
   - Menubar presence
   - Graceful shutdown

3. **Communicate with extension:**
   - Use native messaging if needed
   - Share storage/preferences
   - Coordinate updates

## Resources

### Official Documentation

- [Safari Web Extensions](https://developer.apple.com/documentation/safariservices/safari_web_extensions)
- [Converting Extensions](https://developer.apple.com/documentation/safariservices/safari_web_extensions/converting_a_web_extension_for_safari)
- [App Sandbox](https://developer.apple.com/documentation/security/app_sandbox)
- [Code Signing Guide](https://developer.apple.com/support/code-signing/)

### Tools

- [safari-web-extension-converter](https://developer.apple.com/documentation/safariservices/safari_web_extensions/converting_a_web_extension_for_safari)
- [Xcode](https://developer.apple.com/xcode/)
- [Safari Technology Preview](https://developer.apple.com/safari/technology-preview/)

### Community

- [Apple Developer Forums - Safari Extensions](https://developer.apple.com/forums/tags/safari-extensions)
- [WebExtensions Community Group](https://www.w3.org/community/webextensions/)

## Next Steps

After setting up the Safari extension:

1. **Test thoroughly:**
   - All console capture features
   - WebSocket connections
   - DOM manipulation
   - Content extraction

2. **Optimize for Safari:**
   - Adjust timings if needed
   - Implement Safari-specific fixes
   - Test on multiple macOS versions

3. **Prepare for distribution:**
   - Create app icon assets
   - Write user documentation
   - Set up update mechanism
   - Choose distribution method

4. **Maintain compatibility:**
   - Keep Chrome and Safari versions in sync
   - Test updates on both platforms
   - Monitor user feedback

## Support

For issues specific to this MCP Browser Safari port:
- Open an issue on the GitHub repository
- Check existing issues for solutions
- Contribute improvements via pull requests

For Safari extension development questions:
- Apple Developer Forums
- Stack Overflow (tag: safari-web-extension)
