"""The palette manager: the colors live in utils/colors.py

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-color-palette-manager, derived against a fresh clone at the live head (a43f814).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-18: #63 A. Every app keeps its colors in one file, in one
place: utils/colors.py. Here they lived in ui/colors.py, and the file moves
to utils/colors.py. Every import, path and mention of the old place follows
it, and nothing is left there. brand_map.json, the sync tool's chart
(COLORS.md), the daily brand sync and the docs name the new place.

WHAT LANDS.
  ui/colors.py -> utils/colors.py: the file moves, and only what in it named
      its old place changes.
  42 more files: every import, path and mention follows the colors;
      COLORS.md names the new place, as tools/sync_colors.py writes it.

JUDGMENT CALLS, each reported:
  - ui/__init__.py re-exported nine names from the color file. Nothing read
    them there, and the re-export goes; the package exports what is in it.
  - utils/dialog_helper.py explained its inline import of the colors as
    avoiding a circular import, utils to ui and back. From utils/ to utils/
    there is none: the explanation goes, the import stays where it is.
  - tests/test_brand_mirror.py lists files from git's index, which still
    names ui/colors.py until the move is committed. It also reads files not
    yet committed (--others), so the round's own run reads utils/colors.py.

NO VALUE MOVES. Every value ui/colors.py defined is what it was.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import tokenize
import types
from pathlib import Path

REPO = 'rnv-color-palette-manager'
SENTINEL = '"color_file": "utils/colors.py"'   # brand_map.json names the new place
SENTINEL_FILE = 'brand_map.json'
GUARD = 'tests/test_colors_in_sync.py'
GUARD_FILES = ['tests/test_colors_in_sync.py', 'tests/test_named_and_used.py']
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *GUARD_FILES]
DESCRIPTION = "The palette manager: the colors live in utils/colors.py"

#: EXACTLY WHAT CI RUNS. Both workflows run `python run_tests.py`, which runs
#: the locked root suite under unittest and then tests/ under pytest.
SUITES = [("python run_tests.py  (both CI workflows)",
           [sys.executable, "run_tests.py"])]

SHADOWS = ['colors.py', 'config.py', 'conftest.py', 'run_tests.py', 'sync_colors.py', 'test_colors_in_sync.py', 'test_named_and_used.py', 'test_rnv_palette_manager.py']

LEFT_ALONE = ['every color value: the file moves as it is, and only what names the old place changes.', 'coverage_report.txt, which run_tests.py writes: its next run writes the new path.', 'the image files, and their paths.', 'rnv-brand, which the brand chat keeps.']

# ======================================================================== this round

OLD_PLACE = 'ui/colors.py'
COLOR_FILE = 'utils/colors.py'

#: Every name that leaves utils/config.py for utils/colors.py
MOVED = []

#: sha256 of each file the round reaches, as the head holds it (under its old name if moved)
BASE_SHAS = {'.github/workflows/brand-sync.yml': '677608e51f6557134a45a3e3599bc7443f51459e377ed14a5ec412ae8c991482', 'ARCHITECTURE.md': '6929fdaa044e8922aa0825857e860b7ba2ac47397ed63f850f148dc0a8424f9b', 'COLORS.md': '899f72026a25558cdd98d08b8fb23ad39800960264012c758853f405fa34dab4', 'README.md': '130e8d84ea514e07e8e875bfe8d1720995d5aaca0750283b8b2fc3a773ae64ee', 'RNV_Color_Palette_Manager.py': 'b462b9fba12b16bdfbe2cd32506a53a665226f62643f3e1f7ef836f4f054e5f6', 'TESTING.md': '52743154d61ddc9c55d590c22daa66324516fb9e65cfa9cb0baa429fb00cb114', 'brand_map.json': '5a1ab9cfe9f2f47d6aaffc3dbd96f96dde1e4a4420b61833d2582b9aa32a513e', 'core/color_slot.py': 'ef9c1b6dd365313da83ab7003d34c53393dd8e7e28102ead7f41b12e5f71379f', 'core/palette_formats.py': '10ec05dad684b0caa74f50e1e065647c47922a0fd976f4f63793678329272f19', 'test_rnv_palette_manager.py': '8bfb8bdb3dd91def20880f8a01fcd6b563d5ed37707140506a33f2636c1cb7e6', 'tests/color_values.py': '25f970813d086440e0ebb4a8b2f72b1f8ff817b916d60390c5fa22556d6d3e5b', 'tests/test_app_mirror.py': '1e436bee49686149041f69b34d68507b34d03db81aff4338143c8b542d596f68', 'tests/test_brand_mirror.py': '156a58ccb996b351a2a6ec71609467dc6d7314c5ff56b735a471b7f711d8dbf7', 'tests/test_button_key_names.py': '58b08baac3c6575b5926b6f6070d720774f52a3a176a85568c02505a8f8ab63e', 'tests/test_button_press_step.py': '640463b99d2ab5f792961fafd74ac5585d3e1131bf31f430f4d7980ebf3b2539', 'tests/test_collapse_505050.py': 'a36d6de409980b3915c096dc95acb7d249dce911aa322f4f3b49092a258eb68c', 'tests/test_constant_names.py': '5ea38ec4cf2ea4657305b787d78fda1cb28e3ec0d796d3288c8f97ae60c3b952', 'tests/test_contrast_pairs.py': 'ea752da7c2fa1b57b75881181679df6c6d2c9a49af241b4261939ba7b83bf86d', 'tests/test_derived_values.py': 'ccebfe18c96c38d7ce9e542f521c48250c4b66237141a549e5a73e52ab29255a', 'tests/test_error_red.py': '9f62e21026c1222cc21d9a9cd36af3ec9edc9587476fb21442b3ab114e0a4c8b', 'tests/test_gold_as_text.py': 'bc59b726535c92dd081179a8b9989802f179899f4fb29332ff7105437e9e537d', 'tests/test_ink_on_the_golds.py': 'c4d2d42ba3c572712d3952d58fbcc47a223b6be17b62e13cf3f448b2af92afc5', 'tests/test_ladder_and_plate.py': '6d0b7d552d1957726276c2e0e3316fdddd835ba577c77848bbd1618b87f99a5d', 'tests/test_light_rewalk.py': 'a028095f89b72385cdee7aafd1d11ea38bafa3b7d3b559e675b3601ed13d7959', 'tests/test_light_wiring.py': '569058a2e6376033758620daa5caa7a5084363397c3223d04f6a3aa39cff2ab8', 'tests/test_muted_and_disabled_text.py': 'e00c9059a01273b9686d6dd349864319daa53385250be723320724797adb830d', 'tests/test_named_and_used.py': '4da03a870e08714fb9f4d111c865d96050eaa21380a5c203db859753261c9b5a', 'tests/test_qt_color_slot.py': 'bb8a311a899352206c480644769b74eaab3f34b5b36e76814ad97ab689916db3', 'tests/test_qt_color_slot_paint.py': 'c9a230e59307ea53d88cd1d04f51bc334d554219e858869439396ae5f42148ac', 'tests/test_register_wiring.py': '87c8baef107a988f44479e0220293f3c5f4a1a896d231dfb33bbbbe55e4b600c', 'tests/test_status_register.py': 'f254b1cc5ed550cc827ad5dbd181129a0edc740454070e074fcef16649b33101', 'tests/test_surface_alignment.py': '38e6d85d4e954a3b659698fe642fbcbeb32d8208539ed2523f3b8a7a2f6a1add', 'ui/__init__.py': 'ce61fb555e461949d792991bb3b5d96fe546fd3fc386cd3c99acbbffd9fc91b7', 'ui/about_dialog.py': 'e623d10e878ff722ff45ef7b2c3eb909bdd8ff4a7f77daaff5eb4e8368d236cd', 'ui/batch_export_dialog.py': 'ac709cced3b895dda87bf050d06a2f8e674e168c6a7b241d1da99100c2186507', 'ui/image_upload_dialog.py': '8b576b314d5f0d42c6cb48be7b61d2c8b7ba40197de20cdbbd0885cfa7376d05', 'ui/preview_grid.py': 'bb8604412177597412c62e71ed4cdbc01c5a19ad147c54f08926c35725105284', 'ui/settings_dialog.py': 'f5bd09f2b21e154b150dfe472b807db7e52cacacc7ff9c51562328ce9b311def', 'ui/theme_manager.py': '9e1bcd66bef7279e65b9185063307c2929e2ec58d941626a944b89437f0379d4', 'utils/color_history.py': 'ff204aff2eface510b01796df17c764a685f5cd9755c53a579e7a03b51c0d443', 'ui/colors.py': '2c2804bf76065eecc600cdfcb73499d2142127d36283221c6a74196dbc9ba303', 'utils/dialog_helper.py': 'abc145ed8a19efeca22f455973e0892e0cbf20efa6d6e17ec97dc4ca2b5fa4fa', 'utils/settings_manager.py': 'ceb1d961e005de26952d797e72b3314d3f55db35f07ab838a29db1238e571936'}

#: (new name, old name)
RENAMES = [('utils/colors.py', 'ui/colors.py')]

#: (file, anchor, replacement), applied in order; each anchor is found exactly once
SUBS = [('.github/workflows/brand-sync.yml', '#                                     request is opened with the new pin,\n#                                     ui/colors.py and COLORS.md. If it is\n#                                     still open the next day, it is updated,\n', '#                                     request is opened with the new pin,\n#                                     utils/colors.py and COLORS.md. If it is\n#                                     still open the next day, it is updated,\n'), ('.github/workflows/brand-sync.yml', '          python tools/sync_colors.py | tee sync.log\n          if git diff --quiet -- ui/colors.py; then\n            echo "No color this app uses moved at rnv-brand ${head:0:7}. Nothing to open."\n', '          python tools/sync_colors.py | tee sync.log\n          if git diff --quiet -- utils/colors.py; then\n            echo "No color this app uses moved at rnv-brand ${head:0:7}. Nothing to open."\n'), ('.github/workflows/brand-sync.yml', '          git switch -C brand-sync\n          git add tests/requirements-dev.txt ui/colors.py COLORS.md\n          git commit -m "Brand sync: rnv-brand@${HEAD:0:7}"\n', '          git switch -C brand-sync\n          git add tests/requirements-dev.txt utils/colors.py COLORS.md\n          git commit -m "Brand sync: rnv-brand@${HEAD:0:7}"\n'), ('ARCHITECTURE.md', '\nAll theme color values originate from `ui/colors.py`. No other file in the codebase contains hardcoded color literals — not even for SVG exports, session-restore fallbacks, or transparency overlays. Every hex string, every RGB tuple, every `rgba(…)` CSS value lives in one file.\n\n', '\nAll theme color values originate from `utils/colors.py`. No other file in the codebase contains hardcoded color literals — not even for SVG exports, session-restore fallbacks, or transparency overlays. Every hex string, every RGB tuple, every `rgba(…)` CSS value lives in one file.\n\n'), ('COLORS.md', "\nGenerated by `python tools/sync_colors.py` from `brand_map.json`, `ui/colors.py` and rnv-brand at `b4fa970`, the commit pinned in `tests/requirements-dev.txt`. Don't edit it by hand: change the map and run the script. `tests/test_colors_in_sync.py` fails when this file is out of date.\n\n14 colors come from the brand and 17 are the application's own. 12 more are worked out in `ui/colors.py` from those, so they follow them.\n\n", "\nGenerated by `python tools/sync_colors.py` from `brand_map.json`, `utils/colors.py` and rnv-brand at `b4fa970`, the commit pinned in `tests/requirements-dev.txt`. Don't edit it by hand: change the map and run the script. `tests/test_colors_in_sync.py` fails when this file is out of date.\n\n14 colors come from the brand and 17 are the application's own. 12 more are worked out in `utils/colors.py` from those, so they follow them.\n\n"), ('README.md', '│   ├── py.typed\n│   ├── colors.py                   # Single source of truth for theme colors\n│   ├── theme_manager.py            # Dark / Light / Image mode switching\n', '│   ├── py.typed\n│   ├── theme_manager.py            # Dark / Light / Image mode switching\n'), ('README.md', '│   ├── py.typed\n│   ├── config.py                   # Central config & resource paths\n', '│   ├── py.typed\n│   ├── colors.py                   # Single source of truth for theme colors\n│   ├── config.py                   # Central config & resource paths\n'), ('README.md', '├── tools/                          # Maintenance scripts\n│   └── sync_colors.py              # Writes ui/colors.py and COLORS.md from the brand\n│\n', '├── tools/                          # Maintenance scripts\n│   └── sync_colors.py              # Writes utils/colors.py and COLORS.md from the brand\n│\n'), ('README.md', '\n- **Single source of truth for colors** — all theme values originate from `ui/colors.py`; no hardcoded color literals elsewhere in the codebase\n- **Strict package boundaries** — `core/` contains color science with no Qt dependencies beyond widgets, `ui/` handles presentation, `utils/` provides infrastructure\n', '\n- **Single source of truth for colors** — all theme values originate from `utils/colors.py`; no hardcoded color literals elsewhere in the codebase\n- **Strict package boundaries** — `core/` contains color science with no Qt dependencies beyond widgets, `ui/` handles presentation, `utils/` provides infrastructure\n'), ('RNV_Color_Palette_Manager.py', 'from core.color_math import ColorMath\nfrom ui.colors import (\n    BRAND_GOLD, BRAND_DARK_GOLD, BRAND_DARK_GOLD_DEEP, BRAND_GOLD_HOVER, DARK_THEME_COLORS,\n', 'from core.color_math import ColorMath\nfrom utils.colors import (\n    BRAND_GOLD, BRAND_DARK_GOLD, BRAND_DARK_GOLD_DEEP, BRAND_GOLD_HOVER, DARK_THEME_COLORS,\n'), ('TESTING.md', '| `core/palette_metadata.py` | 100% |\n| `ui/colors.py` | 100% |\n| `utils/undo_manager.py` | 99% |\n', '| `core/palette_metadata.py` | 100% |\n| `utils/colors.py` | 100% |\n| `utils/undo_manager.py` | 99% |\n'), ('brand_map.json', '{\n  "about": "Where each color in ui/colors.py comes from. A string is a name in rnv-brand (TABLE.key, or one of its own constants, in engine/brand.py); an object is a value this application owns, with the reason. Edit this file, then run: python tools/sync_colors.py",\n  "app": "RNV Color Palette Manager",\n  "color_file": "ui/colors.py",\n  "colors": {\n', '{\n  "about": "Where each color in utils/colors.py comes from. A string is a name in rnv-brand (TABLE.key, or one of its own constants, in engine/brand.py); an object is a value this application owns, with the reason. Edit this file, then run: python tools/sync_colors.py",\n  "app": "RNV Color Palette Manager",\n  "color_file": "utils/colors.py",\n  "colors": {\n'), ('core/color_slot.py', 'from utils.config import get_button_image_paths, MAX_SLOTS\nfrom ui.colors import (\n    SLOT_BORDER_THIN_COLOR, SLOT_BORDER_THICK_COLOR,\n', 'from utils.config import get_button_image_paths, MAX_SLOTS\nfrom utils.colors import (\n    SLOT_BORDER_THIN_COLOR, SLOT_BORDER_THICK_COLOR,\n'), ('core/palette_formats.py', 'from utils.logger import Logger, get_logger_instance\nfrom ui.colors import SVG_EXPORT_BG, SVG_EXPORT_STROKE, contrast_ink\n\n', 'from utils.logger import Logger, get_logger_instance\nfrom utils.colors import SVG_EXPORT_BG, SVG_EXPORT_STROKE, contrast_ink\n\n'), ('test_rnv_palette_manager.py', 'from core.palette_metadata import PaletteMetadata\nfrom ui.colors             import (\n    get_theme_colors, is_dark_theme,\n', 'from core.palette_metadata import PaletteMetadata\nfrom utils.colors          import (\n    get_theme_colors, is_dark_theme,\n'), ('test_rnv_palette_manager.py', 'class TestColorsModule(unittest.TestCase):\n    """ui/colors.py — theme dicts, brand constants, get_theme_colors."""\n\n', 'class TestColorsModule(unittest.TestCase):\n    """utils/colors.py — theme dicts, brand constants, get_theme_colors."""\n\n'), ('tests/color_values.py', "RNV-COLOR-SYNC (#53 A), 2026-10-17. The application's colors, brand and its\nown, are named in ui/colors.py, which brand_map.json names, and a test reads\nthem from there. Every other color value a test or the root suite writes is\n", "RNV-COLOR-SYNC (#53 A), 2026-10-17. The application's colors, brand and its\nown, are named in utils/colors.py, which brand_map.json names, and a test reads\nthem from there. Every other color value a test or the root suite writes is\n"), ('tests/test_app_mirror.py', "\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,\n                       LIGHT_THEME_COLORS as LIGHT)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'ui' / 'colors.py'\nABOUT = ROOT / 'ui' / 'about_dialog.py'\n", "\nfrom utils import colors\nfrom utils.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,\n                          LIGHT_THEME_COLORS as LIGHT)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'utils' / 'colors.py'\nABOUT = ROOT / 'ui' / 'about_dialog.py'\n"), ('tests/test_app_mirror.py', "#: was PINNED, each name with its value written beside it; the values are\n#: written into ui/colors.py from the register now, and held there.\nNEUTRALS = ('TRUE_BLACK', 'WHITE', 'BRAND_BLACK', 'APP_CARD', 'APP_BORDER',\n", "#: was PINNED, each name with its value written beside it; the values are\n#: written into utils/colors.py from the register now, and held there.\nNEUTRALS = ('TRUE_BLACK', 'WHITE', 'BRAND_BLACK', 'APP_CARD', 'APP_BORDER',\n"), ('tests/test_app_mirror.py', "                return node.value\n    raise AssertionError(f'{name} is not a dict literal in ui/colors.py')\n\n", "                return node.value\n    raise AssertionError(f'{name} is not a dict literal in utils/colors.py')\n\n"), ('tests/test_app_mirror.py', "    for name in NEUTRALS:\n        assert hasattr(colors, name), f'ui.colors has no {name}'\n    for mode, palette in PALETTES.items():\n", "    for name in NEUTRALS:\n        assert hasattr(colors, name), f'utils.colors has no {name}'\n    for mode, palette in PALETTES.items():\n"), ('tests/test_brand_mirror.py', '    RETIRED_OLD_DARK_GOLD_RGB_SPACED, RETIRED_OLD_DARK_GOLD_RGB_TIGHT)\nfrom ui import colors as C\n\n', '    RETIRED_OLD_DARK_GOLD_RGB_SPACED, RETIRED_OLD_DARK_GOLD_RGB_TIGHT)\nfrom utils import colors as C\n\n'), ('tests/test_brand_mirror.py', '    root = pathlib.Path(C.__file__).resolve().parent.parent\n    out = subprocess.run(["git", "ls-files"], cwd=root,\n                         capture_output=True, text=True).stdout.split()\n    for rel in out:\n', '    root = pathlib.Path(C.__file__).resolve().parent.parent\n    # --others --exclude-standard: a file a change adds is read before it is\n    # committed, as the commit will hold it. The color file\'s move to\n    # utils/colors.py (#63 A, 2026-10-18) is such a change.\n    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],\n                         cwd=root, capture_output=True, text=True).stdout.split()\n    for rel in out:\n'), ('tests/test_brand_mirror.py', '    assert len(files) > 15, f"the scan found only {len(files)} files"\n    assert any(rel == "ui/colors.py" for rel, _ in files), \\\n        "the scan is not reading the color file"\n', '    assert len(files) > 15, f"the scan found only {len(files)} files"\n    assert any(rel == "utils/colors.py" for rel, _ in files), \\\n        "the scan is not reading the color file"\n'), ('tests/test_button_key_names.py', '    """Each key\'s constant, as the value it holds."""\n    from ui import colors\n    return {key: getattr(colors, name) for key, name in pins.items()}\n\n\ndef _palettes():\n    from ui.colors import (DARK_THEME_COLORS, LIGHT_THEME_COLORS,\n                           IMAGE_MODE_COLORS)\n    return {"dark": DARK_THEME_COLORS, "light": LIGHT_THEME_COLORS,\n', '    """Each key\'s constant, as the value it holds."""\n    from utils import colors\n    return {key: getattr(colors, name) for key, name in pins.items()}\n\n\ndef _palettes():\n    from utils.colors import (DARK_THEME_COLORS, LIGHT_THEME_COLORS,\n                              IMAGE_MODE_COLORS)\n    return {"dark": DARK_THEME_COLORS, "light": LIGHT_THEME_COLORS,\n'), ('tests/test_button_press_step.py', '\nfrom ui.colors import (DARK_THEME_COLORS, IMAGE_MODE_COLORS,\n                       LIGHT_THEME_COLORS)\n\n', '\nfrom utils.colors import (DARK_THEME_COLORS, IMAGE_MODE_COLORS,\n                          LIGHT_THEME_COLORS)\n\n'), ('tests/test_collapse_505050.py', '    RETIRED_GRAY_50_RGBA_100, RETIRED_GRAY_50_RGBA_FRACTION)\nfrom ui.colors import GRAY_44\n\n', '    RETIRED_GRAY_50_RGBA_100, RETIRED_GRAY_50_RGBA_FRACTION)\nfrom utils.colors import GRAY_44\n\n'), ('tests/test_collapse_505050.py', '          \'image\': [\'scroll_handle\', \'scrollbar_handle\']}\nPALETTE_FILE = "ui/colors.py"\nDICT_NAMES = {\'dark\': \'DARK_THEME_COLORS\', \'image\': \'IMAGE_MODE_COLORS\',\n', '          \'image\': [\'scroll_handle\', \'scrollbar_handle\']}\nPALETTE_FILE = "utils/colors.py"\nDICT_NAMES = {\'dark\': \'DARK_THEME_COLORS\', \'image\': \'IMAGE_MODE_COLORS\',\n'), ('tests/test_collapse_505050.py', "def _palettes():\n    from ui.colors import (DARK_THEME_COLORS, IMAGE_MODE_COLORS,\n                           LIGHT_THEME_COLORS)\n    return {'dark': DARK_THEME_COLORS, 'image': IMAGE_MODE_COLORS,\n", "def _palettes():\n    from utils.colors import (DARK_THEME_COLORS, IMAGE_MODE_COLORS,\n                              LIGHT_THEME_COLORS)\n    return {'dark': DARK_THEME_COLORS, 'image': IMAGE_MODE_COLORS,\n"), ('tests/test_collapse_505050.py', '    _to_rgb(GRAY_44), so a later move of GRAY_44 reaches them too."""\n    from ui import colors\n    tree = ast.parse((ROOT / PALETTE_FILE).read_text(encoding="utf-8-sig"))\n', '    _to_rgb(GRAY_44), so a later move of GRAY_44 reaches them too."""\n    from utils import colors\n    tree = ast.parse((ROOT / PALETTE_FILE).read_text(encoding="utf-8-sig"))\n'), ('tests/test_constant_names.py', 'from color_values import EXAMPLE_BLACK, EXAMPLE_WHITE, RETIRED_WINDOWS_BLUE\nfrom ui import colors\n\n', 'from color_values import EXAMPLE_BLACK, EXAMPLE_WHITE, RETIRED_WINDOWS_BLUE\nfrom utils import colors\n\n'), ('tests/test_contrast_pairs.py', '\nfrom ui import colors as C\n\n', '\nfrom utils import colors as C\n\n'), ('tests/test_derived_values.py', '    RETIRED_SLOT_IMAGE_LITERAL)\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK,\n                       LIGHT_THEME_COLORS as LIGHT,\n                       IMAGE_MODE_COLORS as IMAGE,\n                       translucent,\n                       translucent_rgba)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / "ui" / "colors.py"\nPALETTES = {"DARK_THEME_COLORS": DARK, "LIGHT_THEME_COLORS": LIGHT,\n', '    RETIRED_SLOT_IMAGE_LITERAL)\nfrom utils import colors\nfrom utils.colors import (DARK_THEME_COLORS as DARK,\n                          LIGHT_THEME_COLORS as LIGHT,\n                          IMAGE_MODE_COLORS as IMAGE,\n                          translucent,\n                          translucent_rgba)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / "utils" / "colors.py"\nPALETTES = {"DARK_THEME_COLORS": DARK, "LIGHT_THEME_COLORS": LIGHT,\n'), ('tests/test_derived_values.py', '    """(where, call node, resolved value) for every helper call at module level\n    in ui/colors.py -- a constant, or a value in a module-level dict."""\n    tree = ast.parse(SRC.read_text(encoding="utf-8-sig"))\n', '    """(where, call node, resolved value) for every helper call at module level\n    in utils/colors.py -- a constant, or a value in a module-level dict."""\n    tree = ast.parse(SRC.read_text(encoding="utf-8-sig"))\n'), ('tests/test_derived_values.py', '    for name, (byte, _was) in ALPHAS.items():\n        assert hasattr(colors, name), f"ui.colors has no {name}"\n        value = getattr(colors, name)\n', '    for name, (byte, _was) in ALPHAS.items():\n        assert hasattr(colors, name), f"utils.colors has no {name}"\n        value = getattr(colors, name)\n'), ('tests/test_derived_values.py', '            elif not hasattr(colors, arg.id):\n                bad.append(f"{where}: the {pos} names {arg.id}, which ui.colors "\n                           f"does not define")\n', '            elif not hasattr(colors, arg.id):\n                bad.append(f"{where}: the {pos} names {arg.id}, which utils.colors "\n                           f"does not define")\n'), ('tests/test_derived_values.py', "\nLOWER8_MODULES = ('ui.colors', 'ui.theme_manager')\n#: Found when this was written; below the floor, the sweep has gone blind.\n", "\nLOWER8_MODULES = ('utils.colors', 'ui.theme_manager')\n#: Found when this was written; below the floor, the sweep has gone blind.\n"), ('tests/test_derived_values.py', "#: Where the derived constants live, and where their bases and alphas live.\nTUPLE_HOME = 'ui/colors.py'\nTUPLE_HOME_MODULE = 'ui.colors'\nTUPLE_BASES_MODULE = 'ui.colors'\n#: Each derived constant, by NAME: (helper, base, alpha or None). A register\n", "#: Where the derived constants live, and where their bases and alphas live.\nTUPLE_HOME = 'utils/colors.py'\nTUPLE_HOME_MODULE = 'utils.colors'\nTUPLE_BASES_MODULE = 'utils.colors'\n#: Each derived constant, by NAME: (helper, base, alpha or None). A register\n"), ('tests/test_error_red.py', '    RETIRED_MATERIAL_RED)\nfrom ui import colors\n\n', '    RETIRED_MATERIAL_RED)\nfrom utils import colors\n\n'), ('tests/test_gold_as_text.py', '\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK,\n                       IMAGE_MODE_COLORS as IMAGE,\n                       LIGHT_THEME_COLORS as LIGHT)\n\n', '\nfrom utils import colors\nfrom utils.colors import (DARK_THEME_COLORS as DARK,\n                          IMAGE_MODE_COLORS as IMAGE,\n                          LIGHT_THEME_COLORS as LIGHT)\n\n'), ('tests/test_gold_as_text.py', '            #: its palette with a lazy import inside each style function --\n            #: `from ui.colors import LIGHT_THEME_COLORS as colors` -- to break\n            #: a circular dependency. Reading only Assign missed that, so a\n', '            #: its palette with a lazy import inside each style function --\n            #: `from utils.colors import LIGHT_THEME_COLORS as colors` -- to break\n            #: a circular dependency. Reading only Assign missed that, so a\n'), ('tests/test_ink_on_the_golds.py', 'from color_values import EXAMPLE_BLACK, EXAMPLE_BLACK_SHORT, EXAMPLE_WHITE\nfrom ui.colors import BRAND_DARK_GOLD, BRAND_GOLD, TRUE_BLACK, WHITE\n\n', 'from color_values import EXAMPLE_BLACK, EXAMPLE_BLACK_SHORT, EXAMPLE_WHITE\nfrom utils.colors import BRAND_DARK_GOLD, BRAND_GOLD, TRUE_BLACK, WHITE\n\n'), ('tests/test_ladder_and_plate.py', "from color_values import REGISTER_GOLD_TEXT_GROUND_FLOOR, RETIRED_GRAY_D0\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK,\n                       IMAGE_MODE_COLORS as IMAGE,\n                       LIGHT_THEME_COLORS as LIGHT)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'ui/colors.py'\n\n", "from color_values import REGISTER_GOLD_TEXT_GROUND_FLOOR, RETIRED_GRAY_D0\nfrom utils import colors\nfrom utils.colors import (DARK_THEME_COLORS as DARK,\n                          IMAGE_MODE_COLORS as IMAGE,\n                          LIGHT_THEME_COLORS as LIGHT)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'utils/colors.py'\n\n"), ('tests/test_ladder_and_plate.py', "                return node.value\n    raise AssertionError(f'{name} is not a dict literal in ui/colors.py')\n\n", "                return node.value\n    raise AssertionError(f'{name} is not a dict literal in utils/colors.py')\n\n"), ('tests/test_ladder_and_plate.py', "    for name in list(NEW) + list(OVERLAYS):\n        assert hasattr(colors, name), f'ui.colors has no {name}'\n    for dict_name, keys in WIRED.items():\n", "    for name in list(NEW) + list(OVERLAYS):\n        assert hasattr(colors, name), f'utils.colors has no {name}'\n    for dict_name, keys in WIRED.items():\n"), ('tests/test_light_rewalk.py', '    REGISTER_APP_SURFACE_LIGHT_2, REGISTER_GOLD_TEXT_GROUND_FLOOR)\nfrom ui import colors as C\n\n', '    REGISTER_APP_SURFACE_LIGHT_2, REGISTER_GOLD_TEXT_GROUND_FLOOR)\nfrom utils import colors as C\n\n'), ('tests/test_light_wiring.py', "    REGISTER_APP_SURFACE_LIGHT_2, RETIRED_GRAY_F0, RETIRED_GRAY_F8, RETIRED_GRAY_FA)\nfrom ui import colors as C\n\nROOT = Path(__file__).resolve().parent.parent\nSOURCE = ROOT / 'ui/colors.py'\nPALETTES = ['DARK_THEME_COLORS', 'LIGHT_THEME_COLORS', 'IMAGE_MODE_COLORS']\n", "    REGISTER_APP_SURFACE_LIGHT_2, RETIRED_GRAY_F0, RETIRED_GRAY_F8, RETIRED_GRAY_FA)\nfrom utils import colors as C\n\nROOT = Path(__file__).resolve().parent.parent\nSOURCE = ROOT / 'utils/colors.py'\nPALETTES = ['DARK_THEME_COLORS', 'LIGHT_THEME_COLORS', 'IMAGE_MODE_COLORS']\n"), ('tests/test_muted_and_disabled_text.py', '\nfrom ui.colors import (DARK_THEME_COLORS, GRAY_66, GRAY_88, IMAGE_MODE_COLORS,\n                       LIGHT_THEME_COLORS)\n\n', '\nfrom utils.colors import (DARK_THEME_COLORS, GRAY_66, GRAY_88, IMAGE_MODE_COLORS,\n                          LIGHT_THEME_COLORS)\n\n'), ('tests/test_muted_and_disabled_text.py', 'ROOT = pathlib.Path(__file__).resolve().parent.parent\nCOLORS_PY = ROOT / "ui" / "colors.py"\n\n', 'ROOT = pathlib.Path(__file__).resolve().parent.parent\nCOLORS_PY = ROOT / "utils" / "colors.py"\n\n'), ('tests/test_named_and_used.py', '#: Where this application writes its colors: the one place a literal belongs.\nCOLOR_MODULES = ("ui/colors.py",)\n#: Where its palettes are written: their own keys are not lookups.\nPALETTE_MODULES = COLOR_MODULES\nSKIP_DIRS = {"tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__"}\n\nfrom ui.colors import DARK_THEME_COLORS, IMAGE_MODE_COLORS, LIGHT_THEME_COLORS  # noqa: E402\n\n', '#: Where this application writes its colors: the one place a literal belongs.\nCOLOR_MODULES = ("utils/colors.py",)\n#: Where its palettes are written: their own keys are not lookups.\nPALETTE_MODULES = COLOR_MODULES\nSKIP_DIRS = {"tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__"}\n\nfrom utils.colors import DARK_THEME_COLORS, IMAGE_MODE_COLORS, LIGHT_THEME_COLORS  # noqa: E402\n\n'), ('tests/test_qt_color_slot.py', '\n    from ui.colors import CLIPBOARD_PREVIEW_COLOR\n    from ui.settings_dialog import SettingsDialog\n', '\n    from utils.colors import CLIPBOARD_PREVIEW_COLOR\n    from ui.settings_dialog import SettingsDialog\n'), ('tests/test_qt_color_slot_paint.py', '    """border_style=\'thin\' draws a 1px border at row/col 0."""\n    from ui.colors import SLOT_BORDER_THIN_COLOR\n\n', '    """border_style=\'thin\' draws a 1px border at row/col 0."""\n    from utils.colors import SLOT_BORDER_THIN_COLOR\n\n'), ('tests/test_qt_color_slot_paint.py', '    """\n    from ui.colors import SLOT_BORDER_THICK_COLOR\n\n', '    """\n    from utils.colors import SLOT_BORDER_THICK_COLOR\n\n'), ('tests/test_qt_color_slot_paint.py', '    """A selected slot draws a 3px gold border."""\n    from ui.colors import BRAND_GOLD_RGB\n\n', '    """A selected slot draws a 3px gold border."""\n    from utils.colors import BRAND_GOLD_RGB\n\n'), ('tests/test_qt_color_slot_paint.py', '    """An unselected slot does NOT draw the gold selection border."""\n    from ui.colors import BRAND_GOLD_RGB\n\n', '    """An unselected slot does NOT draw the gold selection border."""\n    from utils.colors import BRAND_GOLD_RGB\n\n'), ('tests/test_qt_color_slot_paint.py', '    """_search_highlight=True draws a glow border around the slot."""\n    from ui.colors import SEARCH_HIGHLIGHT_COLOR\n\n', '    """_search_highlight=True draws a glow border around the slot."""\n    from utils.colors import SEARCH_HIGHLIGHT_COLOR\n\n'), ('tests/test_register_wiring.py', "\nfrom ui import colors\nfrom ui.colors import (DARK_THEME_COLORS as DARK,\n                       IMAGE_MODE_COLORS as IMAGE)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'ui/colors.py'\n\n", "\nfrom utils import colors\nfrom utils.colors import (DARK_THEME_COLORS as DARK,\n                          IMAGE_MODE_COLORS as IMAGE)\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'utils/colors.py'\n\n"), ('tests/test_status_register.py', '    RETIRED_OWN_DARK_ERROR_TEXT)\nfrom ui import colors\n\n', '    RETIRED_OWN_DARK_ERROR_TEXT)\nfrom utils import colors\n\n'), ('tests/test_status_register.py', "def _palettes():\n    from ui.colors import DARK_THEME_COLORS as D, LIGHT_THEME_COLORS as L, IMAGE_MODE_COLORS as I; P={'dark':D,'light':L,'image':I}\n    return P\n", "def _palettes():\n    from utils.colors import DARK_THEME_COLORS as D, LIGHT_THEME_COLORS as L, IMAGE_MODE_COLORS as I; P={'dark':D,'light':L,'image':I}\n    return P\n"), ('tests/test_surface_alignment.py', '\nfrom ui.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,\n                          LIGHT_THEME_COLORS as LIGHT)\nfrom ui.colors import APP_SURFACE_LIGHT_3, BRAND_BLACK\n\n', '\nfrom utils.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,\n                          LIGHT_THEME_COLORS as LIGHT)\nfrom utils.colors import APP_SURFACE_LIGHT_3, BRAND_BLACK\n\n'), ('ui/__init__.py', '\nfrom ui.colors import (\n    DARK_THEME_COLORS,\n    LIGHT_THEME_COLORS,\n    IMAGE_MODE_COLORS,\n    get_theme_colors,\n    is_dark_theme,\n    ThemeName,\n    ThemeDict,\n    BRAND_GOLD,\n    BRAND_DARK_GOLD,\n)\nfrom ui.theme_manager import ThemeManager\n', '\nfrom ui.theme_manager import ThemeManager\n'), ('ui/__init__.py', '__all__ = [\n    # Theme dictionaries & helpers\n    "DARK_THEME_COLORS",\n    "LIGHT_THEME_COLORS",\n    "IMAGE_MODE_COLORS",\n    "get_theme_colors",\n    "is_dark_theme",\n    "ThemeName",\n    "ThemeDict",\n    # Brand colors\n    "BRAND_GOLD",\n    "BRAND_DARK_GOLD",\n    # Theme manager\n', '__all__ = [\n    # Theme manager\n'), ('ui/about_dialog.py', 'from utils.logger import Logger, get_logger_instance\nfrom ui.colors import BRAND_GOLD, TRUE_BLACK, WHITE\n\n', 'from utils.logger import Logger, get_logger_instance\nfrom utils.colors import BRAND_GOLD, TRUE_BLACK, WHITE\n\n'), ('ui/about_dialog.py', '    """\n    from ui.colors import get_theme_colors\n    return get_theme_colors(getattr(dialog, "_theme_name", "dark"))["accent_ink"]\n', '    """\n    from utils.colors import get_theme_colors\n    return get_theme_colors(getattr(dialog, "_theme_name", "dark"))["accent_ink"]\n'), ('ui/about_dialog.py', '        """\n        from ui.colors import get_theme_colors\n        font_family = get_font_family()\n', '        """\n        from utils.colors import get_theme_colors\n        font_family = get_font_family()\n'), ('ui/batch_export_dialog.py', 'from utils.logger import Logger, get_logger_instance\nfrom ui.colors import (\n    STATUS_ERROR_TEXT,\n', 'from utils.logger import Logger, get_logger_instance\nfrom utils.colors import (\n    STATUS_ERROR_TEXT,\n'), ('ui/image_upload_dialog.py', 'from utils.logger import Logger, get_logger_instance\nfrom ui.colors import GRAY_66, GRAY_EE\n\n', 'from utils.logger import Logger, get_logger_instance\nfrom utils.colors import GRAY_66, GRAY_EE\n\n'), ('ui/preview_grid.py', 'from utils.config import ICONS_DIR\nfrom ui.colors import PREVIEW_GRID_BORDER\n\n', 'from utils.config import ICONS_DIR\nfrom utils.colors import PREVIEW_GRID_BORDER\n\n'), ('ui/settings_dialog.py', 'from utils.font_loader import get_font_family\nfrom ui.colors import (\n    BRAND_GOLD, BRAND_DARK_GOLD, BRAND_DARK_GOLD_DEEP, BRAND_GOLD_HOVER,\n', 'from utils.font_loader import get_font_family\nfrom utils.colors import (\n    BRAND_GOLD, BRAND_DARK_GOLD, BRAND_DARK_GOLD_DEEP, BRAND_GOLD_HOVER,\n'), ('ui/theme_manager.py', '\nfrom ui.colors import (\n    ThemeName,\n', '\nfrom utils.colors import (\n    ThemeName,\n'), ('utils/color_history.py', 'from utils.logger import Logger, get_logger_instance\nfrom ui.colors import DATA_DEFAULT_COLOR, HISTORY_SWATCH_BORDER\n\n', 'from utils.logger import Logger, get_logger_instance\nfrom utils.colors import DATA_DEFAULT_COLOR, HISTORY_SWATCH_BORDER\n\n'), ('utils/dialog_helper.py', '        """Get dark theme dialog stylesheet."""\n        # Lazy import to avoid circular dependency (utils -> ui -> utils)\n        from ui.colors import (\n            DARK_THEME_COLORS as colors,\n', '        """Get dark theme dialog stylesheet."""\n        from utils.colors import (\n            DARK_THEME_COLORS as colors,\n'), ('utils/dialog_helper.py', '        """Get light theme dialog stylesheet."""\n        from ui.colors import (\n            LIGHT_THEME_COLORS as colors,\n', '        """Get light theme dialog stylesheet."""\n        from utils.colors import (\n            LIGHT_THEME_COLORS as colors,\n'), ('utils/settings_manager.py', 'from utils.logger import Logger, get_logger_instance\nfrom ui.colors import SESSION_FALLBACK_COLOR, SESSION_FALLBACK_COLOR_IMAGE\n\n', 'from utils.logger import Logger, get_logger_instance\nfrom utils.colors import SESSION_FALLBACK_COLOR, SESSION_FALLBACK_COLOR_IMAGE\n\n')]

#: Files carried whole: most of what they held leaves them
FULL = {}

#: Files this round creates
NEW_FILES = {}

#: sha256 of every file as this round writes it
WANT = {'.github/workflows/brand-sync.yml': '6e9b4669cb15de59674ed9bdc57e9958f8e7bd014e6a10d9b071b0ebe1b56ced', 'ARCHITECTURE.md': '6f2502eef0303c7733f4ab9d135b57a627acaafd0b048a0135dc99963eb6c38a', 'COLORS.md': '78dc93756af5487dedd115450d21059e88319ace999b8c54e122ab5a76150904', 'README.md': '8cd5fe8ed94aa4e0e630086a28a742e952548693dd86f71360f12f30eca8921f', 'RNV_Color_Palette_Manager.py': '76a6608b404d4edd30e5089e34384349f24f408cad2af48de2ccbdb5c64ca6ec', 'TESTING.md': 'beea304098f39b0c925275f6d083d2f6446b89a17a1fd54c7e6daafe4c408810', 'brand_map.json': 'bab99b73a4453ad54fbfc9b3e942a9f86d3a314f570106ec10d3b80f65cf2751', 'core/color_slot.py': 'd4e44fcd81813d64df252d5001a1536df4d983177b337f8b35095da1cb652281', 'core/palette_formats.py': 'e654fd53838e3498c8e9b3e9f85afacca8401bdf30ac5abb9f2d885d8cf5c7bb', 'test_rnv_palette_manager.py': 'f4e1e873b33d62e2242803eb0396083183598c9efdc58075bf464549e493bc11', 'tests/color_values.py': 'aeafdfa15532fbf8865e083b6975f402ba2b4eeb205bf5e1e9aa0ff874e64803', 'tests/test_app_mirror.py': '8daba78803b40d0a913b0489d6f6d97a40299f2f91698993b850aa98a420f649', 'tests/test_brand_mirror.py': '935ffabc735a69f8100d46e1b619a0851cc04c113675d6a169291b1a12618f1c', 'tests/test_button_key_names.py': '4e5a1551fab3801000063c9bde3760f4cb0dada894cfbd57ad77b4f6cef2e5e0', 'tests/test_button_press_step.py': '99c5d0bcc118e009f8edfafbe5481661185dd08ea80d81e2703838ea3d5e7c2a', 'tests/test_collapse_505050.py': '084160e56d2afd647cfc33e5b6b42ddc36da78fcde6522b0b53616eb4b9a248f', 'tests/test_constant_names.py': '23d107f3a5070e399d41ff2a858bba8c6ee70cbb71f07ff203fdfaafa6cd5d93', 'tests/test_contrast_pairs.py': 'e7d216b0fc566781ef4dbf10779051dbdfb1183dde942881c22f5a8441c7f8c6', 'tests/test_derived_values.py': '2d664af309b462e3bf9a9d7766acf900ca4d231f75b434c70adc5bc637f3d109', 'tests/test_error_red.py': '079f110bd95a9a86205b58d9ff1a6d9558d5fa524e67f69bb286c9c51de7c18d', 'tests/test_gold_as_text.py': '301e687b21c6b53d24710acd724f6fb6819081b38e3180933e8efc4488d95f11', 'tests/test_ink_on_the_golds.py': '7c3cc6f1fe55c615cc64ce332fbb9c13d0d6f73ff8839ea0b48b903c5754bd7e', 'tests/test_ladder_and_plate.py': '1fe264cdcc8df8eef0b7cb200c8c7e2ecfdb25e1355e738ad3760079bc1fe9fb', 'tests/test_light_rewalk.py': 'b6211169cb040db89788df32225252a8e97ea9a6f9c6cc3f1f653ddc995abc40', 'tests/test_light_wiring.py': '00f9d199a78becb11df708c7e855cff2c15234b36d7583e623a6ca0ce6032e58', 'tests/test_muted_and_disabled_text.py': '383353dab0ef7af4f22e10c801506c590c8df3cdeb5793e247b44f2bfd125d6b', 'tests/test_named_and_used.py': 'ace4ae417279668c52dfe0c1bcf9663a3ab84d6f11510f9342616c0b6144f498', 'tests/test_qt_color_slot.py': '33bc400a275fc555bfd88118c22b700694ee5b4a137265e3173f2baae1b5b5a9', 'tests/test_qt_color_slot_paint.py': '74892799e8bcd80d1813028fdb81d85e9ec5b5e5c4c3afe645bf55fc264491b2', 'tests/test_register_wiring.py': 'cb22c9227c02d04e067207a333aa61c01fe4999e24a258cc1015f12aecdb6775', 'tests/test_status_register.py': 'b921bd5cfc76b764e199e7e13601d2e49f4f01e80b58ad96670d8faa9f272d46', 'tests/test_surface_alignment.py': '3b5be073184827de11ecd8ca96d91f2f44ccb80d86bb280db02d762bbb9555de', 'ui/__init__.py': '2ad249462fe227c96c1960e9cf7717355bd445f57f4f1d862fabd1ec6e668121', 'ui/about_dialog.py': '0a099145dca81921a4f2c59fba9132db640def32fbaf075a679177f1627aafa4', 'ui/batch_export_dialog.py': '6ba5e87bbe5ab07a7ef0f4a120bf299cc065b309117cee0cd0fe8b66b7bd6d5c', 'ui/image_upload_dialog.py': 'ebc60053b20512b03d721907c514a845fcf9800d3ca162bd4bce007c0994826f', 'ui/preview_grid.py': 'fe856ee7b171b993491bb05d8456bfec79d2d74bd997ff62c013d371389f7655', 'ui/settings_dialog.py': 'ab7088f648001baad59bc0d536c5aff74467d523d34f05ab3a81c2c0f56270fe', 'ui/theme_manager.py': 'd9bfca7e19ff3f098ca5aa5b5b3bdc93e2793ba4771a5abe7f3c11f90ff0bf8b', 'utils/color_history.py': '7117405865bf6c73ad4e10266a9243775bf4e7e277624138a35bd5b91f030a56', 'utils/colors.py': '2c2804bf76065eecc600cdfcb73499d2142127d36283221c6a74196dbc9ba303', 'utils/dialog_helper.py': 'a5b26a650c330580e5041f39e4b7d554d68fe437cc3b8b480b440c642924e230', 'utils/settings_manager.py': '745e9d32a924687e1f8cf86fbbb4cd0c71a8008c68c306b5bbf2029a99d7386d'}


def edits(tree) -> None:
    for rel, was in BASE_SHAS.items():
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        if got != was:
            raise Stop(f"{rel} is not the head's file this round was derived from ({got[:12]}). "
                       f"Nothing was written. The file moved; re-derive before trusting the script.",
                       EXIT_CANNOT_RUN)
    for new, old in RENAMES:
        if (tree.root / new).exists():
            raise Stop(f"{new} already exists here, and this round moves {old} there. "
                       f"Nothing was written.", EXIT_CANNOT_RUN)
        text = tree.read(old)
        tree.write(new, text)
        tree.form[new] = tree.form[old]          # a moved file keeps its BOM and line endings
        tree.delete(old)
    for rel, old, new in SUBS:
        tree.sub(rel, old, new)
    for rel, body in FULL.items():
        tree.write(rel, body)                     # BASE_SHAS held the head's file
    for rel, body in NEW_FILES.items():
        if (tree.root / rel).exists():
            raise Stop(f"{rel} already exists here, and this round creates it. Nothing was written.",
                       EXIT_CANNOT_RUN)
        tree.write(rel, body)


def _checkout(tree) -> list[str]:
    """Every file in this checkout as this round leaves it: what git tracks, less
    what the round removes, and what it writes."""
    try:
        out = subprocess.run(["git", "-C", str(tree.root), "ls-files", "-z"], capture_output=True,
                             check=True).stdout.decode("utf-8")
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as e:
        raise Stop(f"git could not list this checkout's files ({e}). This round reads every one of "
                   f"them, to see that nothing is left at the old place. Nothing was written.",
                   EXIT_CANNOT_RUN)
    tracked = {rel for rel in out.split(chr(0)) if rel}
    return sorted((tracked - tree.deleted) | set(tree.files))


def _text(tree, rel: str):
    if rel in tree.files:
        return tree.files[rel]
    raw = (tree.root / rel).read_bytes()
    if b"\0" in raw:
        return None
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


class _Modules:
    """Run module text as a module of this checkout, with the round's own files
    standing in for theirs: none of them is on disk yet."""

    def __init__(self, tree) -> None:
        self.tree = tree
        self.saved = {}

    def __enter__(self):
        self.added = str(self.tree.root) not in sys.path
        if self.added:
            sys.path.insert(0, str(self.tree.root))
        return self

    def load(self, rel: str, text: str, register: bool = False):
        name = rel[:-3].replace("/", ".")
        module = types.ModuleType(name)
        module.__file__ = str(self.tree.root / rel)
        if register:
            self.saved.setdefault(name, sys.modules.get(name))
            sys.modules[name] = module
        exec(compile(text, rel, "exec"), module.__dict__)
        return module

    def __exit__(self, *exc) -> None:
        for name, module in self.saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
        if self.added:
            sys.path.remove(str(self.tree.root))


def _comparable(value) -> bool:
    """A value that says what it is: compared by ==, not by identity or by repr."""
    if isinstance(value, (types.ModuleType, types.FunctionType, type)) or callable(value):
        return False
    return type(value).__eq__ is not object.__eq__


def _values(module) -> dict:
    return {k: v for k, v in vars(module).items() if not k.startswith("__") and _comparable(v)}


def _class_values(module) -> dict:
    """Each class the module defines -> its own attributes that say what they are."""
    out = {}
    for k, v in vars(module).items():
        if isinstance(v, type) and v.__module__ == module.__name__:
            out[k] = {a: x for a, x in vars(v).items() if not a.startswith("__") and _comparable(x)}
    return out


def _same(a, b) -> bool:
    return type(a) is type(b) and a == b


def _reads_from_config(src: str) -> list[str]:
    """Each moved name this source reads from utils.config: imported from it, or
    read as an attribute of a name bound to it."""
    tree = ast.parse(src)
    aliases, found = set(), []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module == "utils.config":
            found += [a.name for a in n.names if a.name in MOVED]
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module == "utils":
            aliases |= {a.asname or a.name for a in n.names if a.name == "config"}
        elif isinstance(n, ast.Import):
            aliases |= {a.asname for a in n.names if a.name == "utils.config" and a.asname}
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and n.attr in MOVED:
            v = n.value
            if isinstance(v, ast.Name) and v.id in aliases:
                found.append(n.attr)
            elif (isinstance(v, ast.Attribute) and v.attr == "config" and isinstance(v.value, ast.Name)
                  and v.value.id == "utils"):
                found.append(n.attr)
    return found


#: What names the old place, in a file of any kind
OLD_PLACE_TEXT = re.compile(r"(?<![\w.])ui\.colors\b|\bfrom\s+ui\s+import\s+colors\b"
                            r"|(?<![\w./\\-])ui/colors\.py\b|([\"'])ui\1\s*/\s*([\"'])colors\.py\2")


def checks(tree) -> None:
    root_files = _checkout(tree)
    # ---- no value moves
    with _Modules(tree) as m:
        before = m.load(OLD_PLACE, _original(tree, OLD_PLACE))
        colors = m.load(COLOR_FILE, tree.read(COLOR_FILE), register=True)
        was, now = _values(before), _values(colors)
        if MOVED:
            config = m.load("utils/config.py", tree.read("utils/config.py"))
            stayed = _values(config)
            missing = sorted(set(MOVED) - set(vars(colors)))
            assert not missing, f"{COLOR_FILE} does not define {missing}"
            moved = sorted(k for k in was if not _same(was[k], (now if k in MOVED else stayed).get(k)))
            assert not moved, f"a value moved: {moved}"
            classes_was, classes_now = _class_values(before), _class_values(config)
            for cls, attrs in classes_was.items():
                gone = sorted(a for a, v in attrs.items() if not _same(v, classes_now.get(cls, {}).get(a)))
                assert not gone, f"{cls} serves other values: {gone}"
            for cls, attrs in classes_now.items():
                for a, v in attrs.items():
                    if a in MOVED and isinstance(v, dict):
                        assert v is getattr(colors, a), f"{cls}.{a} is a copy, not {COLOR_FILE}'s {a}"
            defined = sorted(t.id for n in ast.parse(tree.read("utils/config.py")).body
                             if isinstance(n, (ast.Assign, ast.AnnAssign))
                             for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
                             if isinstance(t, ast.Name) and t.id in MOVED)
            assert not defined, f"utils/config.py defines colors again: {defined}"
        else:
            assert sorted(was) == sorted(now), f"{COLOR_FILE} defines other names: {sorted(set(was) ^ set(now))}"
            moved = sorted(k for k in was if not _same(was[k], now[k]))
            assert not moved, f"a value moved: {moved}"
        assert len(was) >= 40, f"only {len(was)} values compared -- the comparison is blind"
    # ---- nothing is left at the old place, in any file of the checkout
    left, elsewhere = [], []
    for rel in root_files:
        if rel.endswith(('coverage_report.txt',)) or rel.rsplit("/", 1)[-1].upper().startswith("LICENSE"):
            continue
        text = _text(tree, rel)
        if text is None or "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
            continue
        found = []
        if MOVED:
            if rel.endswith(".py") and rel != "utils/config.py":
                found = [f"{rel}: reads {name} from utils.config" for name in _reads_from_config(text)]
        elif OLD_PLACE_TEXT.search(text):
            found = [f"{rel}: names {OLD_PLACE}"]
        (left if rel in tree.files else elsewhere).extend(found)
    if elsewhere:
        raise Stop("files this round does not write still reach the old place:\n  " + "\n  ".join(elsewhere[:20])
                   + "\nThe checkout moved; re-derive before trusting the script. Nothing was written.",
                   EXIT_CANNOT_RUN)
    assert not left, "the old place is still read:\n  " + "\n  ".join(left[:20])
    assert COLOR_FILE in root_files, f"{COLOR_FILE} is not here"
    if not MOVED:
        assert OLD_PLACE not in root_files, f"{OLD_PLACE} is still here"
    # ---- the map names the new place
    brand_map = json.loads(tree.read("brand_map.json"))
    assert brand_map["color_file"] == COLOR_FILE, brand_map["color_file"]
    for palette in brand_map.get("palettes", []):
        assert palette["file"] == COLOR_FILE, palette
    # ---- every file this round writes, as it writes it
    assert sorted(tree.files) == sorted(WANT), f"this round writes {sorted(tree.files)}"
    assert sorted(tree.deleted) == sorted(old for _, old in RENAMES), f"this round removes {sorted(tree.deleted)}"
    for rel, want in WANT.items():
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        assert got == want, f"{rel} is not the file this round writes: {got[:12]}"

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
