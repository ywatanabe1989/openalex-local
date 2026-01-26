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
        download download-works download-others download-stop \
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
# DATABASE DOWNLOAD
# ============================================================
# Full snapshot: ~760GB (works: 698GB, authors: 59GB, others: ~3GB)
# Downloads are resumable - safe to interrupt and restart

download: ## Download ALL entities in background (recommended)
	@echo "Starting full OpenAlex download (~760GB)..."
	@echo "Works (698GB) and other entities (60GB) will download in parallel."
	@mkdir -p $(PROJECT_ROOT)/logs
	@screen -dmS openalex-download bash -c '$(SCRIPTS)/database/00_download_safe.sh 2>&1 | tee $(PROJECT_ROOT)/logs/download_safe_run.log'
	@screen -dmS openalex-others bash -c '$(SCRIPTS)/database/01_download_other_entities.sh 2>&1 | tee $(PROJECT_ROOT)/logs/download_others.log'
	@echo ""
	@echo "Downloads started in background:"
	@echo "  - openalex-download: works (698GB)"
	@echo "  - openalex-others: authors + 9 others (60GB)"
	@echo ""
	@echo "Monitor: make status"
	@echo "Attach:  screen -r openalex-download"
	@echo "Logs:    tail -f logs/download_safe_run.log"

download-works: ## Download works only (698GB)
	@echo "Starting works download (698GB)..."
	@mkdir -p $(PROJECT_ROOT)/logs
	@screen -dmS openalex-download bash -c '$(SCRIPTS)/database/00_download_safe.sh 2>&1 | tee $(PROJECT_ROOT)/logs/download_safe_run.log'
	@echo "Started in screen session: openalex-download"
	@echo "Monitor: make status"

download-others: ## Download authors + other entities (60GB)
	@echo "Starting download of authors + other entities (60GB)..."
	@mkdir -p $(PROJECT_ROOT)/logs
	@screen -dmS openalex-others bash -c '$(SCRIPTS)/database/01_download_other_entities.sh 2>&1 | tee $(PROJECT_ROOT)/logs/download_others.log'
	@echo "Started in screen session: openalex-others"
	@echo "Monitor: make status"

download-stop: ## Stop all active downloads
	@echo "Stopping downloads (safe to resume later)..."
	@screen -S openalex-download -X quit 2>/dev/null || true
	@screen -S openalex-others -X quit 2>/dev/null || true
	@echo "Stopped. Run 'make download' to resume."

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
