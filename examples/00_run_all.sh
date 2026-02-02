#!/bin/bash
# -*- coding: utf-8 -*-
# Timestamp: "2026-02-03 (ywatanabe)"
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
    echo "  01_basic_search.py       Basic full-text search"
    echo "  02_get_by_doi.py         Retrieve work by DOI"
    echo "  03_citations.py          APA and BibTeX citations"
    echo "  04_cache_workflow.py     Local caching workflow"
    echo "  05_async_search.py       Async concurrent search"
    echo "  06_enrich_workflow.py    Enriching search results"
    echo ""
    echo "Output:"
    echo "  Each script creates its own log in script_out/"
    echo "  This runner logs to: $LOG_FILE"
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Initialize log
echo "=== OpenAlex Local Examples Runner ===" > "$LOG_FILE"
echo "Started: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

log "========================================"
log "OpenAlex Local Examples Runner"
log "========================================"
log ""

# Run all numbered Python scripts
SCRIPTS=(01_*.py 02_*.py 03_*.py 04_*.py 05_*.py 06_*.py)
COUNT=0
TOTAL=0

for pattern in "${SCRIPTS[@]}"; do
    for script in $pattern; do
        if [[ -f "$script" ]]; then
            TOTAL=$((TOTAL + 1))
        fi
    done
done

for pattern in "${SCRIPTS[@]}"; do
    for script in $pattern; do
        if [[ -f "$script" ]]; then
            COUNT=$((COUNT + 1))
            log "[$COUNT/$TOTAL] Running $script..."
            if python "$script" 2>&1 | tee -a "$LOG_FILE"; then
                log "Done: $script"
            else
                log "WARNING: $script had errors"
            fi
            log ""
        fi
    done
done

log "========================================"
log "All examples completed!"
log "========================================"
log ""
log "Check individual outputs in:"
log "  - script_out/FINISHED_*/  (per-script logs)"
log "  - $LOG_FILE (this runner log)"
log ""
log "Finished: $(date)"
