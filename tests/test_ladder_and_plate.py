"""The retired plate, the dark rung, and the translucent overlays.

WHAT THIS PASS DID. rnv-brand retired #d0d0d0 as a light interaction ground and
registered APP["hover-light"] in its place -- first as #e8e8e8 on 2026-08-29,
then as #eeeeee on 2026-08-30. rev 22 had already registered APP["panel-hover"]
#3a3a3a, which was app-owned here. Two light entries change VALUE; everything
else changes only how it is spelled.

THE DEFECT THIS CLOSES. ui/about_dialog.py draws the hover ground from
dialog_btn_hover_bg and the hover label from accent_ink, in the same rule. In
light that was BRAND_DARK_GOLD_DEEP #7e6529 on #d0d0d0 -- 3.6013:1 against a
4.5 floor. It had been wrong as long as the plate existed and carried a STRICT
xfail since 2026-08-28, written so that fixing it would fail the test and force
the note to be rewritten rather than let the exemption outlive the defect.

WHY #eeeeee AND NOT #e8e8e8, WHICH ALSO CLEARS. #e8e8e8 clears by 0.0334 and is
the ground BRAND_DARK_GOLD_DEEP is derived against -- rev 24 registered it as
GOLD_TEXT_GROUND_FLOOR. A plate on that value fails the moment the gold moves
one step: -13 instead of -14 gives 4.4675. #eeeeee clears by 0.2875 and is
grey(14) exactly. A boundary is not a plate.

THE OVERLAYS. Qt spells a translucent colour #AARRGGBB. The 2026-08-29 wiring
pass swept for six-digit literals, so #ED000000 never matched #000000 and three
registered values sat in IMAGE_MODE_COLORS -- a DARK dict here -- while the
guard reported clean.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from ui import colors
from ui.colors import (DARK_THEME_COLORS as DARK,
                       IMAGE_MODE_COLORS as IMAGE,
                       LIGHT_THEME_COLORS as LIGHT)

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'ui/colors.py'

GRID_STEP = 0x11
LADDER_STEP = 0x10
TEXT_FLOOR = 4.5

#: Constant name -> the APP key it mirrors, and the value both hold.
NEW = {
    'APP_PANEL_HOVER': ('panel-hover', '#3a3a3a'),
    'APP_HOVER_LIGHT': ('hover-light', '#eeeeee'),
}

#: Overlay constant -> (the six-digit constant it composites, its APP key).
OVERLAYS = {
    'APP_WINDOW_OVERLAY': ('TRUE_BLACK', 'window'),
    'APP_PANEL_OVERLAY': ('BRAND_BLACK', 'panel'),
}

#: palette dict name -> the keys in it that must now name a constant.
WIRED = {
    'DARK_THEME_COLORS': ('dialog_btn_hover_bg', 'tab_hover_bg'),
    'IMAGE_MODE_COLORS': ('dialog_btn_hover_bg', 'tab_hover_bg',
                          'window_bg', 'panel_bg', 'scroll_bg'),
    'LIGHT_THEME_COLORS': ('dialog_btn_hover_bg', 'tab_hover_bg'),
}

#: dict NAME -> the live dict. Looking a key up in the wrong palette is how a
#: per-mode difference gets checked against the other mode's value and passes.
PALETTES = {'DARK_THEME_COLORS': DARK, 'IMAGE_MODE_COLORS': IMAGE,
            'LIGHT_THEME_COLORS': LIGHT}

#: The value the register retired as a light interaction ground.
RETIRED = '#d0d0d0'

#: The value the plate must not BE, however close it looks.
FLOOR = '#e8e8e8'


def grey(n: int) -> str:
    v = n * GRID_STEP
    return '#%02x%02x%02x' % (v, v, v)


def _luminance(value: str) -> float:
    channels = [int(value.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def _dict_node(name: str) -> ast.Dict:
    tree = ast.parse(SRC.read_text(encoding='utf-8-sig'))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(target, 'id', None) == name and isinstance(node.value, ast.Dict):
                return node.value
    raise AssertionError(f'{name} is not a dict literal in ui/colors.py')


def _entry(node: ast.Dict, key: str):
    for k, v in zip(node.keys, node.values):
        if isinstance(k, ast.Constant) and k.value == key:
            return v
    return None


# ------------------------------------------------------------- guard the guard

def test_everything_this_file_reads_still_exists():
    """Renaming a key must fail loudly here rather than let the rest of this
    file pass quietly over nothing."""
    for name in list(NEW) + list(OVERLAYS):
        assert hasattr(colors, name), f'ui.colors has no {name}'
    for dict_name, keys in WIRED.items():
        assert dict_name in PALETTES, dict_name
        for key in keys:
            assert key in PALETTES[dict_name], f'{dict_name} has no {key!r}'


def test_the_wiring_map_is_not_empty():
    """Every sweep below iterates WIRED. An empty map passes all of them."""
    assert WIRED and all(WIRED.values())
    assert sum(len(v) for v in WIRED.values()) >= 9


# ------------------------------------------------------------------ the value

def test_the_new_constants_hold_the_registered_values():
    """The local half of the mirror. Runs everywhere, including where
    engine.brand is not importable."""
    drift = {n: getattr(colors, n) for n, (_, v) in NEW.items()
             if getattr(colors, n) != v}
    assert not drift, (
        f'these constants no longer hold their registered values: {drift}\n'
        f'If the brand moved, update this file in the same commit that updates '
        f'ui/colors.py -- never one without the other.')


def test_the_new_constants_match_rnv_brand():
    """The upstream half. Skips where rnv-brand is not importable."""
    brand = pytest.importorskip(
        'engine.brand',
        reason='rnv-brand not importable here; the local pin is doing the work')
    drift = []
    for name, (key, _) in NEW.items():
        theirs, mine = brand.APP[key], getattr(colors, name)
        if mine.lower() != theirs.lower():
            drift.append(f'{name}: ours {mine}, theirs APP[{key!r}] {theirs}')
    assert not drift, 'drift from rnv-brand:\n  ' + '\n  '.join(drift)


def test_provenance_is_declared_for_everything_this_pass_named():
    """A classification that lives only in a test drifts from the thing it
    classifies, so it lives in the module and is read from there."""
    for name in NEW:
        assert colors.APP_PROVENANCE.get(name) == 'register', name
    for name in OVERLAYS:
        assert colors.APP_PROVENANCE.get(name) == 'register-overlay', name


# ------------------------------------------------------------- the retirement

def test_the_retired_value_is_gone_from_every_palette():
    """#d0d0d0 is ruled out as a light interaction ground, not merely replaced
    in the two places that prompted the ruling."""
    looked, found = 0, []
    for dict_name, live in PALETTES.items():
        for key, value in live.items():
            if not isinstance(value, str):
                continue
            looked += 1
            if value.lower() == RETIRED:
                found.append(f'{dict_name}[{key!r}]')
    assert looked >= 60, f'only {looked} entries seen -- the sweep is blind'
    assert not found, f'{RETIRED} is retired and still in use: {found}'


def test_gold_carries_on_the_plate_in_every_mode():
    """The defect the strict xfail was holding open. This is the same pairing
    the About dialog makes: the ground from dialog_btn_hover_bg and the label
    from accent_ink, in one rule."""
    failures = []
    for dict_name, live in PALETTES.items():
        ratio = _contrast(live['accent_ink'], live['dialog_btn_hover_bg'])
        if ratio < TEXT_FLOOR:
            failures.append(f'{dict_name}: {live["accent_ink"]} on '
                            f'{live["dialog_btn_hover_bg"]} = {ratio:.4f}')
    assert not failures, 'gold does not carry on the plate:\n  ' + '\n  '.join(failures)


def test_the_plate_is_a_step_on_the_ink_grid():
    assert colors.APP_HOVER_LIGHT == grey(14) == '#eeeeee'


def test_the_plate_is_not_the_gold_text_floor():
    """Both clear the floor. Only one clears it by enough to survive the gold
    moving, and the other is the value the gold is calibrated against."""
    gold = colors.BRAND_DARK_GOLD_DEEP
    here = _contrast(gold, colors.APP_HOVER_LIGHT)
    edge = _contrast(gold, FLOOR)
    assert colors.APP_HOVER_LIGHT.lower() != FLOOR
    assert here - TEXT_FLOOR >= 0.2, (
        f'the plate clears the floor by only {here - TEXT_FLOOR:.4f}. The '
        f'register moved APP["hover-light"] here for margin, not for a pass.')
    assert edge - TEXT_FLOOR < 0.05, (
        f'{FLOOR} now clears by {edge - TEXT_FLOOR:.4f}, so it is no longer the '
        f'knife-edge this ruling was about. Either the gold moved or the floor '
        f'did; re-derive before trusting the value above.')


def test_the_floor_is_not_used_as_a_hover_anywhere():
    """A negative check needs a companion proving it is still looking."""
    looked, found = 0, []
    for dict_name, live in PALETTES.items():
        for key, value in live.items():
            if 'hover' not in key or not isinstance(value, str):
                continue
            looked += 1
            if value.lower() == FLOOR:
                found.append(f'{dict_name}[{key!r}]')
    assert looked >= 6, f'only {looked} hover keys seen -- the sweep is blind'
    assert not found, (
        f'{FLOOR} is being used as a hover plate: {found}. It is '
        f'GOLD_TEXT_GROUND_FLOOR, not an interaction state.')


# ------------------------------------------------------------------ the ladder

def test_the_dark_rungs_are_exact_steps_on_the_ladder():
    """BRAND_BLACK + n * 0x10. #3a3a3a was app-owned on the argument that the
    ladder might not be real. It is, and this is what says so."""
    base = int(colors.BRAND_BLACK.lstrip('#'), 16)
    for n, name in ((0, 'BRAND_BLACK'), (1, 'APP_CARD'), (2, 'APP_PANEL_HOVER')):
        want = base + n * (LADDER_STEP * 0x010101)
        assert int(getattr(colors, name).lstrip('#'), 16) == want, (
            f'{name} is {getattr(colors, name)}, not rung n={n}')


def test_the_border_is_an_edge_and_not_a_rung():
    """The distinction that made the ladder look incomplete. #333333 is grey(3)
    on the ink grid, which governs inks and edges; it was never a surface."""
    assert colors.APP_BORDER == grey(3)
    base = int(colors.BRAND_BLACK.lstrip('#'), 16)
    rungs = {base + n * (LADDER_STEP * 0x010101) for n in range(-1, 3)}
    assert int(colors.APP_BORDER.lstrip('#'), 16) not in rungs


# ---------------------------------------------------------------- the overlays

def test_every_overlay_is_its_base_at_the_declared_alpha():
    """The overlays are written out because Qt wants eight digits and composing
    them would make the palette resolve to an expression. This is the
    relationship composition would have given, asserted instead."""
    for name, (base_name, _key) in OVERLAYS.items():
        overlay = getattr(colors, name)
        base = getattr(colors, base_name)
        assert len(overlay) == 9, f'{name} is {overlay}, not #AARRGGBB'
        assert overlay[1:3].upper() == colors.IMAGE_OVERLAY_ALPHA.upper(), (
            f'{name} composites at {overlay[1:3]}, not IMAGE_OVERLAY_ALPHA')
        assert overlay[3:].lower() == base[1:].lower(), (
            f'{name} is {overlay}, whose colour half is not {base_name} '
            f'{base}. An overlay that stops tracking its base is the exact '
            f'drift this naming exists to prevent.')


def test_every_overlay_base_is_still_a_register_value():
    """Guard the guard. If a base stopped being registered, these would track
    something app-owned under a name that says otherwise."""
    brand = pytest.importorskip('engine.brand', reason='rnv-brand not importable')
    for name, (base_name, key) in OVERLAYS.items():
        assert brand.APP[key].lower() == getattr(colors, base_name).lower(), (
            f'{name} claims to composite APP[{key!r}], which the register now '
            f'holds as {brand.APP[key]}')


def test_no_translucent_register_value_is_left_as_a_literal():
    """The defect this pass fixes, asserted from the other side."""
    registered = {getattr(colors, n).lower()
                  for n in ('TRUE_BLACK', 'WHITE', 'BRAND_BLACK', 'APP_CARD',
                            'APP_BORDER', 'APP_TEXT', 'APP_TEXT_DIM',
                            'APP_PANEL_HOVER', 'APP_HOVER_LIGHT')}
    found = []
    for dict_name in PALETTES:
        node = _dict_node(dict_name)
        for k, v in zip(node.keys, node.values):
            if (isinstance(v, ast.Constant) and isinstance(v.value, str)
                    and len(v.value) == 9 and v.value.startswith('#')
                    and '#' + v.value[3:].lower() in registered):
                found.append(f'{dict_name}[{k.value!r}] = {v.value}')
    assert not found, (
        'registered values still spelled as translucent literals:\n  '
        + '\n  '.join(found))


# ------------------------------------------------- the spelling, not the value

def test_every_wired_entry_names_a_constant_not_a_literal():
    """A literal cannot follow its base."""
    allowed = set(NEW) | set(OVERLAYS)
    literals = []
    for dict_name, keys in WIRED.items():
        node = _dict_node(dict_name)
        for key in keys:
            value = _entry(node, key)
            if not isinstance(value, ast.Name) or value.id not in allowed:
                literals.append(
                    f'{dict_name}[{key!r}] = '
                    f'{ast.unparse(value) if value else "missing"}')
    assert not literals, (
        'entries still written as literals:\n  ' + '\n  '.join(literals))


def test_the_resolved_values_are_the_constants():
    """The AST check proves the spelling; this proves the value."""
    for dict_name, keys in WIRED.items():
        node = _dict_node(dict_name)
        for key in keys:
            name = _entry(node, key).id
            assert PALETTES[dict_name][key] == getattr(colors, name), (
                f'{dict_name}[{key!r}] resolves to '
                f'{PALETTES[dict_name][key]}, not {name}')
