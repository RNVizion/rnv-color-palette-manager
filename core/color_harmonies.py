"""
Color harmony generation and gradient interpolation.
Generates complementary, analogous, triadic, split-complementary,
tetradic, and monochromatic palettes from a base color.
Optimized for Python 3.13.
"""
from __future__ import annotations

import random

from core.color_math import ColorMath

# Type aliases
type RGB = tuple[int, int, int]


class ColorHarmonies:
    """Generate color harmonies and gradients from base colors."""

    # ------------------------------------------------------------------
    # Harmony generators (all return list[RGB] excluding the base)
    # ------------------------------------------------------------------

    @staticmethod
    def complementary(base: RGB) -> list[RGB]:
        """Opposite on the color wheel (1 color)."""
        h, s, v = ColorMath.rgb_to_hsv(base)
        return [ColorMath.hsv_to_rgb(((h + 0.5) % 1.0, s, v))]

    @staticmethod
    def analogous(base: RGB) -> list[RGB]:
        """Two adjacent colors on the wheel (+/-30 deg)."""
        h, s, v = ColorMath.rgb_to_hsv(base)
        return [
            ColorMath.hsv_to_rgb(((h - 1 / 12) % 1.0, s, v)),
            ColorMath.hsv_to_rgb(((h + 1 / 12) % 1.0, s, v)),
        ]

    @staticmethod
    def triadic(base: RGB) -> list[RGB]:
        """Two colors evenly spaced at 120 deg intervals."""
        h, s, v = ColorMath.rgb_to_hsv(base)
        return [
            ColorMath.hsv_to_rgb(((h + 1 / 3) % 1.0, s, v)),
            ColorMath.hsv_to_rgb(((h + 2 / 3) % 1.0, s, v)),
        ]

    @staticmethod
    def split_complementary(base: RGB) -> list[RGB]:
        """Two colors flanking the complement (+/-30 deg from opposite)."""
        h, s, v = ColorMath.rgb_to_hsv(base)
        opp = (h + 0.5) % 1.0
        return [
            ColorMath.hsv_to_rgb(((opp - 1 / 12) % 1.0, s, v)),
            ColorMath.hsv_to_rgb(((opp + 1 / 12) % 1.0, s, v)),
        ]

    @staticmethod
    def tetradic(base: RGB) -> list[RGB]:
        """Three colors forming a square on the wheel (90 deg apart)."""
        h, s, v = ColorMath.rgb_to_hsv(base)
        return [
            ColorMath.hsv_to_rgb(((h + 0.25) % 1.0, s, v)),
            ColorMath.hsv_to_rgb(((h + 0.50) % 1.0, s, v)),
            ColorMath.hsv_to_rgb(((h + 0.75) % 1.0, s, v)),
        ]

    @staticmethod
    def monochromatic(base: RGB) -> list[RGB]:
        """Four variations of the same hue with different saturation/value."""
        h, s, v = ColorMath.rgb_to_hsv(base)
        return [
            ColorMath.hsv_to_rgb((h, max(0.0, s * 0.4), min(1.0, v * 1.2))),
            ColorMath.hsv_to_rgb((h, max(0.0, s * 0.7), min(1.0, v * 1.1))),
            ColorMath.hsv_to_rgb((h, min(1.0, s * 1.2), max(0.0, v * 0.7))),
            ColorMath.hsv_to_rgb((h, min(1.0, s * 1.0), max(0.0, v * 0.5))),
        ]

    # ------------------------------------------------------------------
    # Lookup by name
    # ------------------------------------------------------------------

    HARMONY_NAMES: list[str] = [
        "Complementary",
        "Analogous",
        "Triadic",
        "Split-Complementary",
        "Tetradic / Square",
        "Monochromatic",
    ]

    @staticmethod
    def generate(name: str, base: RGB) -> list[RGB]:
        """Generate harmony by display name. Returns new colors only."""
        match name:
            case "Complementary":
                return ColorHarmonies.complementary(base)
            case "Analogous":
                return ColorHarmonies.analogous(base)
            case "Triadic":
                return ColorHarmonies.triadic(base)
            case "Split-Complementary":
                return ColorHarmonies.split_complementary(base)
            case "Tetradic / Square":
                return ColorHarmonies.tetradic(base)
            case "Monochromatic":
                return ColorHarmonies.monochromatic(base)
            case _:
                return []

    # ------------------------------------------------------------------
    # Gradient interpolation (LAB space)
    # ------------------------------------------------------------------

    @staticmethod
    def gradient(color_a: RGB, color_b: RGB, steps: int = 5) -> list[RGB]:
        """
        Generate a gradient between two colors using LAB interpolation.

        Args:
            color_a: Starting RGB color.
            color_b: Ending RGB color.
            steps: Total number of colors including start and end.

        Returns:
            List of RGB tuples from color_a to color_b.
        """
        steps = max(2, steps)
        lab_a = ColorMath.rgb_to_lab(color_a)
        lab_b = ColorMath.rgb_to_lab(color_b)

        result: list[RGB] = []
        for i in range(steps):
            t = i / (steps - 1)
            L = lab_a[0] + (lab_b[0] - lab_a[0]) * t
            a = lab_a[1] + (lab_b[1] - lab_a[1]) * t
            b = lab_a[2] + (lab_b[2] - lab_a[2]) * t
            result.append(ColorMath.lab_to_rgb((L, a, b)))
        return result

    # ------------------------------------------------------------------
    # Random palette generation
    # ------------------------------------------------------------------

    @staticmethod
    def random_harmonious(count: int = 5) -> list[RGB]:
        """
        Generate a harmonious random palette.

        Uses a random base hue with controlled saturation/value ranges
        and golden-ratio hue spacing to avoid muddy results.

        Args:
            count: Number of colors (2-12).

        Returns:
            List of RGB tuples.
        """
        count = max(2, min(12, count))
        base_h = random.random()
        # Golden ratio conjugate for nice hue spacing
        golden = 0.618033988749895

        colors: list[RGB] = []
        for i in range(count):
            h = (base_h + i * golden) % 1.0
            s = random.uniform(0.45, 0.85)
            v = random.uniform(0.55, 0.95)
            colors.append(ColorMath.hsv_to_rgb((h, s, v)))
        return colors

    @staticmethod
    def random_single() -> RGB:
        """Generate a single vivid random color."""
        h = random.random()
        s = random.uniform(0.5, 0.9)
        v = random.uniform(0.6, 0.95)
        return ColorMath.hsv_to_rgb((h, s, v))
