#!/bin/bash
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-26"
# Author: ywatanabe (with Claude)
# File: scripts/database/01_download_other_entities.sh
# Description: Download all OpenAlex entities EXCEPT works (which is handled separately)
#
# Usage:
#   screen -S download-others
#   ./scripts/database/01_download_other_entities.sh
#   # Ctrl-A D to detach

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DATA_DIR="${PROJECT_ROOT}/data/snapshot"
LOG_DIR="${PROJECT_ROOT}/logs"

OPENALEX_S3_BASE="s3://openalex/data"

# Entities to download (everything except works)
ENTITIES=(
    "authors"       # 59.2 GiB - largest
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

# Conservative bandwidth settings (can run alongside works download)
BANDWIDTH="${BANDWIDTH:-3MB/s}"
MAX_CONCURRENT=2

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

# Setup AWS config
setup_aws_config() {
    export AWS_CONFIG_FILE="${PROJECT_ROOT}/.aws_download_config_others"
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

    log "Starting download: ${entity}"
    mkdir -p "$local_dir"

    local start_time=$(date +%s)

    aws s3 sync \
        "$s3_path" \
        "$local_dir/" \
        --no-sign-request \
        2>&1 | while read -r line; do
            [[ -n "$line" ]] && echo "  $line"
        done

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local size=$(du -sh "$local_dir" 2>/dev/null | cut -f1)

    ok "${entity}: ${size} downloaded in ${duration}s"
}

# Main
main() {
    echo ""
    echo -e "${BOLD}========================================${NC}"
    echo -e "${BOLD}OpenAlex Other Entities Download${NC}"
    echo -e "${BOLD}========================================${NC}"
    echo "Entities: ${ENTITIES[*]}"
    echo "Bandwidth limit: $BANDWIDTH"
    echo "Note: Running parallel to works download"
    echo -e "${BOLD}========================================${NC}"
    echo ""

    mkdir -p "$DATA_DIR" "$LOG_DIR"
    setup_aws_config

    local total=${#ENTITIES[@]}
    local completed=0

    for entity in "${ENTITIES[@]}"; do
        ((completed++))
        log "Progress: ${completed}/${total} entities"
        download_entity "$entity"
        echo ""
    done

    echo ""
    log "========================================="
    ok "All entity downloads complete!"
    log "========================================="

    # Summary
    echo ""
    log "Downloaded sizes:"
    for entity in "${ENTITIES[@]}"; do
        local size=$(du -sh "${DATA_DIR}/${entity}" 2>/dev/null | cut -f1)
        echo "  ${entity}: ${size:-'N/A'}"
    done
}

# Handle interrupts gracefully
trap 'echo ""; warn "Interrupted. Run again to resume."; exit 1' INT TERM

main "$@"
