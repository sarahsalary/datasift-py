# =============================================================================
# datasift-py — development Makefile
# =============================================================================
# Run `make` or `make help` to see all available targets.
# =============================================================================

PYTHON      ?= python3
PIP         ?= $(PYTHON) -m pip
PYTEST      ?= $(PYTHON) -m pytest
RUFF        ?= $(PYTHON) -m ruff
MYPY        ?= $(PYTHON) -m mypy
MKDOCS      ?= $(PYTHON) -m mkdocs
BUILD       ?= $(PYTHON) -m build
TWINE       ?= $(PYTHON) -m twine

BENCH_DIR   ?= /tmp/datasift-bench
BENCH_ROWS  ?= 1000000

SRC_DIR     := src/datasift
TEST_DIR    := tests
DIST_DIR    := dist

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "datasift-py targets:\n\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Setup
.PHONY: install install-dev install-all bootstrap
install: ## Install in editable mode
	$(PIP) install -e .

install-dev: ## Install with dev dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

install-all: ## Install with all optional dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[all]"

bootstrap: install-all ## First-time setup
	@echo "✓ Environment ready."

##@ Testing
.PHONY: test test-fast test-cov
test: ## Run the test suite
	$(PYTEST)

test-fast: ## Run tests, stop on first failure
	$(PYTEST) -x

test-cov: ## Run tests with coverage
	$(PYTEST) --cov=datasift --cov-report=term-missing --cov-report=html

##@ Code quality
.PHONY: lint format typecheck check
lint: ## Run ruff
	$(RUFF) check $(SRC_DIR) $(TEST_DIR) scripts benchmarks

format: ## Format code with ruff
	$(RUFF) format $(SRC_DIR) $(TEST_DIR) scripts benchmarks

typecheck: ## Run mypy
	$(MYPY) $(SRC_DIR)

check: lint typecheck test ## Run all checks

##@ Benchmarks
.PHONY: bench-generate bench bench-quick
bench-generate: ## Generate benchmark data
	$(PYTHON) -m benchmarks.generate_data --rows $(BENCH_ROWS) --out $(BENCH_DIR)

bench: ## Run full benchmark
	$(PYTHON) -m benchmarks.bench_data_vs_stream --data-dir $(BENCH_DIR) --rows $(BENCH_ROWS)

bench-quick: ## Quick benchmark (100k rows)
	$(PYTHON) -m benchmarks.generate_data --rows 100000 --out $(BENCH_DIR)
	$(PYTHON) -m benchmarks.bench_data_vs_stream --data-dir $(BENCH_DIR) --rows 100000

##@ Documentation
.PHONY: docs docs-build
docs: ## Serve docs locally
	$(MKDOCS) serve

docs-build: ## Build docs (strict)
	$(MKDOCS) build --strict

##@ Build & Release
.PHONY: build build-check release-patch release-minor release-major
build: ## Build wheel and sdist
	$(BUILD)

build-check: build ## Build and validate with twine
	$(TWINE) check $(DIST_DIR)/*

release-patch: ## Release a patch version
	$(PYTHON) scripts/release.py patch

release-minor: ## Release a minor version
	$(PYTHON) scripts/release.py minor

release-major: ## Release a major version
	$(PYTHON) scripts/release.py major

##@ Cleanup
.PHONY: clean clean-all
clean: ## Remove caches and build artifacts
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf htmlcov/ .coverage coverage.xml build/ dist/ site/
	@echo "✓ Cleaned."

clean-all: clean ## Remove everything
	@rm -rf $(BENCH_DIR)