"""the palette manager's colours come from the brand, through brand_map.json

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-color-palette-manager, derived against a fresh clone at the live head (8ad8709).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-16, the colour-sync proposal and its pilot: #36 A (the map is
brand_map.json), #37 A (the colour file takes the values in place), #38 B (a
daily check opens a pull request only when a colour moved), #39 A (one
in-sync check instead of values written into tests), #40 A (COLORS.md),
#41 A (the fleet chart stays published), #42 A (the app's own colours are
in the map, with reasons), #43 A (this app first), #44 A (a marker on each
line), #45 A (the golds follow the register's accent names), #46 A (data
colours are the app's own).

WHAT LANDS.
  brand_map.json               where each of 30 colours comes from: 14 brand
                               names, 16 of the app's own, each with a reason
  tools/sync_colors.py         writes those values into ui/colors.py, and
                               COLORS.md, from the map and the pinned brand
  ui/colors.py                 a note at the top and a marker on 30 lines;
                               NO VALUE MOVES
  COLORS.md                    the app's colour chart
  tests/test_colours_in_sync.py  every value, once, against the brand
  .github/workflows/brand-sync.yml  the daily check
  ten test files               a brand value written as a hex code now reads
                               the name it takes; grounds read by name
  README.md                    the four new files in the project tree

THE DAILY CHECK NEEDS ONE SETTING: Settings > Actions > General > Workflow
permissions > "Allow GitHub Actions to create and approve pull requests".
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import types
from pathlib import Path

REPO = 'rnv-color-palette-manager'
SENTINEL = 'RNV-COLOUR-SYNC (2026-10-16)'
SENTINEL_FILE = 'ui/colors.py'
GUARD = 'tests/test_colours_in_sync.py'
GUARD_FILES = ['tests/test_app_mirror.py', 'tests/test_brand_mirror.py', 'tests/test_button_key_names.py', 'tests/test_colours_in_sync.py', 'tests/test_constant_names.py', 'tests/test_error_red.py', 'tests/test_ladder_and_plate.py', 'tests/test_light_rewalk.py', 'tests/test_register_wiring.py', 'tests/test_status_register.py', 'tests/test_surface_alignment.py']
#: Every test file this round writes, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *GUARD_FILES]
DESCRIPTION = "the palette manager's colours come from the brand, through brand_map.json"

#: EXACTLY WHAT CI RUNS. Both workflows run `python run_tests.py`, which runs
#: the locked root suite under unittest and then tests/ under pytest.
SUITES = [("python run_tests.py  (both CI workflows)",
           [sys.executable, "run_tests.py"])]

SHADOWS = {'conftest.py', 'run_tests.py', 'test_rnv_palette_manager.py', 'sync_colors.py',
           'test_app_mirror.py', 'test_brand_mirror.py', 'test_button_key_names.py', 'test_colours_in_sync.py', 'test_constant_names.py', 'test_error_red.py', 'test_ladder_and_plate.py', 'test_light_rewalk.py', 'test_register_wiring.py', 'test_status_register.py', 'test_surface_alignment.py'}

LEFT_ALONE = [
    "every colour the app draws: all 57 values ui/colors.py defines are what they were.",
    "the image files, and their paths.",
    "the root suite, test_rnv_palette_manager.py, which is locked: its test_light_hover_dark_grey holds #333333, APP.border, and would ask for an edit if the register moved that grey.",
    "tests that give a helper an example colour (translucent('#1a1a1a', ...), contrast_ink('#ffffff')): they test the helper, not the brand.",
    "the register's own boundary values, written as the register publishes them: the gold text floor #e8e8e8 and the light rungs the re-walk was walked against.",
    "the record of retired values and what replaced them (COLLAPSE, RETIRED).",
    "the provenance maps GOLD_PROVENANCE and APP_PROVENANCE: the new guard holds that they agree with brand_map.json.",
]

NEW_FILES = {'brand_map.json': '{\n  "about": "Where each colour in ui/colors.py comes from. A string is a name in rnv-brand (TABLE.key in engine/brand.py); an object is a value this application owns, with the reason. Edit this file, then run: python tools/sync_colors.py",\n  "app": "RNV Color Palette Manager",\n  "colour_file": "ui/colors.py",\n  "colours": {\n    "BRAND_GOLD": "APP.accent",\n    "BRAND_DARK_GOLD": "APP.accent-light-mode",\n    "TRUE_BLACK": "PERMANENT.black",\n    "WHITE": "PERMANENT.white",\n    "BRAND_BLACK": "PERMANENT.charcoal",\n    "APP_CARD": "APP.card",\n    "APP_BORDER": "APP.border",\n    "APP_TEXT": "APP.text",\n    "APP_TEXT_DIM": "APP.text-dim",\n    "APP_PANEL_HOVER": "APP.panel-hover",\n    "GREY_44": {\n      "app": "#444444",\n      "why": "grey(4) on the register\'s ink grid, which the register states as a rule and does not name. The pressed plate and the scrollbar handle (RNV-COLLAPSE-505050)."\n    },\n    "APP_HOVER_LIGHT": "APP.hover-light",\n    "APP_SURFACE_LIGHT_3": "APP.surface-light-3",\n    "GREY_EE": {\n      "app": "#eeeeee",\n      "why": "grey(14) on the ink grid. Static light surfaces, a list header and a scroll ground, that share hover-light\'s hex without being a hover."\n    },\n    "GREY_CC": {\n      "app": "#cccccc",\n      "why": "grey(12) on the ink grid. The light-mode border."\n    },\n    "GREY_88": {\n      "app": "#888888",\n      "why": "grey(8) on the ink grid. Muted text on dark; a scrollbar handle\'s hover on light."\n    },\n    "GREY_55": {\n      "app": "#555555",\n      "why": "grey(5) on the ink grid. Disabled text and a checkbox edge on dark."\n    },\n    "SELECTION_OVERLAY_COLOR": {\n      "app": "rgba(0,120,215,200)",\n      "why": "The blue overlay drawn during gradient and contrast selection, painted where no theme palette reaches."\n    },\n    "GREY_66": {\n      "app": "#666666",\n      "why": "grey(6) on the ink grid. Muted text in light mode."\n    },\n    "SEARCH_HIGHLIGHT_COLOR": {\n      "app": [0, 255, 100],\n      "why": "The bright green border on slots that match a search."\n    },\n    "SLOT_BORDER_THICK_COLOR": {\n      "app": [60, 60, 60],\n      "why": "The thick slot border."\n    },\n    "STATUS_ERROR_TEXT": "STATUS.error-text",\n    "STATUS_ERROR_TEXT_LIGHT": "STATUS.error-text-light",\n    "SVG_EXPORT_BG": {\n      "app": "#ffffff",\n      "why": "Data, not chrome: the background of an exported SVG palette file. White by meaning, so it does not follow the brand\'s white."\n    },\n    "SVG_EXPORT_STROKE": {\n      "app": "#000000",\n      "why": "Data, not chrome: the swatch stroke in an exported SVG palette file."\n    },\n    "DATA_DEFAULT_COLOR": {\n      "app": "#000000",\n      "why": "Data, not chrome: the value a colour record starts with."\n    },\n    "SESSION_FALLBACK_COLOR": {\n      "app": "#a9a9a9",\n      "why": "Data: the grey a restored session or a reset setting falls back to."\n    },\n    "SESSION_FALLBACK_COLOR_IMAGE": {\n      "app": "#000000",\n      "why": "Data: the image-mode fallback for a reset setting."\n    },\n    "TRANSPARENT_RGBA": {\n      "app": [0, 0, 0, 0],\n      "why": "Fully transparent: ghost pixmaps and cleared palettes."\n    },\n    "DEFAULT_SLOT_COLOR": {\n      "app": "#a9a9a9",\n      "why": "The colour a new slot starts with in dark and light mode."\n    }\n  }\n}\n', 'COLORS.md': "# Colours: RNV Color Palette Manager\n\nGenerated by `python tools/sync_colors.py` from `brand_map.json`, `ui/colors.py` and rnv-brand at `b4fa970`, the commit pinned in `tests/requirements-dev.txt`. Don't edit it by hand: change the map and run the script. `tests/test_colours_in_sync.py` fails when this file is out of date.\n\n14 colours come from the brand and 16 are the application's own. 12 more are worked out in `ui/colors.py` from those, so they follow them.\n\n## From the brand\n\n| brand name | value | the app's name | made from it in the app |\n|---|---|---|---|\n| `PERMANENT.charcoal` | `#1a1a1a` | `BRAND_BLACK` | `APP_PANEL_OVERLAY` = `translucent(BRAND_BLACK, IMAGE_OVERLAY_ALPHA)` → `#ed1a1a1a` |\n| `PERMANENT.black` | `#000000` | `TRUE_BLACK` | `APP_WINDOW_OVERLAY` = `translucent(TRUE_BLACK, IMAGE_OVERLAY_ALPHA)` → `#ed000000`<br>`SEARCH_DIM_OVERLAY` = `translucent_tuple(TRUE_BLACK, SEARCH_DIM_ALPHA)` → `(0, 0, 0, 140)`<br>`SIZE_OVERLAY_BG` = `translucent_rgba(TRUE_BLACK, SIZE_OVERLAY_ALPHA)` → `rgba(0, 0, 0, 200)`<br>`PREVIEW_GRID_BORDER` = `_to_rgb(TRUE_BLACK)` → `(0, 0, 0)`<br>`DEFAULT_SLOT_COLOR_IMAGE_RGB` = `translucent_tuple(TRUE_BLACK, SLOT_IMAGE_ALPHA)` → `(0, 0, 0, 171)` |\n| `PERMANENT.white` | `#ffffff` | `WHITE` | — |\n| `APP.card` | `#2a2a2a` | `APP_CARD` | — |\n| `APP.panel-hover` | `#3a3a3a` | `APP_PANEL_HOVER` | — |\n| `APP.border` | `#333333` | `APP_BORDER` | — |\n| `APP.text` | `#dddddd` | `APP_TEXT` | — |\n| `APP.text-dim` | `#aaaaaa` | `APP_TEXT_DIM` | — |\n| `APP.surface-light-3` | `#f5f5f5` | `APP_SURFACE_LIGHT_3` | — |\n| `APP.hover-light` | `#eeeeee` | `APP_HOVER_LIGHT` | — |\n| `APP.accent` | `#d2bc93` | `BRAND_GOLD` | `BRAND_GOLD_HOVER` = `lighten(BRAND_GOLD, 13)` → `#dfc9a0`<br>`BRAND_GOLD_RGB` = `_to_rgb(BRAND_GOLD)` → `(210, 188, 147)` |\n| `APP.accent-light-mode` | `#8c7337` | `BRAND_DARK_GOLD` | `BRAND_DARK_GOLD_DEEP` = `lighten(BRAND_DARK_GOLD, -14)` → `#7e6529`<br>`BRAND_DARK_GOLD_RGB` = `_to_rgb(BRAND_DARK_GOLD)` → `(140, 115, 55)` |\n| `STATUS.error-text` | `#dd6f77` | `STATUS_ERROR_TEXT` | — |\n| `STATUS.error-text-light` | `#ae4650` | `STATUS_ERROR_TEXT_LIGHT` | — |\n\n## The application's own\n\n| the app's name | value | why | made from it in the app |\n|---|---|---|---|\n| `GREY_44` | `#444444` | grey(4) on the register's ink grid, which the register states as a rule and does not name. The pressed plate and the scrollbar handle (RNV-COLLAPSE-505050). | `SLOT_BORDER_THIN_COLOR` = `_to_rgb(GREY_44)` → `(68, 68, 68)`<br>`HISTORY_SWATCH_BORDER` = `_to_rgb(GREY_44)` → `(68, 68, 68)` |\n| `GREY_EE` | `#eeeeee` | grey(14) on the ink grid. Static light surfaces, a list header and a scroll ground, that share hover-light's hex without being a hover. | — |\n| `GREY_CC` | `#cccccc` | grey(12) on the ink grid. The light-mode border. | — |\n| `GREY_88` | `#888888` | grey(8) on the ink grid. Muted text on dark; a scrollbar handle's hover on light. | — |\n| `GREY_55` | `#555555` | grey(5) on the ink grid. Disabled text and a checkbox edge on dark. | — |\n| `SELECTION_OVERLAY_COLOR` | `rgba(0,120,215,200)` | The blue overlay drawn during gradient and contrast selection, painted where no theme palette reaches. | — |\n| `GREY_66` | `#666666` | grey(6) on the ink grid. Muted text in light mode. | — |\n| `SEARCH_HIGHLIGHT_COLOR` | `(0, 255, 100)` | The bright green border on slots that match a search. | — |\n| `SLOT_BORDER_THICK_COLOR` | `(60, 60, 60)` | The thick slot border. | — |\n| `SVG_EXPORT_BG` | `#ffffff` | Data, not chrome: the background of an exported SVG palette file. White by meaning, so it does not follow the brand's white. | — |\n| `SVG_EXPORT_STROKE` | `#000000` | Data, not chrome: the swatch stroke in an exported SVG palette file. | — |\n| `DATA_DEFAULT_COLOR` | `#000000` | Data, not chrome: the value a colour record starts with. | — |\n| `SESSION_FALLBACK_COLOR` | `#a9a9a9` | Data: the grey a restored session or a reset setting falls back to. | — |\n| `SESSION_FALLBACK_COLOR_IMAGE` | `#000000` | Data: the image-mode fallback for a reset setting. | — |\n| `TRANSPARENT_RGBA` | `(0, 0, 0, 0)` | Fully transparent: ghost pixmaps and cleared palettes. | — |\n| `DEFAULT_SLOT_COLOR` | `#a9a9a9` | The colour a new slot starts with in dark and light mode. | — |\n\n## What each palette key takes\n\n| key | Dark | Light | Image |\n|---|---|---|---|\n| `window_bg` | `TRUE_BLACK` `#000000` | `APP_SURFACE_LIGHT_3` `#f5f5f5` | `APP_WINDOW_OVERLAY` `#ed000000` |\n| `panel_bg` | `BRAND_BLACK` `#1a1a1a` | `APP_SURFACE_LIGHT_3` `#f5f5f5` | `APP_PANEL_OVERLAY` `#ed1a1a1a` |\n| `scroll_bg` | `TRUE_BLACK` `#000000` | `GREY_EE` `#eeeeee` | `APP_WINDOW_OVERLAY` `#ed000000` |\n| `card_bg` | `APP_CARD` `#2a2a2a` | `WHITE` `#ffffff` | as dark |\n| `input_bg` | `BRAND_BLACK` `#1a1a1a` | `WHITE` `#ffffff` | as dark |\n| `text_color` | `APP_TEXT` `#dddddd` | `TRUE_BLACK` `#000000` | as dark |\n| `text_secondary` | `GREY_88` `#888888` | `GREY_66` `#666666` | as dark |\n| `text_disabled` | `GREY_55` `#555555` | `APP_TEXT_DIM` `#aaaaaa` | as dark |\n| `border_color` | `APP_BORDER` `#333333` | `GREY_CC` `#cccccc` | as dark |\n| `main_btn_bg` | `BRAND_BLACK` `#1a1a1a` | `WHITE` `#ffffff` | as dark |\n| `main_btn_text` | `APP_TEXT` `#dddddd` | `TRUE_BLACK` `#000000` | as dark |\n| `main_btn_hover_bg` | `APP_BORDER` `#333333` | `APP_BORDER` `#333333` | as dark |\n| `main_btn_hover_text` | `APP_TEXT` `#dddddd` | `TRUE_BLACK` `#000000` | as dark |\n| `main_btn_pressed_bg` | `GREY_44` `#444444` | `GREY_44` `#444444` | as dark |\n| `main_btn_pressed_text` | `TRUE_BLACK` `#000000` | `WHITE` `#ffffff` | as dark |\n| `dialog_btn_hover_bg` | `APP_PANEL_HOVER` `#3a3a3a` | `APP_HOVER_LIGHT` `#eeeeee` | as dark |\n| `dialog_btn_bg` | `BRAND_BLACK` `#1a1a1a` | `WHITE` `#ffffff` | as dark |\n| `dialog_btn_text` | `APP_TEXT` `#dddddd` | `TRUE_BLACK` `#000000` | as dark |\n| `scroll_handle` | `GREY_44` `#444444` | `APP_TEXT_DIM` `#aaaaaa` | as dark |\n| `accent` | `BRAND_GOLD` `#d2bc93` | `BRAND_DARK_GOLD` `#8c7337` | as dark |\n| `accent_dark` | `BRAND_GOLD_HOVER` `#dfc9a0` | `BRAND_DARK_GOLD` `#8c7337` | as dark |\n| `accent_ink` | `BRAND_GOLD` `#d2bc93` | `BRAND_DARK_GOLD_DEEP` `#7e6529` | as dark |\n| `scrollbar_bg` | `BRAND_BLACK` `#1a1a1a` | `APP_SURFACE_LIGHT_3` `#f5f5f5` | `transparent` |\n| `scrollbar_handle` | `GREY_44` `#444444` | `APP_TEXT_DIM` `#aaaaaa` | `translucent(GREY_44, SCROLLBAR_HANDLE_ALPHA)` `#96444444` |\n| `scrollbar_handle_hover` | `BRAND_GOLD` `#d2bc93` | `BRAND_DARK_GOLD` `#8c7337` | as dark |\n| `scrollbar_border` | `APP_BORDER` `#333333` | `GREY_CC` `#cccccc` | `translucent(APP_BORDER, SCROLLBAR_BORDER_ALPHA)` `#64333333` |\n| `dialog_bg` | `BRAND_BLACK` `#1a1a1a` | `APP_SURFACE_LIGHT_3` `#f5f5f5` | as dark |\n\nWhich widgets each key reaches is in the fleet chart, *RNV Colour Chart*.\n", 'tools/sync_colors.py': '"""Write this application\'s colours from the brand.   RNV-COLOUR-SYNC, 2026-10-16\n\n    python tools/sync_colors.py           write ui/colors.py and COLORS.md\n    python tools/sync_colors.py --check   write nothing; exit 1 if either is out of date\n\nbrand_map.json, at the repository root, says where each colour in\nui/colors.py comes from: a name in rnv-brand, such as "APP.card", or a value\nthis application owns, with the reason. This script writes the value on each\nof those lines, and COLORS.md, the chart of this application\'s colours.\n\nTHE BRAND IS READ AT THE PIN. A brand name\'s value comes from rnv-brand as\ninstalled, and only when that is the commit pinned in\ntests/requirements-dev.txt, so what is written is what this repository\ndeclares, never whatever happens to be installed. Moving to a newer brand is:\nchange the pin, `pip install -r tests/requirements-dev.txt`, run this script,\nand read the diff of ui/colors.py. It shows exactly what moved.\n.github/workflows/brand-sync.yml does that every day, and opens a pull\nrequest only when a colour this application uses has moved.\n\nNOTHING READS THE BRAND WHILE THE APPLICATION RUNS. The values are written\ninto the source and the build carries them. A derived colour, such as\nlighten(BRAND_GOLD, 13), stays code in ui/colors.py and follows its base.\nImage files are not touched.\n\ntests/test_colours_in_sync.py runs the --check half of this on every run.\n"""\nfrom __future__ import annotations\n\nimport argparse\nimport ast\nimport importlib.metadata\nimport json\nimport re\nimport sys\nfrom pathlib import Path\nfrom typing import Any\n\nROOT = Path(__file__).resolve().parent.parent\n\n#: Where this repository pins the register.\nDEV_REQS = "tests/requirements-dev.txt"\n\n#: The register\'s tables a map entry may name, as TABLE.key.\nTABLES = ("PERMANENT", "APP", "STATUS")\n\n#: The same pin tests/test_register_pin.py reads: a full commit, never a branch.\nPIN_RE = re.compile(\n    r"^rnv-brand\\s*@\\s*git\\+https://github\\.com/RNVizion/rnv-brand"\n    r"(?:\\.git)?@(?P<ref>[0-9a-f]{40})\\s*$", re.M)\n\n#: One colour constant on one line, `NAME: Final[...] = <value>`, with the\n#: marker this script writes at the end, or none before its first run.\nLINE_RE = (r"^(?P<head>{name}: Final\\[.*\\] = )(?P<value>.+?)"\n           r"(?P<mark>  # (?:brand: \\S+|app-owned))?$")\nMARK_RE = re.compile(r"  # (?:brand: \\S+|app-owned)$")\n\n_HEX_RE = re.compile(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?")\n_RGBA_RE = re.compile(r"rgba?\\([\\d\\s,.]+\\)")\n\n\nclass SyncError(Exception):\n    """Something this script will not write past. The message says what to do."""\n\n\n# ------------------------------------------------------------------ the map\n\ndef load_map(root: Path = ROOT) -> dict[str, Any]:\n    """brand_map.json, checked entry by entry before anything is written."""\n    data = json.loads((root / "brand_map.json").read_text(encoding="utf-8"))\n    colours = data.get("colours")\n    if not isinstance(colours, dict) or not colours:\n        raise SyncError("brand_map.json has no colours")\n    if not isinstance(data.get("colour_file"), str):\n        raise SyncError("brand_map.json does not name its colour_file")\n    for name, entry in colours.items():\n        if isinstance(entry, str):\n            table, _, key = entry.partition(".")\n            if table not in TABLES or not key:\n                raise SyncError(f"{name}: {entry!r} is not TABLE.key, with TABLE "\n                                f"one of {\', \'.join(TABLES)}")\n        elif isinstance(entry, dict):\n            if set(entry) != {"app", "why"}:\n                raise SyncError(f"{name}: an app-owned colour is "\n                                f\'{{"app": <value>, "why": <reason>}}\')\n            if not isinstance(entry["why"], str) or not entry["why"].strip():\n                raise SyncError(f"{name}: an app-owned colour needs its reason")\n            if not is_colour(_as_python(entry["app"])):\n                raise SyncError(f"{name}: {entry[\'app\']!r} is not a colour")\n        else:\n            raise SyncError(f"{name}: an entry is a brand name or an app-owned object")\n    return data\n\n\ndef _as_python(value: Any) -> Any:\n    """A map value as Python holds it: JSON has no tuples."""\n    return tuple(value) if isinstance(value, list) else value\n\n\ndef is_colour(value: Any) -> bool:\n    """A hex, an rgba() string, or an (r, g, b[, a]) tuple of bytes."""\n    if isinstance(value, str):\n        return bool(_HEX_RE.fullmatch(value) or _RGBA_RE.fullmatch(value))\n    if isinstance(value, tuple):\n        return len(value) in (3, 4) and all(\n            isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 255\n            for c in value)\n    return False\n\n\n# ---------------------------------------------------------------- the brand\n\ndef pinned_commit(root: Path = ROOT) -> str:\n    """The rnv-brand commit tests/requirements-dev.txt pins."""\n    match = PIN_RE.search((root / DEV_REQS).read_text(encoding="utf-8"))\n    if not match:\n        raise SyncError(f"{DEV_REQS} does not pin rnv-brand to a full commit")\n    return match.group("ref")\n\n\ndef installed_commit() -> str | None:\n    """The commit pip recorded when it installed rnv-brand, if it did."""\n    try:\n        dist = importlib.metadata.distribution("rnv-brand")\n    except importlib.metadata.PackageNotFoundError:\n        return None\n    raw = dist.read_text("direct_url.json")\n    if not raw:\n        return None\n    return json.loads(raw).get("vcs_info", {}).get("commit_id")\n\n\ndef load_brand(root: Path = ROOT) -> tuple[Any, str]:\n    """engine.brand, refused unless it is the pinned commit."""\n    pin = pinned_commit(root)\n    have = installed_commit()\n    if have != pin:\n        raise SyncError(\n            f"the rnv-brand installed here is "\n            f"{have[:7] if have else \'not one pip recorded a commit for\'}, and "\n            f"this repository pins {pin[:7]}. "\n            f"Run: pip install -r {DEV_REQS}")\n    import engine.brand as brand\n    return brand, pin\n\n\ndef brand_value(brand: Any, ref: str) -> str:\n    """The value a TABLE.key name holds in the register, in lower case."""\n    table, _, key = ref.partition(".")\n    values = getattr(brand, table, None)\n    if not isinstance(values, dict) or key not in values:\n        raise SyncError(f"rnv-brand has no {ref}")\n    value = values[key]\n    if not (isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value)):\n        raise SyncError(f"{ref} is {value!r}, not a six-digit hex colour")\n    return value.lower()\n\n\n# ----------------------------------------------------------- the colour file\n\ndef spell(value: Any) -> str:\n    """A value as the colour file writes it."""\n    if isinstance(value, str):\n        return json.dumps(value)\n    return "(" + ", ".join(str(c) for c in value) + ")"\n\n\ndef resolve(mapping: dict[str, Any], brand: Any) -> dict[str, tuple[Any, str]]:\n    """Each mapped name: (its value, the marker its line carries)."""\n    out: dict[str, tuple[Any, str]] = {}\n    for name, entry in mapping["colours"].items():\n        if isinstance(entry, str):\n            out[name] = (brand_value(brand, entry), f"brand: {entry}")\n        else:\n            out[name] = (_as_python(entry["app"]), "app-owned")\n    return out\n\n\ndef colour_constants(text: str) -> list[str]:\n    """Every module-level constant written as a colour literal."""\n    names = []\n    for node in ast.parse(text).body:\n        if (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)\n                and node.value is not None):\n            try:\n                value = ast.literal_eval(node.value)\n            except ValueError:\n                continue\n            if is_colour(value):\n                names.append(node.target.id)\n    return names\n\n\ndef rewrite(text: str, resolved: dict[str, tuple[Any, str]], where: str) -> str:\n    """The colour file with every mapped line written from the map."""\n    lines = text.split("\\n")\n    for name, (value, mark) in resolved.items():\n        pattern = re.compile(LINE_RE.format(name=re.escape(name)))\n        hits = [i for i, line in enumerate(lines) if pattern.match(line)]\n        if len(hits) != 1:\n            raise SyncError(f"{where}: expected one line defining {name}, "\n                            f"found {len(hits)}")\n        match = pattern.match(lines[hits[0]])\n        try:\n            ast.literal_eval(match.group("value"))\n        except (ValueError, SyntaxError):\n            raise SyncError(\n                f"{where}: {name} is written as {match.group(\'value\')!r}, which is "\n                f"code, not a value. A derived colour stays code; take {name} "\n                f"out of brand_map.json.") from None\n        lines[hits[0]] = f"{match.group(\'head\')}{spell(value)}  # {mark}"\n    new = "\\n".join(lines)\n    unmapped = [n for n in colour_constants(new) if n not in resolved]\n    if unmapped:\n        raise SyncError(\n            f"{where} writes colours brand_map.json does not hold: "\n            f"{\', \'.join(unmapped)}. Add each, as a brand name or as app-owned "\n            f"with its reason.")\n    return new\n\n\n# ------------------------------------------------------------------ the chart\n\ndef _shown(value: Any) -> str:\n    return value if isinstance(value, str) else "(" + ", ".join(map(str, value)) + ")"\n\n\ndef _cell(text: str) -> str:\n    return text.replace("|", "\\\\|")\n\n\ndef chart(text: str, mapping: dict[str, Any], brand: Any, pin: str) -> str:\n    """COLORS.md: the brand\'s names, their values, and this application\'s names."""\n    namespace: dict[str, Any] = {}\n    exec(compile(text, mapping["colour_file"], "exec"), namespace)\n    tree = ast.parse(text)\n    colours = mapping["colours"]\n\n    source: dict[str, str] = {}\n    palettes: list[tuple[str, ast.Dict]] = []\n    for node in tree.body:\n        if not (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)\n                and node.value is not None):\n            continue\n        name = node.target.id\n        if isinstance(node.value, ast.Dict) and ast.unparse(node.annotation) == "Final[ThemeDict]":\n            palettes.append((name, node.value))\n        elif is_colour(namespace.get(name)):\n            source[name] = ast.unparse(node.value)\n\n    # A derived colour is made from the colour names its expression reads.\n    derived = [n for n in source if n not in colours]\n    reads = {n: {x.id for x in ast.walk(ast.parse(source[n], mode="eval"))\n                 if isinstance(x, ast.Name) and x.id in source} for n in derived}\n\n    def roots(name: str, seen: frozenset[str] = frozenset()) -> set[str]:\n        if name in colours:\n            return {name}\n        out: set[str] = set()\n        for base in reads.get(name, ()):\n            if base not in seen:\n                out |= roots(base, seen | {name})\n        return out\n\n    made_from: dict[str, list[str]] = {n: [] for n in colours}\n    for name in derived:\n        for base in sorted(roots(name)):\n            made_from[base].append(name)\n\n    def made(name: str) -> str:\n        return "<br>".join(\n            f"`{d}` = `{_cell(source[d])}` → `{_shown(namespace[d])}`"\n            for d in made_from[name]) or "—"\n\n    def brand_order(item: tuple[str, Any]) -> tuple[int, int]:\n        table, _, key = item[1].partition(".")\n        keys = list(getattr(brand, table))\n        return TABLES.index(table), keys.index(key)\n\n    from_brand = sorted(((n, e) for n, e in colours.items() if isinstance(e, str)),\n                        key=brand_order)\n    own = [(n, e) for n, e in colours.items() if isinstance(e, dict)]\n    orphans = [n for n in derived if not roots(n)]\n\n    out = [\n        f"# Colours: {mapping.get(\'app\', \'this application\')}",\n        "",\n        f"Generated by `python tools/sync_colors.py` from `brand_map.json`, "\n        f"`{mapping[\'colour_file\']}` and rnv-brand at `{pin[:7]}`, the commit pinned in "\n        f"`{DEV_REQS}`. Don\'t edit it by hand: change the map and run "\n        f"the script. `tests/test_colours_in_sync.py` fails when this file is out of date.",\n        "",\n        f"{len(from_brand)} colours come from the brand and {len(own)} are the "\n        f"application\'s own. {len(derived)} more are worked out in "\n        f"`{mapping[\'colour_file\']}` from those, so they follow them.",\n        "",\n        "## From the brand",\n        "",\n        "| brand name | value | the app\'s name | made from it in the app |",\n        "|---|---|---|---|",\n    ]\n    for name, ref in from_brand:\n        out.append(f"| `{ref}` | `{_shown(namespace[name])}` | `{name}` | {made(name)} |")\n    out += [\n        "",\n        "## The application\'s own",\n        "",\n        "| the app\'s name | value | why | made from it in the app |",\n        "|---|---|---|---|",\n    ]\n    for name, entry in own:\n        out.append(f"| `{name}` | `{_shown(namespace[name])}` | {_cell(entry[\'why\'])} "\n                   f"| {made(name)} |")\n    if orphans:\n        out += ["", "Worked out from no colour above: "\n                + ", ".join(f"`{n}`" for n in orphans) + "."]\n\n    # Each palette\'s keys, in order: the expression it writes, or "as dark"\n    # where it takes the entry from a palette it spreads.\n    out += ["", "## What each palette key takes", ""]\n    entries: dict[str, dict[str, str]] = {}\n    for name, node in palettes:\n        written: dict[str, str] = {}\n        for key, value in zip(node.keys, node.values):\n            if key is None:\n                spread = ast.unparse(value)\n                label = namespace[spread]["name"].lower()\n                written.update({k: f"as {label}" for k in entries.get(spread, {})})\n            elif isinstance(key, ast.Constant) and key.value != "name":\n                written[key.value] = ast.unparse(value)\n        entries[name] = written\n    out.append("| key | " + " | ".join(namespace[n]["name"] for n in entries) + " |")\n    out.append("|---|" + "---|" * len(entries))\n    keys: list[str] = []\n    for written in entries.values():\n        keys += [k for k in written if k not in keys]\n    for key in keys:\n        cells = []\n        for name, written in entries.items():\n            expr = written.get(key)\n            if expr is None:\n                cells.append("—")\n            elif expr.startswith("as "):\n                cells.append(expr)\n            elif expr == repr(namespace[name][key]):\n                cells.append(f"`{_shown(namespace[name][key])}`")\n            else:\n                cells.append(f"`{_cell(expr)}` `{_shown(namespace[name][key])}`")\n        out.append(f"| `{key}` | " + " | ".join(cells) + " |")\n    out += ["", "Which widgets each key reaches is in the fleet chart, *RNV Colour Chart*.", ""]\n    return "\\n".join(out)\n\n\n# --------------------------------------------------------------------- run it\n\ndef build(root: Path = ROOT) -> dict[Path, tuple[str, str]]:\n    """Each file this script owns: (what is there, what it would write)."""\n    mapping = load_map(root)\n    brand, pin = load_brand(root)\n    colour_path = root / mapping["colour_file"]\n    before = colour_path.read_text(encoding="utf-8")\n    after = rewrite(before, resolve(mapping, brand), mapping["colour_file"])\n    chart_path = root / "COLORS.md"\n    chart_before = chart_path.read_text(encoding="utf-8") if chart_path.exists() else ""\n    return {colour_path: (before, after),\n            chart_path: (chart_before, chart(after, mapping, brand, pin))}\n\n\ndef moved(before: str, after: str) -> list[str]:\n    """What a write changed: each value that moved, and how many lines only\n    gained their marker."""\n    changes, marked = [], 0\n    for a, b in zip(before.split("\\n"), after.split("\\n")):\n        if a == b:\n            continue\n        old, new = MARK_RE.sub("", a), MARK_RE.sub("", b)\n        if old == new:\n            marked += 1\n            continue\n        name = new.split(":", 1)[0]\n        changes.append(f"  {name}: {old.split(\' = \', 1)[1]} -> {new.split(\' = \', 1)[1]}")\n    if marked:\n        changes.append(f"  {marked} line(s) marked, no value moved")\n    return changes\n\n\ndef main(argv: list[str] | None = None) -> int:\n    parser = argparse.ArgumentParser(description=__doc__.split("\\n", 1)[0])\n    parser.add_argument("--check", action="store_true",\n                        help="write nothing; exit 1 if a file is out of date")\n    args = parser.parse_args(argv)\n    try:\n        plan = build()\n    except SyncError as exc:\n        print(f"sync_colors: {exc}", file=sys.stderr)\n        return 2\n    stale = [path for path, (before, after) in plan.items() if before != after]\n    if args.check:\n        for path in stale:\n            print(f"out of date: {path.relative_to(ROOT).as_posix()}")\n        if stale:\n            print("Run: python tools/sync_colors.py")\n            return 1\n        print("in sync")\n        return 0\n    for path in stale:\n        before, after = plan[path]\n        path.write_text(after, encoding="utf-8")\n        print(f"wrote {path.relative_to(ROOT).as_posix()}")\n        if path.suffix == ".py":\n            print("\\n".join(moved(before, after)))\n    if not stale:\n        print("in sync; nothing to write")\n    return 0\n\n\nif __name__ == "__main__":\n    sys.exit(main())\n', 'tests/test_colours_in_sync.py': '"""The colour file is what the brand and the map say it is.   RNV-COLOUR-SYNC\n\nInstalled 2026-10-16, ruled in #36 to #46. brand_map.json says where each\ncolour in ui/colors.py comes from: a name in rnv-brand, or a value this\napplication owns, with the reason. tools/sync_colors.py writes the value on\neach of those lines from the map and from the brand at the commit pinned in\ntests/requirements-dev.txt, and writes COLORS.md, the chart of them.\n\nWHAT THIS REPLACES. Until this date each brand value was written out by hand\nin two places, the colour file and a test beside it, and a brand move meant\nediting both (#39). The tests that wrote a value as its hex code now hold the\nname it takes; this file holds every value, once, against the brand itself.\n\nWHAT THIS GUARD HOLDS.\n\n1. ui/colors.py and COLORS.md are exactly what the sync would write. A value\n   edited by hand, a map entry changed without a sync, or a pin moved without\n   one, and this names the file and says what to run.\n2. Every colour the colour file writes as a value is in the map, and every\n   colour the app owns says why.\n3. The provenance maps in ui/colors.py agree with the map: a register value\n   is a brand name there, an app\'s ramp step is the app\'s own.\n4. The sync is looking: it puts back a value edited by hand, refuses a colour\n   the map does not hold, refuses a brand that is not the pinned one, and\n   carries a brand move to the one line that takes it.\n5. The daily workflow runs the sync against the brand\'s head and opens a pull\n   request only when the colour file moved.\n"""\nfrom __future__ import annotations\n\nimport importlib.util\nimport json\nimport pathlib\nimport re\nimport types\n\nimport pytest\n\nfrom ui import colors\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nMAP_FILE = ROOT / "brand_map.json"\nWORKFLOW = ROOT / ".github" / "workflows" / "brand-sync.yml"\n\n\ndef _sync():\n    """tools/sync_colors.py, loaded by path: tools/ is not a package."""\n    spec = importlib.util.spec_from_file_location(\n        "sync_colors", ROOT / "tools" / "sync_colors.py")\n    module = importlib.util.module_from_spec(spec)\n    spec.loader.exec_module(module)\n    return module\n\n\nSYNC = _sync()\nMAPPING = SYNC.load_map(ROOT)\nCOLOURS = MAPPING["colours"]\n\n\ndef _brand():\n    """The register as installed, refused unless it is the pinned commit."""\n    try:\n        brand, _ = SYNC.load_brand(ROOT)\n    except SYNC.SyncError as exc:\n        pytest.fail(str(exc))\n    return brand\n\n\n# ------------------------------------------------------------------ in sync\n\ndef test_the_colour_file_and_the_chart_are_what_the_sync_writes():\n    try:\n        plan = SYNC.build(ROOT)\n    except SYNC.SyncError as exc:\n        pytest.fail(str(exc))\n    stale = [path.relative_to(ROOT).as_posix()\n             for path, (before, after) in plan.items() if before != after]\n    assert not stale, (\n        f"out of date: {\', \'.join(stale)}. Run: python tools/sync_colors.py\\n"\n        f"A value in ui/colors.py is written from brand_map.json and the brand "\n        f"at the pin; change the map, not the value.")\n\n\ndef test_every_colour_the_file_writes_is_in_the_map():\n    text = (ROOT / MAPPING["colour_file"]).read_text(encoding="utf-8")\n    written = SYNC.colour_constants(text)\n    missing = sorted(set(written) - set(COLOURS))\n    phantom = sorted(n for n in COLOURS if not hasattr(colors, n))\n    assert not missing, f"colours brand_map.json does not hold: {missing}"\n    assert not phantom, f"brand_map.json names what ui/colors.py does not have: {phantom}"\n    assert len(written) >= 25, f"only {len(written)} colours found -- the reader is blind"\n\n\ndef test_every_colour_the_app_owns_says_why():\n    owned = {n: e for n, e in COLOURS.items() if isinstance(e, dict)}\n    assert owned, "the map holds no colour of the app\'s own -- the reader is blind"\n    silent = [n for n, e in owned.items() if len(e.get("why", "").split()) < 3]\n    assert not silent, f"app-owned colours with no reason: {silent}"\n\n\ndef test_the_provenance_maps_agree_with_the_map():\n    """GOLD_PROVENANCE and APP_PROVENANCE classify these names in ui/colors.py.\n    A register value is a brand name in the map; an app ramp step is the\n    app\'s own; a derived or overlay value is code, and not in the map."""\n    wrong = []\n    for table in (colors.GOLD_PROVENANCE, colors.APP_PROVENANCE):\n        for name, kind in table.items():\n            entry = COLOURS.get(name)\n            if kind == "register" and not isinstance(entry, str):\n                wrong.append(f"{name} is {kind} and the map has {entry!r}")\n            elif kind == "app-ramp" and not isinstance(entry, dict):\n                wrong.append(f"{name} is {kind} and the map has {entry!r}")\n            elif kind in ("derived", "register-overlay") and entry is not None:\n                wrong.append(f"{name} is {kind} and the map writes it as a value")\n    assert not wrong, "the provenance maps and brand_map.json disagree:\\n  " + "\\n  ".join(wrong)\n\n\n# ---------------------------------------------------------- the sync is looking\n\ndef _text():\n    return (ROOT / MAPPING["colour_file"]).read_text(encoding="utf-8")\n\n\ndef test_the_sync_puts_back_a_value_edited_by_hand():\n    text = _text()\n    line = next(l for l in text.split("\\n") if l.startswith("APP_CARD: Final[str] = "))\n    edited = text.replace(line, line.replace(colors.APP_CARD, "#2b2b2b"), 1)\n    assert edited != text\n    resolved = SYNC.resolve(MAPPING, _brand())\n    assert SYNC.rewrite(edited, resolved, "ui/colors.py") == text\n\n\ndef test_the_sync_refuses_a_colour_the_map_does_not_hold():\n    text = _text() + \'\\nSTRAY_COLOUR: Final[str] = "#123456"\\n\'\n    with pytest.raises(SYNC.SyncError, match="STRAY_COLOUR"):\n        SYNC.rewrite(text, SYNC.resolve(MAPPING, _brand()), "ui/colors.py")\n\n\ndef test_the_sync_refuses_a_derived_colour_in_the_map():\n    resolved = dict(SYNC.resolve(MAPPING, _brand()))\n    resolved["BRAND_GOLD_HOVER"] = ("#dfc9a0", "app-owned")\n    with pytest.raises(SYNC.SyncError, match="code, not a value"):\n        SYNC.rewrite(_text(), resolved, "ui/colors.py")\n\n\ndef test_the_sync_refuses_a_brand_that_is_not_the_pin(monkeypatch):\n    monkeypatch.setattr(SYNC, "installed_commit", lambda: "0" * 40)\n    with pytest.raises(SYNC.SyncError, match="pins"):\n        SYNC.load_brand(ROOT)\n\n\ndef test_a_brand_move_reaches_the_one_line_that_takes_it():\n    brand = _brand()\n    moved = types.SimpleNamespace(\n        PERMANENT=dict(brand.PERMANENT), APP=dict(brand.APP), STATUS=dict(brand.STATUS))\n    elsewhere = "#6f94bc" if brand.APP["accent"].lower() != "#6f94bc" else "#456c91"\n    moved.APP["accent"] = elsewhere\n    text = _text()\n    after = SYNC.rewrite(text, SYNC.resolve(MAPPING, moved), "ui/colors.py")\n    changed = [b for a, b in zip(text.split("\\n"), after.split("\\n")) if a != b]\n    assert changed == [f\'BRAND_GOLD: Final[str] = "{elsewhere}"  # brand: APP.accent\'], changed\n\n\n# ------------------------------------------------------------- the daily check\n\ndef test_the_daily_workflow_syncs_the_head_and_asks_only_when_a_colour_moved():\n    text = WORKFLOW.read_text(encoding="utf-8")\n    assert re.search(r"^\\s+schedule:\\s*$", text, re.M), "the workflow runs on no schedule"\n    assert "git ls-remote https://github.com/RNVizion/rnv-brand" in text, \\\n        "the workflow does not read the brand\'s head"\n    assert "python tools/sync_colors.py" in text, "the workflow does not run the sync"\n    assert "git diff --quiet -- ui/colors.py" in text, \\\n        "the workflow does not ask whether the colour file moved"\n    assert "python run_tests.py" in text, "the workflow does not run the tests on the change"\n    assert "gh pr create" in text and "gh pr view" in text, \\\n        "the workflow does not open, or look for, its pull request"\n', '.github/workflows/brand-sync.yml': 'name: Brand sync\n\n# RNV-COLOUR-SYNC, 2026-10-16 (#38 B). Once a day, read rnv-brand\'s head and\n# write this application\'s colours from it with tools/sync_colors.py.\n#\n#   No colour this app uses moved  -> nothing is opened. The run ends there.\n#   One did                        -> the tests run on the change, and ONE pull\n#                                     request is opened with the new pin,\n#                                     ui/colors.py and COLORS.md. If it is\n#                                     still open the next day, it is updated,\n#                                     not opened again.\n#\n# Merge it, and the next build carries the new colours. Nothing reads the\n# brand while the application runs.\n#\n# Needs one repository setting: Settings > Actions > General > Workflow\n# permissions > "Allow GitHub Actions to create and approve pull requests".\n# rnv-brand is public, so no token beyond the workflow\'s own.\n#\n# A pull request opened by this workflow\'s token does not start the other\n# workflows, which is GitHub\'s rule for that token. So this job runs\n# `python run_tests.py`, what both test workflows run, and says in the pull\n# request whether it was green.\n\non:\n  schedule:\n    - cron: "17 6 * * *"\n  workflow_dispatch:\n\npermissions:\n  contents: write\n  pull-requests: write\n\nconcurrency:\n  group: brand-sync\n  cancel-in-progress: false\n\njobs:\n  sync:\n    name: Sync colours from rnv-brand / Python 3.13\n    runs-on: ubuntu-latest\n    timeout-minutes: 20\n\n    steps:\n      - name: Check out repository\n        uses: actions/checkout@v5\n\n      - name: Set up Python 3.13\n        uses: actions/setup-python@v6\n        with:\n          python-version: "3.13"\n\n      - name: Pin the brand\'s head and write the colours from it\n        id: sync\n        run: |\n          # A sync that refuses -- the brand dropped a name this app uses -- fails\n          # the run, so it is seen, rather than passing as "nothing moved".\n          set -o pipefail\n          head=$(git ls-remote https://github.com/RNVizion/rnv-brand HEAD | cut -f1)\n          echo "head=$head" >> "$GITHUB_OUTPUT"\n          sed -i -E "s#(rnv-brand @ git\\+https://github\\.com/RNVizion/rnv-brand(\\.git)?@)[0-9a-f]{40}#\\1$head#" tests/requirements-dev.txt\n          python -m pip install --upgrade pip\n          if ! pip install "rnv-brand @ git+https://github.com/RNVizion/rnv-brand@$head" \\\n             || ! python -c "import engine.brand"; then\n            echo "::warning::rnv-brand at ${head:0:7} does not install or import; nothing was synced."\n            echo "moved=no" >> "$GITHUB_OUTPUT"\n            exit 0\n          fi\n          python tools/sync_colors.py | tee sync.log\n          if git diff --quiet -- ui/colors.py; then\n            echo "No colour this app uses moved at rnv-brand ${head:0:7}. Nothing to open."\n            echo "moved=no" >> "$GITHUB_OUTPUT"\n          else\n            echo "moved=yes" >> "$GITHUB_OUTPUT"\n          fi\n\n      - name: Install system Qt dependencies\n        if: steps.sync.outputs.moved == \'yes\'\n        run: |\n          sudo apt-get update\n          sudo apt-get install -y --no-install-recommends \\\n            libegl1 \\\n            libxkbcommon0 \\\n            libxkbcommon-x11-0 \\\n            libdbus-1-3 \\\n            libxcb-cursor0 \\\n            libxcb-icccm4 \\\n            libxcb-image0 \\\n            libxcb-keysyms1 \\\n            libxcb-randr0 \\\n            libxcb-render-util0 \\\n            libxcb-shape0 \\\n            libxcb-xinerama0 \\\n            libxcb-xkb1 \\\n            libfontconfig1\n\n      - name: Run the tests on the change\n        if: steps.sync.outputs.moved == \'yes\'\n        id: tests\n        env:\n          QT_QPA_PLATFORM: offscreen\n        run: |\n          pip install -r tests/requirements-dev.txt\n          if python run_tests.py > tests.log 2>&1; then\n            echo "result=green" >> "$GITHUB_OUTPUT"\n          else\n            echo "result=red" >> "$GITHUB_OUTPUT"\n          fi\n          tail -n 40 tests.log\n\n      - name: Open the pull request, or update the one already open\n        if: steps.sync.outputs.moved == \'yes\'\n        env:\n          GH_TOKEN: ${{ github.token }}\n          HEAD: ${{ steps.sync.outputs.head }}\n          RESULT: ${{ steps.tests.outputs.result }}\n        run: |\n          git config user.name "github-actions[bot]"\n          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"\n          git switch -C brand-sync\n          git add tests/requirements-dev.txt ui/colors.py COLORS.md\n          git commit -m "Brand sync: rnv-brand@${HEAD:0:7}"\n          git push --force origin brand-sync\n          {\n            echo "rnv-brand moved a colour this application uses, at ${HEAD:0:7}."\n            echo\n            echo \'```\'\n            cat sync.log\n            echo \'```\'\n            echo\n            echo "The tests on this change: **$RESULT** (\\`python run_tests.py\\`)."\n            echo\n            echo "Merge to take it; the next build carries it. Image files are not changed."\n          } > body.md\n          if [ "$(gh pr view brand-sync --json state --jq .state 2>/dev/null)" = "OPEN" ]; then\n            gh pr edit brand-sync --title "Brand sync: rnv-brand@${HEAD:0:7}" --body-file body.md\n          else\n            gh pr create --head brand-sync --title "Brand sync: rnv-brand@${HEAD:0:7}" --body-file body.md\n          fi\n'}

#: Each substitution: (file, anchor, replacement). Every anchor is counted
#: before anything is written.
SUBS = [('ui/colors.py', '"""\nfrom __future__ import annotations\n', '"""\n# RNV-COLOUR-SYNC (2026-10-16). Every colour value below whose line ends\n# "# brand: <name>" or "# app-owned" is written by tools/sync_colors.py from\n# brand_map.json: a brand name\'s value from rnv-brand at the commit pinned in\n# tests/requirements-dev.txt, an app-owned value from the map, with its reason.\n# To change one, change the map and run `python tools/sync_colors.py`. A value\n# edited here is put back by the next sync, and tests/test_colours_in_sync.py\n# fails until then. COLORS.md is the chart of them.\nfrom __future__ import annotations\n'), ('README.md', '├── pyproject.toml                  # PEP 621 project metadata\n', "├── pyproject.toml                  # PEP 621 project metadata\n├── brand_map.json                  # Where each colour comes from: rnv-brand or the app\n├── COLORS.md                       # This app's colour chart, written by the sync\n"), ('README.md', '│   └── workflows/\n│       ├── tests.yml               # CI: Windows test suite on push/PR\n', '│   └── workflows/\n│       ├── brand-sync.yml          # Daily: colours from rnv-brand; a PR only if one moved\n│       ├── tests.yml               # CI: Windows test suite on push/PR\n'), ('README.md', '│\n└── resources/                      # Bundled assets\n', '│\n├── tools/                          # Maintenance scripts\n│   └── sync_colors.py              # Writes ui/colors.py and COLORS.md from the brand\n│\n└── resources/                      # Bundled assets\n'), ('tests/test_app_mirror.py', 'import ast\nimport pathlib\n\nimport pytest\n', 'import ast\nimport json\nimport pathlib\n\nimport pytest\n'), ('tests/test_app_mirror.py', "ROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'ui' / 'colors.py'\nABOUT = ROOT / 'ui' / 'about_dialog.py'\n", 'ROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / \'ui\' / \'colors.py\'\nABOUT = ROOT / \'ui\' / \'about_dialog.py\'\n\n#: RNV-COLOUR-SYNC, 2026-10-16. Where each colour comes from, as brand_map.json\n#: says. The values are held by tests/test_colours_in_sync.py, against the\n#: register at the pin; what this file holds is the name each one takes.\nBRAND_MAP = json.loads((ROOT / "brand_map.json").read_text(encoding="utf-8"))["colours"]\n'), ('tests/test_app_mirror.py', "PINNED = {\n    'TRUE_BLACK': '#000000',\n    'WHITE': '#ffffff',\n    'BRAND_BLACK': '#1a1a1a',\n    'APP_CARD': '#2a2a2a',\n    'APP_BORDER': '#333333',\n    'APP_TEXT': '#dddddd',\n    'APP_TEXT_DIM': '#aaaaaa',\n    'APP_PANEL_HOVER': '#3a3a3a',\n    'APP_HOVER_LIGHT': '#eeeeee',\n    'APP_SURFACE_LIGHT_3': '#f5f5f5',\n}\n", "#: The register's neutrals this app names. RNV-COLOUR-SYNC, 2026-10-16: this\n#: was PINNED, each name with its value written beside it; the values are\n#: written into ui/colors.py from the register now, and held there.\nNEUTRALS = ('TRUE_BLACK', 'WHITE', 'BRAND_BLACK', 'APP_CARD', 'APP_BORDER',\n            'APP_TEXT', 'APP_TEXT_DIM', 'APP_PANEL_HOVER', 'APP_HOVER_LIGHT',\n            'APP_SURFACE_LIGHT_3')\n"), ('tests/test_app_mirror.py', "#: The About dialog's button hover plate, per mode. Unchanged values; only the\n#: name moved off `tab_hover`.\nDIALOG_BTN_HOVER = {'DARK': '#3a3a3a', 'LIGHT': '#eeeeee', 'IMAGE': '#3a3a3a'}\n", "#: The About dialog's button hover plate, per mode. Unchanged values; only the\n#: name moved off `tab_hover`.\nDIALOG_BTN_HOVER = {'DARK': colors.APP_PANEL_HOVER, 'LIGHT': colors.APP_HOVER_LIGHT,\n                    'IMAGE': colors.APP_PANEL_HOVER}\n"), ('tests/test_app_mirror.py', "    for name in PINNED:\n        assert hasattr(colors, name), f'ui.colors has no {name}'\n", "    for name in NEUTRALS:\n        assert hasattr(colors, name), f'ui.colors has no {name}'\n"), ('tests/test_app_mirror.py', "    assert colors.APP_TEXT == grey(13) == '#dddddd', (\n", '    assert colors.APP_TEXT == grey(13), (\n'), ('tests/test_app_mirror.py', 'def test_every_pinned_neutral_is_what_the_register_held():\n    """The local half of the mirror. Runs everywhere."""\n    drift = {n: getattr(colors, n) for n, v in PINNED.items()\n             if getattr(colors, n) != v}\n    assert not drift, (\n        f\'these constants no longer hold their registered values: {drift}\\n\'\n        f\'If the brand moved, update PINNED in the same commit that updates \'\n        f\'ui/colors.py -- never one without the other.\')\n', 'def test_every_pinned_neutral_is_what_the_register_held():\n    """The local half of the mirror. Runs everywhere.\n\n    RNV-COLOUR-SYNC, 2026-10-16. This held each value written out beside its\n    name, and a brand move meant editing it by hand. Now it holds that\n    brand_map.json takes each neutral from the register; the value is written\n    from there, and tests/test_colours_in_sync.py holds it."""\n    own = {n: BRAND_MAP.get(n) for n in NEUTRALS\n           if not isinstance(BRAND_MAP.get(n), str)}\n    assert not own, (\n        f\'these neutrals are not taken from the register: {own}\\n\'\n        f\'Each is a register value; brand_map.json names it as one.\')\n'), ('tests/test_app_mirror.py', "    for name in PINNED:\n        theirs = (brand.APP[name[4:].lower().replace('_', '-')]\n", "    for name in NEUTRALS:\n        theirs = (brand.APP[name[4:].lower().replace('_', '-')]\n"), ('tests/test_app_mirror.py', "    assert LIGHT['text_color'] == colors.TRUE_BLACK == '#000000'\n", "    assert LIGHT['text_color'] == colors.TRUE_BLACK\n"), ('tests/test_app_mirror.py', "        'the light pane is the card colour again')\n    assert resolved == '#f5f5f5'\n", "        'the light pane is the card colour again')\n    assert resolved == colors.APP_SURFACE_LIGHT_3\n"), ('tests/test_app_mirror.py', "    grounds = ('#000000', '#1a1a1a', '#2a2a2a', '#333333', '#3a3a3a', '#444444')\n", '    grounds = (colors.TRUE_BLACK, colors.BRAND_BLACK, colors.APP_CARD,\n               colors.APP_BORDER, colors.APP_PANEL_HOVER, colors.GREY_44)\n'), ('tests/test_brand_mirror.py', 'import ast\nimport pathlib\nimport subprocess\n', 'import ast\nimport json\nimport pathlib\nimport subprocess\n'), ('tests/test_brand_mirror.py', 'from ui import colors as C\n\nPALETTES = {\n', 'from ui import colors as C\n\n#: RNV-COLOUR-SYNC, 2026-10-16. Where each colour comes from, as brand_map.json\n#: says. The values are held by tests/test_colours_in_sync.py, against the\n#: register at the pin; what this file holds is the name each one takes.\nBRAND_MAP = json.loads((pathlib.Path(__file__).resolve().parents[1] / "brand_map.json").read_text(encoding="utf-8"))["colours"]\n\nPALETTES = {\n'), ('tests/test_brand_mirror.py', 'def test_register_values_match_rnv_brand():\n    assert C.BRAND_GOLD == "#d2bc93"\n    assert C.BRAND_DARK_GOLD == "#8c7337"\n', 'def test_register_values_match_rnv_brand():\n    """RNV-COLOUR-SYNC, 2026-10-16. This held the two golds by their hex codes.\n    The golds follow the register\'s accent names, as ruled (#45 A); the\n    values are written from there and held by tests/test_colours_in_sync.py."""\n    assert BRAND_MAP["BRAND_GOLD"] == "APP.accent"\n    assert BRAND_MAP["BRAND_DARK_GOLD"] == "APP.accent-light-mode"\n'), ('tests/test_brand_mirror.py', '    assert C.BRAND_GOLD_HOVER == C.lighten(C.BRAND_GOLD, 13)\n    assert C.BRAND_DARK_GOLD_DEEP == "#7e6529"\n    assert C.BRAND_GOLD_HOVER == "#dfc9a0"\n', '    assert C.BRAND_GOLD_HOVER == C.lighten(C.BRAND_GOLD, 13)\n'), ('tests/test_brand_mirror.py', '    for ground in ("#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"):\n        assert contrast(ink, ground) >= 4.5, f"{ink} on {ground}"\n', '    # The grounds by name, so a brand move measures the new ones; #e8e8e8 is\n    # the register\'s gold text floor, which the app does not draw.\n    for ground in (C.WHITE, C.APP_SURFACE_LIGHT_3, C.APP_HOVER_LIGHT, "#e8e8e8"):\n        assert contrast(ink, ground) >= 4.5, f"{ink} on {ground}"\n'), ('tests/test_button_key_names.py', 'PINNED_MAIN = {\n    "dark": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",\n             "main_btn_hover_bg": "#333333", "main_btn_hover_text": "#dddddd",\n             "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#000000"},\n    "light": {"main_btn_bg": "#ffffff", "main_btn_text": "#000000",\n              "main_btn_hover_bg": "#333333", "main_btn_hover_text": "#000000",\n              "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#ffffff"},\n    "image": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",\n              "main_btn_hover_bg": "#333333", "main_btn_hover_text": "#dddddd",\n              "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#000000"},\n}\n', '#: RNV-COLOUR-SYNC, 2026-10-16: each key by the constant it paints, where it\n#: was written as that constant\'s hex code, so a brand move needs no edit here.\nPINNED_MAIN = {\n    "dark": {"main_btn_bg": "BRAND_BLACK", "main_btn_text": "APP_TEXT",\n             "main_btn_hover_bg": "APP_BORDER", "main_btn_hover_text": "APP_TEXT",\n             "main_btn_pressed_bg": "GREY_44", "main_btn_pressed_text": "TRUE_BLACK"},\n    "light": {"main_btn_bg": "WHITE", "main_btn_text": "TRUE_BLACK",\n              "main_btn_hover_bg": "APP_BORDER", "main_btn_hover_text": "TRUE_BLACK",\n              "main_btn_pressed_bg": "GREY_44", "main_btn_pressed_text": "WHITE"},\n    "image": {"main_btn_bg": "BRAND_BLACK", "main_btn_text": "APP_TEXT",\n              "main_btn_hover_bg": "APP_BORDER", "main_btn_hover_text": "APP_TEXT",\n              "main_btn_pressed_bg": "GREY_44", "main_btn_pressed_text": "TRUE_BLACK"},\n}\n'), ('tests/test_button_key_names.py', 'PINNED_DIALOG = {\n    "dark": {"dialog_btn_bg": "#1a1a1a", "dialog_btn_text": "#dddddd",\n             "dialog_btn_hover_bg": "#3a3a3a"},\n    "light": {"dialog_btn_bg": "#ffffff", "dialog_btn_text": "#000000",\n              "dialog_btn_hover_bg": "#eeeeee"},\n    "image": {"dialog_btn_bg": "#1a1a1a", "dialog_btn_text": "#dddddd",\n              "dialog_btn_hover_bg": "#3a3a3a"},\n}\n', 'PINNED_DIALOG = {\n    "dark": {"dialog_btn_bg": "BRAND_BLACK", "dialog_btn_text": "APP_TEXT",\n             "dialog_btn_hover_bg": "APP_PANEL_HOVER"},\n    "light": {"dialog_btn_bg": "WHITE", "dialog_btn_text": "TRUE_BLACK",\n              "dialog_btn_hover_bg": "APP_HOVER_LIGHT"},\n    "image": {"dialog_btn_bg": "BRAND_BLACK", "dialog_btn_text": "APP_TEXT",\n              "dialog_btn_hover_bg": "APP_PANEL_HOVER"},\n}\n'), ('tests/test_button_key_names.py', 'def _palettes():\n', 'def _values(pins):\n    """Each key\'s constant, as the value it holds."""\n    from ui import colors\n    return {key: getattr(colors, name) for key, name in pins.items()}\n\n\ndef _palettes():\n'), ('tests/test_button_key_names.py', '    for mode, pins in PINNED_MAIN.items():\n        palette = _palettes()[mode]\n        actual = {k: palette.get(k) for k in pins}\n        assert actual == pins, (\n', '    for mode, names in PINNED_MAIN.items():\n        palette = _palettes()[mode]\n        pins = _values(names)\n        actual = {k: palette.get(k) for k in pins}\n        assert actual == pins, (\n'), ('tests/test_button_key_names.py', '    for mode, pins in PINNED_DIALOG.items():\n        palette = _palettes()[mode]\n        actual = {k: palette.get(k) for k in pins}\n', '    for mode, names in PINNED_DIALOG.items():\n        palette = _palettes()[mode]\n        pins = _values(names)\n        actual = {k: palette.get(k) for k in pins}\n'), ('tests/test_constant_names.py', 'import io\nimport re\nimport tokenize\n', 'import io\nimport json\nimport re\nimport tokenize\n'), ('tests/test_constant_names.py', 'ROOT = Path(__file__).resolve().parent.parent\n', 'ROOT = Path(__file__).resolve().parent.parent\n\n#: RNV-COLOUR-SYNC, 2026-10-16. Where each colour comes from, as brand_map.json\n#: says. The values are held by tests/test_colours_in_sync.py, against the\n#: register at the pin; what this file holds is the name each one takes.\nBRAND_MAP = json.loads((ROOT / "brand_map.json").read_text(encoding="utf-8"))["colours"]\n'), ('tests/test_constant_names.py', '    eleven role names were standing in front of."""\n    assert colors.TRUE_BLACK == "#000000"\n    assert colors.WHITE == "#ffffff"\n    assert colors.GREY_66 == "#666666"\n', '    eleven role names were standing in front of.\n\n    RNV-COLOUR-SYNC, 2026-10-16: each was held here by its hex code. Each is\n    held in brand_map.json now, a brand name or the app\'s own value, and\n    tests/test_colours_in_sync.py holds the value the file writes."""\n    for name in ("TRUE_BLACK", "WHITE", "GREY_66", "GREY_EE"):\n        assert name in BRAND_MAP, f"brand_map.json does not hold {name}"\n'), ('tests/test_constant_names.py', '    assert colors.GREY_EE == "#eeeeee"\n    assert not hasattr(colors, "GREY_F0")\n    assert colors.BRAND_DARK_GOLD_DEEP == "#7e6529"\n', '    assert not hasattr(colors, "GREY_F0")\n    assert colors.BRAND_DARK_GOLD_DEEP == colors.lighten(colors.BRAND_DARK_GOLD, -14)\n'), ('tests/test_error_red.py', 'import pytest\n\nfrom ui import colors\n\nTEXT_FLOOR = 4.5\n', 'import json\nimport pathlib\n\nimport pytest\n\nfrom ui import colors\n\n#: RNV-COLOUR-SYNC, 2026-10-16. Where each colour comes from, as brand_map.json\n#: says. The values are held by tests/test_colours_in_sync.py, against the\n#: register at the pin; what this file holds is the name each one takes.\nBRAND_MAP = json.loads((pathlib.Path(__file__).resolve().parents[1] / "brand_map.json").read_text(encoding="utf-8"))["colours"]\n\nTEXT_FLOOR = 4.5\n'), ('tests/test_error_red.py', '    assert colors.STATUS_ERROR_TEXT_LIGHT == "#ae4650"\n    # the registered base, STATUS["error"]; this application draws no fill and carries none\n', '    assert BRAND_MAP["STATUS_ERROR_TEXT_LIGHT"] == "STATUS.error-text-light"\n    # the registered base, STATUS["error"]; this application draws no fill and carries none\n'), ('tests/test_error_red.py', '    the family\'s three fills are the register\'s, and are not carried here."""\n    assert colors.STATUS_ERROR_TEXT == "#dd6f77"\n    assert colors.STATUS_ERROR_TEXT_LIGHT == "#ae4650"\n', '    the family\'s three fills are the register\'s, and are not carried here.\n\n    RNV-COLOUR-SYNC, 2026-10-16: pinned by name in brand_map.json, which takes\n    both from the register; tests/test_colours_in_sync.py holds the values."""\n    assert BRAND_MAP["STATUS_ERROR_TEXT"] == "STATUS.error-text"\n    assert BRAND_MAP["STATUS_ERROR_TEXT_LIGHT"] == "STATUS.error-text-light"\n'), ('tests/test_error_red.py', '@pytest.mark.parametrize("ground", ["#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"])\n', '# RNV-COLOUR-SYNC, 2026-10-16: the grounds by name; #e8e8e8 is the register\'s\n# gold text floor, which the app does not draw.\n@pytest.mark.parametrize("ground", [colors.WHITE, colors.APP_SURFACE_LIGHT_3,\n                                    colors.APP_HOVER_LIGHT, "#e8e8e8"])\n'), ('tests/test_error_red.py', '    The assertion stays exact for the same reason it was written exact."""\n    assert colors.STATUS_ERROR_TEXT == "#dd6f77"\n', '    The assertion stays exact for the same reason it was written exact.\n    RNV-COLOUR-SYNC, 2026-10-16: exact in tests/test_colours_in_sync.py, against\n    the register at the pin; here, by the name brand_map.json takes it from."""\n    assert BRAND_MAP["STATUS_ERROR_TEXT"] == "STATUS.error-text"\n'), ('tests/test_ladder_and_plate.py', 'import ast\nimport pathlib\n\nimport pytest\n', 'import ast\nimport json\nimport pathlib\n\nimport pytest\n'), ('tests/test_ladder_and_plate.py', "ROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'ui/colors.py'\n", 'ROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / \'ui/colors.py\'\n\n#: RNV-COLOUR-SYNC, 2026-10-16. Where each colour comes from, as brand_map.json\n#: says. The values are held by tests/test_colours_in_sync.py, against the\n#: register at the pin; what this file holds is the name each one takes.\nBRAND_MAP = json.loads((ROOT / "brand_map.json").read_text(encoding="utf-8"))["colours"]\n'), ('tests/test_ladder_and_plate.py', "#: Constant name -> the APP key it mirrors, and the value both hold.\nNEW = {\n    'APP_PANEL_HOVER': ('panel-hover', '#3a3a3a'),\n    'APP_HOVER_LIGHT': ('hover-light', '#eeeeee'),\n}\n", "#: Constant name -> the APP key it mirrors. RNV-COLOUR-SYNC, 2026-10-16: the\n#: value both held was written here too; it is written from the register now.\nNEW = {\n    'APP_PANEL_HOVER': 'panel-hover',\n    'APP_HOVER_LIGHT': 'hover-light',\n}\n"), ('tests/test_ladder_and_plate.py', '    """The local half of the mirror. Runs everywhere, including where\n    engine.brand is not importable."""\n    drift = {n: getattr(colors, n) for n, (_, v) in NEW.items()\n             if getattr(colors, n) != v}\n    assert not drift, (\n        f\'these constants no longer hold their registered values: {drift}\\n\'\n        f\'If the brand moved, update this file in the same commit that updates \'\n        f\'ui/colors.py -- never one without the other.\')\n', '    """The local half of the mirror. Runs everywhere, including where\n    engine.brand is not importable.\n\n    RNV-COLOUR-SYNC, 2026-10-16: it held each value written out. It holds now\n    that brand_map.json takes each from its APP key; the value is written from\n    there, and tests/test_colours_in_sync.py holds it."""\n    drift = {n: BRAND_MAP.get(n) for n, key in NEW.items()\n             if BRAND_MAP.get(n) != f\'APP.{key}\'}\n    assert not drift, (\n        f\'brand_map.json does not take these from their APP keys: {drift}\')\n'), ('tests/test_ladder_and_plate.py', '    for name, (key, _) in NEW.items():\n        theirs, mine = brand.APP[key], getattr(colors, name)\n', '    for name, key in NEW.items():\n        theirs, mine = brand.APP[key], getattr(colors, name)\n'), ('tests/test_ladder_and_plate.py', "    assert colors.APP_HOVER_LIGHT == grey(14) == '#eeeeee'\n", '    assert colors.APP_HOVER_LIGHT == grey(14)\n'), ('tests/test_light_rewalk.py', 'import pytest\n\nfrom ui import colors as C\n', 'import json\nimport pathlib\n\nimport pytest\n\nfrom ui import colors as C\n\n#: RNV-COLOUR-SYNC, 2026-10-16. Where each colour comes from, as brand_map.json\n#: says. The values are held by tests/test_colours_in_sync.py, against the\n#: register at the pin; what this file holds is the name each one takes.\nBRAND_MAP = json.loads((pathlib.Path(__file__).resolve().parents[1] / "brand_map.json").read_text(encoding="utf-8"))["colours"]\n'), ('tests/test_light_rewalk.py', "REWALKED = {'STATUS_ERROR_TEXT_LIGHT': '#ae4650'}\n", "#: Each re-walked value, by the register name it is written from.\nREWALKED = {'STATUS_ERROR_TEXT_LIGHT': 'STATUS.error-text-light'}\n"), ('tests/test_light_rewalk.py', 'GOLD_DEEP = "#7e6529"   # BRAND_DARK_GOLD_DEEP, the family this shares with\n', 'GOLD_DEEP = C.BRAND_DARK_GOLD_DEEP   # the family this shares with\n'), ('tests/test_light_rewalk.py', '    """Pinned by value. rev 30 held #8a6581 / #976633 / #b84e58, walked against\n    #f5f5f5; rev 31 holds these, walked against #e8e8e8."""\n    assert getattr(C, name) == value\n', '    """Pinned by value. rev 30 held #8a6581 / #976633 / #b84e58, walked against\n    #f5f5f5; rev 31 holds these, walked against #e8e8e8.\n\n    RNV-COLOUR-SYNC, 2026-10-16: pinned by the register name brand_map.json\n    writes it from; tests/test_colours_in_sync.py holds the value."""\n    assert BRAND_MAP[name] == value\n'), ('tests/test_register_wiring.py', 'import ast\nimport pathlib\n\nimport pytest\n', 'import ast\nimport json\nimport pathlib\n\nimport pytest\n'), ('tests/test_register_wiring.py', "ROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / 'ui/colors.py'\n", 'ROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / \'ui/colors.py\'\n\n#: RNV-COLOUR-SYNC, 2026-10-16. Where each colour comes from, as brand_map.json\n#: says. The values are held by tests/test_colours_in_sync.py, against the\n#: register at the pin; what this file holds is the name each one takes.\nBRAND_MAP = json.loads((ROOT / "brand_map.json").read_text(encoding="utf-8"))["colours"]\n'), ('tests/test_register_wiring.py', "REGISTERED = {'TRUE_BLACK': '#000000', 'BRAND_BLACK': '#1a1a1a', 'APP_CARD': '#2a2a2a', 'APP_BORDER': '#333333',\n              'APP_PANEL_HOVER': '#3a3a3a', 'APP_HOVER_LIGHT': '#eeeeee'}\n", "#: RNV-COLOUR-SYNC, 2026-10-16: each value read from the constant, where it\n#: was written out, so the sweep looks for what the register holds today.\nREGISTERED = {name: getattr(colors, name) for name in (\n    'TRUE_BLACK', 'BRAND_BLACK', 'APP_CARD', 'APP_BORDER', 'APP_PANEL_HOVER',\n    'APP_HOVER_LIGHT')}\n"), ('tests/test_register_wiring.py', "    assert len(REGISTERED) >= 4\n    for name, value in REGISTERED.items():\n        assert getattr(colors, name) == value, (\n            f'{name} is {getattr(colors, name)}, not {value} -- the map this '\n            f'file sweeps for has gone stale against the constants')\n", "    assert len(REGISTERED) >= 4\n    for name in REGISTERED:\n        assert isinstance(BRAND_MAP.get(name), str), (\n            f'{name} is not taken from the register in brand_map.json -- the '\n            f'map this file sweeps for holds a value the register does not')\n"), ('tests/test_register_wiring.py', "            assert colors.LIGHT_THEME_COLORS['scroll_bg'] == '#eeeeee'\n", "            assert colors.LIGHT_THEME_COLORS['scroll_bg'] == colors.GREY_EE\n"), ('tests/test_status_register.py', 'import re\nfrom pathlib import Path\n', 'import json\nimport re\nfrom pathlib import Path\n'), ('tests/test_status_register.py', 'ROOT = Path(__file__).resolve().parent.parent\n', 'ROOT = Path(__file__).resolve().parent.parent\n\n#: RNV-COLOUR-SYNC, 2026-10-16. Where each colour comes from, as brand_map.json\n#: says. The values are held by tests/test_colours_in_sync.py, against the\n#: register at the pin; what this file holds is the name each one takes.\nBRAND_MAP = json.loads((ROOT / "brand_map.json").read_text(encoding="utf-8"))["colours"]\n'), ('tests/test_status_register.py', '    # base was retired, so it moves with it.\n    assert colors.STATUS_ERROR_TEXT == "#dd6f77"\n', '    # base was retired, so it moves with it.\n    # RNV-COLOUR-SYNC, 2026-10-16: pinned by the register name brand_map.json\n    # writes it from; tests/test_colours_in_sync.py holds the value.\n    assert BRAND_MAP["STATUS_ERROR_TEXT"] == "STATUS.error-text"\n'), ('tests/test_status_register.py', '    for ground in ("#000000", "#1a1a1a", "#2a2a2a"):\n', '    for ground in (colors.TRUE_BLACK, colors.BRAND_BLACK, colors.APP_CARD):\n'), ('tests/test_surface_alignment.py', 'from ui.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,\n                          LIGHT_THEME_COLORS as LIGHT)\n', 'from ui.colors import (DARK_THEME_COLORS as DARK, IMAGE_MODE_COLORS as IMAGE,\n                          LIGHT_THEME_COLORS as LIGHT)\nfrom ui.colors import APP_SURFACE_LIGHT_3, BRAND_BLACK\n'), ('tests/test_surface_alignment.py', '    assert LIGHT["panel_bg"] == "#f5f5f5", (\n        f"light panel is {LIGHT[\'panel_bg\']}, not the #f5f5f5 all five apps use")\n', '    # RNV-COLOUR-SYNC, 2026-10-16: the agreed surface by name, where it was its\n    # hex code: the register\'s surface-light-3, which all five apps use.\n    assert LIGHT["panel_bg"] == APP_SURFACE_LIGHT_3, (\n        f"light panel is {LIGHT[\'panel_bg\']}, not the {APP_SURFACE_LIGHT_3} all five apps use")\n'), ('tests/test_surface_alignment.py', '    assert DARK["input_bg"] == "#1a1a1a", (\n        f"dark input is {DARK[\'input_bg\']}, not the #1a1a1a all five apps use")\n', '    assert DARK["input_bg"] == BRAND_BLACK, (\n        f"dark input is {DARK[\'input_bg\']}, not the {BRAND_BLACK} all five apps use")\n'), ('ui/colors.py', '\nBRAND_GOLD: Final[str] = "#d2bc93"\n', '\nBRAND_GOLD: Final[str] = "#d2bc93"  # brand: APP.accent\n'), ('ui/colors.py', '\nBRAND_DARK_GOLD: Final[str] = "#8c7337"\n', '\nBRAND_DARK_GOLD: Final[str] = "#8c7337"  # brand: APP.accent-light-mode\n'), ('ui/colors.py', '\nTRUE_BLACK: Final[str] = "#000000"\n', '\nTRUE_BLACK: Final[str] = "#000000"  # brand: PERMANENT.black\n'), ('ui/colors.py', '\nWHITE: Final[str] = "#ffffff"\n', '\nWHITE: Final[str] = "#ffffff"  # brand: PERMANENT.white\n'), ('ui/colors.py', '\nBRAND_BLACK: Final[str] = "#1a1a1a"\n', '\nBRAND_BLACK: Final[str] = "#1a1a1a"  # brand: PERMANENT.charcoal\n'), ('ui/colors.py', '\nAPP_CARD: Final[str] = "#2a2a2a"\n', '\nAPP_CARD: Final[str] = "#2a2a2a"  # brand: APP.card\n'), ('ui/colors.py', '\nAPP_BORDER: Final[str] = "#333333"\n', '\nAPP_BORDER: Final[str] = "#333333"  # brand: APP.border\n'), ('ui/colors.py', '\nAPP_TEXT: Final[str] = "#dddddd"\n', '\nAPP_TEXT: Final[str] = "#dddddd"  # brand: APP.text\n'), ('ui/colors.py', '\nAPP_TEXT_DIM: Final[str] = "#aaaaaa"\n', '\nAPP_TEXT_DIM: Final[str] = "#aaaaaa"  # brand: APP.text-dim\n'), ('ui/colors.py', '\nAPP_PANEL_HOVER: Final[str] = "#3a3a3a"\n', '\nAPP_PANEL_HOVER: Final[str] = "#3a3a3a"  # brand: APP.panel-hover\n'), ('ui/colors.py', '\nGREY_44: Final[str] = "#444444"\n', '\nGREY_44: Final[str] = "#444444"  # app-owned\n'), ('ui/colors.py', '\nAPP_HOVER_LIGHT: Final[str] = "#eeeeee"\n', '\nAPP_HOVER_LIGHT: Final[str] = "#eeeeee"  # brand: APP.hover-light\n'), ('ui/colors.py', '\nAPP_SURFACE_LIGHT_3: Final[str] = "#f5f5f5"\n', '\nAPP_SURFACE_LIGHT_3: Final[str] = "#f5f5f5"  # brand: APP.surface-light-3\n'), ('ui/colors.py', '\nGREY_EE: Final[str] = "#eeeeee"\n', '\nGREY_EE: Final[str] = "#eeeeee"  # app-owned\n'), ('ui/colors.py', '\nGREY_CC: Final[str] = "#cccccc"\n', '\nGREY_CC: Final[str] = "#cccccc"  # app-owned\n'), ('ui/colors.py', '\nGREY_88: Final[str] = "#888888"\n', '\nGREY_88: Final[str] = "#888888"  # app-owned\n'), ('ui/colors.py', '\nGREY_55: Final[str] = "#555555"\n', '\nGREY_55: Final[str] = "#555555"  # app-owned\n'), ('ui/colors.py', '\nSELECTION_OVERLAY_COLOR: Final[str] = "rgba(0,120,215,200)"\n', '\nSELECTION_OVERLAY_COLOR: Final[str] = "rgba(0,120,215,200)"  # app-owned\n'), ('ui/colors.py', '\nGREY_66: Final[str] = "#666666"\n', '\nGREY_66: Final[str] = "#666666"  # app-owned\n'), ('ui/colors.py', '\nSEARCH_HIGHLIGHT_COLOR: Final[tuple[int,int,int]] = (0, 255, 100)\n', '\nSEARCH_HIGHLIGHT_COLOR: Final[tuple[int,int,int]] = (0, 255, 100)  # app-owned\n'), ('ui/colors.py', '\nSLOT_BORDER_THICK_COLOR: Final[tuple[int,int,int]] = (60, 60, 60)\n', '\nSLOT_BORDER_THICK_COLOR: Final[tuple[int,int,int]] = (60, 60, 60)  # app-owned\n'), ('ui/colors.py', '\nSTATUS_ERROR_TEXT: Final[str] = "#dd6f77"\n', '\nSTATUS_ERROR_TEXT: Final[str] = "#dd6f77"  # brand: STATUS.error-text\n'), ('ui/colors.py', '\nSTATUS_ERROR_TEXT_LIGHT: Final[str] = "#ae4650"\n', '\nSTATUS_ERROR_TEXT_LIGHT: Final[str] = "#ae4650"  # brand: STATUS.error-text-light\n'), ('ui/colors.py', '\nSVG_EXPORT_BG: Final[str] = "#ffffff"\n', '\nSVG_EXPORT_BG: Final[str] = "#ffffff"  # app-owned\n'), ('ui/colors.py', '\nSVG_EXPORT_STROKE: Final[str] = "#000000"\n', '\nSVG_EXPORT_STROKE: Final[str] = "#000000"  # app-owned\n'), ('ui/colors.py', '\nDATA_DEFAULT_COLOR: Final[str] = "#000000"\n', '\nDATA_DEFAULT_COLOR: Final[str] = "#000000"  # app-owned\n'), ('ui/colors.py', '\nSESSION_FALLBACK_COLOR: Final[str] = "#a9a9a9"\n', '\nSESSION_FALLBACK_COLOR: Final[str] = "#a9a9a9"  # app-owned\n'), ('ui/colors.py', '\nSESSION_FALLBACK_COLOR_IMAGE: Final[str] = "#000000"\n', '\nSESSION_FALLBACK_COLOR_IMAGE: Final[str] = "#000000"  # app-owned\n'), ('ui/colors.py', '\nTRANSPARENT_RGBA: Final[tuple[int, int, int, int]] = (0, 0, 0, 0)\n', '\nTRANSPARENT_RGBA: Final[tuple[int, int, int, int]] = (0, 0, 0, 0)  # app-owned\n'), ('ui/colors.py', '\nDEFAULT_SLOT_COLOR: Final[str] = "#a9a9a9"\n', '\nDEFAULT_SLOT_COLOR: Final[str] = "#a9a9a9"  # app-owned\n')]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree, then every new file."""
    for rel, old, new in SUBS:
        tree.sub(rel, old, new)
    for rel, text in NEW_FILES.items():
        if (tree.root / rel).exists():
            raise Stop(f"{rel} already exists here, and this round creates it. "
                       f"Nothing was written.", EXIT_CANNOT_RUN)
        tree.write(rel, text)


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
    def units(src):
        """Every function, method and assignment a source defines, each under its
        name -> its text. A comment is not part of it; a docstring is."""
        out = dict()
        for node in ast.parse(src).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[node.name + "()"] = ast.unparse(node)
            elif isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out[node.name + "." + sub.name + "()"] = ast.unparse(sub)
                    elif isinstance(sub, (ast.Assign, ast.AnnAssign)) and sub.value is not None:
                        t = sub.targets[0] if isinstance(sub, ast.Assign) else sub.target
                        if isinstance(t, ast.Name):
                            out[node.name + "." + t.id] = ast.unparse(sub.value)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                t = node.targets[0] if isinstance(node, ast.Assign) else node.target
                if isinstance(t, ast.Name):
                    out[t.id] = ast.unparse(node.value)
        return out

    def code(src):
        """units() of a source with every docstring taken out: what the code
        does, not what it says of itself."""
        module = ast.parse(src)
        for node in ast.walk(module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                        and isinstance(first.value.value, str):
                    node.body = node.body[1:] or [ast.Pass()]
        return units(ast.unparse(module))

    def moved(was_src, now_src):
        """(what arrives, what goes, what changes) between two sources, by name."""
        was, now = units(was_src), units(now_src)
        return (sorted(set(now) - set(was)), sorted(set(was) - set(now)),
                sorted(k for k in set(was) & set(now) if was[k] != now[k]))

    def as_written(rel):
        """A file as this round leaves it: from the tree if the round holds it, else from disk."""
        if rel in tree.files:
            return tree.files[rel]
        return (tree.root / rel).read_text(encoding="utf-8-sig", errors="replace")

    def app_sources():
        """(path, text) of the application's Python as this round leaves it: no
        tests, no runner, no delivery script."""
        skip = ("tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__",
                "venv", "env", "htmlcov", "node_modules")
        paths = set(p.relative_to(tree.root).as_posix() for p in tree.root.rglob("*.py"))
        paths |= set(r for r in tree.files if r.endswith(".py"))
        for rel in sorted(paths - tree.deleted):
            parts = rel.split("/")
            if any(q in skip or q.startswith(".") for q in parts[:-1]):
                continue
            if len(parts) == 1 and parts[0].startswith(("test_", "conftest", "run_tests")):
                continue
            text = as_written(rel)
            if len(parts) == 1 and "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
                continue
            yield rel, text

    def names_in(text):
        """Every name, attribute and imported name a source reaches for, and
        every string it writes out whole."""
        found = set()
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Name):
                found.add(node.id)
            elif isinstance(node, ast.Attribute):
                found.add(node.attr)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                found.update(a.name for a in node.names)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                found.add(node.value)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                found.add(node.name)
        return found

    def tests_in(src):
        return [n.name for n in ast.walk(ast.parse(src))
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test")]

    def check_moves(table):
        """Each file moves by what the table lists for it, and by nothing else."""
        for rel, arrives, goes, changes in table:
            got = moved(_original(tree, rel), tree.read(rel))
            assert got == (arrives, goes, changes), (
                f"{rel} moved by other than what this round lists: arrives {got[0]}, goes {got[1]}, "
                f"changes {got[2]}")
    check_moves([('tests/test_app_mirror.py', ['BRAND_MAP', 'NEUTRALS'], ['PINNED'], ['DIALOG_BTN_HOVER', 'test_every_pinned_neutral_is_what_the_register_held()', 'test_register_values_match_rnv_brand()', 'test_the_ink_clears_the_text_floor_on_every_dark_ground_it_touches()', 'test_the_ink_is_a_step_on_the_grid()', 'test_the_light_ink_is_true_black()', 'test_the_light_pane_is_no_longer_the_card_colour()', 'test_the_names_this_file_reads_still_exist()']), ('tests/test_brand_mirror.py', ['BRAND_MAP'], [], ['test_light_ink_clears_every_ground_it_draws_on()', 'test_register_values_match_rnv_brand()', 'test_the_derivation_steps_are_the_published_ones()']), ('tests/test_button_key_names.py', ['_values()'], [], ['PINNED_DIALOG', 'PINNED_MAIN', 'test_the_dialog_family_holds_what_the_dialogs_already_painted()', 'test_the_rename_moved_no_value()']), ('tests/test_constant_names.py', ['BRAND_MAP'], [], ['test_the_values_they_named_are_still_here()']), ('tests/test_error_red.py', ['BRAND_MAP'], [], ['test_dark_error_text_mirrors_the_register_and_still_clears()', 'test_light_error_text_carries_on_the_grounds_it_reaches()', 'test_the_family_is_the_registered_one()', 'test_the_light_error_text_is_registered_and_why_that_changed()']), ('tests/test_ladder_and_plate.py', ['BRAND_MAP'], [], ['NEW', 'test_the_new_constants_hold_the_registered_values()', 'test_the_new_constants_match_rnv_brand()', 'test_the_plate_is_a_step_on_the_ink_grid()']), ('tests/test_light_rewalk.py', ['BRAND_MAP'], [], ['GOLD_DEEP', 'REWALKED', 'test_the_light_values_are_the_re_walked_ones()']), ('tests/test_register_wiring.py', ['BRAND_MAP'], [], ['REGISTERED', 'test_the_light_groove_takes_the_ramp_step_not_the_hover()', 'test_the_register_map_is_not_empty()']), ('tests/test_status_register.py', ['BRAND_MAP'], [], ['test_the_dark_error_text_still_clears_on_every_dark_ground()', 'test_the_three_ruled_values_are_the_register_s()']), ('tests/test_surface_alignment.py', [], [], ['test_the_dark_input_is_the_agreed_surface()', 'test_the_light_panel_is_the_agreed_surface()']), ('ui/colors.py', [], [], [])])

    # ---- no colour moves: every value ui/colors.py defines is what it was
    def values(text):
        ns = {}
        exec(compile(text, "ui/colors.py", "exec"), ns)
        return {k: v for k, v in ns.items() if not k.startswith("__") and not callable(v)
                and type(v).__name__ != "TypeAliasType"}
    before, after = values(_original(tree, "ui/colors.py")), values(tree.read("ui/colors.py"))
    assert set(before) == set(after), f"ui/colors.py defines other names: {sorted(set(before) ^ set(after))}"
    moved_values = sorted(k for k in before if before[k] != after[k])
    assert not moved_values, f"a colour moved: {moved_values}"
    assert len(before) >= 50, f"only {len(before)} values compared -- the comparison is blind"

    # ---- the colour file changes by its note and a marker on each mapped line, and nothing else
    was_lines = _original(tree, "ui/colors.py").split("\n")
    now_lines = tree.read("ui/colors.py").split("\n")
    note = [l for l in now_lines if l not in was_lines and l.startswith("# ")]
    assert len(note) == 7 and SENTINEL in note[0], f"the note is not the one this round writes: {note[:1]}"
    rest = [l for l in now_lines if l not in note]
    assert len(rest) == len(was_lines), "ui/colors.py gained or lost a line other than its note"
    mapping = json.loads(tree.read("brand_map.json"))
    marked = []
    for a, b in zip(was_lines, rest):
        if a != b:
            m = re.fullmatch(re.escape(a) + r"  # (brand: \S+|app-owned)", b)
            assert m, f"ui/colors.py: a line changed by more than its marker: {b!r}"
            marked.append(b.split(":", 1)[0])
    assert sorted(marked) == sorted(mapping["colours"]), "the marked lines are not the map's names"

    # ---- the map holds what was ruled
    colours = mapping["colours"]
    assert len(colours) == 30, f"the map holds {len(colours)} colours"
    assert colours["BRAND_GOLD"] == "APP.accent" and colours["BRAND_DARK_GOLD"] == "APP.accent-light-mode", \
        "the golds do not follow the register's accent names (#45 A)"
    for name in ("SVG_EXPORT_BG", "SVG_EXPORT_STROKE", "DATA_DEFAULT_COLOR", "SESSION_FALLBACK_COLOR_IMAGE"):
        assert isinstance(colours[name], dict), f"{name} is not the app's own (#46 A)"
    for name, entry in colours.items():
        ref = entry if isinstance(entry, str) else None
        if ref is None:
            assert len(entry["why"].split()) >= 3, f"{name} gives no reason"
        else:
            table_, _, key = ref.partition(".")
            assert table_ in ("PERMANENT", "APP", "STATUS") and key, f"{name}: {ref}"

    # ---- the sync writes exactly this colour file, for the values it holds
    tool = types.ModuleType("sync_colors")
    tool.__file__ = str(tree.root / "tools" / "sync_colors.py")
    exec(compile(tree.read("tools/sync_colors.py"), "tools/sync_colors.py", "exec"), tool.__dict__)
    stand_in = types.SimpleNamespace(PERMANENT={}, APP={}, STATUS={})
    for name, ref in colours.items():
        if isinstance(ref, str):
            table_, _, key = ref.partition(".")
            getattr(stand_in, table_)[key] = after[name]
    text = tree.read("ui/colors.py")
    assert tool.rewrite(text, tool.resolve(mapping, stand_in), "ui/colors.py") == text, \
        "ui/colors.py is not what the sync writes for the values it holds"
    unmarked = tool.rewrite(_original(tree, "ui/colors.py"), tool.resolve(mapping, stand_in), "ui/colors.py")
    assert [l for l in text.split("\n") if l not in note] == unmarked.split("\n"), \
        "the sync, run on the file as it was, does not write what this round writes"

    # ---- the tests read names, where they wrote a brand value as its hex code
    def hexes_in_code(src):
        doc = set()
        tree_ = ast.parse(src)
        for node in ast.walk(tree_):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                b0 = node.body[0] if node.body else None
                if isinstance(b0, ast.Expr) and isinstance(getattr(b0, "value", None), ast.Constant) \
                        and isinstance(b0.value.value, str):
                    doc.update(range(b0.lineno, b0.end_lineno + 1))
        brand_hexes = {v.lower() for k, v in after.items() if k in colours and isinstance(v, str)
                       and isinstance(colours[k], str)}
        found = []
        for number, line in enumerate(src.split("\n"), 1):
            if number in doc or line.strip().startswith("#"):
                continue
            found += [h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}\b", line) if h.lower() in brand_hexes]
        return sorted(found)
    #: What each edited test still writes as a brand value's hex code, on purpose:
    #: an example given to a helper, and the register's published rungs.
    LEFT = {'tests/test_app_mirror.py': [], 'tests/test_brand_mirror.py': [], 'tests/test_button_key_names.py': [],
            'tests/test_constant_names.py': ['#000000', '#000000', '#ffffff', '#ffffff'],
            'tests/test_error_red.py': ['#000000', '#f5f5f5', '#ffffff', '#ffffff'],
            'tests/test_ladder_and_plate.py': [],
            'tests/test_light_rewalk.py': ['#000000', '#eeeeee', '#f5f5f5', '#ffffff', '#ffffff', '#ffffff', '#ffffff'],
            'tests/test_register_wiring.py': [], 'tests/test_status_register.py': [], 'tests/test_surface_alignment.py': []}
    for rel, left in LEFT.items():
        got = hexes_in_code(tree.read(rel))
        assert got == sorted(left), f"{rel} writes brand values as hex codes: {got}"

    assert sorted(tree.files) == ['.github/workflows/brand-sync.yml', 'COLORS.md', 'README.md', 'brand_map.json', 'tests/test_app_mirror.py', 'tests/test_brand_mirror.py', 'tests/test_button_key_names.py', 'tests/test_colours_in_sync.py', 'tests/test_constant_names.py', 'tests/test_error_red.py', 'tests/test_ladder_and_plate.py', 'tests/test_light_rewalk.py', 'tests/test_register_wiring.py', 'tests/test_status_register.py', 'tests/test_surface_alignment.py', 'tools/sync_colors.py', 'ui/colors.py'] and not tree.deleted, f"this round writes {sorted(tree.files)}"

    # ================= every file this round creates or edits, as this round writes it
    import hashlib
    for rel, sha in (('.github/workflows/brand-sync.yml', '419a9b6a5f9941aa54e0b2977519d365d3337a3a8d316950d93665ea689b1331'), ('COLORS.md', '44e383744a0a1332cad9a130e436e0308f3db82ac98b12c6b5f0a25d111afed8'), ('README.md', 'c7108b5dca626e69154a8e51fe210c3b8249de7d28652cd65efe1d1c94228e9e'), ('brand_map.json', '1eea37c780a5d4a11bf229c82c71727b69e471345665c69ab3ac48da3c33492c'), ('tests/test_app_mirror.py', 'c2dc9abd488b6d8d14cd79210adf4995ef628c8799c5e42c8b1b3b3ee8d5d85d'), ('tests/test_brand_mirror.py', 'e3909ea1c61704ff091e5c96439e93ad8f63847e50fdb76158f054483a5b518f'), ('tests/test_button_key_names.py', '1722d769d15897a0eb439a3d73aac640b9dfdb1660e6e36c64ae3103b748a225'), ('tests/test_colours_in_sync.py', '9ccf67a69151cdf9c910e5bacba535fd9db89b8c7c8cf2a38e9af06cfb993614'), ('tests/test_constant_names.py', 'ca0abf0a95f3ac9e43c775dc971211324b4660e677dd070f46908b8e45218b7f'), ('tests/test_error_red.py', '0ceb805d1b3af0c90e46106635419af85fb203340fb85f843541997bece000e2'), ('tests/test_ladder_and_plate.py', '4eb1a11a32023dc1811f1b7f9d18ea95c9d17f8ee2868a9fbb3c84c46a3a4dd3'), ('tests/test_light_rewalk.py', '5df3f00469f9219d3b6d8ef14f03cce17b981ca0f5127e0830ab0d59a454702e'), ('tests/test_register_wiring.py', '64ff5ea17a8c1db8d830e968ad3b98a51b00f53b52e2a6559044eb44c5919a08'), ('tests/test_status_register.py', 'b314db130487fec5bdb9af097789fcec72c53ce077df09c4673e6d616f40761c'), ('tests/test_surface_alignment.py', 'd232277138fdd19ac9564edcea0abd2ef8129f51cdc29ba67796a21600718381'), ('tools/sync_colors.py', '9bc955e171ae9ee090f7057b5f40af58174d4585982e29cb97e85872354ad06d'), ('ui/colors.py', '60a769a2a98509c81845efb1bb5e568fdf06a9137cf5ceb68dbfe46b80afed97')):
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        assert got == sha, f"{rel} is not the file this round writes: {got[:12]}"

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
