"""
The main button's plate steps on press.

RULED 2026-08-26, after rendering all three states side by side in all three
modes across the five desktop apps. The basic black-and-white scheme moves the
plate twice: rest -> hover lifts it, hover -> pressed lifts it again. The label
flips on press independently.

This app used to hold the plate still on press, so pressing changed only the
label. Two apps did it that way and three stepped; the step won.

What these tests hold is the RELATIONSHIP, not the byte. If the ramp is
retuned later the values move together and these still pass; if someone
collapses pressed back onto hover, they fail and say why.
"""
from __future__ import annotations

import pytest

from ui.colors import (DARK_THEME_COLORS, IMAGE_MODE_COLORS,
                       LIGHT_THEME_COLORS)

THEMES = {
    "DARK": DARK_THEME_COLORS,
    "LIGHT": LIGHT_THEME_COLORS,
    "IMAGE": IMAGE_MODE_COLORS,
}


def _lum(value: str) -> float:
    h = value.lstrip("#")
    if len(h) == 8:                      # Qt #AARRGGBB
        h = h[2:]
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def test_all_three_themes_are_present():
    """Guard the guard. Every test below iterates THEMES; if a rename emptied
    it they would all pass while checking nothing."""
    assert set(THEMES) == {"DARK", "LIGHT", "IMAGE"}
    for name, theme in THEMES.items():
        for key in ("main_btn_bg", "main_btn_hover_bg", "main_btn_pressed_bg",
                    "main_btn_text", "main_btn_pressed_text"):
            assert key in theme, f"{name} has no {key}"


@pytest.mark.parametrize("name", sorted(THEMES))
def test_the_plate_steps_on_press(name):
    theme = THEMES[name]
    hover, pressed = theme["main_btn_hover_bg"], theme["main_btn_pressed_bg"]
    assert hover != pressed, (
        f"{name}: pressed plate {pressed} is the hover plate. The press then "
        f"changes only the label, which is the behaviour this ruling retired.")


@pytest.mark.parametrize("name", sorted(THEMES))
def test_the_plate_lifts_rather_than_darkens(name):
    """Each state is lighter than the one before it, in every mode.

    Light mode inverts the ground but not this: the plate goes dark on hover
    and then one step lighter on press, so the movement reads the same way in
    both themes.
    """
    theme = THEMES[name]
    rest, hover, pressed = (theme["main_btn_bg"], theme["main_btn_hover_bg"],
                            theme["main_btn_pressed_bg"])
    if name == "LIGHT":
        # rest is the white card; hover drops to the dark plate deliberately.
        assert _lum(hover) < _lum(rest), f"{name}: hover should darken from rest"
    else:
        assert _lum(hover) > _lum(rest), f"{name}: hover should lift from rest"
    assert _lum(pressed) > _lum(hover), (
        f"{name}: pressed plate {pressed} does not lift from hover {hover}")


@pytest.mark.parametrize("name", sorted(THEMES))
def test_the_label_flips_on_press(name):
    """The plate moving is only half of it. The label inverts at the same
    moment, and that is what makes the press read as a press rather than as a
    hover that got brighter."""
    theme = THEMES[name]
    resting, pressed = theme["main_btn_text"], theme["main_btn_pressed_text"]
    assert resting != pressed, f"{name}: the label does not change on press"
    assert (_lum(resting) > 0.5) != (_lum(pressed) > 0.5), (
        f"{name}: {resting} -> {pressed} is not an inversion")
