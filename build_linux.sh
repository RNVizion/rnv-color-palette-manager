#!/usr/bin/env bash
# ============================================================
#  RNV Color Palette Manager - Build Executable (Unix/macOS)
#  Runs the test suite, then builds the executable via PyInstaller
# ============================================================
#
# Usage:
#   ./build_linux.sh                Test-gated build (default)
#   ./build_linux.sh --skip-tests   Skip the test step (faster)
#
# Requires:
#   - Python 3.13 on PATH
#   - PyInstaller installed:  pip install pyinstaller
#   - Test dependencies:      pip install -r requirements-dev.txt
#
# Notes:
#   - Linux executables built with PyInstaller are tied to the
#     glibc version of the build machine. A binary built on
#     Ubuntu 24.04 will NOT run on Ubuntu 20.04. For wider
#     distribution, consider AppImage, Flatpak, or a .deb/.rpm.
#   - On macOS, this script also works but produces a Mach-O
#     binary rather than ELF.
# ============================================================

set -e

# Change to the directory containing this script
cd "$(dirname "$0")"

echo ""
echo "============================================================"
echo "  Building RNV Color Palette Manager"
echo "============================================================"
echo ""

# --- Step 1: Clean previous build artifacts -----------------
echo "  [1/3] Cleaning previous build artifacts..."
rm -rf build dist

# --- Step 2: Run tests (unless --skip-tests is passed) ------
if [ "$1" = "--skip-tests" ]; then
    echo "  [2/3] Skipping tests (--skip-tests flag set)."
else
    echo "  [2/3] Running test suite..."
    if ! python run_tests.py; then
        echo ""
        echo "============================================================"
        echo "  BUILD ABORTED: Tests failed."
        echo "  Use --skip-tests to bypass."
        echo "============================================================"
        echo ""
        exit 1
    fi
fi

# --- Step 3: Build with PyInstaller -------------------------
echo "  [3/3] Building executable..."
if ! pyinstaller RNV_Color_Palette_Manager.spec; then
    echo ""
    echo "============================================================"
    echo "  BUILD FAILED: PyInstaller returned an error."
    echo "============================================================"
    echo ""
    exit 1
fi

echo ""
echo "============================================================"
echo "  BUILD SUCCEEDED"
echo "  Output: dist/RNV_Color_Palette_Manager"
echo "============================================================"
echo ""

exit 0
