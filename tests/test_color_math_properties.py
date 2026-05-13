"""
test_color_math_properties.py — Property-based tests for core.color_math
=========================================================================

These hypothesis-driven tests complement the fixed-input tests in
test_rnv_palette_manager.py (TestColorMath, ~50 tests with hand-picked
values) by exercising properties across the full input space.

Where the existing tests verify "for these specific colors, the math
produces these specific results," these tests verify "for ANY valid input,
this property holds." Hypothesis generates hundreds of inputs per test,
including boundary cases (0, 255, 1, 254) and pathological combinations
that fixed-input tests don't reach.

Conventions:
  - RGB tolerances match the existing tests:
      hex   — exact (no tolerance)
      HSV   — ±2 per channel
      HSL   — ±2 per channel
      LAB   — ±3 per channel (lossy gamut clamp)
  - Clamp tests use FINITE floats only. clamp_value/clamp_rgb are not
    designed to handle NaN/inf — safe_rgb is the documented entry point
    for that. See test_rnv_palette_manager.py::test_safe_rgb_invalid_default.

Run:
    pytest tests/test_color_math_properties.py
    pytest tests/test_color_math_properties.py -v
"""
from __future__ import annotations

import math

import pytest
from hypothesis import given, strategies as st

from core.color_math import ColorMath


# ═══════════════════════════════════════════════════════════════════════════
# STRATEGIES
# ═══════════════════════════════════════════════════════════════════════════

# RGB tuple of three integers in [0, 255] — the full RGB cube
rgb_strategy = st.tuples(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
)

# Finite floats only — no NaN, no infinity. Bounded to a sane range to avoid
# integer-conversion overflow inside clamp_value.
finite_float = st.floats(
    min_value=-1e6,
    max_value=1e6,
    allow_nan=False,
    allow_infinity=False,
)

# A single (color, weight) entry for mix algorithms; weight 1..100
color_weight = st.tuples(
    rgb_strategy,
    st.integers(min_value=1, max_value=100),
)

# A non-empty list of color-weight tuples (mixers handle empty separately)
mix_input = st.lists(color_weight, min_size=1, max_size=8)

# All six mixers, parametrized — used to verify properties hold across all
ALL_MIXERS = [
    ColorMath.weighted_rgb_mix,
    ColorMath.weighted_hsv_mix,
    ColorMath.lab_perceptual_mix,
    ColorMath.subtractive_cmy_mix,
    ColorMath.weighted_ryb_mix,
    ColorMath.kubelka_munk_mix,
]


# ═══════════════════════════════════════════════════════════════════════════
# 1. CONVERSION ROUNDTRIPS
# ═══════════════════════════════════════════════════════════════════════════

@given(rgb_strategy)
def test_rgb_hex_roundtrip(rgb):
    """rgb_to_hex → hex_to_rgb returns the original RGB exactly."""
    assert ColorMath.hex_to_rgb(ColorMath.rgb_to_hex(rgb)) == rgb


@given(rgb_strategy)
def test_rgb_hsv_roundtrip(rgb):
    """rgb_to_hsv → hsv_to_rgb returns within ±2 per channel."""
    back = ColorMath.hsv_to_rgb(ColorMath.rgb_to_hsv(rgb))
    for original, restored in zip(rgb, back):
        assert abs(original - restored) <= 2, (
            f"HSV roundtrip drift > 2: {rgb} → {back}"
        )


@given(rgb_strategy)
def test_rgb_hsl_roundtrip(rgb):
    """rgb_to_hsl → hsl_to_rgb returns within ±2 per channel."""
    back = ColorMath.hsl_to_rgb(ColorMath.rgb_to_hsl(rgb))
    for original, restored in zip(rgb, back):
        assert abs(original - restored) <= 2, (
            f"HSL roundtrip drift > 2: {rgb} → {back}"
        )


@given(rgb_strategy)
def test_rgb_lab_roundtrip(rgb):
    """rgb_to_lab → lab_to_rgb returns within ±3 per channel.

    LAB has higher tolerance because the conversion involves gamma
    correction and matrix transforms that introduce floating-point drift.
    """
    back = ColorMath.lab_to_rgb(ColorMath.rgb_to_lab(rgb))
    for original, restored in zip(rgb, back):
        assert abs(original - restored) <= 3, (
            f"LAB roundtrip drift > 3: {rgb} → {back}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 2. CLAMP PROPERTIES
# ═══════════════════════════════════════════════════════════════════════════

@given(finite_float)
def test_clamp_value_in_range(x):
    """clamp_value output is always in [0, 255]."""
    result = ColorMath.clamp_value(x)
    assert 0 <= result <= 255


@given(finite_float)
def test_clamp_value_idempotent(x):
    """clamp_value(clamp_value(x)) == clamp_value(x).

    Idempotence is a stronger guarantee than 'in range' — it means
    re-clamping cannot drift the value, which is a real risk in any
    pipeline that double-clamps.
    """
    once = ColorMath.clamp_value(x)
    twice = ColorMath.clamp_value(once)
    assert once == twice


@given(
    finite_float,
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=101, max_value=255),
)
def test_clamp_value_custom_range(x, lo, hi):
    """clamp_value respects custom min/max bounds."""
    result = ColorMath.clamp_value(x, lo, hi)
    assert lo <= result <= hi


@given(finite_float, finite_float, finite_float)
def test_clamp_rgb_in_range(r, g, b):
    """All three channels of clamp_rgb output are in [0, 255]."""
    result = ColorMath.clamp_rgb(r, g, b)
    assert len(result) == 3
    for channel in result:
        assert 0 <= channel <= 255


@given(finite_float, finite_float, finite_float)
def test_clamp_rgb_idempotent(r, g, b):
    """clamp_rgb(clamp_rgb(...)) == clamp_rgb(...)."""
    once = ColorMath.clamp_rgb(r, g, b)
    twice = ColorMath.clamp_rgb(*once)
    assert once == twice


# ═══════════════════════════════════════════════════════════════════════════
# 3. COLOR DISTANCE PROPERTIES
# ═══════════════════════════════════════════════════════════════════════════

@given(rgb_strategy)
def test_color_distance_zero_on_equal(c):
    """distance(c, c) == 0 for any color c."""
    assert ColorMath.color_distance(c, c) == 0.0


@given(rgb_strategy, rgb_strategy)
def test_color_distance_symmetric(a, b):
    """distance(a, b) == distance(b, a)."""
    assert ColorMath.color_distance(a, b) == ColorMath.color_distance(b, a)


@given(rgb_strategy, rgb_strategy)
def test_color_distance_non_negative(a, b):
    """distance is always >= 0."""
    assert ColorMath.color_distance(a, b) >= 0


# ═══════════════════════════════════════════════════════════════════════════
# 4. MIX ALGORITHM PROPERTIES (parametrized over all 6 mixers)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("mixer", ALL_MIXERS, ids=lambda m: m.__name__)
def test_mixer_empty_returns_none(mixer):
    """Every mixer returns None for an empty input list."""
    assert mixer([]) is None


@pytest.mark.parametrize("mixer", ALL_MIXERS, ids=lambda m: m.__name__)
@given(st.lists(rgb_strategy, min_size=1, max_size=5))
def test_mixer_all_zero_weights_returns_none(mixer, colors):
    """Every mixer returns None when all weights are zero."""
    slots = [(c, 0) for c in colors]
    assert mixer(slots) is None


@pytest.mark.parametrize("mixer", ALL_MIXERS, ids=lambda m: m.__name__)
@given(mix_input)
def test_mixer_output_in_rgb_range(mixer, slots):
    """Every mixer produces output in [0,255]^3 or None."""
    result = mixer(slots)
    if result is not None:
        assert len(result) == 3, f"{mixer.__name__} returned non-3-tuple: {result}"
        for channel in result:
            assert 0 <= channel <= 255, (
                f"{mixer.__name__} channel out of range: {result}"
            )


@given(rgb_strategy, st.integers(min_value=1, max_value=100))
def test_weighted_rgb_single_slot_identity(rgb, weight):
    """weighted_rgb_mix([(c, w)]) == c for any positive w.

    Single-slot identity is a key invariant: a one-color "mix" is just
    that color, regardless of weight. This is the only mixer with this
    exact property — others (LAB, RYB, K-M) round-trip through other
    color spaces and may drift by 1-2 units.
    """
    assert ColorMath.weighted_rgb_mix([(rgb, weight)]) == rgb


# ═══════════════════════════════════════════════════════════════════════════
# 5. SANITY — non-property tests ensuring strategies cover edge cases
# ═══════════════════════════════════════════════════════════════════════════
# These are not hypothesis tests; they're regression guards verifying that
# the boundary RGB values still pass through the property-tested functions
# without exceptions. If a hypothesis test fails on a corner like (0,0,0)
# or (255,255,255), these will fail too and pinpoint the issue immediately.

EDGE_COLORS = [
    (0, 0, 0),
    (255, 255, 255),
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (128, 128, 128),
    (1, 1, 1),
    (254, 254, 254),
]


@pytest.mark.parametrize("rgb", EDGE_COLORS)
def test_edge_case_lab_roundtrip(rgb):
    """LAB roundtrip succeeds on every gamut corner without raising."""
    back = ColorMath.lab_to_rgb(ColorMath.rgb_to_lab(rgb))
    assert all(0 <= c <= 255 for c in back)


@pytest.mark.parametrize("rgb", EDGE_COLORS)
def test_edge_case_hsv_roundtrip(rgb):
    """HSV roundtrip succeeds on every gamut corner without raising."""
    back = ColorMath.hsv_to_rgb(ColorMath.rgb_to_hsv(rgb))
    assert all(0 <= c <= 255 for c in back)
