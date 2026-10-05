"""#505050 is gone from every string in this application. RNV-COLLAPSE-GUARD

Ruled 2026-09-02: #505050 collapses onto GREY_44 #444444. The value was on
neither the surface ladder nor the ink grid, and its neighbours were not a
visible step away. This guard pins the ruling in both directions: the keys
hold the new value, and they hold it THROUGH the constant.

WHAT THIS GUARD USED TO SAY, AND WHY IT WAS WRONG. Until 2026-09-25 its first
line read "#505050 no longer exists in this application", and it passed while
IMAGE_MODE_COLORS['scrollbar_handle'] read 'rgba(80, 80, 80, 100)' -- #505050
at alpha 100, painting the main scrollbar in image mode. Three blind spots
lined up:

  - EXPECT listed image mode's scroll_handle and not its scrollbar_handle;
  - the palette sweep compared whole strings with '#505050';
  - the source sweep looked for that string, quoted.

None of the three decoded rgba(), and rgba() was the only spelling the value
had left. Every check below decodes: #rgb, #rrggbb, #aarrggbb, rgb() and
rgba() all read as the colour they are.

THE LAST TWO, RULED. Two constants held the value as an INTEGER TUPLE, which
no string sweep reads at all:

    SLOT_BORDER_THIN_COLOR   (80, 80, 80)   core/color_slot.py, the thin slot pen
    HISTORY_SWATCH_BORDER    (80, 80, 80)   utils/color_history.py, the swatch pen

Whether a slot border was the same decision as a scrollbar handle was a
ruling, not a sweep, and it was asked. A render showed #505050 and #444444
all but indistinguishable at 1px, and the thick border (#3c3c3c) differs by
its width, not its colour. Ruled 2026-09-25: collapse. Since 2026-09-26 both
are _to_rgb(GREY_44) (RNV-TUPLE-ROUND), and PENDING_RULING is empty, so any
integer spelling of the value that comes back fails.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD_HEX = "#505050"
NEW_HEX = "#444444"
CONST = "GREY_44"
EXPECT = {'dark': ['scroll_handle', 'scrollbar_handle'],
          'image': ['scroll_handle', 'scrollbar_handle']}
PALETTE_FILE = "ui/colors.py"
DICT_NAMES = {'dark': 'DARK_THEME_COLORS', 'image': 'IMAGE_MODE_COLORS',
              'light': 'LIGHT_THEME_COLORS'}

#: The integer spellings of the value that await a ruling, by the name each is
#: assigned to. Not an exemption: the sweep below must find EXACTLY these, so
#: a new one fails. EMPTY since 2026-09-26: the last two were ruled onto
#: GREY_44 and are written through it.
PENDING_RULING: set[tuple[str, str]] = set()

#: Files that name the value in order to forbid it. The last is the fleet's
#: delivery marker: a delivery script quotes what it retires.
SKIP_MARKERS = ("RNV-COLLAPSE-GUARD", "RNV-COLLAPSE-TOOL-DO-NOT-SWEEP",
                "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP")
SKIP_DIRS = {".git", "build", "dist", ".venv", "venv", "__pycache__"}

_HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_FUNC = re.compile(r"\brgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})"
                   r"\s*(?:,\s*[0-9]*\.?[0-9]+\s*)?\)")


def colours_in(text: str) -> set[str]:
    """Every colour written in `text`, normalised to #rrggbb.

    #AARRGGBB is Qt's order, ALPHA FIRST: the colour is the LAST six digits.
    Taking the first six turns #96444444 into #964444 -- a real colour and the
    wrong one, which is the failure that does not look like a failure."""
    found = set()
    for m in _HEX.finditer(text):
        h = m.group(0)[1:].lower()
        if len(h) == 8:
            h = h[2:]
        elif len(h) == 3:
            h = "".join(c * 2 for c in h)
        found.add("#" + h)
    for m in _FUNC.finditer(text):
        channels = [int(g) for g in m.groups()]
        if all(c <= 255 for c in channels):
            found.add("#%02x%02x%02x" % tuple(channels))
    return found


def _palettes():
    from ui.colors import (DARK_THEME_COLORS, IMAGE_MODE_COLORS,
                           LIGHT_THEME_COLORS)
    return {'dark': DARK_THEME_COLORS, 'image': IMAGE_MODE_COLORS,
            'light': LIGHT_THEME_COLORS}


def _dict_nodes():
    tree = ast.parse((ROOT / PALETTE_FILE).read_text(encoding="utf-8-sig"))
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if (getattr(target, "id", None) in DICT_NAMES.values()
                    and isinstance(node.value, ast.Dict)):
                out[target.id] = node.value
    return out


def _sources():
    for path in sorted(ROOT.rglob("*.py")):
        if any(p in SKIP_DIRS for p in path.parts):
            continue
        if path.parent == ROOT and path.name.startswith("up"):
            continue
        text = path.read_bytes().decode("utf-8-sig", errors="replace")
        if any(m in text for m in SKIP_MARKERS):
            continue
        yield path, text


def _string_uses(tree: ast.AST):
    """String constants that are EVALUATED -- not docstrings, and not any
    other bare string statement. A comment is not a string at all.

    Use versus mention: the notes beside each ruled key say "was #505050",
    and that is the record of the ruling, not a use of the value."""
    bare = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list):
            continue
        for statement in body:
            if (isinstance(statement, ast.Expr)
                    and isinstance(statement.value, ast.Constant)):
                bare.add(id(statement.value))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in bare):
            yield node


def _int_spellings(tree: ast.AST, rgb: tuple[int, int, int]):
    """(assigned name or '', line) for every tuple, and every QColor, QPen or
    QBrush call, that spells `rgb` in integers -- the notation no string sweep
    can see."""
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
    for node in ast.walk(tree):
        values = None
        if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) in (3, 4):
            values = node.elts
        elif isinstance(node, ast.Call) and len(node.args) >= 3:
            fname = (getattr(node.func, "id", None)
                     or getattr(node.func, "attr", None))
            if fname in ("QColor", "fromRgb", "QPen", "QBrush"):
                values = node.args
        if not values:
            continue
        ints = tuple(v.value for v in values[:3]
                     if isinstance(v, ast.Constant) and type(v.value) is int)
        if ints != rgb:
            continue
        up = parents.get(id(node))
        name = ""
        if isinstance(up, (ast.Assign, ast.AnnAssign)):
            target = up.targets[0] if isinstance(up, ast.Assign) else up.target
            name = getattr(target, "id", "") or getattr(target, "attr", "")
        yield name, node.lineno


# ------------------------------------------------------------ guard the guard

def test_the_decoder_reads_every_spelling_the_value_can_wear():
    """If this fails, every negative check below is blind in the way the first
    version of this file was."""
    for spelling in ("#505050", "#96505050", "#FF505050",
                     "rgba(80, 80, 80, 100)", "rgba(80,80,80,0.6)",
                     "rgb(80, 80, 80)"):
        assert OLD_HEX in colours_in(f"background: {spelling};"), spelling
    assert colours_in("#555") == {"#555555"}
    # and it does not read colours that are not there, or the wrong end
    assert colours_in("#96444444") == {NEW_HEX}
    assert colours_in("translate(80, 80, 80)") == set()
    assert colours_in("#12345") == set()


def test_the_integer_sweep_reads_both_notations():
    probe = ast.parse("A = (80, 80, 80)\n"
                      "pen.setColor(QColor(80, 80, 80, 150))\n"
                      "C = (80, 80, 81)\n")
    assert sorted(n for n, _ in _int_spellings(probe, (80, 80, 80))) == ["", "A"]


# ------------------------------------------------------------------ the ruling

def test_the_ruled_keys_hold_the_new_value():
    """Decoded, so a derived entry -- GREY_44 at an alpha -- reads as the
    colour it is, not as a string that fails to equal '#444444'."""
    for mode, keys in EXPECT.items():
        palette = _palettes()[mode]
        for key in keys:
            assert colours_in(palette[key]) == {NEW_HEX}, (
                f"{mode}[{key}] is {palette[key]}, ruled onto {NEW_HEX}")


def test_the_keys_are_wired_through_the_constant_not_rewritten():
    """Swapping one literal for another passes the value check and defeats
    the point. The constant is what a later substitution changes -- named
    directly, or as the base of a derived value."""
    nodes = _dict_nodes()
    for mode, keys in EXPECT.items():
        node = nodes[DICT_NAMES[mode]]
        entries = {k.value: v for k, v in zip(node.keys, node.values)
                   if isinstance(k, ast.Constant)}
        # RNV-NAMED-AND-USED, 2026-10-04: the image palette is the dark one
        # under its own name. An entry that arrives through the spread is
        # written in the palette it is spread from, and is read there.
        for k, v in zip(node.keys, node.values):
            if k is None:
                spread = nodes[ast.unparse(v)]
                for k2, v2 in zip(spread.keys, spread.values):
                    if isinstance(k2, ast.Constant):
                        entries.setdefault(k2.value, v2)
        for key in keys:
            value = entries.get(key)
            assert value is not None, f"{mode} has no {key}"
            if isinstance(value, ast.Call):
                assert getattr(value.func, "id", None) == "translucent", (
                    f"{mode}[{key}] is computed by something other than "
                    f"translucent(): {ast.unparse(value)}")
                value = value.args[0]
            assert isinstance(value, ast.Name) and value.id == CONST, (
                f"{mode}[{key}] is {ast.unparse(value)}, not written through "
                f"{CONST}")


def test_the_old_value_is_gone_from_every_palette():
    looked, holders = 0, []
    for mode, palette in _palettes().items():
        for key, value in palette.items():
            if not isinstance(value, str):
                continue
            looked += 1
            if OLD_HEX in colours_in(value):
                holders.append(f"{mode}[{key}] = {value}")
    # 84 since RNV-NAMED-AND-USED, 2026-10-04: nine keys nothing read went
    # from each of the three palettes.
    assert looked >= 84, f"only {looked} palette entries seen -- the sweep is blind"
    assert not holders, f"{OLD_HEX} is still painted, in some spelling: {holders}"


def test_the_old_value_is_not_written_anywhere_in_source():
    """Every evaluated string in every Python file, decoded. Skips this guard
    and anything carrying a delivery marker, which name the value in order to
    forbid it."""
    strays, files = [], 0
    for path, text in _sources():
        try:
            tree = ast.parse(text)
        except SyntaxError:
            strays.append(f"{path.relative_to(ROOT)}: does not parse, so it "
                          f"cannot be swept")
            continue
        files += 1
        for node in _string_uses(tree):
            if OLD_HEX in colours_in(node.value):
                strays.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert files >= 40, f"only {files} files swept -- the walk has gone blind"
    assert not strays, f"{OLD_HEX} is still written as a colour in: {strays}"


def test_the_integer_spellings_are_exactly_the_ones_awaiting_a_ruling():
    """The notation the string sweeps cannot see. Found 2026-09-25 by a census
    of integer tuples, after this guard had reported the value gone for three
    weeks."""
    found = set()
    for path, text in _sources():
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        rel = path.relative_to(ROOT).as_posix()
        for name, line in _int_spellings(tree, (80, 80, 80)):
            found.add((rel, name or f"<unnamed, line {line}>"))
    assert found == PENDING_RULING, (
        f"the integer spellings of {OLD_HEX} are not the known set.\n"
        f"  new, not ruled on:   {sorted(found - PENDING_RULING)}\n"
        f"  gone from the code:  {sorted(PENDING_RULING - found)}\n"
        f"A new one is a survivor. A gone one was ruled on: update "
        f"PENDING_RULING in the same commit.")


def test_the_ruled_tuples_hold_the_new_value_through_the_constant():
    """The two tuples the 2026-09-25 ruling collapsed. #444444, and written as
    _to_rgb(GREY_44), so a later move of GREY_44 reaches them too."""
    from ui import colors
    tree = ast.parse((ROOT / PALETTE_FILE).read_text(encoding="utf-8-sig"))
    values = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            values[getattr(target, "id", "")] = node.value
    for name in ("SLOT_BORDER_THIN_COLOR", "HISTORY_SWATCH_BORDER"):
        assert getattr(colors, name) == (0x44, 0x44, 0x44), (
            f"{name} is {getattr(colors, name)}, ruled onto {NEW_HEX}")
        node = values[name]
        assert (isinstance(node, ast.Call)
                and getattr(node.func, "id", None) == "_to_rgb"
                and [ast.unparse(a) for a in node.args] == [CONST]), (
            f"{name} is {ast.unparse(node)}, not _to_rgb({CONST})")
