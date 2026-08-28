"""
The APP register, the ink move, and the tab keys sorted out.

FOUR THINGS LAND TOGETHER HERE, and they are one job rather than four: every
one of them is about a name or a value that was not telling the truth.

1. THE APP REGISTER IS NAMED. #e0e0e0, #1a1a1a, #2a2a2a and #333333 were bare
   literals with no constant and no provenance, and every one is a REGISTERED
   value in RNVizion/rnv-brand. APP["text"] moved to #dddddd in
   rnv-brand@68d195e and nothing here would have noticed.

2. THE DARK INK MOVES TO grey(13). The published grid is
   grey(n) = n * 0x11, TRUE_BLACK -> WHITE in fifteen steps. It governs inks
   and edges and deliberately not surfaces. #e0e0e0 was one hex doing two
   jobs -- dark ink and a LIGHT SURFACE -- which is the only reason it looked
   like an exception. Only the ink half moved.

3. THE TAB KEYS SAY WHAT THEY DO. This app paints its tabs from card_bg (rest
   and hover) and panel_bg (selected), in BOTH dialogs. So `tab_bg` and
   `tab_selected` were never consumed, and `tab_hover` was consumed to fill a
   QPushButton. The first two are kept and annotated -- rnv-color-picker and
   rnv-icon-builder paint from the equivalents and the values here already
   agree with them -- and renamed to those apps' spelling. The third became
   `dialog_btn_hover_bg`, which is what it always was.

4. THE TWO DIALOGS AGREE ABOUT THE PANE. `tab_pane_bg` is deleted. About and
   Settings drew their tab pane from different keys, and in light that made
   About's pane #ffffff -- the same as card_bg, so a card on it had nothing
   but its own border. In image it made the pane fully opaque, the one surface
   in that dialog opting out of image mode. ui/about_dialog.py already carried
   the right answer as its fallback:

       pane_bg = theme.get('tab_pane_bg', theme['panel_bg'])

   Deleting the key makes that fallback the live path. The override point does
   not disappear -- it IS the .get() -- so a dialog that wants a distinct pane
   adds the key back and nothing else changes.

TWO GUARDS, NOT ONE. rnv-text-transformer's mirror test guards with
importorskip('engine.brand'), so where rnv-brand is not importable it reports
clean and drift hides. Every register value is pinned LOCALLY as well as
mirrored UPSTREAM.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from ui import colors
from ui.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,
                       LIGHT_THEME_COLORS as LIGHT)

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'ui' / 'colors.py'
ABOUT = ROOT / 'ui' / 'about_dialog.py'

GRID_STEP = 0x11

PALETTES = {'DARK': DARK, 'LIGHT': LIGHT, 'IMAGE': IMAGE}

PINNED = {
    'TRUE_BLACK': '#000000',
    'WHITE': '#ffffff',
    'BRAND_BLACK': '#1a1a1a',
    'APP_CARD': '#2a2a2a',
    'APP_BORDER': '#333333',
    'APP_TEXT': '#dddddd',
    'APP_TEXT_DIM': '#aaaaaa',
}

#: Dark and image ink. These carry APP_TEXT and must reference it by name.
INK_KEYS = ('text_color', 'button_text', 'button_hover_text')

#: Unconsumed here, live in the other two apps, values already agreed.
UNCONSUMED_TAB_KEYS = ('tab_bg', 'tab_selected_bg', 'tab_hover_bg')

#: The About dialog's button hover plate, per mode. Unchanged values; only the
#: name moved off `tab_hover`.
DIALOG_BTN_HOVER = {'DARK': '#3a3a3a', 'LIGHT': '#d0d0d0', 'IMAGE': '#3a3a3a'}


def grey(n: int) -> str:
    v = n * GRID_STEP
    return '#%02x%02x%02x' % (v, v, v)


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

def test_the_names_this_file_reads_still_exist():
    """Every assertion below reads these. Rename one and this fails loudly
    instead of the rest quietly passing over nothing."""
    for name in PINNED:
        assert hasattr(colors, name), f'ui.colors has no {name}'
    for mode, palette in PALETTES.items():
        for key in INK_KEYS + UNCONSUMED_TAB_KEYS + ('dialog_btn_hover_bg',):
            assert key in palette, f'{mode} has no {key}'


# ------------------------------------------------------------------- the value

def test_the_ink_is_a_step_on_the_grid():
    assert colors.APP_TEXT == grey(13) == '#dddddd', (
        f'APP_TEXT is {colors.APP_TEXT}, not grey(13).')


def test_every_pinned_neutral_is_what_the_register_held():
    """The local half of the mirror. Runs everywhere."""
    drift = {n: getattr(colors, n) for n, v in PINNED.items()
             if getattr(colors, n) != v}
    assert not drift, (
        f'these constants no longer hold their registered values: {drift}\n'
        f'If the brand moved, update PINNED in the same commit that updates '
        f'ui/colors.py -- never one without the other.')


def test_register_values_match_rnv_brand():
    """The upstream half. Skips where rnv-brand is absent, which is exactly
    why the pin above is not optional."""
    brand = pytest.importorskip(
        'engine.brand',
        reason='rnv-brand not importable here; the local pin is doing the work')
    drift = []
    for name in PINNED:
        theirs = (brand.APP[name[4:].lower().replace('_', '-')]
                  if name.startswith('APP_') else getattr(brand, name))
        if getattr(colors, name).lower() != theirs.lower():
            drift.append(f'{name}: ours {getattr(colors, name)}, theirs {theirs}')
    assert not drift, 'drift from rnv-brand:\n  ' + '\n  '.join(drift)


def test_every_dark_and_image_ink_reads_the_constant_not_a_literal():
    """A literal cannot follow its base. If APP_TEXT moves again these move
    with it, or this fails."""
    literals = []
    for dict_name, mode in (('DARK_THEME_COLORS', 'DARK'),
                            ('IMAGE_MODE_COLORS', 'IMAGE')):
        node = _dict_node(dict_name)
        for key in INK_KEYS:
            value = _entry(node, key)
            if not (isinstance(value, ast.Name) and value.id == 'APP_TEXT'):
                literals.append(
                    f'{mode}.{key} = '
                    f'{ast.unparse(value) if value is not None else "missing"}')
    assert not literals, ('ink entries still written as literals:\n  '
                          + '\n  '.join(literals))


def test_the_resolved_ink_is_the_constant():
    for mode in ('DARK', 'IMAGE'):
        for key in INK_KEYS:
            assert PALETTES[mode][key] == colors.APP_TEXT, f'{mode}[{key!r}]'


def test_the_light_surfaces_did_not_follow_the_ink():
    """#e0e0e0's other half is a LIGHT SURFACE, and the grid does not govern
    surfaces. hover_color and tab_bg stay exactly where they were."""
    assert LIGHT['hover_color'] == '#e0e0e0'
    assert LIGHT['tab_bg'] == '#e0e0e0'


def test_the_light_ink_is_true_black():
    """Primary text is one role with two mode values: dark is a grey on the
    grid, light is TRUE_BLACK."""
    assert LIGHT['text_color'] == colors.TRUE_BLACK == '#000000'


# ------------------------------------------------------------------ the tabs

def _consumers(key: str) -> list[str]:
    """Where a theme key is read outside the palette file and the tests."""
    sites = []
    for path in ROOT.rglob('*.py'):
        parts = path.parts
        if any(p in parts for p in ('.git', '__pycache__', 'tests')):
            continue
        if path.name.startswith('test_') or path == SRC:
            continue
        # A delivery script at the root names the keys it moves. Sweeping it
        # makes this guard fail on the very run that installs it.
        if path.parent == ROOT and path.name.startswith('up'):
            continue
        text = path.read_text(encoding='utf-8-sig', errors='replace')
        for lineno, line in enumerate(text.splitlines(), 1):
            if f"'{key}'" in line or f'"{key}"' in line:
                sites.append(f'{path.relative_to(ROOT)}:{lineno}')
    return sites


@pytest.mark.parametrize('key', UNCONSUMED_TAB_KEYS)
def test_the_tab_keys_are_still_unconsumed(key):
    """They are kept because picker and icon-builder paint from the
    equivalents and these values already agree. The note beside them only
    helps while it is true: wire one up and this says so."""
    sites = _consumers(key)
    assert not sites, (
        f'{key} is now read at {sites}. It is annotated NOT CONSUMED in '
        f'ui/colors.py -- update the note in the same commit.')


def test_the_tab_keys_carry_the_note_that_says_so():
    """Both halves of the arrangement, held together. The values are correct
    and the note explains why they are not painted."""
    src = SRC.read_text(encoding='utf-8-sig')
    assert src.count('NOT CONSUMED') >= 4, (
        'the NOT CONSUMED notes are gone -- text_secondary had three and the '
        'tab block adds one')


def test_the_tabs_are_actually_painted_from_the_surfaces():
    """What the keys above are NOT doing, something else is. Both dialogs
    fill a tab from card_bg and the selected one from the pane."""
    for path in (ABOUT, ROOT / 'ui' / 'settings_dialog.py'):
        text = path.read_text(encoding='utf-8-sig')
        assert 'QTabBar::tab' in text, f'{path.name} no longer styles tabs'
        assert 'card_bg' in text, (
            f'{path.name} no longer reads card_bg -- if the tabs were wired to '
            f'the tab_* keys, those keys are no longer unconsumed')


def test_the_dialog_button_hover_kept_its_value_and_gained_its_name():
    """A rename, not a retune. `tab_hover` filled a QPushButton; the value did
    not change when the name stopped saying 'tab'."""
    for mode, expected in DIALOG_BTN_HOVER.items():
        assert PALETTES[mode]['dialog_btn_hover_bg'] == expected, mode


def test_the_dialog_button_hover_is_not_the_main_button_scheme():
    """Deliberately not button_hover_bg. That is the MAIN button's inverse
    scheme -- #333333 in both modes with the label flipping. Dialog buttons
    take a softer plate with gold text and border. Flattening the two would
    lose a scheme."""
    for mode, palette in PALETTES.items():
        assert palette['dialog_btn_hover_bg'] != palette['button_hover_bg'], (
            f'{mode}: the dialog button hover has been flattened onto the main '
            f'button hover')


# -------------------------------------------------------------------- the pane

def test_tab_pane_bg_is_gone_from_every_palette():
    for mode, palette in PALETTES.items():
        assert 'tab_pane_bg' not in palette, (
            f'{mode} still defines tab_pane_bg. It was deleted because it held '
            f'nothing panel_bg does not; if a dialog needs a distinct pane, '
            f'that is a decision to make on purpose, with a value and a note.')


def test_the_about_dialog_still_resolves_a_pane():
    """Guard the guard for the deletion: the fallback must still be there, or
    the key is gone AND the override point with it."""
    text = ABOUT.read_text(encoding='utf-8-sig')
    assert "theme.get('tab_pane_bg', theme['panel_bg'])" in text, (
        'the fallback that makes the deletion safe is gone from '
        'ui/about_dialog.py')


def test_both_dialogs_now_draw_the_same_pane():
    """The point of the deletion. Whatever About resolves must equal what
    Settings uses, in every mode."""
    for mode, palette in PALETTES.items():
        resolved = palette.get('tab_pane_bg', palette['panel_bg'])
        assert resolved == palette['panel_bg'], mode


def test_the_light_pane_is_no_longer_the_card_colour():
    """What the alignment bought. About's pane was #ffffff, the same as
    card_bg, so a card sitting on it had only its own border."""
    resolved = LIGHT.get('tab_pane_bg', LIGHT['panel_bg'])
    assert resolved != LIGHT['card_bg'], (
        'the light pane is the card colour again')
    assert resolved == '#f5f5f5'


def test_the_image_pane_is_translucent_like_the_rest_of_image_mode():
    """It was fully opaque #1a1a1a -- the one surface in that dialog opting
    out of image mode."""
    resolved = IMAGE.get('tab_pane_bg', IMAGE['panel_bg'])
    assert resolved.upper().startswith('#ED'), (
        f'the image pane is {resolved}, which is opaque')


# ---------------------------------------------------------------- what it costs

def _luminance(value: str) -> float:
    h = value.lstrip('#')
    if len(h) == 8:
        h = h[2:]
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def _contrast(a: str, b: str) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_the_ink_clears_the_text_floor_on_every_dark_ground_it_touches():
    grounds = ('#000000', '#1a1a1a', '#2a2a2a', '#333333', '#3a3a3a', '#444444')
    worst = min((_contrast(colors.APP_TEXT, g), g) for g in grounds)
    assert worst[0] >= 4.5, (
        f'the ink falls to {worst[0]:.2f}:1 on {worst[1]}, under the 4.5 floor')


# ------------------------------------------------------- one defect, recorded

@pytest.mark.xfail(
    strict=True,
    reason='KNOWN DEFECT, pre-existing and out of scope for the 2026-08-28 ink '
           'pass. Light gold text on the dialog button hover plate is 3.60:1, '
           'under the 4.5 floor. It surfaced only because naming the plate '
           'brought it into an audit for the first time -- it has been wrong '
           'as long as the plate has existed. Awaiting a ruling: either the '
           'plate moves above #e8e8e8, or the hover label stops being gold. '
           'Marked strict so fixing it FAILS this test and forces the note to '
           'be updated rather than quietly outliving the defect.')
def test_gold_text_clears_the_dialog_button_hover_plate():
    """The pairing is real: ui/about_dialog.py sets the hover ground from
    dialog_btn_hover_bg and the hover label from accent_ink, in the same rule.

        DARK   #d2bc93 on #3a3a3a   6.15  passes
        IMAGE  #d2bc93 on #3a3a3a   6.15  passes
        LIGHT  #7e6529 on #d0d0d0   3.60  FAILS

    rnv-brand publishes the reason: below #e8e8e8, gold does not carry text.
    #d0d0d0 is well below it. That is a ruling, not a gap, so the plate is
    what is wrong here rather than the floor.
    """
    for mode, palette in PALETTES.items():
        ratio = _contrast(palette['accent_ink'], palette['dialog_btn_hover_bg'])
        assert ratio >= 4.5, (
            f'{mode}: {palette["accent_ink"]} on '
            f'{palette["dialog_btn_hover_bg"]} = {ratio:.2f}:1')
