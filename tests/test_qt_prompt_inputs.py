"""
test_qt_prompt_inputs.py — the prompts' input fields follow the theme
=====================================================================

Generate Gradient To... asks for a number (a spin box), Mix With... for an
algorithm (a combo box) and Add New Group for a name (a line edit), each in
a QInputDialog. The app's stylesheet styled only the prompts' buttons, so
the input field kept the system's white in dark and image modes. It now
takes the theme's input surface, the key the settings dialog's inputs use.

Each field is drawn and its ground read back, in all three modes.
"""
from __future__ import annotations

from unittest import mock

import pytest
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QComboBox, QInputDialog, QLineEdit, QSpinBox

from conftest import _load_main_window
from ui.theme_manager import ThemeManager

THEMES = {
    "dark": ThemeManager.DARK_THEME,
    "light": ThemeManager.LIGHT_THEME,
    "image": ThemeManager.IMAGE_THEME,
}


@pytest.fixture(scope="module")
def main_window(qapp):
    from utils.session_manager import SessionManager
    from utils.settings_manager import SettingsManager

    MainWindow = _load_main_window()
    with (
        mock.patch.object(SessionManager, "has_recovery", return_value=False),
        mock.patch.object(SessionManager, "has_saved_session", return_value=False),
        mock.patch.object(
            SettingsManager,
            "auto_restore_session",
            new_callable=lambda: property(lambda self: False),
        ),
    ):
        win = MainWindow()
    win.closeEvent = lambda event: event.accept()
    try:
        win.session_manager.stop_auto_save()
    except Exception:
        pass
    start = win.theme_manager.current_theme
    yield win
    for _ in range(3):
        if win.theme_manager.current_theme == start:
            break
        win.cycle_theme()


def _set_theme(win, name: str) -> None:
    for _ in range(3):
        if win.theme_manager.current_theme == name:
            break
        win.cycle_theme()
    if win.theme_manager.current_theme != name:
        pytest.skip(f"{name} mode is not available here")


def _prompt(win, kind: str) -> QInputDialog:
    """The prompt each slot action opens, built the way QInputDialog's
    static helpers build it."""
    dlg = QInputDialog(win)
    if kind == "gradient":
        dlg.setInputMode(QInputDialog.InputMode.IntInput)
        dlg.setLabelText("Number of colors (including start and end):")
        dlg.setIntRange(3, 20)
        dlg.setIntValue(5)
    elif kind == "mix":
        dlg.setLabelText("Mix the two colors in equal parts with:")
        dlg.setComboBoxItems(["RGB Weighted", "Subtractive CMY"])
        dlg.setComboBoxEditable(False)
    else:
        dlg.setInputMode(QInputDialog.InputMode.TextInput)
        dlg.setLabelText("Group name:")
    dlg.resize(420, dlg.sizeHint().height())
    return dlg


FIELD = {"gradient": QSpinBox, "mix": QComboBox, "group": QLineEdit}


@pytest.mark.parametrize("theme", list(THEMES))
@pytest.mark.parametrize("kind", list(FIELD))
def test_prompt_input_field_takes_the_theme_input_surface(main_window, qapp, theme, kind):
    win = main_window
    _set_theme(win, theme)
    dlg = _prompt(win, kind)
    dlg.show()
    qapp.processEvents()
    try:
        field = dlg.findChild(FIELD[kind])
        assert field is not None and field.isVisible()
        image = field.grab().toImage()
        # A point of the field's ground, clear of its text, its frame and
        # its arrows: two thirds of the way across, half way down
        ground = image.pixelColor(image.width() * 2 // 3, image.height() // 2)
        want = QColor(THEMES[theme]["input_bg"])
        assert ground.name() == want.name(), (
            f"{kind} field in {theme} mode is {ground.name()}, "
            f"not the input surface {want.name()}"
        )
    finally:
        dlg.close()
        dlg.deleteLater()
