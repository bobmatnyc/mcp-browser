# AppleScript Feature Usage Guide

Complete user guide for using mcp-browser's AppleScript fallback feature on macOS.

## Table of Contents

- [Introduction](#introduction)
- [Quick Start (5 Minutes)](#quick-start-5-minutes)
- [Configuration Options](#configuration-options)
- [macOS Permission Setup](#macos-permission-setup)
- [Supported Operations](#supported-operations)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [FAQ](#faq)
- [Additional Resources](#additional-resources)

## Introduction

### What is the AppleScript Fallback?

The AppleScript fallback is a built-in feature that allows mcp-browser to control Safari or Chrome on macOS without requiring a browser extension. It provides basic browser automation capabilities using macOS's native AppleScript technology.

### When Does It Activate?

AppleScript fallback activates automatically in these scenarios:

- **Extension Not Installed**: You haven't installed the browser extension yet
- **Extension Disconnected**: Browser extension loses connection to the MCP server
- **Manual Override**: You've configured `mode: "applescript"` in settings
- **Extension Restricted**: Corporate or security policies prevent extension installation

The fallback is completely transparent - you'll see a note in responses indicating AppleScript was used.

### Benefits and Limitations

**Benefits:**
- Zero configuration required (works out of the box)
- No browser extension installation needed
- Perfect for quick testing and QA workflows
- Works on macOS without any setup
- Automatic fallback when extension unavailable

**Limitations:**
- Console logs NOT available (browser security restriction)
- Slower performance (~100-500ms vs 10-50ms for extension)
- CSS selectors only (no XPath or text matching)
- Limited to Safari and Chrome browsers
- macOS only (not available on Windows/Linux)
- No real-time monitoring capabilities

## Quick Start (5 Minutes)

### Automatic Fallback (Recommended)

The AppleScript fallback works automatically on macOS:

1. **No Extension Installed**: AppleScript fallback activates automatically
2. **Extension Disconnected**: Falls back to AppleScript seamlessly
3. **Zero Configuration**: Works out of the box with Safari

### First-Time Setup

**Step 1: Install mcp-browser**
```bash
pip install mcp-browser
```

**Step 2: Grant Permissions (One-Time)**

The first time you use AppleScript control, macOS will ask for permission:

1. A dialog appears: "Do you want to allow Terminal to control Safari?"
2. Click **"Allow"**
3. Done!

If you missed the prompt:
1. Open **System Settings** > **Privacy & Security** > **Automation**
2. Find your terminal app (Terminal, iTerm2, VS Code, etc.)
3. Enable **Safari** and/or **Google Chrome**

**Step 3: Test It Works**
```bash
# Start mcp-browser
mcp-browser start

# Use MCP tools from Claude Code
# Navigate, click, fill forms - all work automatically!
```

That's it! AppleScript fallback is ready to use.

## Configuration Options

### Default Configuration (Automatic Fallback)

No configuration needed! The default settings work for most users:

```json
{
  "browser_control": {
    "mode": "auto",
    "applescript_browser": "Safari",
    "fallback_enabled": true
  }
}
```

**How it works:**
1. Tries browser extension first
2. Falls back to AppleScript if extension unavailable
3. Uses Safari as the default browser

### Custom Configuration

Create or edit `~/.config/mcp-browser/config.json`:

**Force AppleScript Only (No Extension):**
```json
{
  "browser_control": {
    "mode": "applescript",
    "applescript_browser": "Safari"
  }
}
```

**Use Case:** Testing without extension, restricted environments

**Use Chrome Instead of Safari:**
```json
{
  "browser_control": {
    "mode": "auto",
    "applescript_browser": "Google Chrome"
  }
}
```

**Use Case:** Prefer Chrome for testing, Chrome-specific features

**Disable Fallback (Extension Only):**
```json
{
  "browser_control": {
    "mode": "extension",
    "fallback_enabled": false
  }
}
```

**Use Case:** Production environments requiring console logs

**Full Configuration Reference:**
```json
{
  "browser_control": {
    "mode": "auto",                    // "auto", "extension", "applescript"
    "applescript_browser": "Safari",   // "Safari" or "Google Chrome"
    "fallback_enabled": true,          // Enable/disable fallback
    "prompt_for_permissions": true     // Show permission instructions
  }
}
```

## macOS Permission Setup

### Initial Permission Prompt

The first time you use AppleScript control, macOS will ask for permission:

**Safari Permission Prompt:**
```
"Terminal" would like to control "Safari".

This will allow "Terminal" to control and perform actions in
"Safari", and to read sensitive information from "Safari",
including passwords.

[Don't Allow]  [OK]
```

Click **"OK"** to grant permission.

### Manual Permission Setup

If you accidentally denied permission or need to change settings:

**Step-by-Step:**

1. **Open System Settings**
   - Click Apple menu () → System Settings
   - Or search Spotlight for "System Settings"

2. **Navigate to Automation**
   - Select **Privacy & Security** from the sidebar
   - Click **Automation** (you may need to scroll down)

3. **Enable Terminal Permissions**
   - Find your terminal app in the list:
     - Terminal
     - iTerm2
     - Visual Studio Code
     - Any app running mcp-browser
   - Expand the app to see browser options
   - Check the box next to **Safari** or **Google Chrome**

4. **Restart Browser**
   - Quit Safari/Chrome completely
   - Relaunch the browser
   - AppleScript commands should now work

5. **Verify Permissions**
   ```bash
   # Test Safari access
   osascript -e 'tell application "Safari" to get URL of current tab of window 1'

   # Or run system diagnostics
   mcp-browser doctor
   ```

### Troubleshooting Permissions

**Error: "Safari does not have UI scripting enabled"**

**Fix:**
1. System Settings > Privacy & Security > Automation
2. Enable your terminal app
3. Restart Safari
4. Try again

**Error: "Operation not permitted"**

**Fix:**
1. Check that Safari/Chrome is in the Automation list
2. Verify your terminal app has permission
3. Try running with `sudo` (not recommended, but can help diagnose)

**Alternative: Use Browser Extension**

If permissions are problematic, install the browser extension for full functionality:
```bash
mcp-browser quickstart  # Interactive installation guide
```

## Supported Operations

### Fully Supported Features

| Feature | AppleScript | Extension | Notes |
|---------|-------------|-----------|-------|
| **Navigate to URLs** | ✅ | ✅ | Opens any URL in browser |
| **Click elements** | ✅ (CSS only) | ✅ (CSS, XPath, text) | AppleScript limited to CSS selectors |
| **Fill form fields** | ✅ | ✅ | Enter text in input fields |
| **Submit forms** | ✅ | ✅ | Submit forms via click or enter |
| **Get element info** | ✅ (basic) | ✅ (full) | Read element properties |
| **Execute JavaScript** | ✅ | ❌ | AppleScript can run custom JS |
| **Get current URL** | ✅ | ✅ | Read active tab URL |
| **Take screenshots** | ✅ | ✅ | Via Playwright (independent) |

### Features NOT Available with AppleScript

| Feature | Available | Workaround |
|---------|-----------|------------|
| **Console logs** | ❌ | Install extension or use browser DevTools |
| **Real-time monitoring** | ❌ | Extension required for live updates |
| **Wait for element** | ❌ | Use JavaScript execution with custom wait logic |
| **Dropdown selection** | ❌ | Use JavaScript execution or click to open |
| **XPath selectors** | ❌ | Convert to CSS selectors |
| **Text matching** | ❌ | Use CSS selectors or JavaScript |
| **Multi-tab control** | ❌ | Extension required for tab management |
| **Content extraction** | ❌ | Extension required (Readability API) |

### Performance Comparison

| Operation | Extension | AppleScript | Difference |
|-----------|-----------|-------------|------------|
| Navigate | 10-50ms | 100-300ms | 5-10x slower |
| Click | 10-30ms | 100-200ms | 8-10x slower |
| Fill field | 10-30ms | 100-250ms | 8-12x slower |
| Get element | 10-20ms | 100-200ms | 10x slower |
| Execute JS | N/A | 150-500ms | AppleScript only |

**Recommendation:** Use extension for production workflows. AppleScript is suitable for:
- Quick QA testing
- Ad-hoc browser control
- Environments where extension installation is restricted
- Simple navigation and form filling

## Common Use Cases

### Use Case 1: QA Testing Without Extension

Perfect for quick QA checks when you don't want to install the extension:

**Scenario:** Test user registration flow on staging site

```bash
# Start mcp-browser
mcp-browser start

# From Claude Code, ask:
# "Navigate to https://staging.example.com/register"
# "Fill the email field with test@example.com"
# "Fill the password field with SecurePass123"
# "Click the register button"
# "Verify we redirected to /welcome"
```

**Benefits:**
- No extension installation needed
- Quick setup for temporary testing
- Works across different browsers (Safari/Chrome)

### Use Case 2: Automated Browser Control from Python

Automate browser tasks using the AppleScript service directly:

```python
from src.services.applescript_service import AppleScriptService
import asyncio

async def test_login_flow():
    service = AppleScriptService()

    # Navigate to login page
    await service.navigate("https://app.example.com/login", "Safari")
    await asyncio.sleep(1)  # Wait for page load

    # Fill login form
    await service.fill_field("#username", "test@example.com", "Safari")
    await service.fill_field("#password", "password123", "Safari")

    # Click submit
    await service.click("#login-button", "Safari")
    await asyncio.sleep(2)  # Wait for redirect

    # Verify redirect
    result = await service.get_current_url("Safari")
    assert "/dashboard" in result["data"]
    print("Login test passed!")

# Run the test
asyncio.run(test_login_flow())
```

**Benefits:**
- Direct Python control
- No manual interaction needed
- Great for automated testing pipelines

### Use Case 3: Extension Backup

Run with extension as primary, AppleScript as automatic fallback:

**Configuration:**
```json
{
  "browser_control": {
    "mode": "auto"
  }
}
```

**How it works:**
1. Normal operation: Uses browser extension (fast, full features)
2. Extension disconnects: Automatically falls back to AppleScript
3. Extension reconnects: Automatically switches back to extension

**Benefits:**
- Seamless operation during extension updates
- No interruption if extension crashes
- Best of both worlds: speed when available, reliability always

### Use Case 4: Corporate Environment

Use AppleScript when IT policies prevent extension installation:

**Scenario:** Testing internal web applications

```bash
# Configure AppleScript-only mode
cat > ~/.config/mcp-browser/config.json << EOF
{
  "browser_control": {
    "mode": "applescript",
    "applescript_browser": "Safari"
  }
}
EOF

# Use mcp-browser normally
mcp-browser start

# All browser operations work via AppleScript
# Note: Console logs won't be available
```

**Benefits:**
- Works without extension approval process
- No additional software installation
- Complies with security policies

### Use Case 5: Quick Website Scraping

Extract data from websites using AppleScript:

```python
async def scrape_product_info():
    service = AppleScriptService()

    # Navigate to product page
    await service.navigate("https://shop.example.com/product/123", "Safari")
    await asyncio.sleep(2)

    # Extract product title
    title_result = await service.execute_javascript(
        "document.querySelector('.product-title').textContent",
        "Safari"
    )

    # Extract price
    price_result = await service.execute_javascript(
        "document.querySelector('.price').textContent",
        "Safari"
    )

    print(f"Product: {title_result['data']}")
    print(f"Price: {price_result['data']}")

asyncio.run(scrape_product_info())
```

**Benefits:**
- No extension needed
- Direct JavaScript execution
- Simple data extraction

## Troubleshooting

### Common Errors

#### "Safari does not have UI scripting enabled"

**Symptom:**
```
Error: Safari does not have UI scripting enabled.
To enable: System Settings > Privacy & Security > Automation
```

**Cause:** macOS permissions not granted

**Solution:**
1. Open System Settings > Privacy & Security > Automation
2. Find your terminal app (Terminal, iTerm2, VS Code, etc.)
3. Enable Safari and/or Google Chrome
4. Restart Safari
5. Try again

**Quick test:**
```bash
osascript -e 'tell application "Safari" to get URL of current tab of window 1'
```

#### "Browser not running"

**Symptom:**
```
Error: Safari is not running
```

**Cause:** Safari/Chrome not open

**Solution:**
```bash
# Open Safari
open -a Safari

# Or open Chrome
open -a "Google Chrome"

# Then try your command again
```

**Pro tip:** AppleScript will auto-launch the browser if configured, but it's faster if already running.

#### "Selector not found"

**Symptom:**
```
Error: Could not find element matching selector '.button'
```

**Cause:**
- CSS selector doesn't match any elements
- Element not loaded yet
- Selector syntax error

**Solution:**
1. **Verify selector in DevTools:**
   - Open browser DevTools (F12)
   - Use Elements inspector
   - Test selector in console: `document.querySelector('.button')`

2. **Use simpler selectors:**
   ```
   ✅ Good: #submit-button
   ✅ Good: .btn-primary
   ✅ Good: button[type="submit"]

   ❌ Avoid: div > div > div > button:nth-child(3)
   ❌ Avoid: [data-test-id="complex-selector"]
   ```

3. **Add wait time:**
   ```python
   await service.navigate(url, "Safari")
   await asyncio.sleep(2)  # Wait for page load
   await service.click(".button", "Safari")
   ```

#### "AppleScript is only available on macOS"

**Symptom:**
```
Error: AppleScript is only available on macOS
```

**Cause:** Running on Linux or Windows

**Solution:** Install browser extension (required for non-macOS platforms)
```bash
mcp-browser quickstart  # Interactive installation guide
```

#### Performance is Slow

**Symptom:** Operations take 200-500ms each

**Cause:** AppleScript has ~100-500ms overhead per operation (normal behavior)

**Solutions:**

1. **Switch to extension** (10-50ms operations):
   ```bash
   mcp-browser quickstart  # Install extension
   ```

2. **Batch operations** when possible:
   ```python
   # Instead of multiple calls
   await service.fill_field("#name", "John", "Safari")
   await service.fill_field("#email", "john@example.com", "Safari")
   await service.fill_field("#phone", "555-1234", "Safari")

   # Use JavaScript to batch
   await service.execute_javascript("""
       document.querySelector('#name').value = 'John';
       document.querySelector('#email').value = 'john@example.com';
       document.querySelector('#phone').value = '555-1234';
   """, "Safari")
   ```

3. **Accept it for QA:** 100-500ms is acceptable for manual QA workflows

#### Console Logs Not Working

**Symptom:**
```
Note: Console log capture requires the browser extension.
```

**Cause:** Browser security restrictions prevent AppleScript access to console

**Solution:** Install browser extension for console log capture
```bash
mcp-browser quickstart  # Interactive installation with console log support
```

**Workaround:** Use browser DevTools manually:
1. Open DevTools (F12)
2. View Console tab
3. Monitor logs visually

### Diagnostic Commands

```bash
# Check overall system status
mcp-browser doctor

# Test Safari AppleScript access
osascript -e 'tell application "Safari" to get URL of current tab of window 1'

# Test Chrome AppleScript access
osascript -e 'tell application "Google Chrome" to get URL of active tab of window 1'

# Verify mcp-browser configuration
cat ~/.config/mcp-browser/config.json

# Check automation permissions
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation"

# Test navigation directly
python3 -c "
import asyncio
from src.services.applescript_service import AppleScriptService

async def test():
    service = AppleScriptService()
    result = await service.navigate('https://example.com', 'Safari')
    print(result)

asyncio.run(test())
"
```

## Best Practices

### DO: Recommended Practices

**1. Use for QA and Testing**
AppleScript is perfect for manual QA workflows and ad-hoc testing:
```bash
# Quick test of user registration
# Navigate, fill, click - all work great
```

**2. Keep Browser Open**
Faster response when browser already running:
```bash
# Before testing, open browser
open -a Safari

# Then run tests - faster initial response
```

**3. Use Simple Selectors**
Stick to straightforward CSS selectors:
```
✅ #submit-button
✅ .btn-primary
✅ button[type="submit"]
✅ input[name="email"]
```

**4. Handle Timeouts Properly**
AppleScript operations can take 100-500ms - add appropriate waits:
```python
await service.navigate(url, "Safari")
await asyncio.sleep(1)  # Wait for page load

await service.click(".button", "Safari")
await asyncio.sleep(0.5)  # Wait for action
```

**5. Batch Related Operations**
Group related actions together:
```python
async def fill_login_form():
    # All related actions in one function
    await service.fill_field("#username", username, "Safari")
    await service.fill_field("#password", password, "Safari")
    await service.click("#login-button", "Safari")
```

**6. Use Auto Mode for Flexibility**
```json
{
  "browser_control": {
    "mode": "auto"  // Extension when available, AppleScript fallback
  }
}
```

### DON'T: Avoid These Practices

**1. Don't Use for High-Frequency Automation**
Extension is much faster (10-50ms vs 100-500ms):
```
❌ AppleScript: CI/CD pipelines with thousands of operations
✅ Extension: Production automation
✅ AppleScript: Manual QA testing
```

**2. Don't Rely on Console Logs**
Use extension for debugging workflows requiring console output:
```
❌ AppleScript: Debugging JavaScript errors via console
✅ Extension: Full console log capture
```

**3. Don't Use Complex Selectors**
Keep selectors simple and reliable:
```
❌ div.container > ul.list > li:nth-child(3) > a.link
✅ .link-to-details
✅ #detail-link
```

**4. Don't Expect Real-Time Monitoring**
AppleScript is request-response only:
```
❌ AppleScript: Monitor console for errors in real-time
✅ Extension: Live console monitoring
```

**5. Don't Skip Permission Setup**
Always grant automation permissions properly:
```
❌ Ignore permission prompts (won't work)
✅ Enable automation in System Settings
```

### When to Use Extension vs AppleScript

**Use Browser Extension When:**
- Need console log capture
- Performance critical (automation, CI/CD)
- Real-time monitoring required
- Running many operations
- Need advanced selectors (XPath, text matching)
- Multi-tab management needed

**Use AppleScript When:**
- Quick QA testing
- Extension not available
- Automated browser control from Python
- Prefer zero-config setup
- Extension installation restricted
- Simple navigation and form filling

## Examples

### Example 1: E-commerce Checkout Test

Complete checkout flow using AppleScript:

```python
from src.services.applescript_service import AppleScriptService
import asyncio

async def test_checkout():
    service = AppleScriptService()
    browser = "Safari"

    print("Starting checkout test...")

    # Step 1: Navigate to product
    print("1. Opening product page...")
    await service.navigate("https://shop.example.com/product/123", browser)
    await asyncio.sleep(2)

    # Step 2: Add to cart
    print("2. Adding to cart...")
    await service.click(".add-to-cart-button", browser)
    await asyncio.sleep(1)

    # Step 3: Go to checkout
    print("3. Going to checkout...")
    await service.navigate("https://shop.example.com/checkout", browser)
    await asyncio.sleep(2)

    # Step 4: Fill shipping info
    print("4. Filling shipping information...")
    await service.fill_field("#name", "John Doe", browser)
    await asyncio.sleep(0.3)

    await service.fill_field("#address", "123 Main St", browser)
    await asyncio.sleep(0.3)

    await service.fill_field("#city", "San Francisco", browser)
    await asyncio.sleep(0.3)

    await service.fill_field("#zip", "94102", browser)
    await asyncio.sleep(0.3)

    # Step 5: Submit order
    print("5. Submitting order...")
    await service.click("#submit-order", browser)
    await asyncio.sleep(3)

    # Step 6: Verify success
    print("6. Verifying order confirmation...")
    result = await service.get_current_url(browser)

    if "/order-confirmation" in result["data"]:
        print("✅ Checkout test PASSED")
    else:
        print(f"❌ Checkout test FAILED - URL: {result['data']}")

# Run the test
asyncio.run(test_checkout())
```

### Example 2: Form Validation Testing

Test form validation using AppleScript:

```python
async def test_form_validation():
    service = AppleScriptService()
    browser = "Safari"

    print("Testing form validation...")

    # Step 1: Open form
    print("1. Opening contact form...")
    await service.navigate("https://app.example.com/contact", browser)
    await asyncio.sleep(2)

    # Step 2: Test required field validation (submit empty form)
    print("2. Testing required field validation...")
    await service.click("#submit", browser)
    await asyncio.sleep(1)

    # Step 3: Check error message appears
    print("3. Checking for error message...")
    error_check = await service.execute_javascript(
        "document.querySelector('.error-message')?.textContent || ''",
        browser
    )

    if error_check["success"] and "required" in error_check["data"].lower():
        print("✅ Required field validation working")
    else:
        print("❌ Required field validation not working")

    # Step 4: Fill form correctly
    print("4. Filling form with valid data...")
    await service.fill_field("#name", "John Doe", browser)
    await service.fill_field("#email", "john@example.com", browser)
    await service.fill_field("#message", "Test message", browser)

    # Step 5: Submit again
    print("5. Submitting valid form...")
    await service.click("#submit", browser)
    await asyncio.sleep(2)

    # Step 6: Verify success
    result = await service.get_current_url(browser)

    if "/thank-you" in result["data"]:
        print("✅ Form submission test PASSED")
    else:
        print("❌ Form submission test FAILED")

asyncio.run(test_form_validation())
```

### Example 3: Multi-Step User Registration

Complete user registration workflow:

```python
async def test_user_registration():
    service = AppleScriptService()
    browser = "Safari"

    print("Testing user registration workflow...")

    # Step 1: Registration
    print("\n=== Step 1: Registration ===")
    await service.navigate("https://app.example.com/register", browser)
    await asyncio.sleep(2)

    await service.fill_field("#email", "newuser@example.com", browser)
    await asyncio.sleep(0.3)

    await service.fill_field("#password", "SecurePass123!", browser)
    await asyncio.sleep(0.3)

    await service.fill_field("#confirm-password", "SecurePass123!", browser)
    await asyncio.sleep(0.3)

    await service.click("#register-button", browser)
    await asyncio.sleep(3)

    # Step 2: Email verification (simulated)
    print("\n=== Step 2: Email Verification ===")
    # In real scenario, you'd read verification link from email
    verification_url = "https://app.example.com/verify?token=abc123"
    await service.navigate(verification_url, browser)
    await asyncio.sleep(2)

    await service.click("#verify-button", browser)
    await asyncio.sleep(2)

    # Step 3: Profile setup
    print("\n=== Step 3: Profile Setup ===")
    await service.fill_field("#displayName", "John Doe", browser)
    await asyncio.sleep(0.3)

    await service.fill_field("#bio", "Software developer", browser)
    await asyncio.sleep(0.3)

    await service.click("#save-profile", browser)
    await asyncio.sleep(2)

    # Step 4: Verify completion
    print("\n=== Step 4: Verification ===")
    result = await service.get_current_url(browser)

    if "/dashboard" in result["data"]:
        print("✅ User registration workflow PASSED")

        # Get welcome message
        welcome = await service.execute_javascript(
            "document.querySelector('.welcome-message')?.textContent || ''",
            browser
        )
        print(f"Welcome message: {welcome['data']}")
    else:
        print(f"❌ Registration workflow FAILED - URL: {result['data']}")

asyncio.run(test_user_registration())
```

### Example 4: Data Extraction

Extract product information from multiple pages:

```python
async def extract_product_catalog():
    service = AppleScriptService()
    browser = "Safari"
    products = []

    print("Extracting product catalog...")

    # Navigate to catalog
    await service.navigate("https://shop.example.com/catalog", browser)
    await asyncio.sleep(2)

    # Get product count
    count_result = await service.execute_javascript(
        "document.querySelectorAll('.product-card').length",
        browser
    )

    product_count = int(count_result["data"])
    print(f"Found {product_count} products")

    # Extract each product
    for i in range(product_count):
        print(f"\nExtracting product {i+1}/{product_count}...")

        # Extract product data using JavaScript
        product_data = await service.execute_javascript(f"""
            (function() {{
                const card = document.querySelectorAll('.product-card')[{i}];
                return {{
                    name: card.querySelector('.product-name')?.textContent,
                    price: card.querySelector('.price')?.textContent,
                    rating: card.querySelector('.rating')?.textContent,
                    url: card.querySelector('a')?.href
                }};
            }})();
        """, browser)

        if product_data["success"]:
            products.append(product_data["data"])
            print(f"  ✅ {product_data['data']}")

    print(f"\n✅ Extracted {len(products)} products")
    return products

# Run extraction
products = asyncio.run(extract_product_catalog())

# Save to file
import json
with open("products.json", "w") as f:
    json.dump(products, f, indent=2)

print("✅ Saved to products.json")
```

### Example 5: Accessibility Testing

Test accessibility features using AppleScript:

```python
async def test_accessibility():
    service = AppleScriptService()
    browser = "Safari"

    print("Running accessibility tests...")

    # Navigate to page
    await service.navigate("https://app.example.com", browser)
    await asyncio.sleep(2)

    # Test 1: Check for alt text on images
    print("\n1. Checking image alt text...")
    alt_test = await service.execute_javascript("""
        (function() {
            const images = document.querySelectorAll('img');
            const missing = [];
            images.forEach((img, i) => {
                if (!img.alt) {
                    missing.push(`Image ${i+1}: ${img.src}`);
                }
            });
            return {
                total: images.length,
                missing: missing,
                passed: missing.length === 0
            };
        })();
    """, browser)

    result = alt_test["data"]
    if result["passed"]:
        print(f"  ✅ All {result['total']} images have alt text")
    else:
        print(f"  ❌ {len(result['missing'])} images missing alt text")

    # Test 2: Check heading hierarchy
    print("\n2. Checking heading hierarchy...")
    heading_test = await service.execute_javascript("""
        (function() {
            const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'));
            const levels = headings.map(h => parseInt(h.tagName[1]));

            let valid = true;
            for (let i = 1; i < levels.length; i++) {
                if (levels[i] > levels[i-1] + 1) {
                    valid = false;
                    break;
                }
            }

            return {
                headings: headings.map(h => h.tagName),
                valid: valid
            };
        })();
    """, browser)

    if heading_test["data"]["valid"]:
        print("  ✅ Heading hierarchy is valid")
    else:
        print("  ❌ Heading hierarchy has skipped levels")

    # Test 3: Check form labels
    print("\n3. Checking form labels...")
    label_test = await service.execute_javascript("""
        (function() {
            const inputs = document.querySelectorAll('input, textarea, select');
            const unlabeled = [];

            inputs.forEach((input, i) => {
                const id = input.id;
                const label = id ? document.querySelector(`label[for="${id}"]`) : null;
                const ariaLabel = input.getAttribute('aria-label');

                if (!label && !ariaLabel) {
                    unlabeled.push(`Input ${i+1}: ${input.name || input.id || 'unnamed'}`);
                }
            });

            return {
                total: inputs.length,
                unlabeled: unlabeled,
                passed: unlabeled.length === 0
            };
        })();
    """, browser)

    result = label_test["data"]
    if result["passed"]:
        print(f"  ✅ All {result['total']} form inputs have labels")
    else:
        print(f"  ❌ {len(result['unlabeled'])} inputs missing labels")

    print("\n=== Accessibility Test Complete ===")

asyncio.run(test_accessibility())
```

## FAQ

### General Questions

**Q: Do I need to install anything for AppleScript fallback?**

A: No! AppleScript is built into macOS. Just grant permissions when prompted (one-time setup).

**Q: Can I use Chrome instead of Safari?**

A: Yes! Set `"applescript_browser": "Google Chrome"` in your config:
```json
{
  "browser_control": {
    "applescript_browser": "Google Chrome"
  }
}
```

**Q: Why can't I see console logs?**

A: Browser security prevents AppleScript access to the JavaScript console. This is a browser limitation, not an mcp-browser limitation. Use the browser extension for console log capture:
```bash
mcp-browser quickstart  # Install extension
```

**Q: Is AppleScript slower than the extension?**

A: Yes, ~100-500ms per operation vs 10-50ms for the extension. This is fine for QA testing but not ideal for high-volume automation. Consider using the extension for performance-critical workflows.

**Q: Can I use both extension and AppleScript?**

A: Yes! Set `"mode": "auto"` to use the extension when available and AppleScript as fallback:
```json
{
  "browser_control": {
    "mode": "auto"  // Extension first, AppleScript fallback
  }
}
```

### Technical Questions

**Q: Does it work on Linux or Windows?**

A: No, AppleScript is macOS-only. Use the browser extension on Linux/Windows:
```bash
mcp-browser quickstart  # Works on all platforms
```

**Q: Do I need Safari open?**

A: No, AppleScript will automatically open Safari if needed. However, it's faster if Safari is already running.

**Q: Can I control multiple browser windows?**

A: AppleScript controls the frontmost window of the specified browser. For multi-window control, use the browser extension which supports tab management.

**Q: Is it safe to grant automation permissions?**

A: Yes, permissions are app-specific. You're only allowing your terminal app (like Terminal or VS Code) to control Safari. It's limited to that specific app. You can revoke permissions anytime in System Settings.

**Q: Can I revoke permissions later?**

A: Yes! Go to System Settings > Privacy & Security > Automation and toggle off the permissions for any app.

### Troubleshooting Questions

**Q: Why do I keep getting permission errors?**

A: Check that:
1. System Settings > Privacy & Security > Automation
2. Your terminal app is listed and enabled
3. Safari/Chrome is checked under your terminal app
4. You've restarted the browser after granting permissions

**Q: My selectors aren't working. What's wrong?**

A: AppleScript only supports CSS selectors (not XPath or text matching). Use browser DevTools to test your selectors:
```javascript
// In browser console
document.querySelector('#your-selector')  // Should return element
```

**Q: Operations are timing out. How can I fix this?**

A: Add wait times between operations:
```python
await service.navigate(url, "Safari")
await asyncio.sleep(1)  # Wait for page load

await service.click(".button", "Safari")
await asyncio.sleep(0.5)  # Wait for action
```

**Q: Can I use AppleScript with headless browsers?**

A: No, AppleScript requires a visible browser window. For headless automation, use Playwright or Selenium directly.

## Additional Resources

### Documentation

- **[AppleScript Fallback Technical Guide](../APPLESCRIPT_FALLBACK.md)** - Technical implementation details and architecture
- **[Quick Start Guide](../../APPLESCRIPT_QUICK_START.md)** - 30-second setup for immediate use
- **[Installation Guide](../INSTALLATION.md)** - Complete installation instructions
- **[Troubleshooting Guide](../TROUBLESHOOTING.md)** - Common issues and solutions
- **[Release Automation](../../RELEASE.md)** - For maintainers

### Getting Help

- **GitHub Issues**: https://github.com/browserpymcp/mcp-browser/issues
- **Discussions**: https://github.com/browserpymcp/mcp-browser/discussions
- **Documentation**: https://github.com/browserpymcp/mcp-browser

### Interactive Commands

```bash
# System diagnostics
mcp-browser doctor         # Check system status and permissions

# Interactive setup
mcp-browser quickstart     # Guided extension installation

# Feature tutorial
mcp-browser tutorial       # Learn all mcp-browser features

# Check version
mcp-browser --version      # Show installed version
```

### Performance Tips

1. **Keep browser open** during testing sessions for faster response
2. **Use simple CSS selectors** (`#id`, `.class`, `button[type=submit]`)
3. **Batch related operations** together in functions
4. **Add appropriate waits** between operations (1-2 seconds for page loads)
5. **Consider extension** for high-frequency automation (10x faster)

### Security Considerations

**AppleScript Permissions:**
- Only grants control to specific terminal apps
- Permissions are app-specific (Terminal, VS Code, etc.)
- Can be revoked anytime in System Settings
- Review automation settings periodically

**JavaScript Execution:**
- AppleScript can execute JavaScript in browser context
- Same security context as the webpage
- Can access page data, cookies, localStorage
- Cannot bypass same-origin policy
- Validate and sanitize JavaScript input
- Avoid executing user-provided scripts

**Best Practices:**
1. Only grant permissions to trusted terminal apps
2. Review automation permissions regularly
3. Revoke permissions when no longer needed
4. Use extension mode for production (more sandboxed)
5. Validate all JavaScript before execution

### Browser Compatibility

**Safari (Recommended):**
- ✅ Native macOS support
- ✅ Faster AppleScript execution
- ✅ Better permission handling
- ✅ "Allow JavaScript from Apple Events" enabled by default
- ✅ More reliable for automation

**Google Chrome:**
- ✅ AppleScript support
- ⚠️ Slightly slower execution
- ⚠️ May require additional permissions
- ⚠️ Less optimized for AppleScript

**Other Browsers:**
- ❌ Firefox: No AppleScript support (use extension)
- ❌ Edge: No AppleScript support (use extension)
- ❌ Brave: No AppleScript support (use extension)

### Next Steps

**New Users:**
1. Grant macOS permissions (System Settings > Automation)
2. Test basic navigation: `mcp-browser doctor`
3. Try examples from this guide
4. Read [Quick Start](../../APPLESCRIPT_QUICK_START.md) for more

**Advanced Users:**
1. Review [Technical Guide](../APPLESCRIPT_FALLBACK.md)
2. Explore Python API in examples
3. Configure custom fallback behavior
4. Consider extension for production use

**Need Console Logs?**
Install the browser extension:
```bash
mcp-browser quickstart  # Interactive installation
```

---

**Last Updated:** November 2025
**Version:** 2.0.10+
**License:** MIT
