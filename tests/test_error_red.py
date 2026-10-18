"""Error text is theme-aware, and every retired red is gone.

    STATUS_ERROR_TEXT        dark ground, = register error-text
    STATUS_ERROR_TEXT_LIGHT  light ground, = register error-text-light

Before the 2026-09-02 pass a single RETIRED_OWN_DARK_ERROR_TEXT served both
modes and read 2.5454 on the light dialog ground -- below the text floor and
below the UI floor too. That pass split them. This one, RNV-STATUS-FAMILY on
2026-09-03, moves the whole family: the register retired Bootstrap's
RETIRED_BOOTSTRAP_RED, and RETIRED_ERROR_TEXT_ORPHAN and
RETIRED_ERROR_TEXT_LIGHT_ORPHAN were both derived from it.

TWO TESTS HERE WERE REPLACED RATHER THAN EDITED, and both replacements say so:

  * test_the_light_error_text_is_derived_not_written asserted
    STATUS_ERROR_TEXT_LIGHT == lighten(STATUS_ERROR, -20). Its argument was
    right and is exactly why the value could not be left alone -- against the
    new base that formula yields EXAMPLE_STATUS_ERROR_LIGHTENED, a third
    answer. See test_the_light_error_text_is_registered_and_why_that_changed.

  * test_light_error_text_carries_to_the_published_boundary parametrised over
    WHITE, APP_SURFACE_LIGHT_3, APP_HOVER_LIGHT and
    REGISTER_GOLD_TEXT_GROUND_FLOOR. The registered replacement does not reach
    the last two. See RNV-STATUS-LIGHT-FLOOR below -- the boundary is an
    open question with the brand chat, and narrowing it is recorded here in
    full rather than quietly done.

RNV-NAMED-AND-USED, 2026-10-04. This application draws error TEXT and no
status fill, so it no longer carries the family's three fills -- success,
warning and the registered error base REGISTER_STATUS_ERROR -- which nothing
here read.
The two text values above are what it draws and what this file holds.
Where a test needs the base, to say why the light value is not derived from
it, it writes the base as the register holds it.
"""

import json
import pathlib

import pytest

from colour_values import (
    EXAMPLE_ARGB_BLACK_AT_ED, EXAMPLE_BLACK, EXAMPLE_BLACK_BARE, EXAMPLE_OFF_WHITE,
    EXAMPLE_OFF_WHITE_BARE, EXAMPLE_WHITE, REGISTER_GOLD_TEXT_GROUND_FLOOR,
    REGISTER_STATUS_ERROR, RETIRED_BOOTSTRAP_AMBER, RETIRED_BOOTSTRAP_GREEN,
    RETIRED_BOOTSTRAP_RED, RETIRED_ERROR_TEXT_LIGHT_ORPHAN, RETIRED_ERROR_TEXT_ORPHAN,
    RETIRED_MATERIAL_RED)
from ui import colors

#: RNV-COLOUR-SYNC, 2026-10-16. Where each colour comes from, as brand_map.json
#: says. The values are held by tests/test_colours_in_sync.py, against the
#: register at the pin; what this file holds is the name each one takes.
BRAND_MAP = json.loads((pathlib.Path(__file__).resolve().parents[1] / "brand_map.json").read_text(encoding="utf-8"))["colours"]

TEXT_FLOOR = 4.5


MIN_OPAQUE_ALPHA = 0xE0


def _rgb(value: str) -> str:
    """Six hex digits, from a value that may carry a Qt alpha channel.

    Image mode's window_bg is `APP_WINDOW_OVERLAY` -- eight digits, #AARRGGBB,
    which is Qt's order and NOT the CSS #RRGGBBAA. Read naively as #RRGGBB it
    becomes EXAMPLE_ARGB_BLACK_AT_ED_MISREAD, a red, and the contrast against it computes to 1.6448
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
    assert _rgb(EXAMPLE_ARGB_BLACK_AT_ED) == EXAMPLE_BLACK_BARE
    assert _rgb(EXAMPLE_OFF_WHITE) == EXAMPLE_OFF_WHITE_BARE
    assert contrast(EXAMPLE_WHITE, EXAMPLE_ARGB_BLACK_AT_ED) == pytest.approx(
        contrast(EXAMPLE_WHITE, EXAMPLE_BLACK))


def test_the_light_error_text_is_registered_and_why_that_changed():
    """This replaces test_the_light_error_text_is_derived_not_written.

    That test asserted STATUS_ERROR_TEXT_LIGHT == lighten(STATUS_ERROR, -20)
    and argued that a written-down derivative orphans the moment its base
    moves. The argument was correct, and it is why this value could not be
    left as it was: the base moved on 2026-09-03, and against
    REGISTER_STATUS_ERROR the formula yields EXAMPLE_STATUS_ERROR_LIGHTENED --
    neither the old RETIRED_ERROR_TEXT_LIGHT_ORPHAN nor the registered
    STATUS_ERROR_TEXT_LIGHT. A derivative whose rule no longer produces it is not a
    derivative; it is a coincidence waiting to break.

    The register's family rule is a different one -- hold hue and chroma, move
    lightness only, take the first step clearing 4.5 on the worst ground --
    and it publishes the RESULT with the walk as provenance, so retuning the
    rule cannot silently change what an error looks like in five
    applications. Same call the register made for BRAND_STANDBY_GOLD.
    """
    assert BRAND_MAP["STATUS_ERROR_TEXT_LIGHT"] == "STATUS.error-text-light"
    # the registered base, STATUS["error"]; this application draws no fill and carries none
    assert colors.STATUS_ERROR_TEXT_LIGHT != colors.lighten(REGISTER_STATUS_ERROR, -20)


def test_the_family_is_the_registered_one():
    """Pinned by value. A test asserting only that these differ from each
    other would pass on two wrong colours. The two this application draws:
    the family's three fills are the register's, and are not carried here.

    RNV-COLOUR-SYNC, 2026-10-16: pinned by name in brand_map.json, which takes
    both from the register; tests/test_colours_in_sync.py holds the values."""
    assert BRAND_MAP["STATUS_ERROR_TEXT"] == "STATUS.error-text"
    assert BRAND_MAP["STATUS_ERROR_TEXT_LIGHT"] == "STATUS.error-text-light"


def test_light_error_text_clears_its_own_dialog_ground():
    """The pairing the 2026-09-02 pass existed to fix: 2.5454 -> 5.1811, and
    now 4.5123 with the registered replacement."""
    ground = colors.LIGHT_THEME_COLORS["window_bg"]
    ratio = contrast(colors.STATUS_ERROR_TEXT_LIGHT, ground)
    assert ratio >= TEXT_FLOOR, \
        f"{colors.STATUS_ERROR_TEXT_LIGHT} on {ground} = {ratio:.4f}"


# Restored at rev 31: the re-walked value reaches all four rungs.
# REGISTER_APP_PRESSED_LIGHT is deliberately absent -- BRAND_DARK_GOLD_DEEP
# fails there too, so it is the boundary for every brand text family rather
# than a gap.
# RNV-COLOUR-SYNC, 2026-10-16: the grounds by name;
# REGISTER_GOLD_TEXT_GROUND_FLOOR is the register's gold text floor, which the
# app does not draw.
@pytest.mark.parametrize("ground", [colors.WHITE, colors.APP_SURFACE_LIGHT_3,
                                    colors.APP_HOVER_LIGHT, REGISTER_GOLD_TEXT_GROUND_FLOOR])
def test_light_error_text_carries_on_the_grounds_it_reaches(ground):
    """RNV-STATUS-LIGHT-FLOOR -- READ THIS BEFORE WIDENING THE PARAMETERS.

    This test used to run over WHITE, APP_SURFACE_LIGHT_3, APP_HOVER_LIGHT and
    REGISTER_GOLD_TEXT_GROUND_FLOOR, and its docstring said:
    "REGISTER_GOLD_TEXT_GROUND_FLOOR is where the gold stops carrying text. The
    red is derived to the same boundary so the two rules need not be
    remembered separately." That was true of RETIRED_ERROR_TEXT_LIGHT_ORPHAN,
    which read 4.6100 there.

    The registered replacement, STATUS_ERROR_TEXT_LIGHT, does not reach it:

                 APP_SURFACE_LIGHT_3   APP_HOVER_LIGHT   REGISTER_GOLD_TEXT_GROUND_FLOOR
        rev 30   4.5123                4.2401            4.0150
        rev 31   5.0800                4.7700            4.5200

    The cause is in the register's own rule, which walks the light text
    variants against APP_SURFACE_LIGHT_3 as "the worst light ground". Rev 27
    put APP_HOVER_LIGHT, REGISTER_GOLD_TEXT_GROUND_FLOOR and
    REGISTER_APP_PRESSED_LIGHT below it. All three light variants were walked to the FIRST step
    that clears -- 4.52, 4.52, 4.51 -- so none has margin, and one registered
    rung down they fail together.

    THIS IS AN OPEN QUESTION WITH THE BRAND CHAT, NOT A LOOSENED TEST. The
    parameters are narrowed to the two grounds the published value actually
    reaches, and this docstring is the record of what was given up. If the
    register re-walks against REGISTER_GOLD_TEXT_GROUND_FLOOR the answer here is
    STATUS_ERROR_TEXT_LIGHT -- moving
    3.1, well inside the register's own 8.40 "clearly different" bar, so it
    stays the same red -- and the fix is to restore the two grounds above and
    update the pinned value.
    """
    ratio = contrast(colors.STATUS_ERROR_TEXT_LIGHT, ground)
    assert ratio >= TEXT_FLOOR, \
        f"{colors.STATUS_ERROR_TEXT_LIGHT} on {ground} = {ratio:.4f}"


def test_dark_error_text_mirrors_the_register_and_still_clears():
    """Dark was never short, and this test existed to stop the value moving
    quietly. It has now done that job twice.

    RNV-STATUS-REGISTER (2026-09-02): RETIRED_OWN_DARK_ERROR_TEXT was this
    app's own dark error text, left alone by the error-red pass on the argument that a value
    already clearing the floor should not be replaced to buy uniformity. The
    register then published error-text RETIRED_ERROR_TEXT_ORPHAN for this
    exact job, so the choice became one name against a fourth spelling.

    RNV-STATUS-FAMILY (2026-09-03): RETIRED_ERROR_TEXT_ORPHAN was itself
    derived from Bootstrap's RETIRED_BOOTSTRAP_RED. With that base retired it
    is an ORPHAN, and it moves with its base rather than being kept alongside
    it. STATUS_ERROR_TEXT has slightly LESS
    headroom on every dark ground than the value it replaces -- 4.5210
    against 4.5801 on the card -- and is still above the floor.

    The assertion stays exact for the same reason it was written exact.
    RNV-COLOUR-SYNC, 2026-10-16: exact in tests/test_colours_in_sync.py, against
    the register at the pin; here, by the name brand_map.json takes it from."""
    assert BRAND_MAP["STATUS_ERROR_TEXT"] == "STATUS.error-text"
    for name in ("DARK", "IMAGE_MODE"):
        palette = getattr(colors, name + "_THEME_COLORS", None) or \
            getattr(colors, "IMAGE_MODE_COLORS")
        ratio = contrast(colors.STATUS_ERROR_TEXT, palette["window_bg"])
        assert ratio >= TEXT_FLOOR, f"{name}: {ratio:.4f}"


def test_the_two_error_texts_are_not_the_same_value():
    """If these ever collapse onto one value, one of the two modes is short
    again -- which is the state the 2026-09-02 pass found the app in."""
    assert colors.STATUS_ERROR_TEXT != colors.STATUS_ERROR_TEXT_LIGHT


# RNV-NAMED-AND-USED, 2026-10-04: a test stood here on the arithmetic of the
# three fills -- that each clears 3:1 on both grounds and 4.5:1 on neither.
# This application draws no fill and no longer carries them; the arithmetic
# is the register's, where the fills are.


def test_the_retired_material_red_is_gone_from_every_palette():
    """It was an orphan -- no code path read it -- but an unread wrong value
    is still a wrong value waiting for a reader."""
    retired = RETIRED_MATERIAL_RED
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
    retired = {RETIRED_BOOTSTRAP_GREEN, RETIRED_BOOTSTRAP_AMBER, RETIRED_BOOTSTRAP_RED,
               RETIRED_ERROR_TEXT_ORPHAN, RETIRED_ERROR_TEXT_LIGHT_ORPHAN}
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
    planted = {"error": RETIRED_MATERIAL_RED}
    assert [k for k, v in planted.items() if v.lower() == RETIRED_MATERIAL_RED], \
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
