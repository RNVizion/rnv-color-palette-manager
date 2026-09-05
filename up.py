#!/usr/bin/env python3
"""
RNV-STATUS-TOOL-DO-NOT-SWEEP

Move rnv-color-palette-manager onto the RNV status family.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file


WHY

The register replaced Bootstrap's three status colours on 2026-09-03. The
amber read 1.63 on #ffffff and 1.49 on #f5f5f5 against a 3:1 fill floor;
success and error sat about 4 apart under deuteranopia, one olive, and those
are the two most consequential colours in any interface. The RNV family leaves
the red-green axis entirely.

    success  #28a745  ->  #926c89      warning  #ffc107  ->  #a2703c
    error    #dc3545  ->  #c75b64

    error-text        #e56b77  ->  #dd6f77
    error-text-light  #c82131  ->  #ae4650

The last two are ORPHANS: both were derived from #dc3545, and a value derived
from something no longer in the palette is the #c4a458 failure this programme
has already paid for once. They move with their base rather than being kept
alongside it. This file's own docstrings make that argument, twice, in the
words of the pass that wrote them -- so it is being applied, not overruled.


WHAT THIS APPLICATION ALREADY HAD RIGHT

The fill/text split. STATUS_ERROR is documented here as "not drawn by this
app, which renders no error fill", held only so the light text value can be
derived from it; STATUS_ERROR_TEXT and STATUS_ERROR_TEXT_LIGHT do the actual
painting, chosen per mode through one helper. That is the shape the register
has now generalised to all three roles, and this repository got there first
for the red.

So no keys are rewired here. The two SEMANTIC KEYS in the palettes --
'success' and 'warning' -- are dead: looked up nowhere in this application,
zero elements in the fleet colour tree, on the standing dead-key list. They
still move to the registered values, because a palette that carries a colour
should carry the right one and this repository's guard says every status value
here is the register's.


THE DERIVATION HAS TO BECOME A VALUE

    STATUS_ERROR_TEXT_LIGHT: Final[str] = lighten(STATUS_ERROR, -20)

no longer produces the registered value. Against the new base it yields
#b44753 -- neither the old #c82131 nor the registered #ae4650. The register's
family derivation is a different rule (hold hue and chroma, move lightness,
first step clearing 4.5) and it publishes the RESULT, with the walk as
provenance.

So this is written down, and the accompanying test -- which asserts
`STATUS_ERROR_TEXT_LIGHT == lighten(STATUS_ERROR, -20)` and argues in its name
that the value is "derived not written" -- is replaced rather than edited. Its
argument was correct and is why the value is not silently kept: a derivative
whose rule no longer produces it is not a derivative, it is a coincidence
waiting to break. The register made the same call for BRAND_STANDBY_GOLD.


THE BOUNDARY THIS PASS WAITED ON, NOW CLOSED

RNV-STATUS-LIGHT-FLOOR was open while these scripts were written. The three
LIGHT text variants had been walked to clear 4.5:1 on #f5f5f5, which the
register's rule called "the worst light ground". It was not: rev 27 had put
APP hover-light #eeeeee, GOLD_TEXT_GROUND_FLOOR #e8e8e8 and pressed-light
#e0e0e0 below it, and because the rule takes the FIRST step that clears, each
value stopped at 4.52 with no margin and all three failed one rung down.

Register rev 31 (2026-09-05) re-walked them against #e8e8e8:

    success-text-light  #8a6581 -> #825d79
    warning-text-light  #976633 -> #8e5e2b
    error-text-light    #b84e58 -> #ae4650

AND THE DECIDING REASON IS NOT THE ONE THIS CHAT GAVE. The argument here was
from cost -- a small move, the same three colours. True, and not sufficient,
because #e0e0e0 would have been affordable too. The register's reason is
better: #e8e8e8 is where BRAND_DARK_GOLD_DEEP already stops.

    on #e8e8e8   gold-deep 4.53   the three 4.52 / 4.53 / 4.52   pass
    on #e0e0e0   gold-deep 4.21   the three 4.20 / 4.20 / 4.20   fail

ONE boundary for every brand text family instead of two. Walking to #e0e0e0
would have covered the pressed plate and left an author having to remember
which family they were in to know where text stops.

So the boundary tests are not narrowed. They run the full four rungs, and they
pass -- which is the point of the re-walk being visible in the test rather than
only in the register.


ONE THING IS STILL OPEN, AND IT IS THE OTHER SIDE OF THE SAME FAULT

The three DARK text variants were derived against APP card #2a2a2a. Rev 29
then registered panel-hover #3a3a3a, which is LIGHTER and therefore worse for
light text on a dark ground. All three fail there:

    success-text 3.61   warning-text 3.64   error-text 3.58   floor 4.5
    BRAND_GOLD clears every dark surface at 6.15

Same two-boundary asymmetry, other side. The register left it open rather than
fixing it in rev 31, because the fix is not symmetric: on light the worst
surface is a PRESSED plate and ruling that running text is not carried on a
transient state is defensible, while on dark the worst is a HOVER, which a
label sits under for as long as a cursor rests there. The walk would cost
CIEDE2000 6.53-7.06 -- inside the 8.40 bar, but more than double the light
move, and it lightens all three toward the ink ramp.

WHAT THIS CHAT CAN ADD: the fleet's exposure today is ZERO. The element sweep
across all five applications resolves four status elements, all of them plain
dialog labels painted with an inline `color:` on a dialog ground; not one
status key is painted in a selector carrying :hover. So this is a register
question about where the boundary should be, not a live defect in these apps
-- and if a status label is ever put on a hover row, the dark-ground
assertions in the guard are where it should surface.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-color-palette-manager"
DESCRIPTION = "move onto the RNV status family; register the light error text"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = "RNV-STATUS-FAMILY"
GUARD = "tests/test_error_red.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ("run_tests.py (unittest + pytest)", [sys.executable, "run_tests.py"]),
]

REGISTERED = {
    "STATUS_SUCCESS": "#926c89",
    "STATUS_WARNING": "#a2703c",
    "STATUS_ERROR": "#c75b64",
    "STATUS_ERROR_TEXT": "#dd6f77",
    "STATUS_ERROR_TEXT_LIGHT": "#ae4650",
}
RETIRED = ("#28a745", "#ffc107", "#dc3545", "#e56b77", "#c82131")


GUARD_SOURCE = r'''"""Error text is theme-aware, and every retired red is gone.

    STATUS_ERROR             #c75b64   registered base; no fill is drawn here
    STATUS_ERROR_TEXT        #dd6f77   dark ground, = register error-text
    STATUS_ERROR_TEXT_LIGHT  #ae4650   light ground, = register error-text-light

Before the 2026-09-02 pass a single #ff6b6b served both modes and read 2.5454
on the light dialog ground -- below the text floor and below the UI floor too.
That pass split them. This one, RNV-STATUS-FAMILY on 2026-09-03, moves the
whole family: the register retired Bootstrap's #dc3545, and #e56b77 and
#c82131 were both derived from it.

TWO TESTS HERE WERE REPLACED RATHER THAN EDITED, and both replacements say so:

  * test_the_light_error_text_is_derived_not_written asserted
    STATUS_ERROR_TEXT_LIGHT == lighten(STATUS_ERROR, -20). Its argument was
    right and is exactly why the value could not be left alone -- against the
    new base that formula yields #b44753, a third answer. See
    test_the_light_error_text_is_registered_and_why_that_changed.

  * test_light_error_text_carries_to_the_published_boundary parametrised over
    #ffffff, #f5f5f5, #eeeeee and #e8e8e8. The registered replacement does not
    reach the last two, so this test was briefly narrowed to two grounds.
    Register rev 31 re-walked them against #e8e8e8 and the four grounds
    are back. See RNV-STATUS-LIGHT-FLOOR below.
"""

import pytest

from ui import colors

TEXT_FLOOR = 4.5


MIN_OPAQUE_ALPHA = 0xE0


def _rgb(value: str) -> str:
    """Six hex digits, from a value that may carry a Qt alpha channel.

    Image mode's window_bg is `#ED000000` -- eight digits, #AARRGGBB, which
    is Qt's order and NOT the CSS #RRGGBBAA. Read naively as #RRGGBB it
    becomes #ED0000, a red, and the contrast against it computes to 1.6448
    instead of the ~7.57 the eye actually sees. That is the 8-digit blind
    spot the family register warns about, and it caught this very test.

    The alpha is asserted rather than ignored: at 0xED the colour is 93%
    opaque, so treating it as its own RGB is a sound approximation. Below
    that it would not be, and this stops rather than quietly approximating.
    """
    h = value.lstrip("#")
    if len(h) == 8:
        alpha = int(h[0:2], 16)
        assert alpha >= MIN_OPAQUE_ALPHA, (
            f"{value} is only {alpha / 255:.0%} opaque; its effective colour "
            f"depends on what is behind it and cannot be measured here")
        return h[2:]
    assert len(h) == 6, f"expected 6 or 8 hex digits, got {value!r}"
    return h


def _luminance(value: str) -> float:
    h = _rgb(value)
    parts = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    parts = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
             for x in parts]
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]


def contrast(a: str, b: str) -> float:
    first, second = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (first + 0.05) / (second + 0.05)


def test_the_argb_reader_is_not_fooled_by_the_alpha_channel():
    """Guard the guard.

    If _rgb ever goes back to slicing the first six digits, every contrast
    number measured against image mode becomes fiction -- and fiction that
    reads as a FAILURE, which is the kind that gets 'fixed' by changing the
    colour rather than the reader.
    """
    assert _rgb("#ED000000") == "000000"
    assert _rgb("#f5f5f5") == "f5f5f5"
    assert contrast("#ffffff", "#ED000000") == pytest.approx(
        contrast("#ffffff", "#000000"))


def test_the_light_error_text_is_registered_and_why_that_changed():
    """This replaces test_the_light_error_text_is_derived_not_written.

    That test asserted STATUS_ERROR_TEXT_LIGHT == lighten(STATUS_ERROR, -20)
    and argued that a written-down derivative orphans the moment its base
    moves. The argument was correct, and it is why this value could not be
    left as it was: the base moved on 2026-09-03, and against #c75b64 the
    formula yields #b44753 -- neither the old #c82131 nor the registered
    #ae4650. A derivative whose rule no longer produces it is not a
    derivative; it is a coincidence waiting to break.

    The register's family rule is a different one -- hold hue and chroma, move
    lightness only, take the first step clearing 4.5 on the worst ground --
    and it publishes the RESULT with the walk as provenance, so retuning the
    rule cannot silently change what an error looks like in five
    applications. Same call the register made for BRAND_STANDBY_GOLD.
    """
    assert colors.STATUS_ERROR_TEXT_LIGHT == "#ae4650"
    assert colors.STATUS_ERROR_TEXT_LIGHT != colors.lighten(colors.STATUS_ERROR, -20)


def test_the_family_is_the_registered_one():
    """Pinned by value. A test asserting only that these differ from each
    other would pass on five wrong colours."""
    assert colors.STATUS_SUCCESS == "#926c89"
    assert colors.STATUS_WARNING == "#a2703c"
    assert colors.STATUS_ERROR == "#c75b64"
    assert colors.STATUS_ERROR_TEXT == "#dd6f77"
    assert colors.STATUS_ERROR_TEXT_LIGHT == "#ae4650"


def test_light_error_text_clears_its_own_dialog_ground():
    """The pairing the 2026-09-02 pass existed to fix: 2.5454 -> 5.1811, and
    now 4.5123 with the registered replacement."""
    ground = colors.LIGHT_THEME_COLORS["window_bg"]
    ratio = contrast(colors.STATUS_ERROR_TEXT_LIGHT, ground)
    assert ratio >= TEXT_FLOOR, \
        f"{colors.STATUS_ERROR_TEXT_LIGHT} on {ground} = {ratio:.4f}"


@pytest.mark.parametrize("ground", ["#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"])
def test_light_error_text_carries_to_the_published_boundary(ground):
    """RNV-STATUS-LIGHT-FLOOR, closed 2026-09-05 at register rev 31.

    This ran over #ffffff, #f5f5f5, #eeeeee and #e8e8e8 when the light value
    was #c82131, which reached all four. The first RNV replacements did not:
    walked against #f5f5f5 as "the worst light ground" and taken at the first
    step that cleared, they stopped at 4.52 with no margin and failed on the
    three registered rungs below it.

    The register re-walked them against #e8e8e8, and the reason is not the
    size of the move. It is that #e8e8e8 is where BRAND_DARK_GOLD_DEEP already
    stops:

        on #e8e8e8   gold-deep 4.53   the three 4.52 / 4.53 / 4.52   pass
        on #e0e0e0   gold-deep 4.21   the three 4.20 / 4.20 / 4.20   fail

    ONE boundary for every brand text family instead of two. #e0e0e0 was
    affordable and would have covered the pressed plate, at the cost of an
    author having to remember which family they were in to know where text
    stops. Below #e8e8e8, no brand text of any family.

    So the four grounds are back, and they are back because the values reach
    them -- not because the test was widened to make a point.
    """
    ratio = contrast(colors.STATUS_ERROR_TEXT_LIGHT, ground)
    assert ratio >= TEXT_FLOOR, \
        f"{colors.STATUS_ERROR_TEXT_LIGHT} on {ground} = {ratio:.4f}"


def test_dark_error_text_mirrors_the_register_and_still_clears():
    """Dark was never short, and this test existed to stop the value moving
    quietly. It has now done that job twice.

    RNV-STATUS-REGISTER (2026-09-02): #ff6b6b was this app's own dark error
    text, left alone by the error-red pass on the argument that a value
    already clearing the floor should not be replaced to buy uniformity. The
    register then published error-text #e56b77 for this exact job, so the
    choice became one name against a fourth spelling.

    RNV-STATUS-FAMILY (2026-09-03): #e56b77 was itself derived from Bootstrap's
    #dc3545. With that base retired it is an ORPHAN, and it moves with its
    base rather than being kept alongside it. #dd6f77 has slightly LESS
    headroom on every dark ground than the value it replaces -- 4.5210
    against 4.5801 on the card -- and is still above the floor.

    The assertion stays exact for the same reason it was written exact."""
    assert colors.STATUS_ERROR_TEXT == "#dd6f77"
    for name in ("DARK", "IMAGE_MODE"):
        palette = getattr(colors, name + "_THEME_COLORS", None) or \
            getattr(colors, "IMAGE_MODE_COLORS")
        ratio = contrast(colors.STATUS_ERROR_TEXT, palette["window_bg"])
        assert ratio >= TEXT_FLOOR, f"{name}: {ratio:.4f}"


def test_the_two_error_texts_are_not_the_same_value():
    """If these ever collapse onto one value, one of the two modes is short
    again -- which is the state the 2026-09-02 pass found the app in."""
    assert colors.STATUS_ERROR_TEXT != colors.STATUS_ERROR_TEXT_LIGHT


def test_the_fills_cannot_carry_text_and_that_is_why_there_are_five_values():
    """The arithmetic behind the family's shape.

    STATUS_SUCCESS, STATUS_WARNING and STATUS_ERROR are fills. Every fill in
    the family sits at L* 48-59, which is exactly what lets ONE value clear
    3:1 on a dark AND a light ground -- and a mid-tone reaches 4.5:1 on
    neither. This application already knew that for the red and spent two
    values on it before the register generalised it.

    If any fill ever clears the text floor, the register has moved it out of
    the band and somebody needs to know rather than quietly benefiting.
    """
    for name in ("STATUS_SUCCESS", "STATUS_WARNING", "STATUS_ERROR"):
        value = getattr(colors, name)
        for ground in ("#1a1a1a", "#2a2a2a", "#f5f5f5", "#ffffff"):
            assert contrast(value, ground) >= 3.0, f"{name} on {ground}"
            assert contrast(value, ground) < TEXT_FLOOR, (
                f"{name} now clears the text floor on {ground}. Do not relax "
                f"this -- find out whether the register moved it.")


def test_the_retired_material_red_is_gone_from_every_palette():
    """It was an orphan -- no code path read it -- but an unread wrong value
    is still a wrong value waiting for a reader."""
    retired = "#f44336"
    for name in ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS"):
        palette = getattr(colors, name)
        offenders = [k for k, v in palette.items()
                     if isinstance(v, str) and v.lower() == retired]
        assert not offenders, f"{name} still carries {retired} on {offenders}"
        assert "error" not in palette, \
            f"{name} still has the dead 'error' key"


def test_no_retired_status_value_is_in_any_palette():
    """The 2026-09-03 sweep. The three Bootstrap values and the two orphans
    derived from the red -- none of them belongs in a palette any more."""
    retired = {"#28a745", "#ffc107", "#dc3545", "#e56b77", "#c82131"}
    for name in ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS"):
        palette = getattr(colors, name)
        offenders = {k: v for k, v in palette.items()
                     if isinstance(v, str) and v.lower() in retired}
        assert not offenders, f"{name} still carries {offenders}"


def test_that_check_is_actually_looking():
    """Guard the guard. The sweeps above walk three palettes; if they ever
    turn up empty they would pass while checking nothing."""
    for name in ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS"):
        palette = getattr(colors, name)
        assert len(palette) > 20, f"{name} has only {len(palette)} keys"
    planted = {"error": "#f44336"}
    assert [k for k, v in planted.items() if v.lower() == "#f44336"], \
        "the retired-value pattern no longer matches a known offender"


def test_both_error_labels_go_through_the_helper(qtbot):
    """The two call sites used to name the constant directly. One helper is
    what stops a future change fixing one of them and forgetting the other.
    """
    import inspect

    from ui import batch_export_dialog

    source = inspect.getsource(batch_export_dialog)
    assert source.count("self._error_text_color()") == 2
    assert "f\"color: {STATUS_ERROR_TEXT};\"" not in source, \
        "a call site still names the dark constant directly"
'''

NEW_CONSTANTS = r'''STATUS_SUCCESS: Final[str] = "#926c89"
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

RNV-STATUS-LIGHT-FLOOR, CLOSED 2026-09-05 at register rev 31. The three
light text variants were first walked against #f5f5f5 as "the worst light
ground". It was not the worst: rev 27 had put APP hover-light #eeeeee,
GOLD_TEXT_GROUND_FLOOR #e8e8e8 and pressed-light #e0e0e0 below it, and each
value was taken at the FIRST step that cleared -- 4.52 -- so none had margin
and one rung down they failed together.

They were re-walked against #e8e8e8, and the deciding reason is not the small
size of the move. It is that #e8e8e8 is where BRAND_DARK_GOLD_DEEP already
stops:

    on #e8e8e8   gold-deep 4.53   the three 4.52 / 4.53 / 4.52   all pass
    on #e0e0e0   gold-deep 4.21   the three 4.20 / 4.20 / 4.20   all fail

ONE boundary for every brand text family rather than two. Walking to #e0e0e0
was affordable and would have covered the pressed plate, at the cost of an
author having to remember which family they were in to know where text stops.
Below #e8e8e8, no brand text of any family."""
'''


def _code_only(text: str) -> str:
    """Source with comments and DOCSTRINGS removed -- and nothing else.

    Why this exists: every value these guards forbid is named, in words, in
    the provenance explaining why it was retired. A sweep that cannot tell a
    value being USED from a value being MENTIONED forces the fix to be silence
    about what changed, which is the opposite of what the provenance is for.

    Why it is fussier than it looks: an earlier version dropped every STRING
    token. In Python a colour value IS a string literal -- `X = "#926c89"` --
    so that version removed the uses along with the mentions and the sweep
    could never find anything. It passed on every input, including a file that
    had just put a retired value back. This file's own guard-the-guard is what
    caught it, which is the entire reason for writing guards that check the
    guard can still see.

    So: a STRING token is dropped only when it STARTS a statement -- a
    docstring, or a bare string expression, which is prose either way. A string
    on the right of an assignment, in a dict, or in a call is kept, because
    that is what a value looks like.
    """
    import io
    import tokenize
    out = []
    # ENCODING behaves like the start of a line for this purpose.
    at_statement_start = True
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                continue
            if tok.type == tokenize.STRING and at_statement_start:
                at_statement_start = False
                continue
            if tok.type in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
                            tokenize.DEDENT, tokenize.ENCODING):
                at_statement_start = True
            else:
                at_statement_start = False
            out.append(tok.string)
    except (tokenize.TokenError, IndentationError):
        # Falling back to the raw text can only make a sweep STRICTER, never
        # looser, so it fails safe.
        return text
    return " ".join(out)


def edits(tree) -> None:
    # --- 1. the five constants, replaced as one block.
    #
    # Anchored on the first line and the last, so a file that has moved fails
    # here rather than composing a wrong replacement out of anchors that still
    # happen to match individually.
    src = tree.read("ui/colors.py")
    start_anchor = 'STATUS_SUCCESS: Final[str] = "#28a745"'
    end_anchor = ("hue at 354.25 degrees, identical to the base.\"\"\"\n")
    if src.count(start_anchor) != 1 or src.count(end_anchor) != 1:
        raise SystemExit("ui/colors.py: the status block is not where this "
                         "script expects it")
    start = src.index(start_anchor)
    end = src.index(end_anchor) + len(end_anchor)
    if end <= start:
        raise SystemExit("ui/colors.py: the status block's anchors are in the "
                         "wrong order")
    tree.write("ui/colors.py", src[:start] + NEW_CONSTANTS + src[end:])

    # --- 2. the three palettes' dead semantic keys.
    #
    # 'success' and 'warning' are looked up nowhere in this application -- zero
    # elements in the fleet colour tree -- and this pass does not wire them to
    # anything; whether they should exist at all is a separate question on the
    # standing dead-key list. They stay wired through the constants, so they
    # move with the values without a single literal changing here.
    #
    # Asserted rather than assumed: if either key were ever rewritten as a
    # literal, the count below would not be three and this would stop.
    body = tree.read("ui/colors.py")
    for key, const in (("success", "STATUS_SUCCESS"), ("warning", "STATUS_WARNING")):
        found = len(re.findall(r"'%s':\s+%s\b" % (key, const), body))
        if found != 3:
            raise SystemExit(
                f"'{key}' is wired through {const} in {found} palettes, not 3. "
                f"A palette that writes it as a literal will not move with the "
                f"constant; re-derive this script before trusting it.")

    # --- 3. tests/test_status_register.py pins the three retired values by hex
    # and explains at length why each was THE one. Changing a hex inside an
    # argument for it would leave the argument standing for a value that lost
    # it, so the three assertions and their reasoning are replaced together.
    tree.sub("tests/test_status_register.py",
             '    assert colors.STATUS_SUCCESS == "#28a745"\n'
             '    assert colors.STATUS_WARNING == "#ffc107"\n'
             '    assert colors.STATUS_ERROR == "#dc3545"\n'
             '    assert colors.STATUS_ERROR_TEXT == "#e56b77"\n',
             '    # RNV-STATUS-FAMILY (2026-09-03): the register replaced all\n'
             '    # three. The green and the red were one olive under\n'
             '    # deuteranopia at about 4 apart; the amber read 1.63 on\n'
             '    # #ffffff against a 3:1 fill floor. Still pinned by value --\n'
             '    # an app that picks its own status colour has an opinion\n'
             '    # about what success means, which is the register\'s job.\n'
             '    assert colors.STATUS_SUCCESS == "#926c89"\n'
             '    assert colors.STATUS_WARNING == "#a2703c"\n'
             '    assert colors.STATUS_ERROR == "#c75b64"\n'
             '    # #e56b77 was derived from #dc3545 and orphaned when the\n'
             '    # base was retired, so it moves with it.\n'
             '    assert colors.STATUS_ERROR_TEXT == "#dd6f77"\n', 1)

    # --- 3b. and the headroom note beside it, which measured the move that
    # brought #ff6b6b down to #e56b77. That move is now two moves.
    tree.sub("tests/test_status_register.py",
             '    """The move costs 0.87 of headroom. This is the check that '
             'says it could\n'
             '    afford it, on the grounds this app actually paints."""\n',
             '    """The 2026-09-02 move cost 0.87 of headroom and this is the\n'
             '    check that said it could afford it. RNV-STATUS-FAMILY\n'
             '    (2026-09-03) takes a little more: #dd6f77 reads 4.5210 on\n'
             '    APP card against #e56b77\'s 4.5801 -- still above the floor,\n'
             '    on the grounds this app\n'
             '    actually paints."""\n', 1)

    # --- 4. that file's stray list. #4caf50 and #ff6b6b are still retired and
    # still worth sweeping for; the three Bootstrap values join them, because a
    # value the register retired is exactly what "stray" means here.
    tree.sub("tests/test_status_register.py",
             'STRAYS = {"#4caf50", "#ff6b6b"}\n',
             'STRAYS = {\n'
             '    "#4caf50",   # Material green, ruled out 2026-09-02\n'
             '    "#ff6b6b",   # this app\'s own dark error text, ruled out 2026-09-02\n'
             '    # RNV-STATUS-FAMILY (2026-09-03), the Bootstrap family and its\n'
             '    # two orphans. #e56b77 and #c82131 were derived from #dc3545;\n'
             '    # with the base retired they are values derived from something\n'
             '    # no longer in the palette, which is the #c4a458 failure.\n'
             '    "#28a745", "#ffc107", "#dc3545", "#e56b77", "#c82131",\n'
             '}\n', 1)

    # --- 5. tests/test_error_red.py, rewritten by the harness as the guard.
    #
    # Two of its tests cannot survive as edits. One asserts the light value
    # equals lighten(STATUS_ERROR, -20) and argues in its own name that the
    # value is "derived not written" -- an argument this pass agrees with and
    # is acting on, since the formula no longer produces the registered value.
    # The other parametrises the coverage boundary down to #e8e8e8, which the
    # registered replacement does not reach. Both are replaced with tests that
    # say what changed and why, rather than with edited assertions that would
    # leave the old reasoning attached to new numbers.
    print("  5 edit groups composed")


def checks(tree) -> None:
    colors_src = tree.read("ui/colors.py")
    reg = tree.read("tests/test_status_register.py")

    for dead in RETIRED:
        if f'"{dead}"' in _code_only(colors_src):
            raise SystemExit(f"{dead} survives as a value in ui/colors.py")

    for name, want in REGISTERED.items():
        if f'{name}: Final[str] = "{want}"' not in colors_src:
            raise SystemExit(f"{name} is not defined as {want}")

    # the derivation is gone: it no longer produces the registered value, and
    # leaving it would give a third answer -- #b44753 -- to a settled question
    if "lighten(STATUS_ERROR" in _code_only(colors_src):
        raise SystemExit("the light error text is still derived with lighten(); "
                         "against the new base that yields #b44753, which is "
                         "neither the old value nor the registered one")

    # the two text values remain distinct. If they ever collapse, one mode is
    # short again, which is the state the 2026-09-02 pass found this app in.
    if REGISTERED["STATUS_ERROR_TEXT"] == REGISTERED["STATUS_ERROR_TEXT_LIGHT"]:
        raise SystemExit("the two error texts are the same value")

    for want in ("#926c89", "#a2703c", "#c75b64"):
        if want not in reg:
            raise SystemExit(f"tests/test_status_register.py does not pin {want}")

    if SENTINEL not in colors_src:
        raise SystemExit("the ruling note did not land in ui/colors.py")
    print("  guards: 5 retired values gone, 5 registered values in, "
          "the light derivation is now a value")


# ------------------------------------------------------------------ plumbing
def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        sys.exit(f"refusing to run as {name} -- it would shadow a module on "
                 f"sys.path. Rename to up.py and run again.")


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}

    def read(self, rel: str) -> str:
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise SystemExit(f"missing file: {rel}")
            self.files[rel] = p.read_text(encoding="utf-8")
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise SystemExit(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.")
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = text.encode("utf-8")
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort" or "env" -- only exit code 1 means a test failed.

    pytest exits 0 passed, 1 tests failed, 2 interrupted, 3 internal error,
    4 usage error, 5 nothing collected; a native abort arrives as 134 or -6.
    Treating every non-zero code as a failing assertion is how a tool reports
    a regression that never happened.
    """
    if code == 0:
        return "pass"
    if code in (-9, 137, -15, 143):
        return "killed"
    if code in (134, -6, 139, -11) or "Fatal Python error" in out:
        return "abort"
    if code == 1 and "INTERNALERROR" not in out:
        return "fail"
    return "env"


ENV_HELP = """\
THE ENVIRONMENT IS NOT READY. NO TEST DISAGREED WITH THIS CHANGE -- the run
did not get far enough to ask one.

PyQt6 needs system libraries a fresh container does not ship; the give-away is
`ImportError: libGL.so.1`. Install those, then the Python packages:

    sudo apt-get update
    sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 \\
      libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\
      libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 \\
      libxcb-xfixes0 libxcb-xkb1

    pip install -r requirements.txt -r tests/requirements-dev.txt
    python up.py --verify
"""

ABORT_HELP = """\
PYTHON ABORTED NATIVELY. That is not a failing assertion. On offscreen Linux
these suites can abort in Qt's thread teardown -- it surfaces during whatever
work is in flight and reads exactly like a regression in it.

Re-run:

    python up.py --verify

If it aborts every time on the same test, that is worth looking at. If it
comes and goes, this change is not involved.
"""


KILLED_HELP = """\
THE TEST PROCESS WAS KILLED FROM OUTSIDE. No test failed and nothing crashed --
something stopped the run, and on a small runner that is almost always the
out-of-memory killer arriving part way through a long Qt suite.

Re-run:

    python up.py --verify

If it keeps dying at roughly the same point, run the suite on its own so you
can watch it, and close anything else heavy first:

    QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
"""


def run(label: str, args: list[str]) -> tuple[int, str]:
    """Stream to a temp file rather than capture_output: a long Qt suite emits
    megabytes, and buffering that in memory can get the run killed, which looks
    exactly like a failure."""
    print(f"  {label} ...", flush=True)
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8",
                                errors="replace") as fh:
        proc = subprocess.run(args, stdout=fh, stderr=subprocess.STDOUT, env=env)
        fh.seek(0)
        out = fh.read()
    return proc.returncode, out


def _step(label: str, args: list[str]) -> int:
    code, out = run(label, args)
    verdict = _outcome(code, out)
    print(_tail(out) if verdict != "pass"
          else "\n".join(out.strip().splitlines()[-3:]))
    if verdict == "env":
        print("\n" + ENV_HELP)
    elif verdict == "abort":
        print("\n" + ABORT_HELP)
    elif verdict == "killed":
        print("\n" + KILLED_HELP)
    elif verdict == "fail":
        print("\nFAILED -- the suite is not green. Nothing was reverted; "
              "`git diff` shows exactly what landed.")
    return code


def verify() -> int:
    code = _step("guard",
                 [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                  GUARD])
    if code != 0:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != 0:
            return code
    print("\nGreen.")
    return 0


def apply(check_only: bool) -> int:
    root = Path.cwd()
    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise SystemExit(globals().get("MISSING_HELP") or
                         f"run this from the root of a {REPO} checkout "
                         f"(no {SENTINEL_FILE} here)")
    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8"):
        raise SystemExit(f"already applied -- {SENTINEL!r} is present in "
                         f"{SENTINEL_FILE}")

    tree = Tree(root)
    edits(tree)
    tree.write(GUARD, GUARD_SOURCE)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        return 0

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    return verify()


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    refuse_to_shadow()
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    if args.finish:
        finish()
        return 0
    if args.verify:
        return verify()
    return apply(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
