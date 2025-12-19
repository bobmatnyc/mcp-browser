# ============================================================================
# release.mk - Version & Publishing Management
# ============================================================================
# Provides: version bumping, build, publish to PyPI, GitHub releases
# Include in main Makefile with: -include .makefiles/release.mk
#
# Uses uv for all Python operations (run, build, publish)
# Adapted for mcp-browser to use scripts/release.py and scripts/bump_version.py
# Dependencies: common.mk (for colors, VERSION, ENV)
#               quality.mk (for pre-publish checks)
# Last updated: 2025-12-19
# ============================================================================

# ============================================================================
# Release Target Declarations
# ============================================================================
.PHONY: release-check release-patch release-minor release-major
.PHONY: release-build release-publish release-verify
.PHONY: release-dry-run release-test-pypi
.PHONY: build-metadata build-info-json
.PHONY: bump-patch bump-minor bump-major
.PHONY: release-script release-script-dry-run release-script-skip-tests

# ============================================================================
# Release Prerequisites Check
# ============================================================================

release-check: ## Check if environment is ready for release
	@echo "$(YELLOW)🔍 Checking release prerequisites...$(NC)"
	@echo "Checking required tools..."
	@command -v git >/dev/null 2>&1 || (echo "$(RED)✗ git not found$(NC)" && exit 1)
	@command -v uv >/dev/null 2>&1 || (echo "$(RED)✗ uv not found$(NC)" && exit 1)
	@command -v gh >/dev/null 2>&1 || (echo "$(RED)✗ GitHub CLI not found. Install from: https://cli.github.com/$(NC)" && exit 1)
	@echo "$(GREEN)✓ All required tools found$(NC)"
	@echo "Checking working directory..."
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "$(RED)✗ Working directory is not clean$(NC)"; \
		git status --short; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Working directory is clean$(NC)"
	@echo "Checking current branch..."
	@BRANCH=$$(git branch --show-current); \
	if [ "$$BRANCH" != "main" ]; then \
		echo "$(YELLOW)⚠ Currently on branch '$$BRANCH', not 'main'$(NC)"; \
		read -p "Continue anyway? [y/N]: " confirm; \
		if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
			echo "$(RED)Aborted$(NC)"; \
			exit 1; \
		fi; \
	else \
		echo "$(GREEN)✓ On main branch$(NC)"; \
	fi
	@echo "$(GREEN)✓ Release prerequisites check passed$(NC)"

# ============================================================================
# Build Metadata Tracking
# ============================================================================

build-metadata: ## Track build metadata in JSON format
	@echo "$(YELLOW)📋 Tracking build metadata...$(NC)"
	@mkdir -p $(BUILD_DIR)
	@VERSION=$$(cat $(VERSION_FILE) 2>/dev/null || echo "0.0.0"); \
	BUILD_NUM=$$(cat $(BUILD_NUMBER_FILE) 2>/dev/null || echo "0"); \
	COMMIT=$$(git rev-parse HEAD 2>/dev/null || echo "unknown"); \
	SHORT_COMMIT=$$(git rev-parse --short HEAD 2>/dev/null || echo "unknown"); \
	BRANCH=$$(git branch --show-current 2>/dev/null || echo "unknown"); \
	TIMESTAMP=$$(date -u +%Y-%m-%dT%H:%M:%SZ); \
	PYTHON_VER=$$(uv run python --version 2>&1); \
	echo "{" > $(BUILD_DIR)/metadata.json; \
	echo '  "version": "'$$VERSION'",' >> $(BUILD_DIR)/metadata.json; \
	echo '  "build_number": '$$BUILD_NUM',' >> $(BUILD_DIR)/metadata.json; \
	echo '  "commit": "'$$COMMIT'",' >> $(BUILD_DIR)/metadata.json; \
	echo '  "commit_short": "'$$SHORT_COMMIT'",' >> $(BUILD_DIR)/metadata.json; \
	echo '  "branch": "'$$BRANCH'",' >> $(BUILD_DIR)/metadata.json; \
	echo '  "timestamp": "'$$TIMESTAMP'",' >> $(BUILD_DIR)/metadata.json; \
	echo '  "python_version": "'$$PYTHON_VER'",' >> $(BUILD_DIR)/metadata.json; \
	echo '  "environment": "'$${ENV:-development}'"' >> $(BUILD_DIR)/metadata.json; \
	echo "}" >> $(BUILD_DIR)/metadata.json
	@echo "$(GREEN)✓ Build metadata saved to $(BUILD_DIR)/metadata.json$(NC)"

build-info-json: build-metadata ## Display build metadata from JSON
	@if [ -f $(BUILD_DIR)/metadata.json ]; then \
		cat $(BUILD_DIR)/metadata.json; \
	else \
		echo "$(YELLOW)No build metadata found. Run 'make build-metadata' first.$(NC)"; \
	fi

# ============================================================================
# Version Bumping (using scripts/bump_version.py)
# ============================================================================

bump-patch: ## Bump patch version using scripts/bump_version.py
	@echo "$(YELLOW)🔧 Bumping patch version...$(NC)"
	@uv run python scripts/bump_version.py patch
	@echo "$(GREEN)✓ Version bumped$(NC)"

bump-minor: ## Bump minor version using scripts/bump_version.py
	@echo "$(YELLOW)✨ Bumping minor version...$(NC)"
	@uv run python scripts/bump_version.py minor
	@echo "$(GREEN)✓ Version bumped$(NC)"

bump-major: ## Bump major version using scripts/bump_version.py
	@echo "$(YELLOW)💥 Bumping major version...$(NC)"
	@uv run python scripts/bump_version.py major
	@echo "$(GREEN)✓ Version bumped$(NC)"

# ============================================================================
# Release Build
# ============================================================================

release-build: pre-publish ext-deploy ## Build Python package for release (runs quality checks first)
	@echo "$(YELLOW)📦 Building package...$(NC)"
	@$(MAKE) build-metadata
	@rm -rf $(DIST_DIR)/ $(BUILD_DIR)/ *.egg-info
	@uv run python -m build $(BUILD_FLAGS)
	@uv run twine check $(DIST_DIR)/*
	@echo "$(GREEN)✓ Package validation passed$(NC)"
	@echo "$(GREEN)✓ Package built successfully$(NC)"
	@ls -la $(DIST_DIR)/

# ============================================================================
# Release Workflow Using scripts/release.py (RECOMMENDED)
# ============================================================================

release-patch: ## Complete patch release using scripts/release.py (RECOMMENDED)
	@echo "$(BLUE)Running automated patch release...$(NC)"
	@uv run python scripts/release.py patch

release-minor: ## Complete minor release using scripts/release.py (RECOMMENDED)
	@echo "$(BLUE)Running automated minor release...$(NC)"
	@uv run python scripts/release.py minor

release-major: ## Complete major release using scripts/release.py (RECOMMENDED)
	@echo "$(BLUE)Running automated major release...$(NC)"
	@uv run python scripts/release.py major

release-script: release-patch ## Alias for release-patch (backward compat)

release-dry-run: ## Test release script without making changes
	@echo "$(BLUE)Running dry-run release simulation...$(NC)"
	@uv run python scripts/release.py --dry-run patch

release-script-dry-run: release-dry-run ## Alias for release-dry-run

release-script-skip-tests: ## Run release script skipping tests
	@echo "$(BLUE)Running release script (skipping tests)...$(NC)"
	@uv run python scripts/release.py --skip-tests patch

# ============================================================================
# Publishing to PyPI
# ============================================================================

release-publish: ## Publish release to PyPI and create GitHub release
	@echo "$(YELLOW)🚀 Publishing release...$(NC)"
	@VERSION=$$(cat $(VERSION_FILE)); \
	echo "Publishing version: $$VERSION"; \
	read -p "Continue with publishing? [y/N]: " confirm; \
	if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
		echo "$(RED)Publishing aborted$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)📤 Publishing to PyPI...$(NC)"
	@uv run twine upload $(DIST_DIR)/*
	@echo "$(GREEN)✓ Published to PyPI$(NC)"
	@echo "$(YELLOW)📤 Creating GitHub release...$(NC)"
	@VERSION=$$(cat $(VERSION_FILE)); \
	gh release create "v$$VERSION" \
		--title "v$$VERSION" \
		--generate-notes \
		$(DIST_DIR)/* || echo "$(YELLOW)⚠ GitHub release creation failed$(NC)"
	@echo "$(GREEN)✓ GitHub release created$(NC)"
	@$(MAKE) release-verify

release-test-pypi: release-build ## Publish to TestPyPI for testing
	@echo "$(YELLOW)🧪 Publishing to TestPyPI...$(NC)"
	@uv run twine upload --repository testpypi $(DIST_DIR)/*
	@echo "$(GREEN)✓ Published to TestPyPI$(NC)"
	@echo "$(BLUE)Test install: pip install --index-url https://test.pypi.org/simple/ mcp-browser$(NC)"

# ============================================================================
# Release Verification
# ============================================================================

release-verify: ## Verify release across all channels
	@echo "$(YELLOW)🔍 Verifying release...$(NC)"
	@VERSION=$$(cat $(VERSION_FILE)); \
	echo "Verifying version: $$VERSION"; \
	echo ""; \
	echo "$(BLUE)📦 PyPI:$(NC) https://pypi.org/project/mcp-browser/$$VERSION/"; \
	echo "$(BLUE)🏷️  GitHub:$(NC) https://github.com/browserpymcp/mcp-browser/releases/tag/v$$VERSION"; \
	echo ""; \
	echo "$(GREEN)✓ Release verification links generated$(NC)"
	@echo "$(BLUE)💡 Test installation with:$(NC)"
	@echo "  pip install mcp-browser==$$(cat $(VERSION_FILE))"

# ============================================================================
# Usage Examples
# ============================================================================
# RECOMMENDED: Use scripts/release.py
#   make release-patch         # Complete patch release (automated)
#   make release-minor         # Complete minor release (automated)
#   make release-major         # Complete major release (automated)
#   make release-dry-run       # Preview without changes
#
# Manual workflow:
#   make bump-patch            # Bump version
#   make release-build         # Build package
#   make release-publish       # Publish to PyPI
#
# Test release on TestPyPI:
#   make release-build
#   make release-test-pypi
#
# Verify published release:
#   make release-verify
# ============================================================================
