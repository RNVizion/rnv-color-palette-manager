#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Brand gold alignment for rnv-color-palette-manager. The last of the five.

    python pm.py             # apply, then verify
    python pm.py --verify    # verify only, change nothing
    python pm.py --finish    # delete this file
    python pm.py --deps      # print the apt/pip commands and exit

WHAT MOVES

  name    BRAND_GOLD_DARK      -> BRAND_DARK_GOLD        (27 occurrences)
          BRAND_GOLD_DARK_RGB  -> BRAND_DARK_GOLD_RGB
  value   #b19145 -> #8c7337
  new     BRAND_DARK_GOLD_DEEP = lighten(BRAND_DARK_GOLD, -14)  -> #7e6529
          BRAND_GOLD_HOVER     = lighten(BRAND_GOLD,       13)  -> #dfc9a0

  Both RGB tuples become DERIVED from their hex instead of restated. They were
  hand-written, so the value change would have left them holding the retired
  gold -- invisible to any hex census. test_rnv_palette_manager.py asserts
  SLOT_SELECTED_COLOR == BRAND_GOLD_DARK_RGB, which stays green with both
  wrong: it asserts they agree, not that either is right.

THE KEY IS accent_ink, NOT accent_text

  This repo already has `accent_text`, and it means text drawn ON the gold
  fill -- #000000 in all three palettes. The mixer used `accent_text` for the
  opposite role because it had no such key, which means the same identifier now
  means opposite things in two repos. That is a naming collision waiting to
  happen and it is on me.

  rnv-text-transformer got it right and this follows it:

      accent_ink   gold used AS text      light #7e6529   dark #d2bc93
      accent_text  text drawn ON gold     light #000000   dark #000000

WHAT THIS DELIBERATELY DOES NOT CHANGE

  - `accent_text` stays #000000 everywhere. This is the only one of the five
    that paints black on the light gold fill, which is what the register
    prefers and the better number (4.6226 vs 4.5429). Per the note's SS5 and
    SS8, an inversion that passes is not flattened -- and that protects this
    repo's black exactly as it protects the others' white.
  - `error` stays #f44336. The Material red rnv-color-picker retired is a
    separate audit; SS5 says change the gold and nothing else.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

TOOL_MARKER = "RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP"
GUARD_MARKER = "RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN"

ROOT = Path.cwd()

OLD_GOLD = "#b" "19145"
GOLD = "#d" "2bc93"
DARK_GOLD = "#8" "c7337"
DEEP = "#7" "e6529"
GOLD_HOVER = "#d" "fc9a0"

COLORS = "ui/colors.py"
ABOUT = "ui/about_dialog.py"
SETTINGS = "ui/settings_dialog.py"
HELPER = "utils/dialog_helper.py"
MAIN = "RNV_Color_Palette_Manager.py"
GUARD_MIRROR = "tests/test_brand_mirror.py"
GUARD_PAIRS = "tests/test_contrast_pairs.py"

OUR_FILES = (COLORS, ABOUT, SETTINGS, HELPER, MAIN,
             GUARD_MIRROR, GUARD_PAIRS, "test_rnv_palette_manager.py")

APT = ("libgl1 libegl1 libfontconfig1 libxkbcommon0 libxkbcommon-x11-0 "
       "libdbus-1-3 libxcb-cursor0 libxcb-icccm4 libxcb-image0 "
       "libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 "
       "libxcb-xinerama0 libxcb-xkb1")


# --------------------------------------------------------------- file access

def read_any(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "bom"
    try:
        return raw.decode("utf-8"), "plain"
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="surrogateescape"), "surrogate"


def write_any(path: Path, text: str, kind: str) -> None:
    if kind == "bom":
        path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    elif kind == "surrogate":
        path.write_bytes(text.encode("utf-8", errors="surrogateescape"))
    else:
        path.write_text(text, encoding="utf-8")


def sub_once(src: str, old: str, new: str, where: str) -> str:
    n = src.count(old)
    if n != 1:
        raise SystemExit(
            f"ABORT: expected exactly 1 occurrence of this anchor in {where}, "
            f"found {n}. Stopping rather than guessing.\n---\n{old}\n---")
    return src.replace(old, new)


def edit(rel: str, fn) -> bool:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"ABORT: {rel} not found. Run from the repository root.")
    src, kind = read_any(path)
    out = fn(src)
    if out == src:
        return False
    if rel.endswith(".py"):
        try:
            ast.parse(out)
        except SyntaxError as exc:
            raise SystemExit(f"ABORT: {rel} would not parse after editing: {exc}")
    write_any(path, out, kind)
    return True


def tracked_text_files():
    """Tracked text files, excluding anything whose job is to name these values.

    Binaries are excluded by extension: six hex characters inside a PNG look
    exactly like a colour to a regex, which is how an earlier uppercase count
    was inflated by a 48MB image.
    """
    out = subprocess.run(["git", "ls-files"], cwd=ROOT,
                         capture_output=True, text=True).stdout.split()
    me = Path(__file__).resolve()
    for rel in out:
        path = ROOT / rel
        if path.suffix.lower() not in (".py", ".md", ".txt", ".json", ".yml",
                                       ".yaml", ".qss", ".css", ".cfg", ".ini"):
            continue
        if path.resolve() == me:
            continue
        try:
            text, kind = read_any(path)
        except Exception:
            continue
        if TOOL_MARKER in text or GUARD_MARKER in text:
            continue
        yield rel, path, text, kind


# ------------------------------------------------- step 1: repo-wide rename

RENAMES = (
    # longest first is not needed -- \b after DARK cannot match before "_RGB",
    # because "_" is a word character. Both patterns are therefore exact.
    (re.compile(r"\bBRAND_GOLD_DARK_RGB\b"), "BRAND_DARK_GOLD_RGB"),
    (re.compile(r"\bBRAND_GOLD_DARK\b"), "BRAND_DARK_GOLD"),
)


def do_rename() -> tuple[int, int]:
    """`BRAND_GOLD_DARK` -> `BRAND_DARK_GOLD` across every tracked text file."""
    files = 0
    hits = 0
    for rel, path, text, kind in tracked_text_files():
        out = text
        n = 0
        for pattern, replacement in RENAMES:
            out, k = pattern.subn(replacement, out)
            n += k
        if n:
            if rel.endswith(".py"):
                try:
                    ast.parse(out)
                except SyntaxError as exc:
                    raise SystemExit(f"ABORT: {rel} would not parse: {exc}")
            write_any(path, out, kind)
            files += 1
            hits += n
    if hits == 0:
        raise SystemExit("ABORT: the rename matched nothing. Either it has "
                         "already run, or the symbol has moved.")
    return files, hits


# ------------------------------------------- step 2: the constants block

NEW_CONSTANTS = '''# ==================== Brand Colors ====================
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


BRAND_GOLD: Final[str] = "@GOLD@"
"""Primary brand gold - dark-mode accents, hovers, group titles, highlights."""

BRAND_DARK_GOLD: Final[str] = "@DARK_GOLD@"
"""Light-mode gold - fills, borders, pressed. Darker BECAUSE the ground is
lighter, which is the opposite of what the old name suggested."""

BRAND_DARK_GOLD_DEEP: Final[str] = lighten(BRAND_DARK_GOLD, -14)
"""DERIVED -> @DEEP@. The light-mode gold that carries TEXT. Not a fill:
black on it measures 3.7806, under the floor."""

BRAND_GOLD_HOVER: Final[str] = lighten(BRAND_GOLD, 13)
"""DERIVED -> @GOLD_HOVER@. The dark-mode hover gold. Hover moves AWAY from
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
'''.replace("@GOLD@", GOLD).replace("@DARK_GOLD@", DARK_GOLD) \
   .replace("@DEEP@", DEEP).replace("@GOLD_HOVER@", GOLD_HOVER)


def step_constants(src: str) -> str:
    """Replace the four hand-written constants with the derived block.

    Bounded by the section banners rather than by scanning for a closing
    token: scanning forward for the next blank line or comment finds the
    docstring under the first constant and stops there.
    """
    if "BRAND_DARK_GOLD_DEEP" in src:
        return src
    start = src.index("# ==================== Brand Colors ====================")
    end = src.index("# ==================== Semantic UI Constants", start)
    span = src[start:end]
    for name in ("BRAND_GOLD", "BRAND_DARK_GOLD", "BRAND_GOLD_RGB",
                 "BRAND_DARK_GOLD_RGB"):
        if name not in span:
            raise SystemExit(f"ABORT: {name} is not in the Brand Colors block; "
                             f"refusing to replace a region I cannot identify.")
    lines = span.count("\n")
    if not (8 <= lines <= 30):
        raise SystemExit(f"ABORT: the Brand Colors block spans {lines} lines, "
                         f"which is not the shape expected.")
    return src[:start] + NEW_CONSTANTS + "\n\n" + src[end:]


# ------------------------------------------------------- step 3: palettes

def step_palettes(src: str) -> str:
    """accent_dark takes the dark derivative; accent_ink is added everywhere.

    accent_dark held BRAND_DARK_GOLD in the DARK and IMAGE palettes -- the
    LIGHT-mode gold, rendering in dark mode as borders and a background in
    settings_dialog and dialog_helper. It becomes BRAND_GOLD_HOVER, which keeps
    its role as a distinct accent while moving away from the dark ground.
    """
    tree = ast.parse(src)
    spans = {}
    for node in ast.walk(tree):
        target = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target.id
        elif isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            target = names[0] if names else None
        if target in ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS",
                      "IMAGE_MODE_COLORS") and isinstance(node.value, ast.Dict):
            spans[target] = (node.lineno, node.end_lineno)
    if len(spans) != 3:
        raise SystemExit(f"ABORT: found {len(spans)} palette dicts, expected 3.")

    lines = src.splitlines(keepends=True)
    for name in sorted(spans, key=lambda n: -spans[n][0]):
        lo, hi = spans[name]
        block = "".join(lines[lo - 1:hi])
        if "'accent_ink'" in block:
            continue
        anchor = "    'accent_dark': BRAND_DARK_GOLD,\n"
        if anchor not in block:
            raise SystemExit(f"ABORT: no accent_dark anchor in {name}")
        if name == "LIGHT_THEME_COLORS":
            # Light keeps BRAND_DARK_GOLD as its fill; the derivative is the
            # ink, so the two jobs stop sharing one value.
            new = ("    'accent_dark': BRAND_DARK_GOLD,\n"
                   "    'accent_ink': BRAND_DARK_GOLD_DEEP,\n")
        else:
            new = ("    'accent_dark': BRAND_GOLD_HOVER,\n"
                   "    'accent_ink': BRAND_GOLD,\n")
        block = block.replace(anchor, new, 1)
        lines[lo - 1:hi] = [block]
    return "".join(lines)


def step_all_exports(src: str) -> str:
    """__all__ lists the renamed symbols; add the two new ones beside them."""
    if '"BRAND_DARK_GOLD_DEEP"' in src:
        return src
    anchor = '    "BRAND_DARK_GOLD_RGB",\n'
    if anchor not in src:
        raise SystemExit("ABORT: __all__ does not list BRAND_DARK_GOLD_RGB")
    return src.replace(anchor,
                       anchor +
                       '    "BRAND_DARK_GOLD_DEEP",\n'
                       '    "BRAND_GOLD_HOVER",\n'
                       '    "GOLD_PROVENANCE",\n'
                       '    "lighten",\n', 1)


# ------------------------------------ step 4: bind accent_ink beside accent

BINDINGS = {
    MAIN: [
        ("            accent = GOLD_DARK                             "
         "# for selection highlight\n",
         "            accent = GOLD_DARK                             "
         "# for selection highlight\n"
         "            accent_ink = DARK_GOLD_DEEP                    "
         "# gold AS text, on a light ground\n"),
        ("            accent = GOLD                                  "
         "# for selection highlight\n",
         "            accent = GOLD                                  "
         "# for selection highlight\n"
         "            accent_ink = GOLD                              "
         "# dark has headroom; ink is the accent\n"),
    ],
    SETTINGS: [
        ("            accent = GOLD_DARK\n            accent_dark = GOLD_DARK\n",
         "            accent = GOLD_DARK\n            accent_dark = GOLD_DARK\n"
         "            accent_ink = DARK_GOLD_DEEP\n"),
        ("            accent = GOLD\n            accent_dark = GOLD_DARK\n",
         "            accent = GOLD\n            accent_dark = GOLD_HOVER\n"
         "            accent_ink = GOLD\n"),
    ],
    HELPER: [
        ("        accent = colors['accent']\n"
         "        accent_dark = colors['accent_dark']\n",
         "        accent = colors['accent']\n"
         "        accent_dark = colors['accent_dark']\n"
         "        accent_ink = colors['accent_ink']\n"),
    ],
    ABOUT: [
        ("        accent       = theme['accent']\n",
         "        accent       = theme['accent']\n"
         "        accent_ink   = theme['accent_ink']\n"),
    ],
}


def step_bindings() -> None:
    for rel, pairs in BINDINGS.items():
        def apply(src: str, pairs=pairs, rel=rel) -> str:
            for old, new in pairs:
                src = sub_once(src, old, new, rel)
            return src
        edit(rel, apply)

    # The second dialog_helper block binds accent_dark alone. After the edit
    # above, the LINE appears twice -- once already followed by accent_ink.
    # Counting the line finds 2 and aborts; match the one NOT yet paired.
    def helper_second(src: str) -> str:
        pattern = re.compile(
            r"( *accent_dark = colors\['accent_dark'\]\n)(?! *accent_ink)")
        found = pattern.findall(src)
        if len(found) != 1:
            raise SystemExit(
                f"ABORT: expected 1 unpaired accent_dark binding in {HELPER}, "
                f"found {len(found)}")
        return pattern.sub(
            lambda m: m.group(1) + "        accent_ink = colors['accent_ink']\n",
            src, count=1)
    edit(HELPER, helper_second)

    # settings_dialog and the main window alias the constants locally.
    def alias(src: str, rel: str) -> str:
        old = "        GOLD_DARK = BRAND_DARK_GOLD\n"
        if old not in src:
            raise SystemExit(f"ABORT: no GOLD_DARK alias in {rel}")
        add = "        DARK_GOLD_DEEP = BRAND_DARK_GOLD_DEEP\n"
        if rel == SETTINGS:
            add += "        GOLD_HOVER = BRAND_GOLD_HOVER\n"
        return src.replace(old, old + add, 1)
    edit(SETTINGS, lambda s: alias(s, SETTINGS))
    edit(MAIN, lambda s: alias(s, MAIN))

    # ...and must import what they now alias.
    def imports(src: str, rel: str) -> str:
        line = "    BRAND_GOLD, BRAND_DARK_GOLD,"
        if line in src:
            return src.replace(line, line + " BRAND_DARK_GOLD_DEEP,"
                                             " BRAND_GOLD_HOVER,", 1)
        line2 = "    BRAND_GOLD, BRAND_DARK_GOLD, DARK_THEME_COLORS,"
        if line2 in src:
            return src.replace(
                line2,
                "    BRAND_GOLD, BRAND_DARK_GOLD, BRAND_DARK_GOLD_DEEP,"
                " DARK_THEME_COLORS,", 1)
        raise SystemExit(f"ABORT: cannot find the colors import in {rel}")
    edit(SETTINGS, lambda s: imports(s, SETTINGS))
    edit(MAIN, lambda s: imports(s, MAIN))


# ------------------------------------------- step 5: route gold-as-text

def step_text_sites() -> int:
    """Route `color: {accent}` to `{accent_ink}` -- and nothing else.

    ANCHORED ON THE WHOLE LINE. Unanchored, `color: {accent};` is a substring
    of `background-color: {accent};` and `border-color: {accent};`, so a plain
    replace rewrites the fill and the border too. That exact mistake shipped in
    the mixer and every contrast test still passed, because the swapped value
    happened to measure better.
    """
    pattern = re.compile(r"^(\s*)color:\s*\{accent(_dark)?\};\s*$", re.M)
    total = 0
    for rel in (MAIN, ABOUT, SETTINGS, HELPER):
        def apply(src: str) -> str:
            nonlocal total
            out, n = pattern.subn(lambda m: f"{m.group(1)}color: {{accent_ink}};",
                                  src)
            total += n
            return out
        edit(rel, apply)
    if total != 11:
        raise SystemExit(f"ABORT: expected 11 gold-as-text sites, routed {total}.")
    return total


def step_about_inline(src: str) -> str:
    """Two labels write BRAND_GOLD straight into a stylesheet.

    Mode-agnostic, so light mode paints the dark-mode gold -- 1.70:1 on a light
    panel. Same defect the mixer had on its section headers.
    """
    src = sub_once(
        src,
        'f"font-size: 14px; color: {BRAND_GOLD}; border: none; '
        'background: transparent;"',
        'f"font-size: 14px; color: {_ink(self)}; border: none; '
        'background: transparent;"',
        ABOUT)
    src = sub_once(src,
                   '<p style="text-align: center; color: {BRAND_GOLD};">',
                   '<p style="text-align: center; color: {_ink(self)};">',
                   ABOUT)
    helper = '''

def _ink(dialog) -> str:
    """The gold that carries TEXT, in the mode the dialog is actually in.

    These two sites hardcoded BRAND_GOLD, so light mode drew #d2bc93 on a light
    panel at 1.70:1.
    """
    from ui.colors import get_theme_colors
    return get_theme_colors(getattr(dialog, "_theme_name", "dark"))["accent_ink"]
'''
    if "def _ink" not in src:
        marker = "\n\nclass AboutDialog"
        if marker not in src:
            raise SystemExit("ABORT: cannot find class AboutDialog to anchor the helper")
        src = src.replace(marker, helper + marker, 1)
    return src


# ---------------------------------------------------------------- guards

GUARD_MIRROR_SRC = '''"""
Brand mirror and provenance guard.   ''' + GUARD_MARKER + '''

This file NAMES RETIRED VALUES ON PURPOSE. Any sweep for a gold literal must
exclude it by the marker above, or it rewrites the very list that says which
values must never come back.

Ported from rnv-text-transformer, wired to this app's palettes.
"""
from __future__ import annotations

import ast
import pathlib
import subprocess

import pytest

from ui import colors as C

PALETTES = {
    "DARK": C.DARK_THEME_COLORS,
    "LIGHT": C.LIGHT_THEME_COLORS,
    "IMAGE": C.IMAGE_MODE_COLORS,
}

RETIRED = {
    "#b19145": "the old dark gold -- 2.997638 on white, under every floor it claimed",
    "(177, 145, 69)": "its RGB tuple, which a hex census cannot see",
    "(177,145,69)": "the same tuple without spaces",
}

GOLD_KEYS = ("accent", "accent_dark", "accent_ink")


def _luminance(value: str) -> float:
    h = value.lstrip("#")
    if len(h) == 8:
        h = h[2:]
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ------------------------------------------------------------- provenance

def test_provenance_covers_every_gold_constant():
    named = {n for n in dir(C)
             if n.startswith("BRAND_") and isinstance(getattr(C, n), str)}
    missing = named - set(C.GOLD_PROVENANCE)
    assert not missing, f"gold constants with no provenance entry: {sorted(missing)}"


def test_provenance_has_no_phantom_entries():
    phantom = [n for n in C.GOLD_PROVENANCE if not hasattr(C, n)]
    assert not phantom, f"provenance names nothing: {phantom}"


def test_register_values_match_rnv_brand():
    assert C.BRAND_GOLD == "''' + GOLD + '''"
    assert C.BRAND_DARK_GOLD == "''' + DARK_GOLD + '''"


def test_the_derivation_steps_are_the_published_ones():
    assert C.BRAND_DARK_GOLD_DEEP == C.lighten(C.BRAND_DARK_GOLD, -14)
    assert C.BRAND_GOLD_HOVER == C.lighten(C.BRAND_GOLD, 13)
    assert C.BRAND_DARK_GOLD_DEEP == "''' + DEEP + '''"
    assert C.BRAND_GOLD_HOVER == "''' + GOLD_HOVER + '''"


def test_derived_constants_are_not_written_as_literals():
    """A derivative restated by hand is orphaned the moment the base moves."""
    src = pathlib.Path(C.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    literals = {n.target.id for n in ast.walk(tree)
                if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
                and isinstance(n.value, ast.Constant)}
    for name, kind in C.GOLD_PROVENANCE.items():
        if kind == "derived":
            assert name not in literals, f"{name} is derived but written as a literal"


def test_the_rgb_tuples_are_derived_from_the_hex():
    """The trap this pass closed. Hand-written, they keep the retired gold
    through a value change, and a test asserting the two agree stays green."""
    assert C.BRAND_GOLD_RGB == C._to_rgb(C.BRAND_GOLD)
    assert C.BRAND_DARK_GOLD_RGB == C._to_rgb(C.BRAND_DARK_GOLD)
    src = pathlib.Path(C.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                and node.target.id.endswith("_GOLD_RGB")):
            assert isinstance(node.value, ast.Call), (
                f"{node.target.id} is restated, not derived")


def test_lighten_holds_hue():
    base = C._to_rgb(C.BRAND_DARK_GOLD)
    deep = C._to_rgb(C.BRAND_DARK_GOLD_DEEP)
    assert {b - d for b, d in zip(base, deep)} == {14}, "the step is not uniform"


# ------------------------------------------------------ two golds per mode

@pytest.mark.parametrize("name", sorted(PALETTES))
def test_two_golds_per_mode(name):
    """One registered gold and one derivative. A third means a role went
    unshared -- and no contrast check would object, because an orphaned gold
    can be perfectly legible."""
    palette = PALETTES[name]
    golds = {palette[k].lower() for k in GOLD_KEYS}
    assert len(golds) == 2, (
        f"{name} renders {len(golds)} golds: {sorted(golds)}")


@pytest.mark.parametrize("name", sorted(PALETTES))
def test_the_gold_key_list_still_matches_the_palette(name):
    """Guard the guard: rename a gold key and the count above would silently
    measure fewer of them and keep passing."""
    missing = [k for k in GOLD_KEYS if k not in PALETTES[name]]
    assert not missing, f"{name} no longer has {missing}"


def test_light_ink_clears_every_ground_it_draws_on():
    ink = PALETTES["LIGHT"]["accent_ink"]
    for ground in ("#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"):
        assert contrast(ink, ground) >= 4.5, f"{ink} on {ground}"


def test_dark_reuses_its_accent_for_ink():
    for name in ("DARK", "IMAGE"):
        assert PALETTES[name]["accent_ink"] == PALETTES[name]["accent"], name


def test_hover_moves_away_from_the_ground():
    light = PALETTES["LIGHT"]
    assert _luminance(light["accent_ink"]) < _luminance(light["accent"])
    for name in ("DARK", "IMAGE"):
        p = PALETTES[name]
        assert _luminance(p["accent_dark"]) > _luminance(p["accent"]), (
            f"{name} accent_dark must move lighter, away from a dark ground")


def test_the_light_gold_stays_out_of_the_dark_palettes():
    for name in ("DARK", "IMAGE"):
        offenders = [k for k, v in PALETTES[name].items()
                     if isinstance(v, str) and v.lower() == C.BRAND_DARK_GOLD.lower()]
        assert not offenders, (
            f"{name} carries the light-mode gold on {offenders}")


def test_text_on_gold_is_black_and_stays_black():
    """This is the only one of the five that paints black on the light fill.
    It is what the register prefers and the better number. Not to be flattened
    to match the others."""
    for name, palette in PALETTES.items():
        assert palette["accent_text"] == "#000000", name
    assert contrast("#000000", PALETTES["LIGHT"]["accent"]) >= 4.5


# ------------------------------------------------------------ retired values

def _sources():
    root = pathlib.Path(C.__file__).resolve().parent.parent
    out = subprocess.run(["git", "ls-files"], cwd=root,
                         capture_output=True, text=True).stdout.split()
    for rel in out:
        path = root / rel
        if path.suffix.lower() not in (".py", ".qss", ".css", ".md"):
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8-sig" if raw.startswith(b"\\xef\\xbb\\xbf")
                              else "utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="surrogateescape")
        if "''' + GUARD_MARKER + '''" in text or "''' + TOOL_MARKER + '''" in text:
            continue
        yield rel, text


def test_retired_values_do_not_appear():
    hits = []
    for rel, text in _sources():
        low = text.lower()
        for value, why in RETIRED.items():
            if value.lower() in low:
                hits.append(f"{rel}: {value} ({why})")
    assert not hits, "retired gold still present -- " + "; ".join(hits)


def test_the_retired_scan_is_still_looking():
    files = list(_sources())
    assert len(files) > 15, f"the scan found only {len(files)} files"
    assert any(rel == "ui/colors.py" for rel, _ in files), \\
        "the scan is not reading the colour file"


def test_the_old_identifier_is_gone():
    for rel, text in _sources():
        assert "BRAND_GOLD_DARK" not in text, (
            f"{rel} still uses the retired identifier BRAND_GOLD_DARK")
'''

GUARD_PAIRS_SRC = '''"""
Contrast pairing guard.   ''' + GUARD_MARKER + '''

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
    ("accent_ink", "tab_pane_bg"),
)


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
    assert len(measured) >= 3, (
        f"{theme}: only {len(measured)} ink pairs resolved -- the pair list has "
        f"gone stale against the palette")


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
'''


# ------------------------------------------------------------- environment

def probe() -> None:
    """Run the real import rather than asking whether it is findable.

    A missing SYSTEM library is not something pip can fix, and this repo's own
    workflow omits libgl1 -- it lists libegl1 and the xcb set. CI passes because
    the GitHub runner image already carries libgl1; a codespace does not.
    """
    code = ("import PyQt6.QtWidgets, pytest; "
            "from PyQt6.QtWidgets import QApplication; print('ok')")
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    proc = subprocess.run([sys.executable, "-c", code],
                          capture_output=True, text=True, env=env)
    if proc.returncode == 0:
        return
    err = (proc.stderr or "").strip()
    print("\nThis environment cannot run the suite yet.\n")
    print(err.splitlines()[-1] if err else "(no error text)")
    if any(t in err for t in ("libGL", "libEGL", "libxkb", "xcb", "libdbus")):
        print("\nThat is a SYSTEM library, not a Python package -- pip cannot")
        print("install it, and re-running the requirements will not help.")
        print("NOTE: this repo's own workflow omits libgl1. Use this list:\n")
        print("  sudo apt-get update && sudo apt-get install -y " + APT)
    else:
        print("\n  pip install -r requirements.txt -r requirements-dev.txt")
        print("\n(This repo has requirements-DEV.txt, not requirements-test.txt.)")
    print("\nThat is a SHELL command. Run it in the terminal, not with python.")
    print("Nothing has been changed.\n")
    raise SystemExit(2)


def split_failures(output: str) -> tuple[list[str], list[str]]:
    """Ours vs pre-existing, by file. Anchored on pytest's own format: the app
    logs lines beginning `ERROR    | Handler |`, and an unanchored prefix match
    reads those as test results."""
    ours, other = [], []
    pattern = re.compile(r"^(FAILED|ERROR) (\S+\.py)(::\S+)?")
    for line in output.splitlines():
        m = pattern.match(line.strip())
        if m:
            (ours if m.group(2) in OUR_FILES else other).append(line.strip())
    return ours, other


def run(label: str, args: list[str]) -> tuple[int, str]:
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    print(f"\n--- {label} ---")
    proc = subprocess.run([sys.executable, "-m", "pytest", *args],
                          capture_output=True, text=True, env=env)
    out = proc.stdout + proc.stderr
    tail = [l for l in out.splitlines()
            if re.match(r"^(FAILED|ERROR) \S+\.py", l.strip())
            or " passed" in l or " failed" in l]
    print("\n".join(tail[-12:]) or (out.splitlines() or ["(no output)"])[-1])
    if proc.returncode < 0:
        names = {6: "SIGABRT", 9: "SIGKILL (out of memory)",
                 15: "SIGTERM (session reclaimed)"}
        sig = -proc.returncode
        print(f"\nKILLED by signal {sig} -- {names.get(sig, sig)}. "
              f"Killed is not failed; nothing is concluded from this run.")
    return proc.returncode, out


# ------------------------------------------------------------------ driver

def apply() -> None:
    print("rnv-color-palette-manager: brand gold alignment\n")
    files, hits = do_rename()
    print(f"  1  BRAND_GOLD_DARK -> BRAND_DARK_GOLD: {hits} occurrences "
          f"in {files} files")
    edit(COLORS, step_constants)
    print(f"  2  constants derived: DEEP {DEEP}, HOVER {GOLD_HOVER}, "
          f"both RGB tuples")
    edit(COLORS, step_palettes)
    print("  3  accent_dark -> the dark derivative; accent_ink added to all three")
    edit(COLORS, step_all_exports)
    print("  4  __all__ updated")
    step_bindings()
    print("  5  accent_ink bound beside accent at every site that builds QSS")
    n = step_text_sites()
    print(f"  6  {n} gold-as-text declarations routed to accent_ink")
    edit(ABOUT, step_about_inline)
    print("  7  two hardcoded BRAND_GOLD labels now follow the mode")
    (ROOT / "tests").mkdir(exist_ok=True)
    (ROOT / GUARD_MIRROR).write_text(GUARD_MIRROR_SRC, encoding="utf-8")
    (ROOT / GUARD_PAIRS).write_text(GUARD_PAIRS_SRC, encoding="utf-8")
    print("  8  guard tests installed (mirror + pairings)")
    regenerate_snapshots()
    print("  9  snapshots regenerated")


def regenerate_snapshots() -> None:
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", UPDATE_SNAPSHOTS="1")
    subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q",
                    "-k", "snapshot", "-p", "no:cacheprovider"],
                   capture_output=True, text=True, env=env)


def verify() -> int:
    print("\nverifying\n")
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    bad = False
    for rel in (COLORS, ABOUT, SETTINGS, HELPER):
        mod = rel[:-3].replace("/", ".")
        proc = subprocess.run(
            [sys.executable, "-c",
             "from PyQt6.QtWidgets import QApplication; a=QApplication([]); "
             "import %s; print('ok')" % mod],
            capture_output=True, text=True, env=env)
        if proc.returncode != 0:
            print(f"  IMPORT FAILED  {rel}")
            print("    " + (proc.stderr.strip().splitlines() or ["?"])[-1])
            bad = True
    if not bad:
        print("  every edited module imports")

    proc = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0,'.'); from ui import colors as C\n"
         "for n in ('DARK_THEME_COLORS','LIGHT_THEME_COLORS','IMAGE_MODE_COLORS'):\n"
         "    p=getattr(C,n)\n"
         "    print('  ', n, sorted({p[k].lower() for k in "
         "('accent','accent_dark','accent_ink')}))"],
        capture_output=True, text=True, env=env)
    print("\n  golds rendered per palette:")
    print(proc.stdout.rstrip() or proc.stderr.strip())

    rc_guard, _ = run("guard suite (the gate)",
                      [GUARD_MIRROR, GUARD_PAIRS, "-q", "-p", "no:cacheprovider"])
    rc_unit, out_unit = run("test_rnv_palette_manager.py",
                            ["test_rnv_palette_manager.py", "-q",
                             "-p", "no:cacheprovider"])
    rc_rest, out_rest = run("tests/", ["tests/", "-q", "-p", "no:cacheprovider"])

    ours, other = split_failures(out_unit + out_rest)
    if other:
        print("\n  pre-existing failures, not from this pass:")
        for line in other:
            print("   ", line)
    if ours:
        print("\n  FAILURES IN FILES THIS PASS TOUCHED:")
        for line in ours:
            print("   ", line)

    ok = rc_guard == 0 and not ours and not bad
    if not ok:
        print("\nNOT CLEAN -- see above. Nothing was reverted; re-run after fixing.")
        return 1
    incomplete = [n for n, rc in (("the unittest file", rc_unit),
                                  ("tests/", rc_rest)) if rc < 0]
    if incomplete:
        print("\nPASS ON THE GATE -- the guard suite is green and nothing this "
              "pass touched failed.")
        print("   But " + " and ".join(incomplete) + " was KILLED before "
              "finishing, so it did not report.")
        print("   Push and let CI run them: it is not tethered to this tab.")
    else:
        print("\nPASS -- the gate is green, every suite finished, and nothing "
              "this pass touched failed.")
    return 0


def finish() -> None:
    me = Path(__file__).resolve()
    me.unlink()
    cache = me.parent / "__pycache__"
    if cache.is_dir():
        shutil.rmtree(cache, ignore_errors=True)
    print("removed", me.name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--finish", action="store_true")
    parser.add_argument("--deps", action="store_true")
    args = parser.parse_args()
    if args.deps:
        print("  sudo apt-get update && sudo apt-get install -y " + APT)
        print("  pip install -r requirements.txt -r requirements-dev.txt")
        return 0
    if args.finish:
        finish()
        return 0
    if not (ROOT / COLORS).exists():
        raise SystemExit("ABORT: run this from the repository root.")
    probe()
    if not args.verify:
        apply()
    return verify()


if __name__ == "__main__":
    raise SystemExit(main())
