#!/bin/bash
# -*- coding: utf-8 -*-
# Timestamp: "2026-02-06 (ywatanabe)"
# File: /home/ywatanabe/proj/openalex-local/examples/00_run_all.sh

# Run all openalex-local examples in sequence.
# Usage: ./00_run_all.sh [--help]

set -e

LOG_FILE="./00_run_all.log"

show_help() {
    echo "Usage: ./00_run_all.sh [OPTIONS]"
    echo ""
    echo "Run all openalex-local examples in sequence."
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Examples run:"
    echo "  01_quickstart.py       Basic quickstart demo"
    echo "  02_basic_search.py     Search functionality"
    echo "  03_get_by_doi.py       DOI lookup"
    echo "  04_citations.py        Citation handling"
    echo "  05_cache_workflow.py   Cache workflow"
    echo "  06_async_search.py     Async search"
    echo "  07_enrich_workflow.py  Enrichment workflow"
    echo "  08_cli_demo.sh         CLI demonstration"
    echo "  09_plot_if_vs_jcr.py   IF validation plot"
    echo ""
    echo "Output:"
    echo "  Each script creates its own log in *_out/"
    echo "  This runner logs to: $LOG_FILE"
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_help
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Initialize log
echo "=== OpenAlex Local Examples Runner ===" >"$LOG_FILE"
echo "Started: $(date)" >>"$LOG_FILE"
echo "" >>"$LOG_FILE"

log "========================================"
log "OpenAlex Local Examples Runner"
log "========================================"
log ""

# Find all numbered scripts (01-09)
SCRIPTS=$(ls -1 0[1-9]_*.py 0[1-9]_*.sh 2>/dev/null | sort)
TOTAL=$(echo "$SCRIPTS" | wc -l)
COUNT=0

for script in $SCRIPTS; do
    if [[ -f "$script" ]]; then
        COUNT=$((COUNT + 1))
        log "[$COUNT/$TOTAL] Running $script..."
        if [[ "$script" == *.py ]]; then
            if python "$script" 2>&1 | tee -a "$LOG_FILE"; then
                log "Done: $script"
            else
                log "WARNING: $script had errors"
            fi
        elif [[ "$script" == *.sh ]]; then
            if bash "$script" 2>&1 | tee -a "$LOG_FILE"; then
                log "Done: $script"
            else
                log "WARNING: $script had errors"
            fi
        fi
        log ""
    fi
done

log "========================================"
log "All examples completed!"
log "========================================"
log ""
log "Check individual outputs in:"
log "  - *_out/ directories"
log "  - $LOG_FILE (this runner log)"
log ""
log "Finished: $(date)"
