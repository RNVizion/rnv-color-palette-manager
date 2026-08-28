#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Name the APP register in rnv-color-palette-manager, move the dark ink onto the
grid, and make the tab keys say what they do.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

FOUR CHANGES, ONE JOB. Each is a name or a value that was not telling the
truth.

1. THE APP REGISTER IS NAMED

   #e0e0e0, #1a1a1a, #2a2a2a and #333333 were bare literals with no constant
   and no provenance, and every one is REGISTERED in RNVizion/rnv-brand. The
   brand could move and nothing here would notice. It nearly did: APP["text"]
   moved to #dddddd in rnv-brand@68d195e.

2. THE DARK INK MOVES TO grey(13)

   DARK + IMAGE  text_color, button_text, button_hover_text
                 #e0e0e0 -> APP_TEXT (#dddddd)

   LIGHT hover_color and tab_bg stay at #e0e0e0. They are SURFACES, and the
   published grid governs inks and edges and deliberately not surfaces. That
   split is the whole reason #e0e0e0 looked like an exception to a rule it was
   never subject to.

3. THE TAB KEYS SAY WHAT THEY DO

   tab_selected -> tab_selected_bg      renamed to the majority spelling
   tab_hover    -> dialog_btn_hover_bg  moved to the button section
   tab_bg, tab_selected_bg, tab_hover_bg   annotated NOT CONSUMED

   This app paints its tabs from card_bg (rest AND hover) and panel_bg
   (selected). So tab_bg and tab_selected were never painting anything, and
   tab_hover was painting a QPushButton in the About dialog -- a key named for
   a tab filling a button. The first two are KEPT and annotated, because
   picker and icon-builder paint from the equivalents and these values already
   agree with them; deleting them would throw away a correct colour decision.
   The third is renamed, not deleted, because it is consumed.

4. THE TWO DIALOGS AGREE ABOUT THE PANE

   tab_pane_bg is DELETED from all three palettes.

   About and Settings drew the tab pane from different keys. In light that
   made About's pane #ffffff -- the same as card_bg, so a card sitting on it
   had nothing but its own border, the exact edge-collapse the 2026-08-27
   surfaces ruling fixed everywhere else. In image it made the pane fully
   opaque, the one surface in that dialog opting out of image mode.

   ui/about_dialog.py already carried the answer as its own fallback:

       pane_bg = theme.get('tab_pane_bg', theme['panel_bg'])

   Deleting the key makes that the live path. THE OVERRIDE POINT DOES NOT
   DISAPPEAR -- it IS the .get(). A dialog that wants a distinct pane adds the
   key back and nothing else changes. What is removed is a duplicate of
   panel_bg that had to be kept equal by hand, which is how two values drift.

   Dark is unaffected: tab_pane_bg and panel_bg were both #1a1a1a already.

TWO GUARDS, NOT ONE

rnv-text-transformer's mirror test guards with importorskip('engine.brand'),
so where rnv-brand is not importable it reports clean and drift hides. Every
register value is pinned LOCALLY as well as mirrored UPSTREAM.

ONE EXISTING TEST IS WIDENED, NOT WEAKENED

tests/test_brand_mirror.py::test_provenance_covers_every_gold_constant sweeps
every name starting with BRAND_ and demands a GOLD_PROVENANCE entry.
BRAND_BLACK is a brand-mirrored constant but not a gold, so the sweep now
accepts a name covered by EITHER map -- and a new test forbids a name being
claimed by both, so nothing can fall between them.
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
DESCRIPTION = "name the APP register, move the ink, sort out the tab keys"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = 'APP_TEXT: Final[str] = "#dddddd"'
GUARD = "tests/test_app_mirror.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

ABOUT = "ui/about_dialog.py"
UNITTEST_FILE = "test_rnv_palette_manager.py"
MIRROR_TEST = "tests/test_brand_mirror.py"

SUITES = [
    ("pytest tests/",
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ("unittest suite",
     [sys.executable, "-m", "unittest", "test_rnv_palette_manager"]),
]

ANCHOR = "\n\n# ==================== Semantic UI Constants ====================\n"

INK_KEYS = ("text_color", "button_text", "button_hover_text")
OLD_INK = "'#e0e0e0'"
NEW_INK = "APP_TEXT"

APP_BLOCK = '\n\n# ==================== APP Neutrals ====================\n#\n# MIRRORED FROM RNVizion/rnv-brand engine/brand.py APP. Until 2026-08-28 these\n# were bare hex literals in the palettes below -- no constant, no provenance --\n# and every one is a REGISTERED brand value. A registered value could move\n# upstream and this app would keep the old one silently, which is the failure\n# #c4a458 had, one level down. It nearly happened: APP["text"] moved from\n# #e0e0e0 to #dddddd in rnv-brand@68d195e.\n#\n# THE INK GRID, published in the brand beside that move:\n#\n#     grey(n) = n * 0x11, n in 0..15.   TRUE_BLACK -> WHITE in fifteen steps.\n#\n# IT GOVERNS INKS AND EDGES AND DELIBERATELY DOES NOT GOVERN SURFACES.\n# BRAND_BLACK sits at n = 1.53 and APP_CARD at n = 2.47; BRAND_BLACK is a\n# permanent and will not move to fit a ladder. The scope is part of the rule.\n#\n# THIS PASS WIRES THE INK ONLY. The other five constants are defined and\n# mirrored so drift is caught, but the palettes still spell them as literals;\n# rewiring those is the grey-ramp derivation pass. Mixing a mechanical\n# substitution into a value change makes both unreadable.\n\nTRUE_BLACK: Final[str] = "#000000"\n"""engine/brand.py TRUE_BLACK, and APP["window"]. Primary text in light mode,\nand the label on a pressed control in dark. grey(0)."""\n\nWHITE: Final[str] = "#ffffff"\n"""engine/brand.py WHITE. Control surface in light mode. grey(15)."""\n\nBRAND_BLACK: Final[str] = "#1a1a1a"\n"""engine/brand.py BRAND_BLACK, and APP["panel"]. Charcoal; a permanent.\nNot on the ink grid (n = 1.53) and not required to be -- it is a surface."""\n\nAPP_CARD: Final[str] = "#2a2a2a"\n"""engine/brand.py APP["card"]. A surface, not on the grid (n = 2.47)."""\n\nAPP_BORDER: Final[str] = "#333333"\n"""engine/brand.py APP["border"]. grey(3). An edge, so the grid governs it."""\n\nAPP_TEXT: Final[str] = "#dddddd"\n"""engine/brand.py APP["text"]. grey(13). Primary ink in dark and image mode.\n\nMOVED FROM #e0e0e0 ON 2026-08-28, with the brand rather than after it.\n#e0e0e0 was one hex doing two unrelated jobs -- ink in dark mode, and a light\nSURFACE in the light palette below (hover_color and tab_bg). It refused to sit\non the grid because the grid governs inks and half its uses were not ink. Only\nthe ink half moved. Contrast falls 0.21 to 0.45 and the floor afterwards is\n7.17:1 on the pressed plate #444444, the darkest ground it is drawn on.\n"""\n\nAPP_TEXT_DIM: Final[str] = "#aaaaaa"\n"""engine/brand.py APP["text-dim"]. grey(10)."""\n\nAPP_PROVENANCE: Final[dict[str, str]] = {\n    "TRUE_BLACK": "register",\n    "WHITE": "register",\n    "BRAND_BLACK": "register",\n    "APP_CARD": "register",\n    "APP_BORDER": "register",\n    "APP_TEXT": "register",\n    "APP_TEXT_DIM": "register",\n}\n"""Declarative, and read by tests/test_app_mirror.py, in the same shape as\nGOLD_PROVENANCE above. A classification that lives only in a test drifts from\nthe thing it classifies."""\n\n'
DARK_TABS_OLD = "    # Dialog / tab widget colors\n    'tab_bg': '#2a2a2a',\n    'tab_selected': '#333333',\n    'tab_hover': '#3a3a3a',\n    'tab_pane_bg': '#1a1a1a',\n"
DARK_TABS_NEW = "    # Dialog / tab widget colors\n    #\n    # NOT CONSUMED -- all three of these. This app paints its tabs from\n    # card_bg (at rest AND on hover, so hovering an unselected tab changes\n    # only the label) and from panel_bg for the selected one, in both\n    # ui/about_dialog.py and ui/settings_dialog.py.\n    #\n    # Kept rather than deleted, on the same reasoning as text_secondary above:\n    # rnv-color-picker and rnv-icon-builder DO paint from the equivalents, and\n    # the values here already agree with them -- tab_bg matches both apps, and\n    # tab_selected_bg matches rnv-icon-builder (rnv-color-picker uses the panel\n    # step #1a1a1a instead, a two-against-one this pass records and does not\n    # settle). So wiring them up stays one line and not a colour decision.\n    #\n    # RENAMED 2026-08-28 to the spelling those two apps use. `tab_hover` left\n    # this block entirely: it was consumed, but to fill a QPushButton, and it\n    # is now dialog_btn_hover_bg in the button section above.\n    'tab_bg': '#2a2a2a',\n    'tab_selected_bg': '#333333',\n    'tab_hover_bg': '#3a3a3a',\n"
LIGHT_TABS_OLD = "    # Dialog / tab widget colors\n    'tab_bg': '#e0e0e0',\n    'tab_selected': '#ffffff',\n    'tab_hover': '#d0d0d0',\n    'tab_pane_bg': '#ffffff',\n"
LIGHT_TABS_NEW = "    # Dialog / tab widget colors\n    #\n    # NOT CONSUMED -- all three of these. This app paints its tabs from\n    # card_bg (at rest AND on hover, so hovering an unselected tab changes\n    # only the label) and from panel_bg for the selected one, in both\n    # ui/about_dialog.py and ui/settings_dialog.py.\n    #\n    # Kept rather than deleted, on the same reasoning as text_secondary above:\n    # rnv-color-picker and rnv-icon-builder DO paint from the equivalents, and\n    # the values here already agree with them -- tab_bg matches both apps, and\n    # tab_selected_bg matches rnv-icon-builder (rnv-color-picker uses the panel\n    # step #1a1a1a instead, a two-against-one this pass records and does not\n    # settle). So wiring them up stays one line and not a colour decision.\n    #\n    # RENAMED 2026-08-28 to the spelling those two apps use. `tab_hover` left\n    # this block entirely: it was consumed, but to fill a QPushButton, and it\n    # is now dialog_btn_hover_bg in the button section above.\n    'tab_bg': '#e0e0e0',\n    'tab_selected_bg': '#ffffff',\n    'tab_hover_bg': '#d0d0d0',\n"
BTN_NOTE = "    # The About dialog's button hover plate. Spelled 'tab_hover' until\n    # 2026-08-28, where it filled a QPushButton and not a tab.\n    #\n    # Deliberately NOT button_hover_bg. That is the MAIN button's inverse\n    # scheme -- #333333 in both modes, with the label flipping -- while dialog\n    # buttons take a softer plate carrying gold text and a gold border.\n    # Flattening the two would lose a scheme. Same value it always had.\n"
CONTRAST_TEST = 'tests/test_contrast_pairs.py'
MUTED_TEST = 'tests/test_muted_and_disabled_text.py'
PAIRS_OLD = 'INK_PAIRS = (\n    ("accent_ink", "panel_bg"),\n    ("accent_ink", "dialog_bg"),\n    ("accent_ink", "card_bg"),\n    ("accent_ink", "tab_pane_bg"),\n)\n'
PAIRS_NEW = 'INK_PAIRS = (\n    ("accent_ink", "panel_bg"),\n    ("accent_ink", "dialog_bg"),\n    ("accent_ink", "card_bg"),\n)\n\n# How many of those pairs each palette can actually MEASURE. Asserted exactly\n# rather than as a floor: a floor cannot tell a pair that vanished from a pair\n# that was never there.\n#\n# IMAGE resolves fewer, and the reason is worth naming rather than tolerating:\n# its window_bg and panel_bg are #AARRGGBB strings, which this flat-hex audit\n# cannot read. Gold text on a translucent ground is UNAUDITED here. That is a\n# gap in the audit, not a pass.\n#\n# IMAGE used to resolve 3, but one was a duplicate -- tab_pane_bg held the same\n# #1a1a1a as dialog_bg -- so deleting that key on 2026-08-28 removed a repeated\n# measurement rather than any coverage.\nRESOLVING = {"DARK": 3, "LIGHT": 3, "IMAGE": 2}\n'
COUNT_OLD = '    assert len(measured) >= 3, (\n        f"{theme}: only {len(measured)} ink pairs resolved -- the pair list has "\n        f"gone stale against the palette")\n'
COUNT_NEW = '    assert len(measured) == RESOLVING[theme], (\n        f"{theme}: {len(measured)} ink pairs resolved, expected "\n        f"{RESOLVING[theme]} -- the pair list has gone stale against the "\n        f"palette")\n'
NOTE_OLD = '    notes = len(re.findall(r"#\\s*NOT CONSUMED",\n                           COLORS_PY.read_text(encoding="utf-8")))\n    assert notes == 3, (\n        f"expected a NOT CONSUMED note beside each of the three "\n        f"text_secondary values, found {notes}")\n'
NOTE_NEW = '    # Counted BESIDE the key rather than across the whole file. A whole-file\n    # count measures every NOT CONSUMED note in ui/colors.py, so annotating any\n    # OTHER dead key -- which the tab block did on 2026-08-28 -- broke a test\n    # that was never about those keys. It measures what it claims now.\n    lines = COLORS_PY.read_text(encoding="utf-8").splitlines()\n    annotated = 0\n    for i, line in enumerate(lines):\n        if not line.strip().startswith("\'text_secondary\':"):\n            continue\n        if re.search(r"#\\s*NOT CONSUMED", "\\n".join(lines[max(0, i - 6):i])):\n            annotated += 1\n    assert annotated == 3, (\n        f"expected a NOT CONSUMED note beside each of the three "\n        f"text_secondary values, found {annotated}")\n'

BTN_HOVER = {"DARK_THEME_COLORS": "#3a3a3a",
             "LIGHT_THEME_COLORS": "#d0d0d0",
             "IMAGE_MODE_COLORS": "#3a3a3a"}


def _bounds(lines):
    """The three palettes carry identically-spelled key lines, so a plain
    string replace cannot tell them apart. Every edit is scoped to its dict."""
    starts = {}
    for i, line in enumerate(lines):
        m = re.match(r"^(DARK_THEME_COLORS|LIGHT_THEME_COLORS|IMAGE_MODE_COLORS)\s*:", line)
        if m:
            starts[m.group(1)] = i
    if len(starts) != 3:
        raise SystemExit(f"expected three theme dicts, found {sorted(starts)}")
    order = sorted(starts.items(), key=lambda kv: kv[1])
    return {n: (st, order[i + 1][1] if i + 1 < len(order) else len(lines))
            for i, (n, st) in enumerate(order)}


def _set(lines, span, key, expect, value):
    st, en = span
    hits = [i for i in range(st, en) if lines[i].strip().startswith(f"'{key}':")]
    if len(hits) != 1:
        raise SystemExit(f"expected one '{key}' in that palette, found {len(hits)}")
    if expect not in lines[hits[0]]:
        raise SystemExit(f"'{key}' is not {expect}: {lines[hits[0]].strip()!r}")
    lines[hits[0]] = lines[hits[0]].replace(expect, value)


def _insert_after(lines, span, key, block):
    """Put the new dialog-button key beside the button block it belongs to."""
    st, en = span
    hits = [i for i in range(st, en)
            if lines[i].strip().startswith("'button_border_color':")]
    if len(hits) != 1:
        raise SystemExit("expected one 'button_border_color' per palette")
    lines.insert(hits[0] + 1, block)


def edits(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if src.count(ANCHOR) != 1:
        raise SystemExit("could not find the Semantic UI Constants heading; "
                         "the file moved, re-derive this edit")
    src = src.replace(ANCHOR, APP_BLOCK + ANCHOR.lstrip("\n"), 1)

    # The tab blocks. DARK and IMAGE are byte-identical, LIGHT differs.
    if src.count(DARK_TABS_OLD) != 2:
        raise SystemExit(f"expected the dark tab block twice (dark and image), "
                         f"found {src.count(DARK_TABS_OLD)}")
    if src.count(LIGHT_TABS_OLD) != 1:
        raise SystemExit("expected the light tab block exactly once")
    src = src.replace(DARK_TABS_OLD, DARK_TABS_NEW, 2)
    src = src.replace(LIGHT_TABS_OLD, LIGHT_TABS_NEW, 1)

    lines = src.splitlines(keepends=True)
    b = _bounds(lines)
    # Ink, dark and image only. Light's #e0e0e0 entries are surfaces.
    for name in ("DARK_THEME_COLORS", "IMAGE_MODE_COLORS"):
        for key in INK_KEYS:
            _set(lines, b[name], key, OLD_INK, NEW_INK)

    # The renamed button-hover key, inserted last so the offsets above hold.
    for name in ("IMAGE_MODE_COLORS", "LIGHT_THEME_COLORS", "DARK_THEME_COLORS"):
        b = _bounds(lines)
        _insert_after(lines, b[name], "button_border_color",
                      BTN_NOTE + f"    'dialog_btn_hover_bg': '{BTN_HOVER[name]}',\n")
    tree.write(SENTINEL_FILE, "".join(lines))

    # The About dialog: read the renamed key, and keep the pane fallback.
    tree.sub(ABOUT,
             "        tab_hover    = theme.get('tab_hover',    theme['hover_color'])\n",
             "        # The pane below deliberately has no key: tab_pane_bg was deleted\n"
             "        # on 2026-08-28 because it held nothing panel_bg does not, and\n"
             "        # this .get() IS the override point that survived it.\n"
             "        btn_hover    = theme['dialog_btn_hover_bg']\n")
    tree.sub(ABOUT, "background-color: {tab_hover};",
             "background-color: {btn_hover};")

    # The unittest key contract.
    tree.sub(UNITTEST_FILE,
             '        "tab_bg","tab_selected","tab_hover","tab_pane_bg",',
             '        "tab_bg","tab_selected_bg","tab_hover_bg",\n'
             '        "dialog_btn_hover_bg",')

    # Widen the gold sweep to accept the second provenance map.
    tree.sub(MIRROR_TEST,
             "    missing = named - set(C.GOLD_PROVENANCE)\n",
             "    missing = named - set(C.GOLD_PROVENANCE) - set(C.APP_PROVENANCE)\n")
    tree.sub(MIRROR_TEST,
             "def test_provenance_has_no_phantom_entries():",
             "def test_no_constant_is_claimed_by_two_provenance_maps():\n"
             "    \"\"\"Widening the sweep above to accept either map only stays safe\n"
             "    while the maps do not overlap -- an entry in both would let a wrong\n"
             "    classification hide behind the right one.\"\"\"\n"
             "    both = sorted(set(C.GOLD_PROVENANCE) & set(C.APP_PROVENANCE))\n"
             "    assert not both, f\"claimed by both provenance maps: {both}\"\n"
             "\n"
             "\n"
             "def test_provenance_has_no_phantom_entries():")

    # Two of this app's own guards caught this change, and both were right.
    # Both are widened to measure what they claim instead of a proxy.
    tree.sub(CONTRAST_TEST, PAIRS_OLD, PAIRS_NEW)
    tree.sub(CONTRAST_TEST, COUNT_OLD, COUNT_NEW)
    tree.sub(MUTED_TEST, NOTE_OLD, NOTE_NEW)


def checks(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if src.count(SENTINEL) != 1:
        raise SystemExit("APP_TEXT was not defined exactly once")
    if "'tab_pane_bg'" in src:
        raise SystemExit("tab_pane_bg survives in ui/colors.py")
    for old in ("'tab_selected':", "'tab_hover':"):
        if old in src:
            raise SystemExit(f"the old spelling {old} survives")
    for new in ("'tab_selected_bg':", "'tab_hover_bg':", "'dialog_btn_hover_bg':"):
        if src.count(new) != 3:
            raise SystemExit(f"expected {new} in all three palettes, "
                             f"found {src.count(new)}")
    for key in INK_KEYS:
        if len(re.findall(rf"'{key}':\s+APP_TEXT,", src)) != 2:
            raise SystemExit(f"{key} does not read APP_TEXT in dark and image")
    # Two light surfaces must survive: hover_color and tab_bg.
    if src.count(OLD_INK) != 2:
        raise SystemExit(f"expected exactly two surviving #e0e0e0 (the light "
                         f"surfaces), found {src.count(OLD_INK)}")
    about = tree.read(ABOUT)
    if "tab_hover" in about:
        raise SystemExit("the About dialog still names tab_hover")
    if "theme.get('tab_pane_bg', theme['panel_bg'])" not in about:
        raise SystemExit("the pane fallback that makes the deletion safe is gone")
    pairs = tree.read(CONTRAST_TEST)
    # The PAIR, not the string. The replacement's own comment explains why the
    # key went, so sweeping for the bare name fails on a mention -- the same
    # use-vs-mention trap that made an early grey census count a comment as a
    # use.
    if '("accent_ink", "tab_pane_bg")' in pairs:
        raise SystemExit("the contrast audit still measures tab_pane_bg")
    if "RESOLVING = " not in pairs:
        raise SystemExit("the per-theme resolve counts were not installed")


GUARD_SOURCE = '"""\nThe APP register, the ink move, and the tab keys sorted out.\n\nFOUR THINGS LAND TOGETHER HERE, and they are one job rather than four: every\none of them is about a name or a value that was not telling the truth.\n\n1. THE APP REGISTER IS NAMED. #e0e0e0, #1a1a1a, #2a2a2a and #333333 were bare\n   literals with no constant and no provenance, and every one is a REGISTERED\n   value in RNVizion/rnv-brand. APP["text"] moved to #dddddd in\n   rnv-brand@68d195e and nothing here would have noticed.\n\n2. THE DARK INK MOVES TO grey(13). The published grid is\n   grey(n) = n * 0x11, TRUE_BLACK -> WHITE in fifteen steps. It governs inks\n   and edges and deliberately not surfaces. #e0e0e0 was one hex doing two\n   jobs -- dark ink and a LIGHT SURFACE -- which is the only reason it looked\n   like an exception. Only the ink half moved.\n\n3. THE TAB KEYS SAY WHAT THEY DO. This app paints its tabs from card_bg (rest\n   and hover) and panel_bg (selected), in BOTH dialogs. So `tab_bg` and\n   `tab_selected` were never consumed, and `tab_hover` was consumed to fill a\n   QPushButton. The first two are kept and annotated -- rnv-color-picker and\n   rnv-icon-builder paint from the equivalents and the values here already\n   agree with them -- and renamed to those apps\' spelling. The third became\n   `dialog_btn_hover_bg`, which is what it always was.\n\n4. THE TWO DIALOGS AGREE ABOUT THE PANE. `tab_pane_bg` is deleted. About and\n   Settings drew their tab pane from different keys, and in light that made\n   About\'s pane #ffffff -- the same as card_bg, so a card on it had nothing\n   but its own border. In image it made the pane fully opaque, the one surface\n   in that dialog opting out of image mode. ui/about_dialog.py already carried\n   the right answer as its fallback:\n\n       pane_bg = theme.get(\'tab_pane_bg\', theme[\'panel_bg\'])\n\n   Deleting the key makes that fallback the live path. The override point does\n   not disappear -- it IS the .get() -- so a dialog that wants a distinct pane\n   adds the key back and nothing else changes.\n\nTWO GUARDS, NOT ONE. rnv-text-transformer\'s mirror test guards with\nimportorskip(\'engine.brand\'), so where rnv-brand is not importable it reports\nclean and drift hides. Every register value is pinned LOCALLY as well as\nmirrored UPSTREAM.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\n\nimport pytest\n\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,\n                       LIGHT_THEME_COLORS as LIGHT)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / \'ui\' / \'colors.py\'\nABOUT = ROOT / \'ui\' / \'about_dialog.py\'\n\nGRID_STEP = 0x11\n\nPALETTES = {\'DARK\': DARK, \'LIGHT\': LIGHT, \'IMAGE\': IMAGE}\n\nPINNED = {\n    \'TRUE_BLACK\': \'#000000\',\n    \'WHITE\': \'#ffffff\',\n    \'BRAND_BLACK\': \'#1a1a1a\',\n    \'APP_CARD\': \'#2a2a2a\',\n    \'APP_BORDER\': \'#333333\',\n    \'APP_TEXT\': \'#dddddd\',\n    \'APP_TEXT_DIM\': \'#aaaaaa\',\n}\n\n#: Dark and image ink. These carry APP_TEXT and must reference it by name.\nINK_KEYS = (\'text_color\', \'button_text\', \'button_hover_text\')\n\n#: Unconsumed here, live in the other two apps, values already agreed.\nUNCONSUMED_TAB_KEYS = (\'tab_bg\', \'tab_selected_bg\', \'tab_hover_bg\')\n\n#: The About dialog\'s button hover plate, per mode. Unchanged values; only the\n#: name moved off `tab_hover`.\nDIALOG_BTN_HOVER = {\'DARK\': \'#3a3a3a\', \'LIGHT\': \'#d0d0d0\', \'IMAGE\': \'#3a3a3a\'}\n\n\ndef grey(n: int) -> str:\n    v = n * GRID_STEP\n    return \'#%02x%02x%02x\' % (v, v, v)\n\n\ndef _dict_node(name: str) -> ast.Dict:\n    tree = ast.parse(SRC.read_text(encoding=\'utf-8-sig\'))\n    for node in ast.walk(tree):\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            target = node.targets[0] if isinstance(node, ast.Assign) else node.target\n            if getattr(target, \'id\', None) == name and isinstance(node.value, ast.Dict):\n                return node.value\n    raise AssertionError(f\'{name} is not a dict literal in ui/colors.py\')\n\n\ndef _entry(node: ast.Dict, key: str):\n    for k, v in zip(node.keys, node.values):\n        if isinstance(k, ast.Constant) and k.value == key:\n            return v\n    return None\n\n\n# ------------------------------------------------------------- guard the guard\n\ndef test_the_names_this_file_reads_still_exist():\n    """Every assertion below reads these. Rename one and this fails loudly\n    instead of the rest quietly passing over nothing."""\n    for name in PINNED:\n        assert hasattr(colors, name), f\'ui.colors has no {name}\'\n    for mode, palette in PALETTES.items():\n        for key in INK_KEYS + UNCONSUMED_TAB_KEYS + (\'dialog_btn_hover_bg\',):\n            assert key in palette, f\'{mode} has no {key}\'\n\n\n# ------------------------------------------------------------------- the value\n\ndef test_the_ink_is_a_step_on_the_grid():\n    assert colors.APP_TEXT == grey(13) == \'#dddddd\', (\n        f\'APP_TEXT is {colors.APP_TEXT}, not grey(13).\')\n\n\ndef test_every_pinned_neutral_is_what_the_register_held():\n    """The local half of the mirror. Runs everywhere."""\n    drift = {n: getattr(colors, n) for n, v in PINNED.items()\n             if getattr(colors, n) != v}\n    assert not drift, (\n        f\'these constants no longer hold their registered values: {drift}\\n\'\n        f\'If the brand moved, update PINNED in the same commit that updates \'\n        f\'ui/colors.py -- never one without the other.\')\n\n\ndef test_register_values_match_rnv_brand():\n    """The upstream half. Skips where rnv-brand is absent, which is exactly\n    why the pin above is not optional."""\n    brand = pytest.importorskip(\n        \'engine.brand\',\n        reason=\'rnv-brand not importable here; the local pin is doing the work\')\n    drift = []\n    for name in PINNED:\n        theirs = (brand.APP[name[4:].lower().replace(\'_\', \'-\')]\n                  if name.startswith(\'APP_\') else getattr(brand, name))\n        if getattr(colors, name).lower() != theirs.lower():\n            drift.append(f\'{name}: ours {getattr(colors, name)}, theirs {theirs}\')\n    assert not drift, \'drift from rnv-brand:\\n  \' + \'\\n  \'.join(drift)\n\n\ndef test_every_dark_and_image_ink_reads_the_constant_not_a_literal():\n    """A literal cannot follow its base. If APP_TEXT moves again these move\n    with it, or this fails."""\n    literals = []\n    for dict_name, mode in ((\'DARK_THEME_COLORS\', \'DARK\'),\n                            (\'IMAGE_MODE_COLORS\', \'IMAGE\')):\n        node = _dict_node(dict_name)\n        for key in INK_KEYS:\n            value = _entry(node, key)\n            if not (isinstance(value, ast.Name) and value.id == \'APP_TEXT\'):\n                literals.append(\n                    f\'{mode}.{key} = \'\n                    f\'{ast.unparse(value) if value is not None else "missing"}\')\n    assert not literals, (\'ink entries still written as literals:\\n  \'\n                          + \'\\n  \'.join(literals))\n\n\ndef test_the_resolved_ink_is_the_constant():\n    for mode in (\'DARK\', \'IMAGE\'):\n        for key in INK_KEYS:\n            assert PALETTES[mode][key] == colors.APP_TEXT, f\'{mode}[{key!r}]\'\n\n\ndef test_the_light_surfaces_did_not_follow_the_ink():\n    """#e0e0e0\'s other half is a LIGHT SURFACE, and the grid does not govern\n    surfaces. hover_color and tab_bg stay exactly where they were."""\n    assert LIGHT[\'hover_color\'] == \'#e0e0e0\'\n    assert LIGHT[\'tab_bg\'] == \'#e0e0e0\'\n\n\ndef test_the_light_ink_is_true_black():\n    """Primary text is one role with two mode values: dark is a grey on the\n    grid, light is TRUE_BLACK."""\n    assert LIGHT[\'text_color\'] == colors.TRUE_BLACK == \'#000000\'\n\n\n# ------------------------------------------------------------------ the tabs\n\ndef _consumers(key: str) -> list[str]:\n    """Where a theme key is read outside the palette file and the tests."""\n    sites = []\n    for path in ROOT.rglob(\'*.py\'):\n        parts = path.parts\n        if any(p in parts for p in (\'.git\', \'__pycache__\', \'tests\')):\n            continue\n        if path.name.startswith(\'test_\') or path == SRC:\n            continue\n        # A delivery script at the root names the keys it moves. Sweeping it\n        # makes this guard fail on the very run that installs it.\n        if path.parent == ROOT and path.name.startswith(\'up\'):\n            continue\n        text = path.read_text(encoding=\'utf-8-sig\', errors=\'replace\')\n        for lineno, line in enumerate(text.splitlines(), 1):\n            if f"\'{key}\'" in line or f\'"{key}"\' in line:\n                sites.append(f\'{path.relative_to(ROOT)}:{lineno}\')\n    return sites\n\n\n@pytest.mark.parametrize(\'key\', UNCONSUMED_TAB_KEYS)\ndef test_the_tab_keys_are_still_unconsumed(key):\n    """They are kept because picker and icon-builder paint from the\n    equivalents and these values already agree. The note beside them only\n    helps while it is true: wire one up and this says so."""\n    sites = _consumers(key)\n    assert not sites, (\n        f\'{key} is now read at {sites}. It is annotated NOT CONSUMED in \'\n        f\'ui/colors.py -- update the note in the same commit.\')\n\n\ndef test_the_tab_keys_carry_the_note_that_says_so():\n    """Both halves of the arrangement, held together. The values are correct\n    and the note explains why they are not painted."""\n    src = SRC.read_text(encoding=\'utf-8-sig\')\n    assert src.count(\'NOT CONSUMED\') >= 4, (\n        \'the NOT CONSUMED notes are gone -- text_secondary had three and the \'\n        \'tab block adds one\')\n\n\ndef test_the_tabs_are_actually_painted_from_the_surfaces():\n    """What the keys above are NOT doing, something else is. Both dialogs\n    fill a tab from card_bg and the selected one from the pane."""\n    for path in (ABOUT, ROOT / \'ui\' / \'settings_dialog.py\'):\n        text = path.read_text(encoding=\'utf-8-sig\')\n        assert \'QTabBar::tab\' in text, f\'{path.name} no longer styles tabs\'\n        assert \'card_bg\' in text, (\n            f\'{path.name} no longer reads card_bg -- if the tabs were wired to \'\n            f\'the tab_* keys, those keys are no longer unconsumed\')\n\n\ndef test_the_dialog_button_hover_kept_its_value_and_gained_its_name():\n    """A rename, not a retune. `tab_hover` filled a QPushButton; the value did\n    not change when the name stopped saying \'tab\'."""\n    for mode, expected in DIALOG_BTN_HOVER.items():\n        assert PALETTES[mode][\'dialog_btn_hover_bg\'] == expected, mode\n\n\ndef test_the_dialog_button_hover_is_not_the_main_button_scheme():\n    """Deliberately not button_hover_bg. That is the MAIN button\'s inverse\n    scheme -- #333333 in both modes with the label flipping. Dialog buttons\n    take a softer plate with gold text and border. Flattening the two would\n    lose a scheme."""\n    for mode, palette in PALETTES.items():\n        assert palette[\'dialog_btn_hover_bg\'] != palette[\'button_hover_bg\'], (\n            f\'{mode}: the dialog button hover has been flattened onto the main \'\n            f\'button hover\')\n\n\n# -------------------------------------------------------------------- the pane\n\ndef test_tab_pane_bg_is_gone_from_every_palette():\n    for mode, palette in PALETTES.items():\n        assert \'tab_pane_bg\' not in palette, (\n            f\'{mode} still defines tab_pane_bg. It was deleted because it held \'\n            f\'nothing panel_bg does not; if a dialog needs a distinct pane, \'\n            f\'that is a decision to make on purpose, with a value and a note.\')\n\n\ndef test_the_about_dialog_still_resolves_a_pane():\n    """Guard the guard for the deletion: the fallback must still be there, or\n    the key is gone AND the override point with it."""\n    text = ABOUT.read_text(encoding=\'utf-8-sig\')\n    assert "theme.get(\'tab_pane_bg\', theme[\'panel_bg\'])" in text, (\n        \'the fallback that makes the deletion safe is gone from \'\n        \'ui/about_dialog.py\')\n\n\ndef test_both_dialogs_now_draw_the_same_pane():\n    """The point of the deletion. Whatever About resolves must equal what\n    Settings uses, in every mode."""\n    for mode, palette in PALETTES.items():\n        resolved = palette.get(\'tab_pane_bg\', palette[\'panel_bg\'])\n        assert resolved == palette[\'panel_bg\'], mode\n\n\ndef test_the_light_pane_is_no_longer_the_card_colour():\n    """What the alignment bought. About\'s pane was #ffffff, the same as\n    card_bg, so a card sitting on it had only its own border."""\n    resolved = LIGHT.get(\'tab_pane_bg\', LIGHT[\'panel_bg\'])\n    assert resolved != LIGHT[\'card_bg\'], (\n        \'the light pane is the card colour again\')\n    assert resolved == \'#f5f5f5\'\n\n\ndef test_the_image_pane_is_translucent_like_the_rest_of_image_mode():\n    """It was fully opaque #1a1a1a -- the one surface in that dialog opting\n    out of image mode."""\n    resolved = IMAGE.get(\'tab_pane_bg\', IMAGE[\'panel_bg\'])\n    assert resolved.upper().startswith(\'#ED\'), (\n        f\'the image pane is {resolved}, which is opaque\')\n\n\n# ---------------------------------------------------------------- what it costs\n\ndef _luminance(value: str) -> float:\n    h = value.lstrip(\'#\')\n    if len(h) == 8:\n        h = h[2:]\n    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]\n    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]\n    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]\n\n\ndef _contrast(a: str, b: str) -> float:\n    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)\n    return (hi + 0.05) / (lo + 0.05)\n\n\ndef test_the_ink_clears_the_text_floor_on_every_dark_ground_it_touches():\n    grounds = (\'#000000\', \'#1a1a1a\', \'#2a2a2a\', \'#333333\', \'#3a3a3a\', \'#444444\')\n    worst = min((_contrast(colors.APP_TEXT, g), g) for g in grounds)\n    assert worst[0] >= 4.5, (\n        f\'the ink falls to {worst[0]:.2f}:1 on {worst[1]}, under the 4.5 floor\')\n\n\n# ------------------------------------------------------- one defect, recorded\n\n@pytest.mark.xfail(\n    strict=True,\n    reason=\'KNOWN DEFECT, pre-existing and out of scope for the 2026-08-28 ink \'\n           \'pass. Light gold text on the dialog button hover plate is 3.60:1, \'\n           \'under the 4.5 floor. It surfaced only because naming the plate \'\n           \'brought it into an audit for the first time -- it has been wrong \'\n           \'as long as the plate has existed. Awaiting a ruling: either the \'\n           \'plate moves above #e8e8e8, or the hover label stops being gold. \'\n           \'Marked strict so fixing it FAILS this test and forces the note to \'\n           \'be updated rather than quietly outliving the defect.\')\ndef test_gold_text_clears_the_dialog_button_hover_plate():\n    """The pairing is real: ui/about_dialog.py sets the hover ground from\n    dialog_btn_hover_bg and the hover label from accent_ink, in the same rule.\n\n        DARK   #d2bc93 on #3a3a3a   6.15  passes\n        IMAGE  #d2bc93 on #3a3a3a   6.15  passes\n        LIGHT  #7e6529 on #d0d0d0   3.60  FAILS\n\n    rnv-brand publishes the reason: below #e8e8e8, gold does not carry text.\n    #d0d0d0 is well below it. That is a ruling, not a gap, so the plate is\n    what is wrong here rather than the floor.\n    """\n    for mode, palette in PALETTES.items():\n        ratio = _contrast(palette[\'accent_ink\'], palette[\'dialog_btn_hover_bg\'])\n        assert ratio >= 4.5, (\n            f\'{mode}: {palette["accent_ink"]} on \'\n            f\'{palette["dialog_btn_hover_bg"]} = {ratio:.2f}:1\')\n'


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
