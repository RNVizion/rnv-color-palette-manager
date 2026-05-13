"""
Accessibility utilities for RNV Color Palette Manager.
WCAG 2.1 contrast ratio checking and color blindness simulation.
Optimized for Python 3.13.
"""
from __future__ import annotations

from dataclasses import dataclass

# Type aliases
type RGB = tuple[int, int, int]


@dataclass
class ContrastResult:
    """Result of a WCAG 2.1 contrast ratio check."""
    ratio: float
    aa_normal: bool       # >= 4.5:1
    aa_large: bool        # >= 3:1
    aaa_normal: bool      # >= 7:1
    aaa_large: bool       # >= 4.5:1

    @property
    def ratio_display(self) -> str:
        return f"{self.ratio:.2f}:1"

    @property
    def summary(self) -> str:
        lines = [f"Contrast Ratio: {self.ratio_display}"]
        lines.append(f"AA Normal Text:  {'PASS' if self.aa_normal else 'FAIL'}")
        lines.append(f"AA Large Text:   {'PASS' if self.aa_large else 'FAIL'}")
        lines.append(f"AAA Normal Text: {'PASS' if self.aaa_normal else 'FAIL'}")
        lines.append(f"AAA Large Text:  {'PASS' if self.aaa_large else 'FAIL'}")
        return "\n".join(lines)


class Accessibility:
    """WCAG contrast checking and color blindness simulation."""

    # ------------------------------------------------------------------
    # WCAG 2.1 Contrast Ratio
    # ------------------------------------------------------------------

    @staticmethod
    def relative_luminance(rgb: RGB) -> float:
        """
        Calculate relative luminance per WCAG 2.1.

        Args:
            rgb: Color as (r, g, b) with values 0-255.

        Returns:
            Luminance value between 0 (black) and 1 (white).
        """
        def linearize(c: int) -> float:
            s = c / 255.0
            return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

        r, g, b = linearize(rgb[0]), linearize(rgb[1]), linearize(rgb[2])
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    @staticmethod
    def contrast_ratio(color_a: RGB, color_b: RGB) -> ContrastResult:
        """
        Calculate WCAG 2.1 contrast ratio between two colors.

        Args:
            color_a, color_b: RGB tuples (0-255).

        Returns:
            ContrastResult with ratio and AA/AAA pass/fail.
        """
        lum_a = Accessibility.relative_luminance(color_a)
        lum_b = Accessibility.relative_luminance(color_b)

        lighter = max(lum_a, lum_b)
        darker = min(lum_a, lum_b)
        ratio = (lighter + 0.05) / (darker + 0.05)

        return ContrastResult(
            ratio=ratio,
            aa_normal=ratio >= 4.5,
            aa_large=ratio >= 3.0,
            aaa_normal=ratio >= 7.0,
            aaa_large=ratio >= 4.5,
        )

    # ------------------------------------------------------------------
    # Color Blindness Simulation
    # ------------------------------------------------------------------
    # Matrices from Machado, Oliveira & Fernandes (2009) at full severity.
    # Each transforms linear RGB to simulated linear RGB.

    # Protanopia (red-blind)
    _PROTAN = (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    )

    # Deuteranopia (green-blind)
    _DEUTAN = (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    )

    # Tritanopia (blue-blind)
    _TRITAN = (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    )

    # Achromatopsia (total color blindness) -- luminance only
    _ACHROM = (
        (0.2126, 0.7152, 0.0722),
        (0.2126, 0.7152, 0.0722),
        (0.2126, 0.7152, 0.0722),
    )

    _MATRICES: dict[str, tuple] = {
        "protanopia": _PROTAN,
        "deuteranopia": _DEUTAN,
        "tritanopia": _TRITAN,
        "achromatopsia": _ACHROM,
    }

    SIMULATION_MODES: list[str] = [
        "none",
        "protanopia",
        "deuteranopia",
        "tritanopia",
        "achromatopsia",
    ]

    @staticmethod
    def simulate(rgb: RGB, mode: str) -> RGB:
        """
        Simulate how a color appears under a color vision deficiency.

        Args:
            rgb: Original color (0-255).
            mode: One of 'protanopia', 'deuteranopia', 'tritanopia',
                  'achromatopsia', or 'none' (returns input unchanged).

        Returns:
            Simulated RGB color (0-255).
        """
        if mode == "none" or mode not in Accessibility._MATRICES:
            return rgb

        matrix = Accessibility._MATRICES[mode]

        # Linearize sRGB
        def lin(c: int) -> float:
            s = c / 255.0
            return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

        r, g, b = lin(rgb[0]), lin(rgb[1]), lin(rgb[2])

        # Apply matrix
        nr = matrix[0][0] * r + matrix[0][1] * g + matrix[0][2] * b
        ng = matrix[1][0] * r + matrix[1][1] * g + matrix[1][2] * b
        nb = matrix[2][0] * r + matrix[2][1] * g + matrix[2][2] * b

        # Inverse gamma (back to sRGB)
        def delin(c: float) -> int:
            c = max(0.0, min(1.0, c))
            s = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1.0 / 2.4)) - 0.055
            return max(0, min(255, int(s * 255 + 0.5)))

        return (delin(nr), delin(ng), delin(nb))

    @staticmethod
    def simulate_palette(colors: list[RGB], mode: str) -> list[RGB]:
        """Simulate an entire palette under a color vision deficiency."""
        if mode == "none":
            return list(colors)
        return [Accessibility.simulate(c, mode) for c in colors]
