"""derive the named colours written as integer tuples (ruling 3)

    python up.py             # apply, then run the guard and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guard and CI's commands, change nothing

For rnv-color-palette-manager, derived against a fresh clone at the live head (c862eae).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-25 (ruling 3): colours written as integer tuples are derived,
the NAMED ones only; the structural QColor(0, 0, 0) and QColor(255, 255, 255)
calls are left alone. Five named tuples are derived now: SEARCH_DIM_OVERLAY and
DEFAULT_SLOT_COLOR_IMAGE_RGB as translucent_tuple(TRUE_BLACK, <named alpha>),
PREVIEW_GRID_BORDER as _to_rgb(TRUE_BLACK), and the two #505050 borders as
_to_rgb(GREY_44).

ONE THING MOVES, BY RULING (2026-09-25, ruling 1). The thin slot border and
the history swatch border go from (80, 80, 80) to GREY_44, (68, 68, 68). A
render showed the two all but indistinguishable at 1px. The collapse guard's
PENDING_RULING empties, so any integer spelling of #505050 that comes back
fails.
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
import typing
from pathlib import Path

REPO = 'rnv-color-palette-manager'
SENTINEL = 'RNV-TUPLE-ROUND'
SENTINEL_FILE = 'tests/test_derived_values.py'
GUARD = 'tests/test_derived_values.py'
DESCRIPTION = 'derive the named colours written as integer tuples (ruling 3)'

#: EXACTLY WHAT CI RUNS. Both workflows run `python run_tests.py`, which runs
#: the locked root suite under unittest and then tests/ under pytest.
SUITES = [("python run_tests.py  (both CI workflows)",
           [sys.executable, "run_tests.py"])]

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '898c16b8a02fa92b09c1bed0fa1f9f8b872d2d3d29d506b7a9c9a1ec357de42e', '.github/workflows/tests.yml': '5d3891f82137b62cb3b2576454eb30079ee981ca559fac90d67431f579e5abe5'}

SHADOWS = {"colors.py", "conftest.py", "run_tests.py", "test_rnv_palette_manager.py"}

LEFT_ALONE = ['SLOT_BORDER_THICK_COLOR (60, 60, 60). #3c3c3c has no row; the ruling found the thick border differs from the thin by its width.', "SEARCH_HIGHLIGHT_COLOR (0, 255, 100). #00ff64 is on no register row, a question for the register like SELECTION_OVERLAY_COLOR's blue.", 'TRANSPARENT_RGBA (0, 0, 0, 0). Alpha zero draws no colour.', 'the colour-name table in ui/color_search.py. It depicts CSS names for search; it is data, not a brand element.']


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('ui/colors.py',
             '    return f"rgba({r}, {g}, {b}, {_alpha_byte(alpha)})"\n',
             '    return f"rgba({r}, {g}, {b}, {_alpha_byte(alpha)})"\n\n\n\ndef translucent_tuple(hex_color: str, alpha: int) -> tuple[int, int, int, int]:\n    """The same derivation, as the (r, g, b, a) tuple QColor(*t) takes.\n\n    RNV-TUPLE-ROUND, 2026-09-26. The third spelling of one derived value:\n    translucent() writes #aarrggbb for stylesheets and QColor(); this is for\n    the callers that unpack a tuple into QColor or key a cache by one. A tuple\n    is the notation the fleet\'s string sweeps never read, so a constant written\n    as one could not follow its base. Same refusals as translucent(), same\n    bytes.\n    """\n    h = _hex6(hex_color)\n    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), _alpha_byte(alpha))\n')
    tree.sub('ui/colors.py',
             'DEFAULT_SLOT_COLOR_IMAGE_RGB spells the same colour as an integer tuple and is\nNOT derived yet. Tuples are a notation of their own, measured across the fleet\non 2026-09-25, and they get a round of their own."""\n',
             'DEFAULT_SLOT_COLOR_IMAGE_RGB spells the same colour as an integer tuple, and\nsince 2026-09-26 it is derived from the same pair (RNV-TUPLE-ROUND)."""\n\nSEARCH_DIM_ALPHA: Final[int] = 0x8C\n"""140. The dim drawn over slots that do not match a search (TRUE_BLACK) --\nthe byte it already had."""\n')
    tree.sub('ui/colors.py',
             'SEARCH_DIM_OVERLAY: Final[tuple[int,int,int,int]] = (0, 0, 0, 140)\n"""Semi-transparent black overlay drawn on non-matching slots."""\n\nSLOT_BORDER_THIN_COLOR: Final[tuple[int,int,int]] = (80, 80, 80)\n"""Border color for thin slot border style."""\n',
             'SEARCH_DIM_OVERLAY: Final[tuple[int,int,int,int]] = translucent_tuple(\n    TRUE_BLACK, SEARCH_DIM_ALPHA)\n"""Semi-transparent black overlay drawn on non-matching slots."""\n\nSLOT_BORDER_THIN_COLOR: Final[tuple[int,int,int]] = _to_rgb(GREY_44)\n"""Border color for thin slot border style. GREY_44: it was (80, 80, 80),\n#505050, until the 2026-09-25 ruling collapsed it (RNV-COLLAPSE-505050)."""\n')
    tree.sub('ui/colors.py',
             'PREVIEW_GRID_BORDER: Final[tuple[int, int, int]] = (0, 0, 0)\n"""Border color for grid cells in the preview grid widget."""\n\nHISTORY_SWATCH_BORDER: Final[tuple[int, int, int]] = (80, 80, 80)\n"""Border color for color history swatch thumbnails."""\n',
             'PREVIEW_GRID_BORDER: Final[tuple[int, int, int]] = _to_rgb(TRUE_BLACK)\n"""Border color for grid cells in the preview grid widget."""\n\nHISTORY_SWATCH_BORDER: Final[tuple[int, int, int]] = _to_rgb(GREY_44)\n"""Border color for color history swatch thumbnails. GREY_44: it was\n(80, 80, 80), #505050, until the 2026-09-25 ruling collapsed it."""\n')
    tree.sub('ui/colors.py',
             'DEFAULT_SLOT_COLOR_IMAGE_RGB: Final[tuple[int, int, int, int]] = (0, 0, 0, 171)\n"""Default slot color in Image mode as RGBA tuple."""\n',
             'DEFAULT_SLOT_COLOR_IMAGE_RGB: Final[tuple[int, int, int, int]] = translucent_tuple(\n    TRUE_BLACK, SLOT_IMAGE_ALPHA)\n"""Default slot color in Image mode as RGBA tuple: DEFAULT_SLOT_COLOR_IMAGE\'s\ncolour and alpha, in the spelling QColor(*t) takes."""\n')
    tree.sub('ui/colors.py',
             '    "translucent_rgba",\n',
             '    "translucent_rgba",\n    "translucent_tuple",\n')
    tree.sub('tests/test_collapse_505050.py',
             'WHAT IT STILL CANNOT CLEAR, STATED RATHER THAN HIDDEN. Two constants hold the\nvalue as an INTEGER TUPLE, which no string sweep reads at all:\n\n    SLOT_BORDER_THIN_COLOR   (80, 80, 80)   core/color_slot.py, the thin slot pen\n    HISTORY_SWATCH_BORDER    (80, 80, 80)   utils/color_history.py, the swatch pen\n\nWhether a slot border is the same decision as a scrollbar handle is a ruling,\nnot a sweep -- the thin and thick slot borders are told apart partly by\ncolour, and a collapse must not erase a distinction nobody was asked about.\nSo they are pinned as the KNOWN set: a third appearing fails, and collapsing\neither fails until PENDING_RULING is updated in the same commit.\n',
             'THE LAST TWO, RULED. Two constants held the value as an INTEGER TUPLE, which\nno string sweep reads at all:\n\n    SLOT_BORDER_THIN_COLOR   (80, 80, 80)   core/color_slot.py, the thin slot pen\n    HISTORY_SWATCH_BORDER    (80, 80, 80)   utils/color_history.py, the swatch pen\n\nWhether a slot border was the same decision as a scrollbar handle was a\nruling, not a sweep, and it was asked. A render showed #505050 and #444444\nall but indistinguishable at 1px, and the thick border (#3c3c3c) differs by\nits width, not its colour. Ruled 2026-09-25: collapse. Since 2026-09-26 both\nare _to_rgb(GREY_44) (RNV-TUPLE-ROUND), and PENDING_RULING is empty, so any\ninteger spelling of the value that comes back fails.\n')
    tree.sub('tests/test_collapse_505050.py',
             '#: The integer spellings of the value that await a ruling, by the name each is\n#: assigned to. Not an exemption: the sweep below must find EXACTLY these, so\n#: a new one fails, and a ruled one fails until this is updated.\nPENDING_RULING = {\n    ("ui/colors.py", "SLOT_BORDER_THIN_COLOR"),\n    ("ui/colors.py", "HISTORY_SWATCH_BORDER"),\n}\n',
             '#: The integer spellings of the value that await a ruling, by the name each is\n#: assigned to. Not an exemption: the sweep below must find EXACTLY these, so\n#: a new one fails. EMPTY since 2026-09-26: the last two were ruled onto\n#: GREY_44 and are written through it.\nPENDING_RULING: set[tuple[str, str]] = set()\n')
    tree.sub('tests/test_collapse_505050.py',
             '        f"A new one is a survivor. A gone one was ruled on: update "\n        f"PENDING_RULING in the same commit.")\n',
             '        f"A new one is a survivor. A gone one was ruled on: update "\n        f"PENDING_RULING in the same commit.")\n\n\ndef test_the_ruled_tuples_hold_the_new_value_through_the_constant():\n    """The two tuples the 2026-09-25 ruling collapsed. #444444, and written as\n    _to_rgb(GREY_44), so a later move of GREY_44 reaches them too."""\n    from ui import colors\n    tree = ast.parse((ROOT / PALETTE_FILE).read_text(encoding="utf-8-sig"))\n    values = {}\n    for node in tree.body:\n        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:\n            target = node.targets[0] if isinstance(node, ast.Assign) else node.target\n            values[getattr(target, "id", "")] = node.value\n    for name in ("SLOT_BORDER_THIN_COLOR", "HISTORY_SWATCH_BORDER"):\n        assert getattr(colors, name) == (0x44, 0x44, 0x44), (\n            f"{name} is {getattr(colors, name)}, ruled onto {NEW_HEX}")\n        node = values[name]\n        assert (isinstance(node, ast.Call)\n                and getattr(node.func, "id", None) == "_to_rgb"\n                and [ast.unparse(a) for a in node.args] == [CONST]), (\n            f"{name} is {ast.unparse(node)}, not _to_rgb({CONST})")\n')
    tree.sub('tests/test_derived_values.py',
             '    assert not written, "written in upper case:\\n  " + "\\n  ".join(written)\n',
             '    assert not written, "written in upper case:\\n  " + "\\n  ".join(written)\n\n\n# ------------------------------------------------- colours spelled in integers\n\nimport importlib as _importlib\n\n#: Where the derived constants live, and where their bases and alphas live.\nTUPLE_HOME = \'ui/colors.py\'\nTUPLE_HOME_MODULE = \'ui.colors\'\nTUPLE_BASES_MODULE = \'ui.colors\'\n#: Each derived constant, by NAME: (helper, base, alpha or None). A register\n#: move passes straight through; a value re-made from something else fails.\nTUPLES_MADE_OF = {\'SEARCH_DIM_OVERLAY\': (\'translucent_tuple\', \'TRUE_BLACK\', \'SEARCH_DIM_ALPHA\'), \'SLOT_BORDER_THIN_COLOR\': (\'_to_rgb\', \'GREY_44\', None), \'PREVIEW_GRID_BORDER\': (\'_to_rgb\', \'TRUE_BLACK\', None), \'HISTORY_SWATCH_BORDER\': (\'_to_rgb\', \'GREY_44\', None), \'DEFAULT_SLOT_COLOR_IMAGE_RGB\': (\'translucent_tuple\', \'TRUE_BLACK\', \'SLOT_IMAGE_ALPHA\')}\n#: The alpha bytes behind them, each the one its literal already carried.\nTUPLE_ALPHAS = {\'SEARCH_DIM_ALPHA\': 140, \'SLOT_IMAGE_ALPHA\': 171}\n#: Module- and class-level constants spelled in integers ON PURPOSE -- data a\n#: person starts from, not a brand element -- with the reason.\nINT_DATA = {}\nTUPLE_FILES = 30\n#: The call each derived constant is wrapped in, if any.\n_WRAP = None\n\n\ndef _int_spelled(tree):\n    """(name, #rrggbb, alpha) for every module- or class-level constant whose\n    value spells a colour in integers: a tuple or list of three or four int\n    literals, or QColor/QPen/QBrush called with them. Locals inside functions\n    are state, not constants, and are not read."""\n    bodies = [tree.body] + [n.body for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]\n    for body in bodies:\n        for statement in body:\n            if (not isinstance(statement, (ast.Assign, ast.AnnAssign))\n                    or statement.value is None):\n                continue\n            target = (statement.targets[0] if isinstance(statement, ast.Assign)\n                      else statement.target)\n            name, value = getattr(target, "id", None), statement.value\n            if isinstance(value, (ast.Tuple, ast.List)):\n                elts = value.elts\n            elif isinstance(value, ast.Call) and (\n                    getattr(value.func, "id", None) or getattr(value.func, "attr", None)\n                    ) in ("QColor", "fromRgb", "QPen", "QBrush"):\n                elts = value.args\n            else:\n                continue\n            if name is None or len(elts) not in (3, 4):\n                continue\n            ints = [e.value for e in elts\n                    if isinstance(e, ast.Constant) and type(e.value) is int]\n            if len(ints) != len(elts) or not all(0 <= i <= 255 for i in ints):\n                continue\n            yield (name, "#%02x%02x%02x" % tuple(ints[:3]),\n                   ints[3] if len(ints) == 4 else 255)\n\n\ndef _tuple_trees():\n    """Application source: not tests, not a root test suite, not a delivery\n    script. BOM-aware."""\n    for path in sorted(ROOT.rglob("*.py")):\n        rel = path.relative_to(ROOT)\n        if any(p in {".git", "tests", "snapshots", "build", "dist", ".venv",\n                     "venv", "__pycache__"} for p in rel.parts):\n            continue\n        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):\n            continue\n        text = path.read_bytes().decode("utf-8-sig", errors="replace")\n        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:\n            continue\n        yield rel, ast.parse(text)\n\n\ndef _rgb_of(hex_color):\n    h = hex_color.lstrip("#")\n    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))\n\n\ndef _as_rgba(value):\n    """A tuple as it is; a QColor as its channels."""\n    if hasattr(value, "alpha") and callable(value.alpha):\n        return (value.red(), value.green(), value.blue(), value.alpha())\n    return tuple(value)\n\n\ndef test_the_integer_sweep_reads_both_notations():\n    """Guard the guard: a tuple and a QColor at module or class level are\n    read; a local inside a function is not."""\n    probe = ast.parse("A = (0, 0, 0, 50)\\n"\n                      "class K:\\n    B = QColor(68, 68, 68)\\n"\n                      "def f():\\n    c = (0, 0, 0)\\n")\n    assert sorted(_int_spelled(probe)) == [("A", "#000000", 50), ("B", "#444444", 255)]\n\n\ndef test_every_tuple_constant_is_derived_by_name():\n    """RNV-TUPLE-ROUND, 2026-09-26. A colour spelled in integers is a colour\n    every string sweep in the fleet was blind to, and #505050 sat in two of\n    them for three weeks after it was ruled away. Each constant here is now\n    its helper called on a named base and a named alpha, and it evaluates to\n    exactly that pair -- held BY NAME, so a register move passes through."""\n    tree = ast.parse((ROOT / TUPLE_HOME).read_text(encoding="utf-8-sig"))\n    values = {}\n    for node in tree.body:\n        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:\n            t = node.targets[0] if isinstance(node, ast.Assign) else node.target\n            if getattr(t, "id", None):\n                values[t.id] = node.value\n    home = _importlib.import_module(TUPLE_HOME_MODULE)\n    bases = _importlib.import_module(TUPLE_BASES_MODULE)\n    assert TUPLES_MADE_OF, "nothing to check"\n    for name, (helper, base, alpha) in TUPLES_MADE_OF.items():\n        call = values.get(name)\n        assert call is not None, f"{name} is gone from {TUPLE_HOME}"\n        if _WRAP:\n            assert (isinstance(call, ast.Call)\n                    and getattr(call.func, "id", None) == _WRAP\n                    and len(call.args) == 1), (\n                f"{name} is not {_WRAP}(...): {ast.unparse(call)}")\n            call = call.args[0]\n        want_names = [base] + ([alpha] if alpha else [])\n        assert (isinstance(call, ast.Call) and getattr(call.func, "id", None) == helper\n                and [getattr(a, "id", None) for a in call.args] == want_names\n                and not call.keywords), (\n            f"{name} is {ast.unparse(call)}, not {helper}({\', \'.join(want_names)})")\n        live = _as_rgba(getattr(home, name))\n        want = _rgb_of(getattr(bases, base)) + ((TUPLE_ALPHAS[alpha],) if alpha else ())\n        if len(live) == 4 and len(want) == 3:\n            want += (255,)\n        assert live == want, f"{name} is {live}; made of {want_names} it is {want}"\n\n\ndef test_the_tuple_alphas_are_the_declared_bytes():\n    bases = _importlib.import_module(TUPLE_BASES_MODULE)\n    for name, byte in TUPLE_ALPHAS.items():\n        value = getattr(bases, name)\n        assert type(value) is int and value == byte, (\n            f"{name} is {value!r}, declared {byte:#x}")\n\n\ndef test_no_named_colour_is_spelled_in_integers():\n    """The completeness half. Every module- or class-level constant in the\n    application that spells a NAMED colour in integers. Alpha 0 draws no\n    colour; a base no constant names has no row to follow; and INT_DATA is\n    data a person starts from, each with its reason."""\n    bases = _importlib.import_module(TUPLE_BASES_MODULE)\n    named = {v.lower() for n, v in vars(bases).items()\n             if n.isupper() and isinstance(v, str)\n             and re.fullmatch(r"#[0-9a-fA-F]{6}", v)}\n    strays, files = [], 0\n    for rel, tree in _tuple_trees():\n        files += 1\n        for name, rgb, alpha in _int_spelled(tree):\n            if name in INT_DATA or alpha == 0 or rgb not in named:\n                continue\n            strays.append(f"{rel}: {name} = {rgb} at alpha {alpha}")\n    assert files >= TUPLE_FILES, f"only {files} files swept -- the walk has gone blind"\n    assert not strays, ("named colours still spelled in integers, where no "\n                        "register move reaches them:\\n  " + "\\n  ".join(strays))\n')


def _original(tree, rel: str) -> str:
    """The file as it is on disk, which checks() runs before flush() changes,
    normalised the way Tree.read() normalises it."""
    raw = (tree.root / rel).read_bytes()
    text = (raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw).decode("utf-8")
    crlf = text.count("\r\n")
    if crlf and crlf == text.count("\n"):
        text = text.replace("\r\n", "\n")
    return text


def _picked(src: str, names: set) -> dict:
    """The named top-level definitions, and nothing else, evaluated in source
    order -- the values checked here without importing the module, which
    pulls in PyQt6 and the application's logger."""
    body = []
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            body.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(t, "id", None) in names:
                body.append(node)
    ns = {"Final": typing.Final}
    exec(compile(ast.Module(body=body, type_ignores=[]), "picked", "exec"), ns)
    missing = set(names) - set(ns)
    assert not missing, f"not found: {sorted(missing)}"
    return ns


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""

    names = ("SEARCH_DIM_OVERLAY", "SLOT_BORDER_THIN_COLOR", "PREVIEW_GRID_BORDER",
             "HISTORY_SWATCH_BORDER", "DEFAULT_SLOT_COLOR_IMAGE_RGB")
    old = _picked(_original(tree, "ui/colors.py"), set(names))
    new = _picked(tree.read("ui/colors.py"),
                  {"_to_rgb", "_hex6", "_alpha_byte", "translucent_tuple", "TRUE_BLACK",
                   "GREY_44", "SEARCH_DIM_ALPHA", "SLOT_IMAGE_ALPHA", *names})
    ruled = {"SLOT_BORDER_THIN_COLOR", "HISTORY_SWATCH_BORDER"}
    for name in names:
        assert type(new[name]) is tuple, f"{name} is not a tuple: {new[name]!r}"
        if name in ruled:
            # the one move, by ruling: #505050 onto GREY_44, and nothing else
            assert old[name] == (80, 80, 80) and new[name] == (68, 68, 68), (
                f"{name}: {old[name]} -> {new[name]}")
        else:
            assert new[name] == old[name], f"{name}: {old[name]} -> {new[name]}"
    collapse = tree.read("tests/test_collapse_505050.py")
    assert "PENDING_RULING: set[tuple[str, str]] = set()" in collapse
    ast.parse(collapse)
    guard = tree.read(GUARD)
    ast.parse(guard)
    assert "def test_every_tuple_constant_is_derived_by_name" in guard
    assert SENTINEL in guard
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
