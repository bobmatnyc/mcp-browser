# MCP Browser - Dual Deployment Guide

This guide explains the two deployment methods for mcp-browser: **local development** and **system-wide installation**.

## Overview

MCP Browser supports a dual deployment model with a smart launcher script that automatically selects the appropriate version based on your current working directory.

## 🏠 Local Development Deployment

When working inside the project directory, the local development version is automatically used.

### Setup

1. **Install dependencies and create virtual environment:**
   ```bash
   make install
   ```

2. **Enable direnv (recommended):**
   ```bash
   # Install direnv if not already installed
   brew install direnv  # On macOS

   # Add to your shell configuration (.bashrc, .zshrc, etc.)
   eval "$(direnv hook bash)"  # For bash
   eval "$(direnv hook zsh)"   # For zsh

   # Allow direnv in the project directory
   cd /Users/masa/Projects/managed/mcp-browser
   direnv allow
   ```

3. **Alternative: Manual PATH setup (without direnv):**
   ```bash
   # Option A: Source the setup script (temporary)
   source /Users/masa/Projects/managed/mcp-browser/bin/setup-path.sh

   # Option B: Add to your shell configuration (permanent)
   echo 'export PATH="/Users/masa/Projects/managed/mcp-browser/bin:$PATH"' >> ~/.bashrc
   # or for zsh
   echo 'export PATH="/Users/masa/Projects/managed/mcp-browser/bin:$PATH"' >> ~/.zshrc
   ```

### Usage

When inside the project directory or any subdirectory:
```bash
# Automatically uses local venv version
mcp-browser --help
mcp-browser serve
mcp-browser browser navigate --url https://example.com
```

### Benefits
- Instant code changes without reinstallation
- Isolated development environment
- No conflicts with system-wide version

## 🌍 System-Wide Deployment

For using mcp-browser from anywhere on your system, install via pipx.

### Setup

1. **Install pipx (if not installed):**
   ```bash
   brew install pipx  # On macOS
   pipx ensurepath
   ```

2. **Install mcp-browser via pipx:**
   ```bash
   # From PyPI (when published)
   pipx install mcp-browser

   # Or from GitHub
   pipx install git+https://github.com/yourusername/mcp-browser.git

   # Or from local project (for testing)
   pipx install /Users/masa/Projects/managed/mcp-browser
   ```

3. **Upgrade pipx version:**
   ```bash
   pipx upgrade mcp-browser
   ```

4. **Uninstall pipx version:**
   ```bash
   pipx uninstall mcp-browser
   ```

### Usage

From any directory outside the project:
```bash
# Automatically uses pipx version
mcp-browser --help
mcp-browser serve
```

## 🎯 Smart Launcher Features

The `/bin/mcp-browser` script intelligently selects which version to use:

### Automatic Detection
- **Inside project directory**: Uses local development version
- **Outside project directory**: Uses pipx-installed version

### Manual Override Flags
```bash
# Force local version from anywhere
mcp-browser --use-local [command]

# Force pipx version even in project directory
mcp-browser --use-pipx [command]

# Show version information
mcp-browser --version-info
```

## 🔧 Configuration Files

### .envrc (direnv configuration)
Automatically adds project bin to PATH when entering the directory.

### bin/mcp-browser
Smart launcher script that handles version selection.

## 📋 Common Scenarios

### Scenario 1: Active Development
```bash
cd /Users/masa/Projects/managed/mcp-browser
# Edit code
vim src/services/browser_service.py
# Test immediately (uses local version)
mcp-browser serve
```

### Scenario 2: Production Usage
```bash
cd ~/Documents
# Uses stable pipx version
mcp-browser serve
```

### Scenario 3: Testing Both Versions
```bash
# Test development version
mcp-browser --use-local serve

# Test production version
mcp-browser --use-pipx serve
```

## 🐛 Troubleshooting

### Issue: "Virtual environment not found"
**Solution:** Run `make install` in the project directory.

### Issue: "mcp-browser is not installed via pipx"
**Solution:** Install with `pipx install mcp-browser` or use from project directory.

### Issue: Command not found
**Solution:**
1. Ensure direnv is set up: `direnv allow`
2. Or add to PATH manually: `export PATH="/Users/masa/Projects/managed/mcp-browser/bin:$PATH"`

### Issue: Wrong version being used
**Solution:** Check with `mcp-browser --version-info` and use override flags if needed.

## 🚀 Best Practices

1. **For Development:**
   - Always use direnv for automatic PATH management
   - Work inside the project directory
   - Use `make dev` for development mode

2. **For Production:**
   - Install via pipx for isolation
   - Keep pipx version updated regularly
   - Use stable releases, not development branches

3. **For Testing:**
   - Test both versions before releasing
   - Use override flags to ensure correct version
   - Document version-specific behaviors

## 📝 Version Management

### Checking Current Version
```bash
# Show which version will be used
mcp-browser --version-info

# Show actual package version
mcp-browser --version
```

### Keeping Versions in Sync
```bash
# Update local development
git pull
make install

# Update pipx version
pipx upgrade mcp-browser
```

## 🔗 Related Documentation

- [README.md](README.md) - Project overview and quick start
- [DEVELOPER.md](DEVELOPER.md) - Development setup and guidelines
- [CLAUDE.md](CLAUDE.md) - AI agent instructions
- [QUICKSTART.md](QUICKSTART.md) - Quick installation guide