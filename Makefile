# OpenAlex Local Makefile
# ========================
# Thin dispatcher - delegates actual logic to scripts
#
# Quick reference (run 'make help' for full list):
#   make status   - Show system status (START HERE)
#   make check    - Verify prerequisites
#   make download - Download OpenAlex snapshot (~760GB)
#   make build    - Build database + FTS index

SHELL := /bin/bash
PROJECT_ROOT := $(shell pwd)
SCRIPTS := $(PROJECT_ROOT)/scripts
PYTHON := python3
DB_PATH := $(PROJECT_ROOT)/data/openalex.db
SNAPSHOT_DIR := $(PROJECT_ROOT)/data/snapshot/works

.PHONY: help status check install dev test \
        download download-works download-others download-stop \
        build build-db build-fts build-info \
        clean lint format db-info db-stats

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

# ============================================================
# DATABASE BUILD
# ============================================================
# Build order: download -> build-db -> build-fts
# Total build time: ~1-3 days depending on hardware

build: build-db build-fts ## Build database and FTS index (run after download)

build-db: ## Build SQLite database from snapshot (background)
	@echo "Starting database build..."
	@echo "This will take 12-48 hours depending on your hardware."
	@echo ""
	@mkdir -p $(PROJECT_ROOT)/logs
	@screen -dmS openalex-build-db bash -c '$(PYTHON) $(SCRIPTS)/database/02_build_database.py 2>&1 | tee $(PROJECT_ROOT)/logs/build_db.log'
	@echo "Build started in screen session: openalex-build-db"
	@echo ""
	@echo "Monitor:"
	@echo "  screen -r openalex-build-db  (attach to session)"
	@echo "  tail -f logs/build_db.log    (watch log)"
	@echo "  make db-info                 (check progress)"

build-db-fg: ## Build SQLite database (foreground, for debugging)
	$(PYTHON) $(SCRIPTS)/database/02_build_database.py

build-fts: ## Build FTS5 full-text search index (background)
	@echo "Starting FTS index build..."
	@echo "This will take 1-4 hours depending on database size."
	@echo ""
	@mkdir -p $(PROJECT_ROOT)/logs
	@screen -dmS openalex-build-fts bash -c '$(PYTHON) $(SCRIPTS)/database/03_build_fts_index.py 2>&1 | tee $(PROJECT_ROOT)/logs/build_fts.log'
	@echo "Build started in screen session: openalex-build-fts"
	@echo ""
	@echo "Monitor:"
	@echo "  screen -r openalex-build-fts  (attach to session)"
	@echo "  tail -f logs/build_fts.log    (watch log)"

build-fts-fg: ## Build FTS index (foreground, for debugging)
	$(PYTHON) $(SCRIPTS)/database/03_build_fts_index.py

build-stop: ## Stop all build processes
	@echo "Stopping build processes..."
	@screen -S openalex-build-db -X quit 2>/dev/null || true
	@screen -S openalex-build-fts -X quit 2>/dev/null || true
	@echo "Stopped. Builds are resumable - run 'make build-db' or 'make build-fts' to continue."

build-info: ## Show build instructions and estimated times
	@echo "╔══════════════════════════════════════════════════════════╗"
	@echo "║            DATABASE BUILD INSTRUCTIONS                   ║"
	@echo "╚══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Prerequisites:"
	@echo "  1. Download complete (make status shows all Complete)"
	@echo "  2. ~2TB free disk space"
	@echo "  3. Python 3.10+"
	@echo ""
	@echo "Build Steps:"
	@echo "┌─────────────────────────────────────────────────────────┐"
	@echo "│  Step 1: make build-db    (12-48 hours)                 │"
	@echo "│          Parse JSON → SQLite, create indices            │"
	@echo "├─────────────────────────────────────────────────────────┤"
	@echo "│  Step 2: make build-fts   (1-4 hours)                   │"
	@echo "│          Build FTS5 full-text search index              │"
	@echo "└─────────────────────────────────────────────────────────┘"
	@echo ""
	@echo "Or run both: make build"
	@echo ""
	@echo "Monitor Progress:"
	@echo "  make db-info      Show database stats"
	@echo "  make db-stats     Show detailed row counts"
	@echo "  screen -ls        List active build sessions"

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
	@if [ -f $(DB_PATH) ]; then \
		echo "Database: $(DB_PATH)"; \
		echo "Size: $$(du -h $(DB_PATH) | cut -f1)"; \
		echo ""; \
		echo "Tables:"; \
		sqlite3 $(DB_PATH) ".tables"; \
		echo ""; \
		echo "Works count:"; \
		sqlite3 $(DB_PATH) "SELECT COUNT(*) FROM works;" 2>/dev/null || echo "  (table not ready)"; \
		echo ""; \
		echo "FTS count:"; \
		sqlite3 $(DB_PATH) "SELECT COUNT(*) FROM works_fts;" 2>/dev/null || echo "  (not built yet)"; \
		echo ""; \
		echo "Build progress:"; \
		sqlite3 $(DB_PATH) "SELECT COUNT(*) as files_processed FROM _build_progress;" 2>/dev/null || echo "  (not started)"; \
	else \
		echo "Database not found: $(DB_PATH)"; \
		echo "Run: make build-db"; \
	fi

db-stats: ## Show detailed database statistics
	@if [ -f $(DB_PATH) ]; then \
		echo "╔══════════════════════════════════════════════════════════╗"; \
		echo "║            DATABASE STATISTICS                           ║"; \
		echo "╚══════════════════════════════════════════════════════════╝"; \
		echo ""; \
		echo "File: $(DB_PATH)"; \
		echo "Size: $$(du -h $(DB_PATH) | cut -f1)"; \
		echo ""; \
		echo "Row Counts:"; \
		echo "─────────────────────────────────────────"; \
		sqlite3 $(DB_PATH) "SELECT 'works' as tbl, COUNT(*) as cnt FROM works UNION ALL SELECT 'works_fts', COUNT(*) FROM works_fts UNION ALL SELECT '_build_progress', COUNT(*) FROM _build_progress;" 2>/dev/null || echo "  (tables not ready)"; \
		echo ""; \
		echo "Metadata:"; \
		echo "─────────────────────────────────────────"; \
		sqlite3 $(DB_PATH) "SELECT key, value FROM _metadata;" 2>/dev/null || echo "  (no metadata)"; \
		echo ""; \
		echo "Sample search test:"; \
		sqlite3 $(DB_PATH) "SELECT COUNT(*) as matches FROM works_fts WHERE works_fts MATCH 'machine learning';" 2>/dev/null || echo "  (FTS not ready)"; \
	else \
		echo "Database not found. Run: make build-db"; \
	fi

db-search: ## Test search (usage: make db-search Q="your query")
	@if [ -f $(DB_PATH) ]; then \
		sqlite3 $(DB_PATH) "SELECT w.openalex_id, w.year, substr(w.title, 1, 60) FROM works_fts f JOIN works w ON f.rowid = w.id WHERE works_fts MATCH '$(Q)' LIMIT 10;"; \
	else \
		echo "Database not found. Run: make build-db"; \
	fi
