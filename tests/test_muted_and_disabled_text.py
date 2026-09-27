"""
Muted and disabled text: aligned to the ecosystem, and honest about which of
them anything actually paints.

`text_disabled` is live -- the batch export dialog and the menu bar both read
it. It is now #555555 dark / #aaaaaa light, matching the other four apps. Both
sit below every contrast floor and are meant to: WCAG 1.4.3 exempts text in an
inactive component, and disabled text that reads as clearly as enabled text is
not doing its job.

`text_secondary` is live since 2026-09-27 (RNV-MUTED-DESCRIPTIONS, ruling 1 of
the colour chart). Until then nothing painted it: the settings dialog read it
into a local it never used, and six labels in two dialogs wrote `color: grey`
instead -- #808080 in every mode. They are named "muted_text" now and each
dialog's stylesheet draws that name in text_secondary: #888888 in dark and
image, #666666 in light, the muted text all five applications paint. The
tests below hold the wiring, the values, and the colour each label ends up
drawn in.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from ui.colors import (DARK_THEME_COLORS, IMAGE_MODE_COLORS,
                       LIGHT_THEME_COLORS)

THEMES = {
    "DARK": DARK_THEME_COLORS,
    "LIGHT": LIGHT_THEME_COLORS,
    "IMAGE": IMAGE_MODE_COLORS,
}
ROOT = pathlib.Path(__file__).resolve().parent.parent
COLORS_PY = ROOT / "ui" / "colors.py"

# The two dialogs that paint the key, and the only files that read it.
PAINTED_IN = ["ui/batch_export_dialog.py", "ui/settings_dialog.py"]


def _luminance(value: str) -> float:
    h = value.lstrip("#")
    if len(h) == 8:                      # Qt #AARRGGBB
        h = h[2:]
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def _contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def test_all_three_palettes_carry_both_keys():
    """Guard the guard: every test below iterates THEMES."""
    assert set(THEMES) == {"DARK", "LIGHT", "IMAGE"}
    for name, theme in THEMES.items():
        for key in ("text_color", "text_secondary", "text_disabled"):
            assert key in theme, f"{name} has no {key}"


@pytest.mark.parametrize("name", sorted(THEMES))
def test_the_text_hierarchy_dims_in_order(name):
    """primary reads strongest, muted next, disabled faintest.

    Held as an ORDER rather than as three values, so a later retune of the ramp
    moves them together and this still passes.
    """
    theme = THEMES[name]
    ground = theme["card_bg"]            # a flat colour in all three palettes
    primary = _contrast(theme["text_color"], ground)
    muted = _contrast(theme["text_secondary"], ground)
    disabled = _contrast(theme["text_disabled"], ground)
    assert primary > muted > disabled, (
        f"{name}: primary {primary:.2f} / muted {muted:.2f} / "
        f"disabled {disabled:.2f} are not in descending order")


@pytest.mark.parametrize("name", sorted(THEMES))
def test_disabled_text_stays_visibly_disabled(name):
    """It is meant to fail the text floor. A disabled label that reads as
    clearly as an enabled one is not communicating anything."""
    theme = THEMES[name]
    ratio = _contrast(theme["text_disabled"], theme["card_bg"])
    assert ratio < 4.5, (
        f"{name}: disabled text reads {ratio:.2f}:1 -- at that strength it no "
        f"longer looks disabled")


def _references(key: str) -> list[str]:
    sites = []
    for path in ROOT.rglob("*.py"):
        parts = path.parts
        if any(p in parts for p in (".git", "__pycache__", "tests", "snapshots")):
            continue
        if path.name.startswith("test_") or path == COLORS_PY:
            continue
        # A delivery script sitting at the root mentions the key it moves.
        # Sweeping it makes the guard fail on the very run that installs it --
        # the same trap the repos' placement guards already exempt `up*.py` for.
        if path.parent == ROOT and path.name.startswith("up"):
            continue
        if key in path.read_text(encoding="utf-8", errors="replace"):
            sites.append(path.relative_to(ROOT).as_posix())
    return sorted(sites)


def test_the_sweep_is_actually_reading_something():
    """A walk that finds nothing passes forever."""
    assert _references("text_disabled"), (
        "the sweep cannot find text_disabled, which IS painted -- it would not "
        "find text_secondary either")


def test_the_muted_key_is_read_where_it_is_painted():
    """Both directions. Read in exactly the two dialogs that paint it, and no
    note beside the values still says nothing paints it -- a note like that is
    how a value gets trusted, or distrusted, for the wrong reason."""
    sites = _references("text_secondary")
    assert sites == PAINTED_IN, (
        f"text_secondary is referenced in {sites}; the dialogs that paint it "
        f"are {PAINTED_IN}. A new reader needs its ground measured.")

    # Counted BESIDE the key rather than across the whole file: the tab block
    # carries NOT CONSUMED notes of its own, and they are not about this key.
    lines = COLORS_PY.read_text(encoding="utf-8").splitlines()
    beside = [i + 1 for i, line in enumerate(lines)
              if line.strip().startswith("'text_secondary':")]
    assert len(beside) == 3, f"expected text_secondary in three palettes, found {beside}"
    stale = [n for n in beside
             if re.search(r"#\s*NOT CONSUMED", "\n".join(lines[max(0, n - 7):n - 1]))]
    assert not stale, f"a NOT CONSUMED note still stands beside text_secondary at {stale}"


def test_the_settings_local_is_now_used():
    """ui/settings_dialog.py assigned the key to a local and never used it,
    which is why a grep for `text_secondary` looked live when it was not. The
    muted-text rule in the dialog's stylesheet is the use."""
    source = (ROOT / "ui" / "settings_dialog.py").read_text(encoding="utf-8")
    # The lookarounds are load-bearing: `\b` happily matches the identifier
    # INSIDE the string key of `theme.get('text_secondary', ...)`, which is the
    # dict lookup and not a use of the local.
    bare = re.compile(r"(?<!['\"])\btext_secondary\b(?!['\"])")
    assigns, uses = [], []
    for i, line in enumerate(source.splitlines(), 1):
        for match in bare.finditer(line):
            after = line[match.end():].lstrip()
            (assigns if after.startswith("=") and not after.startswith("==")
             else uses).append(f"{i}: {line.strip()[:60]}")
    assert len(assigns) == 1, f"expected one assignment, found {assigns}"
    assert uses, "the text_secondary local is assigned and never used"


# RNV-MUTED-DESCRIPTIONS
# ------------------------------------------ the muted labels, drawn (ruling 1)

def test_the_muted_values_are_the_ones_the_fleet_already_uses():
    """Ruling 1 was conditional: two values are fine if every app splits it by
    mode, and only with values already in use. Both halves, held here."""
    assert THEMES["DARK"]["text_secondary"] == THEMES["IMAGE"]["text_secondary"] == "#888888"
    assert THEMES["LIGHT"]["text_secondary"] == "#666666"


def _manager(mode: str):
    from ui.theme_manager import ThemeManager
    manager = ThemeManager()
    manager.current_theme = mode
    manager.image_mode_active = (mode == "image")
    return manager


def _ink(widget) -> str:
    from PyQt6.QtGui import QPalette
    widget.ensurePolished()
    return widget.palette().color(QPalette.ColorRole.WindowText).name()


@pytest.mark.parametrize("mode", ["dark", "light", "image"])
def test_the_muted_labels_draw_in_text_secondary(qapp, mode):
    """Built the way the app builds them, in each mode. Settings draws image
    mode from the dark palette, as its _apply_theme() chooses; batch export
    draws it from the image palette. Both hold #888888 there."""
    from PyQt6.QtWidgets import QLabel

    from ui.batch_export_dialog import BatchExportDialog
    from ui.settings_dialog import SettingsDialog
    from utils.settings_manager import SettingsManager

    manager = _manager(mode)
    settings = SettingsDialog(settings=SettingsManager(), theme_manager=manager)
    batch = BatchExportDialog(settings=SettingsManager(), theme_manager=manager)
    cases = [(settings, THEMES["DARK" if mode == "image" else mode.upper()],
              [settings.lbl_clipboard_preview, settings.lbl_created, settings.lbl_modified]),
             (batch, THEMES[mode.upper()], [batch._lbl_preview])]
    try:
        for dialog, palette, expected in cases:
            name = type(dialog).__name__
            muted = [w for w in dialog.findChildren(QLabel) if w.objectName() == "muted_text"]
            missing = [w.text() for w in expected if all(w is not m for m in muted)]
            assert not missing, (name, "not named muted_text", missing)
            for w in muted:
                assert "color" not in w.styleSheet(), (name, w.text(), w.styleSheet())
                assert _ink(w) == palette["text_secondary"].lower(), (
                    name, mode, w.text()[:40], _ink(w))
            # and the rule reaches nothing it should not
            plain = [w for w in dialog.findChildren(QLabel)
                     if w.objectName() != "muted_text" and not w.styleSheet()]
            assert plain, f"{name}: no plain label left to compare against"
            assert all(_ink(w) == palette["text_color"].lower() for w in plain), (name, mode)
    finally:
        settings.deleteLater()
        batch.deleteLater()


def test_no_label_is_written_in_a_css_grey():
    """The literal the ruling retired, anywhere the application EVALUATES a
    string. Docstrings and comments may still name it; code may not."""
    import ast
    css_grey = re.compile(r"color\s*:\s*(gray|grey)\b", re.I)
    found, files = [], 0
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if any(p in {"tests", "snapshots", ".git", "__pycache__", "build", "dist", ".venv"}
               for p in rel.parts):
            continue
        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
            continue
        files += 1
        tree = ast.parse(text)
        docs = {id(st.value) for node in ast.walk(tree)
                for st in (node.body if isinstance(getattr(node, "body", None), list) else [])
                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant)}
        found += [f"{rel}:{node.lineno}" for node in ast.walk(tree)
                  if isinstance(node, ast.Constant) and isinstance(node.value, str)
                  and id(node) not in docs and css_grey.search(node.value)]
    assert files >= 20, f"only {files} files swept -- the walk has gone blind"
    assert not found, "CSS grey still written as a colour:\n  " + "\n  ".join(found)
