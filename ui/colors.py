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


# ==================== APP Neutrals ====================
#
# MIRRORED FROM RNVizion/rnv-brand engine/brand.py APP. Until 2026-08-28 these
# were bare hex literals in the palettes below -- no constant, no provenance --
# and every one is a REGISTERED brand value. A registered value could move
# upstream and this app would keep the old one silently, which is the failure
# #c4a458 had, one level down. It nearly happened: APP["text"] moved from
# #e0e0e0 to #dddddd in rnv-brand@68d195e.
#
# THE INK GRID, published in the brand beside that move:
#
#     grey(n) = n * 0x11, n in 0..15.   TRUE_BLACK -> WHITE in fifteen steps.
#
# IT GOVERNS INKS AND EDGES AND DELIBERATELY DOES NOT GOVERN SURFACES.
# BRAND_BLACK sits at n = 1.53 and APP_CARD at n = 2.47; BRAND_BLACK is a
# permanent and will not move to fit a ladder. The scope is part of the rule.
#
# THIS PASS WIRES THE INK ONLY. The other five constants are defined and
# mirrored so drift is caught, but the palettes still spell them as literals;
# rewiring those is the grey-ramp derivation pass. Mixing a mechanical
# substitution into a value change makes both unreadable.

TRUE_BLACK: Final[str] = "#000000"
"""engine/brand.py TRUE_BLACK, and APP["window"]. Primary text in light mode,
and the label on a pressed control in dark. grey(0)."""

WHITE: Final[str] = "#ffffff"
"""engine/brand.py WHITE. Control surface in light mode. grey(15)."""

BRAND_BLACK: Final[str] = "#1a1a1a"
"""engine/brand.py BRAND_BLACK, and APP["panel"]. Charcoal; a permanent.
Not on the ink grid (n = 1.53) and not required to be -- it is a surface."""

APP_CARD: Final[str] = "#2a2a2a"
"""engine/brand.py APP["card"]. A surface, not on the grid (n = 2.47)."""

APP_BORDER: Final[str] = "#333333"
"""engine/brand.py APP["border"]. grey(3). An edge, so the grid governs it."""

APP_TEXT: Final[str] = "#dddddd"
"""engine/brand.py APP["text"]. grey(13). Primary ink in dark and image mode.

MOVED FROM #e0e0e0 ON 2026-08-28, with the brand rather than after it.
#e0e0e0 was one hex doing two unrelated jobs -- ink in dark mode, and a light
SURFACE in the light palette below (hover_color and tab_bg). It refused to sit
on the grid because the grid governs inks and half its uses were not ink. Only
the ink half moved. Contrast falls 0.21 to 0.45 and the floor afterwards is
7.17:1 on the pressed plate #444444, the darkest ground it is drawn on.
"""

APP_TEXT_DIM: Final[str] = "#aaaaaa"
"""engine/brand.py APP["text-dim"]. grey(10)."""

APP_PANEL_HOVER: Final[str] = "#3a3a3a"
"""engine/brand.py APP["panel-hover"]. The n=+2 rung of the dark surface
ladder, and the dark interaction plate.

REGISTERED 2026-08-29 in rnv-brand rev 22, app-owned here until then.

    BRAND_BLACK + n * 0x10,  n in -1..+2
    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover

The register had called the ladder "two-thirds specified" because APP_BORDER
#333333 is not #3a3a3a and so looked like a missing rung. It is not a rung at
all: #333333 is grey(3) on the INK grid, which governs inks and EDGES, and a
border is an edge. The ladder was complete when the question was first asked.
"""

APP_HOVER_LIGHT: Final[str] = "#eeeeee"
"""engine/brand.py APP["hover-light"]. grey(14). The light interaction plate.

THIS ONE MOVES A PIXEL, and it is the only thing in this pass that does.

The light dialog-button and tab hover plates were #d0d0d0. rnv-brand RETIRED
that value as a light interaction ground: the About dialog draws the hover
label in BRAND_DARK_GOLD_DEEP #7e6529, which measures 3.6013:1 on #d0d0d0
against a 4.5 floor. The defect was pre-existing and had been marked with a
strict xfail since the 2026-08-28 ink pass, awaiting exactly this ruling.

    #d0d0d0   3.6013   fails      <- what shipped
    #e0e0e0   4.2078   fails
    #e8e8e8   4.5334   clears by 0.0334
    #eeeeee   4.7875   clears by 0.2875   <- this value

Registered 2026-08-29 as #e8e8e8 and moved to #eeeeee on 2026-08-30 in rev 23.
#e8e8e8 is the ground BRAND_DARK_GOLD_DEEP is calibrated against -- rev 24
registered it as GOLD_TEXT_GROUND_FLOOR for that reason -- so putting the hover
plate on it would have pinned every hover to the one value the gold cannot
afford to lose. A boundary is not a plate.
"""

IMAGE_OVERLAY_ALPHA: Final[str] = "ED"
"""The alpha byte image mode composites its chrome at -- 0xED, about 93%.

WHY THE OVERLAYS BELOW ARE WRITTEN OUT RATHER THAN COMPOSED. Qt wants the
eight-digit #AARRGGBB form, and building it from the six-digit constant would
make the palette entries resolve to an expression rather than a value, which
this app's own before/after comparison cannot check. The relationship is
asserted in tests/test_ladder_and_plate.py instead: each overlay's last six
digits must BE the register value it claims, and its alpha byte must be this
one. If the register moves a base, those tests fail and these move with it.

THEY WERE INVISIBLE BEFORE. The 2026-08-29 wiring pass claimed no registered
value was left spelled as a literal in a dark palette. That was true of
six-digit spellings only: its sweep compared whole strings, so #ED000000 never
matched #000000, and three of these sat in IMAGE_MODE_COLORS -- which is a DARK
dict here -- while the test reported clean.
"""

APP_WINDOW_OVERLAY: Final[str] = "#ED000000"
"""TRUE_BLACK, and APP["window"], at IMAGE_OVERLAY_ALPHA."""

APP_PANEL_OVERLAY: Final[str] = "#ED1A1A1A"
"""BRAND_BLACK, and APP["panel"], at IMAGE_OVERLAY_ALPHA."""
APP_PROVENANCE: Final[dict[str, str]] = {
    "TRUE_BLACK": "register",
    "WHITE": "register",
    "BRAND_BLACK": "register",
    "APP_CARD": "register",
    "APP_BORDER": "register",
    "APP_TEXT": "register",
    "APP_TEXT_DIM": "register",
    "APP_PANEL_HOVER": "register",
    "APP_HOVER_LIGHT": "register",
    "APP_WINDOW_OVERLAY": "register-overlay",
    "APP_PANEL_OVERLAY": "register-overlay",
}
"""Declarative, and read by tests/test_app_mirror.py, in the same shape as
GOLD_PROVENANCE above. A classification that lives only in a test drifts from
the thing it classifies."""

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
    'window_bg': TRUE_BLACK,
    'panel_bg': BRAND_BLACK,
    'scroll_bg': TRUE_BLACK,
    'card_bg': APP_CARD,
    'input_bg': BRAND_BLACK,
    # Text
    'text_color': APP_TEXT,
    # NOT CONSUMED. Nothing paints this key -- ui/settings_dialog.py reads it
    # into a local and never uses that local, which is why a grep for it looks
    # live. Aligned to the value the apps that DO paint a muted text use, so
    # wiring it up stays one line and not a colour decision.
    'text_secondary': '#888888',
    'text_disabled': '#555555',
    # Borders
    'border_color': APP_BORDER,
    'hover_color': '#444444',
    # Buttons
    'button_bg': BRAND_BLACK,
    'button_text': APP_TEXT,
    'button_hover_bg': APP_BORDER,
    'button_hover_text': APP_TEXT,
    'button_pressed_bg': '#444444',
    'button_pressed_text': TRUE_BLACK,
    'button_border_color': 'transparent',
    # The About dialog's button hover plate. Spelled 'tab_hover' until
    # 2026-08-28, where it filled a QPushButton and not a tab.
    #
    # Deliberately NOT button_hover_bg. That is the MAIN button's inverse
    # scheme -- #333333 in both modes, with the label flipping -- while dialog
    # buttons take a softer plate carrying gold text and a gold border.
    # Flattening the two would lose a scheme. Same value it always had.
    'dialog_btn_hover_bg': APP_PANEL_HOVER,
    # Dialog / tab widget colors
    #
    # NOT CONSUMED -- all three of these. This app paints its tabs from
    # card_bg (at rest AND on hover, so hovering an unselected tab changes
    # only the label) and from panel_bg for the selected one, in both
    # ui/about_dialog.py and ui/settings_dialog.py.
    #
    # Kept rather than deleted, on the same reasoning as text_secondary above:
    # rnv-color-picker and rnv-icon-builder DO paint from the equivalents, and
    # the values here already agree with them -- tab_bg matches both apps, and
    # tab_selected_bg matches rnv-icon-builder (rnv-color-picker uses the panel
    # step #1a1a1a instead, a two-against-one this pass records and does not
    # settle). So wiring them up stays one line and not a colour decision.
    #
    # RENAMED 2026-08-28 to the spelling those two apps use. `tab_hover` left
    # this block entirely: it was consumed, but to fill a QPushButton, and it
    # is now dialog_btn_hover_bg in the button section above.
    'tab_bg': APP_CARD,
    'tab_selected_bg': APP_BORDER,
    'tab_hover_bg': APP_PANEL_HOVER,
    'scroll_handle': '#505050',
    # Accent (brand gold)
    'accent': BRAND_GOLD,
    'accent_dark': BRAND_GOLD_HOVER,
    'accent_ink': BRAND_GOLD,
    'accent_text': TRUE_BLACK,
    # Scrollbar
    'scrollbar_bg': BRAND_BLACK,
    'scrollbar_handle': '#505050',
    'scrollbar_handle_hover': '#606060',
    'scrollbar_border': APP_BORDER,
    # Dialog
    'dialog_bg': BRAND_BLACK,
    'dialog_border': APP_BORDER,
    # Status
    'success': '#4caf50',
    'warning': '#ffc107',
}


# ==================== Light Theme Colors ====================
LIGHT_THEME_COLORS: Final[ThemeDict] = {
    'name': 'Light',
    # Base colors
    'window_bg': '#f5f5f5',
    'panel_bg': '#f5f5f5',
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
    # The About dialog's button hover plate. Spelled 'tab_hover' until
    # 2026-08-28, where it filled a QPushButton and not a tab.
    #
    # Deliberately NOT button_hover_bg. That is the MAIN button's inverse
    # scheme -- #333333 in both modes, with the label flipping -- while dialog
    # buttons take a softer plate carrying gold text and a gold border.
    # Flattening the two would lose a scheme. Same value it always had.
    'dialog_btn_hover_bg': APP_HOVER_LIGHT,
    # Dialog / tab widget colors
    #
    # NOT CONSUMED -- all three of these. This app paints its tabs from
    # card_bg (at rest AND on hover, so hovering an unselected tab changes
    # only the label) and from panel_bg for the selected one, in both
    # ui/about_dialog.py and ui/settings_dialog.py.
    #
    # Kept rather than deleted, on the same reasoning as text_secondary above:
    # rnv-color-picker and rnv-icon-builder DO paint from the equivalents, and
    # the values here already agree with them -- tab_bg matches both apps, and
    # tab_selected_bg matches rnv-icon-builder (rnv-color-picker uses the panel
    # step #1a1a1a instead, a two-against-one this pass records and does not
    # settle). So wiring them up stays one line and not a colour decision.
    #
    # RENAMED 2026-08-28 to the spelling those two apps use. `tab_hover` left
    # this block entirely: it was consumed, but to fill a QPushButton, and it
    # is now dialog_btn_hover_bg in the button section above.
    'tab_bg': '#e0e0e0',
    'tab_selected_bg': '#ffffff',
    'tab_hover_bg': APP_HOVER_LIGHT,
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
    'window_bg': APP_WINDOW_OVERLAY,
    'panel_bg': APP_PANEL_OVERLAY,
    'scroll_bg': APP_WINDOW_OVERLAY,
    'card_bg': APP_CARD,
    'input_bg': APP_CARD,
    # Text
    'text_color': APP_TEXT,
    # NOT CONSUMED -- see the note in the dark palette.
    'text_secondary': '#888888',
    'text_disabled': '#555555',
    # Borders
    'border_color': APP_BORDER,
    'hover_color': '#444444',
    # Buttons
    'button_bg': BRAND_BLACK,
    'button_text': APP_TEXT,
    'button_hover_bg': APP_BORDER,
    'button_hover_text': APP_TEXT,
    'button_pressed_bg': '#444444',
    'button_pressed_text': TRUE_BLACK,
    'button_border_color': 'transparent',
    # The About dialog's button hover plate. Spelled 'tab_hover' until
    # 2026-08-28, where it filled a QPushButton and not a tab.
    #
    # Deliberately NOT button_hover_bg. That is the MAIN button's inverse
    # scheme -- #333333 in both modes, with the label flipping -- while dialog
    # buttons take a softer plate carrying gold text and a gold border.
    # Flattening the two would lose a scheme. Same value it always had.
    'dialog_btn_hover_bg': APP_PANEL_HOVER,
    # Dialog / tab widget colors
    #
    # NOT CONSUMED -- all three of these. This app paints its tabs from
    # card_bg (at rest AND on hover, so hovering an unselected tab changes
    # only the label) and from panel_bg for the selected one, in both
    # ui/about_dialog.py and ui/settings_dialog.py.
    #
    # Kept rather than deleted, on the same reasoning as text_secondary above:
    # rnv-color-picker and rnv-icon-builder DO paint from the equivalents, and
    # the values here already agree with them -- tab_bg matches both apps, and
    # tab_selected_bg matches rnv-icon-builder (rnv-color-picker uses the panel
    # step #1a1a1a instead, a two-against-one this pass records and does not
    # settle). So wiring them up stays one line and not a colour decision.
    #
    # RENAMED 2026-08-28 to the spelling those two apps use. `tab_hover` left
    # this block entirely: it was consumed, but to fill a QPushButton, and it
    # is now dialog_btn_hover_bg in the button section above.
    'tab_bg': APP_CARD,
    'tab_selected_bg': APP_BORDER,
    'tab_hover_bg': APP_PANEL_HOVER,
    'scroll_handle': '#505050',
    # Accent (brand gold)
    'accent': BRAND_GOLD,
    'accent_dark': BRAND_GOLD_HOVER,
    'accent_ink': BRAND_GOLD,
    'accent_text': TRUE_BLACK,
    # Scrollbar -- uses rgba in CSS strings, not here
    'scrollbar_bg': 'transparent',
    'scrollbar_handle': 'rgba(80, 80, 80, 100)',
    'scrollbar_handle_hover': 'rgba(80, 80, 80, 120)',
    'scrollbar_border': 'rgba(51, 51, 51, 100)',
    # Dialog
    'dialog_bg': BRAND_BLACK,
    'dialog_border': APP_BORDER,
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