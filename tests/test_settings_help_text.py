"""
test_settings_help_text.py — Settings tooltips say what the app does
====================================================================

Two Appearance tooltips were wrong: the border tooltip called *thin* the
default (the default is *none*), and the size overlay's tooltip put it in
the top-left corner (it is drawn at the top right, beside the gear).
"""
from __future__ import annotations

from unittest import mock

import pytest

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


@pytest.fixture
def dialog(qapp):
    from ui.settings_dialog import SettingsDialog
    from utils.settings_manager import SettingsManager
    dlg = SettingsDialog(settings=SettingsManager())
    yield dlg
    dlg.deleteLater()


def test_border_tooltip_names_the_real_default(dialog):
    from utils.settings_manager import Defaults
    lines = dialog.combo_border_style.toolTip().splitlines()
    marked = [line for line in lines if "(default)" in line]
    assert len(marked) == 1, lines
    assert marked[0].startswith(f"{Defaults.SLOT_BORDER_STYLE}:"), marked


def test_size_overlay_tooltip_names_the_corner_it_is_drawn_in(dialog, main_window):
    win = main_window
    win.resize(1280, 800)
    win._update_overlay_positions()
    overlay = win.size_overlay.geometry()
    assert overlay.center().x() > win.width() // 2
    assert overlay.center().y() < win.height() // 2
    tip = dialog.chk_show_overlay.toolTip()
    assert "top-right corner" in tip, tip
    assert "top-left" not in tip, tip
