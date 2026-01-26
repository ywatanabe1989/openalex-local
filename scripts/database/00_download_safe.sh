#!/bin/bash
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-25"
# Author: ywatanabe (with Claude)
# File: scripts/database/00_download_safe.sh
# Description: SAFE download script - sequential, bandwidth-limited, resumable
#
# This script downloads ONE directory at a time with strict bandwidth limits
# to avoid overwhelming the network. Uses aws s3 sync which automatically
# skips already-downloaded files.
#
# Usage:
#   screen -S download
#   ./scripts/database/00_download_safe.sh
#   # Ctrl-A D to detach

set -uo pipefail
# Note: -e removed to allow functions to return non-zero for flow control

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DATA_DIR="${PROJECT_ROOT}/data"
WORKS_DIR="${DATA_DIR}/snapshot/works"
LOG_DIR="${PROJECT_ROOT}/logs"

OPENALEX_S3_BASE="s3://openalex/data/works"

# SAFE SETTINGS - very conservative
BANDWIDTH="${BANDWIDTH:-5MB/s}"      # 5 MB/s max (40 Mbps, 4% of 1Gbps)
MAX_CONCURRENT=1                      # Single connection only
DELAY_BETWEEN_DIRS=1                  # Seconds between directories

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

# Setup AWS config with strict limits
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

# Download single directory (sync skips existing files automatically)
download_dir() {
    local date_dir="$1"
    local local_dir="${WORKS_DIR}/${date_dir}"

    mkdir -p "$local_dir"

    # Capture sync output to check if anything was downloaded
    local output
    output=$(aws s3 sync \
        "${OPENALEX_S3_BASE}/${date_dir}/" \
        "$local_dir/" \
        --no-sign-request \
        2>&1) || true

    if [[ -n "$output" ]]; then
        # Something was downloaded
        local count=$(find "$local_dir" -name "*.gz" 2>/dev/null | wc -l)
        ok "${date_dir}: ${count} files"
        return 0  # Downloaded
    else
        return 1  # Already complete (nothing to sync)
    fi
}

# Main
main() {
    echo ""
    echo -e "${BOLD}========================================${NC}"
    echo -e "${BOLD}OpenAlex SAFE Download${NC}"
    echo -e "${BOLD}========================================${NC}"
    echo "Bandwidth limit: $BANDWIDTH"
    echo "Concurrent connections: $MAX_CONCURRENT"
    echo "Mode: Sequential (one directory at a time)"
    echo -e "${BOLD}========================================${NC}"
    echo ""

    mkdir -p "$WORKS_DIR" "$LOG_DIR"
    setup_aws_config

    log "Fetching directory list from S3..."
    local dirs
    dirs=$(aws s3 ls "${OPENALEX_S3_BASE}/" --no-sign-request 2>/dev/null | awk '{print $2}' | tr -d '/')
    local total=$(echo "$dirs" | wc -l)
    log "Found $total date directories"

    local completed=0
    local skipped=0
    local downloaded=0

    while IFS= read -r date_dir; do
        [[ -z "$date_dir" ]] && continue
        ((completed++))

        # Show progress every 10 directories
        if ((completed % 10 == 0)); then
            local pct=$((completed * 100 / total))
            log "Progress: ${completed}/${total} (${pct}%) [downloaded: $downloaded, skipped: $skipped]"
        fi

        download_dir "$date_dir" && {
            ((downloaded++))
            sleep "$DELAY_BETWEEN_DIRS"
        } || {
            ((skipped++))
        }
    done <<< "$dirs"

    echo ""
    log "========================================="
    ok "Download complete!"
    log "Total directories: $total"
    log "Downloaded: $downloaded"
    log "Skipped (already complete): $skipped"
    log "========================================="

    # Final verification
    local total_files=$(find "$WORKS_DIR" -name "*.gz" 2>/dev/null | wc -l)
    local total_size=$(du -sh "$WORKS_DIR" 2>/dev/null | cut -f1)
    log "Total files: $total_files"
    log "Total size: $total_size"
}

# Handle interrupts gracefully
trap 'echo ""; warn "Interrupted. Run again to resume."; exit 1' INT TERM

main "$@"
