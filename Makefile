# Makefile for MCP Browser - Single Path Workflows
# Architecture: Python MCP Server + Chrome Extension

.DEFAULT_GOAL := help
.PHONY: help install dev build test lint format quality clean deploy version bump-patch bump-minor bump-major check-version

# Colors for output
GREEN := \033[0;32m
BLUE := \033[0;34m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)MCP Browser - Single Path Commands$(NC)"
	@echo "$(YELLOW)Usage: make <target>$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make install    # Install dependencies"
	@echo "  make dev        # Start development mode"
	@echo "  make test       # Run all tests"

# ONE way to install dependencies
install: ## Install all dependencies and Playwright browsers
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	pip install -e ".[dev]"
	@echo "$(BLUE)Installing Playwright browsers...$(NC)"
	playwright install chromium
	@echo "$(GREEN)✓ Installation complete$(NC)"

# ONE way to develop - Full development environment
dev: ## Start full development environment (server + extension)
	@echo "$(BLUE)Starting full development environment...$(NC)"
	@echo "$(YELLOW)This will start both MCP server and Chrome with extension loaded$(NC)"
	scripts/dev-full.sh

# Development subcommands
dev-server: ## Start only the MCP server with hot reload
	@echo "$(BLUE)Starting development server with hot reload...$(NC)"
	scripts/dev-server.sh

dev-extension: ## Load Chrome extension in development mode
	@echo "$(BLUE)Loading Chrome extension...$(NC)"
	scripts/dev-extension.sh

dev-extension-manual: ## Show manual extension loading instructions
	@echo "$(BLUE)Manual extension loading instructions:$(NC)"
	scripts/dev-extension.sh --instructions-only

# ONE way to build
build: ## Build and validate the project
	@echo "$(BLUE)Building project...$(NC)"
	python -m build
	@echo "$(BLUE)Validating installation...$(NC)"
	pip install -e . --quiet
	browserpymcp --help > /dev/null
	@echo "$(GREEN)✓ Build successful$(NC)"

# ONE way to test
test: ## Run all tests with coverage
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest tests/integration/ -v

test-extension: ## Test Chrome extension functionality
	@echo "$(BLUE)Testing Chrome extension...$(NC)"
	python test_implementation.py

# ONE way to lint and format
lint: ## Check code style and type hints
	@echo "$(BLUE)Checking code style...$(NC)"
	ruff check src/ tests/
	@echo "$(BLUE)Checking type hints...$(NC)"
	mypy src/

lint-fix: ## Fix code style automatically
	@echo "$(BLUE)Fixing code style...$(NC)"
	ruff check --fix src/ tests/
	black src/ tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	black src/ tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

# ONE way to run quality checks
quality: lint test ## Run all quality checks (lint + test)
	@echo "$(GREEN)✓ All quality checks passed$(NC)"

# ONE way to clean
clean: ## Clean build artifacts and cache
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ htmlcov/ .coverage
	rm -rf src/__pycache__/ tests/__pycache__/
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Clean complete$(NC)"

# ONE way to deploy/publish
deploy: clean build test ## Deploy to PyPI (requires auth)
	@echo "$(BLUE)Deploying to PyPI...$(NC)"
	twine check dist/*
	twine upload dist/*
	@echo "$(GREEN)✓ Deployment complete$(NC)"

# MCP-specific commands
mcp: ## Run in MCP mode for Claude Desktop
	@echo "$(BLUE)Starting MCP server for Claude Desktop...$(NC)"
	@echo "$(YELLOW)Add to Claude config: {\"mcpServers\": {\"browserpymcp\": {\"command\": \"browserpymcp\", \"args\": [\"mcp\"]}}}$(NC)"
	python -m src.cli.main mcp

status: ## Show server status
	@echo "$(BLUE)Checking server status...$(NC)"
	python -m src.cli.main status

version: ## Show version information
	@python -m src.cli.main version

bump-patch: ## Bump patch version (1.0.1 -> 1.0.2)
	@echo "$(BLUE)Bumping patch version...$(NC)"
	@python scripts/bump_version.py patch
	@echo "$(GREEN)✓ Version bumped$(NC)"

bump-minor: ## Bump minor version (1.0.1 -> 1.1.0)
	@echo "$(BLUE)Bumping minor version...$(NC)"
	@python scripts/bump_version.py minor
	@echo "$(GREEN)✓ Version bumped$(NC)"

bump-major: ## Bump major version (1.0.1 -> 2.0.0)
	@echo "$(BLUE)Bumping major version...$(NC)"
	@python scripts/bump_version.py major
	@echo "$(GREEN)✓ Version bumped$(NC)"

check-version: ## Check version consistency
	@echo "$(BLUE)Checking version consistency...$(NC)"
	@python scripts/check_version_consistency.py

# Extension development
extension-build: ## Build Chrome extension with icons
	@echo "$(BLUE)Building Chrome extension...$(NC)"
	@python tmp/create_extension_icons.py || echo "$(YELLOW)Icons already exist$(NC)"
	@echo "$(GREEN)✓ Extension ready to load$(NC)"
	@echo "$(YELLOW)Navigate to chrome://extensions/ and load 'extension/' folder$(NC)"

extension-test: ## Test extension connection
	@echo "$(BLUE)Testing extension connection...$(NC)"
	python -c "import asyncio; from src.cli.main import BrowserMCPServer; server = BrowserMCPServer(); asyncio.run(server.show_status())"

extension-reload: ## Instructions for reloading extension during development
	@echo "$(BLUE)Extension Reload Instructions:$(NC)"
	@echo "1. Open chrome://extensions/"
	@echo "2. Find 'BrowserPyMCP Console Capture'"
	@echo "3. Click the reload button (🔄)"
	@echo "4. Or use the reload shortcut: Ctrl+R on the extensions page"

# Documentation generation
docs: ## Generate documentation
	@echo "$(BLUE)Documentation available:$(NC)"
	@echo "  README.md       - Project overview and installation"
	@echo "  CLAUDE.md       - AI agent instructions"
	@echo "  DEVELOPER.md    - Technical implementation details"
	@echo "  CODE_STRUCTURE.md - Architecture analysis"

# Setup pre-commit hooks
pre-commit: ## Setup pre-commit hooks
	@echo "$(BLUE)Setting up pre-commit hooks...$(NC)"
	pip install pre-commit
	pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

# Development environment setup
setup: install pre-commit extension-build ## Complete development environment setup
	@echo "$(GREEN)✓ Development environment ready$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. make dev           # Start full development environment"
	@echo "  2. make dev-server    # Start only MCP server"
	@echo "  3. make dev-extension # Load extension in Chrome"
	@echo "  4. Configure Claude Desktop with 'browserpymcp mcp'"

# Development workflow commands
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

# Service-specific commands for debugging
debug-services: ## Show service container status
	@echo "$(BLUE)Service Container Debug...$(NC)"
	python -c "import asyncio; from src.container import ServiceContainer; c = ServiceContainer(); print('Container initialized:', c.get_all_service_names() if hasattr(c, 'get_all_service_names') else 'Empty')"

debug-websocket: ## Test WebSocket connection
	@echo "$(BLUE)Testing WebSocket on port 8875...$(NC)"
	python -c "import asyncio, websockets; asyncio.run(websockets.connect('ws://localhost:8875'))" || echo "$(YELLOW)Server not running - use 'make dev' first$(NC)"

# Docker development commands
docker-dev: ## Start development environment with Docker
	@echo "$(BLUE)Starting Docker development environment...$(NC)"
	docker-compose up --build

docker-dev-bg: ## Start development environment with Docker in background
	@echo "$(BLUE)Starting Docker development environment in background...$(NC)"
	docker-compose up --build -d

docker-dev-chrome: ## Start development environment with Chrome container
	@echo "$(BLUE)Starting Docker development environment with Chrome...$(NC)"
	docker-compose --profile chrome up --build

docker-dev-tools: ## Start development tools container
	@echo "$(BLUE)Starting development tools container...$(NC)"
	docker-compose --profile tools run --rm dev-tools bash

docker-logs: ## Show Docker development logs
	@echo "$(BLUE)Docker Development Logs$(NC)"
	docker-compose logs -f mcp-server

docker-status: ## Show Docker development status
	@echo "$(BLUE)Docker Development Status$(NC)"
	docker-compose ps

docker-clean: ## Clean Docker development environment
	@echo "$(BLUE)Cleaning Docker development environment...$(NC)"
	docker-compose down -v
	docker system prune -f

docker-rebuild: ## Rebuild Docker development environment
	@echo "$(BLUE)Rebuilding Docker development environment...$(NC)"
	docker-compose down
	docker-compose build --no-cache
	docker-compose up


# Quick health check
health: ## Quick health check of all components
	@echo "$(BLUE)Health Check...$(NC)"
	@echo -n "Python package: "
	@python -c "import src; print('✓ OK')" || echo "✗ FAIL"
	@echo -n "Dependencies: "
	@python -c "import websockets, playwright, mcp; print('✓ OK')" || echo "✗ FAIL"
	@echo -n "Extension files: "
	@test -f extension/manifest.json && echo "✓ OK" || echo "✗ FAIL"
	@echo -n "Tests directory: "
	@test -d tests && echo "✓ OK" || echo "✗ FAIL"