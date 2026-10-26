#!/usr/bin/env bash
# ============================================================
#  RNV Color Palette Manager - Clean Python Cache (Unix/macOS)
#  Recursively removes __pycache__, *.pyc, *.pyo, and tool caches
# ============================================================

set -e

# Change to the directory containing this script
cd "$(dirname "$0")"

echo ""
echo "============================================================"
echo "  Cleaning Python Cache Files"
echo "============================================================"
echo ""

# Delete __pycache__ directories recursively
echo "  Removing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Delete .pyc and .pyo files recursively
echo "  Removing compiled .pyc / .pyo files..."
find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true

# Delete type-checker and test-runner caches
echo "  Removing type-checker / test caches..."
find . -type d \( -name ".mypy_cache" -o -name ".pytest_cache" -o -name ".ruff_cache" \) -exec rm -rf {} + 2>/dev/null || true

echo ""
echo "============================================================"
echo "  Done!"
echo "============================================================"
echo ""
