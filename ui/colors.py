"""
RNV Color Palette Manager - Color Definitions
Centralized color palette for consistent theming.

All theme colors are defined here as the single source of truth.
ThemeManager imports these dictionaries rather than defining them inline.

Version: 3.0 (Full color centralization - all UI, data, and export colors)
"""
from __future__ import annotations

from typing import Final, Literal


# ==================== Type Aliases ====================
type ThemeName = Literal['dark', 'light', 'image']
type ThemeDict = dict[str, str]


# ==================== Brand Colors ====================
# Mirrored from RNVizion/rnv-brand engine/brand.py. Do not hand-write a gold
# here -- derive it, so a change to the base carries.
#
# The register holds TWO golds and derives the rest. Light spends its
# derivative on TEXT by necessity: BRAND_DARK_GOLD clears 4.5:1 as text on pure
# white and nothing else, and a gold light enough for #f5f5f5 can no longer
# take white as a fill. Dark spends one on HOVER by choice -- BRAND_GOLD alone
# clears every dark ground from 6.15 to 11.35.
#
# COVERAGE BOUNDARY: BRAND_DARK_GOLD_DEEP carries text down to #e8e8e8 and no
# further. Below that, gold does not carry text. That is a ruling, not a gap.


def _to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def lighten(hex_color: str, step: int) -> str:
    """Shift every channel by the same number of 8-bit steps.

    Uniform per-channel holds hue exactly -- BRAND_DARK_GOLD and its derivative
    both measure 42.4 degrees. Non-uniform steps do not, which is why every
    hand-written variant across these apps drifted.
    """
    r, g, b = _to_rgb(hex_color)
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, c + step)) for c in (r, g, b))


BRAND_GOLD: Final[str] = "#d2bc93"
"""Primary brand gold - dark-mode accents, hovers, group titles, highlights."""

BRAND_DARK_GOLD: Final[str] = "#8c7337"
"""Light-mode gold - fills, borders, pressed. Darker BECAUSE the ground is
lighter, which is the opposite of what the old name suggested."""

BRAND_DARK_GOLD_DEEP: Final[str] = lighten(BRAND_DARK_GOLD, -14)
"""DERIVED -> #7e6529. The light-mode gold that carries TEXT. Not a fill:
black on it measures 3.7806, under the floor."""

BRAND_GOLD_HOVER: Final[str] = lighten(BRAND_GOLD, 13)
"""DERIVED -> #dfc9a0. The dark-mode hover gold. Hover moves AWAY from
the ground in both modes: lighter on dark, deeper on light."""

BRAND_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_GOLD)
"""Brand gold as an RGB tuple, DERIVED so it cannot drift from the hex."""

BRAND_DARK_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_DARK_GOLD)
"""Light-mode gold as an RGB tuple, DERIVED. Restating it by hand is how a
value change leaves the tuple holding the retired colour, where no hex census
can see it."""

GOLD_PROVENANCE: Final[dict[str, str]] = {
    "BRAND_GOLD": "register",
    "BRAND_DARK_GOLD": "register",
    "BRAND_DARK_GOLD_DEEP": "derived",
    "BRAND_GOLD_HOVER": "derived",
}


# ==================== Semantic UI Constants ====================
# Used directly in code that cannot access a theme dict (e.g. paintEvent)
SELECTION_OVERLAY_COLOR: Final[str] = "rgba(0,120,215,200)"
"""Blue overlay used during gradient / contrast selection modes."""

SELECTION_OVERLAY_TEXT: Final[str] = "#ffffff"
"""Text color on the selection overlay."""

SEARCH_HIGHLIGHT_COLOR: Final[tuple[int,int,int]] = (0, 255, 100)
"""Bright green border drawn on search-matching slots."""

SEARCH_DIM_OVERLAY: Final[tuple[int,int,int,int]] = (0, 0, 0, 140)
"""Semi-transparent black overlay drawn on non-matching slots."""

SLOT_BORDER_THIN_COLOR: Final[tuple[int,int,int]] = (80, 80, 80)
"""Border color for thin slot border style."""

SLOT_BORDER_THICK_COLOR: Final[tuple[int,int,int]] = (60, 60, 60)
"""Border color for thick slot border style."""

SLOT_SELECTED_COLOR: Final[tuple[int,int,int]] = BRAND_DARK_GOLD_RGB
"""Gold selection highlight border drawn on the active slot.
Uses dark gold so it is visible in both dark and light modes.
"""

SIZE_OVERLAY_BG: Final[str] = "rgba(0, 0, 0, 200)"
"""Background for the floating size/status overlay widget."""

ACCENT_PRESSED_TEXT_DARK: Final[str] = "#000000"
"""Text color when pressing a gold-accented button in dark/image themes.
Black text on gold background for contrast."""

ACCENT_PRESSED_TEXT_LIGHT: Final[str] = "#ffffff"
"""Text color when pressing a gold-accented button in light theme.
White text on dark-gold background for contrast."""

# ==================== Status Colors ====================
STATUS_ERROR: Final[str] = "#dc3545"
"""The registered error red. Not drawn by this app, which renders no error
fill -- it is here so the light value below can be DERIVED from it rather
than written down.

A written-down derivative orphans the moment its base moves. That is exactly
what happened to #c4a458, a tint of a gold that was later retired."""

STATUS_ERROR_TEXT: Final[str] = "#ff6b6b"
"""Inline error/warning label text on a DARK ground (e.g. batch export
validation).

7.5674 on this app's #000000 dialog background. Left alone by the error-red
pass: dark values that already clear the floor are not replaced to buy
uniformity."""

STATUS_ERROR_TEXT_LIGHT: Final[str] = lighten(STATUS_ERROR, -20)  # -> #c82131
"""The same label on a LIGHT ground.

STATUS_ERROR_TEXT reads 2.5454 on #f5f5f5 -- below the 4.5 text floor and
below even the 3.0 UI floor. This reads 5.1811, and clears 4.5:1 down to
#e8e8e8, the same coverage boundary BRAND_DARK_GOLD_DEEP publishes.

No red carries text at 4.5:1 on a real light panel, so light spends a
derivative on TEXT for exactly the reason the gold does: the fill and text
jobs occupy non-overlapping luminance bands. A uniform per-channel step holds
hue at 354.25 degrees, identical to the base."""

CHECKBOX_ACCENT: Final[str] = "#0078d4"
"""Checkbox checked state and progress bar fill accent."""

# ==================== Preview & History Borders ====================
PREVIEW_GRID_BORDER: Final[tuple[int, int, int]] = (0, 0, 0)
"""Border color for grid cells in the preview grid widget."""

HISTORY_SWATCH_BORDER: Final[tuple[int, int, int]] = (80, 80, 80)
"""Border color for color history swatch thumbnails."""

# ==================== Structural / Data Colors ====================
# These colors are used in non-themed contexts (file export, data defaults,
# transparent fills) and exist here for single-source-of-truth consistency.

SVG_EXPORT_BG: Final[str] = "#ffffff"
"""Background rectangle fill in exported SVG palette files."""

SVG_EXPORT_STROKE: Final[str] = "#000000"
"""Swatch stroke color in exported SVG palette files."""

SVG_EXPORT_TEXT_LIGHT: Final[str] = "#ffffff"
"""Text color on dark swatches in exported SVG palette files."""

SVG_EXPORT_TEXT_DARK: Final[str] = "#000000"
"""Text color on light swatches in exported SVG palette files."""

DATA_DEFAULT_COLOR: Final[str] = "#000000"
"""Default hex value for data records (e.g. color history entries)."""

SESSION_FALLBACK_COLOR: Final[str] = "#a9a9a9"
"""Default grey hex for session restore and settings defaults."""

SESSION_FALLBACK_COLOR_IMAGE: Final[str] = "#000000"
"""Black hex fallback for image mode settings defaults."""

TRANSPARENT_RGBA: Final[tuple[int, int, int, int]] = (0, 0, 0, 0)
"""Fully transparent RGBA - used for ghost pixmaps, palette clears, etc."""

IMAGE_PREVIEW_BORDER: Final[str] = "#666666"
"""Border color for the image preview frame in the upload dialog."""

IMAGE_PREVIEW_BG: Final[str] = "#f0f0f0"
"""Background color for the image preview frame in the upload dialog."""

TEXTEDIT_BG_DARK: Final[str] = "#000000"
"""QTextEdit background in dark-themed dialogs."""

TEXTEDIT_BG_LIGHT: Final[str] = "#ffffff"
"""QTextEdit background in light-themed dialogs."""

# ==================== Default Slot Colors ====================
DEFAULT_SLOT_COLOR: Final[str] = "#a9a9a9"
"""Default color for new color slots in Dark/Light mode (darkgrey)."""

DEFAULT_SLOT_COLOR_IMAGE: Final[str] = "rgba(0, 0, 0, 171)"
"""Default color for new color slots in Image mode (semi-transparent black)."""

DEFAULT_SLOT_COLOR_IMAGE_RGB: Final[tuple[int, int, int, int]] = (0, 0, 0, 171)
"""Default slot color in Image mode as RGBA tuple."""


# ==================== Dark Theme Colors ====================
DARK_THEME_COLORS: Final[ThemeDict] = {
    'name': 'Dark',
    # Base colors
    'window_bg': '#000000',
    'panel_bg': '#1a1a1a',
    'scroll_bg': '#000000',
    'card_bg': '#2a2a2a',
    'input_bg': '#2a2a2a',
    # Text
    'text_color': '#e0e0e0',
    # NOT CONSUMED. Nothing paints this key -- ui/settings_dialog.py reads it
    # into a local and never uses that local, which is why a grep for it looks
    # live. Aligned to the value the apps that DO paint a muted text use, so
    # wiring it up stays one line and not a colour decision.
    'text_secondary': '#888888',
    'text_disabled': '#555555',
    # Borders
    'border_color': '#333333',
    'hover_color': '#444444',
    # Buttons
    'button_bg': '#1a1a1a',
    'button_text': '#e0e0e0',
    'button_hover_bg': '#333333',
    'button_hover_text': '#e0e0e0',
    'button_pressed_bg': '#444444',
    'button_pressed_text': '#000000',
    'button_border_color': 'transparent',
    # Dialog / tab widget colors
    'tab_bg': '#2a2a2a',
    'tab_selected': '#333333',
    'tab_hover': '#3a3a3a',
    'tab_pane_bg': '#1a1a1a',
    'scroll_handle': '#505050',
    # Accent (brand gold)
    'accent': BRAND_GOLD,
    'accent_dark': BRAND_GOLD_HOVER,
    'accent_ink': BRAND_GOLD,
    'accent_text': '#000000',
    # Scrollbar
    'scrollbar_bg': '#1a1a1a',
    'scrollbar_handle': '#505050',
    'scrollbar_handle_hover': '#606060',
    'scrollbar_border': '#333333',
    # Dialog
    'dialog_bg': '#1a1a1a',
    'dialog_border': '#333333',
    # Status
    'success': '#4caf50',
    'warning': '#ffc107',
}


# ==================== Light Theme Colors ====================
LIGHT_THEME_COLORS: Final[ThemeDict] = {
    'name': 'Light',
    # Base colors
    'window_bg': '#f5f5f5',
    'panel_bg': '#eeeeee',
    'scroll_bg': '#eeeeee',
    'card_bg': '#ffffff',
    'input_bg': '#ffffff',
    # Text
    'text_color': '#000000',
    # NOT CONSUMED -- see the note in the dark palette.
    'text_secondary': '#666666',
    'text_disabled': '#aaaaaa',
    # Borders
    'border_color': '#cccccc',
    'hover_color': '#e0e0e0',
    # Buttons: white base, dark-grey hover/press, white text on press, no visible border
    'button_bg': '#ffffff',
    'button_text': '#000000',
    'button_hover_bg': '#333333',
    'button_hover_text': '#000000',
    'button_pressed_bg': '#444444',
    'button_pressed_text': '#ffffff',
    'button_border_color': 'transparent',
    # Dialog / tab widget colors
    'tab_bg': '#e0e0e0',
    'tab_selected': '#ffffff',
    'tab_hover': '#d0d0d0',
    'tab_pane_bg': '#ffffff',
    'scroll_handle': '#aaaaaa',
    # Accent (brand gold - darker variant for readability on light bg)
    'accent': BRAND_DARK_GOLD,
    'accent_dark': BRAND_DARK_GOLD,
    'accent_ink': BRAND_DARK_GOLD_DEEP,
    'accent_text': '#000000',
    # Scrollbar
    'scrollbar_bg': '#f5f5f5',
    'scrollbar_handle': '#aaaaaa',
    'scrollbar_handle_hover': '#888888',
    'scrollbar_border': '#cccccc',
    # Dialog
    'dialog_bg': '#f5f5f5',
    'dialog_border': '#cccccc',
    # Status
    'success': '#4caf50',
    'warning': '#ffc107',
}


# ==================== Image Mode Colors ====================
# Based on Dark theme with transparency for background overlay effect.
IMAGE_MODE_COLORS: Final[ThemeDict] = {
    'name': 'Image',
    # Base colors -- alpha-prefixed hex for Qt stylesheet compatibility
    'window_bg': '#ED000000',
    'panel_bg': '#ED1A1A1A',
    'scroll_bg': '#ED000000',
    'card_bg': '#2a2a2a',
    'input_bg': '#2a2a2a',
    # Text
    'text_color': '#e0e0e0',
    # NOT CONSUMED -- see the note in the dark palette.
    'text_secondary': '#888888',
    'text_disabled': '#555555',
    # Borders
    'border_color': '#333333',
    'hover_color': '#444444',
    # Buttons
    'button_bg': '#1a1a1a',
    'button_text': '#e0e0e0',
    'button_hover_bg': '#333333',
    'button_hover_text': '#e0e0e0',
    'button_pressed_bg': '#444444',
    'button_pressed_text': '#000000',
    'button_border_color': 'transparent',
    # Dialog / tab widget colors
    'tab_bg': '#2a2a2a',
    'tab_selected': '#333333',
    'tab_hover': '#3a3a3a',
    'tab_pane_bg': '#1a1a1a',
    'scroll_handle': '#505050',
    # Accent (brand gold)
    'accent': BRAND_GOLD,
    'accent_dark': BRAND_GOLD_HOVER,
    'accent_ink': BRAND_GOLD,
    'accent_text': '#000000',
    # Scrollbar -- uses rgba in CSS strings, not here
    'scrollbar_bg': 'transparent',
    'scrollbar_handle': 'rgba(80, 80, 80, 100)',
    'scrollbar_handle_hover': 'rgba(80, 80, 80, 120)',
    'scrollbar_border': 'rgba(51, 51, 51, 100)',
    # Dialog
    'dialog_bg': '#1a1a1a',
    'dialog_border': '#333333',
    # Status
    'success': '#4caf50',
    'warning': '#ffc107',
}


# ==================== Theme Lookup ====================

_THEME_MAP: Final[dict[ThemeName, ThemeDict]] = {
    'dark': DARK_THEME_COLORS,
    'light': LIGHT_THEME_COLORS,
    'image': IMAGE_MODE_COLORS,
}


def get_theme_colors(theme_name: ThemeName = 'dark') -> ThemeDict:
    """
    Get the color palette for the specified theme.

    Args:
        theme_name: One of 'dark', 'light', or 'image'.

    Returns:
        Dictionary of color definitions for the requested theme.
        Returns a copy so callers cannot mutate the originals.

    Example:
        colors = get_theme_colors('dark')
        bg = colors['window_bg']  # '#000000'
    """
    return _THEME_MAP.get(theme_name, DARK_THEME_COLORS).copy()


def is_dark_theme(theme_name: ThemeName) -> bool:
    """
    Check if a theme name corresponds to a dark-background theme.

    Args:
        theme_name: Theme identifier.

    Returns:
        True for 'dark' and 'image' themes, False for 'light'.
    """
    return theme_name != 'light'


# ==================== Exports ====================
__all__ = [
    # Type aliases
    "ThemeName",
    "ThemeDict",
    # Brand colors
    "BRAND_GOLD",
    "BRAND_DARK_GOLD",
    "BRAND_GOLD_RGB",
    "BRAND_DARK_GOLD_RGB",
    # Slot defaults
    "DEFAULT_SLOT_COLOR",
    "DEFAULT_SLOT_COLOR_IMAGE",
    "DEFAULT_SLOT_COLOR_IMAGE_RGB",
    # Theme dictionaries
    "DARK_THEME_COLORS",
    "LIGHT_THEME_COLORS",
    "IMAGE_MODE_COLORS",
    # Semantic UI constants
    "SELECTION_OVERLAY_COLOR",
    "SELECTION_OVERLAY_TEXT",
    "SEARCH_HIGHLIGHT_COLOR",
    "SEARCH_DIM_OVERLAY",
    "SLOT_BORDER_THIN_COLOR",
    "SLOT_BORDER_THICK_COLOR",
    "SLOT_SELECTED_COLOR",
    "SIZE_OVERLAY_BG",
    # Accent pressed-text
    "ACCENT_PRESSED_TEXT_DARK",
    "ACCENT_PRESSED_TEXT_LIGHT",
    # Status colors
    "STATUS_ERROR",
    "STATUS_ERROR_TEXT",
    "STATUS_ERROR_TEXT_LIGHT",
    "CHECKBOX_ACCENT",
    # Preview & history borders
    "PREVIEW_GRID_BORDER",
    "HISTORY_SWATCH_BORDER",
    # Structural / data colors
    "SVG_EXPORT_BG",
    "SVG_EXPORT_STROKE",
    "SVG_EXPORT_TEXT_LIGHT",
    "SVG_EXPORT_TEXT_DARK",
    "DATA_DEFAULT_COLOR",
    "SESSION_FALLBACK_COLOR",
    "SESSION_FALLBACK_COLOR_IMAGE",
    "TRANSPARENT_RGBA",
    "IMAGE_PREVIEW_BORDER",
    "IMAGE_PREVIEW_BG",
    "TEXTEDIT_BG_DARK",
    "TEXTEDIT_BG_LIGHT",
    # Functions
    "get_theme_colors",
    "is_dark_theme",
]