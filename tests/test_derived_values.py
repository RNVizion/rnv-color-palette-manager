"""Derived values: a colour that is a named colour AT AN ALPHA.

A colour here used to be one of two things -- a name, or a literal -- and this
file adds the third the application always had and never declared.
rgba(51, 51, 51, 100) is not a colour beside APP_BORDER; it IS APP_BORDER at
alpha 100, and until 2026-09-25 nothing related the two. Now it is written
translucent(APP_BORDER, SCROLLBAR_BORDER_ALPHA), and a change to APP_BORDER
reaches it.

WHY THAT MATTERS HERE, MEASURED. RNV-COLLAPSE-505050 ruled #505050 onto
GREY_44 on 2026-09-02. IMAGE_MODE_COLORS went on painting the main scrollbar
handle with it for three weeks, spelled rgba(80, 80, 80, 100), while the guard
for that ruling reported clean. A written-down derivative is orphaned the
moment its source moves, and nothing says so.

THE OVERLAYS WERE THE OTHER HALF OF THE SAME IDEA. IMAGE_OVERLAY_ALPHA was the
string "ED" and the two overlays were written out beside it, with a test
asserting that their digits agreed. Ruled 2026-09-24: derived values are
DERIVED, not asserted. They compose from it now.

WHAT MOVES A PIXEL: ONE THING, BY RULING. The image-mode scrollbar handle goes
from #505050 at 100 to GREY_44 at 150. Everything else here is the same colour
at the same alpha, respelled so that it follows its base -- and
test_nothing_moved_that_was_not_ruled holds each value to the constant and the
byte it is made of.
"""
from __future__ import annotations

import ast
import pathlib
import re

from ui import colors
from ui.colors import (DARK_THEME_COLORS as DARK,
                       LIGHT_THEME_COLORS as LIGHT,
                       IMAGE_MODE_COLORS as IMAGE,
                       translucent,
                       translucent_rgba)

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "ui" / "colors.py"
PALETTES = {"DARK_THEME_COLORS": DARK, "LIGHT_THEME_COLORS": LIGHT,
            "IMAGE_MODE_COLORS": IMAGE}
HELPERS = ("translucent", "translucent_rgba")

#: constant -> the byte, and the spelling whose alpha it carries. Each is the
#: value the literal it replaced already held, except the handle's, which was
#: ruled up from 100.
ALPHAS = {
    "IMAGE_OVERLAY_ALPHA": (0xED, '"ED", the image chrome overlays'),
    "SCROLLBAR_HANDLE_ALPHA": (0x96, "ruled 2026-09-24; was 100"),
    "SCROLLBAR_BORDER_ALPHA": (0x64, "rgba(51, 51, 51, 100)"),
    "SIZE_OVERLAY_ALPHA": (0xC8, "rgba(0, 0, 0, 200)"),
    "SLOT_IMAGE_ALPHA": (0xAB, "rgba(0, 0, 0, 171)"),
}

#: What each derived value is made of: the constant its colour comes from, and
#: its alpha byte. See test_nothing_moved_that_was_not_ruled for why by name.
MADE_OF = {
    "APP_WINDOW_OVERLAY": ("TRUE_BLACK", 0xED),
    "APP_PANEL_OVERLAY": ("BRAND_BLACK", 0xED),
    "SIZE_OVERLAY_BG": ("TRUE_BLACK", 0xC8),
    "DEFAULT_SLOT_COLOR_IMAGE": ("TRUE_BLACK", 0xAB),
    "IMAGE_MODE_COLORS['scrollbar_border']": ("APP_BORDER", 0x64),
    "IMAGE_MODE_COLORS['scrollbar_handle']": ("GREY_44", 0x96),  # the ruled one
}

#: The one derived value spelled rgba(), and why. rgba() is valid in a
#: stylesheet and INVALID in QColor(), so it is the exception and says so.
RGBA_PINNED = {
    "SIZE_OVERLAY_BG": 'test_rnv_palette_manager.py asserts "rgba" is in it, '
                       'and that suite is locked',
}

_HEX8 = re.compile(r"^#([0-9a-fA-F]{2})([0-9a-fA-F]{6})$")
_RGBA = re.compile(r"^rgba\((\d{1,3}), (\d{1,3}), (\d{1,3}), (\d{1,3})\)$")
_COMPOSED = re.compile(r"#[0-9a-fA-F]{8}\b|\brgba\(\s*\d{1,3}\s*,\s*\d{1,3}"
                       r"\s*,\s*\d{1,3}\s*,\s*[0-9]*\.?[0-9]+\s*\)")


def decompose(value: str) -> tuple[str, int] | None:
    """(base '#rrggbb', alpha byte) -- taken apart, never rebuilt.

    Independent of translucent() by construction: a bug in the composing
    function cannot also be a bug here, which is what makes checking one
    against the other worth anything."""
    m = _HEX8.match(value)
    if m:
        return "#" + m.group(2).lower(), int(m.group(1), 16)
    m = _RGBA.match(value)
    if m:
        r, g, b, a = (int(x) for x in m.groups())
        return "#%02x%02x%02x" % (r, g, b), a
    return None


def _derived():
    """(where, call node, resolved value) for every helper call at module level
    in ui/colors.py -- a constant, or a value in a module-level dict."""
    tree = ast.parse(SRC.read_text(encoding="utf-8-sig"))
    out = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        name = getattr(target, "id", None)
        if name is None or node.value is None:
            continue
        if isinstance(node.value, ast.Call):
            if getattr(node.value.func, "id", None) in HELPERS:
                out.append((name, node.value, getattr(colors, name)))
        elif isinstance(node.value, ast.Dict):
            live = getattr(colors, name)
            for key, value in zip(node.value.keys, node.value.values):
                if (isinstance(value, ast.Call)
                        and getattr(value.func, "id", None) in HELPERS):
                    out.append((f"{name}[{key.value!r}]", value,
                                live[key.value]))
    return out


def _named_colours() -> set[str]:
    """Every six-digit value this module names -- the bases a composed literal
    could have been written against."""
    return {v.lower() for n, v in vars(colors).items()
            if n.isupper() and isinstance(v, str)
            and re.fullmatch(r"#[0-9a-fA-F]{6}", v)}


def _parts_of(spelled: str) -> tuple[str, int]:
    """(base, alpha byte) for any composed spelling _COMPOSED matches, with
    Qt's own reading of a fractional alpha: it TRUNCATES, so 0.3 is 76."""
    if spelled.startswith("#"):
        return "#" + spelled[3:].lower(), int(spelled[1:3], 16)
    numbers = re.findall(r"[0-9]*\.?[0-9]+", spelled)
    r, g, b = (int(x) for x in numbers[:3])
    a = numbers[3]
    return "#%02x%02x%02x" % (r, g, b), (int(float(a) * 255) if "." in a
                                         else int(a))


def _bare_strings(tree: ast.AST) -> set[int]:
    """ids of every string that is a statement on its own -- a docstring, or
    any other string nobody evaluates. Those are mentions, not uses."""
    bare = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list):
            continue
        for statement in body:
            if (isinstance(statement, ast.Expr)
                    and isinstance(statement.value, ast.Constant)):
                bare.add(id(statement.value))
    return bare


# ------------------------------------------------------------ guard the guard

def test_translucent_composes_alpha_first():
    """#AARRGGBB, not #RRGGBBAA. Taking the wrong end gives a real colour and
    the wrong one, which is the failure that does not look like a failure.

    UPPER CASE, unlike rnv-icon-builder's helper of the same name: the two
    overlays this replaced were written that way, and the locked suite checks
    image window_bg with a case-sensitive startswith('#ED')."""
    assert translucent("#1a1a1a", 0xED) == "#ED1A1A1A"
    assert translucent("1A1A1A", 0xED) == "#ED1A1A1A"
    assert translucent("#d2bc93", 0x33) == "#33D2BC93"


def test_translucent_rgba_is_the_same_colour_in_the_other_spelling():
    assert translucent_rgba("#1a1a1a", 191) == "rgba(26, 26, 26, 191)"
    assert translucent_rgba("#000000", 0xC8) == "rgba(0, 0, 0, 200)"
    for base in ("#1a1a1a", "#d2bc93", "#444444"):
        for alpha in (0, 0x64, 0xED, 255):
            assert (decompose(translucent(base, alpha))
                    == decompose(translucent_rgba(base, alpha))
                    == (base, alpha))


def test_the_helpers_refuse_what_they_cannot_compose():
    for helper in (translucent, translucent_rgba):
        for bad in (-1, 256, 999, 0.5, True):
            try:
                helper("#1a1a1a", bad)
            except (ValueError, TypeError):
                pass
            else:
                raise AssertionError(f"{helper.__name__} took alpha {bad!r}")
        for bad in ("#1a1a1", "#1a1a1a1a", "nonsense", "#gggggg"):
            try:
                helper(bad, 0xED)
            except ValueError:
                pass
            else:
                raise AssertionError(f"{helper.__name__} took base {bad!r}")


def test_the_alphas_are_the_declared_bytes():
    for name, (byte, _was) in ALPHAS.items():
        assert hasattr(colors, name), f"ui.colors has no {name}"
        value = getattr(colors, name)
        assert type(value) is int, f"{name} is {value!r}, not an int byte"
        assert value == byte, f"{name} is {value:#x}, declared {byte:#x}"


def test_the_derivation_sweep_is_looking():
    """Every check below iterates _derived(). If it came back empty they
    would all pass over nothing."""
    where = {w for w, _c, _v in _derived()}
    assert {"APP_WINDOW_OVERLAY", "APP_PANEL_OVERLAY", "SIZE_OVERLAY_BG",
            "DEFAULT_SLOT_COLOR_IMAGE",
            "IMAGE_MODE_COLORS['scrollbar_handle']",
            "IMAGE_MODE_COLORS['scrollbar_border']"} <= where, sorted(where)


# ----------------------------------------------------------- the derivations

def test_every_derived_value_names_constants_that_exist():
    """HELPER(BASE, ALPHA) where both are names. A literal in either position
    is the thing this round removed."""
    bad = []
    for where, call, _value in _derived():
        if len(call.args) != 2 or call.keywords:
            bad.append(f"{where}: {ast.unparse(call)} is not (BASE, ALPHA)")
            continue
        base, alpha = call.args
        for pos, arg in (("base", base), ("alpha", alpha)):
            if not isinstance(arg, ast.Name):
                bad.append(f"{where}: the {pos} is {ast.unparse(arg)}, not a name")
            elif not hasattr(colors, arg.id):
                bad.append(f"{where}: the {pos} names {arg.id}, which ui.colors "
                           f"does not define")
        if isinstance(base, ast.Name) and hasattr(colors, base.id):
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(getattr(colors, base.id))):
                bad.append(f"{where}: the base {base.id} is not a six-digit colour")
        if isinstance(alpha, ast.Name) and alpha.id not in ALPHAS:
            bad.append(f"{where}: the alpha {alpha.id} is not a declared "
                       f"composite alpha")
    assert not bad, "derived values that do not derive:\n  " + "\n  ".join(bad)


def test_every_derived_value_decomposes_to_its_base_and_its_alpha():
    """The relationship, checked by TAKING THE VALUE APART rather than by
    building it again -- the entry IS the helper's output, so recomputing it
    would compare a call with itself."""
    wrong = []
    for where, call, value in _derived():
        base, alpha = call.args
        parts = decompose(value)
        if parts is None:
            wrong.append(f"{where} is {value!r}, which is neither #AARRGGBB "
                         f"nor rgba(r, g, b, a)")
            continue
        want = (getattr(colors, base.id).lower(), getattr(colors, alpha.id))
        if parts != want:
            wrong.append(f"{where} is {value}, which takes apart to "
                         f"{parts}, not {base.id}/{alpha.id} {want}")
    assert not wrong, "derived values that do not match:\n  " + "\n  ".join(wrong)


def test_the_rgba_spelling_is_used_only_where_the_lock_pins_it():
    """rgba() is the one derived spelling QColor() cannot read. It is allowed
    where a locked test demands it and nowhere else -- and the pin is re-read
    from the locked suite, so an exception outlives nothing."""
    used = {where for where, call, _v in _derived()
            if call.func.id == "translucent_rgba"}
    assert used == set(RGBA_PINNED), (
        f"translucent_rgba() is used for {sorted(used)}, pinned for "
        f"{sorted(RGBA_PINNED)}. Anything else takes translucent(), which "
        f"QColor() can read.")
    locked = (ROOT / "test_rnv_palette_manager.py").read_text(encoding="utf-8-sig")
    assert 'assertIn("rgba", SIZE_OVERLAY_BG.lower())' in locked, (
        "the locked suite no longer pins SIZE_OVERLAY_BG to rgba(). Move it to "
        "translucent() and drop it from RGBA_PINNED.")


def test_no_composed_literal_is_left_in_the_application():
    """The completeness half. Every EVALUATED string in the application's own
    source -- not tests, not docstrings, not this round's delivery script --
    that spells a named colour at an alpha. A literal cannot follow its base.

    Alpha 0 is not a colour and is not counted; a base no constant here names
    has no row to follow, and is not counted either -- SELECTION_OVERLAY_COLOR
    is Windows' accent blue, #0078d7, which is a question for the register and
    not a derivation this file can check."""
    named = _named_colours()
    strays, files = [], 0
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if any(p in {".git", "tests", "snapshots", "build", "dist", ".venv",
                     "venv", "__pycache__"} for p in rel.parts):
            continue
        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):
            continue
        text = path.read_bytes().decode("utf-8-sig", errors="replace")
        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
            continue
        tree = ast.parse(text)
        files += 1
        bare = _bare_strings(tree)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            if id(node) in bare:
                continue
            for spelled in _COMPOSED.findall(node.value):
                base, alpha = _parts_of(spelled)
                if alpha == 0 or base not in named:
                    continue
                strays.append(f"{rel}:{node.lineno}  {spelled}  ({base} is "
                              f"named here)")
    # 38 application files on 2026-09-25. Thirty is the floor below which the
    # walk has lost a package, not a file.
    assert files >= 30, f"only {files} files swept -- the walk has gone blind"
    assert not strays, ("composed values still written out rather than "
                        "derived:\n  " + "\n  ".join(strays))


# --------------------------------------------------- what moved, and what not

def test_the_scrollbar_handle_is_grey_44_at_150():
    """RNV-COLLAPSE-505050 and the alpha, both ruled 2026-09-24."""
    assert decompose(IMAGE["scrollbar_handle"]) == (
        colors.GREY_44, colors.SCROLLBAR_HANDLE_ALPHA)
    assert colors.SCROLLBAR_HANDLE_ALPHA == 150
    assert "505050" not in IMAGE["scrollbar_handle"]


def test_nothing_moved_that_was_not_ruled():
    """Each derived value, held to what it is MADE OF: the constant its colour
    comes from and its alpha byte, as of 2026-09-25.

    BY NAME, NOT BY HEX, and that is the point of the round. A register move
    is meant to pass straight through these values; a test that pinned
    '#333333' would fail the first time one did, and ask a person to edit it
    by hand -- the exact job derivation exists to remove. What this DOES catch
    is a value quietly re-made from something else: a different base, or a
    different byte, which the decomposition check above would accept as long
    as the source and the value agreed with each other.

    The byte-for-byte before-and-after -- '#ED000000', '#ED1A1A1A',
    'rgba(0, 0, 0, 200)' -- was checked once, by the delivery script, against
    the edited module before it was written. That is evidence for the round,
    not a rule for the repository."""
    live = {where: value for where, _call, value in _derived()}
    for where, (base, alpha) in MADE_OF.items():
        assert where in live, f"{where} is no longer derived"
        assert decompose(live[where]) == (getattr(colors, base).lower(), alpha), (
            f"{where} is {live[where]}, which is not {base} at {alpha:#04x}")
    # the two spellings the locked suite requires, which any respelling keeps
    assert IMAGE["window_bg"].startswith("#ED")
    assert "rgba" in colors.SIZE_OVERLAY_BG.lower()
    assert IMAGE["window_bg"] == IMAGE["scroll_bg"] == colors.APP_WINDOW_OVERLAY
    assert IMAGE["panel_bg"] == colors.APP_PANEL_OVERLAY


def test_what_qcolor_reads_it_can_read():
    """window_bg and scroll_bg go through QColor() in the main window. #AARRGGBB
    is the one derived spelling QColor() parses; rgba() would come back
    INVALID and paint opaque black."""
    from PyQt6.QtGui import QColor
    for value, alpha in ((IMAGE["window_bg"], 0xED), (IMAGE["scroll_bg"], 0xED),
                         (colors.DEFAULT_SLOT_COLOR_IMAGE, 0xAB)):
        colour = QColor(value)
        assert colour.isValid(), f"QColor({value!r}) is invalid"
        assert colour.alpha() == alpha, f"{value} reads at alpha {colour.alpha()}"

# RNV-DERIVE-ALPHA
