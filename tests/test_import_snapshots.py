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

Bug fix history
---------------
Phase 5b initial run surfaced three bugs in palette_formats.py that
prevented round-trip:

  - _import_colors() at line 760: skipped data lines starting with '#'
    as comments, even though hex codes legitimately start with '#'.
    Fixed by distinguishing '# comment' (with space) from '#hex'.

  - _import_hex() at line 783: same bug, same fix.

  - _import_hsl() at line 840: passed (h, s, l) to ColorMath.hsl_to_rgb(),
    but that function wraps Python's colorsys which uses HLS ordering.
    Fixed by passing (h, l, s). Note that ColorMath.rgb_to_hsl /
    hsl_to_rgb are both misleadingly named — they actually operate on
    HLS-ordered tuples internally. The function pair is consistent with
    itself (roundtrip works), but external code passing in HSL-ordered
    tuples will produce wrong colors.

If any of these tests start failing again, the regression is real.

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
        f"JSON snapshot has wrong created_at: {data.get('created_at')!r}."
    )
    assert data.get("modified_at") == "2025-01-01T00:00:00"


# ═══════════════════════════════════════════════════════════════════════════
# THE MAIN TEST — parametrized over all 15 importable formats
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ext", IMPORTABLE_FORMATS)
def test_import_snapshot_returns_canonical_colors(ext: str):
    """Read the canonical snapshot for <ext> and verify colors roundtrip."""
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
    """Importing each canonical snapshot must not raise an exception."""
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
