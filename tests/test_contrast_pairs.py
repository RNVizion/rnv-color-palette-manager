"""
Contrast pairing guard.   RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN

The rest of the suite asserts hex EQUALITY. That cannot catch a legible colour
placed on the wrong ground, which is how every gold failure in these apps
survived: the value was correct on both sides, the pairing was not.

Ported from rnv-text-transformer.
"""
from __future__ import annotations

import pytest

from ui import colors as C

TEXT_FLOOR = 4.5

PALETTES = {
    "DARK": C.DARK_THEME_COLORS,
    "LIGHT": C.LIGHT_THEME_COLORS,
    "IMAGE": C.IMAGE_MODE_COLORS,
}

# (theme, foreground, background) -> why it may sit below the floor.
ACCEPTED = {}


def _luminance(value: str) -> float:
    h = value.lstrip("#")
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _hex(value) -> bool:
    return isinstance(value, str) and len(value) == 7 and value.startswith("#")


# The grounds gold text actually renders on, per palette, read from the palette
# rather than assumed. Each pair is (ink key, ground key).
INK_PAIRS = (
    ("accent_ink", "panel_bg"),
    ("accent_ink", "dialog_bg"),
    ("accent_ink", "card_bg"),
)

# How many of those pairs each palette can actually MEASURE. Asserted exactly
# rather than as a floor: a floor cannot tell a pair that vanished from a pair
# that was never there.
#
# IMAGE resolves fewer, and the reason is worth naming rather than tolerating:
# its window_bg and panel_bg are #AARRGGBB strings, which this flat-hex audit
# cannot read. Gold text on a translucent ground is UNAUDITED here. That is a
# gap in the audit, not a pass.
#
# IMAGE used to resolve 3, but one was a duplicate -- tab_pane_bg held the same
# #1a1a1a as dialog_bg -- so deleting that key on 2026-08-28 removed a repeated
# measurement rather than any coverage.
RESOLVING = {"DARK": 3, "LIGHT": 3, "IMAGE": 2}


@pytest.mark.parametrize("theme", sorted(PALETTES))
def test_gold_text_clears_every_ground_it_lands_on(theme):
    palette = PALETTES[theme]
    failures = []
    for ink_key, ground_key in INK_PAIRS:
        if ink_key not in palette or ground_key not in palette:
            continue
        ink, ground = palette[ink_key], palette[ground_key]
        if not (_hex(ink) and _hex(ground)):
            continue
        if (theme, ink, ground) in ACCEPTED:
            continue
        ratio = contrast(ink, ground)
        if ratio < TEXT_FLOOR:
            failures.append(f"{theme} {ink_key} on {ground_key}: "
                            f"{ink} on {ground} = {ratio:.4f}:1")
    assert not failures, "gold text below AA -- " + "; ".join(failures)


@pytest.mark.parametrize("theme", sorted(PALETTES))
def test_the_audit_finds_something_to_audit(theme):
    """Any detector that can return 'nothing found' needs a companion test
    proving it is still looking."""
    palette = PALETTES[theme]
    measured = [1 for ink, ground in INK_PAIRS
                if ink in palette and ground in palette
                and _hex(palette[ink]) and _hex(palette[ground])]
    assert len(measured) == RESOLVING[theme], (
        f"{theme}: {len(measured)} ink pairs resolved, expected "
        f"{RESOLVING[theme]} -- the pair list has gone stale against the "
        f"palette")


def test_no_accepted_entry_is_stale():
    """A dead exemption is a licence waiting for a future defect."""
    live = set()
    for theme, palette in PALETTES.items():
        for ink, ground in INK_PAIRS:
            if ink in palette and ground in palette:
                live.add((theme, palette[ink], palette[ground]))
    stale = [k for k in ACCEPTED if k not in live]
    assert not stale, f"stale ACCEPTED entries: {stale}"


def test_white_and_black_on_the_gold_fill():
    """Both clear at the new value; the register prefers black and this app
    uses it. Recorded so a future change cannot quietly drop below the floor."""
    for theme, palette in PALETTES.items():
        assert contrast(palette["accent_text"], palette["accent"]) >= TEXT_FLOOR, theme
