"""
Muted and disabled text: aligned to the ecosystem, and honest about which of
them anything actually paints.

`text_disabled` is live -- the batch export dialog and the menu bar both read
it. It is now #555555 dark / #aaaaaa light, matching the other four apps. Both
sit below every contrast floor and are meant to: WCAG 1.4.3 exempts text in an
inactive component, and disabled text that reads as clearly as enabled text is
not doing its job.

`text_secondary` is NOT painted anywhere. It is defined in all three palettes,
read into a local in ui/settings_dialog.py, and that local is never used. It is
kept and kept correct so wiring it up is one line. The tests below hold that
story to the code: if someone paints it, the "NOT CONSUMED" notes beside the
values become false and the run says so.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from ui.colors import (DARK_THEME_COLORS, IMAGE_MODE_COLORS,
                       LIGHT_THEME_COLORS)

THEMES = {
    "DARK": DARK_THEME_COLORS,
    "LIGHT": LIGHT_THEME_COLORS,
    "IMAGE": IMAGE_MODE_COLORS,
}
ROOT = pathlib.Path(__file__).resolve().parent.parent
COLORS_PY = ROOT / "ui" / "colors.py"

# The one place that reads the key without painting it. Named so the sweep
# below can tell a dead read from a live one.
KNOWN_DEAD_READ = "ui/settings_dialog.py"


def _luminance(value: str) -> float:
    h = value.lstrip("#")
    if len(h) == 8:                      # Qt #AARRGGBB
        h = h[2:]
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def _contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def test_all_three_palettes_carry_both_keys():
    """Guard the guard: every test below iterates THEMES."""
    assert set(THEMES) == {"DARK", "LIGHT", "IMAGE"}
    for name, theme in THEMES.items():
        for key in ("text_color", "text_secondary", "text_disabled"):
            assert key in theme, f"{name} has no {key}"


@pytest.mark.parametrize("name", sorted(THEMES))
def test_the_text_hierarchy_dims_in_order(name):
    """primary reads strongest, muted next, disabled faintest.

    Held as an ORDER rather than as three values, so a later retune of the ramp
    moves them together and this still passes.
    """
    theme = THEMES[name]
    ground = theme["card_bg"]            # a flat colour in all three palettes
    primary = _contrast(theme["text_color"], ground)
    muted = _contrast(theme["text_secondary"], ground)
    disabled = _contrast(theme["text_disabled"], ground)
    assert primary > muted > disabled, (
        f"{name}: primary {primary:.2f} / muted {muted:.2f} / "
        f"disabled {disabled:.2f} are not in descending order")


@pytest.mark.parametrize("name", sorted(THEMES))
def test_disabled_text_stays_visibly_disabled(name):
    """It is meant to fail the text floor. A disabled label that reads as
    clearly as an enabled one is not communicating anything."""
    theme = THEMES[name]
    ratio = _contrast(theme["text_disabled"], theme["card_bg"])
    assert ratio < 4.5, (
        f"{name}: disabled text reads {ratio:.2f}:1 -- at that strength it no "
        f"longer looks disabled")


def _references(key: str) -> list[str]:
    sites = []
    for path in ROOT.rglob("*.py"):
        parts = path.parts
        if any(p in parts for p in (".git", "__pycache__", "tests", "snapshots")):
            continue
        if path.name.startswith("test_") or path == COLORS_PY:
            continue
        # A delivery script sitting at the root mentions the key it moves.
        # Sweeping it makes the guard fail on the very run that installs it --
        # the same trap the repos' placement guards already exempt `up*.py` for.
        if path.parent == ROOT and path.name.startswith("up"):
            continue
        if key in path.read_text(encoding="utf-8", errors="replace"):
            sites.append(path.relative_to(ROOT).as_posix())
    return sorted(sites)


def test_the_sweep_is_actually_reading_something():
    """A walk that finds nothing passes forever."""
    assert _references("text_disabled"), (
        "the sweep cannot find text_disabled, which IS painted -- it would not "
        "find text_secondary either")


def test_the_not_consumed_note_is_still_true():
    """Both directions. The note beside `text_secondary` tells the next reader
    nothing paints it. If that stops being true the note is a lie, and a lie in
    a palette is how a value gets trusted that should not be."""
    sites = _references("text_secondary")
    assert sites == [KNOWN_DEAD_READ], (
        f"text_secondary is now referenced in {sites}. If it is being painted, "
        f"delete the NOT CONSUMED notes in ui/colors.py -- they are no longer "
        f"true.")

    notes = len(re.findall(r"#\s*NOT CONSUMED",
                           COLORS_PY.read_text(encoding="utf-8")))
    assert notes == 3, (
        f"expected a NOT CONSUMED note beside each of the three "
        f"text_secondary values, found {notes}")


def test_the_dead_read_is_still_dead():
    """ui/settings_dialog.py assigns the key to a local and never uses it,
    which is exactly why a grep for `text_secondary` looks live."""
    source = (ROOT / KNOWN_DEAD_READ).read_text(encoding="utf-8")
    # The lookarounds are load-bearing: `\b` happily matches the identifier
    # INSIDE the string key of `theme.get('text_secondary', ...)`, which is the
    # dict lookup and not a use of the local. Without them this test fails on
    # the very line it exists to describe.
    bare = re.compile(r"(?<!['\"])\btext_secondary\b(?!['\"])")
    assigns, uses = [], []
    for i, line in enumerate(source.splitlines(), 1):
        for match in bare.finditer(line):
            after = line[match.end():].lstrip()
            (assigns if after.startswith("=") and not after.startswith("==")
             else uses).append(f"{i}: {line.strip()[:60]}")
    assert len(assigns) == 1, f"expected one assignment, found {assigns}"
    assert not uses, (
        f"the text_secondary local is now used -- it is live, and ui/colors.py "
        f"still says it is not: {uses}")
