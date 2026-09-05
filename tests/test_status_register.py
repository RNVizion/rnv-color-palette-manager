"""Every status value in this application is the register's. RNV-STATUS-GUARD

Ruled by Chris on 2026-09-02, reading the STATUS family across the fleet.
Three values disagreed with the register; all three collapse.

A status colour is not decoration. It carries MEANING -- success, warning,
error -- and the meaning is the same in every RNV product, which is why the
register owns the value and an application must not have a second opinion.
This guard is the thing that stops the second opinion coming back.
"""
from __future__ import annotations

import re
from pathlib import Path

from ui import colors

ROOT = Path(__file__).resolve().parent.parent


def _palettes():
    from ui.colors import DARK_THEME_COLORS as D, LIGHT_THEME_COLORS as L, IMAGE_MODE_COLORS as I; P={'dark':D,'light':L,'image':I}
    return P


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hexv):
    h = hexv.lstrip("#")
    t = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return 0.2126 * _lin(t[0]) + 0.7152 * _lin(t[1]) + 0.0722 * _lin(t[2])


def _contrast(a, b):
    la, lb = _luminance(a), _luminance(b)
    hi, lo = (la, lb) if la >= lb else (lb, la)
    return (hi + 0.05) / (lo + 0.05)


STRAYS = {
    "#4caf50",   # Material green, ruled out 2026-09-02
    "#ff6b6b",   # this app's own dark error text, ruled out 2026-09-02
    # RNV-STATUS-FAMILY (2026-09-03), the Bootstrap family and its
    # two orphans. #e56b77 and #c82131 were derived from #dc3545;
    # with the base retired they are values derived from something
    # no longer in the palette, which is the #c4a458 failure.
    "#28a745", "#ffc107", "#dc3545", "#e56b77", "#c82131",
}


def test_the_strays_are_gone_from_every_palette():
    for mode, palette in _palettes().items():
        bad = {k: v for k, v in palette.items()
               if isinstance(v, str) and v.lower() in STRAYS}
        assert not bad, f"{mode} still holds a retired status value: {bad}"


def test_the_three_ruled_values_are_the_register_s():
    """Not "some green" -- THE green. An app that picks its own status colour
    has an opinion about what success means, which is the register's job."""
    # RNV-STATUS-FAMILY (2026-09-03): the register replaced all
    # three. The green and the red were one olive under
    # deuteranopia at about 4 apart; the amber read 1.63 on
    # #ffffff against a 3:1 fill floor. Still pinned by value --
    # an app that picks its own status colour has an opinion
    # about what success means, which is the register's job.
    assert colors.STATUS_SUCCESS == "#926c89"
    assert colors.STATUS_WARNING == "#a2703c"
    assert colors.STATUS_ERROR == "#c75b64"
    # #e56b77 was derived from #dc3545 and orphaned when the
    # base was retired, so it moves with it.
    assert colors.STATUS_ERROR_TEXT == "#dd6f77"


def test_the_palettes_are_wired_through_the_constants_not_rewritten():
    """Swapping one literal for another passes the value check and defeats
    the point: the constant is what a later register change moves."""
    src = (ROOT / "ui" / "colors.py").read_text(encoding="utf-8-sig")
    for key, const in (("success", "STATUS_SUCCESS"), ("warning", "STATUS_WARNING")):
        found = len(re.findall(r"'%s':\s+%s\b" % (key, const), src))
        assert found == 3, f"{key} is wired through {const} in {found} palettes, not 3"


def test_the_dark_error_text_still_clears_on_every_dark_ground():
    """The 2026-09-02 move cost 0.87 of headroom and this is the
    check that said it could afford it. RNV-STATUS-FAMILY
    (2026-09-03) takes a little more: #dd6f77 reads 4.5210 on
    APP card against #e56b77's 4.5801 -- still above the floor,
    on the grounds this app
    actually paints."""
    for ground in ("#000000", "#1a1a1a", "#2a2a2a"):
        assert _contrast(colors.STATUS_ERROR_TEXT, ground) >= 4.5, (
            f"error text {colors.STATUS_ERROR_TEXT} on {ground} is short")
