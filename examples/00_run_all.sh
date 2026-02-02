#!/bin/bash
# -*- coding: utf-8 -*-
# Run all openalex-local examples
#
# Usage:
#   ./examples/00_run_all.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Running openalex-local examples..."
echo ""

echo "=== 01_quickstart.py ==="
python3 01_quickstart.py
echo ""

echo "=== 02_cli_demo.sh ==="
./02_cli_demo.sh
echo ""

echo "All examples completed successfully."
