"""
run_tests.py — Unified test runner for RNV Color Palette Manager
================================================================
Runs both test sources under coverage with branch analysis (configured
in .coveragerc), then merges the data files into a single coverage report.

  Suite 1 — test_rnv_palette_manager.py    (374 unittest tests, ~35s)
  Suite 2 — tests/                          (hypothesis property tests)

Usage:
    python run_tests.py              # run everything, merge, show report
    python run_tests.py --report     # regenerate report from existing data
    python run_tests.py --summary    # report with --skip-covered (gaps only)
    python run_tests.py --html       # also write HTML report to htmlcov/
    python run_tests.py --no-merge   # debug: leave both .coverage.* files

Exit code is non-zero if either suite has failures.

────────────────────────────────────────────────────────────────────────────
NOTE: The unittest suite runs via `-m unittest` rather than as a script.
This is intentional — the test file ends with os._exit() to bypass PyQt6
cleanup crashes, but os._exit() also skips coverage's atexit data flush.
Running via `-m unittest` means the file's __main__ block (where the
os._exit lives) never fires, so coverage flushes normally.

Trade-off: the colored summary printed by test_rnv_palette_manager.py's
__main__ block does NOT appear under this runner — only unittest's
default output. To see the colored summary, run the file directly:
    python test_rnv_palette_manager.py
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Use the current interpreter via -m so we don't depend on coverage/pytest
# being on PATH (more reliable on Windows than bare `coverage` / `pytest`).
PYTHON = sys.executable
COVERAGE = [PYTHON, "-m", "coverage"]

# Per-suite data files so they don't overwrite each other before merge.
UNITTEST_DATA = ".coverage.unittest"
PYTEST_DATA = ".coverage.pytest"


def _run(label: str, cmd: list[str]) -> int:
    """Run a subprocess, stream its output, return its exit code."""
    print()
    print("=" * 72)
    print(f"  {label}")
    print("=" * 72)
    print(f"  $ {' '.join(cmd)}")
    print()
    return subprocess.call(cmd, cwd=ROOT)


# ─── Suite runners ───────────────────────────────────────────────────────────

def run_unittest_suite() -> int:
    """Run the 374-test unittest suite under coverage.

    Uses `-m unittest` rather than executing the file directly, so:
      - The file's `os._exit()` doesn't fire (allows coverage flush)
      - The QApplication setup at top of file still runs (executes on
        import, not under __main__)
    """
    return _run(
        "Suite 1 / 2 — unittest (test_rnv_palette_manager.py)",
        [
            *COVERAGE, "run",
            f"--data-file={UNITTEST_DATA}",
            "-m", "unittest", "test_rnv_palette_manager", "-v",
        ],
    )


def run_pytest_suite() -> int:
    """Run pytest tests under coverage. Skips silently if tests/ is missing."""
    tests_dir = ROOT / "tests"

    if not tests_dir.is_dir():
        print("\n[skip] tests/ directory not found — pytest suite skipped.")
        return 0

    test_files = list(tests_dir.glob("test_*.py"))
    if not test_files:
        print("\n[skip] tests/ has no test_*.py files — pytest suite skipped.")
        return 0

    return _run(
        "Suite 2 / 2 — pytest (tests/)",
        [
            *COVERAGE, "run",
            f"--data-file={PYTEST_DATA}",
            "-m", "pytest", "tests/", "-v",
        ],
    )


# ─── Coverage data handling ──────────────────────────────────────────────────

def merge_data_files() -> int:
    """Combine per-suite .coverage.* files into the canonical .coverage."""
    parts = [p for p in (UNITTEST_DATA, PYTEST_DATA) if (ROOT / p).exists()]
    if not parts:
        print("\n[error] no coverage data files found — cannot merge.")
        return 1

    # `coverage combine` deletes input files after a successful merge.
    return subprocess.call([*COVERAGE, "combine", *parts], cwd=ROOT)


def print_report(summary: bool = False, html: bool = False) -> int:
    """Print combined report. summary=True hides 100%-covered files."""
    print()
    print("=" * 72)
    print("  Coverage report" + ("  (--skip-covered)" if summary else ""))
    print("=" * 72)

    cmd = [*COVERAGE, "report", "-m"]
    if summary:
        cmd.append("--skip-covered")
    rc = subprocess.call(cmd, cwd=ROOT)

    # Archive the full report to a text file for diffing across runs.
    try:
        with open(ROOT / "coverage_report.txt", "w", encoding="utf-8") as f:
            subprocess.call([*COVERAGE, "report", "-m"], cwd=ROOT, stdout=f)
    except Exception as e:
        print(f"[warn] couldn't archive report: {e}")

    if html:
        print()
        print("Generating HTML report at htmlcov/...")
        subprocess.call([*COVERAGE, "html"], cwd=ROOT)
        print("Open htmlcov/index.html in a browser.")

    return rc


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    args = set(sys.argv[1:])
    summary = "--summary" in args
    html = "--html" in args

    # Report-only mode: skip both suites, just regenerate from existing data.
    if "--report" in args:
        return print_report(summary=summary, html=html)

    rc1 = run_unittest_suite()
    rc2 = run_pytest_suite()

    if "--no-merge" not in args:
        merge_data_files()
        print_report(summary=summary, html=html)

    # Non-zero exit if either suite failed — useful for CI gates.
    return max(rc1, rc2)


if __name__ == "__main__":
    sys.exit(main())
