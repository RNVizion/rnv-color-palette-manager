#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Retire #d0d0d0 in rnv-color-palette-manager, adopt APP["panel-hover"] and
APP["hover-light"], and wire the three translucent values the last pass could
not see.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

THIS PASS MOVES TWO PIXELS, AND ONLY TWO

Unlike the other four scripts in this programme, this one is not purely a
respelling. Two light entries change value:

    LIGHT dialog_btn_hover_bg   #d0d0d0 -> #eeeeee
    LIGHT tab_hover_bg          #d0d0d0 -> #eeeeee

That is the retirement rnv-brand ruled. The About dialog draws the hover label
in BRAND_DARK_GOLD_DEEP #7e6529 on this plate, and on #d0d0d0 that measures
3.6013:1 against a 4.5 floor -- a real, visible accessibility defect that has
existed as long as the plate has. tests/test_app_mirror.py has carried a STRICT
xfail on it since 2026-08-28 saying it was awaiting exactly this ruling. Strict,
so that fixing it fails the test and forces the note to be rewritten instead of
the exemption quietly outliving the defect. This script removes the marker and
rewrites the note.

checks() permits those two moves BY NAME and refuses any other. Every other
entry in every palette is resolved before and after and must be identical.

    #d0d0d0   3.6013   fails       <- what shipped
    #e8e8e8   4.5334   clears by 0.0334
    #eeeeee   4.7875   clears by 0.2875   <- the registered plate

WHAT DOES NOT MOVE: EVERYTHING ELSE

    dark   dialog_btn_hover_bg, tab_hover_bg   -> APP_PANEL_HOVER
    image  dialog_btn_hover_bg, tab_hover_bg   -> APP_PANEL_HOVER
    image  window_bg, scroll_bg                -> APP_WINDOW_OVERLAY
    image  panel_bg                            -> APP_PANEL_OVERLAY

A DEFECT IN THE LAST PASS, FIXED HERE

The 2026-08-29 wiring pass claimed no registered value was left spelled as a
literal in a dark palette. True of six-digit spellings only. Qt writes a
translucent colour as #AARRGGBB and the guard compared whole strings, so
#ED000000 never matched #000000 and three registered values sat in
IMAGE_MODE_COLORS with the test reporting clean. Same shape as the three
failures already recorded in this programme: a check whose reach was narrower
than the change's extent, passing because it covered what it could rather than
what mattered.

ONE LIGHT VALUE IS DELIBERATELY LEFT ALONE

LIGHT scroll_bg is #eeeeee, which is now APP["hover-light"]. It is NOT wired.
A scrollbar groove is a surface, not an interaction plate, and the light
SURFACE ladder is precisely what the register has deferred. Wiring it would
claim a role it does not play on the strength of a shared hex -- the same
mistake in the opposite direction from the one this programme keeps catching.
A test asserts it is still a literal, so ruling the light ladder later means
deleting that test on purpose.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-color-palette-manager"
DESCRIPTION = "retire #d0d0d0, adopt the plate, the rung and the overlays"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = "APP_HOVER_LIGHT,"
MIRROR = "tests/test_app_mirror.py"
WIRING = "tests/test_register_wiring.py"
GUARD = "tests/test_ladder_and_plate.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

#: What CI runs, copied from .github/workflows/tests-linux.yml. run_tests.py
#: drives both the unittest and pytest halves.
SUITES = [
    ('run_tests.py (unittest + pytest)', [sys.executable, "run_tests.py"]),
]

#: palette -> {value: constant}. An ALLOWLIST, not a sweep.
SUBSTITUTE = {
    "DARK_THEME_COLORS": {"#3a3a3a": "APP_PANEL_HOVER"},
    "IMAGE_MODE_COLORS": {"#3a3a3a": "APP_PANEL_HOVER",
                          "#ed000000": "APP_WINDOW_OVERLAY",
                          "#ed1a1a1a": "APP_PANEL_OVERLAY"},
    "LIGHT_THEME_COLORS": {"#d0d0d0": "APP_HOVER_LIGHT"},
}
EXPECTED_SUBS = 9

#: The ONLY entries permitted to change value, named individually with the
#: value they leave and the value they arrive at. Anything else that moves
#: aborts the run.
EXPECTED_MOVES = {
    ("LIGHT_THEME_COLORS", "dialog_btn_hover_bg"): ("#d0d0d0", "#eeeeee"),
    ("LIGHT_THEME_COLORS", "tab_hover_bg"): ("#d0d0d0", "#eeeeee"),
}

ALL_DICTS = ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS")

CONSTANTS = '\nAPP_PANEL_HOVER: Final[str] = "#3a3a3a"\n"""engine/brand.py APP["panel-hover"]. The n=+2 rung of the dark surface\nladder, and the dark interaction plate.\n\nREGISTERED 2026-08-29 in rnv-brand rev 22, app-owned here until then.\n\n    BRAND_BLACK + n * 0x10,  n in -1..+2\n    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover\n\nThe register had called the ladder "two-thirds specified" because APP_BORDER\n#333333 is not #3a3a3a and so looked like a missing rung. It is not a rung at\nall: #333333 is grey(3) on the INK grid, which governs inks and EDGES, and a\nborder is an edge. The ladder was complete when the question was first asked.\n"""\n\nAPP_HOVER_LIGHT: Final[str] = "#eeeeee"\n"""engine/brand.py APP["hover-light"]. grey(14). The light interaction plate.\n\nTHIS ONE MOVES A PIXEL, and it is the only thing in this pass that does.\n\nThe light dialog-button and tab hover plates were #d0d0d0. rnv-brand RETIRED\nthat value as a light interaction ground: the About dialog draws the hover\nlabel in BRAND_DARK_GOLD_DEEP #7e6529, which measures 3.6013:1 on #d0d0d0\nagainst a 4.5 floor. The defect was pre-existing and had been marked with a\nstrict xfail since the 2026-08-28 ink pass, awaiting exactly this ruling.\n\n    #d0d0d0   3.6013   fails      <- what shipped\n    #e0e0e0   4.2078   fails\n    #e8e8e8   4.5334   clears by 0.0334\n    #eeeeee   4.7875   clears by 0.2875   <- this value\n\nRegistered 2026-08-29 as #e8e8e8 and moved to #eeeeee on 2026-08-30 in rev 23.\n#e8e8e8 is the ground BRAND_DARK_GOLD_DEEP is calibrated against -- rev 24\nregistered it as GOLD_TEXT_GROUND_FLOOR for that reason -- so putting the hover\nplate on it would have pinned every hover to the one value the gold cannot\nafford to lose. A boundary is not a plate.\n"""\n\nIMAGE_OVERLAY_ALPHA: Final[str] = "ED"\n"""The alpha byte image mode composites its chrome at -- 0xED, about 93%.\n\nWHY THE OVERLAYS BELOW ARE WRITTEN OUT RATHER THAN COMPOSED. Qt wants the\neight-digit #AARRGGBB form, and building it from the six-digit constant would\nmake the palette entries resolve to an expression rather than a value, which\nthis app\'s own before/after comparison cannot check. The relationship is\nasserted in tests/test_ladder_and_plate.py instead: each overlay\'s last six\ndigits must BE the register value it claims, and its alpha byte must be this\none. If the register moves a base, those tests fail and these move with it.\n\nTHEY WERE INVISIBLE BEFORE. The 2026-08-29 wiring pass claimed no registered\nvalue was left spelled as a literal in a dark palette. That was true of\nsix-digit spellings only: its sweep compared whole strings, so #ED000000 never\nmatched #000000, and three of these sat in IMAGE_MODE_COLORS -- which is a DARK\ndict here -- while the test reported clean.\n"""\n\nAPP_WINDOW_OVERLAY: Final[str] = "#ED000000"\n"""TRUE_BLACK, and APP["window"], at IMAGE_OVERLAY_ALPHA."""\n\nAPP_PANEL_OVERLAY: Final[str] = "#ED1A1A1A"\n"""BRAND_BLACK, and APP["panel"], at IMAGE_OVERLAY_ALPHA."""\n'
PROVENANCE = '    "APP_PANEL_HOVER": "register",\n    "APP_HOVER_LIGHT": "register",\n    "APP_WINDOW_OVERLAY": "register-overlay",\n    "APP_PANEL_OVERLAY": "register-overlay",\n'
PINNED = "    'APP_PANEL_HOVER': '#3a3a3a',\n    'APP_HOVER_LIGHT': '#eeeeee',\n"
OLD_HOVER_TABLE = "DIALOG_BTN_HOVER = {'DARK': '#3a3a3a', 'LIGHT': '#d0d0d0', 'IMAGE': '#3a3a3a'}"
NEW_HOVER_TABLE = "DIALOG_BTN_HOVER = {'DARK': '#3a3a3a', 'LIGHT': '#eeeeee', 'IMAGE': '#3a3a3a'}"
OLD_XFAIL = '@pytest.mark.xfail(\n    strict=True,\n    reason=\'KNOWN DEFECT, pre-existing and out of scope for the 2026-08-28 ink \'\n           \'pass. Light gold text on the dialog button hover plate is 3.60:1, \'\n           \'under the 4.5 floor. It surfaced only because naming the plate \'\n           \'brought it into an audit for the first time -- it has been wrong \'\n           \'as long as the plate has existed. Awaiting a ruling: either the \'\n           \'plate moves above #e8e8e8, or the hover label stops being gold. \'\n           \'Marked strict so fixing it FAILS this test and forces the note to \'\n           \'be updated rather than quietly outliving the defect.\')\ndef test_gold_text_clears_the_dialog_button_hover_plate():\n    """The pairing is real: ui/about_dialog.py sets the hover ground from\n    dialog_btn_hover_bg and the hover label from accent_ink, in the same rule.\n\n        DARK   #d2bc93 on #3a3a3a   6.15  passes\n        IMAGE  #d2bc93 on #3a3a3a   6.15  passes\n        LIGHT  #7e6529 on #d0d0d0   3.60  FAILS\n\n    rnv-brand publishes the reason: below #e8e8e8, gold does not carry text.\n    #d0d0d0 is well below it. That is a ruling, not a gap, so the plate is\n    what is wrong here rather than the floor.\n    """'
NEW_XFAIL = 'def test_gold_text_clears_the_dialog_button_hover_plate():\n    """The pairing is real: ui/about_dialog.py sets the hover ground from\n    dialog_btn_hover_bg and the hover label from accent_ink, in the same rule.\n\n        DARK   #d2bc93 on #3a3a3a   6.1503  passes\n        IMAGE  #d2bc93 on #3a3a3a   6.1503  passes\n        LIGHT  #7e6529 on #eeeeee   4.7875  passes\n\n    FIXED 2026-08-30, AND THE XFAIL IS GONE. This carried a strict xfail from\n    the 2026-08-28 ink pass: the light plate was #d0d0d0 and the gold label\n    measured 3.6013:1 against a 4.5 floor. The note said it was awaiting a\n    ruling -- either the plate moves above #e8e8e8 or the label stops being\n    gold -- and marked the xfail strict so that fixing it would FAIL and force\n    this text to be rewritten rather than let the exemption outlive the defect.\n\n    That is what happened. rnv-brand retired #d0d0d0 as a light interaction\n    ground and registered APP["hover-light"], first as #e8e8e8 and then as\n    #eeeeee. The plate moved; the label did not.\n\n    WHY NOT #e8e8e8, WHICH ALSO CLEARS. It clears by 0.0334, and it is the\n    ground BRAND_DARK_GOLD_DEEP is derived against -- rev 24 registered it as\n    GOLD_TEXT_GROUND_FLOOR. A plate on that value would fail the moment the\n    gold moved by one step. #eeeeee clears by 0.2875 and is grey(14) exactly.\n    """'
OLD_LIGHT_TEST = 'def test_the_light_palettes_were_left_alone():\n    """This pass is the DARK half, on the register\'s stated order. The light\n    ladder is unruled -- nine surfaces inside three grid steps, and which of\n    them are real distinctions is a judgement the register has not made. If a\n    later pass wires light, this test is the thing that has to be deleted on\n    purpose."""\n    named = []\n    for dict_name, node in _dicts(LIGHT_DICTS).items():\n        for key, value in zip(node.keys, node.values):\n            if isinstance(value, ast.Name) and value.id in REGISTERED:\n                named.append(f\'{dict_name}[{key.value!r}] -> {value.id}\')\n    assert not named, (\n        \'the light palettes now reference the register:\\n  \' + \'\\n  \'.join(named)\n        + \'\\n\\nThat is the light half, and it is not ruled yet.\')'
NEW_LIGHT_TEST = '#: The light half is ruled one value at a time. This is the allowlist, and it\n#: is what a later pass has to extend ON PURPOSE.\nLIGHT_RULED = (\'APP_HOVER_LIGHT\',)\n\n\ndef test_the_light_palettes_reference_only_what_the_register_has_ruled():\n    """This began life as "the light palettes were left alone", which was true\n    while the light half was entirely unruled. rnv-brand rev 23 ruled one value\n    of it -- APP["hover-light"] -- so the test becomes an allowlist rather than\n    a prohibition. The light LADDER is still unruled: nine surfaces inside three\n    grid steps, and which of them are real distinctions is a judgement the\n    register has not made.\n\n    THE EARLIER FORM COULD NOT HAVE CAUGHT THIS PASS. It flagged names found in\n    REGISTERED, and REGISTERED was a four-value snapshot that did not contain\n    the value being wired -- so light could have been wired underneath it and it\n    would have reported clean. REGISTERED is widened in the same commit."""\n    named = []\n    for dict_name, node in _dicts(LIGHT_DICTS).items():\n        for key, value in zip(node.keys, node.values):\n            if (isinstance(value, ast.Name) and value.id in REGISTERED\n                    and value.id not in LIGHT_RULED):\n                named.append(f\'{dict_name}[{key.value!r}] -> {value.id}\')\n    assert not named, (\n        \'the light palettes reference register values that are not ruled \'\n        \'yet:\\n  \' + \'\\n  \'.join(named)\n        + \'\\n\\nAdd the name to LIGHT_RULED in the same commit that wires it, \'\n          \'or do not wire it.\')\n\n\ndef test_the_ruled_light_value_is_actually_wired():\n    """The allowlist permits; this requires. An allowlist entry nothing uses is\n    a licence with no subject -- the same shape as a dead exemption."""\n    used = set()\n    for node in _dicts(LIGHT_DICTS).values():\n        for value in node.values:\n            if isinstance(value, ast.Name) and value.id in LIGHT_RULED:\n                used.add(value.id)\n    assert used == set(LIGHT_RULED), (\n        f\'LIGHT_RULED lists {sorted(LIGHT_RULED)} but the light palettes use \'\n        f\'{sorted(used)}\')\n\n\ndef test_the_unruled_light_surface_is_still_a_literal():\n    """scroll_bg is #eeeeee, which is now APP["hover-light"] -- and it is NOT\n    wired, on purpose. A scrollbar groove is a surface, not an interaction\n    plate, and the light SURFACE ladder is what the register has deferred.\n    Wiring it would claim a role it does not play, on the strength of a shared\n    hex. When the light ladder is ruled, this test is the thing that has to be\n    deleted deliberately."""\n    node = _dicts(LIGHT_DICTS)[\'LIGHT_THEME_COLORS\']\n    for key, value in zip(node.keys, node.values):\n        if isinstance(key, ast.Constant) and key.value == \'scroll_bg\':\n            assert isinstance(value, ast.Constant), (\n                \'scroll_bg now names a constant. If the light ladder has been \'\n                \'ruled, delete this test in that commit and say so.\')\n            assert value.value == \'#eeeeee\'\n            return\n    raise AssertionError(\'LIGHT_THEME_COLORS has no scroll_bg\')'
OLD_SWEEP = "            if isinstance(value, ast.Constant) and isinstance(value.value, str):\n                if value.value.lower() in by_value:\n                    literals.append(\n                        f'{dict_name}[{key.value!r}] = {value.value} '\n                        f'(should read {by_value[value.value.lower()]})')"
NEW_SWEEP = '            if isinstance(value, ast.Constant) and isinstance(value.value, str):\n                # Qt spells a translucent colour #AARRGGBB. This sweep compared\n                # whole strings, so an eight-digit spelling of a registered\n                # value never matched a six-digit register entry --\n                # IMAGE_MODE_COLORS kept three of them (#ED000000 twice and\n                # #ED1A1A1A) while this test reported clean and the pass it\n                # guards claimed completeness. Both lengths normalise to the\n                # RGB half now.\n                spelled = value.value.lower()\n                rgb = \'#\' + spelled[3:] if len(spelled) == 9 else spelled\n                if rgb in by_value:\n                    literals.append(\n                        f\'{dict_name}[{key.value!r}] = {value.value} \'\n                        f\'(should read {by_value[rgb]}\'\n                        f\'{" as an overlay" if rgb != spelled else ""})\')'
OLD_REG = "REGISTERED = {'TRUE_BLACK': '#000000', 'BRAND_BLACK': '#1a1a1a', 'APP_CARD': '#2a2a2a', 'APP_BORDER': '#333333'}"
NEW_REG = "REGISTERED = {'TRUE_BLACK': '#000000', 'BRAND_BLACK': '#1a1a1a', 'APP_CARD': '#2a2a2a', 'APP_BORDER': '#333333',\n              'APP_PANEL_HOVER': '#3a3a3a', 'APP_HOVER_LIGHT': '#eeeeee'}"

#: CONSTANTS supplies its own leading newline and the anchor it replaces gave
#: one up, hence the -1.
EXPECTED_ADDED = {
    SENTINEL_FILE: CONSTANTS.count("\n") - 1 + PROVENANCE.count("\n"),
    MIRROR: (PINNED.count("\n")
             + NEW_XFAIL.count("\n") - OLD_XFAIL.count("\n")
             + NEW_HOVER_TABLE.count("\n") - OLD_HOVER_TABLE.count("\n")),
    WIRING: (NEW_LIGHT_TEST.count("\n") - OLD_LIGHT_TEST.count("\n")
             + NEW_SWEEP.count("\n") - OLD_SWEEP.count("\n")
             + NEW_REG.count("\n") - OLD_REG.count("\n")),
}


def _resolve(source: str) -> dict:
    """Every palette, resolved to plain values, whether an entry is written as
    a literal or a name."""
    tree = ast.parse(source.lstrip("\ufeff"))
    consts = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                consts[target.id] = node.value.value
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            name = getattr(target, "id", None)
            if name in ALL_DICTS and isinstance(node.value, ast.Dict):
                palette = {}
                for key, value in zip(node.value.keys, node.value.values):
                    if not isinstance(key, ast.Constant):
                        continue
                    if isinstance(value, ast.Constant):
                        palette[key.value] = value.value
                    elif isinstance(value, ast.Name):
                        palette[key.value] = consts.get(value.id, f"<{value.id}>")
                    else:
                        palette[key.value] = ast.unparse(value)
                out[name] = palette
    return out


def _bounds(lines):
    """The palettes carry identically-spelled key lines, so a plain string
    replace cannot tell dark from light. Every edit is scoped to its own."""
    starts = {}
    pattern = re.compile(r"^(" + "|".join(ALL_DICTS) + r")\s*[:=]")
    for i, line in enumerate(lines):
        m = pattern.match(line)
        if m:
            starts[m.group(1)] = i
    if len(starts) != len(ALL_DICTS):
        raise SystemExit(f"expected {len(ALL_DICTS)} palettes, found {sorted(starts)}")
    order = sorted(starts.items(), key=lambda kv: kv[1])
    return {n: (st, order[i + 1][1] if i + 1 < len(order) else len(lines))
            for i, (n, st) in enumerate(order)}


def edits(tree) -> None:
    tree.sub(SENTINEL_FILE,
             '\nAPP_PROVENANCE: Final[dict[str, str]] = {',
             CONSTANTS + 'APP_PROVENANCE: Final[dict[str, str]] = {')
    tree.sub(SENTINEL_FILE, '    "APP_TEXT_DIM": "register",\n',
             '    "APP_TEXT_DIM": "register",\n' + PROVENANCE)

    source = tree.read(SENTINEL_FILE)
    lines = source.splitlines(keepends=True)
    bounds = _bounds(lines)
    swapped = 0
    for dict_name, table in SUBSTITUTE.items():
        start, end = bounds[dict_name]
        for i in range(start, end):
            line = lines[i]
            # Match the line WITHOUT its ending and put the ending back
            # verbatim. Python's `$` also matches just before a trailing
            # newline, so a pattern ending in `(,.*)$` silently drops it, and
            # the result is still valid Python -- every test passes while the
            # palette is reflowed onto one line.
            body = line.rstrip("\r\n")
            ending = line[len(body):]
            m = re.match(r"^(\s*'[a-z_0-9]+':\s*)'(#[0-9a-fA-F]{6}|"
                         r"#[0-9a-fA-F]{8})'(,.*)$", body)
            if not m:
                continue
            const = table.get(m.group(2).lower())
            if const:
                lines[i] = f"{m.group(1)}{const}{m.group(3)}{ending}"
                swapped += 1
    if swapped != EXPECTED_SUBS:
        raise SystemExit(f"expected {EXPECTED_SUBS} substitutions, made "
                         f"{swapped}. Re-derive this script before trusting it.")
    tree.write(SENTINEL_FILE, "".join(lines))
    print(f"  substituted {swapped} literals for their names")

    tree.sub(MIRROR, "    'APP_TEXT_DIM': '#aaaaaa',\n",
             "    'APP_TEXT_DIM': '#aaaaaa',\n" + PINNED)
    tree.sub(MIRROR, OLD_HOVER_TABLE, NEW_HOVER_TABLE)
    # The strict xfail and its note go together. Removing the marker without
    # rewriting the note would leave a description of a defect that no longer
    # exists standing over a passing test.
    tree.sub(MIRROR, OLD_XFAIL, NEW_XFAIL)

    tree.sub(WIRING, OLD_REG, NEW_REG)
    tree.sub(WIRING, OLD_SWEEP, NEW_SWEEP)
    tree.sub(WIRING, OLD_LIGHT_TEST, NEW_LIGHT_TEST)


def checks(tree) -> None:
    for rel, added in EXPECTED_ADDED.items():
        before = (Path.cwd() / rel).read_text(encoding="utf-8-sig")
        after = tree.read(rel)
        delta = after.count("\n") - before.count("\n")
        if delta != added:
            raise SystemExit(
                f"{rel} changed shape by {delta} lines; this pass adds exactly "
                f"{added}. A substitution that eats or adds a line ending "
                f"leaves every value identical and every test green.")

    original = (Path.cwd() / SENTINEL_FILE).read_text(encoding="utf-8-sig")
    edited = tree.read(SENTINEL_FILE)

    before, after = _resolve(original), _resolve(edited)
    if set(before) != set(after):
        raise SystemExit(f"a palette appeared or vanished: {set(before) ^ set(after)}")

    moved = {}
    for name in before:
        for key in set(before[name]) | set(after[name]):
            was, now = before[name].get(key), after[name].get(key)
            if was != now:
                moved[(name, key)] = (was, now)
    unexpected = {k: v for k, v in moved.items() if k not in EXPECTED_MOVES}
    if unexpected:
        raise SystemExit(
            "this pass moves exactly two values and it moved others:\n  "
            + "\n  ".join(f"{n}[{k!r}]: {w} -> {g}"
                          for (n, k), (w, g) in unexpected.items()))
    wrong = {k: v for k, v in moved.items()
             if EXPECTED_MOVES[k] != (v[0].lower(), v[1].lower())}
    if wrong:
        raise SystemExit(
            "an expected move did not land on the expected value:\n  "
            + "\n  ".join(f"{n}[{k!r}]: {w} -> {g}, wanted "
                          f"{EXPECTED_MOVES[(n, k)]}"
                          for (n, k), (w, g) in wrong.items()))
    missing = set(EXPECTED_MOVES) - set(moved)
    if missing:
        raise SystemExit(f"these were meant to move and did not: {sorted(missing)}")

    # The retired value must be gone from every palette, at both spellings.
    for name, palette in after.items():
        for key, value in palette.items():
            if isinstance(value, str) and value.lower() == "#d0d0d0":
                raise SystemExit(
                    f"{name}[{key!r}] is still #d0d0d0, which the register "
                    f"retired as a light interaction ground.")

    # The plate must not land on the floor.
    for name, palette in after.items():
        for key, value in palette.items():
            if ("hover" in key and isinstance(value, str)
                    and value.lower() == "#e8e8e8"):
                raise SystemExit(
                    f"{name}[{key!r}] is #e8e8e8 -- that is "
                    f"GOLD_TEXT_GROUND_FLOOR, not an interaction plate.")

    # Completeness, at BOTH spellings. The six-digit-only version of this check
    # is the defect this pass exists to fix, so it is not repeated here.
    wanted = {v for table in SUBSTITUTE.values() for v in table}
    lines = edited.splitlines()
    bounds = _bounds([l + "\n" for l in lines])
    survivors = []
    for name in ALL_DICTS:
        start, end = bounds[name]
        for i in range(start, end):
            m = re.match(r"^\s*'([a-z_0-9]+)':\s*'(#[0-9a-fA-F]{6}|"
                         r"#[0-9a-fA-F]{8})',", lines[i])
            if m and m.group(2).lower() in wanted:
                survivors.append(f"{name}[{m.group(1)!r}] = {m.group(2)}")
    if survivors:
        raise SystemExit("a value this pass names is still a literal:\n  "
                         + "\n  ".join(survivors))

    # The one that is deliberately NOT wired.
    if after["LIGHT_THEME_COLORS"].get("scroll_bg") != "#eeeeee":
        raise SystemExit("LIGHT scroll_bg was supposed to be left alone")

    if SENTINEL not in edited:
        raise SystemExit(f"expected {SENTINEL!r} in the edited palette")


GUARD_SOURCE = '"""The retired plate, the dark rung, and the translucent overlays.\n\nWHAT THIS PASS DID. rnv-brand retired #d0d0d0 as a light interaction ground and\nregistered APP["hover-light"] in its place -- first as #e8e8e8 on 2026-08-29,\nthen as #eeeeee on 2026-08-30. rev 22 had already registered APP["panel-hover"]\n#3a3a3a, which was app-owned here. Two light entries change VALUE; everything\nelse changes only how it is spelled.\n\nTHE DEFECT THIS CLOSES. ui/about_dialog.py draws the hover ground from\ndialog_btn_hover_bg and the hover label from accent_ink, in the same rule. In\nlight that was BRAND_DARK_GOLD_DEEP #7e6529 on #d0d0d0 -- 3.6013:1 against a\n4.5 floor. It had been wrong as long as the plate existed and carried a STRICT\nxfail since 2026-08-28, written so that fixing it would fail the test and force\nthe note to be rewritten rather than let the exemption outlive the defect.\n\nWHY #eeeeee AND NOT #e8e8e8, WHICH ALSO CLEARS. #e8e8e8 clears by 0.0334 and is\nthe ground BRAND_DARK_GOLD_DEEP is derived against -- rev 24 registered it as\nGOLD_TEXT_GROUND_FLOOR. A plate on that value fails the moment the gold moves\none step: -13 instead of -14 gives 4.4675. #eeeeee clears by 0.2875 and is\ngrey(14) exactly. A boundary is not a plate.\n\nTHE OVERLAYS. Qt spells a translucent colour #AARRGGBB. The 2026-08-29 wiring\npass swept for six-digit literals, so #ED000000 never matched #000000 and three\nregistered values sat in IMAGE_MODE_COLORS -- a DARK dict here -- while the\nguard reported clean.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\n\nimport pytest\n\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK,\n                       IMAGE_MODE_COLORS as IMAGE,\n                       LIGHT_THEME_COLORS as LIGHT)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / \'ui/colors.py\'\n\nGRID_STEP = 0x11\nLADDER_STEP = 0x10\nTEXT_FLOOR = 4.5\n\n#: Constant name -> the APP key it mirrors, and the value both hold.\nNEW = {\n    \'APP_PANEL_HOVER\': (\'panel-hover\', \'#3a3a3a\'),\n    \'APP_HOVER_LIGHT\': (\'hover-light\', \'#eeeeee\'),\n}\n\n#: Overlay constant -> (the six-digit constant it composites, its APP key).\nOVERLAYS = {\n    \'APP_WINDOW_OVERLAY\': (\'TRUE_BLACK\', \'window\'),\n    \'APP_PANEL_OVERLAY\': (\'BRAND_BLACK\', \'panel\'),\n}\n\n#: palette dict name -> the keys in it that must now name a constant.\nWIRED = {\n    \'DARK_THEME_COLORS\': (\'dialog_btn_hover_bg\', \'tab_hover_bg\'),\n    \'IMAGE_MODE_COLORS\': (\'dialog_btn_hover_bg\', \'tab_hover_bg\',\n                          \'window_bg\', \'panel_bg\', \'scroll_bg\'),\n    \'LIGHT_THEME_COLORS\': (\'dialog_btn_hover_bg\', \'tab_hover_bg\'),\n}\n\n#: dict NAME -> the live dict. Looking a key up in the wrong palette is how a\n#: per-mode difference gets checked against the other mode\'s value and passes.\nPALETTES = {\'DARK_THEME_COLORS\': DARK, \'IMAGE_MODE_COLORS\': IMAGE,\n            \'LIGHT_THEME_COLORS\': LIGHT}\n\n#: The value the register retired as a light interaction ground.\nRETIRED = \'#d0d0d0\'\n\n#: The value the plate must not BE, however close it looks.\nFLOOR = \'#e8e8e8\'\n\n\ndef grey(n: int) -> str:\n    v = n * GRID_STEP\n    return \'#%02x%02x%02x\' % (v, v, v)\n\n\ndef _luminance(value: str) -> float:\n    channels = [int(value.lstrip(\'#\')[i:i + 2], 16) / 255 for i in (0, 2, 4)]\n    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4\n                for c in channels]\n    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]\n\n\ndef _contrast(a: str, b: str) -> float:\n    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)\n    return (high + 0.05) / (low + 0.05)\n\n\ndef _dict_node(name: str) -> ast.Dict:\n    tree = ast.parse(SRC.read_text(encoding=\'utf-8-sig\'))\n    for node in ast.walk(tree):\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            target = node.targets[0] if isinstance(node, ast.Assign) else node.target\n            if getattr(target, \'id\', None) == name and isinstance(node.value, ast.Dict):\n                return node.value\n    raise AssertionError(f\'{name} is not a dict literal in ui/colors.py\')\n\n\ndef _entry(node: ast.Dict, key: str):\n    for k, v in zip(node.keys, node.values):\n        if isinstance(k, ast.Constant) and k.value == key:\n            return v\n    return None\n\n\n# ------------------------------------------------------------- guard the guard\n\ndef test_everything_this_file_reads_still_exists():\n    """Renaming a key must fail loudly here rather than let the rest of this\n    file pass quietly over nothing."""\n    for name in list(NEW) + list(OVERLAYS):\n        assert hasattr(colors, name), f\'ui.colors has no {name}\'\n    for dict_name, keys in WIRED.items():\n        assert dict_name in PALETTES, dict_name\n        for key in keys:\n            assert key in PALETTES[dict_name], f\'{dict_name} has no {key!r}\'\n\n\ndef test_the_wiring_map_is_not_empty():\n    """Every sweep below iterates WIRED. An empty map passes all of them."""\n    assert WIRED and all(WIRED.values())\n    assert sum(len(v) for v in WIRED.values()) >= 9\n\n\n# ------------------------------------------------------------------ the value\n\ndef test_the_new_constants_hold_the_registered_values():\n    """The local half of the mirror. Runs everywhere, including where\n    engine.brand is not importable."""\n    drift = {n: getattr(colors, n) for n, (_, v) in NEW.items()\n             if getattr(colors, n) != v}\n    assert not drift, (\n        f\'these constants no longer hold their registered values: {drift}\\n\'\n        f\'If the brand moved, update this file in the same commit that updates \'\n        f\'ui/colors.py -- never one without the other.\')\n\n\ndef test_the_new_constants_match_rnv_brand():\n    """The upstream half. Skips where rnv-brand is not importable."""\n    brand = pytest.importorskip(\n        \'engine.brand\',\n        reason=\'rnv-brand not importable here; the local pin is doing the work\')\n    drift = []\n    for name, (key, _) in NEW.items():\n        theirs, mine = brand.APP[key], getattr(colors, name)\n        if mine.lower() != theirs.lower():\n            drift.append(f\'{name}: ours {mine}, theirs APP[{key!r}] {theirs}\')\n    assert not drift, \'drift from rnv-brand:\\n  \' + \'\\n  \'.join(drift)\n\n\ndef test_provenance_is_declared_for_everything_this_pass_named():\n    """A classification that lives only in a test drifts from the thing it\n    classifies, so it lives in the module and is read from there."""\n    for name in NEW:\n        assert colors.APP_PROVENANCE.get(name) == \'register\', name\n    for name in OVERLAYS:\n        assert colors.APP_PROVENANCE.get(name) == \'register-overlay\', name\n\n\n# ------------------------------------------------------------- the retirement\n\ndef test_the_retired_value_is_gone_from_every_palette():\n    """#d0d0d0 is ruled out as a light interaction ground, not merely replaced\n    in the two places that prompted the ruling."""\n    looked, found = 0, []\n    for dict_name, live in PALETTES.items():\n        for key, value in live.items():\n            if not isinstance(value, str):\n                continue\n            looked += 1\n            if value.lower() == RETIRED:\n                found.append(f\'{dict_name}[{key!r}]\')\n    assert looked >= 60, f\'only {looked} entries seen -- the sweep is blind\'\n    assert not found, f\'{RETIRED} is retired and still in use: {found}\'\n\n\ndef test_gold_carries_on_the_plate_in_every_mode():\n    """The defect the strict xfail was holding open. This is the same pairing\n    the About dialog makes: the ground from dialog_btn_hover_bg and the label\n    from accent_ink, in one rule."""\n    failures = []\n    for dict_name, live in PALETTES.items():\n        ratio = _contrast(live[\'accent_ink\'], live[\'dialog_btn_hover_bg\'])\n        if ratio < TEXT_FLOOR:\n            failures.append(f\'{dict_name}: {live["accent_ink"]} on \'\n                            f\'{live["dialog_btn_hover_bg"]} = {ratio:.4f}\')\n    assert not failures, \'gold does not carry on the plate:\\n  \' + \'\\n  \'.join(failures)\n\n\ndef test_the_plate_is_a_step_on_the_ink_grid():\n    assert colors.APP_HOVER_LIGHT == grey(14) == \'#eeeeee\'\n\n\ndef test_the_plate_is_not_the_gold_text_floor():\n    """Both clear the floor. Only one clears it by enough to survive the gold\n    moving, and the other is the value the gold is calibrated against."""\n    gold = colors.BRAND_DARK_GOLD_DEEP\n    here = _contrast(gold, colors.APP_HOVER_LIGHT)\n    edge = _contrast(gold, FLOOR)\n    assert colors.APP_HOVER_LIGHT.lower() != FLOOR\n    assert here - TEXT_FLOOR >= 0.2, (\n        f\'the plate clears the floor by only {here - TEXT_FLOOR:.4f}. The \'\n        f\'register moved APP["hover-light"] here for margin, not for a pass.\')\n    assert edge - TEXT_FLOOR < 0.05, (\n        f\'{FLOOR} now clears by {edge - TEXT_FLOOR:.4f}, so it is no longer the \'\n        f\'knife-edge this ruling was about. Either the gold moved or the floor \'\n        f\'did; re-derive before trusting the value above.\')\n\n\ndef test_the_floor_is_not_used_as_a_hover_anywhere():\n    """A negative check needs a companion proving it is still looking."""\n    looked, found = 0, []\n    for dict_name, live in PALETTES.items():\n        for key, value in live.items():\n            if \'hover\' not in key or not isinstance(value, str):\n                continue\n            looked += 1\n            if value.lower() == FLOOR:\n                found.append(f\'{dict_name}[{key!r}]\')\n    assert looked >= 6, f\'only {looked} hover keys seen -- the sweep is blind\'\n    assert not found, (\n        f\'{FLOOR} is being used as a hover plate: {found}. It is \'\n        f\'GOLD_TEXT_GROUND_FLOOR, not an interaction state.\')\n\n\n# ------------------------------------------------------------------ the ladder\n\ndef test_the_dark_rungs_are_exact_steps_on_the_ladder():\n    """BRAND_BLACK + n * 0x10. #3a3a3a was app-owned on the argument that the\n    ladder might not be real. It is, and this is what says so."""\n    base = int(colors.BRAND_BLACK.lstrip(\'#\'), 16)\n    for n, name in ((0, \'BRAND_BLACK\'), (1, \'APP_CARD\'), (2, \'APP_PANEL_HOVER\')):\n        want = base + n * (LADDER_STEP * 0x010101)\n        assert int(getattr(colors, name).lstrip(\'#\'), 16) == want, (\n            f\'{name} is {getattr(colors, name)}, not rung n={n}\')\n\n\ndef test_the_border_is_an_edge_and_not_a_rung():\n    """The distinction that made the ladder look incomplete. #333333 is grey(3)\n    on the ink grid, which governs inks and edges; it was never a surface."""\n    assert colors.APP_BORDER == grey(3)\n    base = int(colors.BRAND_BLACK.lstrip(\'#\'), 16)\n    rungs = {base + n * (LADDER_STEP * 0x010101) for n in range(-1, 3)}\n    assert int(colors.APP_BORDER.lstrip(\'#\'), 16) not in rungs\n\n\n# ---------------------------------------------------------------- the overlays\n\ndef test_every_overlay_is_its_base_at_the_declared_alpha():\n    """The overlays are written out because Qt wants eight digits and composing\n    them would make the palette resolve to an expression. This is the\n    relationship composition would have given, asserted instead."""\n    for name, (base_name, _key) in OVERLAYS.items():\n        overlay = getattr(colors, name)\n        base = getattr(colors, base_name)\n        assert len(overlay) == 9, f\'{name} is {overlay}, not #AARRGGBB\'\n        assert overlay[1:3].upper() == colors.IMAGE_OVERLAY_ALPHA.upper(), (\n            f\'{name} composites at {overlay[1:3]}, not IMAGE_OVERLAY_ALPHA\')\n        assert overlay[3:].lower() == base[1:].lower(), (\n            f\'{name} is {overlay}, whose colour half is not {base_name} \'\n            f\'{base}. An overlay that stops tracking its base is the exact \'\n            f\'drift this naming exists to prevent.\')\n\n\ndef test_every_overlay_base_is_still_a_register_value():\n    """Guard the guard. If a base stopped being registered, these would track\n    something app-owned under a name that says otherwise."""\n    brand = pytest.importorskip(\'engine.brand\', reason=\'rnv-brand not importable\')\n    for name, (base_name, key) in OVERLAYS.items():\n        assert brand.APP[key].lower() == getattr(colors, base_name).lower(), (\n            f\'{name} claims to composite APP[{key!r}], which the register now \'\n            f\'holds as {brand.APP[key]}\')\n\n\ndef test_no_translucent_register_value_is_left_as_a_literal():\n    """The defect this pass fixes, asserted from the other side."""\n    registered = {getattr(colors, n).lower()\n                  for n in (\'TRUE_BLACK\', \'WHITE\', \'BRAND_BLACK\', \'APP_CARD\',\n                            \'APP_BORDER\', \'APP_TEXT\', \'APP_TEXT_DIM\',\n                            \'APP_PANEL_HOVER\', \'APP_HOVER_LIGHT\')}\n    found = []\n    for dict_name in PALETTES:\n        node = _dict_node(dict_name)\n        for k, v in zip(node.keys, node.values):\n            if (isinstance(v, ast.Constant) and isinstance(v.value, str)\n                    and len(v.value) == 9 and v.value.startswith(\'#\')\n                    and \'#\' + v.value[3:].lower() in registered):\n                found.append(f\'{dict_name}[{k.value!r}] = {v.value}\')\n    assert not found, (\n        \'registered values still spelled as translucent literals:\\n  \'\n        + \'\\n  \'.join(found))\n\n\n# ------------------------------------------------- the spelling, not the value\n\ndef test_every_wired_entry_names_a_constant_not_a_literal():\n    """A literal cannot follow its base."""\n    allowed = set(NEW) | set(OVERLAYS)\n    literals = []\n    for dict_name, keys in WIRED.items():\n        node = _dict_node(dict_name)\n        for key in keys:\n            value = _entry(node, key)\n            if not isinstance(value, ast.Name) or value.id not in allowed:\n                literals.append(\n                    f\'{dict_name}[{key!r}] = \'\n                    f\'{ast.unparse(value) if value else "missing"}\')\n    assert not literals, (\n        \'entries still written as literals:\\n  \' + \'\\n  \'.join(literals))\n\n\ndef test_the_resolved_values_are_the_constants():\n    """The AST check proves the spelling; this proves the value."""\n    for dict_name, keys in WIRED.items():\n        node = _dict_node(dict_name)\n        for key in keys:\n            name = _entry(node, key).id\n            assert PALETTES[dict_name][key] == getattr(colors, name), (\n                f\'{dict_name}[{key!r}] resolves to \'\n                f\'{PALETTES[dict_name][key]}, not {name}\')\n'


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
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists() or p.read_text(encoding="utf-8") != text:
                p.write_text(text, encoding="utf-8")
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
        raise SystemExit(f"run this from the root of a {REPO} checkout "
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
