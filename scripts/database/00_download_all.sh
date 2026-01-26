#!/bin/bash
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-14"
# Author: ywatanabe (with Claude)
# File: scripts/database/00_download_all.sh
# Description: Master download orchestration script for OpenAlex snapshot
#
# Downloads OpenAlex Works snapshot from AWS S3 (~200-300GB).
# Supports resume - just run again if interrupted.
#
# TIMELINE (approximate):
#   Download: 2-8 hours (depends on connection speed)
#
# REQUIREMENTS:
#   - AWS CLI installed (pip install awscli)
#   - 500GB+ disk space recommended

set -euo pipefail

# Ensure PATH includes common binary locations
export PATH="$HOME/local/bin:$HOME/.local/bin:/usr/local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DATA_DIR="${PROJECT_ROOT}/data"
SNAPSHOT_DIR="${DATA_DIR}/snapshot"
WORKS_DIR="${SNAPSHOT_DIR}/works"
LOG_DIR="${PROJECT_ROOT}/logs"

OPENALEX_S3_BASE="s3://openalex/data"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log() { echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*"; }
ok() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] [COMMAND]

Download OpenAlex snapshot from AWS S3.

COMMANDS:
    all         Download everything (default)
    manifest    Download manifest only (to check size)
    works       Download works snapshot (~200-300GB)
    resume      Resume interrupted download

OPTIONS:
    -y, --yes       Skip confirmation prompt
    -n, --dry-run   Show what would be done
    -b, --bandwidth LIMIT  Limit bandwidth (e.g., 50MB/s, 10MB/s). Default: unlimited
    -h, --help      Show this help

EXAMPLES:
    # Check size first
    $(basename "$0") manifest

    # Full download (in screen session recommended)
    screen -S download
    $(basename "$0") all
    # Ctrl-A D to detach

    # Download with bandwidth limit (50 MB/s)
    $(basename "$0") works --bandwidth 50MB/s

    # Low-impact background download (10 MB/s)
    $(basename "$0") works -y -b 10MB/s

    # Resume interrupted download
    $(basename "$0") resume
EOF
}

check_prerequisites() {
    log "Checking prerequisites..."

    # Check AWS CLI
    if ! command -v aws &>/dev/null; then
        error "AWS CLI not installed"
        echo ""
        echo "Install with: pip install awscli"
        echo "Or run: make check"
        exit 1
    fi

    # Check disk space
    mkdir -p "$DATA_DIR"
    AVAILABLE_GB=$(df -BG "$DATA_DIR" 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G')
    if [[ "$AVAILABLE_GB" -lt 350 ]]; then
        warn "Low disk space: ${AVAILABLE_GB}GB available"
        echo "    Snapshot requires ~200-300GB"
        if [[ "${FORCE:-}" != "1" ]]; then
            read -p "Continue anyway? [y/N] " response
            [[ "$response" != "y" ]] && exit 1
        fi
    else
        ok "Disk space: ${AVAILABLE_GB}GB available"
    fi

    # Test S3 connectivity (simple check - full test happens during download)
    log "Testing S3 connectivity..."
    if aws s3 ls "s3://openalex/" --no-sign-request 2>&1 | head -1 | grep -qE "(PRE|data)"; then
        ok "S3 connection OK"
    else
        warn "S3 connectivity check inconclusive - proceeding with download"
    fi

    ok "Prerequisites satisfied"
}

download_manifest() {
    log "Downloading manifest..."
    mkdir -p "$WORKS_DIR"

    aws s3 cp "${OPENALEX_S3_BASE}/works/manifest" "$WORKS_DIR/manifest" --no-sign-request

    if [[ -f "$WORKS_DIR/manifest" ]]; then
        ok "Manifest saved to: $WORKS_DIR/manifest"

        # Parse manifest for info
        FILE_COUNT=$(grep -c '"url"' "$WORKS_DIR/manifest" 2>/dev/null || echo "?")
        echo ""
        echo "Manifest summary:"
        echo "  Files to download: $FILE_COUNT"
        echo "  Estimated size: ~200-300GB compressed"
        echo ""
        echo "To download all files, run:"
        echo "  make download"
        echo "  # or: $0 works"
    fi
}

download_works() {
    log "Starting works snapshot download..."
    mkdir -p "$WORKS_DIR" "$LOG_DIR"

    # Show current status
    EXISTING=$(find "$WORKS_DIR" -name "*.gz" 2>/dev/null | wc -l)
    if [[ "$EXISTING" -gt 0 ]]; then
        log "Found $EXISTING existing files (will resume)"
    fi

    echo ""
    echo -e "${BOLD}========================================${NC}"
    echo -e "${BOLD}OpenAlex Works Snapshot Download${NC}"
    echo -e "${BOLD}========================================${NC}"
    echo "Source: ${OPENALEX_S3_BASE}/works/"
    echo "Target: ${WORKS_DIR}/"
    echo "Estimated: ~200-300GB compressed"
    if [[ -n "$BANDWIDTH" ]]; then
        echo -e "Bandwidth: ${GREEN}${BANDWIDTH}${NC} (limited)"
    else
        echo -e "Bandwidth: ${YELLOW}Unlimited${NC}"
    fi
    echo "Note: Download is resumable. Run again if interrupted."
    echo -e "${BOLD}========================================${NC}"
    echo ""

    if [[ "${YES:-}" != "1" ]]; then
        read -p "Start download? [y/N] " response
        if [[ "$response" != "y" ]]; then
            echo "Aborted."
            exit 0
        fi
    fi

    log "Downloading... (this will take several hours)"
    log "Log: $LOG_DIR/download_works.log"

    # Build AWS CLI options
    AWS_OPTS=(
        "--no-sign-request"
        "--only-show-errors"
    )

    # Apply bandwidth limit if specified
    if [[ -n "$BANDWIDTH" ]]; then
        log "Bandwidth limit: $BANDWIDTH"
        # Set AWS CLI max_bandwidth via config
        export AWS_CONFIG_FILE="${PROJECT_ROOT}/.aws_download_config"
        mkdir -p "$(dirname "$AWS_CONFIG_FILE")"
        cat > "$AWS_CONFIG_FILE" << EOF
[default]
s3 =
    max_bandwidth = $BANDWIDTH
    max_concurrent_requests = 2
EOF
    fi

    # Use aws s3 sync for resumable download
    aws s3 sync \
        "${OPENALEX_S3_BASE}/works/" \
        "$WORKS_DIR/" \
        "${AWS_OPTS[@]}" \
        2>&1 | tee "$LOG_DIR/download_works.log"

    # Verify
    FINAL_COUNT=$(find "$WORKS_DIR" -name "*.gz" 2>/dev/null | wc -l)
    TOTAL_SIZE=$(du -sh "$WORKS_DIR" 2>/dev/null | cut -f1)

    echo ""
    log "========================================="
    ok "Download complete!"
    log "Files: $FINAL_COUNT"
    log "Size: $TOTAL_SIZE"
    log "Location: $WORKS_DIR/"
    log "========================================="
    echo ""
    echo "Next step: make build-db"
}

show_status() {
    echo ""
    echo -e "${BOLD}Download Status${NC}"
    echo "────────────────────────────────────────"

    if [[ -d "$WORKS_DIR" ]]; then
        GZ_COUNT=$(find "$WORKS_DIR" -name "*.gz" 2>/dev/null | wc -l)
        TOTAL_SIZE=$(du -sh "$WORKS_DIR" 2>/dev/null | cut -f1 || echo "0")

        echo "Location: $WORKS_DIR"
        echo "Files: $GZ_COUNT"
        echo "Size: $TOTAL_SIZE"

        if [[ -f "$WORKS_DIR/manifest" ]]; then
            EXPECTED=$(grep -c '"url"' "$WORKS_DIR/manifest" 2>/dev/null || echo "?")
            echo "Expected: $EXPECTED files"

            if [[ "$GZ_COUNT" -lt "$EXPECTED" ]]; then
                REMAINING=$((EXPECTED - GZ_COUNT))
                echo -e "${YELLOW}Status: INCOMPLETE ($REMAINING files remaining)${NC}"
            else
                echo -e "${GREEN}Status: COMPLETE${NC}"
            fi
        fi
    else
        echo "Status: NOT STARTED"
        echo "Run: make download"
    fi
    echo ""
}

# Parse arguments
DRY_RUN=0
YES=0
BANDWIDTH=""
COMMAND="all"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--dry-run) DRY_RUN=1; shift ;;
        -y|--yes) YES=1; shift ;;
        -b|--bandwidth) BANDWIDTH="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        all|manifest|works|resume|status) COMMAND="$1"; shift ;;
        *) error "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# Main
case "$COMMAND" in
    all|works|resume)
        if [[ "$DRY_RUN" == "1" ]]; then
            warn "DRY RUN - no changes will be made"
            check_prerequisites
            show_status
            exit 0
        fi
        check_prerequisites
        download_works
        ;;
    manifest)
        check_prerequisites
        download_manifest
        ;;
    status)
        show_status
        ;;
esac
