#!/usr/bin/env bash
# MCP Browser Installation Script
# Installs mcp-browser using pipx for isolated environment management

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="mcp-browser"
HOME_DIR="$HOME/.mcp-browser"
BIN_DIR="$HOME/.local/bin"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

print_header() {
    echo ""
    echo "═══════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════"
    echo ""
}

# Check system requirements
check_requirements() {
    print_header "Checking System Requirements"

    local has_errors=false

    # Check for pipx
    if ! command -v pipx &> /dev/null; then
        print_warning "pipx is not installed"
        print_info "Installing pipx..."
        if command -v brew &> /dev/null; then
            brew install pipx
            pipx ensurepath
        elif command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y pipx
            pipx ensurepath
        else
            # Try installing via pip
            python3 -m pip install --user pipx
            python3 -m pipx ensurepath
        fi
        # Source the path updates
        if [[ -f "$HOME/.bashrc" ]]; then
            source "$HOME/.bashrc"
        elif [[ -f "$HOME/.zshrc" ]]; then
            source "$HOME/.zshrc"
        fi
        if ! command -v pipx &> /dev/null; then
            print_error "Failed to install pipx. Please install it manually."
            print_info "Visit: https://pypa.github.io/pipx/installation/"
            has_errors=true
        else
            print_status "pipx installed successfully"
        fi
    else
        print_status "pipx is installed"
    fi

    # Check Python
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        print_status "Python 3 found (version $python_version)"

        # Check if version is 3.8+
        major=$(echo "$python_version" | cut -d. -f1)
        minor=$(echo "$python_version" | cut -d. -f2)
        if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 8 ]); then
            print_error "Python 3.8+ required (found $python_version)"
            has_errors=true
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8+"
        has_errors=true
    fi

    # Check pip
    if command -v pip3 &> /dev/null; then
        print_status "pip3 found"
    else
        print_error "pip3 not found. Please install pip3"
        has_errors=true
    fi

    # Check Git (for development)
    if command -v git &> /dev/null; then
        print_status "Git found"
    else
        print_warning "Git not found (optional for development)"
    fi

    # Check Chrome/Chromium
    if [ -d "/Applications/Google Chrome.app" ] || [ -d "/Applications/Chromium.app" ] || command -v google-chrome &> /dev/null || command -v chromium &> /dev/null; then
        print_status "Chrome/Chromium browser found"
    else
        print_warning "Chrome/Chromium not found (required for browser integration)"
    fi

    if [ "$has_errors" = true ]; then
        echo ""
        print_error "Please install missing requirements and try again"
        exit 1
    fi

    echo ""
    print_status "All requirements met"
}

# Install mcp-browser using pipx
install_with_pipx() {
    print_header "Installing MCP Browser with pipx"

    # Check if already installed
    if pipx list 2>/dev/null | grep -q "$PROJECT_NAME"; then
        print_warning "$PROJECT_NAME is already installed via pipx"
        read -p "Do you want to reinstall it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Uninstalling existing installation..."
            pipx uninstall "$PROJECT_NAME"
        else
            print_info "Keeping existing installation"
            print_info "Run 'pipx upgrade $PROJECT_NAME' to upgrade"
            return 0
        fi
    fi

    # Install from current directory (development mode)
    if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
        print_info "Installing $PROJECT_NAME from local directory..."
        pipx install "$SCRIPT_DIR" --verbose
        print_status "$PROJECT_NAME installed successfully"
    else
        # Install from PyPI (when published)
        print_info "Installing $PROJECT_NAME from PyPI..."
        pipx install "$PROJECT_NAME" --verbose
        print_status "$PROJECT_NAME installed successfully"
    fi

    # Ensure Playwright browsers are installed
    print_info "Installing Playwright browsers..."
    pipx runpip "$PROJECT_NAME" install playwright
    pipx run --spec "$PROJECT_NAME" playwright install chromium
    print_status "Playwright browsers installed"

    # Show installed version
    print_info "Installed version:"
    mcp-browser --version || true
}

# Set up directories
setup_directories() {
    print_header "Setting Up Directories"

    # Create home directory structure
    local dirs=(
        "$HOME_DIR"
        "$HOME_DIR/config"
        "$HOME_DIR/logs"
        "$HOME_DIR/run"
        "$HOME_DIR/data"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created $dir"
        else
            print_info "Directory exists: $dir"
        fi
    done

    # Create port-specific log directories
    for port in {8875..8895}; do
        mkdir -p "$HOME_DIR/logs/$port"
    done
    print_status "Created port-specific log directories (8875-8895)"

    # Create default configuration
    local config_file="$HOME_DIR/config/settings.json"
    if [ ! -f "$config_file" ]; then
        cat > "$config_file" << EOF
{
    "storage": {
        "base_path": "$HOME_DIR/data",
        "max_file_size_mb": 50,
        "retention_days": 7
    },
    "websocket": {
        "port_range": [8875, 8895],
        "host": "localhost"
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}
EOF
        print_status "Created default configuration"
    else
        print_info "Configuration already exists"
    fi
}

# Verify installation
verify_installation() {
    print_header "Verifying Installation"

    # Check if mcp-browser command is available
    if command -v mcp-browser &> /dev/null; then
        print_status "mcp-browser command is available"
        local version=$(mcp-browser --version 2>/dev/null || echo "unknown")
        print_info "Version: $version"
    else
        print_error "mcp-browser command not found in PATH"
        print_info "You may need to restart your shell or run:"
        echo "  pipx ensurepath"
        echo "  source ~/.bashrc  # or ~/.zshrc"
    fi

    # Check pipx installation
    if pipx list 2>/dev/null | grep -q "$PROJECT_NAME"; then
        print_status "$PROJECT_NAME is installed via pipx"
    else
        print_warning "$PROJECT_NAME not found in pipx list"
    fi
}

# Initialize project extension
initialize_project() {
    print_header "Project Extension Setup"

    print_info "Each project needs its own extension copy"
    echo ""
    echo "To initialize a project:"
    echo "  1. Navigate to your project directory:"
    echo "     cd /path/to/your/project"
    echo ""
    echo "  2. Initialize the extension:"
    echo "     mcp-browser init"
    echo ""
    echo "  3. Start the server with dashboard:"
    echo "     mcp-browser start"
    echo ""
    echo "  4. Open the dashboard:"
    echo "     http://localhost:8080"
    echo ""
    echo "  5. Install the extension from the dashboard"
    echo "  2. Enable 'Developer mode' (top right)"
    echo "  3. Click 'Load unpacked'"
    echo "  4. Select the directory: $extension_dir"
    echo ""
    print_info "The extension will show a green indicator when connected"
}

# Test installation
test_installation() {
    print_header "Testing Installation"

    # Test mcp-browser command
    print_info "Testing mcp-browser command..."
    if mcp-browser --version > /dev/null 2>&1; then
        print_status "mcp-browser command working"
        local version=$(mcp-browser --version 2>/dev/null | head -n1)
        print_info "Version: $version"
    else
        print_warning "mcp-browser command test failed"
        print_info "Try running: pipx ensurepath"
    fi

    # Test WebSocket port availability
    print_info "Checking WebSocket port availability..."
    local available_ports=0
    for port in {8875..8885}; do
        if ! lsof -i :$port > /dev/null 2>&1; then
            available_ports=$((available_ports + 1))
        fi
    done
    print_status "$available_ports ports available (8875-8885)"

    # Check dashboard port
    if ! lsof -i :8080 > /dev/null 2>&1; then
        print_status "Dashboard port 8080 is available"
    else
        print_warning "Port 8080 is in use (dashboard may conflict)"
    fi

    echo ""
    print_status "Installation test completed"
}

# Show next steps
show_next_steps() {
    print_header "Installation Complete!"

    echo "MCP Browser has been successfully installed via pipx."
    echo ""
    echo "Quick Start:"
    echo ""
    echo "1. Navigate to your project:"
    echo "   cd /path/to/your/project"
    echo ""
    echo "2. Initialize the extension:"
    echo "   mcp-browser init"
    echo ""
    echo "3. Start server with dashboard:"
    echo "   mcp-browser start"
    echo ""
    echo "4. Open dashboard in browser:"
    echo "   http://localhost:8080"
    echo ""
    echo "5. Install Chrome extension:"
    echo "   - Click 'Install Extension' in dashboard"
    echo "   - Follow the step-by-step guide"
    echo ""
    echo "Additional Commands:"
    echo "   mcp-browser status      # Check server status"
    echo "   mcp-browser dashboard   # Run dashboard only"
    echo "   mcp-browser mcp        # Run in MCP stdio mode"
    echo ""
    echo "To upgrade later:"
    echo "   pipx upgrade mcp-browser"
    echo ""
    print_info "Documentation: https://github.com/yourusername/mcp-browser"
}

# Main installation flow
main() {
    print_header "MCP Browser Installation via pipx"

    echo "This script will install MCP Browser using pipx."
    echo "Installation method: pipx (isolated environment)"
    echo "Source directory: $SCRIPT_DIR"
    echo "Config directory: $HOME_DIR"
    echo ""

    read -p "Continue with installation? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]] && [ -n "$REPLY" ]; then
        print_info "Installation cancelled"
        exit 0
    fi

    # Run installation steps
    check_requirements
    install_with_pipx
    setup_directories
    verify_installation
    test_installation
    initialize_project
    show_next_steps
}

# Run main function
main "$@"