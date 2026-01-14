# OpenAlex Local Makefile
# ========================
# Thin dispatcher - delegates actual logic to scripts
#
# Quick reference (run 'make help' for full list):
#   make status   - Show system status (START HERE)
#   make check    - Verify prerequisites
#   make download - Download OpenAlex snapshot (~300GB)

SHELL := /bin/bash
PROJECT_ROOT := $(shell pwd)
SCRIPTS := $(PROJECT_ROOT)/scripts

.PHONY: help status check install dev test \
        download download-manifest download-screen \
        build-db build-fts \
        clean lint format

# ============================================================
# HELP & STATUS
# ============================================================

help: ## Show this help
	@echo "OpenAlex Local - Available Commands"
	@echo "===================================="
	@echo ""
	@echo "Start here:"
	@echo "  make status   Show current system status"
	@echo "  make check    Verify prerequisites are installed"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

status: ## Show comprehensive status report
	@$(SCRIPTS)/utils/status.sh

# ============================================================
# SETUP
# ============================================================

check: ## Verify all prerequisites are installed
	@$(SCRIPTS)/setup/check_prerequisites.sh

install: ## Install openalex-local package
	pip install -e .

dev: ## Install with dev dependencies
	pip install -e ".[dev]"

# ============================================================
# DATABASE BUILDING
# ============================================================

download-manifest: ## Download manifest to check snapshot size
	@$(SCRIPTS)/database/00_download_all.sh manifest

download: ## Download OpenAlex works snapshot (~300GB)
	@$(SCRIPTS)/database/00_download_all.sh works

download-screen: ## Download in detached screen session (recommended)
	@echo "Starting download in screen session 'openalex-download'..."
	@screen -dmS openalex-download $(SCRIPTS)/database/00_download_all.sh works -y
	@echo "Detached. To attach: screen -r openalex-download"
	@echo "To check progress: make status"

build-db: ## Build SQLite database from snapshot
	@echo "TODO: Implement build script"
	@echo "Run: python $(SCRIPTS)/database/02_build_database.py"

build-fts: ## Build FTS5 full-text search index
	@echo "TODO: Implement FTS build script"
	@echo "Run: python $(SCRIPTS)/database/03_build_fts_index.py"

# ============================================================
# DEVELOPMENT
# ============================================================

test: ## Run tests
	pytest tests/ -v

lint: ## Run linter
	ruff check src/ tests/

format: ## Format code
	ruff format src/ tests/

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# ============================================================
# DATABASE INFO
# ============================================================

db-info: ## Show database schema and stats
	@if [ -f data/openalex.db ]; then \
		echo "Database: data/openalex.db"; \
		echo "Size: $$(du -h data/openalex.db | cut -f1)"; \
		echo ""; \
		echo "Tables:"; \
		sqlite3 data/openalex.db ".tables"; \
	else \
		echo "Database not found. Run: make build-db"; \
	fi
