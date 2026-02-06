#!/bin/bash
# -*- coding: utf-8 -*-
# OpenAlex Local - CLI Demo
#
# Usage:
#   ./examples/02_cli_demo.sh

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  OpenAlex Local - CLI Demo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "1. Basic Search"
echo "───────────────────────────────────────────────────────────────────"
echo "\$ openalex-local search \"machine learning\" -n 3"
openalex-local search "machine learning" -n 3 || true

echo ""
echo "2. Search with Abstracts"
echo "───────────────────────────────────────────────────────────────────"
echo "\$ openalex-local search \"CRISPR\" -n 2 -a"
openalex-local search "CRISPR" -n 2 -a || true

echo ""
echo "3. Search with Authors and Concepts"
echo "───────────────────────────────────────────────────────────────────"
echo "\$ openalex-local search \"neural network\" -n 2 -A --concepts"
openalex-local search "neural network" -n 2 -A --concepts || true

echo ""
echo "4. JSON Output (for scripting)"
echo "───────────────────────────────────────────────────────────────────"
echo "\$ openalex-local search \"protein folding\" -n 1 --json | head -20"
openalex-local search "protein folding" -n 1 --json 2>/dev/null | head -20 || true

echo ""
echo "5. Help"
echo "───────────────────────────────────────────────────────────────────"
echo "\$ openalex-local --help"
openalex-local --help

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Demo complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
