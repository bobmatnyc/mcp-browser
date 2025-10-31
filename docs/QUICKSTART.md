# MCP Browser Quick Start Guide

## Installation in 3 Steps (5 Minutes Total)

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/browserpymcp/mcp-browser.git
cd mcp-browser

# Use the project management script for installation
./mcp-browser install  # Install dependencies in project-local venv
./mcp-browser init     # Initialize MCP configuration
```

This will:
- ✅ Check system requirements (Python 3.8+, Chrome)
- ✅ Create project-local virtual environment in `.venv/`
- ✅ Install all dependencies (MCP, WebSocket, Playwright)
- ✅ Set up directory structure (tmp/, data/, logs/)
- ✅ Create MCP configuration file
- ✅ Configure default settings

### Step 2: Load Chrome Extension (30 seconds)

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked"
4. Select the `extension/` folder from this project
5. Extension icon appears with green connection indicator
6. Extension automatically connects to WebSocket (ports 8875-8895)

### Step 3: Configure Claude Code Integration

```bash
# Auto-configure Claude Code integration
./setup-claude-code.sh
```

This script will:
- ✅ Test MCP server functionality
- ✅ Validate all 11 MCP tools
- ✅ Generate Claude Code configuration
- ✅ Create demo files for testing
- ✅ Show connection instructions

Then start the MCP server:
```bash
./mcp-browser start  # Start MCP server in background
# or
./mcp-browser dev    # Start in development mode with hot reload
```

Claude Code will automatically discover and use all 11 browser automation tools.

## Testing the Setup

### 1. Start the Server

```bash
mcp-browser start
```

You should see:
```
[✓] WebSocket server listening on port 8875
[✓] MCP Browser server started successfully
[✓] Process ID: 12345
[✓] Ready for browser connections
```

### 2. Check Extension Connection

- Look at the extension icon in Chrome toolbar
- Green badge with port number = connected
- Red badge with "!" = disconnected

### 3. Test Console Capture and DOM Interaction

#### Test Console Capture
Open any website and run in the browser console:
```javascript
console.log("Test message from MCP Browser");
console.error("Test error");
console.warn("Test warning");
```

#### Test DOM Interaction with Demo Page
```bash
# Open the demo page
open tmp/demo_dom_interaction.html
```

Then ask Claude Code to:
- "Fill the username field with 'testuser'"
- "Click the test button and wait for results"
- "Select 'Canada' from the country dropdown"
- "Fill out the entire form and submit it"
- "Take a screenshot of the page"
- "Execute JavaScript to validate the form data"

## 🎯 Self-Documenting CLI Help

**New to MCP Browser?** The CLI guides you through everything:

```bash
# Interactive setup and feature tour
mcp-browser quickstart     # Complete setup guide
mcp-browser tutorial       # Step-by-step feature demo
mcp-browser doctor         # Diagnose and fix issues

# Get help anytime
mcp-browser --help         # See all commands
mcp-browser start --help   # Help for specific commands
```

## 🗺️ Built-in Tutorial Mode

After installation, run the tutorial to learn all features:

```bash
mcp-browser tutorial
```

This interactive tutorial covers:
- ✅ Chrome extension setup and connection
- ✅ Console log capture and filtering
- ✅ DOM interaction with live examples
- ✅ Form filling and submission
- ✅ JavaScript execution in browser
- ✅ Claude Code integration
- ✅ Troubleshooting common issues

## 🔍 Need Help? Built-in Diagnostics

**Something not working?** Run the doctor command:

```bash
mcp-browser doctor
```

This will:
- ✅ Check system requirements
- ✅ Verify installation integrity
- ✅ Test Chrome extension connection
- ✅ Validate MCP tools
- ✅ Provide specific fix instructions
- ✅ Export diagnostic information

## 🚀 Quick Test After Installation

### 1. Verify Everything Works

```bash
# Check installation
mcp-browser --version
mcp-browser status

# Run comprehensive test
mcp-browser test-mcp
```

### 2. Interactive Demo

```bash
# Start server
mcp-browser start

# Open demo page (created during quickstart)
open tmp/demo_dom_interaction.html
```

### 3. Test with Claude Code

Ask Claude to:
- "Fill the username field with 'testuser'"
- "Click the test button and wait for results"
- "Select 'Canada' from the country dropdown"
- "Fill out the entire form and submit it"
- "Take a screenshot of the page"
- "Execute JavaScript to validate the form data"

## 🏠 Professional CLI Commands

Once installed, use these commands for daily operation:

### Server Management
```bash
mcp-browser start          # Start the server
mcp-browser stop           # Stop the server
mcp-browser restart        # Restart (stop + start)
mcp-browser status         # Check status (ports, PIDs, logs)
```

### Monitoring and Logs
```bash
mcp-browser logs           # Last 50 lines
mcp-browser logs 100       # Last 100 lines
mcp-browser follow         # Real-time tail
```

### MCP Integration
```bash
mcp-browser mcp            # Run in MCP mode for Claude Code
mcp-browser test-mcp       # Test all MCP tools
```

### Utilities
```bash
mcp-browser config         # Show configuration
mcp-browser clean          # Clean old logs and data
mcp-browser doctor         # System diagnostics
```

## 🎆 What You Get

After running `mcp-browser quickstart`, you'll have:

### 🤖 11 Powerful MCP Tools for Claude Code
1. **browser_navigate** - Navigate to any URL
2. **browser_query_logs** - Search console logs with filters
3. **browser_screenshot** - Capture high-quality screenshots
4. **browser_click** - Click elements by selector, XPath, or text
5. **browser_fill_field** - Fill input fields with data
6. **browser_fill_form** - Fill entire forms at once
7. **browser_submit_form** - Submit forms intelligently
8. **browser_get_element** - Extract element information
9. **browser_wait_for_element** - Wait for dynamic content
10. **browser_select_option** - Handle dropdowns and selects
11. **browser_evaluate_js** - Execute JavaScript in browser

### 🎨 Chrome Extension Features
- ✅ Real-time console log capture from active tab only
- ✅ Visual connection status indicator (🔴 error, 🟡 listening, 🟢 connected)
- ✅ Automatic reconnection on failures
- ✅ Active tab filtering (prevents duplicate messages)
- ✅ WebSocket communication (ports 8875-8895)

### 🔧 Professional CLI
- ✅ Self-documenting with built-in help
- ✅ Interactive setup and tutorials
- ✅ Health monitoring and diagnostics
- ✅ Process management and monitoring
- ✅ Advanced logging and debugging

## 🎓 Learning Path

For new users, follow this learning path:

1. **Install**: `pip install mcp-browser`
2. **Setup**: `mcp-browser quickstart` (follow all prompts)
3. **Learn**: `mcp-browser tutorial` (hands-on examples)
4. **Practice**: Use demo page with Claude Code
5. **Explore**: Try all 11 MCP tools
6. **Troubleshoot**: `mcp-browser doctor` when needed

## 📚 Need More Information?

- **Full Installation Guide**: [INSTALLATION.md](INSTALLATION.md)
- **Complete Feature List**: [README.md](README.md)
- **Developer Documentation**: [DEVELOPER.md](DEVELOPER.md)
- **AI Agent Instructions**: [CLAUDE.md](CLAUDE.md)

## ✨ Pro Tips

- Use `mcp-browser --help` for any command to see detailed options
- Run `mcp-browser doctor` if anything isn't working
- The tutorial mode is interactive - follow along in your browser
- All CLI commands have smart defaults - no configuration needed
- Extension automatically reconnects if connection drops

**🎉 You're Ready!**

Your MCP Browser is now set up with:
- ✅ Self-documenting CLI (`mcp-browser --help`)
- ✅ Interactive tutorials (`mcp-browser tutorial`)
- ✅ Health monitoring (`mcp-browser doctor`)
- ✅ 11 powerful MCP tools for Claude Code
- ✅ Chrome extension for console capture and DOM interaction

## 🆘 Need Help? Built-in Troubleshooting

**Something not working?** The CLI has built-in diagnostics:

```bash
# Comprehensive system check
mcp-browser doctor

# Get help with any command
mcp-browser --help
mcp-browser start --help

# Test all functionality
mcp-browser test-mcp
```

### Common Issues (Quick Fixes)

#### Extension Not Connecting?
```bash
# Check status and get fix instructions
mcp-browser doctor
mcp-browser status

# Restart if needed
mcp-browser restart
```

#### No Console Logs?
```bash
# Verify extension connection
# Extension popup should show green indicator
# If red, follow the quickstart guide again
mcp-browser quickstart
```

#### Claude Code Integration Issues?
```bash
# Test MCP tools
mcp-browser test-mcp

# Regenerate configuration if needed
mcp-browser config --reset
```

## 📋 Success Checklist

After running `mcp-browser quickstart`, verify these indicators:

### ✅ Installation Success
- [ ] `mcp-browser --version` shows current version
- [ ] `mcp-browser status` shows server running
- [ ] `mcp-browser doctor` reports all systems healthy

### ✅ Chrome Extension Working
- [ ] Extension icon visible in Chrome toolbar
- [ ] Extension popup shows green connection indicator
- [ ] Port number displayed (8875-8895 range)
- [ ] Console logs appear in real-time

### ✅ Claude Code Integration
- [ ] All 11 MCP tools available in Claude Code
- [ ] `mcp-browser test-mcp` passes all tests
- [ ] Demo page interactions work smoothly
- [ ] Can navigate, fill forms, and take screenshots

## 📖 Next Steps

### 1. Explore Features
```bash
# Interactive feature tour
mcp-browser tutorial

# Test all MCP tools
mcp-browser test-mcp

# Try the demo page
open tmp/demo_dom_interaction.html
```

### 2. Daily Usage
```bash
# Start server for Claude Code
mcp-browser start

# Monitor logs and status
mcp-browser status
mcp-browser follow
```

### 3. Get Help When Needed
```bash
# Built-in diagnostics
mcp-browser doctor

# Command help
mcp-browser --help
mcp-browser COMMAND --help
```

## 📚 Documentation

- **[README.md](README.md)**: Complete feature overview
- **[INSTALLATION.md](INSTALLATION.md)**: Detailed installation guide
- **[DEVELOPER.md](DEVELOPER.md)**: Technical implementation
- **[CLAUDE.md](CLAUDE.md)**: AI agent instructions

## 🎯 You're All Set!

MCP Browser is now ready to automate your browser with Claude Code. The interactive `quickstart` command has set up everything you need, and the self-documenting CLI will guide you through any future needs.

**Happy browsing! 🚀**