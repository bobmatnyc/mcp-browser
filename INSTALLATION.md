# MCP Browser Installation Guide

## Overview

MCP Browser offers multiple installation methods to suit different needs. The recommended PyPI installation takes under 30 seconds with the interactive quickstart command that guides you through the entire setup process.

## 🌟 Quick Start (30 Seconds)

**Just want to get started?** Run this and follow the prompts:

```bash
pip install mcp-browser
mcp-browser quickstart
```

The quickstart command provides:
- Interactive installation guide
- Chrome extension setup with screenshots
- Claude Code integration
- Feature demonstration
- Troubleshooting help

## Key Features

### 1. **Self-Documenting CLI**
- **quickstart**: Interactive setup guide with everything
- **doctor**: System diagnostics and troubleshooting
- **tutorial**: Step-by-step feature demonstration
- **start**: Run MCP server with auto-discovery
- **mcp**: Run in MCP stdio mode for Claude Code
- **--help**: Built-in help for any command

### 2. **Installation Features**
- **Zero Documentation Required**: Everything guided interactively
- **Multiple Methods**: pip, pipx, or development installation
- **Auto-Configuration**: Smart defaults with system detection
- **Shell Completion**: Tab completion for all commands
- **Health Monitoring**: Built-in diagnostics and repair

### 3. **Chrome Extension Integration**
- **Guided Installation**: Screenshots and step-by-step instructions
- **Real-time Status**: Visual connection indicators
- **Multi-tab Support**: Console capture from all browser tabs
- **Auto-reconnection**: Handles connection drops gracefully
- **Port Discovery**: Automatic WebSocket port selection (8875-8895)

### 4. **Claude Code Integration**
- **Automatic Setup**: Detects and configures Claude Code
- **11 MCP Tools**: Complete browser automation suite
- **Smart Element Discovery**: CSS selectors, XPath, and text-based finding
- **Form Automation**: Fill fields, submit forms, handle validation
- **Dynamic Content**: Wait for elements, handle AJAX loading
- **JavaScript Execution**: Run custom code in browser context

## Installation Methods

### Method 1: PyPI Installation (Recommended)

**Standard Installation:**
```bash
# Install with pip
pip install mcp-browser

# Run interactive setup
mcp-browser quickstart
```

**Isolated Installation:**
```bash
# Install with pipx (completely isolated)
pipx install mcp-browser
mcp-browser quickstart
```

### Method 2: Development Installation

**From Source:**
```bash
# Clone repository
git clone https://github.com/browserpymcp/mcp-browser.git
cd mcp-browser

# Install dependencies
./install.sh

# Run setup
mcp-browser quickstart
```

**Editable Installation:**
```bash
# For development with live code changes
pip install -e .
mcp-browser quickstart
```

### Method 3: Platform-Specific Installation

See platform-specific sections below for detailed instructions.

### What the quickstart command does:

#### System Verification
- ✅ Checks Python 3.10+ availability and version
- ✅ Validates pip installation and functionality
- ✅ Detects Chrome/Chromium browser installation
- ✅ Tests MCP Browser CLI functionality
- ✅ Verifies system permissions and requirements

#### Interactive Setup
- ✅ Guides Chrome extension installation with screenshots
- ✅ Detects and configures Claude Code integration
- ✅ Tests all MCP tools with live examples
- ✅ Sets up optimal configuration for your system
- ✅ Provides troubleshooting for any issues

#### Feature Demonstration
- ✅ Opens demo page for hands-on testing
- ✅ Shows DOM interaction capabilities
- ✅ Demonstrates console log capture
- ✅ Tests screenshot functionality
- ✅ Validates end-to-end workflow

## Platform-Specific Instructions

### macOS

**Prerequisites:**
```bash
# Install Python 3.10+ via Homebrew (recommended)
brew install python3

# Or use system Python (ensure it's 3.10+)
python3 --version
```

**Installation:**
```bash
# Install MCP Browser
pip3 install mcp-browser

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Run setup
mcp-browser quickstart
```

**Chrome Extension:**
- Download extension from Chrome Web Store (coming soon)
- Or load unpacked from project directory

### Linux (Ubuntu/Debian)

**Prerequisites:**
```bash
# Update package list
sudo apt update

# Install Python 3.10+ and pip
sudo apt install python3 python3-pip python3-venv

# Install Chrome/Chromium
sudo apt install chromium-browser
# Or download Chrome from google.com/chrome
```

**Installation:**
```bash
# Install MCP Browser
pip3 install --user mcp-browser

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Run setup
mcp-browser quickstart
```

### Linux (CentOS/RHEL/Fedora)

**Prerequisites:**
```bash
# Fedora
sudo dnf install python3 python3-pip chromium

# CentOS/RHEL (with EPEL)
sudo yum install python3 python3-pip
sudo yum install chromium  # or download Chrome
```

**Installation:**
```bash
# Same as Ubuntu
pip3 install --user mcp-browser
mcp-browser quickstart
```

### Windows

**Prerequisites:**
1. Install Python 3.10+ from [python.org](https://python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation
2. Install Chrome from [google.com/chrome](https://google.com/chrome)

**Installation:**
```cmd
# Install MCP Browser
pip install mcp-browser

# Run setup
mcp-browser quickstart
```

**PowerShell:**
```powershell
# If pip isn't in PATH
python -m pip install mcp-browser
mcp-browser quickstart
```

## Shell Completion Setup

### Bash
```bash
# Add to ~/.bashrc
eval "$(_MCP_BROWSER_COMPLETE=bash_source mcp-browser)"
```

### Zsh
```bash
# Add to ~/.zshrc
eval "$(_MCP_BROWSER_COMPLETE=zsh_source mcp-browser)"
```

### Fish
```bash
# Add to ~/.config/fish/config.fish
eval (env _MCP_BROWSER_COMPLETE=fish_source mcp-browser)
```

## Troubleshooting Common Issues

### Python Version Issues
```bash
# Check Python version
python3 --version

# If < 3.10, install newer version
# macOS: brew install python@3.12
# Ubuntu: sudo apt install python3.12
# Windows: Download from python.org
```

### PATH Issues
```bash
# Check if mcp-browser is in PATH
which mcp-browser

# If not found, add ~/.local/bin to PATH
export PATH="$HOME/.local/bin:$PATH"

# Make permanent by adding to shell config
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Permission Issues
```bash
# Install with --user flag
pip install --user mcp-browser

# Or fix permissions
sudo chown -R $USER ~/.local/
```

### Chrome Extension Issues
1. **Extension not loading:**
   - Enable Developer Mode in chrome://extensions/
   - Click "Load unpacked" and select extension folder
   - Check for error messages in Chrome DevTools

2. **Extension not connecting:**
   - Run `mcp-browser doctor` for diagnostics
   - Check if server is running: `mcp-browser status`
   - Verify ports 8875-8895 are available

3. **No console logs captured:**
   - Refresh the page after installing extension
   - Check extension popup for connection status
   - Look for test message in browser console

### MCP Integration Issues
```bash
# Test MCP tools
mcp-browser test-mcp

# Check Claude Code configuration
mcp-browser config

# Diagnose system
mcp-browser doctor
```

## Verification Steps

### 1. Verify Installation
```bash
# Check version
mcp-browser --version

# Run diagnostics
mcp-browser doctor

# Test basic functionality
mcp-browser status
```

### 2. Test Chrome Extension
```bash
# Start server
mcp-browser start

# Open test page
open tmp/demo_dom_interaction.html

# Check extension popup for green connection indicator
```

### 3. Test Claude Code Integration
```bash
# Test MCP tools
mcp-browser test-mcp

# Run in MCP mode (for Claude Code)
mcp-browser mcp
```

### What happens after installation:
- ✅ Chrome extension setup guide with screenshots
- ✅ Claude Code integration automatically detected and configured
- ✅ Demo files created for immediate testing
- ✅ All 11 MCP tools validated and ready to use
- ✅ Interactive tutorial for hands-on learning

## Usage and Operation

### Starting the Server
```bash
mcp-browser start
```
**Output example:**
```
[✓] Virtual environment activated
[✓] WebSocket server listening on port 8875
[✓] MCP Browser server started successfully
[✓] Process ID: 12345 saved to ~/.mcp-browser/run/mcp-browser.pid
[✓] Logs: ~/.mcp-browser/logs/mcp-browser.log
[✓] Ready for browser connections and MCP tools
```

### Comprehensive Status Checking
```bash
mcp-browser status
```
**Detailed output includes:**
- **Server State**: Running/stopped with PID and uptime
- **Process Information**: Memory usage, CPU, command line
- **Active Connections**: WebSocket ports and client count
- **Log Files**: Locations, sizes, and recent activity
- **Storage Statistics**: JSONL files, rotation status, disk usage
- **Health Metrics**: Connection counts, error rates, performance
- **Configuration**: Active settings and file locations

### Advanced Log Management
```bash
# Show recent logs with smart formatting
mcp-browser logs          # Last 50 lines
mcp-browser logs 100      # Last 100 lines

# Real-time log following with filtering
mcp-browser follow        # All logs
mcp-browser follow error  # Error logs only

# Export and analyze logs
mcp-browser logs --export /tmp/mcp-logs.txt
mcp-browser logs --json   # JSON format output
```

### Professional Process Management
```bash
# Graceful server management
mcp-browser start         # Start with health checks
mcp-browser stop          # Graceful shutdown with cleanup
mcp-browser restart       # Stop + start with validation
mcp-browser reload        # Reload configuration without restart

# Maintenance operations
mcp-browser clean         # Clean old logs and temp files
mcp-browser reset         # Reset to factory defaults
mcp-browser update        # Update dependencies and configuration

# Diagnostic and monitoring
mcp-browser health        # Comprehensive health check
mcp-browser version       # Version and build information
mcp-browser help          # Complete command reference
```

### MCP Integration for Claude Code
```bash
# Start MCP server for Claude Code integration
mcp-browser mcp
```
**Features:**
- **STDIO Mode**: Direct communication with Claude Code
- **Tool Discovery**: All 11 tools automatically exposed
- **Error Handling**: Comprehensive error reporting and recovery
- **Performance**: Optimized for AI agent interactions
- **Monitoring**: Real-time tool usage and performance metrics

## Configuration and Customization

### Auto-Generated Configuration
Location: `~/.mcp-browser/config/settings.json`

```json
{
  "storage": {
    "base_path": "~/.mcp-browser/data",
    "max_file_size_mb": 50,
    "retention_days": 7,
    "rotation_enabled": true,
    "compression": "gzip"
  },
  "websocket": {
    "port_range": [8875, 8895],
    "host": "localhost",
    "connection_timeout": 30,
    "heartbeat_interval": 10,
    "max_connections": 10
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "max_file_size_mb": 10,
    "backup_count": 5
  },
  "mcp": {
    "tool_timeout": 30,
    "max_screenshot_size": "1920x1080",
    "playwright_timeout": 30000,
    "dom_interaction_timeout": 10000
  },
  "chrome_extension": {
    "auto_reconnect": true,
    "buffer_size": 1000,
    "flush_interval": 2500
  }
}
```

### Environment Variables
```bash
# Override default settings
export MCP_BROWSER_PORT_START=8875
export MCP_BROWSER_PORT_END=8895
export MCP_BROWSER_LOG_LEVEL=DEBUG
export MCP_BROWSER_DATA_PATH=/custom/path
export MCP_BROWSER_CONFIG_PATH=/custom/config.json
```

## Advanced Features and Capabilities

### Professional Process Management
- **PID Tracking**: Automatic process identification and monitoring
- **Graceful Shutdown**: SIGTERM handling with proper cleanup
- **Force Kill Protection**: Timeout-based force termination prevention
- **Instance Management**: Prevention of multiple server instances
- **Health Monitoring**: Continuous process health and performance tracking
- **Auto-Recovery**: Automatic restart on unexpected failures

### Intelligent Log Management
- **Structured Logging**: JSON and text formats with proper timestamps
- **Port Isolation**: Separate logs for each WebSocket connection
- **Automatic Rotation**: Size-based rotation with compression
- **Retention Policies**: Configurable cleanup and archival
- **Real-time Monitoring**: Live log streaming and filtering
- **Export Capabilities**: Log aggregation and analysis tools

### Robust Virtual Environment
- **Isolation**: Complete dependency isolation from system Python
- **Version Management**: Automatic dependency version validation
- **Clean Installation**: No system Python pollution or conflicts
- **Portable**: Self-contained environment for easy deployment
- **Reproducible**: Deterministic dependency resolution

### DOM Interaction Engine
- **Smart Selectors**: CSS, XPath, and text-based element discovery
- **Form Automation**: Complete form filling and submission
- **Dynamic Content**: AJAX and SPA support with intelligent waiting
- **Event Simulation**: Real user interaction simulation
- **Error Recovery**: Robust error handling and retry mechanisms
- **Performance Optimization**: Efficient element discovery and interaction

### MCP Tool Suite (11 Tools)
1. **browser_navigate**: Smart navigation with URL validation
2. **browser_query_logs**: Advanced console log filtering and retrieval
3. **browser_screenshot**: High-quality viewport capture
4. **browser_click**: Intelligent element clicking with verification
5. **browser_fill_field**: Precise form field filling
6. **browser_fill_form**: Bulk form filling automation
7. **browser_submit_form**: Smart form submission handling
8. **browser_get_element**: Element information extraction
9. **browser_wait_for_element**: Dynamic content waiting
10. **browser_select_option**: Dropdown and select handling
11. **browser_evaluate_js**: Custom JavaScript execution

### Production Deployment (Optional)

#### Systemd Service Setup
```bash
# Install system service
sudo cp scripts/mcp-browser.service /etc/systemd/system/
sudo systemctl enable mcp-browser@$USER
sudo systemctl start mcp-browser@$USER

# Monitor service
sudo systemctl status mcp-browser@$USER
sudo journalctl -u mcp-browser@$USER -f
```

#### Docker Deployment
```bash
# Build Docker image
docker build -t mcp-browser .

# Run with volume mounts
docker run -d \
  --name mcp-browser \
  -p 8875-8895:8875-8895 \
  -v ~/.mcp-browser:/root/.mcp-browser \
  mcp-browser

# Monitor container
docker logs -f mcp-browser
```

#### Environment-Specific Configuration
```bash
# Development environment
export MCP_BROWSER_ENV=development
export MCP_BROWSER_LOG_LEVEL=DEBUG

# Production environment
export MCP_BROWSER_ENV=production
export MCP_BROWSER_LOG_LEVEL=INFO
export MCP_BROWSER_METRICS_ENABLED=true

# Testing environment
export MCP_BROWSER_ENV=testing
export MCP_BROWSER_MOCK_BROWSER=true
```

## Testing and Validation

### Comprehensive Installation Testing
```bash
# Multi-stage installation verification
./test_installation.sh
```
**Test Coverage:**
- ✅ System requirements validation
- ✅ Virtual environment functionality
- ✅ Dependency installation verification
- ✅ CLI command testing
- ✅ WebSocket connectivity
- ✅ MCP server functionality
- ✅ Chrome extension compatibility
- ✅ DOM interaction capabilities
- ✅ Log system operation
- ✅ Configuration validation

### Interactive Feature Demonstration
```bash
# Complete feature showcase
./demo.sh
```
**Demo Coverage:**
- ✅ WebSocket connection establishment
- ✅ Console log capture
- ✅ Navigation commands
- ✅ Screenshot functionality
- ✅ DOM element interaction
- ✅ Form filling and submission
- ✅ JavaScript execution
- ✅ Error handling and recovery

### DOM Interaction Testing
```bash
# Open interactive demo page
open tmp/demo_dom_interaction.html

# Test with Claude Code:
# "Fill the username field with 'testuser'"
# "Click the test button and wait for results"
# "Select 'Canada' from the country dropdown"
# "Fill out the entire form and submit it"
# "Execute custom JavaScript to validate the form"
```

### Performance and Load Testing
```bash
# Performance benchmarks
mcp-browser benchmark

# Load testing with multiple connections
mcp-browser stress-test --connections 10 --duration 60

# Memory and CPU profiling
mcp-browser profile --duration 300
```

## Troubleshooting and Common Issues

### Installation Problems

#### Python Version Issues
```bash
# Check Python version (need 3.8+)
python3 --version

# If wrong version, install correct Python
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
```

#### Virtual Environment Problems
```bash
# Completely clean and reinstall
rm -rf .venv
rm -rf ~/.mcp-browser
./install.sh

# Check virtual environment
source .venv/bin/activate
python --version
pip list | grep mcp
```

#### Permission Issues
```bash
# Fix directory permissions
chmod -R u+w ~/.mcp-browser
sudo chown -R $USER ~/.mcp-browser

# Fix command symlink
sudo rm /usr/local/bin/mcp-browser
ln -sf $(pwd)/mcp-browser ~/.local/bin/mcp-browser
```

### Runtime Issues

#### Port Conflicts
```bash
# Check port availability
netstat -an | grep LISTEN | grep 887
lsof -i :8875-8895

# Force port cleanup
mcp-browser stop --force
killall -9 python
```

#### WebSocket Connection Problems
```bash
# Test WebSocket connectivity
wscat ws://localhost:8875

# Check firewall settings
sudo ufw status

# Reset WebSocket server
mcp-browser restart --reset-ports
```

#### Chrome Extension Issues
```bash
# Reload extension
# chrome://extensions/ → Developer mode → Reload

# Check extension console
# Right-click extension icon → Inspect popup

# Clear extension storage
# Chrome DevTools → Application → Storage → Clear

# Reinstall extension
rm -rf /tmp/mcp-browser-extension-*
cp -r extension /tmp/mcp-browser-extension-backup
```

### MCP Integration Problems

#### Claude Code Not Detecting Tools
```bash
# Verify MCP server
mcp-browser mcp --test

# Check tool registration
mcp-browser tools --list

# Validate configuration
./setup-claude-code.sh --verify

# Reset Claude Code configuration
rm ~/.config/claude-desktop/claude_desktop_config.json
./setup-claude-code.sh
```

#### DOM Interaction Failures
```bash
# Test with demo page
open tmp/demo_dom_interaction.html

# Check browser console for errors
# F12 → Console → Look for MCP Browser messages

# Verify element selectors
# F12 → Elements → Test CSS selectors

# Test JavaScript execution
console.log("MCP Browser DOM test")
```

### Performance Issues

#### High Memory Usage
```bash
# Check memory usage
mcp-browser status --memory

# Clean old logs
mcp-browser clean --logs

# Restart with fresh state
mcp-browser restart --clean
```

#### Slow Response Times
```bash
# Check system resources
top -p $(cat ~/.mcp-browser/run/mcp-browser.pid)

# Optimize configuration
mcp-browser config --optimize

# Enable performance monitoring
mcp-browser start --profile
```

### Diagnostic Commands

```bash
# Comprehensive system check
mcp-browser doctor

# Export diagnostic information
mcp-browser diagnose --export /tmp/mcp-diagnosis.txt

# Test all components
mcp-browser test --all

# Validate installation integrity
./test_installation.sh --verbose
```

## Directory Structure Summary

```
mcp-browser/
├── mcp-browser              # Main entry point script
├── install.sh               # Installation script
├── setup-claude-code.sh     # Claude Code setup
├── test_installation.sh     # Installation test
├── demo.sh                  # Feature demonstration
├── src/
│   ├── cli/
│   │   └── main.py         # Enhanced CLI with professional features
│   ├── container/          # Dependency injection
│   ├── services/           # Service layer (SOA)
│   └── models/             # Data models
├── extension/              # Chrome extension
├── scripts/
│   └── mcp-browser.service # Systemd service file
├── requirements.txt        # Production dependencies
└── requirements-dev.txt    # Development dependencies
```

## Support and Resources

### Documentation Hierarchy
- **INSTALLATION.md**: You are here - Complete installation guide
- **README.md**: Feature overview and quick start
- **QUICKSTART.md**: 5-minute setup guide
- **CLAUDE.md**: AI agent instructions and architecture
- **DEVELOPER.md**: Technical implementation details

### Self-Help Tools
```bash
# Built-in diagnostics
mcp-browser doctor          # Health check
mcp-browser test --all      # Comprehensive testing
./test_installation.sh      # Installation verification
./demo.sh                   # Feature demonstration
```

### Community and Support
- **GitHub Repository**: https://github.com/yourusername/mcp-browser
- **Issue Tracker**: https://github.com/yourusername/mcp-browser/issues
- **Discussions**: https://github.com/yourusername/mcp-browser/discussions
- **Wiki**: https://github.com/yourusername/mcp-browser/wiki

### Version Information
- **Current Version**: 2.0.0
- **Release Date**: September 2024
- **License**: MIT License
- **Python Compatibility**: 3.8+
- **Browser Support**: Chrome, Chromium, Edge (Chromium-based)

## Installation Success Checklist

### ✅ Core Installation
- Professional CLI with all commands (`mcp-browser help`)
- Virtual environment isolation (`.venv/` directory exists)
- Organized structure in `~/.mcp-browser/`
- Global command accessibility (`which mcp-browser`)
- Configuration generation (`~/.mcp-browser/config/settings.json`)

### ✅ Process Management
- Server start/stop functionality
- PID tracking and process monitoring
- Graceful shutdown with cleanup
- Log management and rotation
- Health checking and diagnostics

### ✅ Browser Integration
- Chrome extension installation
- WebSocket connectivity (ports 8875-8895)
- Console log capture
- DOM interaction capabilities
- Real-time communication

### ✅ MCP Integration
- All 11 tools exposed and functional
- Claude Code configuration generated
- STDIO mode operation
- Tool validation and testing
- Error handling and recovery

### ✅ Testing and Validation
- Installation test passes (`./test_installation.sh`)
- Feature demo works (`./demo.sh`)
- DOM interaction demo functional
- WebSocket connectivity confirmed
- All CLI commands operational

### ✅ Production Readiness
- Automated deployment scripts
- Configuration management
- Log rotation and retention
- Performance monitoring
- Error handling and recovery
- Documentation completeness

## Next Steps After Installation

1. **Verify Installation**: Run `./test_installation.sh`
2. **Load Chrome Extension**: Follow Step 3 instructions
3. **Configure Claude Code**: Run `./setup-claude-code.sh`
4. **Test DOM Interaction**: Open `tmp/demo_dom_interaction.html`
5. **Start Using**: Ask Claude to automate your browser tasks!

**Installation Complete! 🎉**