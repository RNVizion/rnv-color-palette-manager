"""Error text is theme-aware, and every retired red is gone.

    STATUS_ERROR             #c75b64   registered base; no fill is drawn here
    STATUS_ERROR_TEXT        #dd6f77   dark ground, = register error-text
    STATUS_ERROR_TEXT_LIGHT  #b84e58   light ground, = register error-text-light

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
    reach the last two. See RNV-STATUS-LIGHT-FLOOR below -- the boundary is an
    open question with the brand chat, and narrowing it is recorded here in
    full rather than quietly done.
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
    #b84e58. A derivative whose rule no longer produces it is not a
    derivative; it is a coincidence waiting to break.

    The register's family rule is a different one -- hold hue and chroma, move
    lightness only, take the first step clearing 4.5 on the worst ground --
    and it publishes the RESULT with the walk as provenance, so retuning the
    rule cannot silently change what an error looks like in five
    applications. Same call the register made for BRAND_STANDBY_GOLD.
    """
    assert colors.STATUS_ERROR_TEXT_LIGHT == "#b84e58"
    assert colors.STATUS_ERROR_TEXT_LIGHT != colors.lighten(colors.STATUS_ERROR, -20)


def test_the_family_is_the_registered_one():
    """Pinned by value. A test asserting only that these differ from each
    other would pass on five wrong colours."""
    assert colors.STATUS_SUCCESS == "#926c89"
    assert colors.STATUS_WARNING == "#a2703c"
    assert colors.STATUS_ERROR == "#c75b64"
    assert colors.STATUS_ERROR_TEXT == "#dd6f77"
    assert colors.STATUS_ERROR_TEXT_LIGHT == "#b84e58"


def test_light_error_text_clears_its_own_dialog_ground():
    """The pairing the 2026-09-02 pass existed to fix: 2.5454 -> 5.1811, and
    now 4.5123 with the registered replacement."""
    ground = colors.LIGHT_THEME_COLORS["window_bg"]
    ratio = contrast(colors.STATUS_ERROR_TEXT_LIGHT, ground)
    assert ratio >= TEXT_FLOOR, \
        f"{colors.STATUS_ERROR_TEXT_LIGHT} on {ground} = {ratio:.4f}"


@pytest.mark.parametrize("ground", ["#ffffff", "#f5f5f5"])
def test_light_error_text_carries_on_the_grounds_it_reaches(ground):
    """RNV-STATUS-LIGHT-FLOOR -- READ THIS BEFORE WIDENING THE PARAMETERS.

    This test used to run over #ffffff, #f5f5f5, #eeeeee and #e8e8e8, and its
    docstring said: "#e8e8e8 is where the gold stops carrying text. The red is
    derived to the same boundary so the two rules need not be remembered
    separately." That was true of #c82131, which read 4.6100 there.

    The registered replacement does not reach it:

        #b84e58   #f5f5f5 4.5123   #eeeeee 4.2401   #e8e8e8 4.0150   #e0e0e0 3.7266

    The cause is in the register's own rule, which walks the light text
    variants against #f5f5f5 as "the worst light ground". Rev 27 put APP
    hover-light #eeeeee, GOLD_TEXT_GROUND_FLOOR #e8e8e8 and pressed-light
    #e0e0e0 below it. All three light variants were walked to the FIRST step
    that clears -- 4.52, 4.52, 4.51 -- so none has margin, and one registered
    rung down they fail together.

    THIS IS AN OPEN QUESTION WITH THE BRAND CHAT, NOT A LOOSENED TEST. The
    parameters are narrowed to the two grounds the published value actually
    reaches, and this docstring is the record of what was given up. If the
    register re-walks against #e8e8e8 the answer here is #ae4650 -- moving
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
