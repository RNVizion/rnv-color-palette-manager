"""
Core modules for RNV Color Palette Manager.
Contains color math, slots, palette formats, metadata, color extraction,
harmonies, and accessibility utilities.
"""
from __future__ import annotations

from core.color_math import ColorMath
from core.palette_formats import PaletteFormats, ImportResult
from core.palette_metadata import PaletteMetadata
from core.color_slot import ColorSlot, ColorSlotWidget
from core.color_extractor import ColorExtractor
from core.color_harmonies import ColorHarmonies
from core.accessibility import Accessibility, ContrastResult

__all__ = [
    # Color math & conversions
    "ColorMath",
    # Palette import/export
    "PaletteFormats",
    "ImportResult",
    # Metadata
    "PaletteMetadata",
    # Color slot widgets
    "ColorSlot",
    "ColorSlotWidget",
    # Image-based color extraction
    "ColorExtractor",
    # Color harmonies & gradients
    "ColorHarmonies",
    # Accessibility (WCAG contrast & CVD simulation)
    "Accessibility",
    "ContrastResult",
]
