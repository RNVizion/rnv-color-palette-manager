#!/usr/bin/env python3
"""
RNV-NAMING-TOOL-DO-NOT-SWEEP

Constants name colours. Roles go back to being roles, the dead ones go, and
the ink question gets one answer.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHY

Chris, reading the colour tree on 2026-09-02:

    "_DRAG_HIGHLIGHT_GOLD reads as a constant but it should read as a key --
     the constant should denote the colour, as that is what will change to
     affect the rest of the app elements, not the keys."

That is the naming half of rule 1: a constant names a COLOUR, a key names a
ROLE. This application held eleven names that answered both questions at once
and two that answered neither, because nothing used them.

WHAT THE ROLE NAMES ACTUALLY WERE

    ACCENT_PRESSED_TEXT_DARK   ->  TRUE_BLACK
    ACCENT_PRESSED_TEXT_LIGHT  ->  WHITE
    TEXTEDIT_BG_DARK           ->  TRUE_BLACK
    TEXTEDIT_BG_LIGHT          ->  WHITE
    SELECTION_OVERLAY_TEXT     ->  WHITE
    IMAGE_PREVIEW_BORDER       ->  GREY_66
    IMAGE_PREVIEW_BG           ->  GREY_F0
    DARK_GOLD_DEEP             ->  BRAND_DARK_GOLD_DEEP
    SLOT_SELECTED_COLOR        ->  BRAND_DARK_GOLD_RGB

Every one of these was a second name for a value the palette module already
had. The survey proposed turning the _DARK / _LIGHT pairs into palette keys;
reading the call sites showed that was wrong. They are not palette entries,
they are inline branches -- `X if is_light else Y` -- and the two arms are
just black and white. So the pairs collapse to the register constants at the
use site and the branch keeps saying which mode it is in, which is the part
that was carrying the meaning all along.

TWO THAT WERE SIMPLY DEAD

    CHECKBOX_ACCENT "#0078d4"   Windows blue. Defined, exported, and used by
                                nothing. Chris read it and said it should be
                                a brand gold by mode -- and it already is:
                                the checked checkbox is painted at
                                ui/settings_dialog.py with
                                `background-color: {accent};`, the
                                mode-selected gold. The behaviour he expected
                                is the behaviour that ships. So this is a
                                delete, not a repoint, and no pixel moves.

    SVG_EXPORT_TEXT_DARK/_LIGHT the two arms of the export's own brightness
                                branch. Replaced by the rule, below.

ONE RULE FOR THE INK

core/palette_formats.py chose an exported swatch's label colour with
sum(color) / 3 < 128. That is not a contrast measurement, and it is the fifth
copy of the question found in the fleet, on the third different rule. Ruled by
Chris after seeing them rendered side by side: unify on WCAG relative
luminance. rnv-color-picker and rnv-icon-builder carry the identical block.

WHAT MOVES

The label on an exported SVG swatch, and only where the mean was wrong: mid
greys and saturated colour. Nothing in any palette. Nothing on screen.

ALSO HERE

core/palette_formats.py is not valid UTF-8 -- it carries cp1252 em-dashes.
CPython tolerates them because they sit in comments, so the app has always
run; tooling does not. An audit script of mine read it with plain UTF-8,
caught the decode error, skipped the file, and reported four live constants
as dead. The picker's copy of this same file had the same bytes. Normalised
here, with a guard that every source file decodes.
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
DESCRIPTION = "constants name colours, the dead go, one ink rule"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = "RNV-INK-RULE"
GUARD = "tests/test_constant_names.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('run_tests.py (unittest + pytest)', [sys.executable, "run_tests.py"]),
]

RENAMES = [('ACCENT_PRESSED_TEXT_DARK', 'TRUE_BLACK'), ('ACCENT_PRESSED_TEXT_LIGHT', 'WHITE'), ('TEXTEDIT_BG_DARK', 'TRUE_BLACK'), ('TEXTEDIT_BG_LIGHT', 'WHITE'), ('SELECTION_OVERLAY_TEXT', 'WHITE'), ('IMAGE_PREVIEW_BORDER', 'GREY_66'), ('IMAGE_PREVIEW_BG', 'GREY_F0'), ('DARK_GOLD_DEEP', 'BRAND_DARK_GOLD_DEEP'), ('SLOT_SELECTED_COLOR', 'BRAND_DARK_GOLD_RGB')]
SWEEP = ('ui/colors.py', 'RNV_Color_Palette_Manager.py', 'ui/about_dialog.py', 'ui/settings_dialog.py', 'ui/batch_export_dialog.py', 'ui/image_upload_dialog.py', 'utils/dialog_helper.py', 'test_rnv_palette_manager.py')
DROP_DEFS = [('ui/colors.py', 'ACCENT_PRESSED_TEXT_DARK'), ('ui/colors.py', 'ACCENT_PRESSED_TEXT_LIGHT'), ('ui/colors.py', 'TEXTEDIT_BG_DARK'), ('ui/colors.py', 'TEXTEDIT_BG_LIGHT'), ('ui/colors.py', 'SELECTION_OVERLAY_TEXT'), ('ui/colors.py', 'IMAGE_PREVIEW_BORDER'), ('ui/colors.py', 'IMAGE_PREVIEW_BG'), ('ui/colors.py', 'SLOT_SELECTED_COLOR'), ('ui/colors.py', 'CHECKBOX_ACCENT'), ('ui/colors.py', 'SVG_EXPORT_TEXT_DARK'), ('ui/colors.py', 'SVG_EXPORT_TEXT_LIGHT')]
RETIRED = ('ACCENT_PRESSED_TEXT_DARK', 'ACCENT_PRESSED_TEXT_LIGHT', 'TEXTEDIT_BG_DARK', 'TEXTEDIT_BG_LIGHT', 'SELECTION_OVERLAY_TEXT', 'IMAGE_PREVIEW_BORDER', 'IMAGE_PREVIEW_BG', 'DARK_GOLD_DEEP', 'SLOT_SELECTED_COLOR', 'CHECKBOX_ACCENT', 'SVG_EXPORT_TEXT_DARK', 'SVG_EXPORT_TEXT_LIGHT')

BAD_BYTES_FILE = "core/palette_formats.py"
ANCHOR = 'SELECTION_OVERLAY_COLOR: Final[str] = "rgba(0,120,215,200)"\n'


def _token_sub(text: str) -> tuple[str, int]:
    """One pass, longest name first, whole tokens only.

    Sequential passes break the moment one new name contains an old one, and
    word boundaries make the quoted forms in __all__ rename themselves.
    """
    pairs = sorted(RENAMES, key=lambda p: -len(p[0]))
    lookup = dict(pairs)
    pattern = re.compile(r"\b(%s)\b" % "|".join(re.escape(o) for o, _ in pairs))
    n = 0

    def swap(m):
        nonlocal n
        n += 1
        return lookup[m.group(1)]

    return pattern.sub(swap, text), n


def _dedupe_imports(text: str) -> str:
    """Two role names that were the same colour become the same name twice.

    utils/dialog_helper.py imported ACCENT_PRESSED_TEXT_DARK and
    TEXTEDIT_BG_DARK together; both are TRUE_BLACK. Python accepts the
    duplicate, but it reads as a mistake, so collapse it.
    """
    def fix(m):
        head, body, tail = m.group(1), m.group(2), m.group(3)
        seen, keep = set(), []
        for line in body.splitlines(True):
            name = line.strip().rstrip(",").strip()
            if name and name not in seen:
                seen.add(name)
                keep.append(line)
            elif not name:
                keep.append(line)
        return head + "".join(keep) + tail

    return re.sub(r"(from ui\.colors import \(\n)((?:[ \t]+[^\n]*\n)+?)([ \t]*\)\n)",
                  fix, text)


def _drop_definition(text: str, name: str) -> str:
    """Remove a module-level assignment, its docstring, and its __all__ entry.

    Anchored on the assignment line and everything up to the next blank line
    that is followed by something at column zero -- which is how every
    constant in this file is written."""
    pat = re.compile(
        r"^%s\s*:[^\n]*\n(?:\"\"\"(?:[^\"]|\"(?!\"\"))*\"\"\"\n)?(?:\n)?"
        % re.escape(name), re.M)
    text, n = pat.subn("", text)
    if n != 1:
        raise SystemExit(f"expected 1 definition of {name}, removed {n}")
    text, n = re.subn(r'^[ \t]*"%s",\n' % re.escape(name), "", text, flags=re.M)
    if n > 1:
        raise SystemExit(f"{name} appears {n} times in __all__")
    return text


def edits(tree) -> None:
    # FIRST, before anything reads it. The harness reads UTF-8 and this file
    # is not UTF-8, so any earlier tree.read() of it raises rather than edits.
    raw = (Path(tree.root) / BAD_BYTES_FILE).read_bytes()
    hits = raw.count(b"\x97")
    if hits < 1:
        raise SystemExit(f"expected cp1252 dashes in {BAD_BYTES_FILE}, found none")
    tree.write(BAD_BYTES_FILE, raw.decode("cp1252"))
    print(f"  {BAD_BYTES_FILE}: {hits} cp1252 byte(s) normalised to UTF-8")

    tree.sub(BAD_BYTES_FILE, OLD_PF_IMP, NEW_PF_IMP, 1)
    tree.sub(BAD_BYTES_FILE, OLD_PF_USE, NEW_PF_USE, 1)
    print("  the export's brightness branch now asks the rule")

    # The definitions go before the sweep, so the sweep does not rename a
    # line that is about to be deleted and then fail to find it.
    src = tree.read(SENTINEL_FILE)
    for _, name in DROP_DEFS:
        src = _drop_definition(src, name)
    tree.write(SENTINEL_FILE, src)
    print(f"  {len(DROP_DEFS)} definition(s) removed from {SENTINEL_FILE}")

    # The two local aliases go BEFORE the sweep. Renaming them instead would
    # have produced `BRAND_DARK_GOLD_DEEP = BRAND_DARK_GOLD_DEEP` inside a
    # method, which Python reads as a local assignment shadowing the global
    # -- an UnboundLocalError on the same line. Caught by the suite.
    for rel in ("RNV_Color_Palette_Manager.py", "ui/settings_dialog.py"):
        tree.sub(rel, "        DARK_GOLD_DEEP = BRAND_DARK_GOLD_DEEP\n", "", 1)
    print("  2 local alias(es) of a register name deleted")

    tree.sub(SENTINEL_FILE, ANCHOR, ANCHOR + "\n" + NEW_CONSTS, 1)
    tree.sub(SENTINEL_FILE, '    "BRAND_DARK_GOLD_RGB",\n',
             '    "BRAND_DARK_GOLD_RGB",\n' + NEW_ALL, 1)

    _regenerate_snapshot(tree)

    total = 0
    for rel in SWEEP:
        text = tree.read(rel)
        new, n = _token_sub(text)
        if n:
            tree.write(rel, _dedupe_imports(new))
        total += n
        print(f"  {rel}: {n} occurrence(s) renamed")
    print(f"  {total} occurrence(s) across {len(SWEEP)} file(s)")


SNAPSHOT = "snapshots/canonical.svg"


def _luminance(hexv: str) -> float:
    """The rule, restated here so the snapshot is recomputed rather than
    accepted. Running the exporter to regenerate would prove only that the
    exporter agrees with itself."""
    h = hexv.lstrip("#")
    out = 0.0
    for i, w in ((0, 0.2126), (2, 0.7152), (4, 0.0722)):
        c = int(h[i:i + 2], 16) / 255.0
        out += w * (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def _regenerate_snapshot(tree) -> None:
    """The exported SVG's swatch labels move where the mean was wrong.

    snapshots/canonical.svg pins the export byte for byte, so it has to be
    re-derived, not blessed. Each label's colour is recomputed from the
    swatch it sits on, and the count of labels that actually change is
    asserted -- a regeneration that moved every label, or none, would be a
    bug wearing a passing test.
    """
    text = tree.read(SNAPSHOT)
    pattern = re.compile(
        r'(?P<head><rect x="\d+"[^>]*fill="(?P<ground>#[0-9a-fA-F]{6})"[^>]*/>\n'
        r'\s*<text[^>]*fill=")(?P<ink>#[0-9a-fA-F]{6})(?P<tail>">)')
    moved = []

    def fix(m):
        ground = m.group("ground")
        # black wins above the crossover; the ratios are equal at 0.1791287
        want = "#000000" if _luminance(ground) > 0.1791287 else "#ffffff"
        if want != m.group("ink").lower():
            moved.append(f"{ground} {m.group('ink')} -> {want}")
        return m.group("head") + want + m.group("tail")

    new, n = pattern.subn(fix, text)
    if n != 5:
        raise SystemExit(f"expected 5 swatch labels in {SNAPSHOT}, found {n}")
    if len(moved) != 2:
        raise SystemExit(f"expected exactly 2 labels to move (pure red and "
                         f"pure green), got {len(moved)}: {moved}")
    tree.write(SNAPSHOT, new)
    print(f"  {SNAPSHOT}: {len(moved)} label(s) re-derived -- " + "; ".join(moved))


def checks(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if SENTINEL not in src:
        raise SystemExit("the ruling note did not land")

    root = Path(tree.root)
    strays = []
    for path in sorted(root.rglob("*.py")):
        if any(p in {".git", "build", "dist", ".venv", "__pycache__"}
               for p in path.parts):
            continue
        if path.name in ("up.py", "up1.py", "up2.py"):
            continue
        rel = str(path.relative_to(root))
        text = tree.files.get(rel)
        if text is None:
            text = path.read_bytes().decode("utf-8-sig", errors="replace")
        if "RNV-NAMING-TOOL-DO-NOT-SWEEP" in text or "RNV-NAME-GUARD" in text:
            continue
        for old in RETIRED:
            if re.search(r"\b%s\b" % re.escape(old), text):
                strays.append(f"{rel}: {old}")
    if strays:
        raise SystemExit("retired names survived:\n  " + "\n  ".join(strays))

    for name in ("GREY_66", "GREY_F0", "contrast_ink", "prefers_dark_ink",
                 "relative_luminance", "contrast_ratio", "better_on"):
        if f'"{name}",' not in src:
            raise SystemExit(f"{name} is not exported from {SENTINEL_FILE}")

    tree.read(BAD_BYTES_FILE).encode("utf-8")
    print(f"  guards: {len(RETIRED)} names retired, ink rule stated once, "
          f"{BAD_BYTES_FILE} is UTF-8")


NEW_CONSTS = '''# ── Neutral greys, named for what they are ──
# RNV-INK-RULE (2026-09-02). These were IMAGE_PREVIEW_BORDER and
# IMAGE_PREVIEW_BG -- role names on values that four applications in the
# fleet paint with. GREY_F0 in particular is used by the picker, the icon
# builder and this app, and until now had a name in none of them.
GREY_66: Final[str] = "#666666"
GREY_F0: Final[str] = "#f0f0f0"


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

'''

NEW_ALL = '''    "GREY_66",
    "GREY_F0",
    "relative_luminance",
    "contrast_ratio",
    "better_on",
    "contrast_ink",
    "prefers_dark_ink",
'''

OLD_PF_IMP = 'from ui.colors import SVG_EXPORT_BG, SVG_EXPORT_STROKE, SVG_EXPORT_TEXT_LIGHT, SVG_EXPORT_TEXT_DARK\n'
NEW_PF_IMP = 'from ui.colors import SVG_EXPORT_BG, SVG_EXPORT_STROKE, contrast_ink\n'
OLD_PF_USE = '                brightness = sum(color) / 3\n                text_color = SVG_EXPORT_TEXT_LIGHT if brightness < 128 else SVG_EXPORT_TEXT_DARK\n'
NEW_PF_USE = '                # RNV-INK-RULE: was sum(color) / 3 < 128, which is not a\n                # contrast measurement and put white on pure green.\n                text_color = contrast_ink(color)\n'

GUARD_SOURCE = r'''"""A constant names a colour, not a role. RNV-NAME-GUARD

Ruled by Chris on 2026-09-02. Eleven names in this application answered both
questions at once -- what colour is this, and what is it painting -- and two
answered neither, because nothing used them.

The pairs that looked like palette keys were not: they were inline
`X if is_light else Y` branches whose two arms were black and white. The
branch was carrying the mode all along; only the arms needed naming honestly.
"""
from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path

from ui import colors

ROOT = Path(__file__).resolve().parent.parent
RETIRED = ('ACCENT_PRESSED_TEXT_DARK', 'ACCENT_PRESSED_TEXT_LIGHT', 'TEXTEDIT_BG_DARK', 'TEXTEDIT_BG_LIGHT', 'SELECTION_OVERLAY_TEXT', 'IMAGE_PREVIEW_BORDER', 'IMAGE_PREVIEW_BG', 'DARK_GOLD_DEEP', 'SLOT_SELECTED_COLOR', 'CHECKBOX_ACCENT', 'SVG_EXPORT_TEXT_DARK', 'SVG_EXPORT_TEXT_LIGHT')
SKIP = {".git", "build", "dist", ".venv", "__pycache__"}


def _code_only(text: str) -> str:
    """The file with every comment and string literal removed.

    A guard that sweeps for the thing it forbids must tell a use from a
    mention. Doing that by excluding files stops working the moment a third
    file has a legitimate reason to say the word; tokenising needs no list.
    """
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            out.append(tok.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text
    return " ".join(out)


def _sources():
    for path in sorted(ROOT.rglob("*.py")):
        if any(p in SKIP for p in path.parts):
            continue
        text = path.read_bytes().decode("utf-8-sig", errors="replace")
        if "RNV-NAME-GUARD" in text or "RNV-NAMING-TOOL-DO-NOT-SWEEP" in text:
            continue
        yield path, text


def test_the_retired_names_are_gone():
    strays = []
    for path, text in _sources():
        for old in RETIRED:
            if re.search(r"\b%s\b" % re.escape(old), text):
                strays.append(f"{path.relative_to(ROOT)}: {old}")
    assert not strays, "retired names are still in use:\n  " + "\n  ".join(strays)


def test_the_values_they_named_are_still_here():
    """A rename that loses a value is not a rename. These are the colours the
    eleven role names were standing in front of."""
    assert colors.TRUE_BLACK == "#000000"
    assert colors.WHITE == "#ffffff"
    assert colors.GREY_66 == "#666666"
    assert colors.GREY_F0 == "#f0f0f0"
    assert colors.BRAND_DARK_GOLD_DEEP == "#7e6529"


def test_the_checkbox_still_uses_the_mode_selected_gold():
    """CHECKBOX_ACCENT was Windows blue, exported, and used by nothing. The
    checked checkbox has always been painted with the accent. Deleting the
    dead constant must not have disturbed the live one."""
    src = (ROOT / "ui" / "settings_dialog.py").read_text(encoding="utf-8-sig")
    checked = re.search(
        r"QCheckBox::indicator:checked \{\{(?P<body>.*?)\}\}", src, re.S)
    assert checked, "the checked-checkbox rule is gone from the stylesheet"
    body = checked.group("body")
    assert "background-color: {accent}" in body, (
        "the checked checkbox no longer fills with the mode-selected accent")
    assert "border-color: {accent_dark}" in body
    for palette in (colors.DARK_THEME_COLORS, colors.LIGHT_THEME_COLORS):
        assert palette["accent"] in (colors.BRAND_GOLD, colors.BRAND_DARK_GOLD)


def test_no_windows_blue_anywhere():
    """The value it held is on no ladder, no grid and no brand."""
    strays = []
    for path, text in _sources():
        if re.search(r"""['"]#0078d4['"]""", text, re.I):
            strays.append(str(path.relative_to(ROOT)))
    assert not strays, f"#0078d4 is back in: {strays}"


def test_the_ink_rule_is_a_real_contrast_measurement():
    assert colors.contrast_ink("#ffffff") == colors.TRUE_BLACK
    assert colors.contrast_ink("#000000") == colors.WHITE
    assert round(colors.contrast_ratio("#ffffff", "#000000"), 2) == 21.0


def test_the_exported_svg_labels_follow_the_rule():
    """snapshots/canonical.svg pins the export byte for byte. Pure red and
    pure green used to carry white labels at 4.00:1 and 1.37:1, because the
    mean of the channels called them dark. They carry black now."""
    svg = (ROOT / "snapshots" / "canonical.svg").read_text(encoding="utf-8")
    pairs = re.findall(
        r'<rect x="\d+"[^>]*fill="(#[0-9a-fA-F]{6})"[^>]*/>\s*'
        r'<text[^>]*fill="(#[0-9a-fA-F]{6})"', svg)
    assert len(pairs) == 5, f"expected 5 swatches in the snapshot, found {len(pairs)}"
    for ground, ink in pairs:
        assert ink.lower() == colors.contrast_ink(ground), (
            f"the snapshot writes {ink} on {ground}; the rule says "
            f"{colors.contrast_ink(ground)}")


def test_the_ink_rule_gets_saturated_colour_right():
    """The case sum(color) / 3 got wrong. Pure green is a LIGHT ground."""
    assert colors.contrast_ink((0, 255, 0)) == colors.TRUE_BLACK
    assert colors.contrast_ratio((0, 255, 0), colors.TRUE_BLACK) > 15
    assert sum((0, 255, 0)) / 3 < 128       # what the old rule saw


def test_no_call_site_measures_brightness_by_hand():
    """Reads code with comments and strings removed, so the note above the
    replaced call site -- which names the arithmetic it retired -- does not
    fail the sweep that forbids it."""
    mean = re.compile(r"sum \( colou?r \) / 3|\( r \+ g \+ b \) / 3")
    luma = re.compile(r"\* 299\b|\* 587\b|\* 114\b")
    strays = []
    for path, text in _sources():
        code = _code_only(text)
        if mean.search(code) or luma.search(code):
            strays.append(str(path.relative_to(ROOT)))
    assert not strays, f"hand-rolled brightness rules are back in: {strays}"


def test_every_source_file_is_utf8():
    """core/palette_formats.py carried cp1252 em-dashes. CPython let it run
    because they sat in comments; an audit script read it with plain UTF-8,
    swallowed the decode error, skipped the file, and reported four live
    constants as dead. A sweep that cannot read a file is worse than one that
    fails."""
    bad = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(p in SKIP for p in path.parts):
            continue
        try:
            path.read_bytes().decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            bad.append(f"{path.relative_to(ROOT)}: {exc}")
    assert not bad, "not valid UTF-8:\n  " + "\n  ".join(bad)
'''


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
