# ============================================================================
# deps.mk - Dependency Management
# ============================================================================
# Provides: pip-based dependency management and installation
# Include in main Makefile with: -include .makefiles/deps.mk
#
# Adapted for mcp-browser (pip-based, no Poetry)
# Dependencies: common.mk (for colors, PYTHON)
# Last updated: 2025-12-11
# ============================================================================
#
# Workflow for updating dependencies:
#   1. make install            - Install dependencies from pyproject.toml
#   2. make install-dev        - Install with dev dependencies
#   3. make test               - Test with installed deps
#
# For CI/CD integration:
#   make install-prod          - Install production dependencies only
# ============================================================================

# ============================================================================
# Dependency Management Target Declarations
# ============================================================================
.PHONY: install install-prod install-dev deps-info playwright-install

# ============================================================================
# Installation Targets
# ============================================================================

install: ## Install project with all dependencies and Playwright browsers
	@echo "$(YELLOW)📦 Installing Python dependencies...$(NC)"
	@$(PYTHON) -m pip install -e ".[dev]"
	@echo "$(GREEN)✓ Python dependencies installed$(NC)"
	@$(MAKE) playwright-install

install-prod: ## Install production dependencies only (no dev deps)
	@echo "$(YELLOW)📦 Installing production dependencies...$(NC)"
	@$(PYTHON) -m pip install -e .
	@echo "$(GREEN)✓ Production dependencies installed$(NC)"
	@$(MAKE) playwright-install

install-dev: install ## Alias for development installation (includes dev deps)

playwright-install: ## Install Playwright browsers
	@echo "$(YELLOW)🌐 Installing Playwright browsers...$(NC)"
	@playwright install chromium
	@echo "$(GREEN)✓ Playwright browsers installed$(NC)"

deps-info: ## Display dependency information from pyproject.toml
	@echo "$(BLUE)════════════════════════════════════════$(NC)"
	@echo "$(BLUE)Dependency Information$(NC)"
	@echo "$(BLUE)════════════════════════════════════════$(NC)"
	@if [ -f pyproject.toml ]; then \
		echo "$(GREEN)✓ pyproject.toml exists$(NC)"; \
		echo ""; \
		echo "$(YELLOW)Production dependencies:$(NC)"; \
		grep -A 20 '^\[project\]' pyproject.toml | grep 'dependencies =' -A 10 | head -15; \
		echo ""; \
		echo "$(YELLOW)Dev dependencies:$(NC)"; \
		grep -A 20 'optional-dependencies' pyproject.toml | grep 'dev =' -A 10 | head -15; \
	else \
		echo "$(RED)✗ pyproject.toml not found$(NC)"; \
	fi

# ============================================================================
# Dependency Management Best Practices
# ============================================================================
# 1. Keep pyproject.toml dependencies up to date
# 2. Test after updating dependencies: `make test`
# 3. Use `make install-prod` for production deployments
# 4. Use `make install-dev` for development environments
# ============================================================================

# ============================================================================
# Usage Examples
# ============================================================================
# Initial setup:
#   make install               # Install all dependencies (dev + prod + Playwright)
#
# Production deployment:
#   make install-prod          # Install production dependencies only
#
# Development setup:
#   make install-dev           # Install with dev dependencies
#
# Check dependencies:
#   make deps-info             # View dependencies from pyproject.toml
#   pip list                   # View installed packages
#   pip show <package>         # Check specific package
# ============================================================================
