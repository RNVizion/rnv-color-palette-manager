"""derive every alpha-carrying colour from its base

    python up.py             # apply, then run the guard and CI's own command
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guard and CI's command, change nothing

For rnv-color-palette-manager, derived against a fresh clone at the live head.

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-24. Every colour this application writes at an alpha becomes
translucent(BASE, ALPHA), so a change to a base ripples to every alpha form of it.
One pixel moves, by ruling: the image-mode scrollbar handle leaves #505050 at
100 for GREY_44 at 150, closing RNV-COLLAPSE-505050's last string spelling here.

The collapse guard rides along, because it reported the value gone while it
painted: it decoded nothing but quoted six-digit hex. It now reads every
spelling, and names the two integer tuples still awaiting a ruling rather
than claiming they are not there.

The two overlays keep their exact string, and the size readout keeps rgba(),
because the locked suite checks both. Nothing else moves.
"""
from __future__ import annotations

import argparse
import ast
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = 'rnv-color-palette-manager'
SENTINEL = 'RNV-DERIVE-ALPHA'
SENTINEL_FILE = "tests/conftest.py"
GUARD = "tests/test_derived_values.py"
DESCRIPTION = 'derive every alpha-carrying colour from its base'

#: EXACTLY WHAT CI RUNS. Both workflows run `python run_tests.py`, which runs
#: the locked root suite under unittest and then tests/ under pytest. The
#: icon-builder round was verified with `pytest tests/` alone and went red in
#: CI on a root-suite test that command never reaches.
SUITES = [("python run_tests.py  (both CI workflows)",
           [sys.executable, "run_tests.py"])]

#: The workflows SUITES was written from, by content hash. The build refuses
#: a script whose record has gone stale or misses a workflow.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '898c16b8a02fa92b09c1bed0fa1f9f8b872d2d3d29d506b7a9c9a1ec357de42e', '.github/workflows/tests.yml': '5d3891f82137b62cb3b2576454eb30079ee981ca559fac90d67431f579e5abe5'}

SHADOWS = {"colors.py", "conftest.py", "run_tests.py",
           "test_rnv_palette_manager.py"}

LEFT_ALONE = [
    "the two integer-tuple spellings of #505050, SLOT_BORDER_THIN_COLOR and "
    "HISTORY_SWATCH_BORDER, both (80, 80, 80) and both painted -- the thin "
    "slot pen and the history swatch pen. Whether a slot border collapses "
    "with a scrollbar handle is a ruling. The collapse guard now pins them "
    "as the known set instead of claiming the value is gone.",
    "every colour spelled as an integer tuple, the registered ones included: "
    "SEARCH_DIM_OVERLAY (0, 0, 0, 140), DEFAULT_SLOT_COLOR_IMAGE_RGB "
    "(0, 0, 0, 171), PREVIEW_GRID_BORDER (0, 0, 0). Tuples are a notation of "
    "their own and get a fleet round of their own; this application already "
    "derives its gold tuples with _to_rgb(), which is the pattern to extend.",
    "SELECTION_OVERLAY_COLOR, rgba(0,120,215,200). Its base #0078d7 is "
    "Windows' accent blue and on no register row, so there is nothing for it "
    "to follow. It is the family test_constant_names.py already forbids as "
    "#0078d4, in the one spelling that guard cannot read -- a question for "
    "the register, not a derivation.",
    "tests/test_register_wiring.py's literal sweep, which still reads only "
    "#rrggbb and #aarrggbb. tests/test_derived_values.py now sweeps every "
    "file for composed literals; widening the older one would be a second "
    "rule for the same fact.",
    "the picker, the mixer and the transformer, which each get their own "
    "round; and the chart's element resolver, which must learn that a "
    "derived value is a call rather than a constant.",
]

GUARD_SOURCE = '"""Derived values: a colour that is a named colour AT AN ALPHA.\n\nA colour here used to be one of two things -- a name, or a literal -- and this\nfile adds the third the application always had and never declared.\nrgba(51, 51, 51, 100) is not a colour beside APP_BORDER; it IS APP_BORDER at\nalpha 100, and until 2026-09-25 nothing related the two. Now it is written\ntranslucent(APP_BORDER, SCROLLBAR_BORDER_ALPHA), and a change to APP_BORDER\nreaches it.\n\nWHY THAT MATTERS HERE, MEASURED. RNV-COLLAPSE-505050 ruled #505050 onto\nGREY_44 on 2026-09-02. IMAGE_MODE_COLORS went on painting the main scrollbar\nhandle with it for three weeks, spelled rgba(80, 80, 80, 100), while the guard\nfor that ruling reported clean. A written-down derivative is orphaned the\nmoment its source moves, and nothing says so.\n\nTHE OVERLAYS WERE THE OTHER HALF OF THE SAME IDEA. IMAGE_OVERLAY_ALPHA was the\nstring "ED" and the two overlays were written out beside it, with a test\nasserting that their digits agreed. Ruled 2026-09-24: derived values are\nDERIVED, not asserted. They compose from it now.\n\nWHAT MOVES A PIXEL: ONE THING, BY RULING. The image-mode scrollbar handle goes\nfrom #505050 at 100 to GREY_44 at 150. Everything else here is the same colour\nat the same alpha, respelled so that it follows its base -- and\ntest_nothing_moved_that_was_not_ruled holds each value to the constant and the\nbyte it is made of.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK,\n                       LIGHT_THEME_COLORS as LIGHT,\n                       IMAGE_MODE_COLORS as IMAGE,\n                       translucent,\n                       translucent_rgba)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / "ui" / "colors.py"\nPALETTES = {"DARK_THEME_COLORS": DARK, "LIGHT_THEME_COLORS": LIGHT,\n            "IMAGE_MODE_COLORS": IMAGE}\nHELPERS = ("translucent", "translucent_rgba")\n\n#: constant -> the byte, and the spelling whose alpha it carries. Each is the\n#: value the literal it replaced already held, except the handle\'s, which was\n#: ruled up from 100.\nALPHAS = {\n    "IMAGE_OVERLAY_ALPHA": (0xED, \'"ED", the image chrome overlays\'),\n    "SCROLLBAR_HANDLE_ALPHA": (0x96, "ruled 2026-09-24; was 100"),\n    "SCROLLBAR_BORDER_ALPHA": (0x64, "rgba(51, 51, 51, 100)"),\n    "SIZE_OVERLAY_ALPHA": (0xC8, "rgba(0, 0, 0, 200)"),\n    "SLOT_IMAGE_ALPHA": (0xAB, "rgba(0, 0, 0, 171)"),\n}\n\n#: What each derived value is made of: the constant its colour comes from, and\n#: its alpha byte. See test_nothing_moved_that_was_not_ruled for why by name.\nMADE_OF = {\n    "APP_WINDOW_OVERLAY": ("TRUE_BLACK", 0xED),\n    "APP_PANEL_OVERLAY": ("BRAND_BLACK", 0xED),\n    "SIZE_OVERLAY_BG": ("TRUE_BLACK", 0xC8),\n    "DEFAULT_SLOT_COLOR_IMAGE": ("TRUE_BLACK", 0xAB),\n    "IMAGE_MODE_COLORS[\'scrollbar_border\']": ("APP_BORDER", 0x64),\n    "IMAGE_MODE_COLORS[\'scrollbar_handle\']": ("GREY_44", 0x96),  # the ruled one\n}\n\n#: The one derived value spelled rgba(), and why. rgba() is valid in a\n#: stylesheet and INVALID in QColor(), so it is the exception and says so.\nRGBA_PINNED = {\n    "SIZE_OVERLAY_BG": \'test_rnv_palette_manager.py asserts "rgba" is in it, \'\n                       \'and that suite is locked\',\n}\n\n_HEX8 = re.compile(r"^#([0-9a-fA-F]{2})([0-9a-fA-F]{6})$")\n_RGBA = re.compile(r"^rgba\\((\\d{1,3}), (\\d{1,3}), (\\d{1,3}), (\\d{1,3})\\)$")\n_COMPOSED = re.compile(r"#[0-9a-fA-F]{8}\\b|\\brgba\\(\\s*\\d{1,3}\\s*,\\s*\\d{1,3}"\n                       r"\\s*,\\s*\\d{1,3}\\s*,\\s*[0-9]*\\.?[0-9]+\\s*\\)")\n\n\ndef decompose(value: str) -> tuple[str, int] | None:\n    """(base \'#rrggbb\', alpha byte) -- taken apart, never rebuilt.\n\n    Independent of translucent() by construction: a bug in the composing\n    function cannot also be a bug here, which is what makes checking one\n    against the other worth anything."""\n    m = _HEX8.match(value)\n    if m:\n        return "#" + m.group(2).lower(), int(m.group(1), 16)\n    m = _RGBA.match(value)\n    if m:\n        r, g, b, a = (int(x) for x in m.groups())\n        return "#%02x%02x%02x" % (r, g, b), a\n    return None\n\n\ndef _derived():\n    """(where, call node, resolved value) for every helper call at module level\n    in ui/colors.py -- a constant, or a value in a module-level dict."""\n    tree = ast.parse(SRC.read_text(encoding="utf-8-sig"))\n    out = []\n    for node in tree.body:\n        if not isinstance(node, (ast.Assign, ast.AnnAssign)):\n            continue\n        target = node.targets[0] if isinstance(node, ast.Assign) else node.target\n        name = getattr(target, "id", None)\n        if name is None or node.value is None:\n            continue\n        if isinstance(node.value, ast.Call):\n            if getattr(node.value.func, "id", None) in HELPERS:\n                out.append((name, node.value, getattr(colors, name)))\n        elif isinstance(node.value, ast.Dict):\n            live = getattr(colors, name)\n            for key, value in zip(node.value.keys, node.value.values):\n                if (isinstance(value, ast.Call)\n                        and getattr(value.func, "id", None) in HELPERS):\n                    out.append((f"{name}[{key.value!r}]", value,\n                                live[key.value]))\n    return out\n\n\ndef _named_colours() -> set[str]:\n    """Every six-digit value this module names -- the bases a composed literal\n    could have been written against."""\n    return {v.lower() for n, v in vars(colors).items()\n            if n.isupper() and isinstance(v, str)\n            and re.fullmatch(r"#[0-9a-fA-F]{6}", v)}\n\n\ndef _parts_of(spelled: str) -> tuple[str, int]:\n    """(base, alpha byte) for any composed spelling _COMPOSED matches, with\n    Qt\'s own reading of a fractional alpha: it TRUNCATES, so 0.3 is 76."""\n    if spelled.startswith("#"):\n        return "#" + spelled[3:].lower(), int(spelled[1:3], 16)\n    numbers = re.findall(r"[0-9]*\\.?[0-9]+", spelled)\n    r, g, b = (int(x) for x in numbers[:3])\n    a = numbers[3]\n    return "#%02x%02x%02x" % (r, g, b), (int(float(a) * 255) if "." in a\n                                         else int(a))\n\n\ndef _bare_strings(tree: ast.AST) -> set[int]:\n    """ids of every string that is a statement on its own -- a docstring, or\n    any other string nobody evaluates. Those are mentions, not uses."""\n    bare = set()\n    for node in ast.walk(tree):\n        body = getattr(node, "body", None)\n        if not isinstance(body, list):\n            continue\n        for statement in body:\n            if (isinstance(statement, ast.Expr)\n                    and isinstance(statement.value, ast.Constant)):\n                bare.add(id(statement.value))\n    return bare\n\n\n# ------------------------------------------------------------ guard the guard\n\ndef test_translucent_composes_alpha_first():\n    """#AARRGGBB, not #RRGGBBAA. Taking the wrong end gives a real colour and\n    the wrong one, which is the failure that does not look like a failure.\n\n    UPPER CASE, unlike rnv-icon-builder\'s helper of the same name: the two\n    overlays this replaced were written that way, and the locked suite checks\n    image window_bg with a case-sensitive startswith(\'#ED\')."""\n    assert translucent("#1a1a1a", 0xED) == "#ED1A1A1A"\n    assert translucent("1A1A1A", 0xED) == "#ED1A1A1A"\n    assert translucent("#d2bc93", 0x33) == "#33D2BC93"\n\n\ndef test_translucent_rgba_is_the_same_colour_in_the_other_spelling():\n    assert translucent_rgba("#1a1a1a", 191) == "rgba(26, 26, 26, 191)"\n    assert translucent_rgba("#000000", 0xC8) == "rgba(0, 0, 0, 200)"\n    for base in ("#1a1a1a", "#d2bc93", "#444444"):\n        for alpha in (0, 0x64, 0xED, 255):\n            assert (decompose(translucent(base, alpha))\n                    == decompose(translucent_rgba(base, alpha))\n                    == (base, alpha))\n\n\ndef test_the_helpers_refuse_what_they_cannot_compose():\n    for helper in (translucent, translucent_rgba):\n        for bad in (-1, 256, 999, 0.5, True):\n            try:\n                helper("#1a1a1a", bad)\n            except (ValueError, TypeError):\n                pass\n            else:\n                raise AssertionError(f"{helper.__name__} took alpha {bad!r}")\n        for bad in ("#1a1a1", "#1a1a1a1a", "nonsense", "#gggggg"):\n            try:\n                helper(bad, 0xED)\n            except ValueError:\n                pass\n            else:\n                raise AssertionError(f"{helper.__name__} took base {bad!r}")\n\n\ndef test_the_alphas_are_the_declared_bytes():\n    for name, (byte, _was) in ALPHAS.items():\n        assert hasattr(colors, name), f"ui.colors has no {name}"\n        value = getattr(colors, name)\n        assert type(value) is int, f"{name} is {value!r}, not an int byte"\n        assert value == byte, f"{name} is {value:#x}, declared {byte:#x}"\n\n\ndef test_the_derivation_sweep_is_looking():\n    """Every check below iterates _derived(). If it came back empty they\n    would all pass over nothing."""\n    where = {w for w, _c, _v in _derived()}\n    assert {"APP_WINDOW_OVERLAY", "APP_PANEL_OVERLAY", "SIZE_OVERLAY_BG",\n            "DEFAULT_SLOT_COLOR_IMAGE",\n            "IMAGE_MODE_COLORS[\'scrollbar_handle\']",\n            "IMAGE_MODE_COLORS[\'scrollbar_border\']"} <= where, sorted(where)\n\n\n# ----------------------------------------------------------- the derivations\n\ndef test_every_derived_value_names_constants_that_exist():\n    """HELPER(BASE, ALPHA) where both are names. A literal in either position\n    is the thing this round removed."""\n    bad = []\n    for where, call, _value in _derived():\n        if len(call.args) != 2 or call.keywords:\n            bad.append(f"{where}: {ast.unparse(call)} is not (BASE, ALPHA)")\n            continue\n        base, alpha = call.args\n        for pos, arg in (("base", base), ("alpha", alpha)):\n            if not isinstance(arg, ast.Name):\n                bad.append(f"{where}: the {pos} is {ast.unparse(arg)}, not a name")\n            elif not hasattr(colors, arg.id):\n                bad.append(f"{where}: the {pos} names {arg.id}, which ui.colors "\n                           f"does not define")\n        if isinstance(base, ast.Name) and hasattr(colors, base.id):\n            if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(getattr(colors, base.id))):\n                bad.append(f"{where}: the base {base.id} is not a six-digit colour")\n        if isinstance(alpha, ast.Name) and alpha.id not in ALPHAS:\n            bad.append(f"{where}: the alpha {alpha.id} is not a declared "\n                       f"composite alpha")\n    assert not bad, "derived values that do not derive:\\n  " + "\\n  ".join(bad)\n\n\ndef test_every_derived_value_decomposes_to_its_base_and_its_alpha():\n    """The relationship, checked by TAKING THE VALUE APART rather than by\n    building it again -- the entry IS the helper\'s output, so recomputing it\n    would compare a call with itself."""\n    wrong = []\n    for where, call, value in _derived():\n        base, alpha = call.args\n        parts = decompose(value)\n        if parts is None:\n            wrong.append(f"{where} is {value!r}, which is neither #AARRGGBB "\n                         f"nor rgba(r, g, b, a)")\n            continue\n        want = (getattr(colors, base.id).lower(), getattr(colors, alpha.id))\n        if parts != want:\n            wrong.append(f"{where} is {value}, which takes apart to "\n                         f"{parts}, not {base.id}/{alpha.id} {want}")\n    assert not wrong, "derived values that do not match:\\n  " + "\\n  ".join(wrong)\n\n\ndef test_the_rgba_spelling_is_used_only_where_the_lock_pins_it():\n    """rgba() is the one derived spelling QColor() cannot read. It is allowed\n    where a locked test demands it and nowhere else -- and the pin is re-read\n    from the locked suite, so an exception outlives nothing."""\n    used = {where for where, call, _v in _derived()\n            if call.func.id == "translucent_rgba"}\n    assert used == set(RGBA_PINNED), (\n        f"translucent_rgba() is used for {sorted(used)}, pinned for "\n        f"{sorted(RGBA_PINNED)}. Anything else takes translucent(), which "\n        f"QColor() can read.")\n    locked = (ROOT / "test_rnv_palette_manager.py").read_text(encoding="utf-8-sig")\n    assert \'assertIn("rgba", SIZE_OVERLAY_BG.lower())\' in locked, (\n        "the locked suite no longer pins SIZE_OVERLAY_BG to rgba(). Move it to "\n        "translucent() and drop it from RGBA_PINNED.")\n\n\ndef test_no_composed_literal_is_left_in_the_application():\n    """The completeness half. Every EVALUATED string in the application\'s own\n    source -- not tests, not docstrings, not this round\'s delivery script --\n    that spells a named colour at an alpha. A literal cannot follow its base.\n\n    Alpha 0 is not a colour and is not counted; a base no constant here names\n    has no row to follow, and is not counted either -- SELECTION_OVERLAY_COLOR\n    is Windows\' accent blue, #0078d7, which is a question for the register and\n    not a derivation this file can check."""\n    named = _named_colours()\n    strays, files = [], 0\n    for path in sorted(ROOT.rglob("*.py")):\n        rel = path.relative_to(ROOT)\n        if any(p in {".git", "tests", "snapshots", "build", "dist", ".venv",\n                     "venv", "__pycache__"} for p in rel.parts):\n            continue\n        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):\n            continue\n        text = path.read_bytes().decode("utf-8-sig", errors="replace")\n        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:\n            continue\n        tree = ast.parse(text)\n        files += 1\n        bare = _bare_strings(tree)\n        for node in ast.walk(tree):\n            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):\n                continue\n            if id(node) in bare:\n                continue\n            for spelled in _COMPOSED.findall(node.value):\n                base, alpha = _parts_of(spelled)\n                if alpha == 0 or base not in named:\n                    continue\n                strays.append(f"{rel}:{node.lineno}  {spelled}  ({base} is "\n                              f"named here)")\n    # 38 application files on 2026-09-25. Thirty is the floor below which the\n    # walk has lost a package, not a file.\n    assert files >= 30, f"only {files} files swept -- the walk has gone blind"\n    assert not strays, ("composed values still written out rather than "\n                        "derived:\\n  " + "\\n  ".join(strays))\n\n\n# --------------------------------------------------- what moved, and what not\n\ndef test_the_scrollbar_handle_is_grey_44_at_150():\n    """RNV-COLLAPSE-505050 and the alpha, both ruled 2026-09-24."""\n    assert decompose(IMAGE["scrollbar_handle"]) == (\n        colors.GREY_44, colors.SCROLLBAR_HANDLE_ALPHA)\n    assert colors.SCROLLBAR_HANDLE_ALPHA == 150\n    assert "505050" not in IMAGE["scrollbar_handle"]\n\n\ndef test_nothing_moved_that_was_not_ruled():\n    """Each derived value, held to what it is MADE OF: the constant its colour\n    comes from and its alpha byte, as of 2026-09-25.\n\n    BY NAME, NOT BY HEX, and that is the point of the round. A register move\n    is meant to pass straight through these values; a test that pinned\n    \'#333333\' would fail the first time one did, and ask a person to edit it\n    by hand -- the exact job derivation exists to remove. What this DOES catch\n    is a value quietly re-made from something else: a different base, or a\n    different byte, which the decomposition check above would accept as long\n    as the source and the value agreed with each other.\n\n    The byte-for-byte before-and-after -- \'#ED000000\', \'#ED1A1A1A\',\n    \'rgba(0, 0, 0, 200)\' -- was checked once, by the delivery script, against\n    the edited module before it was written. That is evidence for the round,\n    not a rule for the repository."""\n    live = {where: value for where, _call, value in _derived()}\n    for where, (base, alpha) in MADE_OF.items():\n        assert where in live, f"{where} is no longer derived"\n        assert decompose(live[where]) == (getattr(colors, base).lower(), alpha), (\n            f"{where} is {live[where]}, which is not {base} at {alpha:#04x}")\n    # the two spellings the locked suite requires, which any respelling keeps\n    assert IMAGE["window_bg"].startswith("#ED")\n    assert "rgba" in colors.SIZE_OVERLAY_BG.lower()\n    assert IMAGE["window_bg"] == IMAGE["scroll_bg"] == colors.APP_WINDOW_OVERLAY\n    assert IMAGE["panel_bg"] == colors.APP_PANEL_OVERLAY\n\n\ndef test_what_qcolor_reads_it_can_read():\n    """window_bg and scroll_bg go through QColor() in the main window. #AARRGGBB\n    is the one derived spelling QColor() parses; rgba() would come back\n    INVALID and paint opaque black."""\n    from PyQt6.QtGui import QColor\n    for value, alpha in ((IMAGE["window_bg"], 0xED), (IMAGE["scroll_bg"], 0xED),\n                         (colors.DEFAULT_SLOT_COLOR_IMAGE, 0xAB)):\n        colour = QColor(value)\n        assert colour.isValid(), f"QColor({value!r}) is invalid"\n        assert colour.alpha() == alpha, f"{value} reads at alpha {colour.alpha()}"\n\n# RNV-DERIVE-ALPHA\n'


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for exactly one occurrence before anything is written."""
    tree.sub('ui/colors.py',
             '    r, g, b = _to_rgb(hex_color)\n    return "#%02x%02x%02x" % tuple(\n        max(0, min(255, c + step)) for c in (r, g, b))\n',
             '    r, g, b = _to_rgb(hex_color)\n    return "#%02x%02x%02x" % tuple(\n        max(0, min(255, c + step)) for c in (r, g, b))\n\n\ndef _hex6(hex_color: str) -> str:\n    """The six hex digits of a colour, or ValueError. Shared by the two\n    helpers below so that they refuse exactly the same inputs."""\n    h = hex_color.lstrip("#")\n    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):\n        raise ValueError(f"{hex_color!r} is not a six-digit hex colour")\n    return h\n\n\ndef _alpha_byte(alpha: int) -> int:\n    """An alpha as the 0-255 byte, or an error. A fraction is refused, not\n    scaled: Qt TRUNCATES a fractional alpha (0.3 is 76, not 77), and a helper\n    that rounded would move a pixel inside a respelling."""\n    if isinstance(alpha, bool) or not isinstance(alpha, int):\n        raise TypeError(f"alpha {alpha!r} is not an int byte")\n    if not 0 <= alpha <= 255:\n        raise ValueError(f"alpha {alpha} is outside 0-255")\n    return alpha\n\n\ndef translucent(hex_color: str, alpha: int) -> str:\n    """A colour at an alpha, as Qt\'s eight-digit #AARRGGBB -- ALPHA FIRST.\n\n    WHY A FUNCTION RATHER THAN A WRITTEN-OUT VALUE. A value computed from\n    another value must be computed in code; a written-down derivative is\n    orphaned the moment its source moves, and nothing says so.\n    RNV-COLLAPSE-505050 is what that cost here: the value was ruled onto\n    GREY_44 on 2026-09-02, and IMAGE_MODE_COLORS went on painting the main\n    scrollbar handle with it for three weeks, written out as rgba(), while\n    the guard for that ruling reported clean.\n\n    WHY #AARRGGBB. It is the one spelling valid both in a stylesheet and in\n    QColor(). QColor() cannot parse rgba(): it returns an INVALID colour, and\n    Qt paints that as opaque black.\n\n    WHY UPPER CASE, when rnv-icon-builder\'s helper of the same name writes\n    lower. The two overlays this replaced were written #ED000000 and\n    #ED1A1A1A, and the locked suite checks image window_bg with a\n    case-sensitive startswith("#ED"). Upper case keeps both byte-identical.\n    Qt reads either. Whether eight-digit hex falls under the register\'s\n    lower-case rule is a question for rnv-brand, which has not ruled on it.\n    """\n    return "#%02X%s" % (_alpha_byte(alpha), _hex6(hex_color).upper())\n\n\ndef translucent_rgba(hex_color: str, alpha: int) -> str:\n    """The same derivation, spelled rgba(r, g, b, a). STYLESHEETS ONLY.\n\n    It exists for one consumer. The locked suite asserts that SIZE_OVERLAY_BG\n    contains "rgba", and that lock stands; everything that reads\n    SIZE_OVERLAY_BG is a stylesheet, where rgba() is valid. QColor() is not\n    -- it reads rgba() as INVALID and paints opaque black -- so translucent()\n    is the default and this is the exception, pinned in\n    tests/test_derived_values.py to the one constant that needs it.\n    """\n    h = _hex6(hex_color)\n    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))\n    return f"rgba({r}, {g}, {b}, {_alpha_byte(alpha)})"\n')
    tree.sub('ui/colors.py',
             'APP_PANEL_HOVER: Final[str] = "#3a3a3a"\n\n# grey(4) on the ink grid. The main button\'s pressed plate (ruled 2026-08-26)\n# and, from 2026-09-02, the scrollbar handle -- RNV-COLLAPSE-505050: this app\n# held #505050 for its handle where the other four already used #444444, and\n# #505050 was on neither the ladder nor the grid. Named here for the first\n# time in this app; rnv-text-transformer already calls it GREY_44.\nGREY_44: Final[str] = "#444444"\n"""engine/brand.py APP["panel-hover"]. The n=+2 rung of the dark surface\nladder, and the dark interaction plate.\n\nREGISTERED 2026-08-29 in rnv-brand rev 22, app-owned here until then.\n\n    BRAND_BLACK + n * 0x10,  n in -1..+2\n    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover\n\nThe register had called the ladder "two-thirds specified" because APP_BORDER\n#333333 is not #3a3a3a and so looked like a missing rung. It is not a rung at\nall: #333333 is grey(3) on the INK grid, which governs inks and EDGES, and a\nborder is an edge. The ladder was complete when the question was first asked.\n"""\n',
             'APP_PANEL_HOVER: Final[str] = "#3a3a3a"\n"""engine/brand.py APP["panel-hover"]. The n=+2 rung of the dark surface\nladder, and the dark interaction plate.\n\nREGISTERED 2026-08-29 in rnv-brand rev 22, app-owned here until then.\n\n    BRAND_BLACK + n * 0x10,  n in -1..+2\n    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover\n\nThe register had called the ladder "two-thirds specified" because APP_BORDER\n#333333 is not #3a3a3a and so looked like a missing rung. It is not a rung at\nall: #333333 is grey(3) on the INK grid, which governs inks and EDGES, and a\nborder is an edge. The ladder was complete when the question was first asked.\n"""\n\n# grey(4) on the ink grid. The main button\'s pressed plate (ruled 2026-08-26)\n# and the scrollbar handle -- RNV-COLLAPSE-505050, ruled 2026-09-02: #505050\n# was on neither the ladder nor the grid. Named here for the first time in\n# this app; rnv-text-transformer already calls it GREY_44.\n#\n# CORRECTED 2026-09-25, AND MOVED. This said the other four applications\n# "already used #444444" for the handle. In dark mode three did, and the\n# mixer used #333333. In image mode none did: all four still painted #505050,\n# spelled rgba(), on the main surface -- the mixer in IMAGE_STYLESHEET,\n# beside the #333333 its palette gives dialogs -- and so did this\n# application\'s own image scrollbar_handle, until this date. The comment also\n# sat between APP_PANEL_HOVER and that constant\'s docstring, so the text\n# describing the panel-hover rung read as GREY_44\'s.\nGREY_44: Final[str] = "#444444"\n"""grey(4) on the ink grid. The pressed plate, and the scrollbar handle in\nevery mode -- in image mode at SCROLLBAR_HANDLE_ALPHA."""\n')
    tree.sub('ui/colors.py',
             'IMAGE_OVERLAY_ALPHA: Final[str] = "ED"\n"""The alpha byte image mode composites its chrome at -- 0xED, about 93%.\n\nWHY THE OVERLAYS BELOW ARE WRITTEN OUT RATHER THAN COMPOSED. Qt wants the\neight-digit #AARRGGBB form, and building it from the six-digit constant would\nmake the palette entries resolve to an expression rather than a value, which\nthis app\'s own before/after comparison cannot check. The relationship is\nasserted in tests/test_ladder_and_plate.py instead: each overlay\'s last six\ndigits must BE the register value it claims, and its alpha byte must be this\none. If the register moves a base, those tests fail and these move with it.\n\nTHEY WERE INVISIBLE BEFORE. The 2026-08-29 wiring pass claimed no registered\nvalue was left spelled as a literal in a dark palette. That was true of\nsix-digit spellings only: its sweep compared whole strings, so #ED000000 never\nmatched #000000, and three of these sat in IMAGE_MODE_COLORS -- which is a DARK\ndict here -- while the test reported clean.\n"""\n\nAPP_WINDOW_OVERLAY: Final[str] = "#ED000000"\n"""TRUE_BLACK, and APP["window"], at IMAGE_OVERLAY_ALPHA."""\n\nAPP_PANEL_OVERLAY: Final[str] = "#ED1A1A1A"\n"""BRAND_BLACK, and APP["panel"], at IMAGE_OVERLAY_ALPHA."""\n',
             '# ==================== Composite alphas ====================\n# A composite is a named colour AT AN ALPHA: translucent(BASE, ALPHA). The\n# colour half is a name, so a register move reaches it; the alpha half is one\n# of these, so that same move carries every alpha form of the colour with it.\n# Each byte is the one the literal it replaced already held, except the\n# scrollbar handle\'s, which was ruled.\n\nIMAGE_OVERLAY_ALPHA: Final[int] = 0xED\n"""237, about 93%. The alpha image mode composites its chrome at.\n\nWAS THE STRING "ED", AND THE OVERLAYS BELOW WERE WRITTEN OUT. The reason\ngiven was that composing them would make the palette entries resolve to an\nexpression rather than a value, which this app\'s own before/after comparison\ncould not check -- so tests/test_ladder_and_plate.py asserted the\nrelationship instead, and a register move would have failed that test and\nwaited for someone to edit two strings by hand.\n\nRULED 2026-09-24 by Chris: derived values are DERIVED, not asserted. The\npalettes still resolve to plain strings at import, so every comparison of\nvalues still compares values. What changed is that a register move now\nreaches the overlays on its own. The ladder test keeps its check, taking each\noverlay apart rather than trusting the call that built it.\n\nTHEY WERE INVISIBLE BEFORE. The 2026-08-29 wiring pass claimed no registered\nvalue was left spelled as a literal in a dark palette. That was true of\nsix-digit spellings only: its sweep compared whole strings, so #ED000000 never\nmatched #000000, and three of these sat in IMAGE_MODE_COLORS -- which is a DARK\ndict here -- while the test reported clean.\n"""\n\nSCROLLBAR_HANDLE_ALPHA: Final[int] = 0x96\n"""150. The image-mode scrollbar handle. It was 100 here and 150 in all four\nother applications, and nothing recorded why. Ruled 2026-09-24: 150\nfleet-wide, moving with the handle\'s colour."""\n\nSCROLLBAR_BORDER_ALPHA: Final[int] = 0x64\n"""100. The image-mode scrollbar edge -- the byte it already had."""\n\nSIZE_OVERLAY_ALPHA: Final[int] = 0xC8\n"""200. The floating size and status readout -- the byte it already had."""\n\nSLOT_IMAGE_ALPHA: Final[int] = 0xAB\n"""171. A new slot\'s default fill in image mode -- the byte it already had.\n\nDEFAULT_SLOT_COLOR_IMAGE_RGB spells the same colour as an integer tuple and is\nNOT derived yet. Tuples are a notation of their own, measured across the fleet\non 2026-09-25, and they get a round of their own."""\n\nAPP_WINDOW_OVERLAY: Final[str] = translucent(TRUE_BLACK, IMAGE_OVERLAY_ALPHA)\n"""TRUE_BLACK, and APP["window"], at IMAGE_OVERLAY_ALPHA."""\n\nAPP_PANEL_OVERLAY: Final[str] = translucent(BRAND_BLACK, IMAGE_OVERLAY_ALPHA)\n"""BRAND_BLACK, and APP["panel"], at IMAGE_OVERLAY_ALPHA."""\n')
    tree.sub('ui/colors.py',
             'SIZE_OVERLAY_BG: Final[str] = "rgba(0, 0, 0, 200)"\n"""Background for the floating size/status overlay widget."""\n',
             'SIZE_OVERLAY_BG: Final[str] = translucent_rgba(TRUE_BLACK, SIZE_OVERLAY_ALPHA)\n"""Background for the floating size/status overlay widget. TRUE_BLACK at\nSIZE_OVERLAY_ALPHA, spelled rgba() because the locked suite pins that\nspelling -- every consumer is a stylesheet, where it is valid."""\n')
    tree.sub('ui/colors.py',
             'DEFAULT_SLOT_COLOR_IMAGE: Final[str] = "rgba(0, 0, 0, 171)"\n"""Default color for new color slots in Image mode (semi-transparent black)."""\n',
             'DEFAULT_SLOT_COLOR_IMAGE: Final[str] = translucent(TRUE_BLACK, SLOT_IMAGE_ALPHA)\n"""Default color for new color slots in Image mode (semi-transparent black).\nTRUE_BLACK at SLOT_IMAGE_ALPHA: the colour it always was, in the one\nspelling QColor() can read as well as a stylesheet."""\n')
    tree.sub('ui/colors.py',
             "    # Scrollbar -- uses rgba in CSS strings, not here\n    'scrollbar_bg': 'transparent',\n    'scrollbar_handle': 'rgba(80, 80, 80, 100)',\n    'scrollbar_handle_hover': BRAND_GOLD,\n    'scrollbar_border': 'rgba(51, 51, 51, 100)',\n",
             "    # Scrollbar. The two composites are DERIVED -- a named colour at a\n    # declared alpha -- so a register move reaches them.\n    'scrollbar_bg': 'transparent',\n    # RNV-COLLAPSE-505050, closed in this palette 2026-09-25. This read\n    # rgba(80, 80, 80, 100) -- the retired value at alpha 100 -- three\n    # weeks after the ruling, while tests/test_collapse_505050.py\n    # reported it gone: nothing here decoded rgba(). The alpha moves\n    # to 150 with it, the byte the other four image scrollbars use.\n    'scrollbar_handle': translucent(GREY_44, SCROLLBAR_HANDLE_ALPHA),\n    'scrollbar_handle_hover': BRAND_GOLD,\n    'scrollbar_border': translucent(APP_BORDER, SCROLLBAR_BORDER_ALPHA),\n")
    tree.sub('ui/colors.py',
             '    # Functions\n    "get_theme_colors",\n',
             '    # Functions\n    "translucent",\n    "translucent_rgba",\n    "get_theme_colors",\n')
    tree.sub('tests/test_ladder_and_plate.py',
             '    """The overlays are written out because Qt wants eight digits and composing\n    them would make the palette resolve to an expression. This is the\n    relationship composition would have given, asserted instead."""\n    for name, (base_name, _key) in OVERLAYS.items():\n        overlay = getattr(colors, name)\n        base = getattr(colors, base_name)\n        assert len(overlay) == 9, f\'{name} is {overlay}, not #AARRGGBB\'\n        assert overlay[1:3].upper() == colors.IMAGE_OVERLAY_ALPHA.upper(), (\n',
             '    """The overlays are COMPOSED now -- translucent(BASE, IMAGE_OVERLAY_ALPHA),\n    ruled 2026-09-24 -- and this still takes each one apart rather than\n    building it again, so a bug in the composing function fails here. Until\n    that date they were written out, and this was the only thing relating\n    them to their bases."""\n    for name, (base_name, _key) in OVERLAYS.items():\n        overlay = getattr(colors, name)\n        base = getattr(colors, base_name)\n        assert len(overlay) == 9, f\'{name} is {overlay}, not #AARRGGBB\'\n        assert int(overlay[1:3], 16) == colors.IMAGE_OVERLAY_ALPHA, (\n')
    tree.sub('tests/test_collapse_505050.py',
             '"""#505050 no longer exists in this application. RNV-COLLAPSE-GUARD\n\nRuled 2026-09-02: #505050 collapses onto GREY_44 #444444. The value was on\nneither the surface ladder nor the ink grid, and its neighbours were not a\nvisible step away. This guard pins the ruling in both directions: the keys\nhold the new value, and they hold it THROUGH the constant.\n"""\nfrom __future__ import annotations\n\nimport re\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parent.parent\nOLD_HEX = "#505050"\nNEW_HEX = "#444444"\nCONST = "GREY_44"\nKEYS = [\'scroll_handle\', \'scrollbar_handle\']\nEXPECT = {\'dark\': [\'scroll_handle\', \'scrollbar_handle\'], \'image\': [\'scroll_handle\']}\nPALETTE_FILE = "ui/colors.py"\n\n\ndef _palettes():\n    from ui.colors import DARK_THEME_COLORS as D, IMAGE_MODE_COLORS as I, LIGHT_THEME_COLORS as L; P={\'dark\':D,\'image\':I,\'light\':L}\n    return P\n\n\ndef test_the_ruled_keys_hold_the_new_value():\n    for mode, keys in EXPECT.items():\n        palette = _palettes()[mode]\n        for key in keys:\n            assert palette[key] == NEW_HEX, (\n                f"{mode}[{key}] is {palette[key]}, ruled onto {NEW_HEX}")\n\n\ndef test_the_old_value_is_gone_from_every_palette():\n    for mode, palette in _palettes().items():\n        holders = [k for k, v in palette.items() if str(v).lower() == OLD_HEX]\n        assert not holders, f"{mode} still holds {OLD_HEX} under {holders}"\n\n\ndef test_the_keys_are_wired_through_the_constant_not_rewritten():\n    """Swapping one literal for another passes the value check and defeats\n    the point. The constant is what a later substitution changes."""\n    src = (ROOT / PALETTE_FILE).read_text(encoding="utf-8-sig")\n    for key in KEYS:\n        assert re.search(r"\'%s\':\\s+%s\\b" % (key, CONST), src), (\n            f"{key} is not written as {CONST} in {PALETTE_FILE}")\n\n\ndef test_the_old_value_is_not_written_anywhere_in_source():\n    """A sweep for the literal AS A STRING -- quoted. The palette file records\n    "was #505050" in a comment beside each ruled key, and that mention is the\n    provenance, not a use. The first version of this test matched the bare\n    text and failed on its own script\'s comment: use versus mention, again.\n    Excludes this guard and the delivery script, which quote the value in\n    order to forbid it."""\n    strays = []\n    for path in sorted(ROOT.rglob("*.py")):\n        if any(p in {".git", "build", "dist", ".venv", "__pycache__"} for p in path.parts):\n            continue\n        text = path.read_text(encoding="utf-8-sig", errors="replace")\n        if "RNV-COLLAPSE-GUARD" in text or "RNV-COLLAPSE-TOOL-DO-NOT-SWEEP" in text:\n            continue\n        if re.search(r"""[\'"]%s[\'"]""" % OLD_HEX, text, re.I):\n            strays.append(str(path.relative_to(ROOT)))\n    assert not strays, f"{OLD_HEX} is still written as a literal in: {strays}"\n',
             '"""#505050 is gone from every string in this application. RNV-COLLAPSE-GUARD\n\nRuled 2026-09-02: #505050 collapses onto GREY_44 #444444. The value was on\nneither the surface ladder nor the ink grid, and its neighbours were not a\nvisible step away. This guard pins the ruling in both directions: the keys\nhold the new value, and they hold it THROUGH the constant.\n\nWHAT THIS GUARD USED TO SAY, AND WHY IT WAS WRONG. Until 2026-09-25 its first\nline read "#505050 no longer exists in this application", and it passed while\nIMAGE_MODE_COLORS[\'scrollbar_handle\'] read \'rgba(80, 80, 80, 100)\' -- #505050\nat alpha 100, painting the main scrollbar in image mode. Three blind spots\nlined up:\n\n  - EXPECT listed image mode\'s scroll_handle and not its scrollbar_handle;\n  - the palette sweep compared whole strings with \'#505050\';\n  - the source sweep looked for that string, quoted.\n\nNone of the three decoded rgba(), and rgba() was the only spelling the value\nhad left. Every check below decodes: #rgb, #rrggbb, #aarrggbb, rgb() and\nrgba() all read as the colour they are.\n\nWHAT IT STILL CANNOT CLEAR, STATED RATHER THAN HIDDEN. Two constants hold the\nvalue as an INTEGER TUPLE, which no string sweep reads at all:\n\n    SLOT_BORDER_THIN_COLOR   (80, 80, 80)   core/color_slot.py, the thin slot pen\n    HISTORY_SWATCH_BORDER    (80, 80, 80)   utils/color_history.py, the swatch pen\n\nWhether a slot border is the same decision as a scrollbar handle is a ruling,\nnot a sweep -- the thin and thick slot borders are told apart partly by\ncolour, and a collapse must not erase a distinction nobody was asked about.\nSo they are pinned as the KNOWN set: a third appearing fails, and collapsing\neither fails until PENDING_RULING is updated in the same commit.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport re\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parent.parent\nOLD_HEX = "#505050"\nNEW_HEX = "#444444"\nCONST = "GREY_44"\nEXPECT = {\'dark\': [\'scroll_handle\', \'scrollbar_handle\'],\n          \'image\': [\'scroll_handle\', \'scrollbar_handle\']}\nPALETTE_FILE = "ui/colors.py"\nDICT_NAMES = {\'dark\': \'DARK_THEME_COLORS\', \'image\': \'IMAGE_MODE_COLORS\',\n              \'light\': \'LIGHT_THEME_COLORS\'}\n\n#: The integer spellings of the value that await a ruling, by the name each is\n#: assigned to. Not an exemption: the sweep below must find EXACTLY these, so\n#: a new one fails, and a ruled one fails until this is updated.\nPENDING_RULING = {\n    ("ui/colors.py", "SLOT_BORDER_THIN_COLOR"),\n    ("ui/colors.py", "HISTORY_SWATCH_BORDER"),\n}\n\n#: Files that name the value in order to forbid it. The last is the fleet\'s\n#: delivery marker: a delivery script quotes what it retires.\nSKIP_MARKERS = ("RNV-COLLAPSE-GUARD", "RNV-COLLAPSE-TOOL-DO-NOT-SWEEP",\n                "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP")\nSKIP_DIRS = {".git", "build", "dist", ".venv", "venv", "__pycache__"}\n\n_HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\\b")\n_FUNC = re.compile(r"\\brgba?\\(\\s*(\\d{1,3})\\s*,\\s*(\\d{1,3})\\s*,\\s*(\\d{1,3})"\n                   r"\\s*(?:,\\s*[0-9]*\\.?[0-9]+\\s*)?\\)")\n\n\ndef colours_in(text: str) -> set[str]:\n    """Every colour written in `text`, normalised to #rrggbb.\n\n    #AARRGGBB is Qt\'s order, ALPHA FIRST: the colour is the LAST six digits.\n    Taking the first six turns #96444444 into #964444 -- a real colour and the\n    wrong one, which is the failure that does not look like a failure."""\n    found = set()\n    for m in _HEX.finditer(text):\n        h = m.group(0)[1:].lower()\n        if len(h) == 8:\n            h = h[2:]\n        elif len(h) == 3:\n            h = "".join(c * 2 for c in h)\n        found.add("#" + h)\n    for m in _FUNC.finditer(text):\n        channels = [int(g) for g in m.groups()]\n        if all(c <= 255 for c in channels):\n            found.add("#%02x%02x%02x" % tuple(channels))\n    return found\n\n\ndef _palettes():\n    from ui.colors import (DARK_THEME_COLORS, IMAGE_MODE_COLORS,\n                           LIGHT_THEME_COLORS)\n    return {\'dark\': DARK_THEME_COLORS, \'image\': IMAGE_MODE_COLORS,\n            \'light\': LIGHT_THEME_COLORS}\n\n\ndef _dict_nodes():\n    tree = ast.parse((ROOT / PALETTE_FILE).read_text(encoding="utf-8-sig"))\n    out = {}\n    for node in ast.walk(tree):\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            target = node.targets[0] if isinstance(node, ast.Assign) else node.target\n            if (getattr(target, "id", None) in DICT_NAMES.values()\n                    and isinstance(node.value, ast.Dict)):\n                out[target.id] = node.value\n    return out\n\n\ndef _sources():\n    for path in sorted(ROOT.rglob("*.py")):\n        if any(p in SKIP_DIRS for p in path.parts):\n            continue\n        if path.parent == ROOT and path.name.startswith("up"):\n            continue\n        text = path.read_bytes().decode("utf-8-sig", errors="replace")\n        if any(m in text for m in SKIP_MARKERS):\n            continue\n        yield path, text\n\n\ndef _string_uses(tree: ast.AST):\n    """String constants that are EVALUATED -- not docstrings, and not any\n    other bare string statement. A comment is not a string at all.\n\n    Use versus mention: the notes beside each ruled key say "was #505050",\n    and that is the record of the ruling, not a use of the value."""\n    bare = set()\n    for node in ast.walk(tree):\n        body = getattr(node, "body", None)\n        if not isinstance(body, list):\n            continue\n        for statement in body:\n            if (isinstance(statement, ast.Expr)\n                    and isinstance(statement.value, ast.Constant)):\n                bare.add(id(statement.value))\n    for node in ast.walk(tree):\n        if (isinstance(node, ast.Constant) and isinstance(node.value, str)\n                and id(node) not in bare):\n            yield node\n\n\ndef _int_spellings(tree: ast.AST, rgb: tuple[int, int, int]):\n    """(assigned name or \'\', line) for every tuple, and every QColor, QPen or\n    QBrush call, that spells `rgb` in integers -- the notation no string sweep\n    can see."""\n    parents = {}\n    for node in ast.walk(tree):\n        for child in ast.iter_child_nodes(node):\n            parents[id(child)] = node\n    for node in ast.walk(tree):\n        values = None\n        if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) in (3, 4):\n            values = node.elts\n        elif isinstance(node, ast.Call) and len(node.args) >= 3:\n            fname = (getattr(node.func, "id", None)\n                     or getattr(node.func, "attr", None))\n            if fname in ("QColor", "fromRgb", "QPen", "QBrush"):\n                values = node.args\n        if not values:\n            continue\n        ints = tuple(v.value for v in values[:3]\n                     if isinstance(v, ast.Constant) and type(v.value) is int)\n        if ints != rgb:\n            continue\n        up = parents.get(id(node))\n        name = ""\n        if isinstance(up, (ast.Assign, ast.AnnAssign)):\n            target = up.targets[0] if isinstance(up, ast.Assign) else up.target\n            name = getattr(target, "id", "") or getattr(target, "attr", "")\n        yield name, node.lineno\n\n\n# ------------------------------------------------------------ guard the guard\n\ndef test_the_decoder_reads_every_spelling_the_value_can_wear():\n    """If this fails, every negative check below is blind in the way the first\n    version of this file was."""\n    for spelling in ("#505050", "#96505050", "#FF505050",\n                     "rgba(80, 80, 80, 100)", "rgba(80,80,80,0.6)",\n                     "rgb(80, 80, 80)"):\n        assert OLD_HEX in colours_in(f"background: {spelling};"), spelling\n    assert colours_in("#555") == {"#555555"}\n    # and it does not read colours that are not there, or the wrong end\n    assert colours_in("#96444444") == {NEW_HEX}\n    assert colours_in("translate(80, 80, 80)") == set()\n    assert colours_in("#12345") == set()\n\n\ndef test_the_integer_sweep_reads_both_notations():\n    probe = ast.parse("A = (80, 80, 80)\\n"\n                      "pen.setColor(QColor(80, 80, 80, 150))\\n"\n                      "C = (80, 80, 81)\\n")\n    assert sorted(n for n, _ in _int_spellings(probe, (80, 80, 80))) == ["", "A"]\n\n\n# ------------------------------------------------------------------ the ruling\n\ndef test_the_ruled_keys_hold_the_new_value():\n    """Decoded, so a derived entry -- GREY_44 at an alpha -- reads as the\n    colour it is, not as a string that fails to equal \'#444444\'."""\n    for mode, keys in EXPECT.items():\n        palette = _palettes()[mode]\n        for key in keys:\n            assert colours_in(palette[key]) == {NEW_HEX}, (\n                f"{mode}[{key}] is {palette[key]}, ruled onto {NEW_HEX}")\n\n\ndef test_the_keys_are_wired_through_the_constant_not_rewritten():\n    """Swapping one literal for another passes the value check and defeats\n    the point. The constant is what a later substitution changes -- named\n    directly, or as the base of a derived value."""\n    nodes = _dict_nodes()\n    for mode, keys in EXPECT.items():\n        node = nodes[DICT_NAMES[mode]]\n        entries = {k.value: v for k, v in zip(node.keys, node.values)\n                   if isinstance(k, ast.Constant)}\n        for key in keys:\n            value = entries.get(key)\n            assert value is not None, f"{mode} has no {key}"\n            if isinstance(value, ast.Call):\n                assert getattr(value.func, "id", None) == "translucent", (\n                    f"{mode}[{key}] is computed by something other than "\n                    f"translucent(): {ast.unparse(value)}")\n                value = value.args[0]\n            assert isinstance(value, ast.Name) and value.id == CONST, (\n                f"{mode}[{key}] is {ast.unparse(value)}, not written through "\n                f"{CONST}")\n\n\ndef test_the_old_value_is_gone_from_every_palette():\n    looked, holders = 0, []\n    for mode, palette in _palettes().items():\n        for key, value in palette.items():\n            if not isinstance(value, str):\n                continue\n            looked += 1\n            if OLD_HEX in colours_in(value):\n                holders.append(f"{mode}[{key}] = {value}")\n    assert looked >= 100, f"only {looked} palette entries seen -- the sweep is blind"\n    assert not holders, f"{OLD_HEX} is still painted, in some spelling: {holders}"\n\n\ndef test_the_old_value_is_not_written_anywhere_in_source():\n    """Every evaluated string in every Python file, decoded. Skips this guard\n    and anything carrying a delivery marker, which name the value in order to\n    forbid it."""\n    strays, files = [], 0\n    for path, text in _sources():\n        try:\n            tree = ast.parse(text)\n        except SyntaxError:\n            strays.append(f"{path.relative_to(ROOT)}: does not parse, so it "\n                          f"cannot be swept")\n            continue\n        files += 1\n        for node in _string_uses(tree):\n            if OLD_HEX in colours_in(node.value):\n                strays.append(f"{path.relative_to(ROOT)}:{node.lineno}")\n    assert files >= 40, f"only {files} files swept -- the walk has gone blind"\n    assert not strays, f"{OLD_HEX} is still written as a colour in: {strays}"\n\n\ndef test_the_integer_spellings_are_exactly_the_ones_awaiting_a_ruling():\n    """The notation the string sweeps cannot see. Found 2026-09-25 by a census\n    of integer tuples, after this guard had reported the value gone for three\n    weeks."""\n    found = set()\n    for path, text in _sources():\n        try:\n            tree = ast.parse(text)\n        except SyntaxError:\n            continue\n        rel = path.relative_to(ROOT).as_posix()\n        for name, line in _int_spellings(tree, (80, 80, 80)):\n            found.add((rel, name or f"<unnamed, line {line}>"))\n    assert found == PENDING_RULING, (\n        f"the integer spellings of {OLD_HEX} are not the known set.\\n"\n        f"  new, not ruled on:   {sorted(found - PENDING_RULING)}\\n"\n        f"  gone from the code:  {sorted(PENDING_RULING - found)}\\n"\n        f"A new one is a survivor. A gone one was ruled on: update "\n        f"PENDING_RULING in the same commit.")\n')
    tree.sub('tests/conftest.py',
             '# RNV-GOLD-HOVER, 2026-09-12 -- every hover on the main surface takes the\n',
             '# RNV-DERIVE-ALPHA, 2026-09-25 -- every colour this application writes\n# at an alpha is DERIVED, translucent(BASE, ALPHA), so a change to a base\n# reaches every alpha form of it. The image-mode scrollbar handle left\n# #505050 at 100 for GREY_44 at 150, by ruling. tests/test_derived_values.py\n# holds the derivations; tests/test_collapse_505050.py now decodes every\n# spelling, and names the two integer tuples still awaiting a ruling.\n# RNV-GOLD-HOVER, 2026-09-12 -- every hover on the main surface takes the\n')


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""
    src = tree.read('ui/colors.py')

    # it parses, and the palettes are still dict literals
    module = ast.parse(src)
    dicts, derived = {}, []
    for node in module.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        t = node.targets[0] if isinstance(node, ast.Assign) else node.target
        name = getattr(t, 'id', None)
        if isinstance(node.value, ast.Dict):
            dicts[name] = node.value
            for k, v in zip(node.value.keys, node.value.values):
                if isinstance(v, ast.Call) and getattr(v.func, 'id', None) in (
                        'translucent', 'translucent_rgba'):
                    derived.append(f'{name}[{k.value!r}]')
        elif isinstance(node.value, ast.Call) and getattr(
                node.value.func, 'id', None) in ('translucent', 'translucent_rgba'):
            derived.append(name)
    for name in ('DARK_THEME_COLORS', 'LIGHT_THEME_COLORS', 'IMAGE_MODE_COLORS'):
        assert name in dicts, f'{name} is no longer a dict literal'
    assert sorted(derived) == sorted([
        'APP_WINDOW_OVERLAY', 'APP_PANEL_OVERLAY', 'SIZE_OVERLAY_BG',
        'DEFAULT_SLOT_COLOR_IMAGE', "IMAGE_MODE_COLORS['scrollbar_handle']",
        "IMAGE_MODE_COLORS['scrollbar_border']"]), f'derived: {derived}'

    # no composed literal left in any palette
    for name, node in dicts.items():
        for k, v in zip(node.keys, node.values):
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                assert 'rgba(' not in v.value, f'{name}[{k.value!r}] = {v.value}'

    # THE VALUES, EVALUATED. ui/colors.py imports nothing but typing, so the
    # edited module can be run here and every claim checked on what it
    # produces rather than on how it is spelled.
    ns = {}
    exec(compile(src, 'ui/colors.py (edited, in memory)', 'exec'), ns)
    assert ns['APP_WINDOW_OVERLAY'] == '#ED000000', ns['APP_WINDOW_OVERLAY']
    assert ns['APP_PANEL_OVERLAY'] == '#ED1A1A1A', ns['APP_PANEL_OVERLAY']
    assert ns['SIZE_OVERLAY_BG'] == 'rgba(0, 0, 0, 200)', ns['SIZE_OVERLAY_BG']
    assert ns['DEFAULT_SLOT_COLOR_IMAGE'] == '#AB000000'
    image = ns['IMAGE_MODE_COLORS']
    assert image['scrollbar_border'] == '#64333333', image['scrollbar_border']
    assert image['scrollbar_handle'] == '#96444444', image['scrollbar_handle']
    assert image['window_bg'].startswith('#ED'), 'the locked suite checks this'
    assert 'rgba' in ns['SIZE_OVERLAY_BG'].lower(), 'the locked suite checks this'
    assert type(ns['IMAGE_OVERLAY_ALPHA']) is int

    # GREY_44's docstring is its own again, and panel-hover has its text back
    doc_after = {}
    for a, b in zip(module.body, module.body[1:]):
        if (isinstance(a, ast.AnnAssign) and isinstance(b, ast.Expr)
                and isinstance(b.value, ast.Constant)):
            doc_after[a.target.id] = b.value.value
    assert doc_after['APP_PANEL_HOVER'].startswith('engine/brand.py APP["panel-hover"]')
    assert doc_after['GREY_44'].startswith('grey(4) on the ink grid')

    # the guards this round rewrites say what they now do
    collapse = tree.read('tests/test_collapse_505050.py')
    assert 'PENDING_RULING' in collapse and 'RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP' in collapse
    assert "EXPECT = {'dark': ['scroll_handle', 'scrollbar_handle'],\n          'image': ['scroll_handle', 'scrollbar_handle']}" in collapse
    ladder = tree.read('tests/test_ladder_and_plate.py')
    assert 'IMAGE_OVERLAY_ALPHA.upper()' not in ladder
# ------------------------------------------------------------------ plumbing
#
# EXIT CODES ARE A TAXONOMY, NOT A BOOLEAN. Rev 6 §3.0.1. A harness that
# returns non-zero for everything tells the operator something is wrong and
# nothing about what, and the three non-zero cases want three different
# actions: read the diff, install something, re-run.
EXIT_CLEAN = 0       # everything agreed
EXIT_DISAGREES = 1   # something ran and disagreed -- read it
EXIT_CANNOT_RUN = 2  # the environment is not ready -- nothing was asked
EXIT_INCOMPLETE = 3  # it ran and did not finish -- re-run before believing it


class Stop(SystemExit):
    """A refusal this script chose, as opposed to a crash.

    Carries an exit code from the taxonomy. Bare SystemExit('message') exits 1,
    which says A TEST DISAGREED -- so every refusal used to arrive wearing the
    one verdict it was not.
    """

    def __init__(self, message: str, code: int = EXIT_CANNOT_RUN) -> None:
        super().__init__(message)
        self.code = code


#: Two files per repository that exist there and in none of the others.
#: Verified against the live fleet by _fingerprint_check.py at build time,
#: because a fingerprint that has been renamed away identifies nothing and
#: would refuse every correct checkout.
FINGERPRINTS = {
    "rnv-color-mixer": ("core/image_handler.py", "ui/canvas_view.py"),
    "rnv-color-palette-manager": ("core/color_extractor.py",
                                  "ui/batch_export_dialog.py"),
    "rnv-color-picker": ("core/hilbert_curve.py", "ui/color_swatch_widget.py"),
    "rnv-icon-builder": ("core/icon_builder_core.py", "core/project_manager.py"),
    "rnv-text-transformer": ("core/diff_engine.py", "core/text_cleaner.py"),
}


def refuse_wrong_repository(root) -> None:
    """Refuse a checkout that is not the repository this script was built for.

    CALLED FIRST IN apply(), BEFORE THE SENTINEL AND BEFORE ANY ANCHOR, and the
    order is the whole point. The five applications share file names -- four of
    them have a utils/config.py or a ui/colors.py, and several share a
    tests/conftest.py. Run in the wrong sibling, a sentinel check says "already
    applied" or "not a checkout" and an anchor check says "the file moved",
    and BOTH of those are the script guessing at the wrong question.

    A fingerprint is a file only the right repository has. Two, because one
    that gets renamed takes the check with it.
    """
    want = FINGERPRINTS.get(REPO)
    if not want:
        return
    missing = [f for f in want if not (root / f).exists()]
    if missing:
        raise Stop(
            f"this is not a {REPO} checkout.\n"
            f"  expected to find: {', '.join(want)}\n"
            f"  missing here:     {', '.join(missing)}\n"
            f"Run it from the root of {REPO}. Nothing was read or written.",
            EXIT_CANNOT_RUN)


def _left_alone() -> None:
    """Print what this round deliberately did not touch.

    LEFT_ALONE is optional and is prose, not a guard. It exists because a
    reader of a diff can see what changed and cannot see what was considered
    and declined, and the second is where a round's scope actually lives.
    """
    items = globals().get("LEFT_ALONE")
    if not items:
        return
    print("\nleft alone, deliberately:")
    for line in items:
        print(f"  - {line}")


def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        raise Stop(f"refusing to run as {name} -- it would shadow a module on "
                   f"sys.path. Rename to up.py and run again.", EXIT_CANNOT_RUN)


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}
        self.deleted: set[str] = set()
        #: rel -> (had a BOM, line endings were CRLF throughout). What a file
        #: was on disk, so flush() can put back exactly that around the edit.
        self.form: dict[str, tuple[bool, bool]] = {}

    def read(self, rel: str) -> str:
        """The file as text with LF line endings, whatever it is on disk.

        A FILE IS ITS BYTES, AND AN EDIT MUST NOT CHANGE THE ONES IT DID NOT
        MEAN TO. This used to read with read_text('utf-8-sig') and flush with
        encode('utf-8'). The first strips a byte-order mark and folds CRLF to
        LF; the second puts neither back. So a one-line edit to a CRLF file
        rewrote every line ending in it, and any edit to a file with a BOM
        deleted its first three bytes. rnv-color-picker's utils/config.py --
        the picker's palette -- carries a BOM, so its next round would have.

        Anchors are written with \\n, so a CRLF file is held as LF in memory
        and its endings are restored on write. A file that MIXES endings is
        held exactly as it is: anchors then match only its LF lines, and
        everything else round-trips untouched.
        """
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise Stop(f"missing file: {rel}", EXIT_CANNOT_RUN)
            raw = p.read_bytes()
            bom = raw.startswith(b"\xef\xbb\xbf")
            text = (raw[3:] if bom else raw).decode("utf-8")
            crlf = text.count("\r\n")
            all_crlf = crlf > 0 and crlf == text.count("\n")
            if all_crlf:
                text = text.replace("\r\n", "\n")
            self.files[rel] = text
            self.form[rel] = (bom, all_crlf)
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def delete(self, rel: str) -> None:
        """Mark a file for removal. Nothing leaves disk until flush()."""
        if not (self.root / rel).exists() and rel not in self.files:
            raise Stop(f"cannot delete {rel}: it is not in this checkout",
                       EXIT_CANNOT_RUN)
        self.files.pop(rel, None)
        self.deleted.add(rel)

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise Stop(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.", EXIT_CANNOT_RUN)
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel in sorted(self.deleted):
            p = self.root / rel
            if p.exists():
                p.unlink()
                touched.append(f"{rel} (deleted)")
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = self.encode(rel, text)
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched

    def encode(self, rel: str, text: str) -> bytes:
        """Text back to bytes in the form the file had when it was read.

        A file never read -- one this script creates -- has no form to keep
        and is written as plain UTF-8 with LF, which is what every file in
        this fleet is unless it says otherwise.
        """
        bom, all_crlf = self.form.get(rel, (False, False))
        if all_crlf:
            text = text.replace("\n", "\r\n")
        return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort", "killed" or "env" -- only exit code 1 means a
    test failed.

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
        # EXIT 1 IS NOT ALWAYS A TEST DISAGREEING, and this used to assume it
        # was. A missing pytest PLUGIN or a missing pinned package does not
        # stop collection -- the tests are found, then fail at setup -- so
        # pytest exits 1, the same code a real regression gives.
        #
        # It shipped that way. A fresh Codespace with the app requirements and
        # none of tests/requirements-dev.txt ran a round that had landed
        # cleanly and got 85 errors ("fixture 'qtbot' not found": pytest-qt)
        # and 3 failures ("No module named 'engine'": the rnv-brand pin), and
        # the verdict was "FAILED -- the suite is not green". Not one of the 88
        # was the change disagreeing with anything.
        #
        # The discriminator is the assertion. A regression raises
        # AssertionError; a missing dependency raises nothing of the kind. If
        # the run carries environment signatures and NO assertion failure, it
        # is the environment. If it carries both, it is a failure -- the
        # conservative direction, because under-reporting a real regression is
        # the one way this verdict must never be wrong.
        if _missing_dependency(out) and not _ASSERTION.search(out):
            return "env"
        return "fail"
    return "env"


#: A dependency that is not installed, as pytest reports it. Each of these
#: arrived in a real run of this fleet's suites.
_ENV_SIGNS = (
    re.compile(r"fixture '\w+' not found"),                 # a pytest plugin
    re.compile(r"ModuleNotFoundError: No module named"),    # a package
    re.compile(r"\bis not importable\b"),                   # the register pin
    re.compile(r"ImportError: lib[\w.+-]+\.so"),            # a system library
)
#: A real regression. pytest prints the failing line under `E   ` and the
#: exception class in the summary.
_ASSERTION = re.compile(r"^E\s+assert\b|\bAssertionError\b", re.M)


def _missing_dependency(out: str) -> bool:
    return any(sign.search(out) for sign in _ENV_SIGNS)


#: verdict -> taxonomy. "abort" and "killed" are EXIT_INCOMPLETE rather than
#: EXIT_CANNOT_RUN: the environment WAS ready and the run started, which is a
#: different instruction to the operator -- re-run, do not go installing things.
_VERDICT_CODE = {
    "pass": EXIT_CLEAN,
    "fail": EXIT_DISAGREES,
    "env": EXIT_CANNOT_RUN,
    "abort": EXIT_INCOMPLETE,
    "killed": EXIT_INCOMPLETE,
}


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
    return _VERDICT_CODE[verdict]


def verify() -> int:
    # A script that changes the ENVIRONMENT its suites run in does it here,
    # not in checks(): checks() runs against the in-memory tree before
    # anything is on disk. The register pin is the case that needed it -- it
    # writes a dependency line and then runs tests that import what the line
    # declares, and DECLARING IS NOT INSTALLING.
    #
    # In verify() rather than apply() so that `--verify` gets it too; that is
    # the entry point someone uses to re-check a repository, and it has to
    # prepare the same environment.
    hook = globals().get("post_write")
    if hook is not None:
        hook()
        print()

    # GUARD_CMD is OPTIONAL and exists for a repository with no pytest. Every
    # round until 2026-09-12 ran inside one of the five applications, where a
    # guard is a test file; rnv-brand has no tests directory, no pytest
    # dependency, and a deliberate ZERO-IMPORT policy in engine/brand.py --
    # its own idiom is a function that runs AT IMPORT and raises. Installing
    # pytest there to satisfy this harness would change the shape of someone
    # else's repository to suit a tool, which is backwards. GUARD still names
    # the file that holds the check; GUARD_CMD says how to run it.
    guard_cmd = globals().get("GUARD_CMD") or [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", GUARD]
    code = _step("guard", guard_cmd)
    if code != EXIT_CLEAN:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != EXIT_CLEAN:
            return code
    print("\nGreen.")
    return EXIT_CLEAN


def apply(check_only: bool) -> int:
    root = Path.cwd()

    # FIRST. Before the sentinel, before any anchor. See the docstring.
    refuse_wrong_repository(root)

    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise Stop(globals().get("MISSING_HELP") or
                   f"run this from the root of a {REPO} checkout "
                   f"(no {SENTINEL_FILE} here)", EXIT_CANNOT_RUN)

    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8-sig"):
        # ALREADY APPLIED IS NOT AN ERROR, AND USED TO EXIT 1.
        #
        # The operator runs this from a phone and the honest question behind a
        # second run is "did this land?". Exiting 1 answered "something
        # disagreed", which is the one thing that had not happened. Re-running
        # the suites answers the question that was actually asked, and a
        # repository that has the change and passes its tests is CLEAN.
        print(f"already applied -- {SENTINEL!r} is present in "
              f"{SENTINEL_FILE}.\nNothing to write. Re-running the suites so "
              f"the answer is measured rather than assumed.\n")
        return verify()

    tree = Tree(root)
    edits(tree)

    # THE SCRIPT MUST WRITE ITS OWN SENTINEL WHERE apply() LOOKS FOR IT.
    #
    # Checked here, against the in-memory tree, before anything reaches disk.
    #
    # WHY THIS IS NOT A BUILD-TIME CHECK. The build's `sentinel-written` guard
    # asserts the marker appears at least twice in the composed script -- its
    # own declaration plus somewhere it gets written. That is a PROXY. A round
    # can carry the marker in a new guard file and never put it in
    # SENTINEL_FILE, and the build passes while the already-applied branch can
    # never fire. That shipped once, on 2026-09-24: the operator ran a landed
    # script a second time and got "expected 1 occurrence of the anchor, found
    # 0. The file moved" -- about a file that had not moved, from a script
    # that could not tell it had already run.
    #
    # Here the question is exact rather than approximated: after every edit,
    # is the marker in the file apply() reads? It fires on the FIRST run, in
    # the author's verification, rather than on the operator's second.
    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise Stop(
            f"this script never writes {SENTINEL!r} into {SENTINEL_FILE}, "
            f"which is the file it reads to tell whether it has already run.\n"
            f"Applied once it would work; run again it would re-attempt "
            f"anchors that are already replaced and report them as missing.\n"
            f"Add an edit that marks {SENTINEL_FILE}. Nothing was written.",
            EXIT_CANNOT_RUN)
    # GUARD_SOURCE is OPTIONAL. Every round until 2026-09-12 installed a new
    # guard file, so the harness assumed one; the ramp-condense round adopts
    # three that already exist -- the mixer's SPLITS table and two RETIRED
    # tuples -- and adding a fourth rule for what they already watch is how a
    # suite grows checks that disagree. GUARD still names the file verify()
    # runs first; it just does not have to be a file this script wrote.
    source = globals().get("GUARD_SOURCE")
    if source is not None:
        tree.write(GUARD, source)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        _left_alone()
        return EXIT_CLEAN

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    code = verify()
    if code == EXIT_CLEAN:
        _left_alone()
    return code


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    try:
        refuse_to_shadow()
        if args.finish:
            finish()
            return EXIT_CLEAN
        if args.verify:
            return verify()
        return apply(args.check)
    except Stop as stop:
        # Print it ourselves and return the taxonomy code. Letting SystemExit
        # propagate would print the message and exit 1 regardless of .code.
        print(stop.args[0] if stop.args else "", file=sys.stderr)
        return stop.code


if __name__ == "__main__":
    raise SystemExit(main())
