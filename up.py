"""every colour named, and every name used: the palette manager's unread palette keys and constants go

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-color-palette-manager, derived against a fresh clone at the live head (7c41ed6).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-04, items 6 to 9 of decisions-pending-2026-09-29.md:

  "As long as a color exist in the app it should be named and used no
   hardcoded or pointless literals should exist, only literals with a
   purpose, like data or comparison are allowed. Colors are name for swap
   ability and alignment."

USED. Nine palette keys no mode read go from all three palettes:
accent_text, dialog_border, hover_color, main_btn_border_color, success,
tab_bg, tab_hover_bg, tab_selected_bg, warning. With them go the NOT
CONSUMED notes above the tab keys and the two tests that held those keys
unread. The image palette was the dark one written out a second time with
seven entries changed. It is the dark palette under its own name now, with
the six entries image mode reads and draws differently. The seventh,
input_bg at the card colour, was a difference nothing drew: its one reader
is the settings dialog, which takes the dark palette in image mode. Five
constants nothing in the application read go: GREY_E0, STATUS_SUCCESS,
STATUS_WARNING, STATUS_ERROR and DEFAULT_SLOT_COLOR_IMAGE.

NAMED. One colour value was written out in the code: the alpha a new slot
takes in image mode, 171, beside SLOT_IMAGE_ALPHA, which holds that byte.
It is read from the name. The settings' comment beside the image-mode
default said "black (semi-transparent)"; what is stored is opaque black,
and the comment now says where the transparency comes from.

PROVEN BEFORE BUILDING. No line of the application looks up any of the nine
keys, on any receiver. Every window, tab and combo in every mode draws what
it drew, and every stylesheet and palette entry the application reads holds
what it held.

FOUND ON THE WAY, AND NOT CHANGED. Two tests said this application paints
black on its light gold fill, and read accent_text to say it. Nothing read
that key. The application paints WHITE there, in four places. The tests now
measure what is drawn; whether light should take black is a ruling.
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
SENTINEL = 'RNV-NAMED-AND-USED'
SENTINEL_FILE = 'ui/colors.py'
GUARD = 'tests/test_named_and_used.py'
GUARD_FILES = ['tests/test_named_and_used.py', 'tests/test_app_mirror.py', 'tests/test_brand_mirror.py', 'tests/test_button_key_names.py', 'tests/test_collapse_505050.py', 'tests/test_contrast_pairs.py', 'tests/test_derived_values.py', 'tests/test_error_red.py', 'tests/test_ladder_and_plate.py', 'tests/test_muted_and_disabled_text.py', 'tests/test_status_register.py', 'tests/test_surface_alignment.py']
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_named_and_used.py', 'tests/test_app_mirror.py', 'tests/test_brand_mirror.py', 'tests/test_button_key_names.py', 'tests/test_collapse_505050.py', 'tests/test_contrast_pairs.py', 'tests/test_derived_values.py', 'tests/test_error_red.py', 'tests/test_ladder_and_plate.py', 'tests/test_muted_and_disabled_text.py', 'tests/test_status_register.py', 'tests/test_surface_alignment.py']
DESCRIPTION = "every colour named, and every name used: the palette manager's unread palette keys and constants go"

#: EXACTLY WHAT CI RUNS. Both workflows run `python run_tests.py`, which runs
#: the locked root suite under unittest and then tests/ under pytest.
SUITES = [("python run_tests.py  (both CI workflows)",
           [sys.executable, "run_tests.py"])]

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '898c16b8a02fa92b09c1bed0fa1f9f8b872d2d3d29d506b7a9c9a1ec357de42e', '.github/workflows/tests.yml': '5d3891f82137b62cb3b2576454eb30079ee981ca559fac90d67431f579e5abe5'}

SHADOWS = {"colors.py", "conftest.py", "run_tests.py", "theme_manager.py", "settings_dialog.py", "settings_manager.py", "test_rnv_palette_manager.py"}

LEFT_ALONE = ['the ink on the gold fill: black in dark and image, WHITE in light, written where it is used. The register prefers black on gold; changing light is a ruling of its own.', "the CSS colour names a search understands, the examples the settings show, safe_rgb()'s fallback and a cluster's starting sums: data, each listed with its reason in the guard's DATA table.", "image mode's entries as KEYS: they come through the spread with dark's values, read where image mode reads them and unwritten where it does not.", 'tab_pane_bg, read with a fallback and held by no palette: an override point, as tests/test_app_mirror.py records.', 'the allowance for a GREY_E0 split in tests/test_light_wiring.py: a table the fleet shares, naming pairs this application may never hold.', "clear: 'transparent', alpha 0 and Qt's transparent are how a widget is told to paint nothing, and are left as written."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('ui/colors.py',
             '# ==================== Dark Theme Colors ====================\nDARK_THEME_COLORS: Final[ThemeDict] = {\n    \'name\': \'Dark\',\n    # Base colors\n    \'window_bg\': TRUE_BLACK,\n    \'panel_bg\': BRAND_BLACK,\n    \'scroll_bg\': TRUE_BLACK,\n    \'card_bg\': APP_CARD,\n    \'input_bg\': BRAND_BLACK,\n    # Text\n    \'text_color\': APP_TEXT,\n    # Muted text. Kept aligned while nothing painted it, so that wiring it up\n    # would be one line and not a colour decision -- and on 2026-09-27 it was\n    # (RNV-MUTED-DESCRIPTIONS, ruling 1): the settings and batch export\n    # dialogs\' notes, previews and empty history, named "muted_text" in each\n    # dialog\'s stylesheet. They were `color: grey`, #808080 in every mode.\n    \'text_secondary\': GREY_88,\n    \'text_disabled\': GREY_55,\n    # Borders\n    \'border_color\': APP_BORDER,\n    \'hover_color\': GREY_44,\n    # Buttons\n    \'main_btn_bg\': BRAND_BLACK,\n    \'main_btn_text\': APP_TEXT,\n    \'main_btn_hover_bg\': APP_BORDER,\n    \'main_btn_hover_text\': APP_TEXT,\n    \'main_btn_pressed_bg\': GREY_44,\n    \'main_btn_pressed_text\': TRUE_BLACK,\n    \'main_btn_border_color\': \'transparent\',\n    # The About dialog\'s button hover plate. Spelled \'tab_hover\' until\n    # 2026-08-28, where it filled a QPushButton and not a tab.\n    #\n    # Deliberately NOT main_btn_hover_bg. That is the MAIN button\'s inverse\n    # scheme -- #333333 in both modes, with the label flipping -- while dialog\n    # buttons take a softer plate carrying gold text and a gold border.\n    # Flattening the two would lose a scheme. Same value it always had.\n    \'dialog_btn_hover_bg\': APP_PANEL_HOVER,\n    # The plate and label a dialog button RESTS on. Added 2026-09-01,\n    # holding what these dialogs already painted -- before this they\n    # reached into the main family for both, which is why one name\n    # ended up describing two schemes.\n    \'dialog_btn_bg\': BRAND_BLACK,\n    \'dialog_btn_text\': APP_TEXT,\n    # Dialog / tab widget colors\n    #\n    # NOT CONSUMED -- all three of these. This app paints its tabs from\n    # card_bg (at rest AND on hover, so hovering an unselected tab changes\n    # only the label) and from panel_bg for the selected one, in both\n    # ui/about_dialog.py and ui/settings_dialog.py.\n    #\n    # Kept rather than deleted, on the same reasoning as text_secondary above:\n    # rnv-color-picker and rnv-icon-builder DO paint from the equivalents, and\n    # the values here already agree with them -- tab_bg matches both apps, and\n    # tab_selected_bg matches rnv-icon-builder (rnv-color-picker uses the panel\n    # step #1a1a1a instead, a two-against-one this pass records and does not\n    # settle). So wiring them up stays one line and not a colour decision.\n    #\n    # RENAMED 2026-08-28 to the spelling those two apps use. `tab_hover` left\n    # this block entirely: it was consumed, but to fill a QPushButton, and it\n    # is now dialog_btn_hover_bg in the button section above.\n    \'tab_bg\': APP_CARD,\n    \'tab_selected_bg\': APP_BORDER,\n    \'tab_hover_bg\': APP_PANEL_HOVER,\n    \'scroll_handle\': GREY_44,   # was #505050, see GREY_44\n    # Accent (brand gold)\n    \'accent\': BRAND_GOLD,\n    \'accent_dark\': BRAND_GOLD_HOVER,\n    \'accent_ink\': BRAND_GOLD,\n    \'accent_text\': TRUE_BLACK,\n    # Scrollbar\n    \'scrollbar_bg\': BRAND_BLACK,\n    \'scrollbar_handle\': GREY_44,   # was #505050, see GREY_44\n    \'scrollbar_handle_hover\': BRAND_GOLD,\n    \'scrollbar_border\': APP_BORDER,\n    # Dialog\n    \'dialog_bg\': BRAND_BLACK,\n    \'dialog_border\': APP_BORDER,\n    # Status\n    \'success\': STATUS_SUCCESS,\n    \'warning\': STATUS_WARNING,\n}\n\n\n',
             '# ==================== Dark Theme Colors ====================\n# RNV-NAMED-AND-USED (2026-10-04): a palette holds what is looked up. Nine\n# keys nothing read went from all three palettes: a hover, the three tab\n# keys and the note that called them not consumed, two status fills, a\n# dialog border, an ink for the accent, and a main-button border written\n# as transparent while the button draws its border from border_color.\nDARK_THEME_COLORS: Final[ThemeDict] = {\n    \'name\': \'Dark\',\n    # Base colors\n    \'window_bg\': TRUE_BLACK,\n    \'panel_bg\': BRAND_BLACK,\n    \'scroll_bg\': TRUE_BLACK,\n    \'card_bg\': APP_CARD,\n    \'input_bg\': BRAND_BLACK,\n    # Text\n    \'text_color\': APP_TEXT,\n    # Muted text. Kept aligned while nothing painted it, so that wiring it up\n    # would be one line and not a colour decision -- and on 2026-09-27 it was\n    # (RNV-MUTED-DESCRIPTIONS, ruling 1): the settings and batch export\n    # dialogs\' notes, previews and empty history, named "muted_text" in each\n    # dialog\'s stylesheet. They were `color: grey`, #808080 in every mode.\n    \'text_secondary\': GREY_88,\n    \'text_disabled\': GREY_55,\n    # Borders\n    \'border_color\': APP_BORDER,\n    # Buttons\n    \'main_btn_bg\': BRAND_BLACK,\n    \'main_btn_text\': APP_TEXT,\n    \'main_btn_hover_bg\': APP_BORDER,\n    \'main_btn_hover_text\': APP_TEXT,\n    \'main_btn_pressed_bg\': GREY_44,\n    \'main_btn_pressed_text\': TRUE_BLACK,\n    # The About dialog\'s button hover plate. Spelled \'tab_hover\' until\n    # 2026-08-28, where it filled a QPushButton and not a tab.\n    #\n    # Deliberately NOT main_btn_hover_bg. That is the MAIN button\'s inverse\n    # scheme -- #333333 in both modes, with the label flipping -- while dialog\n    # buttons take a softer plate carrying gold text and a gold border.\n    # Flattening the two would lose a scheme. Same value it always had.\n    \'dialog_btn_hover_bg\': APP_PANEL_HOVER,\n    # The plate and label a dialog button RESTS on. Added 2026-09-01,\n    # holding what these dialogs already painted -- before this they\n    # reached into the main family for both, which is why one name\n    # ended up describing two schemes.\n    \'dialog_btn_bg\': BRAND_BLACK,\n    \'dialog_btn_text\': APP_TEXT,\n    # The About dialog\'s scroll handle\n    \'scroll_handle\': GREY_44,   # was #505050, see GREY_44\n    # Accent (brand gold)\n    \'accent\': BRAND_GOLD,\n    \'accent_dark\': BRAND_GOLD_HOVER,\n    \'accent_ink\': BRAND_GOLD,\n    # Scrollbar\n    \'scrollbar_bg\': BRAND_BLACK,\n    \'scrollbar_handle\': GREY_44,   # was #505050, see GREY_44\n    \'scrollbar_handle_hover\': BRAND_GOLD,\n    \'scrollbar_border\': APP_BORDER,\n    # Dialog\n    \'dialog_bg\': BRAND_BLACK,\n}\n\n\n')
    tree.sub('ui/colors.py',
             "# ==================== Light Theme Colors ====================\nLIGHT_THEME_COLORS: Final[ThemeDict] = {\n    'name': 'Light',\n    # Base colors\n    'window_bg': APP_SURFACE_LIGHT_3,\n    'panel_bg': APP_SURFACE_LIGHT_3,\n    'scroll_bg': GREY_EE,\n    'card_bg': WHITE,\n    'input_bg': WHITE,\n    # Text\n    'text_color': TRUE_BLACK,\n    # Muted text -- see the note in the dark palette.\n    'text_secondary': GREY_66,\n    'text_disabled': APP_TEXT_DIM,\n    # Borders\n    'border_color': GREY_CC,\n    'hover_color': GREY_E0,\n    # Buttons: white base, dark-grey hover/press, white text on press, no visible border\n    'main_btn_bg': WHITE,\n    'main_btn_text': TRUE_BLACK,\n    'main_btn_hover_bg': APP_BORDER,\n    'main_btn_hover_text': TRUE_BLACK,\n    'main_btn_pressed_bg': GREY_44,\n    'main_btn_pressed_text': WHITE,\n    'main_btn_border_color': 'transparent',\n    # The About dialog's button hover plate. Spelled 'tab_hover' until\n    # 2026-08-28, where it filled a QPushButton and not a tab.\n    #\n    # Deliberately NOT main_btn_hover_bg. That is the MAIN button's inverse\n    # scheme -- #333333 in both modes, with the label flipping -- while dialog\n    # buttons take a softer plate carrying gold text and a gold border.\n    # Flattening the two would lose a scheme. Same value it always had.\n    'dialog_btn_hover_bg': APP_HOVER_LIGHT,\n    # The plate and label a dialog button RESTS on. Added 2026-09-01,\n    # holding what these dialogs already painted -- before this they\n    # reached into the main family for both, which is why one name\n    # ended up describing two schemes.\n    'dialog_btn_bg': WHITE,\n    'dialog_btn_text': TRUE_BLACK,\n    # Dialog / tab widget colors\n    #\n    # NOT CONSUMED -- all three of these. This app paints its tabs from\n    # card_bg (at rest AND on hover, so hovering an unselected tab changes\n    # only the label) and from panel_bg for the selected one, in both\n    # ui/about_dialog.py and ui/settings_dialog.py.\n    #\n    # Kept rather than deleted, on the same reasoning as text_secondary above:\n    # rnv-color-picker and rnv-icon-builder DO paint from the equivalents, and\n    # the values here already agree with them -- tab_bg matches both apps, and\n    # tab_selected_bg matches rnv-icon-builder (rnv-color-picker uses the panel\n    # step #1a1a1a instead, a two-against-one this pass records and does not\n    # settle). So wiring them up stays one line and not a colour decision.\n    #\n    # RENAMED 2026-08-28 to the spelling those two apps use. `tab_hover` left\n    # this block entirely: it was consumed, but to fill a QPushButton, and it\n    # is now dialog_btn_hover_bg in the button section above.\n    'tab_bg': GREY_E0,\n    'tab_selected_bg': WHITE,\n    'tab_hover_bg': APP_HOVER_LIGHT,\n    'scroll_handle': APP_TEXT_DIM,\n    # Accent (brand gold - darker variant for readability on light bg)\n    'accent': BRAND_DARK_GOLD,\n    'accent_dark': BRAND_DARK_GOLD,\n    'accent_ink': BRAND_DARK_GOLD_DEEP,\n    'accent_text': TRUE_BLACK,\n    # Scrollbar\n    'scrollbar_bg': APP_SURFACE_LIGHT_3,\n    'scrollbar_handle': APP_TEXT_DIM,\n    'scrollbar_handle_hover': BRAND_DARK_GOLD,\n    'scrollbar_border': GREY_CC,\n    # Dialog\n    'dialog_bg': APP_SURFACE_LIGHT_3,\n    'dialog_border': GREY_CC,\n    # Status\n    'success': STATUS_SUCCESS,\n    'warning': STATUS_WARNING,\n}\n\n\n",
             "# ==================== Light Theme Colors ====================\nLIGHT_THEME_COLORS: Final[ThemeDict] = {\n    'name': 'Light',\n    # Base colors\n    'window_bg': APP_SURFACE_LIGHT_3,\n    'panel_bg': APP_SURFACE_LIGHT_3,\n    'scroll_bg': GREY_EE,\n    'card_bg': WHITE,\n    'input_bg': WHITE,\n    # Text\n    'text_color': TRUE_BLACK,\n    # Muted text -- see the note in the dark palette.\n    'text_secondary': GREY_66,\n    'text_disabled': APP_TEXT_DIM,\n    # Borders\n    'border_color': GREY_CC,\n    # Buttons: white base, dark-grey hover/press, white text on press\n    'main_btn_bg': WHITE,\n    'main_btn_text': TRUE_BLACK,\n    'main_btn_hover_bg': APP_BORDER,\n    'main_btn_hover_text': TRUE_BLACK,\n    'main_btn_pressed_bg': GREY_44,\n    'main_btn_pressed_text': WHITE,\n    # The About dialog's button hover plate. Spelled 'tab_hover' until\n    # 2026-08-28, where it filled a QPushButton and not a tab.\n    #\n    # Deliberately NOT main_btn_hover_bg. That is the MAIN button's inverse\n    # scheme -- #333333 in both modes, with the label flipping -- while dialog\n    # buttons take a softer plate carrying gold text and a gold border.\n    # Flattening the two would lose a scheme. Same value it always had.\n    'dialog_btn_hover_bg': APP_HOVER_LIGHT,\n    # The plate and label a dialog button RESTS on. Added 2026-09-01,\n    # holding what these dialogs already painted -- before this they\n    # reached into the main family for both, which is why one name\n    # ended up describing two schemes.\n    'dialog_btn_bg': WHITE,\n    'dialog_btn_text': TRUE_BLACK,\n    # The About dialog's scroll handle\n    'scroll_handle': APP_TEXT_DIM,\n    # Accent (brand gold - darker variant for readability on light bg)\n    'accent': BRAND_DARK_GOLD,\n    'accent_dark': BRAND_DARK_GOLD,\n    'accent_ink': BRAND_DARK_GOLD_DEEP,\n    # Scrollbar\n    'scrollbar_bg': APP_SURFACE_LIGHT_3,\n    'scrollbar_handle': APP_TEXT_DIM,\n    'scrollbar_handle_hover': BRAND_DARK_GOLD,\n    'scrollbar_border': GREY_CC,\n    # Dialog\n    'dialog_bg': APP_SURFACE_LIGHT_3,\n}\n\n\n")
    tree.sub('ui/colors.py',
             "# ==================== Image Mode Colors ====================\n# Based on Dark theme with transparency for background overlay effect.\nIMAGE_MODE_COLORS: Final[ThemeDict] = {\n    'name': 'Image',\n    # Base colors -- alpha-prefixed hex for Qt stylesheet compatibility\n    'window_bg': APP_WINDOW_OVERLAY,\n    'panel_bg': APP_PANEL_OVERLAY,\n    'scroll_bg': APP_WINDOW_OVERLAY,\n    'card_bg': APP_CARD,\n    'input_bg': APP_CARD,\n    # Text\n    'text_color': APP_TEXT,\n    # Muted text -- see the note in the dark palette.\n    'text_secondary': GREY_88,\n    'text_disabled': GREY_55,\n    # Borders\n    'border_color': APP_BORDER,\n    'hover_color': GREY_44,\n    # Buttons\n    'main_btn_bg': BRAND_BLACK,\n    'main_btn_text': APP_TEXT,\n    'main_btn_hover_bg': APP_BORDER,\n    'main_btn_hover_text': APP_TEXT,\n    'main_btn_pressed_bg': GREY_44,\n    'main_btn_pressed_text': TRUE_BLACK,\n    'main_btn_border_color': 'transparent',\n    # The About dialog's button hover plate. Spelled 'tab_hover' until\n    # 2026-08-28, where it filled a QPushButton and not a tab.\n    #\n    # Deliberately NOT main_btn_hover_bg. That is the MAIN button's inverse\n    # scheme -- #333333 in both modes, with the label flipping -- while dialog\n    # buttons take a softer plate carrying gold text and a gold border.\n    # Flattening the two would lose a scheme. Same value it always had.\n    'dialog_btn_hover_bg': APP_PANEL_HOVER,\n    # The plate and label a dialog button RESTS on. Added 2026-09-01,\n    # holding what these dialogs already painted -- before this they\n    # reached into the main family for both, which is why one name\n    # ended up describing two schemes.\n    'dialog_btn_bg': BRAND_BLACK,\n    'dialog_btn_text': APP_TEXT,\n    # Dialog / tab widget colors\n    #\n    # NOT CONSUMED -- all three of these. This app paints its tabs from\n    # card_bg (at rest AND on hover, so hovering an unselected tab changes\n    # only the label) and from panel_bg for the selected one, in both\n    # ui/about_dialog.py and ui/settings_dialog.py.\n    #\n    # Kept rather than deleted, on the same reasoning as text_secondary above:\n    # rnv-color-picker and rnv-icon-builder DO paint from the equivalents, and\n    # the values here already agree with them -- tab_bg matches both apps, and\n    # tab_selected_bg matches rnv-icon-builder (rnv-color-picker uses the panel\n    # step #1a1a1a instead, a two-against-one this pass records and does not\n    # settle). So wiring them up stays one line and not a colour decision.\n    #\n    # RENAMED 2026-08-28 to the spelling those two apps use. `tab_hover` left\n    # this block entirely: it was consumed, but to fill a QPushButton, and it\n    # is now dialog_btn_hover_bg in the button section above.\n    'tab_bg': APP_CARD,\n    'tab_selected_bg': APP_BORDER,\n    'tab_hover_bg': APP_PANEL_HOVER,\n    'scroll_handle': GREY_44,   # was #505050, see GREY_44\n    # Accent (brand gold)\n    'accent': BRAND_GOLD,\n    'accent_dark': BRAND_GOLD_HOVER,\n    'accent_ink': BRAND_GOLD,\n    'accent_text': TRUE_BLACK,\n    # Scrollbar. The two composites are DERIVED -- a named colour at a\n    # declared alpha -- so a register move reaches them.\n    'scrollbar_bg': 'transparent',\n    # RNV-COLLAPSE-505050, closed in this palette 2026-09-25. This read\n    # rgba(80, 80, 80, 100) -- the retired value at alpha 100 -- three\n    # weeks after the ruling, while tests/test_collapse_505050.py\n    # reported it gone: nothing here decoded rgba(). The alpha moves\n    # to 150 with it, the byte the other four image scrollbars use.\n    'scrollbar_handle': translucent(GREY_44, SCROLLBAR_HANDLE_ALPHA),\n    'scrollbar_handle_hover': BRAND_GOLD,\n    'scrollbar_border': translucent(APP_BORDER, SCROLLBAR_BORDER_ALPHA),\n    # Dialog\n    'dialog_bg': BRAND_BLACK,\n    'dialog_border': APP_BORDER,\n    # Status\n    'success': STATUS_SUCCESS,\n    'warning': STATUS_WARNING,\n}\n\n\n",
             "# ==================== Image Mode Colors ====================\n# The dark palette under its own name, with what image mode draws differently.\n#\n# RNV-NAMED-AND-USED (2026-10-04): this was the dark palette written out a\n# second time, entry by entry, with seven of them changed. Most of the copy\n# was a second spelling of values image mode never looked up, and one of the\n# seven was a difference nothing drew: input_bg, at APP_CARD, whose one\n# reader is the settings dialog, and that dialog takes the dark palette in\n# image mode. So this is dark's values, and after the spread the six entries\n# image mode reads and draws differently. A key image mode looks up is always\n# there, and nothing it never reads is written.\nIMAGE_MODE_COLORS: Final[ThemeDict] = {\n    **DARK_THEME_COLORS,\n    'name': 'Image',\n    # Base colors -- alpha-prefixed hex for Qt stylesheet compatibility\n    'window_bg': APP_WINDOW_OVERLAY,\n    'panel_bg': APP_PANEL_OVERLAY,\n    'scroll_bg': APP_WINDOW_OVERLAY,\n    # Scrollbar. The two composites are DERIVED -- a named colour at a\n    # declared alpha -- so a register move reaches them.\n    'scrollbar_bg': 'transparent',\n    # RNV-COLLAPSE-505050, closed in this palette 2026-09-25. This read\n    # rgba(80, 80, 80, 100) -- the retired value at alpha 100 -- three\n    # weeks after the ruling, while tests/test_collapse_505050.py\n    # reported it gone: nothing here decoded rgba(). The alpha moves\n    # to 150 with it, the byte the other four image scrollbars use.\n    'scrollbar_handle': translucent(GREY_44, SCROLLBAR_HANDLE_ALPHA),\n    'scrollbar_border': translucent(APP_BORDER, SCROLLBAR_BORDER_ALPHA),\n}\n\n\n")
    tree.sub('ui/colors.py',
             'GREY_E0: Final[str] = "#e0e0e0"\n"""grey(14) on the ramp, #e0e0e0. Static surfaces that share a hex with\nAPP_PRESSED_LIGHT without being a pressed state. See the split note\nthere. Named by its byte, like every other ramp step."""\n\n',
             '# RNV-NAMED-AND-USED (2026-10-04): a ramp step at #e0e0e0 stood here, for two\n# light keys nothing read. It went with them.\n\n')
    tree.sub('ui/colors.py',
             '    "GREY_E0": "app-ramp",\n',
             '')
    tree.sub('ui/colors.py',
             '# ==================== Status Colors ====================\nSTATUS_SUCCESS: Final[str] = "#926c89"\n"""MIRRORS the register\'s STATUS["success"]. A FILL.\n\nRNV-STATUS-FAMILY (2026-09-03): was #28a745, Bootstrap\'s green. Retired\nbecause it and Bootstrap\'s red collapsed to one olive under deuteranopia at\nabout 4 apart -- roughly 8% of men could not tell success from error, which\nare the two most consequential colours in an interface.\n\nIt is a FILL and cannot carry text: 3.92 on #1a1a1a, 3.23 on #2a2a2a. That is\nthe fill band, not a shortcoming -- a value that clears 3:1 on a dark AND a\nlight ground sits at L* 48-59 by arithmetic, and a mid-tone reaches 4.5:1 on\nneither side. This application already knew that for the red and spent two\nvalues on it; the register has now generalised it to all three roles.\n\nRNV-STATUS-REGISTER (2026-09-02): the three palettes wrote #4caf50,\nMaterial\'s green, as a literal. Two applications held that value for one\nrole while the other three used the register\'s. Named here so the value\nhas one home, and collapsed onto the register so the fleet has one green."""\n\nSTATUS_WARNING: Final[str] = "#a2703c"\n"""MIRRORS the register\'s STATUS["warning"]. A FILL.\n\nRNV-STATUS-FAMILY (2026-09-03): was #ffc107, retired on arithmetic rather\nthan taste -- 1.63 on #ffffff and 1.49 on #f5f5f5 against a 3:1 fill floor.\nIt could not legally carry a boundary on a light ground at all."""\n\nSTATUS_ERROR: Final[str] = "#c75b64"\n"""The registered error red. Not drawn by this app, which renders no error\nfill -- it is here so the family has its base and so the two text values\nbelow are visibly siblings of it rather than free-standing reds.\n\nRNV-STATUS-FAMILY (2026-09-03): was #dc3545, Bootstrap\'s. IT IS NO LONGER\nWHAT THE LIGHT VALUE IS DERIVED FROM -- see STATUS_ERROR_TEXT_LIGHT."""\n\n',
             '# ==================== Status Colors ====================\n# RNV-NAMED-AND-USED (2026-10-04): the family\'s three fills stood here --\n# success, warning and the error red the two text values below are siblings\n# of. This application draws error TEXT and no status fill, and nothing read\n# the three, so it carries none: the register holds them, as STATUS["success"],\n# STATUS["warning"] and STATUS["error"].\n\n')
    tree.sub('ui/colors.py',
             'DEFAULT_SLOT_COLOR_IMAGE: Final[str] = translucent(TRUE_BLACK, SLOT_IMAGE_ALPHA)\n"""Default color for new color slots in Image mode (semi-transparent black).\nTRUE_BLACK at SLOT_IMAGE_ALPHA: the colour it always was, in the one\nspelling QColor() can read as well as a stylesheet."""\n\nDEFAULT_SLOT_COLOR_IMAGE_RGB: Final[tuple[int, int, int, int]] = translucent_tuple(\n    TRUE_BLACK, SLOT_IMAGE_ALPHA)\n"""Default slot color in Image mode as RGBA tuple: DEFAULT_SLOT_COLOR_IMAGE\'s\ncolour and alpha, in the spelling QColor(*t) takes."""\n',
             'DEFAULT_SLOT_COLOR_IMAGE_RGB: Final[tuple[int, int, int, int]] = translucent_tuple(\n    TRUE_BLACK, SLOT_IMAGE_ALPHA)\n"""Default color for new color slots in Image mode (semi-transparent black):\nTRUE_BLACK at SLOT_IMAGE_ALPHA, in the spelling QColor(*t) takes.\n\nRNV-NAMED-AND-USED (2026-10-04): the same colour stood beside this as an\neight-digit hex string, and nothing read it. This is the spelling the slot\nreads; where a slot\'s colour comes from the settings, the main window sets\nSLOT_IMAGE_ALPHA on it."""\n')
    tree.sub('ui/colors.py',
             'DEFAULT_SLOT_COLOR_IMAGE_RGB spells the same colour as an integer tuple, and\nsince 2026-09-26 it is derived from the same pair (RNV-TUPLE-ROUND)."""\n',
             'DEFAULT_SLOT_COLOR_IMAGE_RGB is TRUE_BLACK at this byte, derived from the pair\nsince 2026-09-26 (RNV-TUPLE-ROUND); and the main window sets this byte on a\nslot colour that comes from the settings."""\n')
    tree.sub('ui/colors.py',
             '    "DEFAULT_SLOT_COLOR",\n    "DEFAULT_SLOT_COLOR_IMAGE",\n',
             '    "DEFAULT_SLOT_COLOR",\n')
    tree.sub('ui/colors.py',
             '    "STATUS_SUCCESS",\n    "STATUS_WARNING",\n    "STATUS_ERROR",\n',
             '')
    tree.sub('RNV_Color_Palette_Manager.py',
             '    SIZE_OVERLAY_BG, SESSION_FALLBACK_COLOR, TRANSPARENT_RGBA,\n)\n',
             '    SIZE_OVERLAY_BG, SESSION_FALLBACK_COLOR, TRANSPARENT_RGBA,\n    SLOT_IMAGE_ALPHA,\n)\n')
    tree.sub('RNV_Color_Palette_Manager.py',
             '            # Image mode uses semi-transparent version\n            color.setAlpha(171)\n',
             '            # Image mode uses semi-transparent version.\n            # RNV-NAMED-AND-USED (2026-10-04): was 171, written out; the same byte.\n            color.setAlpha(SLOT_IMAGE_ALPHA)\n')
    tree.sub('test_rnv_palette_manager.py',
             '    REQUIRED = [\n        "window_bg","panel_bg","scroll_bg","card_bg","input_bg",\n        "text_color","text_secondary","text_disabled",\n        "border_color","hover_color",\n        "main_btn_bg","main_btn_text","main_btn_hover_bg","main_btn_hover_text",\n        "main_btn_pressed_bg","main_btn_pressed_text","main_btn_border_color",\n        "accent","accent_dark","accent_text",\n        "tab_bg","tab_selected_bg","tab_hover_bg",\n        "dialog_btn_hover_bg",\n        "scroll_handle","dialog_bg","dialog_border",\n        "success","warning",\n    ]\n',
             '    # RNV-NAMED-AND-USED 2026-10-04: nine keys nothing read went from the\n    # palettes, and from this list with them. Ruled: "for the locked key test\n    # if we don\'t use these values we can fix the test and remove unused values".\n    REQUIRED = [\n        "window_bg","panel_bg","scroll_bg","card_bg","input_bg",\n        "text_color","text_secondary","text_disabled",\n        "border_color",\n        "main_btn_bg","main_btn_text","main_btn_hover_bg","main_btn_hover_text",\n        "main_btn_pressed_bg","main_btn_pressed_text",\n        "accent","accent_dark",\n        "dialog_btn_hover_bg",\n        "scroll_handle","dialog_bg",\n    ]\n')
    tree.sub('tests/test_app_mirror.py',
             "3. THE TAB KEYS SAY WHAT THEY DO. This app paints its tabs from card_bg (rest\n   and hover) and panel_bg (selected), in BOTH dialogs. So `tab_bg` and\n   `tab_selected` were never consumed, and `tab_hover` was consumed to fill a\n   QPushButton. The first two are kept and annotated -- rnv-color-picker and\n   rnv-icon-builder paint from the equivalents and the values here already\n   agree with them -- and renamed to those apps' spelling. The third became\n   `dialog_btn_hover_bg`, which is what it always was.\n",
             '3. THE TAB KEYS SAY WHAT THEY DO. This app paints its tabs from card_bg (rest\n   and hover) and panel_bg (selected), in BOTH dialogs. So `tab_bg` and\n   `tab_selected` were never consumed, and `tab_hover` was consumed to fill a\n   QPushButton. The third became `dialog_btn_hover_bg`, which is what it\n   always was. The first two were kept, renamed and annotated NOT CONSUMED\n   until RNV-NAMED-AND-USED, 2026-10-04, when it was ruled that a palette\n   holds what is used: they went, with the hover key beside them, the note,\n   and the tests here that held them unread.\n')
    tree.sub('tests/test_app_mirror.py',
             "#: Unconsumed here, live in the other two apps, values already agreed.\nUNCONSUMED_TAB_KEYS = ('tab_bg', 'tab_selected_bg', 'tab_hover_bg')\n\n",
             '')
    tree.sub('tests/test_app_mirror.py',
             "        for key in INK_KEYS + UNCONSUMED_TAB_KEYS + ('dialog_btn_hover_bg',):\n",
             "        for key in INK_KEYS + ('dialog_btn_hover_bg',):\n")
    tree.sub('tests/test_app_mirror.py',
             'def test_every_dark_and_image_ink_reads_the_constant_not_a_literal():\n    """A literal cannot follow its base. If APP_TEXT moves again these move\n    with it, or this fails."""\n    literals = []\n    for dict_name, mode in ((\'DARK_THEME_COLORS\', \'DARK\'),\n                            (\'IMAGE_MODE_COLORS\', \'IMAGE\')):\n        node = _dict_node(dict_name)\n        for key in INK_KEYS:\n            value = _entry(node, key)\n            if not (isinstance(value, ast.Name) and value.id == \'APP_TEXT\'):\n                literals.append(\n                    f\'{mode}.{key} = \'\n                    f\'{ast.unparse(value) if value is not None else "missing"}\')\n    assert not literals, (\'ink entries still written as literals:\\n  \'\n                          + \'\\n  \'.join(literals))\n',
             'def test_every_dark_and_image_ink_reads_the_constant_not_a_literal():\n    """A literal cannot follow its base. If APP_TEXT moves again these move\n    with it, or this fails.\n\n    RNV-NAMED-AND-USED, 2026-10-04: the image palette is the dark one under\n    its own name -- `{**DARK_THEME_COLORS, ...}` -- so its ink arrives through\n    the spread. What is held for image is that it spreads the dark palette\n    and no other, and that an ink written after the spread is still the\n    constant."""\n    literals = []\n    node = _dict_node(\'DARK_THEME_COLORS\')\n    for key in INK_KEYS:\n        value = _entry(node, key)\n        if not (isinstance(value, ast.Name) and value.id == \'APP_TEXT\'):\n            literals.append(\n                f\'DARK.{key} = \'\n                f\'{ast.unparse(value) if value is not None else "missing"}\')\n    node = _dict_node(\'IMAGE_MODE_COLORS\')\n    spreads = [ast.unparse(v) for k, v in zip(node.keys, node.values) if k is None]\n    assert spreads == [\'DARK_THEME_COLORS\'], (\n        f\'IMAGE_MODE_COLORS spreads {spreads}, not the dark palette alone\')\n    for key in INK_KEYS:\n        value = _entry(node, key)\n        if value is not None and not (isinstance(value, ast.Name)\n                                      and value.id == \'APP_TEXT\'):\n            literals.append(f\'IMAGE.{key} = {ast.unparse(value)}\')\n    assert not literals, (\'ink entries still written as literals:\\n  \'\n                          + \'\\n  \'.join(literals))\n')
    tree.sub('tests/test_app_mirror.py',
             'def test_the_light_surfaces_did_not_follow_the_ink():\n    """#e0e0e0\'s other half is a LIGHT SURFACE, and the grid does not govern\n    surfaces. hover_color and tab_bg stay exactly where they were."""\n    assert LIGHT[\'hover_color\'] == \'#e0e0e0\'\n    assert LIGHT[\'tab_bg\'] == \'#e0e0e0\'\n\n\n',
             '# RNV-NAMED-AND-USED, 2026-10-04: a test stood here holding two light\n# surfaces at #e0e0e0 while the ink moved off it. Nothing read either key, so\n# no surface was drawn from them; they went, and the test with them.\n\n\n')
    tree.sub('tests/test_app_mirror.py',
             'def _consumers(key: str) -> list[str]:\n    """Where a theme key is read outside the palette file and the tests."""\n    sites = []\n    for path in ROOT.rglob(\'*.py\'):\n        parts = path.parts\n        if any(p in parts for p in (\'.git\', \'__pycache__\', \'tests\')):\n            continue\n        if path.name.startswith(\'test_\') or path == SRC:\n            continue\n        # A delivery script at the root names the keys it moves. Sweeping it\n        # makes this guard fail on the very run that installs it.\n        if path.parent == ROOT and path.name.startswith(\'up\'):\n            continue\n        text = path.read_text(encoding=\'utf-8-sig\', errors=\'replace\')\n        for lineno, line in enumerate(text.splitlines(), 1):\n            if f"\'{key}\'" in line or f\'"{key}"\' in line:\n                sites.append(f\'{path.relative_to(ROOT)}:{lineno}\')\n    return sites\n\n\n@pytest.mark.parametrize(\'key\', UNCONSUMED_TAB_KEYS)\ndef test_the_tab_keys_are_still_unconsumed(key):\n    """They are kept because picker and icon-builder paint from the\n    equivalents and these values already agree. The note beside them only\n    helps while it is true: wire one up and this says so."""\n    sites = _consumers(key)\n    assert not sites, (\n        f\'{key} is now read at {sites}. It is annotated NOT CONSUMED in \'\n        f\'ui/colors.py -- update the note in the same commit.\')\n\n\ndef test_the_tab_keys_carry_the_note_that_says_so():\n    """Both halves of the arrangement, held together. The values are correct\n    and the note explains why they are not painted -- one note above the tab\n    keys in each of the three palettes.\n\n    Counted across the whole file until 2026-09-27, as four or more: three\n    beside text_secondary and the tab block\'s. text_secondary is painted now\n    (RNV-MUTED-DESCRIPTIONS, ruling 1) and its notes went with it, so this\n    measures the tab block\'s own, where they stand."""\n    lines = SRC.read_text(encoding=\'utf-8-sig\').splitlines()\n    rows = [i for i, line in enumerate(lines) if line.strip().startswith("\'tab_bg\':")]\n    assert len(rows) == 3, f\'expected tab_bg in three palettes, found lines {rows}\'\n    for i in rows:\n        assert \'NOT CONSUMED\' in \'\\n\'.join(lines[max(0, i - 20):i]), (\n            f\'the tab keys at line {i + 1} lost the note that says they are \'\n            f\'not painted\')\n\n\n',
             '# RNV-NAMED-AND-USED, 2026-10-04: two tests stood here. One held the three\n# tab keys unread, the other held the note beside them that said so. The\n# keys and the note went: a palette holds what is used, and a list of what\n# is not used keeps nothing.\n\n\n')
    tree.sub('tests/test_app_mirror.py',
             '    """What the keys above are NOT doing, something else is. Both dialogs\n    fill a tab from card_bg and the selected one from the pane."""\n    for path in (ABOUT, ROOT / \'ui\' / \'settings_dialog.py\'):\n        text = path.read_text(encoding=\'utf-8-sig\')\n        assert \'QTabBar::tab\' in text, f\'{path.name} no longer styles tabs\'\n        assert \'card_bg\' in text, (\n            f\'{path.name} no longer reads card_bg -- if the tabs were wired to \'\n            f\'the tab_* keys, those keys are no longer unconsumed\')\n',
             '    """Both dialogs fill a tab from card_bg and the selected one from the\n    pane. There are no tab keys: the surfaces are what a tab is drawn from."""\n    for path in (ABOUT, ROOT / \'ui\' / \'settings_dialog.py\'):\n        text = path.read_text(encoding=\'utf-8-sig\')\n        assert \'QTabBar::tab\' in text, f\'{path.name} no longer styles tabs\'\n        assert \'card_bg\' in text, (\n            f\'{path.name} no longer reads card_bg, the surface its tabs are \'\n            f\'drawn from\')\n')
    tree.sub('tests/test_brand_mirror.py',
             'def test_text_on_gold_is_black_and_stays_black():\n    """This is the only one of the five that paints black on the light fill.\n    It is what the register prefers and the better number. Not to be flattened\n    to match the others."""\n    for name, palette in PALETTES.items():\n        assert palette["accent_text"] == "#000000", name\n    assert contrast("#000000", PALETTES["LIGHT"]["accent"]) >= 4.5\n',
             'def test_text_on_gold_clears_in_every_mode():\n    """What is painted on the gold fill: black in dark and image, WHITE in\n    light. Both clear the floor at this gold.\n\n    RNV-NAMED-AND-USED, 2026-10-04. This was\n    test_text_on_gold_is_black_and_stays_black. It read accent_text, #000000\n    in all three palettes, and said this application is the one of the five\n    that paints black on the light fill. Nothing read that key. The pressed\n    states in the main window, the settings and batch export dialogs and the\n    message boxes write their ink themselves: TRUE_BLACK in dark and image,\n    WHITE in light. So the key went, and this measures what is drawn, read\n    from the code that draws it. Whether light should take black, which the\n    register prefers, is a ruling and not this test\'s to make."""\n    root = pathlib.Path(C.__file__).resolve().parent.parent\n    inks = set()\n    for rel in ("RNV_Color_Palette_Manager.py", "ui/settings_dialog.py",\n                "ui/batch_export_dialog.py", "utils/dialog_helper.py"):\n        tree = ast.parse((root / rel).read_text(encoding="utf-8-sig"))\n        found = {ast.unparse(node.value) for node in ast.walk(tree)\n                 if isinstance(node, ast.Assign) and len(node.targets) == 1\n                 and getattr(node.targets[0], "id", "").endswith("pressed_text")}\n        assert found, f"{rel} no longer writes a pressed ink"\n        inks |= found\n    assert inks == {"WHITE", "TRUE_BLACK", "WHITE if is_light else TRUE_BLACK"}, (\n        f"the ink on a pressed gold fill is written as {sorted(inks)}")\n    for name in ("DARK", "IMAGE"):\n        assert contrast(C.TRUE_BLACK, PALETTES[name]["accent"]) >= 4.5, name\n    assert contrast(C.WHITE, PALETTES["LIGHT"]["accent"]) >= 4.5\n')
    tree.sub('tests/test_button_key_names.py',
             'NEW = tuple("main_" + n.replace("button_", "btn_") for n in OLD)\n',
             '#: RNV-NAMED-AND-USED, 2026-10-04: the main family as the application reads\n#: it. The rename carried seven names across; the seventh, a border colour\n#: written as transparent, was read by nothing -- the main button draws its\n#: border from border_color -- and went.\nNEW = tuple("main_" + n.replace("button_", "btn_") for n in OLD[:-1])\n')
    tree.sub('tests/test_button_key_names.py',
             '             "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#000000",\n             "main_btn_border_color": "transparent"},\n    "light": {"main_btn_bg": "#ffffff", "main_btn_text": "#000000",\n              "main_btn_hover_bg": "#333333", "main_btn_hover_text": "#000000",\n              "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#ffffff",\n              "main_btn_border_color": "transparent"},\n    "image": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",\n              "main_btn_hover_bg": "#333333", "main_btn_hover_text": "#dddddd",\n              "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#000000",\n              "main_btn_border_color": "transparent"},\n}\n',
             '             "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#000000"},\n    "light": {"main_btn_bg": "#ffffff", "main_btn_text": "#000000",\n              "main_btn_hover_bg": "#333333", "main_btn_hover_text": "#000000",\n              "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#ffffff"},\n    "image": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",\n              "main_btn_hover_bg": "#333333", "main_btn_hover_text": "#dddddd",\n              "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#000000"},\n}\n')
    tree.sub('tests/test_collapse_505050.py',
             '        entries = {k.value: v for k, v in zip(node.keys, node.values)\n                   if isinstance(k, ast.Constant)}\n        for key in keys:\n            value = entries.get(key)\n            assert value is not None, f"{mode} has no {key}"\n',
             '        entries = {k.value: v for k, v in zip(node.keys, node.values)\n                   if isinstance(k, ast.Constant)}\n        # RNV-NAMED-AND-USED, 2026-10-04: the image palette is the dark one\n        # under its own name. An entry that arrives through the spread is\n        # written in the palette it is spread from, and is read there.\n        for k, v in zip(node.keys, node.values):\n            if k is None:\n                spread = nodes[ast.unparse(v)]\n                for k2, v2 in zip(spread.keys, spread.values):\n                    if isinstance(k2, ast.Constant):\n                        entries.setdefault(k2.value, v2)\n        for key in keys:\n            value = entries.get(key)\n            assert value is not None, f"{mode} has no {key}"\n')
    tree.sub('tests/test_collapse_505050.py',
             '    assert looked >= 100, f"only {looked} palette entries seen -- the sweep is blind"\n',
             '    # 84 since RNV-NAMED-AND-USED, 2026-10-04: nine keys nothing read went\n    # from each of the three palettes.\n    assert looked >= 84, f"only {looked} palette entries seen -- the sweep is blind"\n')
    tree.sub('tests/test_contrast_pairs.py',
             'def test_white_and_black_on_the_gold_fill():\n    """Both clear at the new value; the register prefers black and this app\n    uses it. Recorded so a future change cannot quietly drop below the floor."""\n    for theme, palette in PALETTES.items():\n        assert contrast(palette["accent_text"], palette["accent"]) >= TEXT_FLOOR, theme\n',
             'def test_white_and_black_on_the_gold_fill():\n    """Both clear at the new value. Recorded so a future change cannot quietly\n    drop below the floor.\n\n    RNV-NAMED-AND-USED, 2026-10-04: this read accent_text, a key nothing\n    painted from, and said the application uses black. It paints black on\n    the gold in dark and image and WHITE on it in light; each is measured on\n    the fill it is drawn on. tests/test_brand_mirror.py reads the two inks\n    from the code that writes them."""\n    for theme, palette in PALETTES.items():\n        ink = C.WHITE if theme == "LIGHT" else C.TRUE_BLACK\n        assert contrast(ink, palette["accent"]) >= TEXT_FLOOR, theme\n')
    tree.sub('tests/test_derived_values.py',
             '    "SIZE_OVERLAY_BG": ("TRUE_BLACK", 0xC8),\n    "DEFAULT_SLOT_COLOR_IMAGE": ("TRUE_BLACK", 0xAB),\n',
             '    "SIZE_OVERLAY_BG": ("TRUE_BLACK", 0xC8),\n')
    tree.sub('tests/test_derived_values.py',
             '    assert {"APP_WINDOW_OVERLAY", "APP_PANEL_OVERLAY", "SIZE_OVERLAY_BG",\n            "DEFAULT_SLOT_COLOR_IMAGE",\n            "IMAGE_MODE_COLORS[\'scrollbar_handle\']",\n',
             '    assert {"APP_WINDOW_OVERLAY", "APP_PANEL_OVERLAY", "SIZE_OVERLAY_BG",\n            "IMAGE_MODE_COLORS[\'scrollbar_handle\']",\n')
    tree.sub('tests/test_derived_values.py',
             '    """window_bg and scroll_bg go through QColor() in the main window. #AARRGGBB\n    is the one derived spelling QColor() parses; rgba() would come back\n    INVALID and paint opaque black."""\n    from PyQt6.QtGui import QColor\n    for value, alpha in ((IMAGE["window_bg"], 0xED), (IMAGE["scroll_bg"], 0xED),\n                         (colors.DEFAULT_SLOT_COLOR_IMAGE, 0xAB)):\n        colour = QColor(value)\n        assert colour.isValid(), f"QColor({value!r}) is invalid"\n        assert colour.alpha() == alpha, f"{value} reads at alpha {colour.alpha()}"\n',
             '    """window_bg and scroll_bg go through QColor() in the main window. #AARRGGBB\n    is the one derived spelling QColor() parses; rgba() would come back\n    INVALID and paint opaque black.\n\n    RNV-NAMED-AND-USED, 2026-10-04: a new slot\'s default in image mode was\n    held here as an eight-digit string nothing read. A slot reads the tuple,\n    QColor(*DEFAULT_SLOT_COLOR_IMAGE_RGB), so the tuple is what is held."""\n    from PyQt6.QtGui import QColor\n    for value, alpha in ((IMAGE["window_bg"], 0xED), (IMAGE["scroll_bg"], 0xED)):\n        colour = QColor(value)\n        assert colour.isValid(), f"QColor({value!r}) is invalid"\n        assert colour.alpha() == alpha, f"{value} reads at alpha {colour.alpha()}"\n    slot = QColor(*colors.DEFAULT_SLOT_COLOR_IMAGE_RGB)\n    assert slot.isValid() and slot.alpha() == colors.SLOT_IMAGE_ALPHA == 0xAB, (\n        f"a new slot in image mode reads at alpha {slot.alpha()}")\n')
    tree.sub('tests/test_error_red.py',
             '    STATUS_ERROR             #c75b64   registered base; no fill is drawn here\n    STATUS_ERROR_TEXT        #dd6f77   dark ground, = register error-text\n',
             '    STATUS_ERROR_TEXT        #dd6f77   dark ground, = register error-text\n')
    tree.sub('tests/test_error_red.py',
             '    open question with the brand chat, and narrowing it is recorded here in\n    full rather than quietly done.\n"""\n',
             '    open question with the brand chat, and narrowing it is recorded here in\n    full rather than quietly done.\n\nRNV-NAMED-AND-USED, 2026-10-04. This application draws error TEXT and no\nstatus fill, so it no longer carries the family\'s three fills -- success,\nwarning and the registered error base #c75b64 -- which nothing here read.\nThe two text values above are what it draws and what this file holds.\nWhere a test needs the base, to say why the light value is not derived from\nit, it writes the base as the register holds it.\n"""\n')
    tree.sub('tests/test_error_red.py',
             '    assert colors.STATUS_ERROR_TEXT_LIGHT == "#ae4650"\n    assert colors.STATUS_ERROR_TEXT_LIGHT != colors.lighten(colors.STATUS_ERROR, -20)\n',
             '    assert colors.STATUS_ERROR_TEXT_LIGHT == "#ae4650"\n    # the registered base, STATUS["error"]; this application draws no fill and carries none\n    assert colors.STATUS_ERROR_TEXT_LIGHT != colors.lighten("#c75b64", -20)\n')
    tree.sub('tests/test_error_red.py',
             '    """Pinned by value. A test asserting only that these differ from each\n    other would pass on five wrong colours."""\n    assert colors.STATUS_SUCCESS == "#926c89"\n    assert colors.STATUS_WARNING == "#a2703c"\n    assert colors.STATUS_ERROR == "#c75b64"\n    assert colors.STATUS_ERROR_TEXT == "#dd6f77"\n',
             '    """Pinned by value. A test asserting only that these differ from each\n    other would pass on two wrong colours. The two this application draws:\n    the family\'s three fills are the register\'s, and are not carried here."""\n    assert colors.STATUS_ERROR_TEXT == "#dd6f77"\n')
    tree.sub('tests/test_error_red.py',
             'def test_the_fills_cannot_carry_text_and_that_is_why_there_are_five_values():\n    """The arithmetic behind the family\'s shape.\n\n    STATUS_SUCCESS, STATUS_WARNING and STATUS_ERROR are fills. Every fill in\n    the family sits at L* 48-59, which is exactly what lets ONE value clear\n    3:1 on a dark AND a light ground -- and a mid-tone reaches 4.5:1 on\n    neither. This application already knew that for the red and spent two\n    values on it before the register generalised it.\n\n    If any fill ever clears the text floor, the register has moved it out of\n    the band and somebody needs to know rather than quietly benefiting.\n    """\n    for name in ("STATUS_SUCCESS", "STATUS_WARNING", "STATUS_ERROR"):\n        value = getattr(colors, name)\n        for ground in ("#1a1a1a", "#2a2a2a", "#f5f5f5", "#ffffff"):\n            assert contrast(value, ground) >= 3.0, f"{name} on {ground}"\n            assert contrast(value, ground) < TEXT_FLOOR, (\n                f"{name} now clears the text floor on {ground}. Do not relax "\n                f"this -- find out whether the register moved it.")\n\n\n',
             "# RNV-NAMED-AND-USED, 2026-10-04: a test stood here on the arithmetic of the\n# three fills -- that each clears 3:1 on both grounds and 4.5:1 on neither.\n# This application draws no fill and no longer carries them; the arithmetic\n# is the register's, where the fills are.\n\n\n")
    tree.sub('tests/test_ladder_and_plate.py',
             "WIRED = {\n    'DARK_THEME_COLORS': ('dialog_btn_hover_bg', 'tab_hover_bg'),\n    'IMAGE_MODE_COLORS': ('dialog_btn_hover_bg', 'tab_hover_bg',\n                          'window_bg', 'panel_bg', 'scroll_bg'),\n    'LIGHT_THEME_COLORS': ('dialog_btn_hover_bg', 'tab_hover_bg'),\n}\n",
             "#: RNV-NAMED-AND-USED, 2026-10-04: the tab hover went with the other keys\n#: nothing read, and the image palette is the dark one under its own name,\n#: so its plate is dark's entry and is held there. What image writes for\n#: itself are the three overlays.\nWIRED = {\n    'DARK_THEME_COLORS': ('dialog_btn_hover_bg',),\n    'IMAGE_MODE_COLORS': ('window_bg', 'panel_bg', 'scroll_bg'),\n    'LIGHT_THEME_COLORS': ('dialog_btn_hover_bg',),\n}\n")
    tree.sub('tests/test_ladder_and_plate.py',
             '    assert sum(len(v) for v in WIRED.values()) >= 9\n',
             '    assert sum(len(v) for v in WIRED.values()) >= 5\n')
    tree.sub('tests/test_muted_and_disabled_text.py',
             '    assert len(beside) == 3, f"expected text_secondary in three palettes, found {beside}"\n',
             '    # two since RNV-NAMED-AND-USED, 2026-10-04: the image palette is the dark\n    # one under its own name, and takes dark\'s entry through the spread.\n    assert len(beside) == 2, f"expected text_secondary in two palettes, found {beside}"\n')
    tree.sub('tests/test_status_register.py',
             '    # an app that picks its own status colour has an opinion\n    # about what success means, which is the register\'s job.\n    assert colors.STATUS_SUCCESS == "#926c89"\n    assert colors.STATUS_WARNING == "#a2703c"\n    assert colors.STATUS_ERROR == "#c75b64"\n',
             "    # an app that picks its own status colour has an opinion\n    # about what success means, which is the register's job.\n    # RNV-NAMED-AND-USED, 2026-10-04: the three fills were pinned\n    # here. This application draws none of them and no longer\n    # carries them; what it draws is the error text below.\n")
    tree.sub('tests/test_status_register.py',
             'def test_the_palettes_are_wired_through_the_constants_not_rewritten():\n    """Swapping one literal for another passes the value check and defeats\n    the point: the constant is what a later register change moves."""\n    src = (ROOT / "ui" / "colors.py").read_text(encoding="utf-8-sig")\n    for key, const in (("success", "STATUS_SUCCESS"), ("warning", "STATUS_WARNING")):\n        found = len(re.findall(r"\'%s\':\\s+%s\\b" % (key, const), src))\n        assert found == 3, f"{key} is wired through {const} in {found} palettes, not 3"\n\n\n',
             "# RNV-NAMED-AND-USED, 2026-10-04: a test stood here holding the palettes'\n# success and warning keys to their constants. Nothing read the keys, so\n# they went, and the constants with them.\n\n\n")
    tree.sub('tests/test_surface_alignment.py',
             'def test_image_mode_was_left_alone():\n    """Recorded rather than trusted: if image mode is aligned later, this test\n    is the thing that has to be deleted on purpose."""\n    assert "input_bg" in IMAGE\n    assert IMAGE["input_bg"] != "#1a1a1a", (\n        "image mode now uses the dark input surface. That was outside the "\n        "2026-08-27 ruling -- if it is intended, delete this test and say so.")\n',
             "# RNV-NAMED-AND-USED, 2026-10-04: test_image_mode_was_left_alone stood here,\n# holding image mode's input_bg off the dark input surface, and it said that\n# if image mode were aligned later the test should be deleted on purpose.\n# This is that. The entry it held, input_bg at the card colour, was read by\n# nothing in image mode: its one reader is the settings dialog, and that\n# dialog takes the dark palette in image mode. Ruled 2026-10-04: a value\n# that differs from what is drawn, and that nothing needs, is removed. Image\n# mode now holds dark's input_bg through the spread, the surface the\n# settings dialog always drew there.\n")
    tree.sub('utils/settings_manager.py',
             '    DEFAULT_SLOT_COLOR_IMAGE: str = SESSION_FALLBACK_COLOR_IMAGE  # black (semi-transparent) for Image Mode\n',
             '    # RNV-NAMED-AND-USED (2026-10-04): the comment here said "black\n    # (semi-transparent)". What is stored is opaque black. A new slot is\n    # drawn semi-transparent in image mode because the main window sets\n    # SLOT_IMAGE_ALPHA on the colour it reads from here.\n    DEFAULT_SLOT_COLOR_IMAGE: str = SESSION_FALLBACK_COLOR_IMAGE  # black for Image Mode; drawn at SLOT_IMAGE_ALPHA\n')
    if (tree.root / 'tests/test_named_and_used.py').exists():
        raise Stop('tests/test_named_and_used.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_named_and_used.py', '"""\ntests/test_named_and_used.py\n============================\nRNV-NAMED-AND-USED, 2026-10-04. Every colour in the application is named,\nand every name is used.\n\nRuled 2026-10-04: "As long as a color exist in the app it should be named\nand used no hardcoded or pointless literals should exist, only literals with\na purpose, like data or comparison are allowed. Colors are name for swap\nability and alignment."\n\nIn this application that removed nine palette keys no mode read, with the\nnotes that called three of them not consumed; made the image palette the\ndark palette under its own name with the six entries image mode draws\ndifferently, dropping an input ground nothing in image mode read; removed\nfive constants nothing read; and read the alpha a new slot takes in image\nmode from the name it already had.\n\nThree sweeps hold it, each over the application\'s own source:\n\n1. NAMED. No colour is written out in the code. Every spelling is read: hex,\n   rgb() and rgba(), a CSS colour name, QColor built from numbers, a Qt\n   global colour, a tuple or a list of channels, an alpha set as a number.\n   A colour is written once, in the colour module, under a name; everything\n   else reads the name. What stays written is DATA, each entry with its\n   reason, and the sweep fails for an entry that no longer matches anything.\n2. USED, the palettes. Every colour a palette holds is looked up by key\n   somewhere in the application.\n3. USED, the constants. Every colour the colour module names is read\n   somewhere in the application: by the palettes, by another constant, or by\n   the code.\n\nClear is not a colour: \'transparent\', alpha 0 and Qt\'s transparent are how a\nwidget is told to paint nothing, and are left as written.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport importlib\nimport pathlib\nimport re\n\nimport pytest\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\n\n#: Where this application writes its colours: the one place a literal belongs.\nCOLOUR_MODULES = ("ui/colors.py",)\n#: Where its palettes are written: their own keys are not lookups.\nPALETTE_MODULES = COLOUR_MODULES\nSKIP_DIRS = {"tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__"}\n\nfrom ui.colors import DARK_THEME_COLORS, IMAGE_MODE_COLORS, LIGHT_THEME_COLORS  # noqa: E402\n\nPALETTES = {"DARK_THEME_COLORS": DARK_THEME_COLORS, "LIGHT_THEME_COLORS": LIGHT_THEME_COLORS,\n            "IMAGE_MODE_COLORS": IMAGE_MODE_COLORS}\n\n#: Below these a sweep has gone blind.\nMIN_FILES = 30\nMIN_ENTRIES = 80\nMIN_CONSTANTS = 30\n\n#: What stays written, and why: (file, literal) -> the reason. "*" covers a\n#: file that is a table of data. Data a person searches by or is shown as an\n#: example is not the application\'s look, and a brand move should not change it.\nDATA = {\n    ("ui/color_search.py", "*"):\n        "the CSS colour names a search understands, and the example in the search box: data",\n    ("ui/settings_dialog.py", "#4a90d9"):\n        "the example a clipboard format is previewed with, as hex: text shown to the person",\n    ("ui/settings_dialog.py", "rgb(74, 144, 217)"):\n        "the same example, as rgb(): text shown to the person",\n    ("core/color_math.py", "(0, 0, 0)"):\n        "what safe_rgb() hands back for channels it cannot use: a fallback, as data",\n    ("core/color_extractor.py", "[0, 0, 0]"):\n        "where a cluster\'s three channel sums start: arithmetic, not a colour",\n}\n\nCSS_NAMES = frozenset("""aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue\nblueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue\ndarkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid\ndarkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink\ndeepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold\ngoldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender lavenderblush\nlawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey\nlightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime\nlimegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen\nmediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin\nnavajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise\npalevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue\nsaddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow\nspringgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow\nyellowgreen""".split())\nQT_GLOBAL = frozenset({"white", "black", "red", "darkRed", "green", "darkGreen", "blue", "darkBlue", "cyan",\n                       "darkCyan", "magenta", "darkMagenta", "yellow", "darkYellow", "gray", "darkGray",\n                       "lightGray"})\nHEX = re.compile(r"(?<![\\w&])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_])")\nFUNC = re.compile(r"\\b(?:rgba?|hsla?|hsva?)\\(\\s*[0-9.]+%?\\s*,[^)]*\\)", re.I)\nPROP = re.compile(r"(?:^|[;{\\s\\"\'])((?:[a-z-]*color|background(?:-color)?|border(?:-[a-z]+)*|outline(?:-[a-z]+)*|"\n                  r"fill|stroke))\\s*[:=]\\s*([^;{}<>]*)", re.I)\nWORD = re.compile(r"(?<![\\w#.-])([a-z]+)(?![\\w(-])", re.I)\nNOT_A_COLOUR = re.compile(r"margin|padding|spacing|size|offset|geometry|rect|pos|range|version|ratio|weight", re.I)\nA_COLOUR = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})|rgba?\\([^)]*\\)")\n\n\ndef _sources():\n    """(repo-relative path, text) of every file of the application: not the\n    tests, not a delivery script, not what a build leaves behind."""\n    for path in sorted(ROOT.rglob("*.py")):\n        rel = path.relative_to(ROOT).as_posix()\n        parts = rel.split("/")\n        if any(p in SKIP_DIRS or p.startswith(".") for p in parts[:-1]):\n            continue\n        if len(parts) == 1 and (parts[0].startswith(("test_", "up", "conftest", "run_tests"))):\n            continue\n        text = path.read_text(encoding="utf-8-sig", errors="replace")\n        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:\n            continue\n        yield rel, text\n\n\ndef _prose(tree) -> set:\n    """ids of the strings that are prose: docstrings and bare string statements."""\n    return {id(n.value) for n in ast.walk(tree)\n            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)}\n\n\ndef _clear(literal: str) -> bool:\n    """rgba(..., 0) and QColor(..., 0): clear, not a colour."""\n    nums = re.findall(r"[0-9.]+", literal)\n    return len(nums) == 4 and float(nums[3]) == 0\n\n\ndef _written(rel: str, text: str) -> list:\n    """(line, kind, literal) for every colour this file writes out."""\n    tree = ast.parse(text)\n    prose, out = _prose(tree), []\n    parent = {}\n    for node in ast.walk(tree):\n        for child in ast.iter_child_nodes(node):\n            parent[id(child)] = node\n\n    def named_like(node) -> str:\n        """The name a value is given: its assignment target, keyword or parameter."""\n        up = parent.get(id(node))\n        while isinstance(up, (ast.IfExp, ast.BoolOp, ast.Tuple, ast.List)):\n            node, up = up, parent.get(id(up))\n        if isinstance(up, ast.keyword):\n            return up.arg or ""\n        if isinstance(up, (ast.Assign, ast.AnnAssign)):\n            target = up.targets[0] if isinstance(up, ast.Assign) else up.target\n            return ast.unparse(target)\n        if isinstance(up, ast.arguments):\n            both = up.posonlyargs + up.args\n            if node in up.defaults:\n                return both[len(both) - len(up.defaults) + up.defaults.index(node)].arg\n            if node in up.kw_defaults:\n                return up.kwonlyargs[up.kw_defaults.index(node)].arg\n        return ""\n\n    def a_name_on_its_own(node, up) -> bool:\n        """A CSS colour name that is the whole string, where a colour is given:\n        handed to a call, chosen by an if, assigned, returned, a default or a\n        value in a table. A key, an index and a comparison are not a colour\n        given to anything."""\n        s = node.value\n        if isinstance(up, (ast.Call, ast.keyword, ast.IfExp)):\n            return s.lower() in CSS_NAMES              # Qt and PIL read a name in any case\n        if s not in CSS_NAMES:\n            return False\n        if isinstance(up, ast.Dict):\n            return any(v is node for v in up.values)\n        if isinstance(up, ast.arguments):\n            return node in up.defaults or node in up.kw_defaults\n        return isinstance(up, (ast.Assign, ast.AnnAssign, ast.Return)) and up.value is node\n\n    for node in ast.walk(tree):\n        up = parent.get(id(node))\n        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in prose:\n            s = node.value\n            for m in HEX.finditer(s):\n                out.append((node.lineno, "hex", m.group(0)))\n            for m in FUNC.finditer(s):\n                if not _clear(m.group(0)):\n                    out.append((node.lineno, "func", " ".join(m.group(0).split())))\n            for m in PROP.finditer(s):\n                for w in WORD.finditer(m.group(2)):\n                    if w.group(1).lower() in CSS_NAMES:\n                        out.append((node.lineno, "name", f"{m.group(1).lower()}: {w.group(1)}"))\n            # a colour name on its own: QColor("yellow"), fill="white", ink = "black"\n            if a_name_on_its_own(node, up):\n                out.append((node.lineno, "name", s))\n        elif isinstance(node, ast.Call):\n            name = getattr(node.func, "id", getattr(node.func, "attr", None))\n            if name in ("QColor", "fromRgb", "fromRgbF", "qRgb", "qRgba") and node.args \\\n                    and all(isinstance(a, ast.Constant) and not isinstance(a.value, str) for a in node.args):\n                literal = ast.unparse(node)\n                if not _clear(literal):\n                    out.append((node.lineno, "qcolor", literal))\n            # an alpha set as a number: colour.setAlpha(171). Clear and solid are not a choice of alpha.\n            elif name in ("setAlpha", "setAlphaF") and len(node.args) == 1 and isinstance(node.args[0], ast.Constant) \\\n                    and type(node.args[0].value) in (int, float) \\\n                    and node.args[0].value not in ((0, 255) if name == "setAlpha" else (0, 1)):\n                out.append((node.lineno, "alpha", f"{name}({node.args[0].value!r})"))\n        elif isinstance(node, ast.Attribute) and node.attr in QT_GLOBAL \\\n                and ast.unparse(node.value) in ("Qt.GlobalColor", "Qt", "QtCore.Qt.GlobalColor", "QtCore.Qt"):\n            out.append((node.lineno, "global", ast.unparse(node)))\n        elif isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) in (3, 4) and all(\n                isinstance(e, ast.Constant) and type(e.value) is int and 0 <= e.value <= 255 for e in node.elts):\n            if (isinstance(up, (ast.comprehension, ast.For)) and up.iter is node) \\\n                    or isinstance(up, (ast.Compare, ast.Subscript)):\n                continue                                   # an index, a membership or a comparison\n            if isinstance(up, ast.Call) and getattr(up.func, "id", getattr(up.func, "attr", "")) in QCOLOR_CALLS:\n                continue                                   # counted with its QColor(...)\n            if len(node.elts) == 4 and node.elts[3].value == 0:\n                continue                                   # clear\n            if NOT_A_COLOUR.search(named_like(node)):\n                continue\n            out.append((node.lineno, "list" if isinstance(node, ast.List) else "tuple", ast.unparse(node)))\n    return out\n\n\nQCOLOR_CALLS = ("QColor", "fromRgb", "fromRgbF", "qRgb", "qRgba")\n\n\ndef _all_written() -> list:\n    """(rel, line, kind, literal) outside the colour module."""\n    out = []\n    for rel, text in _sources():\n        if rel in COLOUR_MODULES:\n            continue\n        out += [(rel, line, kind, literal) for line, kind, literal in _written(rel, text)]\n    return out\n\n\ndef _data(rel: str, literal: str):\n    """The DATA entry that covers this literal, or None."""\n    for (where, what) in DATA:\n        if where == rel and what in ("*", literal):\n            return (where, what)\n    return None\n\n\n# ------------------------------------------------------------ guard the guard\n\ndef test_the_sweep_reads_the_application():\n    files = [rel for rel, _text in _sources()]\n    assert len(files) >= MIN_FILES, f"only {len(files)} files swept: the sweep has gone blind"\n    for rel in COLOUR_MODULES:\n        assert rel in files, f"{rel} is not among the files swept"\n    assert not [f for f in files if f.startswith("tests/")], "the sweep reads the tests"\n\n\ndef test_the_sweep_reads_every_spelling():\n    """Each spelling of a colour, in a line of the kind the application\n    writes, is seen; clear, an index and a margin are not."""\n    seen = {(kind, literal) for _line, kind, literal in _written("probe.py", (\n        "from PyQt6.QtGui import QColor\\n"\n        "from PyQt6.QtCore import Qt\\n"\n        "a = \'background-color: #ffcccc; border: 2px solid red;\'\\n"\n        "b = f\'color: rgba(255, 255, 255, 230); padding: {4}px\'\\n"\n        "c = QColor(128, 128, 128)\\n"\n        "d = Qt.GlobalColor.darkGreen\\n"\n        "e = QColor(\'yellow\')\\n"\n        "text_color = (0, 0, 0) if a else (255, 255, 255)\\n"\n        "f = saved.get(\'color\', [200, 200, 200])\\n"\n        "ink = \'white\'\\n"\n        "g = {\'ground\': \'black\'}\\n"\n        "h = Image.new(\'RGB\', (8, 8), \'Gray\')\\n"\n        "c.setAlpha(171)\\n"))}\n    assert seen == {("hex", "#ffcccc"), ("name", "border: red"), ("func", "rgba(255, 255, 255, 230)"),\n                    ("qcolor", "QColor(128, 128, 128)"), ("global", "Qt.GlobalColor.darkGreen"),\n                    ("name", "yellow"), ("tuple", "(0, 0, 0)"), ("tuple", "(255, 255, 255)"),\n                    ("list", "[200, 200, 200]"), ("name", "white"), ("name", "black"), ("name", "Gray"),\n                    ("alpha", "setAlpha(171)")}, seen\n    quiet = _written("probe.py", (\n        "from PyQt6.QtGui import QColor\\n"\n        "from PyQt6.QtCore import Qt\\n"\n        "a = \'background: transparent; border: none; color: rgba(0, 0, 0, 0);\'\\n"\n        "b = QColor(0, 0, 0, 0)\\n"\n        "b.setAlpha(0)\\n"\n        "b.setAlpha(255)\\n"\n        "c = Qt.GlobalColor.transparent\\n"\n        "d = [int(h[i:i + 2], 16) for i in (0, 2, 4)]\\n"\n        "margins = (10, 10, 10, 10)\\n"\n        "sizes = [16, 32, 48]\\n"\n        "\'\'\'a bare string is prose: color: red, #ffcccc\'\'\'\\n"\n        "if d in (5, 10, 20) or d == (0, 0, 0) or a == \'red\':\\n"\n        "    pass\\n"\n        "for size in [16, 32, 48]:\\n"\n        "    e = {\'red\': 1}[\'red\']\\n"))\n    assert quiet == [], quiet\n\n\n# ----------------------------------------------------------------- 1. named\n\ndef test_no_colour_is_written_out_in_the_code():\n    stray = [f"{rel}:{line}  {literal}" for rel, line, _kind, literal in _all_written()\n             if _data(rel, literal) is None]\n    assert not stray, (\n        "a colour is written out where a name belongs. Name it in "\n        f"{COLOUR_MODULES[0]} and read the name; or, if it is data, add it to DATA "\n        "with its reason:\\n  " + "\\n  ".join(stray))\n\n\ndef test_every_data_entry_still_covers_something():\n    """An exemption that outlives what it excused is a licence for the next\n    literal written in that file."""\n    used = {_data(rel, literal) for rel, _line, _kind, literal in _all_written()}\n    stale = [f"{where}: {what}" for (where, what) in DATA if (where, what) not in used]\n    assert not stale, "DATA entries that match nothing now:\\n  " + "\\n  ".join(stale)\n    assert all(reason.strip() for reason in DATA.values()), "a DATA entry has no reason"\n\n\n# ---------------------------------------------------- 2. used: the palettes\n\ndef _strings_the_application_reads() -> set:\n    """Every string the code holds outside the palettes\' own keys: what a\n    lookup by key, or a table of keys, is written with. A module\'s __all__\n    is a list of the names it exports, not of keys, and is left out: a\n    function called warning() does not look up a palette\'s \'warning\'."""\n    out = set()\n    for rel, text in _sources():\n        tree = ast.parse(text)\n        not_keys = _prose(tree)\n        if rel in PALETTE_MODULES:\n            for node in ast.walk(tree):\n                if isinstance(node, ast.Dict):\n                    not_keys |= {id(k) for k in node.keys if k is not None}\n        for node in tree.body:\n            target = (node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else\n                      node.target if isinstance(node, ast.AnnAssign) else None)\n            if getattr(target, "id", None) == "__all__" and node.value is not None:\n                not_keys |= {id(n) for n in ast.walk(node.value)}\n        for node in ast.walk(tree):\n            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in not_keys:\n                if (rel, node.value) in NOT_LOOKUPS:        # spelled like a key, and not a lookup of one\n                    _NOT_A_READ_SEEN.add((rel, node.value))\n                    continue\n                out.add(node.value)\n    return out\n\n\ndef test_every_colour_a_palette_holds_is_looked_up():\n    read = _strings_the_application_reads()\n    unread = sorted({f"{name}[{key!r}]" for name, palette in PALETTES.items() for key, value in palette.items()\n                     if isinstance(value, str) and (A_COLOUR.fullmatch(value) or value == "transparent")\n                     and key not in read})\n    assert not unread, (\n        "palette entries nothing in the application looks up. A colour is kept "\n        "for what uses it:\\n  " + "\\n  ".join(unread))\n    assert sum(len(p) for p in PALETTES.values()) >= MIN_ENTRIES, "the palettes have gone missing"\n\n\n# --------------------------------------------------- 3. used: the constants\n\ndef _colour_constants() -> dict:\n    """NAME -> where it is defined, for every module-level constant of the\n    colour module whose value is a colour: a hex string, an rgb() string, or\n    channels under a name that says so."""\n    out = {}\n    for rel in COLOUR_MODULES:\n        module = importlib.import_module(rel[:-3].replace("/", "."))\n        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8-sig"))\n        for node in tree.body:\n            target = (node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else\n                      node.target if isinstance(node, ast.AnnAssign) else None)\n            if not isinstance(target, ast.Name) or not target.id.isupper():\n                continue\n            value = getattr(module, target.id, None)\n            if isinstance(value, str) and A_COLOUR.fullmatch(value):\n                out[target.id] = rel\n            elif isinstance(value, tuple) and len(value) in (3, 4) and all(type(v) is int for v in value) \\\n                    and re.search(r"RGB|COLOR|COLOUR|OVERLAY", target.id):\n                out[target.id] = rel\n    return out\n\n\ndef _names_the_application_reads() -> dict:\n    """NAME -> how many times the code reads it: as a name or as an attribute."""\n    counts: dict[str, int] = {}\n    for rel, text in _sources():\n        for node in ast.walk(ast.parse(text)):\n            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):\n                counts[node.id] = counts.get(node.id, 0) + 1\n            elif isinstance(node, ast.Attribute):\n                if (rel, node.attr) in NOT_READS:           # spelled like a constant, and not a read of one\n                    _NOT_A_READ_SEEN.add((rel, node.attr))\n                    continue\n                counts[node.attr] = counts.get(node.attr, 0) + 1\n    return counts\n\n\ndef test_every_colour_constant_is_read():\n    constants = _colour_constants()\n    assert len(constants) >= MIN_CONSTANTS, f"only {len(constants)} colour constants found"\n    reads = _names_the_application_reads()\n    unread = sorted(name for name in constants if not reads.get(name))\n    assert not unread, (\n        "colour constants nothing in the application reads. A name is kept for "\n        "what uses it:\\n  " + "\\n  ".join(f"{name}  ({constants[name]})" for name in unread))\n\n\ndef test_every_exported_name_exists():\n    """__all__ names what the colour module offers. A name it lists and does\n    not define makes `from module import *` fail."""\n    for rel in COLOUR_MODULES:\n        module = importlib.import_module(rel[:-3].replace("/", "."))\n        missing = [n for n in getattr(module, "__all__", []) if not hasattr(module, n)]\n        assert not missing, f"{rel} exports names it does not define: {missing}"\n\n\n# ---------------------------------------------- image mode\'s own palette\n\n#: Image mode is the dark palette under its own name and, after the spread,\n#: the entries image mode reads and draws for itself. A new one is a\n#: decision: it is added here with the entry.\nIMAGE_OWN = (\'window_bg\', \'panel_bg\', \'scroll_bg\', \'scrollbar_bg\', \'scrollbar_handle\', \'scrollbar_border\')\n\n\ndef _palette_display(name: str) -> ast.Dict:\n    """The dict display NAME is assigned, at module level or in a class body."""\n    for rel in PALETTE_MODULES:\n        for node in ast.walk(ast.parse((ROOT / rel).read_text(encoding="utf-8-sig"))):\n            target = (node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else\n                      node.target if isinstance(node, ast.AnnAssign) else None)\n            if getattr(target, "id", None) == name and isinstance(node.value, ast.Dict):\n                return node.value\n    raise AssertionError(f"{name} is not written as a dict display")\n\n\ndef test_image_mode_is_the_dark_palette_and_its_own_entries():\n    node = _palette_display("IMAGE_MODE_COLORS")\n    spreads = [ast.unparse(v) for k, v in zip(node.keys, node.values) if k is None]\n    assert spreads == ["DARK_THEME_COLORS"] and node.keys[0] is None, (\n        f"IMAGE_MODE_COLORS spreads {spreads}: it is the dark palette first, and no other")\n    written = sorted(k.value for k in node.keys if k is not None and k.value != "name")\n    assert written == sorted(IMAGE_OWN), (\n        "the entries image mode writes for itself are not the ones listed. An entry "\n        f"image mode never reads is a value nothing shows:\\n  written {written}\\n  listed  {sorted(IMAGE_OWN)}")\n\n\n# ------------------------------------------- what only looks like a read\n\n#: A string the code holds that is spelled like a palette key and is not a\n#: lookup of one: (file, string) -> what it is. Left uncounted, so a key\n#: this round removed cannot come back and be taken for read by a line\n#: that never read it.\nNOT_LOOKUPS = dict()\n\n#: An attribute the code reads that is spelled like a colour constant and is\n#: not one: (file, name) -> what it is. Left uncounted for the same reason.\nNOT_READS = {\n    (\'utils/settings_manager.py\', \'DEFAULT_SLOT_COLOR_IMAGE\'):\n        \'Keys.DEFAULT_SLOT_COLOR_IMAGE and Defaults.DEFAULT_SLOT_COLOR_IMAGE: the key a \'\n        "stored preference is kept under and its default. A setting\'s names, which the colour"\n        \' constant of the same spelling shared\',\n}\n\n_NOT_A_READ_SEEN: set = set()\n\n\ndef test_what_only_looks_like_a_read_is_still_in_the_code():\n    """An entry that matches no line excuses nothing, and is taken out."""\n    _strings_the_application_reads()\n    _names_the_application_reads()\n    listed = set(NOT_LOOKUPS) | set(NOT_READS)\n    stale = sorted(listed - _NOT_A_READ_SEEN)\n    assert not stale, f"listed as only looking like a read, and no longer in the code: {stale}"\n    assert all(reason.strip() for reason in list(NOT_LOOKUPS.values()) + list(NOT_READS.values())), (\n        "an entry has no reason")\n')


def _original(tree, rel: str) -> str:
    """The file as it is on disk, which checks() runs before flush() changes,
    normalised the way Tree.read() normalises it."""
    raw = (tree.root / rel).read_bytes()
    text = (raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw).decode("utf-8")
    crlf = text.count("\r\n")
    if crlf and crlf == text.count("\n"):
        text = text.replace("\r\n", "\n")
    return text


def _function(src: str, name: str, cls: str | None = None):
    """The named function, at module level or inside the named class."""
    body = ast.parse(src).body
    if cls is not None:
        body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == cls).body
    return next(n for n in body if isinstance(n, ast.FunctionDef) and n.name == name)


def _top(src: str) -> dict:
    """Module-level NAME -> ast.dump of the value it is assigned."""
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(t, ast.Name):
                out[t.id] = ast.dump(node.value)
    return out


def _entries(node) -> dict:
    """A dict display's literal keys -> ast.dump of each value; ** spreads
    under their own ast.dump, so a moved spread is seen too."""
    return {(k.value if k is not None else "**" + ast.dump(v)): ast.dump(v)
             for k, v in zip(node.keys, node.values)}


def _sheet_parts(call) -> list:
    """The literal text of a setStyleSheet(f"...") call, the parts between
    its placeholders, in order."""
    arg = call.args[0]
    assert isinstance(arg, ast.JoinedStr), ast.unparse(arg)[:80]
    return [v.value for v in arg.values if isinstance(v, ast.Constant)]


def _calls(fn, attr: str) -> list:
    return [c for c in ast.walk(fn) if isinstance(c, ast.Call)
            and getattr(c.func, "attr", getattr(c.func, "id", None)) == attr]


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""
    CFG = "ui/colors.py"
    MAIN = "RNV_Color_Palette_Manager.py"
    KEYS_GONE = ('accent_text', 'dialog_border', 'hover_color', 'main_btn_border_color', 'success', 'tab_bg', 'tab_hover_bg', 'tab_selected_bg', 'warning')
    IMAGE_OWN = ('window_bg', 'panel_bg', 'scroll_bg', 'scrollbar_bg', 'scrollbar_handle', 'scrollbar_border')
    IMAGE_UNREAD = 'input_bg'
    NAMES_GONE = ('GREY_E0', 'STATUS_SUCCESS', 'STATUS_WARNING', 'STATUS_ERROR', 'DEFAULT_SLOT_COLOR_IMAGE')
    LOST = {'tests/test_app_mirror.py': ['test_the_light_surfaces_did_not_follow_the_ink', 'test_the_tab_keys_are_still_unconsumed', 'test_the_tab_keys_carry_the_note_that_says_so'], 'tests/test_brand_mirror.py': ['test_text_on_gold_is_black_and_stays_black'], 'tests/test_error_red.py': ['test_the_fills_cannot_carry_text_and_that_is_why_there_are_five_values'], 'tests/test_status_register.py': ['test_the_palettes_are_wired_through_the_constants_not_rewritten'], 'tests/test_surface_alignment.py': ['test_image_mode_was_left_alone']}
    old_cfg, new_cfg = _original(tree, CFG), tree.read(CFG)

    def value(expr):
        return ast.dump(ast.parse(expr, mode="eval").body)

    def assigned(src, name):
        for node in ast.parse(src).body:
            t = (node.targets[0] if isinstance(node, ast.Assign) else
                 node.target if isinstance(node, ast.AnnAssign) else None)
            if getattr(t, "id", None) == name:
                return node.value
        raise AssertionError(f"no {name}")

    def palette(src, name):
        return _entries(assigned(src, name))

    def app_sources():
        for p in sorted(tree.root.rglob("*.py")):
            rel = p.relative_to(tree.root).as_posix()
            parts = rel.split("/")
            if any(q in ("tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__")
                   or q.startswith(".") for q in parts[:-1]):
                continue
            if len(parts) == 1 and parts[0].startswith(("test_", "up", "conftest", "run_tests")):
                continue
            text = tree.read(rel) if rel in tree.files else p.read_text(encoding="utf-8-sig", errors="replace")
            if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
                continue
            yield rel, text

    d_b, l_b, i_b = (palette(old_cfg, n) for n in ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS"))

    # ---- dark and light: nine keys out of each, and nothing else moves
    for name, before in (("DARK_THEME_COLORS", d_b), ("LIGHT_THEME_COLORS", l_b)):
        after = palette(new_cfg, name)
        assert set(before) - set(after) == set(KEYS_GONE), f"{name} lost {sorted(set(before) - set(after))}"
        assert after == {k: v for k, v in before.items() if k not in KEYS_GONE}, f"{name} moved beyond the keys removed"

    # ---- image: the dark palette under its own name, and its six entries at the values they had
    i_a = palette(new_cfg, "IMAGE_MODE_COLORS")
    spread = "**" + value("DARK_THEME_COLORS")
    assert set(i_a) == {spread, "name"} | set(IMAGE_OWN), \
        f"IMAGE_MODE_COLORS is not the dark palette and its six entries: {sorted(i_a)}"
    assert list(i_a)[0] == spread, "image mode's own entries do not come after the spread"
    assert all(i_a[k] == i_b[k] for k in ("name",) + IMAGE_OWN), "an entry image mode draws differently moved"
    assert not set(KEYS_GONE) & set(i_a) and IMAGE_UNREAD not in i_a

    # ---- the module: five names go, none comes, and only the palettes and the two tables move
    old_top, new_top = _top(old_cfg), _top(new_cfg)
    assert set(old_top) - set(new_top) == set(NAMES_GONE), sorted(set(old_top) - set(new_top))
    assert set(new_top) == set(old_top) - set(NAMES_GONE), sorted(set(new_top) - set(old_top))
    moved = sorted(n for n in new_top if old_top[n] != new_top[n])
    assert moved == ["APP_PROVENANCE", "DARK_THEME_COLORS", "IMAGE_MODE_COLORS", "LIGHT_THEME_COLORS", "__all__"], \
        f"ui/colors.py: these names moved: {moved}"
    was, now = ast.literal_eval(assigned(old_cfg, "APP_PROVENANCE")), ast.literal_eval(assigned(new_cfg, "APP_PROVENANCE"))
    assert now == {k: v for k, v in was.items() if k not in NAMES_GONE}, "APP_PROVENANCE moved beyond the name removed"
    was, now = ast.literal_eval(assigned(old_cfg, "__all__")), ast.literal_eval(assigned(new_cfg, "__all__"))
    assert now == [n for n in was if n not in NAMES_GONE], "__all__ moved beyond the names removed"

    def functions(src):
        return {n.name: ast.dump(n) for n in ast.parse(src).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    assert functions(old_cfg) == functions(new_cfg), "ui/colors.py: a function moved"
    missing = [n for n in now if n not in set(new_top) | set(functions(new_cfg)) | {"ThemeName", "ThemeDict"}]
    assert not missing, f"__all__ names what is not defined: {missing}"
    assert "NOT CONSUMED" not in new_cfg, "a NOT CONSUMED note is still in the palettes"

    # ---- the alpha a new slot takes in image mode: the byte written out is the byte named
    assert old_top["SLOT_IMAGE_ALPHA"] == value("171"), "SLOT_IMAGE_ALPHA is not 171, the byte the main window wrote out"
    old_main, new_main = _original(tree, MAIN), tree.read(MAIN)

    def methods(src):
        out = dict()
        for node in ast.parse(src).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[node.name] = ast.unparse(node)
            elif isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out[node.name + "." + sub.name] = ast.unparse(sub)
        return out
    fo, fn = methods(old_main), methods(new_main)
    assert set(fo) == set(fn), f"{MAIN}: functions came or went"
    changed = sorted(k for k in fo if fo[k] != fn[k])
    assert len(changed) == 1 and changed[0].endswith("._get_default_slot_color"), f"{MAIN}: the functions that moved are {changed}"
    assert fn[changed[0]] == fo[changed[0]].replace("color.setAlpha(171)", "color.setAlpha(SLOT_IMAGE_ALPHA)") \
        and fo[changed[0]].count("color.setAlpha(171)") == 1, "_get_default_slot_color() moved beyond naming its alpha"
    imported = [a.name for n in ast.parse(new_main).body if isinstance(n, ast.ImportFrom) and n.module == "ui.colors"
                for a in n.names]
    assert imported.count("SLOT_IMAGE_ALPHA") == 1, f"{MAIN} does not import SLOT_IMAGE_ALPHA once"

    # ---- the settings: the comment beside the image-mode default, and nothing else
    assert ast.dump(ast.parse(_original(tree, "utils/settings_manager.py"))) == \
        ast.dump(ast.parse(tree.read("utils/settings_manager.py"))), "utils/settings_manager.py moved beyond its comment"

    # ---- derived, over the whole application: nothing reads what went
    readers_of_unread = set()
    for rel, text in app_sources():
        mod = ast.parse(text)
        aliases = {a.asname or a.name for n in ast.walk(mod) if isinstance(n, ast.ImportFrom) and n.module == "ui"
                   for a in n.names if a.name == "colors"}
        for node in ast.walk(mod):
            key = None
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
                key = node.slice.value
            elif isinstance(node, ast.Call) and getattr(node.func, "attr", None) in ("get", "pop", "setdefault") \
                    and node.args and isinstance(node.args[0], ast.Constant):
                key = node.args[0].value
            if isinstance(key, str):
                assert key not in KEYS_GONE, f"{rel}:{node.lineno} looks up {key!r}, a key this round removes"
                if key == IMAGE_UNREAD:
                    readers_of_unread.add(rel)
            names = []
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                names = [node.id]
            elif isinstance(node, ast.ImportFrom) and (node.module or "").endswith("colors"):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases:
                names = [node.attr]
            for n in names:
                assert n not in NAMES_GONE, f"{rel}:{node.lineno} still names {n}, which this round removes"

    # ---- image mode's input ground: its one reader takes the dark palette in image mode
    assert readers_of_unread == {"ui/settings_dialog.py"}, \
        f"{IMAGE_UNREAD!r} is looked up in {sorted(readers_of_unread)}: image mode's entry may be read"
    settings = tree.root / "ui" / "settings_dialog.py"
    for fn_node in ast.walk(ast.parse(settings.read_text(encoding="utf-8-sig"))):
        if isinstance(fn_node, ast.FunctionDef) and IMAGE_UNREAD in [
                n.args[0].value for n in ast.walk(fn_node) if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "get"
                and n.args and isinstance(n.args[0], ast.Constant)]:
            takes_dark = [n for n in ast.walk(fn_node) if isinstance(n, ast.If)
                          and ast.unparse(n.test) == "self.theme_manager.is_image_mode()"
                          and any(ast.unparse(s) == "theme = ThemeManager.DARK_THEME" for s in n.body)]
            assert takes_dark, f"ui/settings_dialog.py: {fn_node.name}() no longer takes the dark palette in image mode"
    manager = ast.parse((tree.root / "ui" / "theme_manager.py").read_text(encoding="utf-8-sig"))
    cls = next(n for n in manager.body if isinstance(n, ast.ClassDef) and n.name == "ThemeManager")
    held = {getattr(n.target, "id", None): ast.unparse(n.value) for n in cls.body if isinstance(n, ast.AnnAssign) and n.value}
    assert held.get("DARK_THEME") == "DARK_THEME_COLORS", "ThemeManager.DARK_THEME is not the dark palette"

    # ---- the tests: the root suite keeps every test; each guard loses what named what went
    def tests_in(src):
        return [n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert tests_in(_original(tree, "test_rnv_palette_manager.py")) == tests_in(tree.read("test_rnv_palette_manager.py")), \
        "the root suite gained or lost a test"
    assert tests_in(tree.read(GUARD)) == ['test_the_sweep_reads_the_application', 'test_the_sweep_reads_every_spelling', 'test_no_colour_is_written_out_in_the_code', 'test_every_data_entry_still_covers_something', 'test_every_colour_a_palette_holds_is_looked_up', 'test_every_colour_constant_is_read', 'test_every_exported_name_exists', 'test_image_mode_is_the_dark_palette_and_its_own_entries', 'test_what_only_looks_like_a_read_is_still_in_the_code'], f"{GUARD}: its tests are {tests_in(tree.read(GUARD))}"
    for rel in GUARD_FILES[1:]:
        lost = sorted(set(tests_in(_original(tree, rel))) - set(tests_in(tree.read(rel))))
        assert lost == LOST.get(rel, []), f"{rel} lost {lost}"
    assert SENTINEL in new_cfg and SENTINEL in tree.read(GUARD), "the sentinel is not in the palette and its guard"
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
