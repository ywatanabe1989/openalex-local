#!/bin/bash
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-14"
# Author: ywatanabe (with Claude)
# File: scripts/setup/check_prerequisites.sh
# Description: Check and guide installation of prerequisites for OpenAlex Local

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log() { echo -e "${CYAN}[INFO]${NC} $*"; }
ok() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Track issues
ISSUES=()

echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}OpenAlex Local - Prerequisites Check${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""

# 1. Check Python
echo -e "${CYAN}[1/5] Python${NC}"
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
        ok "Python $PY_VERSION found"
    else
        error "Python $PY_VERSION found, but 3.10+ required"
        ISSUES+=("python")
    fi
else
    error "Python3 not found"
    ISSUES+=("python")
fi

# 2. Check AWS CLI
echo ""
echo -e "${CYAN}[2/5] AWS CLI${NC}"
if command -v aws &>/dev/null; then
    AWS_VERSION=$(aws --version 2>&1 | cut -d' ' -f1 | cut -d'/' -f2)
    ok "AWS CLI $AWS_VERSION found"
else
    error "AWS CLI not installed"
    echo ""
    echo "    Install options:"
    echo ""
    echo "    Option 1 - pip (recommended):"
    echo "      pip install awscli"
    echo ""
    echo "    Option 2 - conda:"
    echo "      conda install -c conda-forge awscli"
    echo ""
    echo "    Option 3 - system package (Ubuntu/Debian):"
    echo "      sudo apt-get install awscli"
    echo ""
    ISSUES+=("aws")
fi

# 3. Check disk space
echo ""
echo -e "${CYAN}[3/5] Disk Space${NC}"
DATA_DIR="${PROJECT_ROOT}/data"
mkdir -p "$DATA_DIR"

AVAILABLE_GB=$(df -BG "$DATA_DIR" 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G')
REQUIRED_GB=500  # ~300GB compressed + headroom for database

if [[ "$AVAILABLE_GB" -ge "$REQUIRED_GB" ]]; then
    ok "${AVAILABLE_GB}GB available (need ${REQUIRED_GB}GB)"
else
    warn "${AVAILABLE_GB}GB available (recommend ${REQUIRED_GB}GB+)"
    echo "    OpenAlex works snapshot: ~200-300GB compressed"
    echo "    Built database: ~200-500GB"
    ISSUES+=("disk")
fi

# 4. Check network connectivity to S3
echo ""
echo -e "${CYAN}[4/5] S3 Connectivity${NC}"
if command -v aws &>/dev/null; then
    if aws s3 ls s3://openalex/ --no-sign-request 2>/dev/null | head -1 | grep -q "data"; then
        ok "Can access OpenAlex S3 bucket"
    else
        warn "Cannot verify S3 access (may work during download)"
    fi
else
    warn "Skipped (AWS CLI not installed)"
fi

# 5. Check project installation
echo ""
echo -e "${CYAN}[5/5] Project Installation${NC}"
if pip show openalex-local &>/dev/null 2>&1; then
    INSTALLED_VERSION=$(pip show openalex-local 2>/dev/null | grep Version | cut -d' ' -f2)
    ok "openalex-local $INSTALLED_VERSION installed"
else
    warn "openalex-local not installed"
    echo "    Run: make install"
    ISSUES+=("install")
fi

# Summary
echo ""
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}Summary${NC}"
echo -e "${BOLD}========================================${NC}"

if [[ ${#ISSUES[@]} -eq 0 ]]; then
    echo ""
    ok "All prerequisites satisfied!"
    echo ""
    echo "Next steps:"
    echo "  1. make download-manifest   # Check snapshot size"
    echo "  2. make download            # Download (~300GB, several hours)"
    echo "  3. make build-db            # Build database (~1-2 days)"
    echo ""
    exit 0
else
    echo ""
    error "Issues found: ${ISSUES[*]}"
    echo ""
    echo "Please resolve the above issues before proceeding."
    echo "Run 'make check' again after fixing."
    echo ""
    exit 1
fi
