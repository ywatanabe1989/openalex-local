#!/bin/bash
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-26"
# Author: ywatanabe (with Claude)
# File: scripts/database/00_download_all_entities.sh
# Description: Download ALL OpenAlex entities with safe bandwidth limits
#
# This is the unified script for downloading the complete OpenAlex snapshot.
# Uses aws s3 sync which automatically skips already-downloaded files.
#
# Usage:
#   screen -S openalex-download
#   ./scripts/database/00_download_all_entities.sh
#   # Ctrl-A D to detach
#
# Entity sizes (approximate):
#   works:        698 GiB  (largest - downloaded first)
#   authors:       59 GiB
#   institutions: 164 MiB
#   sources:      125 MiB
#   funders:      7.6 MiB
#   concepts:     6.1 MiB
#   topics:       4.9 MiB
#   publishers:   1.7 MiB
#   subfields:    315 KiB
#   fields:       7.7 KiB
#   domains:      1.4 KiB

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DATA_DIR="${PROJECT_ROOT}/data/snapshot"
LOG_DIR="${PROJECT_ROOT}/logs"

OPENALEX_S3_BASE="s3://openalex/data"

# All entity types (ordered by size - largest first)
ENTITIES=(
    "works"         # 698 GiB
    "authors"       # 59 GiB
    "institutions"  # 164 MiB
    "sources"       # 125 MiB
    "funders"       # 7.6 MiB
    "concepts"      # 6.1 MiB
    "topics"        # 4.9 MiB
    "publishers"    # 1.7 MiB
    "subfields"     # 315 KiB
    "fields"        # 7.7 KiB
    "domains"       # 1.4 KiB
)

# SAFE SETTINGS - conservative bandwidth
BANDWIDTH="${BANDWIDTH:-5MB/s}"
MAX_CONCURRENT="${MAX_CONCURRENT:-2}"
DELAY_BETWEEN_ENTITIES=5

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

# Setup AWS config with bandwidth limits
setup_aws_config() {
    export AWS_CONFIG_FILE="${PROJECT_ROOT}/.aws_download_config"
    cat > "$AWS_CONFIG_FILE" << EOF
[default]
s3 =
    max_bandwidth = $BANDWIDTH
    max_concurrent_requests = $MAX_CONCURRENT
    multipart_threshold = 100MB
    multipart_chunksize = 50MB
EOF
    log "AWS config: bandwidth=$BANDWIDTH, concurrent=$MAX_CONCURRENT"
}

# Download single entity type
download_entity() {
    local entity="$1"
    local local_dir="${DATA_DIR}/${entity}"
    local s3_path="${OPENALEX_S3_BASE}/${entity}/"

    log "========================================="
    log "Starting: ${entity}"
    log "========================================="
    mkdir -p "$local_dir"

    local start_time=$(date +%s)
    local start_size=$(du -sb "$local_dir" 2>/dev/null | cut -f1 || echo 0)

    aws s3 sync \
        "$s3_path" \
        "$local_dir/" \
        --no-sign-request \
        2>&1 | while read -r line; do
            # Show download progress
            if [[ "$line" == *"download:"* ]] || [[ "$line" == *"Completed"* ]]; then
                echo "  $line"
            fi
        done

    local end_time=$(date +%s)
    local end_size=$(du -sb "$local_dir" 2>/dev/null | cut -f1 || echo 0)
    local duration=$((end_time - start_time))
    local downloaded=$((end_size - start_size))
    local downloaded_hr=$(numfmt --to=iec-i --suffix=B $downloaded 2>/dev/null || echo "${downloaded} bytes")
    local total_hr=$(du -sh "$local_dir" 2>/dev/null | cut -f1)

    ok "${entity}: ${total_hr} total (${downloaded_hr} new) in ${duration}s"
}

# Show status summary
show_status() {
    echo ""
    log "Current download status:"
    echo "----------------------------------------"
    for entity in "${ENTITIES[@]}"; do
        local dir="${DATA_DIR}/${entity}"
        if [[ -d "$dir" ]]; then
            local size=$(du -sh "$dir" 2>/dev/null | cut -f1)
            local files=$(find "$dir" -name "*.gz" 2>/dev/null | wc -l)
            printf "  %-15s %8s  (%d files)\n" "$entity:" "$size" "$files"
        else
            printf "  %-15s %8s\n" "$entity:" "not started"
        fi
    done
    echo "----------------------------------------"
}

# Main
main() {
    echo ""
    echo -e "${BOLD}========================================${NC}"
    echo -e "${BOLD}OpenAlex Complete Snapshot Download${NC}"
    echo -e "${BOLD}========================================${NC}"
    echo "Entities: ${#ENTITIES[@]} types"
    echo "Bandwidth limit: $BANDWIDTH"
    echo "Concurrent requests: $MAX_CONCURRENT"
    echo -e "${BOLD}========================================${NC}"
    echo ""

    mkdir -p "$DATA_DIR" "$LOG_DIR"
    setup_aws_config

    show_status

    local total=${#ENTITIES[@]}
    local completed=0

    for entity in "${ENTITIES[@]}"; do
        ((completed++))
        echo ""
        log "Entity ${completed}/${total}: ${entity}"
        download_entity "$entity"
        sleep "$DELAY_BETWEEN_ENTITIES"
    done

    echo ""
    echo -e "${BOLD}========================================${NC}"
    ok "ALL DOWNLOADS COMPLETE!"
    echo -e "${BOLD}========================================${NC}"
    show_status
}

# Handle interrupts gracefully
trap 'echo ""; warn "Interrupted. Run again to resume."; exit 1' INT TERM

main "$@"
