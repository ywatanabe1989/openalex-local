#!/bin/bash
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-14"
# Author: ywatanabe (with Claude)
# File: scripts/utils/status.sh
# Description: Comprehensive status report for OpenAlex Local
#
# This is the reliable device for loading necessary information
# into administrator's short-term memory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DATA_DIR="${PROJECT_ROOT}/data"
SNAPSHOT_DIR="${DATA_DIR}/snapshot"
DB_PATH="${DATA_DIR}/openalex.db"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# Icons (simple ASCII)
CHECK="[OK]"
CROSS="[!!]"
WARN="[??]"
INFO="[--]"

divider() {
    echo -e "${DIM}────────────────────────────────────────────────────────────${NC}"
}

header() {
    echo ""
    echo -e "${BOLD}$1${NC}"
    divider
}

# ============================================================
# SYSTEM STATUS
# ============================================================
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║          OPENALEX LOCAL - STATUS REPORT                  ║${NC}"
echo -e "${BOLD}║          $(date '+%Y-%m-%d %H:%M:%S')                           ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"

# ============================================================
# PREREQUISITES
# ============================================================
header "PREREQUISITES"

# Python
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo -e "${GREEN}${CHECK}${NC} Python: $PY_VER"
else
    echo -e "${RED}${CROSS}${NC} Python: NOT FOUND"
fi

# AWS CLI
if command -v aws &>/dev/null; then
    AWS_VER=$(aws --version 2>&1 | cut -d' ' -f1 | cut -d'/' -f2)
    echo -e "${GREEN}${CHECK}${NC} AWS CLI: $AWS_VER"
else
    echo -e "${RED}${CROSS}${NC} AWS CLI: NOT INSTALLED"
    echo -e "         ${DIM}Install: pip install awscli${NC}"
fi

# Package
if pip show openalex-local &>/dev/null 2>&1; then
    PKG_VER=$(pip show openalex-local 2>/dev/null | grep Version | cut -d' ' -f2)
    echo -e "${GREEN}${CHECK}${NC} Package: openalex-local $PKG_VER"
else
    echo -e "${YELLOW}${WARN}${NC} Package: not installed (run: make install)"
fi

# ============================================================
# DISK SPACE
# ============================================================
header "DISK SPACE"

if [[ -d "$DATA_DIR" ]]; then
    DISK_INFO=$(df -h "$DATA_DIR" 2>/dev/null | tail -1)
    DISK_AVAIL=$(echo "$DISK_INFO" | awk '{print $4}')
    DISK_USED=$(echo "$DISK_INFO" | awk '{print $3}')
    DISK_PCT=$(echo "$DISK_INFO" | awk '{print $5}')
    echo -e "${INFO} Available: ${BOLD}$DISK_AVAIL${NC} (Used: $DISK_USED, $DISK_PCT)"

    # Check if enough space
    AVAIL_GB=$(df -BG "$DATA_DIR" 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G')
    if [[ "$AVAIL_GB" -lt 500 ]]; then
        echo -e "${YELLOW}${WARN}${NC} Low disk space! Recommend 500GB+ for full setup"
    fi
else
    echo -e "${YELLOW}${WARN}${NC} Data directory not found: $DATA_DIR"
fi

# ============================================================
# SNAPSHOT STATUS
# ============================================================
header "SNAPSHOT (data/snapshot/)"

if [[ -d "$SNAPSHOT_DIR/works" ]]; then
    # Count files
    GZ_COUNT=$(find "$SNAPSHOT_DIR/works" -name "*.gz" 2>/dev/null | wc -l)
    TOTAL_SIZE=$(du -sh "$SNAPSHOT_DIR/works" 2>/dev/null | cut -f1)

    if [[ "$GZ_COUNT" -gt 0 ]]; then
        echo -e "${GREEN}${CHECK}${NC} Works snapshot: ${BOLD}$GZ_COUNT files${NC} ($TOTAL_SIZE)"

        # Check manifest
        if [[ -f "$SNAPSHOT_DIR/works/manifest" ]]; then
            EXPECTED=$(grep -c "url" "$SNAPSHOT_DIR/works/manifest" 2>/dev/null || echo "?")
            echo -e "${INFO} Manifest: $EXPECTED files expected"

            if [[ "$GZ_COUNT" -lt "$EXPECTED" ]]; then
                REMAINING=$((EXPECTED - GZ_COUNT))
                PCT=$((GZ_COUNT * 100 / EXPECTED))

                # Calculate ETA from download log
                LOG_FILE="${PROJECT_ROOT}/logs/download.log"
                if [[ -f "$LOG_FILE" ]]; then
                    START_TIME=$(head -1 "$LOG_FILE" 2>/dev/null | grep -oP '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}' | head -1)
                    if [[ -n "$START_TIME" ]]; then
                        START_EPOCH=$(date -d "$START_TIME" +%s 2>/dev/null || echo "")
                        NOW_EPOCH=$(date +%s)
                        if [[ -n "$START_EPOCH" ]]; then
                            ELAPSED_SEC=$((NOW_EPOCH - START_EPOCH))
                            ELAPSED_HOURS=$((ELAPSED_SEC / 3600))
                            # Get size in GB
                            SIZE_GB=$(du -s "$SNAPSHOT_DIR/works" 2>/dev/null | awk '{print int($1/1024/1024)}')
                            if [[ "$SIZE_GB" -gt 0 ]] && [[ "$ELAPSED_HOURS" -gt 0 ]]; then
                                RATE=$((SIZE_GB / ELAPSED_HOURS))
                                if [[ "$RATE" -gt 0 ]]; then
                                    REMAINING_GB=$((300 - SIZE_GB))
                                    ETA_HOURS=$((REMAINING_GB / RATE))
                                    echo -e "${YELLOW}${WARN}${NC} Download incomplete: ${PCT}% ($TOTAL_SIZE / ~300GB)"
                                    echo -e "${INFO} Rate: ~${RATE} GB/hour, ETA: ~${ETA_HOURS} hours"
                                else
                                    echo -e "${YELLOW}${WARN}${NC} Download incomplete: ${PCT}% ($REMAINING files remaining)"
                                fi
                            else
                                echo -e "${YELLOW}${WARN}${NC} Download incomplete: ${PCT}% ($REMAINING files remaining)"
                            fi
                        else
                            echo -e "${YELLOW}${WARN}${NC} Download incomplete: ${PCT}% ($REMAINING files remaining)"
                        fi
                    else
                        echo -e "${YELLOW}${WARN}${NC} Download incomplete: ${PCT}% ($REMAINING files remaining)"
                    fi
                else
                    echo -e "${YELLOW}${WARN}${NC} Download incomplete: ${PCT}% ($REMAINING files remaining)"
                fi
            elif [[ "$GZ_COUNT" -ge "$EXPECTED" ]]; then
                echo -e "${GREEN}${CHECK}${NC} Download complete!"
                echo -e "${INFO} Next step: make build-db"
            fi
        fi
    else
        echo -e "${YELLOW}${WARN}${NC} No data files found"
        echo -e "         ${DIM}Run: make download${NC}"
    fi
elif [[ -f "$SNAPSHOT_DIR/works/manifest" ]]; then
    echo -e "${YELLOW}${WARN}${NC} Manifest only (no data files yet)"
    echo -e "         ${DIM}Run: make download${NC}"
else
    echo -e "${INFO} Not downloaded yet"
    echo -e "         ${DIM}Run: make download-manifest  # Check size first${NC}"
    echo -e "         ${DIM}Run: make download           # Download snapshot${NC}"
fi

# ============================================================
# DATABASE STATUS
# ============================================================
header "DATABASE (data/openalex.db)"

if [[ -f "$DB_PATH" ]]; then
    DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
    echo -e "${GREEN}${CHECK}${NC} Database: ${BOLD}$DB_SIZE${NC}"

    # Check tables if sqlite3 available
    if command -v sqlite3 &>/dev/null; then
        WORKS_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM works;" 2>/dev/null || echo "?")
        echo -e "${INFO} Works: $WORKS_COUNT rows"

        # Check FTS
        if sqlite3 "$DB_PATH" "SELECT 1 FROM sqlite_master WHERE name='works_fts';" 2>/dev/null | grep -q 1; then
            echo -e "${GREEN}${CHECK}${NC} FTS index: built"
        else
            echo -e "${YELLOW}${WARN}${NC} FTS index: not built (run: make build-fts)"
        fi
    fi
else
    echo -e "${INFO} Not built yet"
    echo -e "         ${DIM}Run: make build-db  # After downloading snapshot${NC}"
fi

# ============================================================
# QUICK COMMANDS
# ============================================================
header "QUICK COMMANDS"

echo -e "${DIM}make check${NC}             # Verify prerequisites"
echo -e "${DIM}make download-manifest${NC} # Check snapshot size (~300GB)"
echo -e "${DIM}make download${NC}          # Download snapshot (several hours)"
echo -e "${DIM}make build-db${NC}          # Build database (1-2 days)"
echo -e "${DIM}make build-fts${NC}         # Build search index (~hours)"
echo -e "${DIM}make status${NC}            # Show this report"

# ============================================================
# NOTIFICATIONS/WARNINGS
# ============================================================
# Collect warnings
WARNINGS=()

if ! command -v aws &>/dev/null; then
    WARNINGS+=("AWS CLI not installed - required for download")
fi

if [[ -d "$SNAPSHOT_DIR/works" ]]; then
    GZ_COUNT=$(find "$SNAPSHOT_DIR/works" -name "*.gz" 2>/dev/null | wc -l)
    if [[ -f "$SNAPSHOT_DIR/works/manifest" ]]; then
        EXPECTED=$(grep -c "url" "$SNAPSHOT_DIR/works/manifest" 2>/dev/null || echo "0")
        if [[ "$GZ_COUNT" -gt 0 ]] && [[ "$GZ_COUNT" -lt "$EXPECTED" ]]; then
            WARNINGS+=("Download incomplete - run 'make download' to resume")
        fi
    fi
fi

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    header "NOTIFICATIONS"
    for w in "${WARNINGS[@]}"; do
        echo -e "${YELLOW}!${NC} $w"
    done
fi

echo ""
