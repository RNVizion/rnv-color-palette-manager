"""
test_perf_palette_io.py — Performance benchmarks for palette import/export
============================================================================

Phase 9. Benchmarks the per-format palette I/O paths. Less hot-path than
color math (these run once per save/open, not per frame), but still worth
guarding against accidental quadratic regressions in parsers and serializers.

Why these specific formats
---------------------------
We sample a representative subset:
  - JSON: pure-text serializer, baseline
  - GPL: line-by-line text parser, common case
  - ASE: binary format, exercises struct packing
  - SVG: text with formatting, more complex serializer
  - ACO: another binary format

Skipping 11+ format-specific benchmarks because they share parsing patterns;
if one binary format regresses, all binary formats likely regress together.

Running
-------
    pytest tests/test_perf_palette_io.py --benchmark-only
"""
from __future__ import annotations

import pytest

from core.palette_formats import PaletteFormats


# Note: no `pytestmark = pytest.mark.benchmark` — pytest-benchmark detects
# benchmarks via the `benchmark` fixture, not via marker.


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_colors():
    """30-color palette — represents a typical full palette."""
    return [
        ((i * 8 % 256, (i * 13) % 256, (i * 17) % 256), 100 // 30)
        for i in range(30)
    ]


# ═══════════════════════════════════════════════════════════════════════════
# EXPORT BENCHMARKS
# ═══════════════════════════════════════════════════════════════════════════

def test_bench_export_json(benchmark, sample_colors, tmp_path):
    """JSON export — the project's canonical format."""
    out = tmp_path / "bench.json"
    benchmark(PaletteFormats.export_palette, str(out), sample_colors)


def test_bench_export_gpl(benchmark, sample_colors, tmp_path):
    """GPL export — common interop format with GIMP."""
    out = tmp_path / "bench.gpl"
    benchmark(PaletteFormats.export_palette, str(out), sample_colors)


def test_bench_export_ase(benchmark, sample_colors, tmp_path):
    """ASE export — Adobe binary format, exercises struct packing."""
    out = tmp_path / "bench.ase"
    benchmark(PaletteFormats.export_palette, str(out), sample_colors)


def test_bench_export_svg(benchmark, sample_colors, tmp_path):
    """SVG export — most complex text serializer."""
    out = tmp_path / "bench.svg"
    benchmark(PaletteFormats.export_palette, str(out), sample_colors)


def test_bench_export_aco(benchmark, sample_colors, tmp_path):
    """ACO export — Photoshop binary format."""
    out = tmp_path / "bench.aco"
    benchmark(PaletteFormats.export_palette, str(out), sample_colors)


# ═══════════════════════════════════════════════════════════════════════════
# IMPORT BENCHMARKS — write once, then import multiple times
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_json_file(sample_colors, tmp_path):
    """Pre-export a JSON file we can re-import for benchmarking."""
    p = tmp_path / "sample.json"
    PaletteFormats.export_palette(str(p), sample_colors)
    return str(p)


@pytest.fixture
def sample_gpl_file(sample_colors, tmp_path):
    p = tmp_path / "sample.gpl"
    PaletteFormats.export_palette(str(p), sample_colors)
    return str(p)


@pytest.fixture
def sample_ase_file(sample_colors, tmp_path):
    p = tmp_path / "sample.ase"
    PaletteFormats.export_palette(str(p), sample_colors)
    return str(p)


def test_bench_import_json(benchmark, sample_json_file):
    """JSON import — should be very fast."""
    benchmark(PaletteFormats.import_palette, sample_json_file)


def test_bench_import_gpl(benchmark, sample_gpl_file):
    """GPL import — line-by-line text parsing."""
    benchmark(PaletteFormats.import_palette, sample_gpl_file)


def test_bench_import_ase(benchmark, sample_ase_file):
    """ASE import — binary parsing, watches for struct.unpack regressions."""
    benchmark(PaletteFormats.import_palette, sample_ase_file)
