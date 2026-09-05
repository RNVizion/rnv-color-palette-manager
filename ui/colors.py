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

# grey(4) on the ink grid. The main button's pressed plate (ruled 2026-08-26)
# and, from 2026-09-02, the scrollbar handle -- RNV-COLLAPSE-505050: this app
# held #505050 for its handle where the other four already used #444444, and
# #505050 was on neither the ladder nor the grid. Named here for the first
# time in this app; rnv-text-transformer already calls it GREY_44.
GREY_44: Final[str] = "#444444"
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

# ── Neutral greys, named for what they are ──
# RNV-INK-RULE (2026-09-02). These were GREY_66 and
# GREY_F0 -- role names on values that four applications in the
# fleet paint with. GREY_F0 in particular is used by the picker, the icon
# builder and this app, and until now had a name in none of them.
GREY_66: Final[str] = "#666666"
GREY_F0: Final[str] = "#f0f0f0"


# ── Which ink goes on this ground ──
#
# RNV-INK-RULE (2026-09-02, ruled by Chris). Across the fleet this question
# was asked in ten places and answered three different ways, none of them a
# contrast measurement. Here it was core/palette_formats.py, choosing the
# label colour for an exported SVG swatch with sum(color) / 3 < 128.
#
# The mean is not a contrast measurement, and on saturated colour it is badly
# wrong: pure green is 71% of the luminance of white, and the mean calls it
# dark and writes WHITE on it at 1.37:1 where the right answer is black at
# 15.30:1.
#
# One rule now, stated as a real comparison rather than a threshold --
# whichever candidate has the higher contrast ratio against the ground wins.
# The same maths as the surface ladder and the 4.5 floor. rnv-color-picker
# and rnv-icon-builder carry the identical block.


def _channel(value: float) -> float:
    """One sRGB channel, 0-255, linearised."""
    c = value / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _rgb(color: "str | tuple[int, int, int]") -> tuple[int, int, int]:
    """Accept either shape. Callers hold hex strings and RGB triples both."""
    if isinstance(color, str):
        h = color.lstrip("#")
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return (int(color[0]), int(color[1]), int(color[2]))


def relative_luminance(color: "str | tuple[int, int, int]") -> float:
    """WCAG 2.x relative luminance, 0.0 (black) to 1.0 (white)."""
    r, g, b = _rgb(color)
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(a: "str | tuple[int, int, int]",
                   b: "str | tuple[int, int, int]") -> float:
    """WCAG contrast ratio between two colours, 1.0 to 21.0."""
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = (la, lb) if la >= lb else (lb, la)
    return (hi + 0.05) / (lo + 0.05)


def better_on(background: "str | tuple[int, int, int]", *candidates: str) -> str:
    """Whichever candidate reads best on this ground. Ties go to the first."""
    return max(candidates, key=lambda c: contrast_ratio(background, c))


def contrast_ink(background: "str | tuple[int, int, int]") -> str:
    """Text colour for an arbitrary ground: WHITE or TRUE_BLACK.

    For a colour the USER chose. Not for brand surfaces: what sits on a brand
    gold is a ruling, not a measurement, and the two are 0.08 apart on
    BRAND_DARK_GOLD.
    """
    return better_on(background, TRUE_BLACK, WHITE)


def prefers_dark_ink(background: "str | tuple[int, int, int]") -> bool:
    """True when TRUE_BLACK reads better on this ground than WHITE does."""
    return contrast_ink(background) == TRUE_BLACK

"""Blue overlay used during gradient / contrast selection modes."""

SEARCH_HIGHLIGHT_COLOR: Final[tuple[int,int,int]] = (0, 255, 100)
"""Bright green border drawn on search-matching slots."""

SEARCH_DIM_OVERLAY: Final[tuple[int,int,int,int]] = (0, 0, 0, 140)
"""Semi-transparent black overlay drawn on non-matching slots."""

SLOT_BORDER_THIN_COLOR: Final[tuple[int,int,int]] = (80, 80, 80)
"""Border color for thin slot border style."""

SLOT_BORDER_THICK_COLOR: Final[tuple[int,int,int]] = (60, 60, 60)
"""Border color for thick slot border style."""

SIZE_OVERLAY_BG: Final[str] = "rgba(0, 0, 0, 200)"
"""Background for the floating size/status overlay widget."""

# ==================== Status Colors ====================
STATUS_SUCCESS: Final[str] = "#926c89"
"""MIRRORS the register's STATUS["success"]. A FILL.

RNV-STATUS-FAMILY (2026-09-03): was #28a745, Bootstrap's green. Retired
because it and Bootstrap's red collapsed to one olive under deuteranopia at
about 4 apart -- roughly 8% of men could not tell success from error, which
are the two most consequential colours in an interface.

It is a FILL and cannot carry text: 3.92 on #1a1a1a, 3.23 on #2a2a2a. That is
the fill band, not a shortcoming -- a value that clears 3:1 on a dark AND a
light ground sits at L* 48-59 by arithmetic, and a mid-tone reaches 4.5:1 on
neither side. This application already knew that for the red and spent two
values on it; the register has now generalised it to all three roles.

RNV-STATUS-REGISTER (2026-09-02): the three palettes wrote #4caf50,
Material's green, as a literal. Two applications held that value for one
role while the other three used the register's. Named here so the value
has one home, and collapsed onto the register so the fleet has one green."""

STATUS_WARNING: Final[str] = "#a2703c"
"""MIRRORS the register's STATUS["warning"]. A FILL.

RNV-STATUS-FAMILY (2026-09-03): was #ffc107, retired on arithmetic rather
than taste -- 1.63 on #ffffff and 1.49 on #f5f5f5 against a 3:1 fill floor.
It could not legally carry a boundary on a light ground at all."""

STATUS_ERROR: Final[str] = "#c75b64"
"""The registered error red. Not drawn by this app, which renders no error
fill -- it is here so the family has its base and so the two text values
below are visibly siblings of it rather than free-standing reds.

RNV-STATUS-FAMILY (2026-09-03): was #dc3545, Bootstrap's. IT IS NO LONGER
WHAT THE LIGHT VALUE IS DERIVED FROM -- see STATUS_ERROR_TEXT_LIGHT."""

STATUS_ERROR_TEXT: Final[str] = "#dd6f77"
"""Inline error/warning label text on a DARK ground (e.g. batch export
validation). MIRRORS the register's STATUS["error-text"].

RNV-STATUS-FAMILY (2026-09-03): was #e56b77, which was derived from the
retired #dc3545. With that base gone it is an ORPHAN -- a value derived from
something no longer in the palette -- which is precisely the #c4a458 failure
this file's own docstrings warn about twice. It moves with its base.

    #e56b77  6.7011 on #000000   4.5801 on #2a2a2a
    #dd6f77  6.6146 on #000000   4.5210 on #2a2a2a

Slightly LESS headroom than the value it replaces -- 4.5210 against
4.5801 on the card -- and still above the floor. The gamut correction of
2026-09-04 moved the whole red family a byte or so; the direction of that
half-point is worth stating rather than rounding away.

RNV-STATUS-REGISTER (2026-09-02): before #e56b77 this was #ff6b6b, and being
left alone was a RULING rather than an oversight -- the error-red pass held
that a dark value already clearing the floor should not be replaced to buy
uniformity. That argument was right when the register had no name for this
job. It now does, and a fourth spelling of a registered colour costs more
than the headroom does."""

STATUS_ERROR_TEXT_LIGHT: Final[str] = "#b84e58"
"""The same label on a LIGHT ground. MIRRORS STATUS["error-text-light"].

STATUS_ERROR_TEXT reads 2.8367 on #f5f5f5 -- below the 4.5 text floor and
below even the 3.0 UI floor. This reads 4.5123. No red carries text at 4.5:1
on a real light panel, so light spends a value on TEXT for exactly the reason
the gold does: the fill and text jobs occupy non-overlapping luminance bands.

WRITTEN DOWN, NOT DERIVED, AND THAT IS A CHANGE. This was
lighten(STATUS_ERROR, -20), and the test beside it argued -- correctly -- that
a written-down derivative orphans the moment its base moves. That argument is
why the value is not silently kept: against the new base the formula yields
#b44753, which is neither the old #c82131 nor the registered #b84e58. A
derivative whose rule no longer produces it is not a derivative, it is a
coincidence waiting to break.

The register's family derivation is a different rule -- hold hue and chroma,
move lightness only, take the first step that clears 4.5 on the worst ground
-- and it publishes the RESULT with the walk as provenance, so that retuning
the rule cannot silently change what an error looks like in five
applications. Same call the register made for BRAND_STANDBY_GOLD.

RNV-STATUS-LIGHT-FLOOR: this value does NOT reach the coverage boundary its
predecessor did. #c82131 read 4.6100 on #e8e8e8; #b84e58 reads 4.0150 there
and 4.2401 on APP hover-light #eeeeee. The register walks its light variants
against #f5f5f5 as "the worst light ground", and rev 27 put three registered
rungs below it. The question is open with the brand chat; if it re-walks
against #e8e8e8 the answer here is #ae4650, moving 3.1 -- well inside the
register's own 8.40 threshold, so it would stay the same red."""

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

DATA_DEFAULT_COLOR: Final[str] = "#000000"
"""Default hex value for data records (e.g. color history entries)."""

SESSION_FALLBACK_COLOR: Final[str] = "#a9a9a9"
"""Default grey hex for session restore and settings defaults."""

SESSION_FALLBACK_COLOR_IMAGE: Final[str] = "#000000"
"""Black hex fallback for image mode settings defaults."""

TRANSPARENT_RGBA: Final[tuple[int, int, int, int]] = (0, 0, 0, 0)
"""Fully transparent RGBA - used for ghost pixmaps, palette clears, etc."""

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
    'hover_color': GREY_44,
    # Buttons
    'main_btn_bg': BRAND_BLACK,
    'main_btn_text': APP_TEXT,
    'main_btn_hover_bg': APP_BORDER,
    'main_btn_hover_text': APP_TEXT,
    'main_btn_pressed_bg': GREY_44,
    'main_btn_pressed_text': TRUE_BLACK,
    'main_btn_border_color': 'transparent',
    # The About dialog's button hover plate. Spelled 'tab_hover' until
    # 2026-08-28, where it filled a QPushButton and not a tab.
    #
    # Deliberately NOT main_btn_hover_bg. That is the MAIN button's inverse
    # scheme -- #333333 in both modes, with the label flipping -- while dialog
    # buttons take a softer plate carrying gold text and a gold border.
    # Flattening the two would lose a scheme. Same value it always had.
    'dialog_btn_hover_bg': APP_PANEL_HOVER,
    # The plate and label a dialog button RESTS on. Added 2026-09-01,
    # holding what these dialogs already painted -- before this they
    # reached into the main family for both, which is why one name
    # ended up describing two schemes.
    'dialog_btn_bg': BRAND_BLACK,
    'dialog_btn_text': APP_TEXT,
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
    'scroll_handle': GREY_44,   # was #505050, see GREY_44
    # Accent (brand gold)
    'accent': BRAND_GOLD,
    'accent_dark': BRAND_GOLD_HOVER,
    'accent_ink': BRAND_GOLD,
    'accent_text': TRUE_BLACK,
    # Scrollbar
    'scrollbar_bg': BRAND_BLACK,
    'scrollbar_handle': GREY_44,   # was #505050, see GREY_44
    'scrollbar_handle_hover': '#606060',
    'scrollbar_border': APP_BORDER,
    # Dialog
    'dialog_bg': BRAND_BLACK,
    'dialog_border': APP_BORDER,
    # Status
    'success': STATUS_SUCCESS,
    'warning': STATUS_WARNING,
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
    'main_btn_bg': '#ffffff',
    'main_btn_text': '#000000',
    'main_btn_hover_bg': '#333333',
    'main_btn_hover_text': '#000000',
    'main_btn_pressed_bg': GREY_44,
    'main_btn_pressed_text': '#ffffff',
    'main_btn_border_color': 'transparent',
    # The About dialog's button hover plate. Spelled 'tab_hover' until
    # 2026-08-28, where it filled a QPushButton and not a tab.
    #
    # Deliberately NOT main_btn_hover_bg. That is the MAIN button's inverse
    # scheme -- #333333 in both modes, with the label flipping -- while dialog
    # buttons take a softer plate carrying gold text and a gold border.
    # Flattening the two would lose a scheme. Same value it always had.
    'dialog_btn_hover_bg': APP_HOVER_LIGHT,
    # The plate and label a dialog button RESTS on. Added 2026-09-01,
    # holding what these dialogs already painted -- before this they
    # reached into the main family for both, which is why one name
    # ended up describing two schemes.
    'dialog_btn_bg': '#ffffff',
    'dialog_btn_text': '#000000',
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
    'success': STATUS_SUCCESS,
    'warning': STATUS_WARNING,
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
    'hover_color': GREY_44,
    # Buttons
    'main_btn_bg': BRAND_BLACK,
    'main_btn_text': APP_TEXT,
    'main_btn_hover_bg': APP_BORDER,
    'main_btn_hover_text': APP_TEXT,
    'main_btn_pressed_bg': GREY_44,
    'main_btn_pressed_text': TRUE_BLACK,
    'main_btn_border_color': 'transparent',
    # The About dialog's button hover plate. Spelled 'tab_hover' until
    # 2026-08-28, where it filled a QPushButton and not a tab.
    #
    # Deliberately NOT main_btn_hover_bg. That is the MAIN button's inverse
    # scheme -- #333333 in both modes, with the label flipping -- while dialog
    # buttons take a softer plate carrying gold text and a gold border.
    # Flattening the two would lose a scheme. Same value it always had.
    'dialog_btn_hover_bg': APP_PANEL_HOVER,
    # The plate and label a dialog button RESTS on. Added 2026-09-01,
    # holding what these dialogs already painted -- before this they
    # reached into the main family for both, which is why one name
    # ended up describing two schemes.
    'dialog_btn_bg': BRAND_BLACK,
    'dialog_btn_text': APP_TEXT,
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
    'scroll_handle': GREY_44,   # was #505050, see GREY_44
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
    'success': STATUS_SUCCESS,
    'warning': STATUS_WARNING,
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
    "GREY_66",
    "GREY_F0",
    "relative_luminance",
    "contrast_ratio",
    "better_on",
    "contrast_ink",
    "prefers_dark_ink",
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
    "SEARCH_HIGHLIGHT_COLOR",
    "SEARCH_DIM_OVERLAY",
    "SLOT_BORDER_THIN_COLOR",
    "SLOT_BORDER_THICK_COLOR",
    "SIZE_OVERLAY_BG",
    # Accent pressed-text
    # Status colors
    "STATUS_SUCCESS",
    "STATUS_WARNING",
    "STATUS_ERROR",
    "STATUS_ERROR_TEXT",
    "STATUS_ERROR_TEXT_LIGHT",
    # Preview & history borders
    "PREVIEW_GRID_BORDER",
    "HISTORY_SWATCH_BORDER",
    # Structural / data colors
    "SVG_EXPORT_BG",
    "SVG_EXPORT_STROKE",
    "DATA_DEFAULT_COLOR",
    "SESSION_FALLBACK_COLOR",
    "SESSION_FALLBACK_COLOR_IMAGE",
    "TRANSPARENT_RGBA",
    # Functions
    "get_theme_colors",
    "is_dark_theme",
]