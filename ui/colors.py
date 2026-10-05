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


def _hex6(hex_color: str) -> str:
    """The six hex digits of a colour, or ValueError. Shared by the two
    helpers below so that they refuse exactly the same inputs."""
    h = hex_color.lstrip("#")
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        raise ValueError(f"{hex_color!r} is not a six-digit hex colour")
    return h


def _alpha_byte(alpha: int) -> int:
    """An alpha as the 0-255 byte, or an error. A fraction is refused, not
    scaled: Qt TRUNCATES a fractional alpha (0.3 is 76, not 77), and a helper
    that rounded would move a pixel inside a respelling."""
    if isinstance(alpha, bool) or not isinstance(alpha, int):
        raise TypeError(f"alpha {alpha!r} is not an int byte")
    if not 0 <= alpha <= 255:
        raise ValueError(f"alpha {alpha} is outside 0-255")
    return alpha


def translucent(hex_color: str, alpha: int) -> str:
    """A colour at an alpha, as Qt's eight-digit #AARRGGBB -- ALPHA FIRST.

    WHY A FUNCTION RATHER THAN A WRITTEN-OUT VALUE. A value computed from
    another value must be computed in code; a written-down derivative is
    orphaned the moment its source moves, and nothing says so.
    RNV-COLLAPSE-505050 is what that cost here: the value was ruled onto
    GREY_44 on 2026-09-02, and IMAGE_MODE_COLORS went on painting the main
    scrollbar handle with it for three weeks, written out as rgba(), while
    the guard for that ruling reported clean.

    WHY #AARRGGBB. It is the one spelling valid both in a stylesheet and in
    QColor(). QColor() cannot parse rgba(): it returns an INVALID colour, and
    Qt paints that as opaque black.

    WHY LOWER CASE. The register writes hex in lower case (Notation, Brand
    Book decision #19), and on 2026-09-25 that rule was extended to eight
    digits (RNV-LOWER-EIGHT). This helper wrote upper case until then,
    because the locked suite checked image window_bg with a case-sensitive
    startswith("#ED"); the same ruling bent that one line to "#ed". Qt
    reads either case, so no pixel moved.
    """
    return "#%02x%s" % (_alpha_byte(alpha), _hex6(hex_color).lower())


def translucent_rgba(hex_color: str, alpha: int) -> str:
    """The same derivation, spelled rgba(r, g, b, a). STYLESHEETS ONLY.

    It exists for one consumer. The locked suite asserts that SIZE_OVERLAY_BG
    contains "rgba", and that lock stands; everything that reads
    SIZE_OVERLAY_BG is a stylesheet, where rgba() is valid. QColor() is not
    -- it reads rgba() as INVALID and paints opaque black -- so translucent()
    is the default and this is the exception, pinned in
    tests/test_derived_values.py to the one constant that needs it.
    """
    h = _hex6(hex_color)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {_alpha_byte(alpha)})"



def translucent_tuple(hex_color: str, alpha: int) -> tuple[int, int, int, int]:
    """The same derivation, as the (r, g, b, a) tuple QColor(*t) takes.

    RNV-TUPLE-ROUND, 2026-09-26. The third spelling of one derived value:
    translucent() writes #aarrggbb for stylesheets and QColor(); this is for
    the callers that unpack a tuple into QColor or key a cache by one. A tuple
    is the notation the fleet's string sweeps never read, so a constant written
    as one could not follow its base. Same refusals as translucent(), same
    bytes.
    """
    h = _hex6(hex_color)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), _alpha_byte(alpha))


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

# grey(4) on the ink grid. The main button's pressed plate (ruled 2026-08-26)
# and the scrollbar handle -- RNV-COLLAPSE-505050, ruled 2026-09-02: #505050
# was on neither the ladder nor the grid. Named here for the first time in
# this app; rnv-text-transformer already calls it GREY_44.
#
# CORRECTED 2026-09-25, AND MOVED. This said the other four applications
# "already used #444444" for the handle. In dark mode three did, and the
# mixer used #333333. In image mode none did: all four still painted #505050,
# spelled rgba(), on the main surface -- the mixer in IMAGE_STYLESHEET,
# beside the #333333 its palette gives dialogs -- and so did this
# application's own image scrollbar_handle, until this date. The comment also
# sat between APP_PANEL_HOVER and that constant's docstring, so the text
# describing the panel-hover rung read as GREY_44's.
GREY_44: Final[str] = "#444444"
"""grey(4) on the ink grid. The pressed plate, and the scrollbar handle in
every mode -- in image mode at SCROLLBAR_HANDLE_ALPHA."""

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

# RNV-LIGHT-WIRING (2026-09-06): the constants below name values the
# palettes already carried as literals. Nothing here is a new colour.
# Registered values take the register's key; ramp greys take their byte.

APP_SURFACE_LIGHT_3: Final[str] = "#f5f5f5"
"""engine/brand.py APP["surface-light-3"]. The light window and panel
ground -- what a dialog sits on in light mode.

RNV-LIGHT-WIRING (2026-09-06): this value was written out as a literal
in every palette that used it, so nothing could move it. Registered by
rev 27 as the third rung of the light surface ladder; named here under
the register's key, the way APP_PANEL_HOVER and APP_HOVER_LIGHT are.
Every key that carries it is a surface, so it is not split."""

# RNV-NAMED-AND-USED (2026-10-04): a ramp step at #e0e0e0 stood here, for two
# light keys nothing read. It went with them.

GREY_EE: Final[str] = "#eeeeee"
"""grey(14) on the ramp, #eeeeee. Static surfaces that share a hex with
APP_HOVER_LIGHT without being a hover: a list header, a scroll ground.
Same split rnv-text-transformer ruled for its diff headers."""

GREY_CC: Final[str] = "#cccccc"
"""grey(12) on the ramp, #cccccc. The light-mode border."""

GREY_88: Final[str] = "#888888"
"""grey(8) on the ramp, #888888. Muted text on dark, a scrollbar handle
hover on light."""

GREY_55: Final[str] = "#555555"
"""grey(5) on the ramp, #555555. Disabled text and a checkbox edge on dark."""

# ==================== Composite alphas ====================
# A composite is a named colour AT AN ALPHA: translucent(BASE, ALPHA). The
# colour half is a name, so a register move reaches it; the alpha half is one
# of these, so that same move carries every alpha form of the colour with it.
# Each byte is the one the literal it replaced already held, except the
# scrollbar handle's, which was ruled.

IMAGE_OVERLAY_ALPHA: Final[int] = 0xED
"""237, about 93%. The alpha image mode composites its chrome at.

WAS THE STRING "ED", AND THE OVERLAYS BELOW WERE WRITTEN OUT. The reason
given was that composing them would make the palette entries resolve to an
expression rather than a value, which this app's own before/after comparison
could not check -- so tests/test_ladder_and_plate.py asserted the
relationship instead, and a register move would have failed that test and
waited for someone to edit two strings by hand.

RULED 2026-09-24 by Chris: derived values are DERIVED, not asserted. The
palettes still resolve to plain strings at import, so every comparison of
values still compares values. What changed is that a register move now
reaches the overlays on its own. The ladder test keeps its check, taking each
overlay apart rather than trusting the call that built it.

THEY WERE INVISIBLE BEFORE. The 2026-08-29 wiring pass claimed no registered
value was left spelled as a literal in a dark palette. That was true of
six-digit spellings only: its sweep compared whole strings, so #ED000000 never
matched #000000, and three of these sat in IMAGE_MODE_COLORS -- which is a DARK
dict here -- while the test reported clean.
"""

SCROLLBAR_HANDLE_ALPHA: Final[int] = 0x96
"""150. The image-mode scrollbar handle. It was 100 here and 150 in all four
other applications, and nothing recorded why. Ruled 2026-09-24: 150
fleet-wide, moving with the handle's colour."""

SCROLLBAR_BORDER_ALPHA: Final[int] = 0x64
"""100. The image-mode scrollbar edge -- the byte it already had."""

SIZE_OVERLAY_ALPHA: Final[int] = 0xC8
"""200. The floating size and status readout -- the byte it already had."""

SLOT_IMAGE_ALPHA: Final[int] = 0xAB
"""171. A new slot's default fill in image mode -- the byte it already had.

DEFAULT_SLOT_COLOR_IMAGE_RGB is TRUE_BLACK at this byte, derived from the pair
since 2026-09-26 (RNV-TUPLE-ROUND); and the main window sets this byte on a
slot colour that comes from the settings."""

SEARCH_DIM_ALPHA: Final[int] = 0x8C
"""140. The dim drawn over slots that do not match a search (TRUE_BLACK) --
the byte it already had."""

APP_WINDOW_OVERLAY: Final[str] = translucent(TRUE_BLACK, IMAGE_OVERLAY_ALPHA)
"""TRUE_BLACK, and APP["window"], at IMAGE_OVERLAY_ALPHA."""

APP_PANEL_OVERLAY: Final[str] = translucent(BRAND_BLACK, IMAGE_OVERLAY_ALPHA)
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
    "APP_SURFACE_LIGHT_3": "register",
    "GREY_EE": "app-ramp",
    "GREY_CC": "app-ramp",
    "GREY_88": "app-ramp",
    "GREY_55": "app-ramp",
}
"""Declarative, and read by tests/test_app_mirror.py, in the same shape as
GOLD_PROVENANCE above. A classification that lives only in a test drifts from
the thing it classifies."""

# ==================== Semantic UI Constants ====================
# Used directly in code that cannot access a theme dict (e.g. paintEvent)
SELECTION_OVERLAY_COLOR: Final[str] = "rgba(0,120,215,200)"

# ── Neutral greys, named for what they are ──
# RNV-INK-RULE (2026-09-02). This was a role name on a value four
# applications paint with.
#
# RNV-LIGHT-WIRING (2026-09-06): GREY_F0 (#f0f0f0) was defined beside this
# and painted by ui/image_upload_dialog.py. #f0f0f0 sat on no ladder,
# 0.42 CIEDE2000 from APP hover-light #eeeeee, and was ruled onto it
# with the other two light strays. The dialog now paints GREY_EE, defined
# with the ramp steps above. THIS MOVES A PIXEL in that dialog -- the
# one place in this script that does.
GREY_66: Final[str] = "#666666"


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

SEARCH_DIM_OVERLAY: Final[tuple[int,int,int,int]] = translucent_tuple(
    TRUE_BLACK, SEARCH_DIM_ALPHA)
"""Semi-transparent black overlay drawn on non-matching slots."""

SLOT_BORDER_THIN_COLOR: Final[tuple[int,int,int]] = _to_rgb(GREY_44)
"""Border color for thin slot border style. GREY_44: it was (80, 80, 80),
#505050, until the 2026-09-25 ruling collapsed it (RNV-COLLAPSE-505050)."""

SLOT_BORDER_THICK_COLOR: Final[tuple[int,int,int]] = (60, 60, 60)
"""Border color for thick slot border style."""

SIZE_OVERLAY_BG: Final[str] = translucent_rgba(TRUE_BLACK, SIZE_OVERLAY_ALPHA)
"""Background for the floating size/status overlay widget. TRUE_BLACK at
SIZE_OVERLAY_ALPHA, spelled rgba() because the locked suite pins that
spelling -- every consumer is a stylesheet, where it is valid."""

# ==================== Status Colors ====================
# RNV-NAMED-AND-USED (2026-10-04): the family's three fills stood here --
# success, warning and the error red the two text values below are siblings
# of. This application draws error TEXT and no status fill, and nothing read
# the three, so it carries none: the register holds them, as STATUS["success"],
# STATUS["warning"] and STATUS["error"].

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

STATUS_ERROR_TEXT_LIGHT: Final[str] = "#ae4650"
"""The same label on a LIGHT ground. MIRRORS STATUS["error-text-light"].

STATUS_ERROR_TEXT reads 2.8367 on #f5f5f5 -- below the 4.5 text floor and
below even the 3.0 UI floor. This reads 4.5123. No red carries text at 4.5:1
on a real light panel, so light spends a value on TEXT for exactly the reason
the gold does: the fill and text jobs occupy non-overlapping luminance bands.

WRITTEN DOWN, NOT DERIVED, AND THAT IS A CHANGE. This was
lighten(STATUS_ERROR, -20), and the test beside it argued -- correctly -- that
a written-down derivative orphans the moment its base moves. That argument is
why the value is not silently kept: against the new base the formula yields
#b44753, which is neither the old #c82131 nor the registered #ae4650. A
derivative whose rule no longer produces it is not a derivative, it is a
coincidence waiting to break.

The register's family derivation is a different rule -- hold hue and chroma,
move lightness only, take the first step that clears 4.5 on the worst ground
-- and it publishes the RESULT with the walk as provenance, so that retuning
the rule cannot silently change what an error looks like in five
applications. Same call the register made for BRAND_STANDBY_GOLD.

RNV-STATUS-LIGHT-FLOOR, CLOSED 2026-09-05 at register rev 31.

These were first walked against #f5f5f5 as "the worst light ground". It was
not the worst: rev 27 had put APP hover-light #eeeeee, GOLD_TEXT_GROUND_FLOOR
#e8e8e8 and pressed-light #e0e0e0 below it, and because the rule takes the
FIRST step that clears, each value stopped at 4.52 with no margin and they
failed one rung down together.

Re-walked against #e8e8e8. THE DECIDING REASON IS NOT THE SIZE OF THE MOVE --
#e0e0e0 was affordable on identical grounds, so cost does not pick between
them. It is that #e8e8e8 is where BRAND_DARK_GOLD_DEEP already stops:

    on #e8e8e8   gold-deep 4.53   these 4.52 / 4.53 / 4.52   pass
    on #e0e0e0   gold-deep 4.21   these 4.20 / 4.20 / 4.20   fail

ONE boundary for every brand text family instead of two. Walking to #e0e0e0
would have covered the pressed plate and left an author having to remember
which family they were in to know where text stops. Below #e8e8e8, no brand
text of any family.

This value reads 4.52 on #e8e8e8 and 5.08 on #f5f5f5, so it reaches the
coverage boundary its predecessor #c82131 did -- which the intermediate
#ae4650 did not, at 4.0150."""

# ==================== Preview & History Borders ====================
PREVIEW_GRID_BORDER: Final[tuple[int, int, int]] = _to_rgb(TRUE_BLACK)
"""Border color for grid cells in the preview grid widget."""

HISTORY_SWATCH_BORDER: Final[tuple[int, int, int]] = _to_rgb(GREY_44)
"""Border color for color history swatch thumbnails. GREY_44: it was
(80, 80, 80), #505050, until the 2026-09-25 ruling collapsed it."""

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

DEFAULT_SLOT_COLOR_IMAGE_RGB: Final[tuple[int, int, int, int]] = translucent_tuple(
    TRUE_BLACK, SLOT_IMAGE_ALPHA)
"""Default color for new color slots in Image mode (semi-transparent black):
TRUE_BLACK at SLOT_IMAGE_ALPHA, in the spelling QColor(*t) takes.

RNV-NAMED-AND-USED (2026-10-04): the same colour stood beside this as an
eight-digit hex string, and nothing read it. This is the spelling the slot
reads; where a slot's colour comes from the settings, the main window sets
SLOT_IMAGE_ALPHA on it."""


# ==================== Dark Theme Colors ====================
# RNV-NAMED-AND-USED (2026-10-04): a palette holds what is looked up. Nine
# keys nothing read went from all three palettes: a hover, the three tab
# keys and the note that called them not consumed, two status fills, a
# dialog border, an ink for the accent, and a main-button border written
# as transparent while the button draws its border from border_color.
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
    # Muted text. Kept aligned while nothing painted it, so that wiring it up
    # would be one line and not a colour decision -- and on 2026-09-27 it was
    # (RNV-MUTED-DESCRIPTIONS, ruling 1): the settings and batch export
    # dialogs' notes, previews and empty history, named "muted_text" in each
    # dialog's stylesheet. They were `color: grey`, #808080 in every mode.
    'text_secondary': GREY_88,
    'text_disabled': GREY_55,
    # Borders
    'border_color': APP_BORDER,
    # Buttons
    'main_btn_bg': BRAND_BLACK,
    'main_btn_text': APP_TEXT,
    'main_btn_hover_bg': APP_BORDER,
    'main_btn_hover_text': APP_TEXT,
    'main_btn_pressed_bg': GREY_44,
    'main_btn_pressed_text': TRUE_BLACK,
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
    # The About dialog's scroll handle
    'scroll_handle': GREY_44,   # was #505050, see GREY_44
    # Accent (brand gold)
    'accent': BRAND_GOLD,
    'accent_dark': BRAND_GOLD_HOVER,
    'accent_ink': BRAND_GOLD,
    # Scrollbar
    'scrollbar_bg': BRAND_BLACK,
    'scrollbar_handle': GREY_44,   # was #505050, see GREY_44
    'scrollbar_handle_hover': BRAND_GOLD,
    'scrollbar_border': APP_BORDER,
    # Dialog
    'dialog_bg': BRAND_BLACK,
}


# ==================== Light Theme Colors ====================
LIGHT_THEME_COLORS: Final[ThemeDict] = {
    'name': 'Light',
    # Base colors
    'window_bg': APP_SURFACE_LIGHT_3,
    'panel_bg': APP_SURFACE_LIGHT_3,
    'scroll_bg': GREY_EE,
    'card_bg': WHITE,
    'input_bg': WHITE,
    # Text
    'text_color': TRUE_BLACK,
    # Muted text -- see the note in the dark palette.
    'text_secondary': GREY_66,
    'text_disabled': APP_TEXT_DIM,
    # Borders
    'border_color': GREY_CC,
    # Buttons: white base, dark-grey hover/press, white text on press
    'main_btn_bg': WHITE,
    'main_btn_text': TRUE_BLACK,
    'main_btn_hover_bg': APP_BORDER,
    'main_btn_hover_text': TRUE_BLACK,
    'main_btn_pressed_bg': GREY_44,
    'main_btn_pressed_text': WHITE,
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
    'dialog_btn_bg': WHITE,
    'dialog_btn_text': TRUE_BLACK,
    # The About dialog's scroll handle
    'scroll_handle': APP_TEXT_DIM,
    # Accent (brand gold - darker variant for readability on light bg)
    'accent': BRAND_DARK_GOLD,
    'accent_dark': BRAND_DARK_GOLD,
    'accent_ink': BRAND_DARK_GOLD_DEEP,
    # Scrollbar
    'scrollbar_bg': APP_SURFACE_LIGHT_3,
    'scrollbar_handle': APP_TEXT_DIM,
    'scrollbar_handle_hover': BRAND_DARK_GOLD,
    'scrollbar_border': GREY_CC,
    # Dialog
    'dialog_bg': APP_SURFACE_LIGHT_3,
}


# ==================== Image Mode Colors ====================
# The dark palette under its own name, with what image mode draws differently.
#
# RNV-NAMED-AND-USED (2026-10-04): this was the dark palette written out a
# second time, entry by entry, with seven of them changed. Most of the copy
# was a second spelling of values image mode never looked up, and one of the
# seven was a difference nothing drew: input_bg, at APP_CARD, whose one
# reader is the settings dialog, and that dialog takes the dark palette in
# image mode. So this is dark's values, and after the spread the six entries
# image mode reads and draws differently. A key image mode looks up is always
# there, and nothing it never reads is written.
IMAGE_MODE_COLORS: Final[ThemeDict] = {
    **DARK_THEME_COLORS,
    'name': 'Image',
    # Base colors -- alpha-prefixed hex for Qt stylesheet compatibility
    'window_bg': APP_WINDOW_OVERLAY,
    'panel_bg': APP_PANEL_OVERLAY,
    'scroll_bg': APP_WINDOW_OVERLAY,
    # Scrollbar. The two composites are DERIVED -- a named colour at a
    # declared alpha -- so a register move reaches them.
    'scrollbar_bg': 'transparent',
    # RNV-COLLAPSE-505050, closed in this palette 2026-09-25. This read
    # rgba(80, 80, 80, 100) -- the retired value at alpha 100 -- three
    # weeks after the ruling, while tests/test_collapse_505050.py
    # reported it gone: nothing here decoded rgba(). The alpha moves
    # to 150 with it, the byte the other four image scrollbars use.
    'scrollbar_handle': translucent(GREY_44, SCROLLBAR_HANDLE_ALPHA),
    'scrollbar_border': translucent(APP_BORDER, SCROLLBAR_BORDER_ALPHA),
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
    "GREY_EE",
    "relative_luminance",
    "contrast_ratio",
    "better_on",
    "contrast_ink",
    "prefers_dark_ink",
    # Slot defaults
    "DEFAULT_SLOT_COLOR",
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
    "translucent",
    "translucent_rgba",
    "translucent_tuple",
    "get_theme_colors",
    "is_dark_theme",
]

# RNV-GOLD-GUARD (2026-09-07): the values below are swept by
# tests/test_gold_as_text.py, which resolves every QSS f-string in this
# repository through these palettes and measures the gold family as text
# and as a fill. A gold that reads correctly here can still be drawn on
# the wrong ground three files away, and that is what it is for.
