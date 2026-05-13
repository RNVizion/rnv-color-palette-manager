"""
test_perf_color_math.py — Performance benchmarks for ColorMath
================================================================

Phase 9. Performance regression guards for the project's hottest pure
code path: color space conversions and palette mixing algorithms. These
benchmarks run under pytest-benchmark and compare current run times
against historical statistics stored in `.benchmarks/`.

Why benchmark these specific functions
---------------------------------------
ColorMath operations are called in tight loops:
  - Palette generation iterates `generate_color_palette` per slot
  - Mixing reruns on every slider change in the mixer UI
  - LAB/HSL conversions happen on every paint redraw in image mode
  - Color search runs `color_distance` against every slot per keystroke

A 2x slowdown in any of these is user-visible. These tests give us
early warning before that ships.

Running
-------
    # Run benchmarks once, save results
    pytest tests/test_perf_color_math.py --benchmark-only

    # Compare against last saved run
    pytest tests/test_perf_color_math.py --benchmark-compare

    # Save a new baseline
    pytest tests/test_perf_color_math.py --benchmark-only --benchmark-save=baseline

Skipping in regular test runs
------------------------------
The conftest skips benchmarks unless --benchmark-only is passed, so
these don't slow down the normal `python run_tests.py` workflow.
"""
from __future__ import annotations

import pytest

from core.color_math import ColorMath


# Note: no `pytestmark = pytest.mark.benchmark` — pytest-benchmark detects
# benchmarks via the `benchmark` fixture, not via marker. Avoiding the
# marker also keeps these tests compatible with --strict-markers.


# ═══════════════════════════════════════════════════════════════════════════
# COLOR SPACE CONVERSIONS — single-color paths
# ═══════════════════════════════════════════════════════════════════════════

def test_bench_rgb_to_hex(benchmark):
    """rgb_to_hex is called everywhere — must stay fast."""
    benchmark(ColorMath.rgb_to_hex, (123, 45, 200))


def test_bench_hex_to_rgb(benchmark):
    """hex_to_rgb runs on every palette import."""
    benchmark(ColorMath.hex_to_rgb, "#7B2DC8")


def test_bench_rgb_to_hsv(benchmark):
    benchmark(ColorMath.rgb_to_hsv, (123, 45, 200))


def test_bench_rgb_to_hsl(benchmark):
    benchmark(ColorMath.rgb_to_hsl, (123, 45, 200))


def test_bench_rgb_to_lab(benchmark):
    """LAB conversion is the most expensive single conversion."""
    benchmark(ColorMath.rgb_to_lab, (123, 45, 200))


def test_bench_lab_to_rgb(benchmark):
    """Inverse LAB conversion — used heavily in lab_perceptual_mix."""
    benchmark(ColorMath.lab_to_rgb, (50.0, 25.0, -30.0))


# ═══════════════════════════════════════════════════════════════════════════
# COLOR DISTANCE — used per slot, per keystroke, in search
# ═══════════════════════════════════════════════════════════════════════════

def test_bench_color_distance(benchmark):
    """color_distance runs N times per search keystroke (N = slot count)."""
    benchmark(ColorMath.color_distance, (255, 100, 50), (123, 45, 200))


# ═══════════════════════════════════════════════════════════════════════════
# MIXING ALGORITHMS — runs on every slider drag in the mixer UI
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def four_slot_inputs():
    """Typical mixer input: 4 slots with varied weights."""
    return [
        ((255, 0, 0), 30),    # Red 30%
        ((0, 255, 0), 25),    # Green 25%
        ((0, 0, 255), 25),    # Blue 25%
        ((255, 255, 0), 20),  # Yellow 20%
    ]


def test_bench_weighted_rgb_mix(benchmark, four_slot_inputs):
    """RGB mix is the simplest and most-used algorithm."""
    benchmark(ColorMath.weighted_rgb_mix, four_slot_inputs)


def test_bench_weighted_hsv_mix(benchmark, four_slot_inputs):
    benchmark(ColorMath.weighted_hsv_mix, four_slot_inputs)


def test_bench_lab_perceptual_mix(benchmark, four_slot_inputs):
    """LAB mixing is the slowest — convert each color to LAB, mix, convert back."""
    benchmark(ColorMath.lab_perceptual_mix, four_slot_inputs)


def test_bench_subtractive_cmy_mix(benchmark, four_slot_inputs):
    benchmark(ColorMath.subtractive_cmy_mix, four_slot_inputs)


def test_bench_weighted_ryb_mix(benchmark, four_slot_inputs):
    benchmark(ColorMath.weighted_ryb_mix, four_slot_inputs)


def test_bench_kubelka_munk_mix(benchmark, four_slot_inputs):
    """Kubelka-Munk is the most complex mixing algorithm."""
    benchmark(ColorMath.kubelka_munk_mix, four_slot_inputs)


# ═══════════════════════════════════════════════════════════════════════════
# WORST-CASE SCENARIOS — many slots
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def many_slot_inputs():
    """Large mixer input: 30 slots — typical max palette size."""
    return [
        ((i * 8 % 256, (i * 13) % 256, (i * 17) % 256), 100 // 30)
        for i in range(30)
    ]


def test_bench_lab_mix_30_slots(benchmark, many_slot_inputs):
    """Worst case: 30-slot LAB mix. This is the slowest path the user can hit."""
    benchmark(ColorMath.lab_perceptual_mix, many_slot_inputs)


def test_bench_kubelka_munk_30_slots(benchmark, many_slot_inputs):
    """Worst case: 30-slot KM mix."""
    benchmark(ColorMath.kubelka_munk_mix, many_slot_inputs)


# ═══════════════════════════════════════════════════════════════════════════
# PALETTE GENERATION
# ═══════════════════════════════════════════════════════════════════════════

def test_bench_generate_palette_5(benchmark):
    """generate_color_palette runs once when the user clicks 'Generate'."""
    benchmark(ColorMath.generate_color_palette, (123, 45, 200), 5)


def test_bench_generate_palette_30(benchmark):
    """30-color generation — the user's max practical palette size."""
    benchmark(ColorMath.generate_color_palette, (123, 45, 200), 30)
