"""
test_qt_export_default_format.py — Settings → Export → Default Export Format
============================================================================

The Export Palette dialog opens with the Default Export Format already
chosen as its file type. Before this, the dialog always opened on the first
filter (Adobe Swatch Exchange) whatever the setting said.
"""
from __future__ import annotations

from unittest import mock

import pytest
from PyQt6.QtWidgets import QFileDialog

from conftest import _load_main_window


@pytest.fixture(scope="module")
def main_window(qapp):
    """Module-scoped MainWindow with session restore switched off."""
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
    yield win


@pytest.mark.parametrize("ext, expected", [
    (".gpl", "GIMP Palette (*.gpl)"),
    (".swatches", "Procreate Swatches (*.swatches)"),
    (".TXT", "Plain Text (*.txt)"),
])
def test_export_dialog_preselects_the_default_format(main_window, ext, expected):
    settings = main_window.settings_manager
    saved = settings.last_export_format
    settings.last_export_format = ext
    try:
        with mock.patch.object(
            QFileDialog, "getSaveFileName", return_value=("", "")
        ) as dialog:
            main_window.export_palette()
    finally:
        settings.last_export_format = saved
    args = dialog.call_args.args
    filters = args[3].split(";;")
    assert args[4] == expected
    assert args[4] in filters


def test_export_dialog_unknown_default_falls_back_to_the_first_filter(main_window):
    settings = main_window.settings_manager
    saved = settings.last_export_format
    settings.last_export_format = ".pal"
    try:
        with mock.patch.object(
            QFileDialog, "getSaveFileName", return_value=("", "")
        ) as dialog:
            main_window.export_palette()
    finally:
        settings.last_export_format = saved
    assert dialog.call_args.args[4] == ""
