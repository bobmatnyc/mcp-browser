# ============================================================================
# Makefile for MCP Browser - Modular Build System
# ============================================================================
# Architecture: Python MCP Server + Chrome Extension
# Build System: Modular makefiles in .makefiles/
#
# Quick Start:
#   make install         # Install dependencies
#   make dev             # Start development mode
#   make test            # Run all tests
#   make quality         # Run all quality checks
#
# Release:
#   make release-patch   # Complete patch release (recommended)
#   make release-minor   # Complete minor release
#   make release-major   # Complete major release
# ============================================================================

.DEFAULT_GOAL := help
.PHONY: help

# ============================================================================
# Load Modular Makefiles
# ============================================================================
-include .makefiles/common.mk
-include .makefiles/deps.mk
-include .makefiles/quality.mk
-include .makefiles/testing.mk
-include .makefiles/release.mk

# ============================================================================
# Load Environment Variables
# ============================================================================
ifneq (,$(wildcard .env.local))
    include .env.local
    export
endif

# ============================================================================
# Help Target
# ============================================================================
help: ## Show this help message
	@echo "$(BLUE)MCP Browser - Modular Build System$(NC)"
	@echo "$(YELLOW)Usage: make <target>$(NC)"
	@echo ""
	@echo "$(YELLOW)Core Targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | grep -v ".makefiles" | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quality & Testing (from .makefiles/):$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' .makefiles/quality.mk .makefiles/testing.mk 2>/dev/null | grep -E "(quality|lint|test)" | sort -u | awk -F: 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}' | head -10
	@echo ""
	@echo "$(YELLOW)Release (from .makefiles/):$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' .makefiles/release.mk 2>/dev/null | grep -E "(release-|bump-)" | sort -u | awk -F: 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}' | head -8
	@echo ""
	@echo "$(YELLOW)Development & Extension:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | grep -E "(dev|ext-|extension)" | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}' | head -10
	@echo ""
	@echo "$(BLUE)For complete list: make help-all$(NC)"

help-all: ## Show all available targets
	@echo "$(BLUE)MCP Browser - All Available Targets$(NC)"
	@echo ""
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile .makefiles/*.mk 2>/dev/null | sort -u | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'

# ============================================================================
# Build Target
# ============================================================================
build: ext-deploy ## Build and validate the project
	@echo "$(BLUE)Building project...$(NC)"
	@$(PYTHON) -m build
	@echo "$(BLUE)Validating installation...$(NC)"
	@pip install -e . --quiet
	@mcp-browser --help > /dev/null
	@echo "$(GREEN)✓ Build successful$(NC)"

# ============================================================================
# Clean Targets
# ============================================================================
clean: ## Clean build artifacts and cache
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf build/ dist/ *.egg-info/
	@rm -rf .pytest_cache/ htmlcov/ .coverage
	@rm -rf src/__pycache__/ tests/__pycache__/
	@find . -type d -name "__pycache__" -delete
	@find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Clean complete$(NC)"

# ============================================================================
# Development Targets
# ============================================================================
dev: ext-deploy ## Start full development environment (server + extension)
	@echo "$(BLUE)Starting full development environment...$(NC)"
	@echo "$(YELLOW)This will start both MCP server and Chrome with extension loaded$(NC)"
	@scripts/dev-full.sh

dev-server: ## Start only the MCP server with hot reload
	@echo "$(BLUE)Starting development server with hot reload...$(NC)"
	@scripts/dev-server.sh

dev-extension: ## Load Chrome extension in development mode
	@echo "$(BLUE)Loading Chrome extension...$(NC)"
	@scripts/dev-extension.sh

dev-extension-manual: ## Show manual extension loading instructions
	@echo "$(BLUE)Manual extension loading instructions:$(NC)"
	@scripts/dev-extension.sh --instructions-only

dev-status: ## Show development environment status
	@echo "$(BLUE)Development Environment Status$(NC)"
	@echo "================================="
	@echo -n "MCP Server: "
	@curl -s http://localhost:8875 >/dev/null 2>&1 && echo "$(GREEN)Running$(NC)" || echo "$(RED)Stopped$(NC)"
	@echo -n "Extension Icons: "
	@test -f extension/icon-16.png && echo "$(GREEN)Present$(NC)" || echo "$(RED)Missing$(NC)"
	@echo -n "Scripts: "
	@test -x scripts/dev-full.sh && echo "$(GREEN)Executable$(NC)" || echo "$(RED)Not executable$(NC)"
	@echo -n "Environment: "
	@test -f .env.development && echo "$(GREEN)Configured$(NC)" || echo "$(RED)Missing$(NC)"

dev-logs: ## Show development server logs
	@echo "$(BLUE)Development Server Logs$(NC)"
	@if [ -f tmp/dev-server.pid ]; then \
		echo "Server PID: $$(cat tmp/dev-server.pid)"; \
		echo "Recent logs:"; \
		tail -20 tmp/logs/mcp-server.log 2>/dev/null || echo "No logs found"; \
	else \
		echo "$(YELLOW)Development server not running$(NC)"; \
	fi

dev-clean: ## Clean development artifacts
	@echo "$(BLUE)Cleaning development artifacts...$(NC)"
	@rm -rf tmp/chrome-dev-profile
	@rm -f tmp/dev-server.pid tmp/chrome-dev.pid
	@rm -rf tmp/logs
	@echo "$(GREEN)✓ Development artifacts cleaned$(NC)"

# ============================================================================
# MCP Server Targets
# ============================================================================
mcp: ## Run in MCP mode for Claude Desktop
	@echo "$(BLUE)Starting MCP server for Claude Desktop...$(NC)"
	@echo "$(YELLOW)Add to Claude config: {\"mcpServers\": {\"mcp-browser\": {\"command\": \"mcp-browser\", \"args\": [\"mcp\"]}}}$(NC)"
	@$(PYTHON) -m src.cli.main mcp

status: ## Show server status
	@echo "$(BLUE)Checking server status...$(NC)"
	@$(PYTHON) -m src.cli.main status

version: ## Show version information
	@$(PYTHON) -m src.cli.main version

# ============================================================================
# Extension Build Targets
# ============================================================================
extension-build: ## Build Chrome extension with icons
	@echo "$(BLUE)Building Chrome extension...$(NC)"
	@$(PYTHON) tmp/create_extension_icons.py || echo "$(YELLOW)Icons already exist$(NC)"
	@echo "$(GREEN)✓ Extension ready to load$(NC)"
	@echo "$(YELLOW)Navigate to chrome://extensions/ and load 'extension/' folder$(NC)"

extension-test: ## Test extension connection
	@echo "$(BLUE)Testing extension connection...$(NC)"
	@$(PYTHON) -c "import asyncio; from src.cli.main import BrowserMCPServer; server = BrowserMCPServer(); asyncio.run(server.show_status())"

extension-reload: ## Instructions for reloading extension during development
	@echo "$(BLUE)Extension Reload Instructions:$(NC)"
	@echo "1. Open chrome://extensions/"
	@echo "2. Find 'mcp-browser Console Capture'"
	@echo "3. Click the reload button (🔄)"
	@echo "4. Or use the reload shortcut: Ctrl+R on the extensions page"

test-extension: ## Test Chrome extension functionality
	@echo "$(BLUE)Testing Chrome extension...$(NC)"
	@$(PYTHON) tests/integration/test_implementation.py

# ============================================================================
# Extension Package Management
# ============================================================================
ext-build: ## Build extension package with current version
	@echo "$(BLUE)Building Chrome extension package...$(NC)"
	@$(PYTHON) scripts/build_extension.py build

ext-build-auto: ## Build with auto-version if changes detected
	@echo "$(BLUE)Building extension with auto-versioning...$(NC)"
	@$(PYTHON) scripts/build_extension.py build --auto-version

ext-release: ## Auto-increment patch version and build
	@echo "$(BLUE)Releasing extension (patch increment)...$(NC)"
	@$(PYTHON) scripts/build_extension.py release

ext-release-patch: ## Release with patch version bump
	@echo "$(BLUE)Releasing extension (patch: x.x.N+1)...$(NC)"
	@$(PYTHON) scripts/build_extension.py release --bump patch

ext-release-minor: ## Release with minor version bump
	@echo "$(BLUE)Releasing extension (minor: x.N+1.0)...$(NC)"
	@$(PYTHON) scripts/build_extension.py release --bump minor

ext-release-major: ## Release with major version bump
	@echo "$(BLUE)Releasing extension (major: N+1.0.0)...$(NC)"
	@$(PYTHON) scripts/build_extension.py release --bump major

ext-clean: ## Clean extension build artifacts
	@echo "$(BLUE)Cleaning extension packages...$(NC)"
	@$(PYTHON) scripts/build_extension.py clean
	@echo "$(GREEN)✓ Extension packages cleaned$(NC)"

ext-sync: ## Sync extension version with project version
	@echo "$(BLUE)Syncing extension version with project...$(NC)"
	@$(PYTHON) scripts/build_extension.py sync

ext-info: ## Show extension version information and change status
	@$(PYTHON) scripts/build_extension.py info

ext-deploy: ## Deploy extensions from source to mcp-browser-extensions/
	@echo "$(BLUE)Deploying browser extensions from source...$(NC)"
	@mkdir -p mcp-browser-extensions
	@rm -rf mcp-browser-extensions/chrome mcp-browser-extensions/firefox mcp-browser-extensions/safari
	@cp -r src/extensions/chrome mcp-browser-extensions/chrome
	@cp -r src/extensions/firefox mcp-browser-extensions/firefox
	@if [ -d src/extensions/safari ]; then cp -r src/extensions/safari mcp-browser-extensions/safari; fi
	@VERSION=$$(grep -m1 '__version__' src/_version.py | cut -d'"' -f2); \
	TIMESTAMP=$$(date -u +%Y-%m-%dT%H:%M:%SZ); \
	echo "mcp-browser extension v$$VERSION" > mcp-browser-extensions/VERSION.txt; \
	echo "Deployed: $$TIMESTAMP" >> mcp-browser-extensions/VERSION.txt; \
	echo "Source: src/extensions/" >> mcp-browser-extensions/VERSION.txt; \
	echo "$(GREEN)✓ Extensions deployed to mcp-browser-extensions/ (v$$VERSION)$(NC)"
	@echo "  - Chrome:  mcp-browser-extensions/chrome/"
	@echo "  - Firefox: mcp-browser-extensions/firefox/"
	@test -d mcp-browser-extensions/safari && echo "  - Safari:  mcp-browser-extensions/safari/" || true
	@cat mcp-browser-extensions/VERSION.txt

# ============================================================================
# Docker Development
# ============================================================================
docker-dev: ## Start development environment with Docker
	@echo "$(BLUE)Starting Docker development environment...$(NC)"
	@docker-compose up --build

docker-dev-bg: ## Start development environment with Docker in background
	@echo "$(BLUE)Starting Docker development environment in background...$(NC)"
	@docker-compose up --build -d

docker-dev-chrome: ## Start development environment with Chrome container
	@echo "$(BLUE)Starting Docker development environment with Chrome...$(NC)"
	@docker-compose --profile chrome up --build

docker-logs: ## Show Docker development logs
	@echo "$(BLUE)Docker Development Logs$(NC)"
	@docker-compose logs -f mcp-server

docker-status: ## Show Docker development status
	@echo "$(BLUE)Docker Development Status$(NC)"
	@docker-compose ps

docker-clean: ## Clean Docker development environment
	@echo "$(BLUE)Cleaning Docker development environment...$(NC)"
	@docker-compose down -v
	@docker system prune -f

# ============================================================================
# Setup & Health Check
# ============================================================================
setup: install pre-commit extension-build ## Complete development environment setup
	@echo "$(GREEN)✓ Development environment ready$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. make dev           # Start full development environment"
	@echo "  2. make dev-server    # Start only MCP server"
	@echo "  3. make dev-extension # Load extension in Chrome"
	@echo "  4. Configure Claude Desktop with 'mcp-browser mcp'"

pre-commit: ## Setup pre-commit hooks
	@echo "$(BLUE)Setting up pre-commit hooks...$(NC)"
	@pip install pre-commit
	@pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

health: ## Quick health check of all components
	@echo "$(BLUE)Health Check...$(NC)"
	@echo -n "Python package: "
	@$(PYTHON) -c "import src; print('✓ OK')" || echo "✗ FAIL"
	@echo -n "Dependencies: "
	@$(PYTHON) -c "import websockets, playwright, mcp; print('✓ OK')" || echo "✗ FAIL"
	@echo -n "Extension files: "
	@test -f extension/manifest.json && echo "✓ OK" || echo "✗ FAIL"
	@echo -n "Tests directory: "
	@test -d tests && echo "✓ OK" || echo "✗ FAIL"

# ============================================================================
# Documentation
# ============================================================================
docs: ## List available documentation
	@echo "$(BLUE)Documentation available:$(NC)"
	@echo "  README.md       - Project overview and installation"
	@echo "  CLAUDE.md       - AI agent instructions"
	@echo "  DEVELOPER.md    - Technical implementation details"
	@echo "  CODE_STRUCTURE.md - Architecture analysis"

# ============================================================================
# Deployment (legacy alias)
# ============================================================================
deploy: clean build test ## Build and test (use 'make release-*' for publishing)
	@echo "$(GREEN)✓ Build and tests complete$(NC)"
	@echo "$(YELLOW)To publish, use: make release-patch/minor/major$(NC)"
