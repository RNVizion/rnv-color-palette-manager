"""chart ruling 1: the dialogs' notes and previews in the muted text

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-color-palette-manager, derived against a fresh clone at the live head (c82ddf2).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-27, decision 1 of the colour chart: "If they all split it for
each mode then it's fine to have 2 values, but make sure they are values we
are already using." They all split it the same way. Muted text is #888888 in
dark and image and #666666 in light in all five applications, and the
description labels that wrote `color: gray`/`grey` -- #808080 in every mode,
4.40:1 on the dark panels and 3.62:1 in light, under the 4.5 floor -- now read
the app's own muted key. No new colour: both values are already painted.

Here: six labels in the settings and batch export dialogs -- the clipboard
preview, the created and modified dates, the empty-history line (twice) and
the batch filename preview. Each is named "muted_text", and each dialog's
stylesheet draws that name in text_secondary -- the key this app kept aligned
and unpainted for exactly this, and the local the settings dialog already read
and never used. Rendered: 12 of 123 captures change, 4 per mode, every changed
pixel the grey recoloured.
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
SENTINEL = 'RNV-MUTED-DESCRIPTIONS'
SENTINEL_FILE = 'tests/test_muted_and_disabled_text.py'
GUARD = 'tests/test_muted_and_disabled_text.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_muted_and_disabled_text.py', 'tests/test_app_mirror.py']
DESCRIPTION = "chart ruling 1: the dialogs' notes and previews in the muted text"

#: EXACTLY WHAT CI RUNS. Both workflows run `python run_tests.py`, which runs
#: the locked root suite under unittest and then tests/ under pytest.
SUITES = [("python run_tests.py  (both CI workflows)",
           [sys.executable, "run_tests.py"])]

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '898c16b8a02fa92b09c1bed0fa1f9f8b872d2d3d29d506b7a9c9a1ec357de42e', '.github/workflows/tests.yml': '5d3891f82137b62cb3b2576454eb30079ee981ca559fac90d67431f579e5abe5'}

SHADOWS = {"colors.py", "conftest.py", "run_tests.py", "settings_dialog.py", "test_rnv_palette_manager.py"}

LEFT_ALONE = ['the tab keys, still NOT CONSUMED and still noted so, one note in each palette.', 'the About dialog, which has no grey text to move.']


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('ui/settings_dialog.py',
             '        self.lbl_clipboard_preview.setStyleSheet("color: grey; font-style: italic;")\n',
             '        self.lbl_clipboard_preview.setObjectName("muted_text")\n        self.lbl_clipboard_preview.setStyleSheet("font-style: italic;")\n')
    tree.sub('ui/settings_dialog.py',
             '        self.lbl_created.setStyleSheet("color: grey; font-style: italic;")\n',
             '        self.lbl_created.setObjectName("muted_text")\n        self.lbl_created.setStyleSheet("font-style: italic;")\n')
    tree.sub('ui/settings_dialog.py',
             '        self.lbl_modified.setStyleSheet("color: grey; font-style: italic;")\n',
             '        self.lbl_modified.setObjectName("muted_text")\n        self.lbl_modified.setStyleSheet("font-style: italic;")\n')
    tree.sub('ui/settings_dialog.py',
             '            placeholder.setStyleSheet("color: grey; font-style: italic;")\n',
             '            placeholder.setObjectName("muted_text")\n            placeholder.setStyleSheet("font-style: italic;")\n', times=2)
    tree.sub('ui/settings_dialog.py',
             "            /* ---- Labels ---- */\n            QLabel {{\n                color: {theme['text_color']};\n            }}\n",
             "            /* ---- Labels ---- */\n            QLabel {{\n                color: {theme['text_color']};\n            }}\n            /* ---- Muted text: notes, previews, the empty history ----\n               RNV-MUTED-DESCRIPTIONS, ruling 1 of 2026-09-27 */\n            QLabel#muted_text {{\n                color: {text_secondary};\n            }}\n")
    tree.sub('ui/batch_export_dialog.py',
             '        self._lbl_preview.setStyleSheet("color: grey; font-style: italic; font-size: 11px;")\n',
             '        self._lbl_preview.setObjectName("muted_text")\n        self._lbl_preview.setStyleSheet("font-style: italic; font-size: 11px;")\n')
    tree.sub('ui/batch_export_dialog.py',
             '            QLabel {{ color: {text}; }}\n',
             '            QLabel {{ color: {text}; }}\n            /* RNV-MUTED-DESCRIPTIONS, ruling 1: the filename preview */\n            QLabel#muted_text {{ color: {theme["text_secondary"]}; }}\n')
    tree.sub('ui/colors.py',
             "    # NOT CONSUMED. Nothing paints this key -- ui/settings_dialog.py reads it\n    # into a local and never uses that local, which is why a grep for it looks\n    # live. Aligned to the value the apps that DO paint a muted text use, so\n    # wiring it up stays one line and not a colour decision.\n    'text_secondary': GREY_88,\n",
             '    # Muted text. Kept aligned while nothing painted it, so that wiring it up\n    # would be one line and not a colour decision -- and on 2026-09-27 it was\n    # (RNV-MUTED-DESCRIPTIONS, ruling 1): the settings and batch export\n    # dialogs\' notes, previews and empty history, named "muted_text" in each\n    # dialog\'s stylesheet. They were `color: grey`, #808080 in every mode.\n    \'text_secondary\': GREY_88,\n')
    tree.sub('ui/colors.py',
             "    # NOT CONSUMED -- see the note in the dark palette.\n    'text_secondary': GREY_66,\n",
             "    # Muted text -- see the note in the dark palette.\n    'text_secondary': GREY_66,\n")
    tree.sub('ui/colors.py',
             "    # NOT CONSUMED -- see the note in the dark palette.\n    'text_secondary': GREY_88,\n",
             "    # Muted text -- see the note in the dark palette.\n    'text_secondary': GREY_88,\n")
    tree.sub('tests/test_muted_and_disabled_text.py',
             '`text_secondary` is NOT painted anywhere. It is defined in all three palettes,\nread into a local in ui/settings_dialog.py, and that local is never used. It is\nkept and kept correct so wiring it up is one line. The tests below hold that\nstory to the code: if someone paints it, the "NOT CONSUMED" notes beside the\nvalues become false and the run says so.\n',
             '`text_secondary` is live since 2026-09-27 (RNV-MUTED-DESCRIPTIONS, ruling 1 of\nthe colour chart). Until then nothing painted it: the settings dialog read it\ninto a local it never used, and six labels in two dialogs wrote `color: grey`\ninstead -- #808080 in every mode. They are named "muted_text" now and each\ndialog\'s stylesheet draws that name in text_secondary: #888888 in dark and\nimage, #666666 in light, the muted text all five applications paint. The\ntests below hold the wiring, the values, and the colour each label ends up\ndrawn in.\n')
    tree.sub('tests/test_muted_and_disabled_text.py',
             '# The one place that reads the key without painting it. Named so the sweep\n# below can tell a dead read from a live one.\nKNOWN_DEAD_READ = "ui/settings_dialog.py"\n',
             '# The two dialogs that paint the key, and the only files that read it.\nPAINTED_IN = ["ui/batch_export_dialog.py", "ui/settings_dialog.py"]\n')
    tree.sub('tests/test_app_mirror.py',
             'def test_the_tab_keys_carry_the_note_that_says_so():\n    """Both halves of the arrangement, held together. The values are correct\n    and the note explains why they are not painted."""\n    src = SRC.read_text(encoding=\'utf-8-sig\')\n    assert src.count(\'NOT CONSUMED\') >= 4, (\n        \'the NOT CONSUMED notes are gone -- text_secondary had three and the \'\n        \'tab block adds one\')\n',
             'def test_the_tab_keys_carry_the_note_that_says_so():\n    """Both halves of the arrangement, held together. The values are correct\n    and the note explains why they are not painted -- one note above the tab\n    keys in each of the three palettes.\n\n    Counted across the whole file until 2026-09-27, as four or more: three\n    beside text_secondary and the tab block\'s. text_secondary is painted now\n    (RNV-MUTED-DESCRIPTIONS, ruling 1) and its notes went with it, so this\n    measures the tab block\'s own, where they stand."""\n    lines = SRC.read_text(encoding=\'utf-8-sig\').splitlines()\n    rows = [i for i, line in enumerate(lines) if line.strip().startswith("\'tab_bg\':")]\n    assert len(rows) == 3, f\'expected tab_bg in three palettes, found lines {rows}\'\n    for i in rows:\n        assert \'NOT CONSUMED\' in \'\\n\'.join(lines[max(0, i - 20):i]), (\n            f\'the tab keys at line {i + 1} lost the note that says they are \'\n            f\'not painted\')\n')
    tree.sub('tests/test_muted_and_disabled_text.py',
             'def test_the_not_consumed_note_is_still_true():\n    """Both directions. The note beside `text_secondary` tells the next reader\n    nothing paints it. If that stops being true the note is a lie, and a lie in\n    a palette is how a value gets trusted that should not be."""\n    sites = _references("text_secondary")\n    assert sites == [KNOWN_DEAD_READ], (\n        f"text_secondary is now referenced in {sites}. If it is being painted, "\n        f"delete the NOT CONSUMED notes in ui/colors.py -- they are no longer "\n        f"true.")\n\n    # Counted BESIDE the key rather than across the whole file. A whole-file\n    # count measures every NOT CONSUMED note in ui/colors.py, so annotating any\n    # OTHER dead key -- which the tab block did on 2026-08-28 -- broke a test\n    # that was never about those keys. It measures what it claims now.\n    lines = COLORS_PY.read_text(encoding="utf-8").splitlines()\n    annotated = 0\n    for i, line in enumerate(lines):\n        if not line.strip().startswith("\'text_secondary\':"):\n            continue\n        if re.search(r"#\\s*NOT CONSUMED", "\\n".join(lines[max(0, i - 6):i])):\n            annotated += 1\n    assert annotated == 3, (\n        f"expected a NOT CONSUMED note beside each of the three "\n        f"text_secondary values, found {annotated}")\n\n\ndef test_the_dead_read_is_still_dead():\n    """ui/settings_dialog.py assigns the key to a local and never uses it,\n    which is exactly why a grep for `text_secondary` looks live."""\n    source = (ROOT / KNOWN_DEAD_READ).read_text(encoding="utf-8")\n    # The lookarounds are load-bearing: `\\b` happily matches the identifier\n    # INSIDE the string key of `theme.get(\'text_secondary\', ...)`, which is the\n    # dict lookup and not a use of the local. Without them this test fails on\n    # the very line it exists to describe.\n    bare = re.compile(r"(?<![\'\\"])\\btext_secondary\\b(?![\'\\"])")\n    assigns, uses = [], []\n    for i, line in enumerate(source.splitlines(), 1):\n        for match in bare.finditer(line):\n            after = line[match.end():].lstrip()\n            (assigns if after.startswith("=") and not after.startswith("==")\n             else uses).append(f"{i}: {line.strip()[:60]}")\n    assert len(assigns) == 1, f"expected one assignment, found {assigns}"\n    assert not uses, (\n        f"the text_secondary local is now used -- it is live, and ui/colors.py "\n        f"still says it is not: {uses}")\n',
             'def test_the_muted_key_is_read_where_it_is_painted():\n    """Both directions. Read in exactly the two dialogs that paint it, and no\n    note beside the values still says nothing paints it -- a note like that is\n    how a value gets trusted, or distrusted, for the wrong reason."""\n    sites = _references("text_secondary")\n    assert sites == PAINTED_IN, (\n        f"text_secondary is referenced in {sites}; the dialogs that paint it "\n        f"are {PAINTED_IN}. A new reader needs its ground measured.")\n\n    # Counted BESIDE the key rather than across the whole file: the tab block\n    # carries NOT CONSUMED notes of its own, and they are not about this key.\n    lines = COLORS_PY.read_text(encoding="utf-8").splitlines()\n    beside = [i + 1 for i, line in enumerate(lines)\n              if line.strip().startswith("\'text_secondary\':")]\n    assert len(beside) == 3, f"expected text_secondary in three palettes, found {beside}"\n    stale = [n for n in beside\n             if re.search(r"#\\s*NOT CONSUMED", "\\n".join(lines[max(0, n - 7):n - 1]))]\n    assert not stale, f"a NOT CONSUMED note still stands beside text_secondary at {stale}"\n\n\ndef test_the_settings_local_is_now_used():\n    """ui/settings_dialog.py assigned the key to a local and never used it,\n    which is why a grep for `text_secondary` looked live when it was not. The\n    muted-text rule in the dialog\'s stylesheet is the use."""\n    source = (ROOT / "ui" / "settings_dialog.py").read_text(encoding="utf-8")\n    # The lookarounds are load-bearing: `\\b` happily matches the identifier\n    # INSIDE the string key of `theme.get(\'text_secondary\', ...)`, which is the\n    # dict lookup and not a use of the local.\n    bare = re.compile(r"(?<![\'\\"])\\btext_secondary\\b(?![\'\\"])")\n    assigns, uses = [], []\n    for i, line in enumerate(source.splitlines(), 1):\n        for match in bare.finditer(line):\n            after = line[match.end():].lstrip()\n            (assigns if after.startswith("=") and not after.startswith("==")\n             else uses).append(f"{i}: {line.strip()[:60]}")\n    assert len(assigns) == 1, f"expected one assignment, found {assigns}"\n    assert uses, "the text_secondary local is assigned and never used"\n\n\n# RNV-MUTED-DESCRIPTIONS\n# ------------------------------------------ the muted labels, drawn (ruling 1)\n\ndef test_the_muted_values_are_the_ones_the_fleet_already_uses():\n    """Ruling 1 was conditional: two values are fine if every app splits it by\n    mode, and only with values already in use. Both halves, held here."""\n    assert THEMES["DARK"]["text_secondary"] == THEMES["IMAGE"]["text_secondary"] == "#888888"\n    assert THEMES["LIGHT"]["text_secondary"] == "#666666"\n\n\ndef _manager(mode: str):\n    from ui.theme_manager import ThemeManager\n    manager = ThemeManager()\n    manager.current_theme = mode\n    manager.image_mode_active = (mode == "image")\n    return manager\n\n\ndef _ink(widget) -> str:\n    from PyQt6.QtGui import QPalette\n    widget.ensurePolished()\n    return widget.palette().color(QPalette.ColorRole.WindowText).name()\n\n\n@pytest.mark.parametrize("mode", ["dark", "light", "image"])\ndef test_the_muted_labels_draw_in_text_secondary(qapp, mode):\n    """Built the way the app builds them, in each mode. Settings draws image\n    mode from the dark palette, as its _apply_theme() chooses; batch export\n    draws it from the image palette. Both hold #888888 there."""\n    from PyQt6.QtWidgets import QLabel\n\n    from ui.batch_export_dialog import BatchExportDialog\n    from ui.settings_dialog import SettingsDialog\n    from utils.settings_manager import SettingsManager\n\n    manager = _manager(mode)\n    settings = SettingsDialog(settings=SettingsManager(), theme_manager=manager)\n    batch = BatchExportDialog(settings=SettingsManager(), theme_manager=manager)\n    cases = [(settings, THEMES["DARK" if mode == "image" else mode.upper()],\n              [settings.lbl_clipboard_preview, settings.lbl_created, settings.lbl_modified]),\n             (batch, THEMES[mode.upper()], [batch._lbl_preview])]\n    try:\n        for dialog, palette, expected in cases:\n            name = type(dialog).__name__\n            muted = [w for w in dialog.findChildren(QLabel) if w.objectName() == "muted_text"]\n            missing = [w.text() for w in expected if all(w is not m for m in muted)]\n            assert not missing, (name, "not named muted_text", missing)\n            for w in muted:\n                assert "color" not in w.styleSheet(), (name, w.text(), w.styleSheet())\n                assert _ink(w) == palette["text_secondary"].lower(), (\n                    name, mode, w.text()[:40], _ink(w))\n            # and the rule reaches nothing it should not\n            plain = [w for w in dialog.findChildren(QLabel)\n                     if w.objectName() != "muted_text" and not w.styleSheet()]\n            assert plain, f"{name}: no plain label left to compare against"\n            assert all(_ink(w) == palette["text_color"].lower() for w in plain), (name, mode)\n    finally:\n        settings.deleteLater()\n        batch.deleteLater()\n\n\ndef test_no_label_is_written_in_a_css_grey():\n    """The literal the ruling retired, anywhere the application EVALUATES a\n    string. Docstrings and comments may still name it; code may not."""\n    import ast\n    css_grey = re.compile(r"color\\s*:\\s*(gray|grey)\\b", re.I)\n    found, files = [], 0\n    for path in sorted(ROOT.rglob("*.py")):\n        rel = path.relative_to(ROOT)\n        if any(p in {"tests", "snapshots", ".git", "__pycache__", "build", "dist", ".venv"}\n               for p in rel.parts):\n            continue\n        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):\n            continue\n        text = path.read_text(encoding="utf-8-sig", errors="replace")\n        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:\n            continue\n        files += 1\n        tree = ast.parse(text)\n        docs = {id(st.value) for node in ast.walk(tree)\n                for st in (node.body if isinstance(getattr(node, "body", None), list) else [])\n                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant)}\n        found += [f"{rel}:{node.lineno}" for node in ast.walk(tree)\n                  if isinstance(node, ast.Constant) and isinstance(node.value, str)\n                  and id(node) not in docs and css_grey.search(node.value)]\n    assert files >= 20, f"only {files} files swept -- the walk has gone blind"\n    assert not found, "CSS grey still written as a colour:\\n  " + "\\n  ".join(found)\n')


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
    def css_greys(src):
        tree = ast.parse(src)
        docs = {id(st.value) for node in ast.walk(tree)
                for st in (node.body if isinstance(getattr(node, "body", None), list) else [])
                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant)}
        pat = re.compile(r"color\s*:\s*(gray|grey)\b", re.I)
        return [n.lineno for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and id(n) not in docs and pat.search(n.value)]

    # the two dialogs: labels named, colour gone from their own sheets, one
    # rule each, and nothing else moved
    rules = {
        "ui/settings_dialog.py": (
            "            /* ---- Muted text: notes, previews, the empty history ----\n"
            "               RNV-MUTED-DESCRIPTIONS, ruling 1 of 2026-09-27 */\n"
            "            QLabel#muted_text {{\n"
            "                color: {text_secondary};\n"
            "            }}\n", 5),
        "ui/batch_export_dialog.py": (
            "            /* RNV-MUTED-DESCRIPTIONS, ruling 1: the filename preview */\n"
            "            QLabel#muted_text {{ color: {theme[\"text_secondary\"]}; }}\n", 1),
    }
    for rel, (rule, labels) in rules.items():
        old, new = _original(tree, rel), tree.read(rel)
        assert css_greys(old) and not css_greys(new), (rel, css_greys(new))
        assert new.count(rule) == 1, f"{rel}: the muted rule is not in its stylesheet"
        assert new.count('.setObjectName("muted_text")') == labels, rel
        named = [l for l in new.splitlines() if l.strip().endswith('.setObjectName("muted_text")')]
        back = "\n".join(l for l in new.replace(rule, "").splitlines() if l not in named)
        prior = old.replace("color: grey; ", "")
        assert back == prior.rstrip("\n") or back + "\n" == prior, f"{rel} moved beyond the colour"

    # the palettes: the values stand; only the notes beside text_secondary change
    old_c, new_c = _original(tree, "ui/colors.py"), tree.read("ui/colors.py")
    assert _top(old_c) == _top(new_c), "a palette value moved"
    assert new_c.count("NOT CONSUMED") == old_c.count("NOT CONSUMED") - 3

    for rel in ("tests/test_muted_and_disabled_text.py", "tests/test_app_mirror.py"):
        ast.parse(tree.read(rel))
    guard = tree.read("tests/test_muted_and_disabled_text.py")
    assert SENTINEL in guard and "def test_the_muted_labels_draw_in_text_secondary" in guard
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
