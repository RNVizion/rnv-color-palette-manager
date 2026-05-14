@echo off
REM ============================================================
REM  RNV Color Palette Manager - Build Executable (Windows)
REM  Runs the test suite, then builds the .exe via PyInstaller
REM ============================================================
REM
REM Usage:
REM   build_windows.bat                Test-gated build (default)
REM   build_windows.bat --skip-tests   Skip the test step (faster)
REM
REM Requires:
REM   - Python 3.13 on PATH
REM   - PyInstaller installed: pip install pyinstaller
REM   - Test dependencies:     pip install -r requirements-dev.txt
REM ============================================================

echo.
echo ============================================================
echo   Building RNV Color Palette Manager
echo ============================================================
echo.

REM Change to the directory containing this script
cd /d "%~dp0"

REM --- Step 1: Clean previous build artifacts ----------------
echo   [1/3] Cleaning previous build artifacts...
if exist "build" rd /s /q "build"
if exist "dist"  rd /s /q "dist"

REM --- Step 2: Run tests (unless --skip-tests is passed) -----
if /i "%~1"=="--skip-tests" (
    echo   [2/3] Skipping tests ^(--skip-tests flag set^).
) else (
    echo   [2/3] Running test suite...
    python run_tests.py
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo   BUILD ABORTED: Tests failed.
        echo   Use --skip-tests to bypass.
        echo ============================================================
        echo.
        pause
        exit /b 1
    )
)

REM --- Step 3: Build with PyInstaller ------------------------
echo   [3/3] Building executable...
pyinstaller RNV_Color_Palette_Manager.spec
if errorlevel 1 (
    echo.
    echo ============================================================
    echo   BUILD FAILED: PyInstaller returned an error.
    echo ============================================================
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   BUILD SUCCEEDED
echo   Output: dist\RNV_Color_Palette_Manager.exe
echo ============================================================
echo.

REM Open the dist folder so the executable is easy to find
if exist "dist" explorer "dist"

pause
exit /b 0
