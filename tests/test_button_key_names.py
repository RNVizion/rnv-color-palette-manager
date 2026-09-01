"""The button keys say where the button lives.

RNV-BUTTON-NAMING-GUARD

main_btn_* is the main window at launch. dialog_btn_* is anything that opens
later. Before this pass the main family here was called button_* -- the same
name that holds the GOLD DIALOG scheme in rnv-color-picker and
rnv-icon-builder. One name, two schemes, decided by which repository you had
open. These tests are what stop it drifting back.

This application's dialogs already had their own hover plate
(dialog_btn_hover_bg) and take their pressed state from accent. What they did
not have was a name for the plate and label they rest on -- they reached into
the main family for those. dialog_btn_bg and dialog_btn_text close that, with
the values those dialogs already painted.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OLD = ("button_bg", "button_text", "button_hover_bg", "button_hover_text",
       "button_pressed_bg", "button_pressed_text", "button_border_color")
NEW = tuple("main_" + n.replace("button_", "btn_") for n in OLD)
DIALOG = ("dialog_btn_bg", "dialog_btn_text", "dialog_btn_hover_bg")

PINNED_MAIN = {
    "dark": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",
             "main_btn_hover_bg": "#333333", "main_btn_hover_text": "#dddddd",
             "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#000000",
             "main_btn_border_color": "transparent"},
    "light": {"main_btn_bg": "#ffffff", "main_btn_text": "#000000",
              "main_btn_hover_bg": "#333333", "main_btn_hover_text": "#000000",
              "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#ffffff",
              "main_btn_border_color": "transparent"},
    "image": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",
              "main_btn_hover_bg": "#333333", "main_btn_hover_text": "#dddddd",
              "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#000000",
              "main_btn_border_color": "transparent"},
}

#: The dialog family holds exactly what those dialogs painted before the
#: rename. If one of these ever stops matching its main counterpart that is
#: fine -- it means a dialog scheme was ruled on. What must not happen is a
#: value moving during a rename.
PINNED_DIALOG = {
    "dark": {"dialog_btn_bg": "#1a1a1a", "dialog_btn_text": "#dddddd",
             "dialog_btn_hover_bg": "#3a3a3a"},
    "light": {"dialog_btn_bg": "#ffffff", "dialog_btn_text": "#000000",
              "dialog_btn_hover_bg": "#eeeeee"},
    "image": {"dialog_btn_bg": "#1a1a1a", "dialog_btn_text": "#dddddd",
              "dialog_btn_hover_bg": "#3a3a3a"},
}

SKIP = {".git", "build", "dist", ".venv", "__pycache__"}

#: A sweep for a name cannot tell a USE from a MENTION, and the two files
#: certain to mention the old names are this guard -- which lists them in order
#: to forbid them -- and the delivery script that performs the rename. Skipped
#: by marker rather than by filename: the script arrives under whatever name it
#: is saved as.
MARKERS = ("RNV-BUTTON-NAMING-GUARD", "RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP")

#: Dialogs, and the family each is allowed to read.
DIALOG_FILES = ("ui/about_dialog.py", "ui/batch_export_dialog.py",
                "utils/dialog_helper.py")


def _palettes():
    from ui.colors import (DARK_THEME_COLORS, LIGHT_THEME_COLORS,
                           IMAGE_MODE_COLORS)
    return {"dark": DARK_THEME_COLORS, "light": LIGHT_THEME_COLORS,
            "image": IMAGE_MODE_COLORS}


def _sources():
    for path in sorted(ROOT.rglob("*")):
        # Prose is not swept: docs are updated in one pass after alignment
        # settles, so they name the old keys until then, and failing on that
        # would be failing on a decision rather than on a defect.
        if path.is_dir() or path.suffix != ".py":
            continue
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(marker in text for marker in MARKERS):
            continue
        yield path, text


def test_no_old_button_key_name_survives():
    offenders = []
    for path, text in _sources():
        for old in OLD:
            if re.search(r"(['\"])" + old + r"\1", text):
                offenders.append(f"{path.relative_to(ROOT)}: {old}")
    assert not offenders, (
        "these are main-window button keys and must be named main_btn_*:\n  "
        + "\n  ".join(offenders))


def test_the_marker_exemption_covers_only_the_two_tools():
    marked = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(marker in text for marker in MARKERS):
            marked.append(path.relative_to(ROOT))
    assert len(marked) <= 2, f"unexpected marked file(s): {marked}"
    assert Path(__file__).relative_to(ROOT) in marked


def test_all_three_palettes_carry_both_families():
    for mode, palette in _palettes().items():
        missing = [n for n in NEW + DIALOG if n not in palette]
        assert not missing, f"{mode} palette missing {missing}"


def test_the_rename_moved_no_value():
    for mode, pins in PINNED_MAIN.items():
        palette = _palettes()[mode]
        actual = {k: palette.get(k) for k in pins}
        assert actual == pins, (
            f"the {mode} main button values changed.\n"
            f"  wanted {pins}\n  found  {actual}\n"
            "A rename that changes a value is not a rename.")


def test_the_dialog_family_holds_what_the_dialogs_already_painted():
    for mode, pins in PINNED_DIALOG.items():
        palette = _palettes()[mode]
        actual = {k: palette.get(k) for k in pins}
        assert actual == pins, (
            f"the {mode} dialog button values are not what those dialogs "
            f"painted before the rename.\n  wanted {pins}\n  found  {actual}")


def test_dialogs_read_the_dialog_family_and_not_the_main_one():
    for rel in DIALOG_FILES:
        src = (ROOT / rel).read_text(encoding="utf-8-sig")
        assert "dialog_btn_" in src, f"{rel} no longer reads the dialog family"
        assert not re.search(r"(['\"])main_btn_", src), (
            f"{rel} reads the main family. Dialogs open later and rest on the "
            f"dialog plate; wiring one to main_btn_* refuses the distinction "
            f"this rename exists to make.")


def test_the_settings_dialog_surface_fallback_is_still_a_surface_fallback():
    """One read of the main plate inside a dialog is deliberate and stays.

    ui/settings_dialog.py resolves an INPUT background through
    input_bg -> card_bg -> main_btn_bg. The last step is a surface fallback,
    not a button, and pointing it at dialog_btn_bg would be renaming by
    proximity. Asserted so it is not tidied away by the next reader.
    """
    src = (ROOT / "ui" / "settings_dialog.py").read_text(encoding="utf-8-sig")
    assert "theme.get('card_bg', theme['main_btn_bg'])" in src, (
        "the settings dialog's input-background fallback chain changed shape")
    assert "theme['dialog_btn_text']" in src, (
        "the settings dialog's button label should read the dialog family")


def test_the_two_schemes_are_still_different():
    """The dialog hover is a softer plate carrying gold; the main hover is the
    inverse scheme. They were separate before this pass and stay separate."""
    for mode, palette in _palettes().items():
        assert palette["dialog_btn_hover_bg"] != palette["main_btn_hover_bg"], (
            f"{mode}: the dialog hover plate and the main hover plate now hold "
            f"the same value ({palette['main_btn_hover_bg']}). Flattening the "
            f"two loses a scheme.")
