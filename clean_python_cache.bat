@echo off
REM ============================================================
REM  RNV Color Palette Manager - Clean Python Cache (Windows)
REM  Recursively removes __pycache__, *.pyc, *.pyo, and tool caches
REM ============================================================

echo.
echo ============================================================
echo   Cleaning Python Cache Files
echo ============================================================
echo.

REM Change to the directory containing this script
cd /d "%~dp0"

REM Delete __pycache__ directories recursively
echo   Removing __pycache__ directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Delete .pyc and .pyo files recursively
echo   Removing compiled .pyc / .pyo files...
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul

REM Delete type-checker and test-runner caches
echo   Removing type-checker / test caches...
for /d /r . %%d in (.mypy_cache)   do @if exist "%%d" rd /s /q "%%d"
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d"
for /d /r . %%d in (.ruff_cache)   do @if exist "%%d" rd /s /q "%%d"

echo.
echo ============================================================
echo   Done!
echo ============================================================
echo.
pause
