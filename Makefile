# OpenAlex Local Makefile

SHELL := /bin/bash
PYTHON := python3
PROJECT_ROOT := $(shell pwd)
SCRIPTS := $(PROJECT_ROOT)/scripts

.PHONY: help install dev test download build-db status clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install package
	pip install -e .

dev: ## Install with dev dependencies
	pip install -e ".[dev]"

test: ## Run tests
	pytest tests/ -v

# Database building
download-manifest: ## Download manifest to check snapshot size
	$(PYTHON) $(SCRIPTS)/database/01_download_snapshot.py --manifest-only

download: ## Download OpenAlex works snapshot (~300GB)
	$(PYTHON) $(SCRIPTS)/database/01_download_snapshot.py

build-db: ## Build SQLite database from snapshot
	$(PYTHON) $(SCRIPTS)/database/02_build_database.py

build-fts: ## Build FTS5 full-text search index
	$(PYTHON) $(SCRIPTS)/database/03_build_fts_index.py

status: ## Show database status
	@echo "Database Status"
	@echo "==============="
	@ls -lh data/*.db 2>/dev/null || echo "No database found"
	@ls -lh data/snapshot/works/*.gz 2>/dev/null | wc -l | xargs -I{} echo "Snapshot files: {}"

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Development
lint: ## Run linter
	ruff check src/ tests/

format: ## Format code
	ruff format src/ tests/
