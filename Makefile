# Makefile for MCP Browser - Single Path Workflows
# Architecture: Python MCP Server + Chrome Extension

.DEFAULT_GOAL := help
.PHONY: help install dev build test lint format quality clean deploy

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

# ONE way to develop
dev: ## Start development server with WebSocket
	@echo "$(BLUE)Starting development server...$(NC)"
	@echo "$(YELLOW)Chrome Extension: Load 'extension/' folder in chrome://extensions/$(NC)"
	@echo "$(YELLOW)Claude Desktop: Use 'browserpymcp mcp' command$(NC)"
	python -m src.cli.main start

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

# Extension development
extension-build: ## Build Chrome extension (if build steps needed)
	@echo "$(BLUE)Chrome extension ready to load$(NC)"
	@echo "$(YELLOW)Navigate to chrome://extensions/ and load 'extension/' folder$(NC)"

extension-test: ## Test extension connection
	@echo "$(BLUE)Testing extension connection...$(NC)"
	python -c "import asyncio; from src.cli.main import BrowserMCPServer; server = BrowserMCPServer(); asyncio.run(server.show_status())"

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
setup: install pre-commit ## Complete development environment setup
	@echo "$(GREEN)✓ Development environment ready$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. make dev           # Start development server"
	@echo "  2. Load extension in Chrome"
	@echo "  3. Configure Claude Desktop"

# Service-specific commands for debugging
debug-services: ## Show service container status
	@echo "$(BLUE)Service Container Debug...$(NC)"
	python -c "import asyncio; from src.container import ServiceContainer; c = ServiceContainer(); print('Container initialized:', c.get_all_service_names() if hasattr(c, 'get_all_service_names') else 'Empty')"

debug-websocket: ## Test WebSocket connection
	@echo "$(BLUE)Testing WebSocket on port 8875...$(NC)"
	python -c "import asyncio, websockets; asyncio.run(websockets.connect('ws://localhost:8875'))" || echo "$(YELLOW)Server not running - use 'make dev' first$(NC)"

# Version management
version: ## Show current version
	@echo "$(BLUE)Current version:$(NC)"
	python -c "import toml; print(toml.load('pyproject.toml')['project']['version'])"

bump-version: ## Bump version (requires manual edit of pyproject.toml)
	@echo "$(YELLOW)Manual version bump required in pyproject.toml$(NC)"
	@echo "Current version: $$(python -c "import toml; print(toml.load('pyproject.toml')['project']['version'])")"

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