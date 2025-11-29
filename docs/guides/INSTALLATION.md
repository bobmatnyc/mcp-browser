# MCP Browser Installation Guide

Complete installation guide for MCP Browser with platform-specific instructions and troubleshooting.

## Quick Install

### Recommended: Zero-Config Installation

```bash
# Install from PyPI
pip install mcp-browser

# Run interactive setup (handles everything)
mcp-browser quickstart
```

The `quickstart` command will guide you through:
- ✅ System requirements verification
- ✅ Chrome extension installation
- ✅ Claude Code integration setup
- ✅ Feature testing and validation
- ✅ Troubleshooting any issues

---

## Installation Methods

### Method 1: PyPI Installation (Recommended)

**Best for**: Production use, most users

```bash
# Install package
pip install mcp-browser

# Run interactive setup
mcp-browser quickstart
```

**Advantages**:
- ✅ Latest stable release
- ✅ Automatic dependency management
- ✅ Easy updates with `pip install --upgrade mcp-browser`
- ✅ Clean uninstall with `pip uninstall mcp-browser`

---

### Method 2: pipx Installation (Isolated)

**Best for**: Users who want complete isolation from system Python

```bash
# Install pipx if not already installed
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install mcp-browser with pipx
pipx install mcp-browser

# Run setup
mcp-browser quickstart
```

**Advantages**:
- ✅ Complete isolation from system Python
- ✅ No dependency conflicts
- ✅ Easy management with `pipx` commands
- ✅ Automatic virtual environment handling

**Manage with pipx**:
```bash
pipx upgrade mcp-browser     # Upgrade to latest version
pipx uninstall mcp-browser   # Uninstall completely
pipx list                    # List installed packages
```

---

### Method 3: Development Installation

**Best for**: Contributors, developers, testing unreleased features

```bash
# Clone repository
git clone https://github.com/browserpymcp/mcp-browser.git
cd mcp-browser

# Run installation script
./install.sh

# Run setup
mcp-browser quickstart
```

**What `install.sh` does**:
- Creates virtual environment in `.venv/`
- Installs dependencies from `requirements.txt`
- Creates necessary directories
- Sets up CLI entry point
- Configures development mode

**Development workflow**:
```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Run tests
make test

# Run linting
make lint

# Build package
make build
```

---

## System Requirements

### Prerequisites

- **Python 3.10 or higher**
  ```bash
  python --version  # Check your version
  ```

- **Chrome or Chromium browser**
  - Google Chrome (recommended)
  - Chromium
  - Brave (Chromium-based)
  - Edge (Chromium-based)

- **pip** (usually included with Python)
  ```bash
  pip --version
  ```

### Platform-Specific Requirements

#### macOS
```bash
# Install Python 3.10+ if needed
brew install python@3.10

# Verify installation
python3 --version
pip3 --version
```

#### Linux (Ubuntu/Debian)
```bash
# Install Python 3.10+
sudo apt update
sudo apt install python3.10 python3-pip

# Install Playwright dependencies
sudo apt install libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
                 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
                 libdrm2 libxkbcommon0 libxcomposite1 \
                 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
                 libpango-1.0-0 libcairo2 libasound2
```

#### Windows
```powershell
# Install Python 3.10+ from python.org
# Or use Chocolatey
choco install python310

# Verify installation
python --version
pip --version
```

---

## Post-Installation Setup

### Step 1: Chrome Extension Installation

**Automated Guide**:
```bash
mcp-browser quickstart  # Includes extension setup
```

**Manual Installation**:

1. **Get the extension files**:
   ```bash
   # If installed via pip/pipx, download extension
   mcp-browser init --project

   # Extension will be in ./mcp-browser-extension/
   ```

2. **Load in Chrome**:
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right)
   - Click "Load unpacked"
   - Select the `mcp-browser-extension/` directory
   - Extension icon should appear in toolbar

3. **Verify installation**:
   - Click the extension icon
   - Should show "Disconnected" status (normal until server starts)

---

### Step 2: Claude Code Integration

**Automated Setup**:
```bash
mcp-browser install          # Install for Claude Code (default)
mcp-browser install --target claude-desktop  # Install for Claude Desktop
mcp-browser install --target both           # Install for both
```

**What this does**:
- Detects your installation type (pipx, pip, or dev)
- Adds `mcp-browser` to MCP configuration
- Configures correct command paths
- Sets up environment for Claude integration

**Manual Setup** (if automated fails):

1. **Find configuration file**:
   - **Claude Code**: `~/.claude/settings.local.json`
   - **Claude Desktop (macOS)**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Claude Desktop (Linux)**: `~/.config/Claude/claude_desktop_config.json`
   - **Claude Desktop (Windows)**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add MCP Browser entry**:
   ```json
   {
     "mcpServers": {
       "mcp-browser": {
         "command": "mcp-browser",
         "args": ["mcp"]
       }
     }
   }
   ```

3. **Restart Claude Code/Desktop**

---

### Step 3: Start the Server

```bash
# Start server with auto-discovery
mcp-browser start

# Check status
mcp-browser status

# View logs
mcp-browser logs
```

**Expected output**:
```
WebSocket server started on port 8875
Waiting for browser connections...
```

---

### Step 4: Verify Installation

**Quick verification**:
```bash
mcp-browser doctor
```

**Manual verification**:

1. **Check server is running**:
   ```bash
   mcp-browser status
   ```
   Should show: "✓ Server is running on port 8875"

2. **Verify extension connection**:
   - Open Chrome
   - Click extension icon
   - Should show "Connected on port 8875" (green)

3. **Test MCP tools in Claude Code**:
   - Open Claude Code
   - Ask: "What MCP tools are available?"
   - Should list `mcp-browser` tools

4. **Test basic functionality**:
   ```bash
   mcp-browser test-mcp
   ```

---

## Configuration

### Environment Variables

```bash
# Port range for auto-discovery
export BROWSERPYMCP_PORT_START=8875
export BROWSERPYMCP_PORT_END=8895

# Log level (DEBUG, INFO, WARNING, ERROR)
export BROWSERPYMCP_LOG_LEVEL=INFO

# Storage path
export BROWSERPYMCP_STORAGE_PATH=~/.mcp-browser
```

### Configuration File

**Location**: `~/.mcp-browser/config/settings.json`

**Auto-generated on first run**:
```json
{
  "port_start": 8875,
  "port_end": 8895,
  "log_level": "INFO",
  "storage_path": "~/.mcp-browser",
  "log_rotation_size": 52428800,
  "log_retention_days": 7
}
```

**Modify settings**:
```bash
# View current config
mcp-browser config

# Edit manually
nano ~/.mcp-browser/config/settings.json

# Restart to apply changes
mcp-browser restart
```

---

## Troubleshooting

### Installation Issues

#### Problem: "pip install" fails with dependency errors

**Solution**:
```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Try installation again
pip install mcp-browser

# If still fails, use verbose mode
pip install -v mcp-browser
```

#### Problem: "command not found: mcp-browser"

**Cause**: Installation directory not in PATH

**Solution**:
```bash
# Find installation location
pip show mcp-browser

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Or use full path
python -m mcp_browser.cli.main --help
```

#### Problem: "Permission denied" during installation

**Solution**:
```bash
# Install for current user only
pip install --user mcp-browser

# Or use pipx (recommended)
pipx install mcp-browser
```

---

### Extension Issues

#### Problem: Extension doesn't appear in Chrome

**Solution**:
1. Verify extension files exist:
   ```bash
   ls -la mcp-browser-extension/
   ```
2. Check Chrome version: `chrome://version/`
3. Try reloading extension:
   - Go to `chrome://extensions/`
   - Click reload icon on MCP Browser extension

#### Problem: Extension shows "Disconnected"

**This is normal** if server isn't running!

**Solution**:
```bash
# Start server
mcp-browser start

# Verify server status
mcp-browser status

# Refresh browser page
# Extension should now show "Connected"
```

#### Problem: Extension shows connection but no logs captured

**Solution**:
1. Open browser DevTools (F12)
2. Check Console for test message:
   ```
   [mcp-browser] Console capture initialized
   ```
3. If not present, reload extension:
   - `chrome://extensions/` → Reload button
4. Refresh the webpage

---

### Claude Code Integration Issues

#### Problem: MCP Browser tools not available in Claude

**Solution**:
```bash
# Reinstall MCP configuration
mcp-browser install --force

# Verify config file
cat ~/.claude/settings.local.json

# Restart Claude Code
```

#### Problem: "Failed to start mcp-browser server"

**Cause**: Incorrect command path in configuration

**Solution**:
```bash
# Check installation type
which mcp-browser

# Update configuration with correct path
mcp-browser install --force

# Or manually edit ~/.claude/settings.local.json
```

#### Problem: Tools listed but "Connection failed" when used

**Solution**:
```bash
# Make sure server is running
mcp-browser start

# Check Claude Code can reach server
mcp-browser test-mcp

# Check firewall isn't blocking localhost connections
```

---

### Server Issues

#### Problem: "Port already in use"

**Solution**:
```bash
# Server uses auto-discovery (8875-8895)
# If all ports busy, free one up:
lsof -i :8875  # Find process using port

# Or kill existing server
mcp-browser stop
mcp-browser start
```

#### Problem: Server crashes on startup

**Solution**:
```bash
# Check logs for details
mcp-browser logs

# Common causes:
# 1. Playwright not installed
playwright install chromium

# 2. Missing dependencies (Linux)
sudo apt install libglib2.0-0 libnss3

# 3. Corrupted data directory
rm -rf ~/.mcp-browser
mcp-browser start
```

---

### Playwright Issues

#### Problem: Screenshots fail with "Browser not installed"

**Solution**:
```bash
# Install Playwright browsers
playwright install chromium

# If permission issues (Linux)
sudo playwright install-deps chromium
```

#### Problem: "Executable doesn't exist" error

**Solution**:
```bash
# Reinstall Playwright
pip uninstall playwright
pip install playwright
playwright install chromium
```

---

## Platform-Specific Notes

### macOS

**Gatekeeper issues**:
```bash
# If blocked by Gatekeeper
xattr -cr ~/.local/pipx/venvs/mcp-browser  # For pipx installation
```

**M1/M2 (Apple Silicon)**:
- Python 3.10+ recommended (native ARM support)
- Rosetta not required

### Linux

**System dependencies for Playwright**:
```bash
# Ubuntu/Debian
sudo apt install libnss3 libnspr4 libdbus-1-3 libatk1.0-0

# Fedora/RHEL
sudo dnf install nss nspr dbus-libs atk

# Arch
sudo pacman -S nss dbus atk
```

**SELinux issues**:
```bash
# If SELinux blocks WebSocket
sudo setsebool -P httpd_can_network_connect 1
```

### Windows

**Long path issues**:
```powershell
# Enable long paths in Windows
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
  -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

**PowerShell execution policy**:
```powershell
# If scripts blocked
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Antivirus interference**:
- Whitelist `~/.mcp-browser/` directory
- Whitelist `mcp-browser.exe` binary

---

## Upgrading

### Upgrade from pip

```bash
# Upgrade to latest version
pip install --upgrade mcp-browser

# Verify new version
mcp-browser version

# Reconfigure if needed
mcp-browser install --force

# Restart server
mcp-browser restart
```

### Upgrade from pipx

```bash
# Upgrade with pipx
pipx upgrade mcp-browser

# Verify version
mcp-browser version

# Restart
mcp-browser restart
```

### Upgrade from development

```bash
# Navigate to repository
cd ~/path/to/mcp-browser

# Pull latest changes
git pull origin main

# Reinstall
./install.sh

# Restart
mcp-browser restart
```

---

## Uninstalling

For complete uninstall instructions, see **[UNINSTALL.md](UNINSTALL.md)**.

### Quick Uninstall

```bash
# Remove MCP configuration
mcp-browser uninstall

# Uninstall package
pip uninstall mcp-browser         # If installed with pip
pipx uninstall mcp-browser        # If installed with pipx
```

### Complete Removal

```bash
# Remove everything (with backup)
mcp-browser uninstall --clean-all

# Uninstall package
pip uninstall mcp-browser
```

---

## Next Steps

After successful installation:

1. **Learn the CLI**:
   ```bash
   mcp-browser --help
   mcp-browser tutorial
   ```

2. **Start using in Claude Code**:
   - Ask: "Navigate to https://example.com"
   - Ask: "Capture a screenshot of the current page"
   - Ask: "What console errors are showing?"

3. **Explore advanced features**:
   - Form automation
   - DOM interaction
   - Multi-tab monitoring
   - Log filtering

4. **Check documentation**:
   - [README.md](../../README.md) - Overview and features
   - [UNINSTALL.md](UNINSTALL.md) - Removal guide
   - CLI help: `mcp-browser <command> --help`

---

## Getting Help

### Diagnostic Information

Before requesting help, gather diagnostic info:

```bash
# System information
mcp-browser version
mcp-browser config
mcp-browser status
python --version
pip list | grep mcp-browser

# Check logs
mcp-browser logs 50

# Run diagnostics
mcp-browser doctor
```

### Support Resources

- **Documentation**: [README.md](../../README.md)
- **Uninstall Guide**: [UNINSTALL.md](UNINSTALL.md)
- **Issues**: [GitHub Issues](https://github.com/browserpymcp/mcp-browser/issues)
- **CLI Help**: `mcp-browser --help`

### Reporting Issues

Include the following in bug reports:

1. **Environment**:
   ```bash
   mcp-browser version
   python --version
   uname -a  # macOS/Linux
   ```

2. **Installation method**: pip, pipx, or development

3. **Error logs**:
   ```bash
   mcp-browser logs 100
   ```

4. **Steps to reproduce**

5. **Expected vs actual behavior**

---

## Summary

**Quick Install**:
```bash
pip install mcp-browser
mcp-browser quickstart
```

**Manual Install Steps**:
1. Install Python 3.10+
2. `pip install mcp-browser`
3. Install Chrome extension (`mcp-browser init --project`)
4. Configure Claude Code (`mcp-browser install`)
5. Start server (`mcp-browser start`)
6. Verify (`mcp-browser doctor`)

**Need help?** Run `mcp-browser quickstart` for interactive guided setup!
