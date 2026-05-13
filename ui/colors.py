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
BRAND_GOLD: Final[str] = "#d2bc93"
"""Primary brand gold - use for hover accents, group titles, highlights."""

BRAND_GOLD_DARK: Final[str] = "#b19145"
"""Darker gold - use for borders, pressed states, light-mode accents."""

BRAND_GOLD_RGB: Final[tuple[int, int, int]] = (210, 188, 147)
"""Brand gold as RGB tuple."""

BRAND_GOLD_DARK_RGB: Final[tuple[int, int, int]] = (177, 145, 69)
"""Dark brand gold as RGB tuple."""


# ==================== Semantic UI Constants ====================
# Used directly in code that cannot access a theme dict (e.g. paintEvent)
SELECTION_OVERLAY_COLOR: Final[str] = "rgba(0,120,215,200)"
"""Blue overlay used during gradient / contrast selection modes."""

SELECTION_OVERLAY_TEXT: Final[str] = "#FFFFFF"
"""Text color on the selection overlay."""

SEARCH_HIGHLIGHT_COLOR: Final[tuple[int,int,int]] = (0, 255, 100)
"""Bright green border drawn on search-matching slots."""

SEARCH_DIM_OVERLAY: Final[tuple[int,int,int,int]] = (0, 0, 0, 140)
"""Semi-transparent black overlay drawn on non-matching slots."""

SLOT_BORDER_THIN_COLOR: Final[tuple[int,int,int]] = (80, 80, 80)
"""Border color for thin slot border style."""

SLOT_BORDER_THICK_COLOR: Final[tuple[int,int,int]] = (60, 60, 60)
"""Border color for thick slot border style."""

SLOT_SELECTED_COLOR: Final[tuple[int,int,int]] = BRAND_GOLD_DARK_RGB
"""Gold selection highlight border drawn on the active slot.
Uses dark gold so it is visible in both dark and light modes.
"""

SIZE_OVERLAY_BG: Final[str] = "rgba(0, 0, 0, 200)"
"""Background for the floating size/status overlay widget."""

ACCENT_PRESSED_TEXT_DARK: Final[str] = "#000000"
"""Text color when pressing a gold-accented button in dark/image themes.
Black text on gold background for contrast."""

ACCENT_PRESSED_TEXT_LIGHT: Final[str] = "#FFFFFF"
"""Text color when pressing a gold-accented button in light theme.
White text on dark-gold background for contrast."""

# ==================== Status Colors ====================
STATUS_ERROR_TEXT: Final[str] = "#ff6b6b"
"""Inline error/warning label text (e.g. batch export validation)."""

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

TEXTEDIT_BG_LIGHT: Final[str] = "#FFFFFF"
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
    'panel_bg': '#1A1A1A',
    'scroll_bg': '#000000',
    'card_bg': '#2A2A2A',
    'input_bg': '#2A2A2A',
    # Text
    'text_color': '#E0E0E0',
    'text_secondary': '#AAAAAA',
    'text_disabled': '#666666',
    # Borders
    'border_color': '#333333',
    'hover_color': '#444444',
    # Buttons
    'button_bg': '#1A1A1A',
    'button_text': '#E0E0E0',
    'button_hover_bg': '#333333',
    'button_hover_text': '#E0E0E0',
    'button_pressed_bg': '#333333',
    'button_pressed_text': '#000000',
    'button_border_color': 'transparent',
    # Dialog / tab widget colors
    'tab_bg': '#2A2A2A',
    'tab_selected': '#333333',
    'tab_hover': '#3A3A3A',
    'tab_pane_bg': '#1A1A1A',
    'scroll_handle': '#505050',
    # Accent (brand gold)
    'accent': BRAND_GOLD,
    'accent_dark': BRAND_GOLD_DARK,
    'accent_text': '#000000',
    # Scrollbar
    'scrollbar_bg': '#1A1A1A',
    'scrollbar_handle': '#505050',
    'scrollbar_handle_hover': '#606060',
    'scrollbar_border': '#333333',
    # Dialog
    'dialog_bg': '#1A1A1A',
    'dialog_border': '#333333',
    # Status
    'success': '#4CAF50',
    'warning': '#FFC107',
    'error': '#F44336',
}


# ==================== Light Theme Colors ====================
LIGHT_THEME_COLORS: Final[ThemeDict] = {
    'name': 'Light',
    # Base colors
    'window_bg': '#F5F5F5',
    'panel_bg': '#EEEEEE',
    'scroll_bg': '#EEEEEE',
    'card_bg': '#FFFFFF',
    'input_bg': '#FFFFFF',
    # Text
    'text_color': '#000000',
    'text_secondary': '#555555',
    'text_disabled': '#999999',
    # Borders
    'border_color': '#CCCCCC',
    'hover_color': '#E0E0E0',
    # Buttons: white base, dark-grey hover/press, white text on press, no visible border
    'button_bg': '#FFFFFF',
    'button_text': '#000000',
    'button_hover_bg': '#333333',
    'button_hover_text': '#000000',
    'button_pressed_bg': '#333333',
    'button_pressed_text': '#FFFFFF',
    'button_border_color': 'transparent',
    # Dialog / tab widget colors
    'tab_bg': '#E0E0E0',
    'tab_selected': '#FFFFFF',
    'tab_hover': '#D0D0D0',
    'tab_pane_bg': '#FFFFFF',
    'scroll_handle': '#AAAAAA',
    # Accent (brand gold - darker variant for readability on light bg)
    'accent': BRAND_GOLD_DARK,
    'accent_dark': BRAND_GOLD_DARK,
    'accent_text': '#000000',
    # Scrollbar
    'scrollbar_bg': '#F5F5F5',
    'scrollbar_handle': '#AAAAAA',
    'scrollbar_handle_hover': '#888888',
    'scrollbar_border': '#CCCCCC',
    # Dialog
    'dialog_bg': '#F5F5F5',
    'dialog_border': '#CCCCCC',
    # Status
    'success': '#4CAF50',
    'warning': '#FFC107',
    'error': '#F44336',
}


# ==================== Image Mode Colors ====================
# Based on Dark theme with transparency for background overlay effect.
IMAGE_MODE_COLORS: Final[ThemeDict] = {
    'name': 'Image',
    # Base colors -- alpha-prefixed hex for Qt stylesheet compatibility
    'window_bg': '#ED000000',
    'panel_bg': '#ED1A1A1A',
    'scroll_bg': '#ED000000',
    'card_bg': '#2A2A2A',
    'input_bg': '#2A2A2A',
    # Text
    'text_color': '#E0E0E0',
    'text_secondary': '#AAAAAA',
    'text_disabled': '#666666',
    # Borders
    'border_color': '#333333',
    'hover_color': '#444444',
    # Buttons
    'button_bg': '#1A1A1A',
    'button_text': '#E0E0E0',
    'button_hover_bg': '#333333',
    'button_hover_text': '#E0E0E0',
    'button_pressed_bg': '#333333',
    'button_pressed_text': '#000000',
    'button_border_color': 'transparent',
    # Dialog / tab widget colors
    'tab_bg': '#2A2A2A',
    'tab_selected': '#333333',
    'tab_hover': '#3A3A3A',
    'tab_pane_bg': '#1A1A1A',
    'scroll_handle': '#505050',
    # Accent (brand gold)
    'accent': BRAND_GOLD,
    'accent_dark': BRAND_GOLD_DARK,
    'accent_text': '#000000',
    # Scrollbar -- uses rgba in CSS strings, not here
    'scrollbar_bg': 'transparent',
    'scrollbar_handle': 'rgba(80, 80, 80, 100)',
    'scrollbar_handle_hover': 'rgba(80, 80, 80, 120)',
    'scrollbar_border': 'rgba(51, 51, 51, 100)',
    # Dialog
    'dialog_bg': '#1A1A1A',
    'dialog_border': '#333333',
    # Status
    'success': '#4CAF50',
    'warning': '#FFC107',
    'error': '#F44336',
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
    "BRAND_GOLD_DARK",
    "BRAND_GOLD_RGB",
    "BRAND_GOLD_DARK_RGB",
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
    "STATUS_ERROR_TEXT",
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