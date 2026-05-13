"""
test_import_snapshots.py — Import-side roundtrip tests using snapshot files
============================================================================

Pairs with test_export_snapshots.py. That file ensures exporters produce
canonical bytes; this file feeds those same bytes back through
PaletteFormats.import_palette() and verifies colors round-trip correctly.

Together they cover both halves of the format story:

    canonical input → export → snapshot file → import → match canonical input

Why a separate file
-------------------
Export and import are different concerns with different failure modes
(format drift vs format-misparsing) and different tolerance requirements.
Keeping them separate makes failures unambiguous.

Format coverage
---------------
Tests every format in PaletteFormats.get_import_formats() — 15 formats.
The .acb format is export-only (no importer exists) so it's deliberately
excluded; the cross-check sanity test will fail loudly if that ever changes.

Tolerance per format
--------------------
Round-trip drift varies by format. Per-format tolerance reflects the
max RGB-channel delta that's mathematically possible given the format's
storage representation:

  Exact (±0): formats storing raw integers or hex strings
              gpl, css, json, xml, hex, txt, colors

  ±1: formats storing floats in [0,1] then re-multiplying by 255 on import
      ase, aco, swatches, afpalette, clr

  ±1: SVG hex extraction (text format, +1 tolerance for safety)
      svg

  ±2: HSV/HSL formats (trigonometric round-trip drift through angles)
      hsv, hsl

SVG special case
----------------
The SVG exporter writes a white background rect plus the swatches, so
SVG import returns 6 colors (white + 5 canonical). The test handles this
by checking that all canonical colors APPEAR in the result.

Known bugs (xfail-marked)
-------------------------
This file documents three bugs surfaced when running these tests for the
first time. Each is marked with @pytest.mark.xfail referencing this section.
When fixed, remove the xfail and verify XPASS.

  BUG #1: _import_colors() at palette_formats.py:760
    Exporter writes data lines starting with '#' (the hex prefix):
        #ff0000 255   0   0  50 # Color 1
    Importer skips any line where `line.startswith('#')`, treating ALL
    data lines as comments. Returns empty.
    Fix: distinguish '# comment ' (with following space) from '#hex'.

  BUG #2: _import_hex() at palette_formats.py:783
    Same root cause as Bug #1. Exporter writes:
        #ff0000  50 # Color 1
    Importer skips because line starts with '#'. Returns empty.
    Same one-line fix applies.

  BUG #3: _export_hsl() at palette_formats.py:470
    Variable misnaming corrupts every HSL export:
        h, l, s = ColorMath.rgb_to_hsl(color)
    rgb_to_hsl returns (h, s, l) but unpacking names them (h, l, s) — so
    the variable named 'l' actually holds saturation, and 's' holds
    lightness. Subsequent f.write() emits H, S-column-with-L-value,
    L-column-with-S-value. Format header advertises H/S/L but file
    contains H/L/S. Pure red (255,0,0) exports as H=0, "S"=50, "L"=100,
    which on import is interpreted as L=100% → white.
    Severity: this corrupts every .hsl file the app produces. Anyone
    importing those files (in this app or another) gets wrong colors.

Run:
    pytest tests/test_import_snapshots.py
    pytest tests/test_import_snapshots.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.palette_formats import PaletteFormats


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS (mirror test_export_snapshots.py — keep in sync)
# ═══════════════════════════════════════════════════════════════════════════

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = ROOT / "snapshots"
SNAPSHOT_BASENAME = "canonical"

EXPECTED_COLORS: list[tuple[int, int, int]] = [
    (255,   0,   0),
    (  0, 255,   0),
    (  0,   0, 255),
    (128, 128, 128),
    (255, 200, 100),
]

IMPORTABLE_FORMATS: list[str] = [
    "ase", "aco", "swatches",
    "gpl", "colors", "css", "json", "xml", "hex", "txt",
    "afpalette", "clr",
    "hsv", "hsl",
    "svg",
]

TOLERANCES: dict[str, int] = {
    "gpl": 0, "css": 0, "json": 0, "xml": 0, "hex": 0, "txt": 0, "colors": 0,
    "afpalette": 1, "clr": 1, "ase": 1, "aco": 1, "swatches": 1,
    "hsv": 2, "hsl": 2,
    "svg": 1,
}

FORMATS_WITH_EXTRA_COLORS = {"svg"}

# Known bugs in palette_formats.py — see module docstring for full details.
# Each entry: ext → short reason for xfail. Tests xfail when format is here.
KNOWN_BUGS: dict[str, str] = {
    "colors": (
        "BUG #1: _import_colors() at palette_formats.py:760 skips lines "
        "starting with '#' as comments, but data lines start with '#hex'. "
        "Returns empty. See test_import_snapshots.py docstring."
    ),
    "hex": (
        "BUG #2: _import_hex() at palette_formats.py:783 — same comment-line "
        "bug as Bug #1. Returns empty. See test_import_snapshots.py docstring."
    ),
    "hsl": (
        "BUG #3: _export_hsl() at palette_formats.py:470 misnames variables "
        "(h, l, s = rgb_to_hsl) and swaps S/L on output. Pure colors export "
        "as white. See test_import_snapshots.py docstring."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _snapshot_path(ext: str) -> Path:
    return SNAPSHOT_DIR / f"{SNAPSHOT_BASENAME}.{ext}"


def _within_tolerance(
    expected: tuple[int, int, int],
    actual: tuple[int, int, int],
    tolerance: int,
) -> bool:
    return all(abs(e - a) <= tolerance for e, a in zip(expected, actual))


# ═══════════════════════════════════════════════════════════════════════════
# SANITY CHECKS
# ═══════════════════════════════════════════════════════════════════════════

def test_importable_formats_match_get_import_formats():
    """IMPORTABLE_FORMATS must match what PaletteFormats actually imports."""
    declared: set[str] = set()
    for _label, spec in PaletteFormats.get_import_formats():
        for chunk in spec.split():
            ext = chunk.lstrip("*.").lower()
            if ext and ext != "*":
                declared.add(ext)

    expected = set(IMPORTABLE_FORMATS)

    missing_from_test = declared - expected
    missing_from_code = expected - declared

    assert not missing_from_test, (
        f"Formats declared in PaletteFormats.get_import_formats() but not "
        f"tested: {sorted(missing_from_test)}."
    )
    assert not missing_from_code, (
        f"Formats in IMPORTABLE_FORMATS but not declared in "
        f"PaletteFormats.get_import_formats(): {sorted(missing_from_code)}."
    )


def test_every_importable_format_has_tolerance():
    """No format may be in IMPORTABLE_FORMATS without a defined tolerance."""
    missing = set(IMPORTABLE_FORMATS) - set(TOLERANCES.keys())
    assert not missing, f"Tolerance not defined for: {sorted(missing)}"


def test_canonical_json_snapshot_has_fixed_timestamps():
    """Snapshot timestamps must match what test_export_snapshots.py wrote."""
    json_snapshot = _snapshot_path("json")
    if not json_snapshot.exists():
        pytest.skip(
            "JSON snapshot not generated yet.\n"
            "Run: UPDATE_SNAPSHOTS=1 pytest tests/test_export_snapshots.py"
        )

    data = json.loads(json_snapshot.read_text(encoding="utf-8"))
    assert data.get("created_at") == "2025-01-01T00:00:00", (
        f"JSON snapshot has wrong created_at: {data.get('created_at')!r}. "
        f"Snapshot was regenerated with non-canonical metadata."
    )
    assert data.get("modified_at") == "2025-01-01T00:00:00"


# ═══════════════════════════════════════════════════════════════════════════
# THE MAIN TEST — parametrized over all 15 importable formats
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ext", IMPORTABLE_FORMATS)
def test_import_snapshot_returns_canonical_colors(ext: str):
    """Read the canonical snapshot for <ext> and verify colors roundtrip.

    Tests for formats with known bugs are marked xfail; when the bug is
    fixed the test will XPASS (notable but not a failure) until the
    KNOWN_BUGS entry is removed.
    """
    # XFail known bugs explicitly. Using xfail (not skip) so that fixing
    # the bug causes XPASS — visible feedback that the fix worked.
    if ext in KNOWN_BUGS:
        pytest.xfail(KNOWN_BUGS[ext])

    snapshot_path = _snapshot_path(ext)
    if not snapshot_path.exists():
        pytest.skip(
            f"Snapshot missing: {snapshot_path}\n"
            f"Run: UPDATE_SNAPSHOTS=1 pytest tests/test_export_snapshots.py"
        )

    result = PaletteFormats.import_palette(str(snapshot_path))

    assert not result.is_empty, (
        f".{ext} import returned empty result. Check that "
        f"PaletteFormats._import_{ext}() handles the canonical export."
    )

    tolerance = TOLERANCES[ext]
    actual_colors = [color for color, _weight in result.colors]

    if ext not in FORMATS_WITH_EXTRA_COLORS:
        # Strict path
        assert len(actual_colors) == len(EXPECTED_COLORS), (
            f".{ext} returned {len(actual_colors)} colors, expected "
            f"{len(EXPECTED_COLORS)}. Got: {actual_colors}"
        )
        for i, (expected, actual) in enumerate(zip(EXPECTED_COLORS, actual_colors)):
            assert _within_tolerance(expected, actual, tolerance), (
                f".{ext} color #{i+1}: expected {expected}, got {actual} "
                f"(tolerance ±{tolerance})"
            )
        return

    # Lenient path — every canonical color must appear somewhere
    for expected in EXPECTED_COLORS:
        found = any(
            _within_tolerance(expected, actual, tolerance)
            for actual in actual_colors
        )
        assert found, (
            f".{ext} import is missing canonical color {expected}. "
            f"Got: {actual_colors}"
        )


@pytest.mark.parametrize("ext", IMPORTABLE_FORMATS)
def test_import_snapshot_does_not_raise(ext: str):
    """Importing each canonical snapshot must not raise an exception.

    Note: this test does NOT xfail for KNOWN_BUGS — even a buggy importer
    should fail gracefully (return empty) rather than raising. This test
    catches silent breakage where exceptions propagate instead.
    """
    snapshot_path = _snapshot_path(ext)
    if not snapshot_path.exists():
        pytest.skip(f"Snapshot missing: {snapshot_path}")

    result = PaletteFormats.import_palette(str(snapshot_path))
    assert result is not None, f".{ext} import returned None"


# ═══════════════════════════════════════════════════════════════════════════
# METADATA ROUNDTRIP — JSON only
# ═══════════════════════════════════════════════════════════════════════════

def test_json_import_recovers_metadata():
    """JSON import must recover name, author, and timestamps from the snapshot."""
    snapshot_path = _snapshot_path("json")
    if not snapshot_path.exists():
        pytest.skip("JSON snapshot not generated yet.")

    result = PaletteFormats.import_palette(str(snapshot_path))
    assert result.metadata is not None, "JSON import should recover metadata"

    assert result.metadata.name == "Test Palette"
    assert result.metadata.author == "Tester"
    assert result.metadata.created_at == "2025-01-01T00:00:00"
    assert result.metadata.modified_at == "2025-01-01T00:00:00"
