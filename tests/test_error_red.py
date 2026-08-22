"""Error text is theme-aware, and the Material red is gone.

    STATUS_ERROR             #dc3545   registered base, derived from only
    STATUS_ERROR_TEXT        #ff6b6b   dark ground
    STATUS_ERROR_TEXT_LIGHT  #c82131   light ground, derived

Before this pass a single #ff6b6b served both modes and read 2.5454 on the
light dialog ground -- below the text floor and below the UI floor too.
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


def test_the_light_error_text_is_derived_not_written():
    assert colors.STATUS_ERROR_TEXT_LIGHT == colors.lighten(colors.STATUS_ERROR, -20)
    assert colors.STATUS_ERROR_TEXT_LIGHT != colors.STATUS_ERROR


def test_light_error_text_clears_its_own_dialog_ground():
    """The pairing this pass existed to fix: 2.5454 -> 5.1811."""
    ground = colors.LIGHT_THEME_COLORS["window_bg"]
    ratio = contrast(colors.STATUS_ERROR_TEXT_LIGHT, ground)
    assert ratio >= TEXT_FLOOR, \
        f"{colors.STATUS_ERROR_TEXT_LIGHT} on {ground} = {ratio:.4f}"


@pytest.mark.parametrize("ground", ["#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"])
def test_light_error_text_carries_to_the_published_boundary(ground):
    """#e8e8e8 is where the gold stops carrying text. The red is derived to
    the same boundary so the two rules need not be remembered separately."""
    ratio = contrast(colors.STATUS_ERROR_TEXT_LIGHT, ground)
    assert ratio >= TEXT_FLOOR, \
        f"{colors.STATUS_ERROR_TEXT_LIGHT} on {ground} = {ratio:.4f}"


def test_dark_error_text_was_left_alone_and_still_clears():
    """Dark was never short. Asserted so a later pass cannot move it quietly
    while everyone is looking at light."""
    assert colors.STATUS_ERROR_TEXT == "#ff6b6b"
    for name in ("DARK", "IMAGE_MODE"):
        palette = getattr(colors, name + "_THEME_COLORS", None) or \
            getattr(colors, "IMAGE_MODE_COLORS")
        ratio = contrast(colors.STATUS_ERROR_TEXT, palette["window_bg"])
        assert ratio >= TEXT_FLOOR, f"{name}: {ratio:.4f}"


def test_the_two_error_texts_are_not_the_same_value():
    """If these ever collapse onto one value, one of the two modes is short
    again -- which is the state this pass found the app in."""
    assert colors.STATUS_ERROR_TEXT != colors.STATUS_ERROR_TEXT_LIGHT


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


def test_that_check_is_actually_looking():
    """Guard the guard. The sweep above walks three palettes; if they ever
    turn up empty it would pass while checking nothing."""
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
