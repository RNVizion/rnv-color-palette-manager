"""
test_export_snapshots.py — Byte-exact snapshot tests for palette exports
=========================================================================

For each of the 16 supported export formats, exports a canonical 5-color
palette with FIXED metadata, then byte-compares the result against a
stored snapshot file under /snapshots/.

Why this matters
----------------
Format roundtrip tests (in test_rnv_palette_manager.py::TestPaletteFormats)
verify that exporting and re-importing returns the same colors. Snapshot
tests verify something stronger: that the EXACT BYTES of each export
haven't changed. This catches:

  - Silent format drift (e.g. a refactor changes whitespace or field order)
  - Accidental dependency-version output changes (json.dump key ordering,
    XML serializer behavior, struct packing differences)
  - Locale or platform-dependent output (timezone, line endings)

When format changes are intentional, regenerate the snapshots:

    UPDATE_SNAPSHOTS=1 pytest tests/test_export_snapshots.py

Then commit the changed snapshot files alongside the format changes.
The diff in the snapshots makes the format change explicit in code review.

Snapshot location
-----------------
Snapshots live in /snapshots/ at the project root, one file per format:
    snapshots/canonical.gpl
    snapshots/canonical.json
    snapshots/canonical.ase
    ... (16 total)

Run:
    pytest tests/test_export_snapshots.py
    pytest tests/test_export_snapshots.py -v
    UPDATE_SNAPSHOTS=1 pytest tests/test_export_snapshots.py
"""
from __future__ import annotations

import difflib
import os
from pathlib import Path

import pytest

from core.palette_formats import PaletteFormats
from core.palette_metadata import PaletteMetadata


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL FIXTURES
# ═══════════════════════════════════════════════════════════════════════════
# These values are intentionally fixed. Changing them invalidates all
# snapshots — only do so if you've also re-run UPDATE_SNAPSHOTS=1 and
# committed the new snapshot files.

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = ROOT / "snapshots"
SNAPSHOT_BASENAME = "canonical"

# Same 5-color palette used in test_rnv_palette_manager.py::TestPaletteFormats
CANONICAL_COLORS: list[tuple[tuple[int, int, int], int]] = [
    ((255,   0,   0), 50),
    ((  0, 255,   0), 50),
    ((  0,   0, 255), 50),
    ((128, 128, 128), 50),
    ((255, 200, 100), 50),
]

# Metadata with FIXED timestamps. Critical for determinism — the JSON
# exporter embeds created_at and modified_at, which would otherwise be
# the current time and would diff on every run.
CANONICAL_METADATA = PaletteMetadata(
    name="Test Palette",
    author="Tester",
    created_at="2025-01-01T00:00:00",
    modified_at="2025-01-01T00:00:00",
)

# All 16 export-format extensions (no leading dot).
# This list is verified against PaletteFormats.get_export_formats() in a
# separate test below — adding a format there but not here will fail.
ALL_FORMATS: list[str] = [
    # Binary formats
    "ase",       # Adobe Swatch Exchange
    "aco",       # Adobe Color
    "acb",       # Adobe Color Book (export-only)
    "swatches",  # Procreate

    # Text formats
    "gpl",       # GIMP Palette
    "afpalette", # Affinity Designer (JSON-based)
    "clr",       # macOS color list (XML-based)
    "colors",    # Plain text with hex+rgb
    "css",       # CSS variables
    "json",      # JSON with full metadata
    "xml",       # XML with metadata
    "svg",       # SVG palette swatches
    "hex",       # Hex text list
    "hsv",       # HSV numeric text
    "hsl",       # HSL numeric text
    "txt",       # Human-readable plain text
]

# Which formats produce text vs binary output. Affects how we diff failures.
TEXT_FORMATS = {
    "gpl", "afpalette", "clr", "colors", "css", "json", "xml",
    "svg", "hex", "hsv", "hsl", "txt",
}
BINARY_FORMATS = {"ase", "aco", "acb", "swatches"}


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _snapshot_path(ext: str) -> Path:
    """Path to the canonical snapshot file for the given format extension."""
    return SNAPSHOT_DIR / f"{SNAPSHOT_BASENAME}.{ext}"


def _is_update_mode() -> bool:
    """True if running with UPDATE_SNAPSHOTS=1 (or true/yes)."""
    return os.environ.get("UPDATE_SNAPSHOTS", "").strip().lower() in {"1", "true", "yes"}


@pytest.fixture(scope="module", autouse=True)
def ensure_snapshot_dir():
    """Make sure snapshots/ exists before any tests run."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
# SANITY CHECKS — run first to catch fixture drift before all 16 format tests
# ═══════════════════════════════════════════════════════════════════════════

def test_canonical_metadata_has_fixed_timestamps():
    """If timestamps drift to current time, JSON snapshots will diff every run."""
    assert CANONICAL_METADATA.created_at == "2025-01-01T00:00:00"
    assert CANONICAL_METADATA.modified_at == "2025-01-01T00:00:00"


def test_all_formats_match_get_export_formats():
    """ALL_FORMATS must mirror PaletteFormats.get_export_formats() exactly.

    Catches the case where a new format is added in palette_formats.py
    but no snapshot test exists for it yet.
    """
    declared = {
        spec.lstrip("*.").lower()
        for _, spec in PaletteFormats.get_export_formats()
        if spec != "*.*"
    }
    expected = set(ALL_FORMATS)

    missing_from_test = declared - expected
    missing_from_code = expected - declared

    assert not missing_from_test, (
        f"Formats declared in PaletteFormats.get_export_formats() but missing "
        f"from this test's ALL_FORMATS: {sorted(missing_from_test)}. "
        f"Add them and run UPDATE_SNAPSHOTS=1 to generate snapshots."
    )
    assert not missing_from_code, (
        f"Formats in this test's ALL_FORMATS but not declared in "
        f"PaletteFormats.get_export_formats(): {sorted(missing_from_code)}. "
        f"Either add them to get_export_formats() or remove from ALL_FORMATS."
    )


# ═══════════════════════════════════════════════════════════════════════════
# THE MAIN SNAPSHOT TEST — parametrized over all 16 formats
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ext", ALL_FORMATS)
def test_export_matches_snapshot(ext: str, tmp_path: Path):
    """Export the canonical palette in <ext> and byte-compare to snapshot.

    In normal mode: fails if the snapshot doesn't exist or doesn't match.
    In update mode (UPDATE_SNAPSHOTS=1): writes the current export as the
    new snapshot and passes.
    """
    actual_path = tmp_path / f"actual.{ext}"
    snapshot_path = _snapshot_path(ext)

    # Generate the export
    PaletteFormats.export_palette(
        str(actual_path),
        CANONICAL_COLORS,
        CANONICAL_METADATA,
    )
    actual_bytes = actual_path.read_bytes()

    if _is_update_mode():
        # Write current output as new snapshot. Pass.
        snapshot_path.write_bytes(actual_bytes)
        return

    # Comparison mode: snapshot must exist
    if not snapshot_path.exists():
        pytest.fail(
            f"Snapshot missing: {snapshot_path}\n\n"
            f"To generate snapshots for the first time, run:\n"
            f"  UPDATE_SNAPSHOTS=1 pytest tests/test_export_snapshots.py\n"
        )

    expected_bytes = snapshot_path.read_bytes()

    # Fast path: bytes match
    if actual_bytes == expected_bytes:
        return

    # ─── Failure path — produce a useful diff ─────────────────────────────
    if ext in TEXT_FORMATS:
        try:
            actual_text = actual_bytes.decode("utf-8")
            expected_text = expected_bytes.decode("utf-8")
            diff = "\n".join(difflib.unified_diff(
                expected_text.splitlines(),
                actual_text.splitlines(),
                fromfile=f"snapshot.{ext}",
                tofile=f"actual.{ext}",
                lineterm="",
            ))
            pytest.fail(
                f"Export of .{ext} differs from snapshot.\n"
                f"To accept the new output, run:\n"
                f"  UPDATE_SNAPSHOTS=1 pytest tests/test_export_snapshots.py\n\n"
                f"--- diff ---\n{diff}"
            )
        except UnicodeDecodeError:
            # Format declared as text but produced non-UTF-8 — surprising
            pytest.fail(
                f"Export of .{ext} (declared TEXT) couldn't be decoded as UTF-8.\n"
                f"Either the format is actually binary or the export changed "
                f"its encoding. Snapshot size: {len(expected_bytes)} bytes, "
                f"actual size: {len(actual_bytes)} bytes."
            )
    else:
        # Binary format — show byte-level summary
        first_diff = next(
            (i for i, (a, b) in enumerate(zip(actual_bytes, expected_bytes)) if a != b),
            min(len(actual_bytes), len(expected_bytes)),
        )
        pytest.fail(
            f"Export of .{ext} (binary) differs from snapshot.\n"
            f"Snapshot size: {len(expected_bytes)} bytes\n"
            f"Actual size:   {len(actual_bytes)} bytes\n"
            f"First differing byte at offset: {first_diff}\n\n"
            f"To accept the new output, run:\n"
            f"  UPDATE_SNAPSHOTS=1 pytest tests/test_export_snapshots.py"
        )


# ═══════════════════════════════════════════════════════════════════════════
# COVERAGE GUARDS — separate from snapshots, ensure the FORMAT is exercised
# ═══════════════════════════════════════════════════════════════════════════
# These tests don't compare to snapshots; they just verify each format
# produces a non-empty file with sane minimum size, even when snapshots
# haven't been generated yet. Acts as a smoke-test layer below snapshots.

@pytest.mark.parametrize("ext", ALL_FORMATS)
def test_export_produces_nonempty_file(ext: str, tmp_path: Path):
    """Every format produces a non-empty output file."""
    output = tmp_path / f"smoke.{ext}"
    PaletteFormats.export_palette(
        str(output),
        CANONICAL_COLORS,
        CANONICAL_METADATA,
    )
    assert output.exists(), f"Export of .{ext} did not create a file"
    assert output.stat().st_size > 0, f"Export of .{ext} created an empty file"
