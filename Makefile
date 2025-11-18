# Makefile for MCP Browser - Single Path Workflows
# Architecture: Python MCP Server + Chrome Extension

.DEFAULT_GOAL := help
.PHONY: help install dev build test lint format quality clean deploy version bump-patch bump-minor bump-major check-version \
        pre-publish security-scan release-prep bump-and-commit-patch bump-and-commit-minor bump-and-commit-major \
        publish-pypi github-release update-homebrew release-patch release-minor release-major verify-release

# Load environment variables from .env.local if it exists
ifneq (,$(wildcard .env.local))
    include .env.local
    export
endif

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
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make install         # Install dependencies"
	@echo "  make dev             # Start development mode"
	@echo "  make test            # Run all tests"
	@echo ""
	@echo "$(YELLOW)Release Automation:$(NC)"
	@echo "  make release-patch   # Complete patch release (recommended)"
	@echo "  make release-minor   # Complete minor release"
	@echo "  make release-major   # Complete major release"
	@echo "  make release-prep    # Run quality gate + security scan"
	@echo "  make verify-release  # Verify published release"

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
	python tests/integration/test_implementation.py

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
	@echo "2. Find 'mcp-browser Console Capture'"
	@echo "3. Click the reload button (🔄)"
	@echo "4. Or use the reload shortcut: Ctrl+R on the extensions page"

# Extension build and packaging commands
ext-build: ## Build extension package with current version
	@echo "$(BLUE)Building Chrome extension package...$(NC)"
	@python scripts/build_extension.py build

ext-build-auto: ## Build with auto-version if changes detected
	@echo "$(BLUE)Building extension with auto-versioning...$(NC)"
	@python scripts/build_extension.py build --auto-version

ext-release: ## Auto-increment patch version and build
	@echo "$(BLUE)Releasing extension (patch increment)...$(NC)"
	@python scripts/build_extension.py release

ext-release-patch: ## Release with patch version bump
	@echo "$(BLUE)Releasing extension (patch: x.x.N+1)...$(NC)"
	@python scripts/build_extension.py release --bump patch

ext-release-minor: ## Release with minor version bump
	@echo "$(BLUE)Releasing extension (minor: x.N+1.0)...$(NC)"
	@python scripts/build_extension.py release --bump minor

ext-release-major: ## Release with major version bump
	@echo "$(BLUE)Releasing extension (major: N+1.0.0)...$(NC)"
	@python scripts/build_extension.py release --bump major

ext-version-patch: ## Increment patch version and build (backward compat)
	@echo "$(BLUE)Bumping patch version and building...$(NC)"
	@python scripts/build_extension.py version patch

ext-version-minor: ## Increment minor version and build (backward compat)
	@echo "$(BLUE)Bumping minor version and building...$(NC)"
	@python scripts/build_extension.py version minor

ext-version-major: ## Increment major version and build (backward compat)
	@echo "$(BLUE)Bumping major version and building...$(NC)"
	@python scripts/build_extension.py version major

ext-clean: ## Clean extension build artifacts
	@echo "$(BLUE)Cleaning extension packages...$(NC)"
	@python scripts/build_extension.py clean
	@echo "$(GREEN)✓ Extension packages cleaned$(NC)"

ext-sync: ## Sync extension version with project version
	@echo "$(BLUE)Syncing extension version with project...$(NC)"
	@python scripts/build_extension.py sync

ext-info: ## Show extension version information and change status
	@python scripts/build_extension.py info

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

# =============================================================================
# RELEASE AUTOMATION
# =============================================================================

# Pre-Release Quality Gate
pre-publish: clean ## Run all pre-publish quality checks
	@echo "$(BLUE)Running pre-publish quality gate...$(NC)"
	@echo "$(YELLOW)1/5 Linting...$(NC)"
	ruff check src/ tests/
	@echo "$(YELLOW)2/5 Formatting check...$(NC)"
	ruff format --check src/ tests/
	@echo "$(YELLOW)3/5 Type checking...$(NC)"
	-mypy src/ 2>/dev/null || echo "$(YELLOW)Type checking warnings (non-blocking)$(NC)"
	@echo "$(YELLOW)4/5 Running tests...$(NC)"
	pytest tests/ -v --cov=src
	@echo "$(YELLOW)5/5 Building package...$(NC)"
	python -m build
	@echo "$(GREEN)✓ All quality checks passed$(NC)"

# Security Scan
security-scan: ## Scan for secrets and vulnerabilities
	@echo "$(BLUE)Running security scan...$(NC)"
	@echo "$(YELLOW)Checking for hardcoded secrets...$(NC)"
	@! grep -rn "api[_-]key\s*=" src/ --include="*.py" | grep -v ".env" || (echo "$(RED)✗ Found hardcoded API keys$(NC)" && exit 1)
	@! grep -rn "password\s*=\s*['\"]" src/ --include="*.py" | grep -v "getpass" || (echo "$(RED)✗ Found hardcoded passwords$(NC)" && exit 1)
	@echo "$(YELLOW)Checking dependencies for vulnerabilities...$(NC)"
	-pip install safety 2>/dev/null
	-safety check || echo "$(YELLOW)Warning: Some dependency vulnerabilities found$(NC)"
	@echo "$(GREEN)✓ Security scan complete$(NC)"

# Release Preparation
release-prep: ## Prepare for release (quality gate + security)
	@echo "$(BLUE)======================================$(NC)"
	@echo "$(BLUE)   RELEASE PREPARATION CHECKLIST$(NC)"
	@echo "$(BLUE)======================================$(NC)"
	@$(MAKE) pre-publish
	@$(MAKE) security-scan
	@echo "$(GREEN)✓ Release preparation complete$(NC)"
	@echo "$(YELLOW)Ready to publish!$(NC)"

# Version Bump with Git Commit
bump-and-commit-patch: ## Bump patch version and commit changes
	@echo "$(BLUE)Bumping patch version...$(NC)"
	@python scripts/bump_version.py patch --no-git
	@NEW_VERSION=$$(cat VERSION); \
	echo "$(GREEN)New version: $$NEW_VERSION$(NC)"; \
	git add pyproject.toml src/_version.py VERSION CHANGELOG.md; \
	git commit -m "chore: bump version to $$NEW_VERSION"; \
	echo "$(GREEN)✓ Version bumped and committed$(NC)"

bump-and-commit-minor: ## Bump minor version and commit changes
	@echo "$(BLUE)Bumping minor version...$(NC)"
	@python scripts/bump_version.py minor --no-git
	@NEW_VERSION=$$(cat VERSION); \
	echo "$(GREEN)New version: $$NEW_VERSION$(NC)"; \
	git add pyproject.toml src/_version.py VERSION CHANGELOG.md; \
	git commit -m "chore: bump version to $$NEW_VERSION"; \
	echo "$(GREEN)✓ Version bumped and committed$(NC)"

bump-and-commit-major: ## Bump major version and commit changes
	@echo "$(BLUE)Bumping major version...$(NC)"
	@python scripts/bump_version.py major --no-git
	@NEW_VERSION=$$(cat VERSION); \
	echo "$(GREEN)New version: $$NEW_VERSION$(NC)"; \
	git add pyproject.toml src/_version.py VERSION CHANGELOG.md; \
	git commit -m "chore: bump version to $$NEW_VERSION"; \
	echo "$(GREEN)✓ Version bumped and committed$(NC)"

# PyPI Publishing
publish-pypi: ## Publish to PyPI using .env.local credentials
	@echo "$(BLUE)Publishing to PyPI...$(NC)"
	@if [ -z "$$PYPI_TOKEN" ]; then \
		echo "$(RED)ERROR: PYPI_TOKEN not found in .env.local$(NC)"; \
		echo "$(YELLOW)Please add: PYPI_TOKEN=pypi-...$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Uploading to PyPI...$(NC)"
	@TWINE_USERNAME=__token__ TWINE_PASSWORD=$$PYPI_TOKEN python -m twine upload dist/*
	@NEW_VERSION=$$(cat VERSION); \
	echo "$(GREEN)✓ Published to PyPI: https://pypi.org/project/mcp-browser/$$NEW_VERSION/$(NC)"

# GitHub Release
github-release: ## Create GitHub release using .env.local credentials
	@echo "$(BLUE)Creating GitHub release...$(NC)"
	@if [ -z "$$GITHUB_TOKEN" ]; then \
		echo "$(RED)ERROR: GITHUB_TOKEN not found in .env.local$(NC)"; \
		echo "$(YELLOW)Please add: GITHUB_TOKEN=ghp_...$(NC)"; \
		exit 1; \
	fi
	@NEW_VERSION=$$(cat VERSION); \
	GITHUB_OWNER=$${GITHUB_OWNER:-browserpymcp}; \
	echo "$(YELLOW)Creating release v$$NEW_VERSION...$(NC)"; \
	gh release create "v$$NEW_VERSION" \
		--title "v$$NEW_VERSION" \
		--notes "$$(python scripts/extract_changelog.py $$NEW_VERSION)" \
		--repo $$GITHUB_OWNER/mcp-browser \
		dist/*; \
	echo "$(GREEN)✓ GitHub release created$(NC)"

# Homebrew Tap Update
update-homebrew: ## Update Homebrew tap formula
	@echo "$(BLUE)Updating Homebrew tap...$(NC)"
	@NEW_VERSION=$$(cat VERSION); \
	echo "$(YELLOW)Fetching SHA256 from PyPI...$(NC)"; \
	bash scripts/update_homebrew_tap.sh $$NEW_VERSION; \
	echo "$(GREEN)✓ Homebrew tap information displayed$(NC)"

# Complete Release Workflows
release-patch: ## Complete patch release workflow (bump, build, publish, release)
	@echo "$(BLUE)======================================$(NC)"
	@echo "$(BLUE)   COMPLETE PATCH RELEASE WORKFLOW$(NC)"
	@echo "$(BLUE)======================================$(NC)"
	@$(MAKE) release-prep
	@$(MAKE) bump-and-commit-patch
	@$(MAKE) publish-pypi
	@git push origin main
	@$(MAKE) github-release
	@$(MAKE) update-homebrew
	@echo "$(GREEN)======================================$(NC)"
	@echo "$(GREEN)   ✓ RELEASE COMPLETE!$(NC)"
	@echo "$(GREEN)======================================$(NC)"
	@NEW_VERSION=$$(cat VERSION); \
	GITHUB_OWNER=$${GITHUB_OWNER:-browserpymcp}; \
	echo "$(YELLOW)Version $$NEW_VERSION published to:$(NC)"; \
	echo "  PyPI: https://pypi.org/project/mcp-browser/$$NEW_VERSION/"; \
	echo "  GitHub: https://github.com/$$GITHUB_OWNER/mcp-browser/releases/tag/v$$NEW_VERSION"

release-minor: ## Complete minor release workflow
	@echo "$(BLUE)======================================$(NC)"
	@echo "$(BLUE)   COMPLETE MINOR RELEASE WORKFLOW$(NC)"
	@echo "$(BLUE)======================================$(NC)"
	@$(MAKE) release-prep
	@$(MAKE) bump-and-commit-minor
	@$(MAKE) publish-pypi
	@git push origin main
	@$(MAKE) github-release
	@$(MAKE) update-homebrew
	@echo "$(GREEN)======================================$(NC)"
	@echo "$(GREEN)   ✓ RELEASE COMPLETE!$(NC)"
	@echo "$(GREEN)======================================$(NC)"
	@NEW_VERSION=$$(cat VERSION); \
	GITHUB_OWNER=$${GITHUB_OWNER:-browserpymcp}; \
	echo "$(YELLOW)Version $$NEW_VERSION published to:$(NC)"; \
	echo "  PyPI: https://pypi.org/project/mcp-browser/$$NEW_VERSION/"; \
	echo "  GitHub: https://github.com/$$GITHUB_OWNER/mcp-browser/releases/tag/v$$NEW_VERSION"

release-major: ## Complete major release workflow
	@echo "$(BLUE)======================================$(NC)"
	@echo "$(BLUE)   COMPLETE MAJOR RELEASE WORKFLOW$(NC)"
	@echo "$(BLUE)======================================$(NC)"
	@$(MAKE) release-prep
	@$(MAKE) bump-and-commit-major
	@$(MAKE) publish-pypi
	@git push origin main
	@$(MAKE) github-release
	@$(MAKE) update-homebrew
	@echo "$(GREEN)======================================$(NC)"
	@echo "$(GREEN)   ✓ RELEASE COMPLETE!$(NC)"
	@echo "$(GREEN)======================================$(NC)"
	@NEW_VERSION=$$(cat VERSION); \
	GITHUB_OWNER=$${GITHUB_OWNER:-browserpymcp}; \
	echo "$(YELLOW)Version $$NEW_VERSION published to:$(NC)"; \
	echo "  PyPI: https://pypi.org/project/mcp-browser/$$NEW_VERSION/"; \
	echo "  GitHub: https://github.com/$$GITHUB_OWNER/mcp-browser/releases/tag/v$$NEW_VERSION"

# Post-Release Verification
verify-release: ## Verify release was successful
	@echo "$(BLUE)Verifying release...$(NC)"
	@NEW_VERSION=$$(cat VERSION); \
	echo "$(YELLOW)Testing PyPI installation...$(NC)"; \
	pip install --upgrade mcp-browser==$$NEW_VERSION || echo "$(RED)✗ PyPI package not found yet (may need to wait for propagation)$(NC)"; \
	echo "$(YELLOW)Checking GitHub release...$(NC)"; \
	GITHUB_OWNER=$${GITHUB_OWNER:-browserpymcp}; \
	gh release view "v$$NEW_VERSION" --repo $$GITHUB_OWNER/mcp-browser && echo "$(GREEN)✓ GitHub release verified$(NC)" || echo "$(RED)✗ GitHub release not found$(NC)"

# =============================================================================
# RELEASE SCRIPT (AUTOMATED)
# =============================================================================

release-script-patch: ## Run automated release script for patch version
	@echo "$(BLUE)Running automated patch release...$(NC)"
	@python3 scripts/release.py patch

release-script-minor: ## Run automated release script for minor version
	@echo "$(BLUE)Running automated minor release...$(NC)"
	@python3 scripts/release.py minor

release-script-major: ## Run automated release script for major version
	@echo "$(BLUE)Running automated major release...$(NC)"
	@python3 scripts/release.py major

release-script-dry-run: ## Test release script without changes
	@echo "$(BLUE)Running dry-run release simulation...$(NC)"
	@python3 scripts/release.py --dry-run patch

release-script-skip-tests: ## Run release script skipping tests
	@echo "$(BLUE)Running release script (skipping tests)...$(NC)"
	@python3 scripts/release.py --skip-tests patch

release-script-skip-push: ## Run release script without pushing to GitHub
	@echo "$(BLUE)Running release script (local only)...$(NC)"
	@python3 scripts/release.py --skip-push patch