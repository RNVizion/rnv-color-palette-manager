"""
test_qt_color_slot.py — Real mouse interaction tests against ColorSlot
========================================================================

ColorSlotWidget defines no Qt signals — interactions flow as direct
callbacks to MainWindow (e.g. `_on_slot_click` → `main_window.select_slot()`
or `change_color()`). These tests drive REAL mouse events through the
slot widgets and verify the callback chain reaches MainWindow correctly.

The existing TestMainWindowIntegration tests verify select_slot() and
change_color() in isolation. These tests verify the click → callback
wiring on top.

Single-click vs double-click semantics
---------------------------------------
The slot's behavior on left-click depends on settings_manager.single_click_edit:
  - single_click_edit=True:  left-click opens color picker
  - single_click_edit=False: left-click selects slot, double-click opens picker

We force single_click_edit=False for tests that want to verify selection,
and force True for tests that verify color editing flow.

Run
---
    pytest tests/test_qt_color_slot.py
    pytest tests/test_qt_color_slot.py -v
"""
from __future__ import annotations

from unittest import mock

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QColorDialog

from conftest import _load_main_window


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def main_window(qapp):
    """Module-scoped MainWindow — same setup pattern as test_qt_main_window."""
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
def select_mode(main_window):
    """Force single_click_edit=False so left-click selects (not edits)."""
    sm = main_window.settings_manager
    original = sm.single_click_edit
    sm.single_click_edit = False
    yield
    sm.single_click_edit = original


@pytest.fixture
def edit_mode(main_window):
    """Force single_click_edit=True so left-click opens picker."""
    sm = main_window.settings_manager
    original = sm.single_click_edit
    sm.single_click_edit = True
    yield
    sm.single_click_edit = original


@pytest.fixture
def fresh_slot(main_window):
    """Add a slot for the test, restore by undoing afterward."""
    main_window.select_slot(None)
    main_window.add_slot_with_color(QColor(100, 150, 200))
    widget = main_window.slots_widgets[-1]
    yield widget
    main_window.select_slot(None)
    main_window.undo()


# ═══════════════════════════════════════════════════════════════════════════
# CLICK → SELECTION PATH (single_click_edit=False)
# ═══════════════════════════════════════════════════════════════════════════

def test_left_click_selects_slot_in_select_mode(main_window, fresh_slot, qtbot, select_mode):
    """Left-click on a slot must select it when single_click_edit is False."""
    assert main_window._selected_slot is not fresh_slot

    qtbot.mouseClick(fresh_slot.slot, Qt.MouseButton.LeftButton)

    assert main_window._selected_slot is fresh_slot, (
        f"Left-click did not select slot. "
        f"_selected_slot={main_window._selected_slot}, expected={fresh_slot}"
    )


def test_left_click_different_slots_changes_selection(main_window, qtbot, select_mode):
    """Clicking a different slot must move selection."""
    while len(main_window.slots_widgets) < 2:
        main_window.add_slot()

    slot_a = main_window.slots_widgets[0]
    slot_b = main_window.slots_widgets[1]
    try:
        qtbot.mouseClick(slot_a.slot, Qt.MouseButton.LeftButton)
        assert main_window._selected_slot is slot_a

        qtbot.mouseClick(slot_b.slot, Qt.MouseButton.LeftButton)
        assert main_window._selected_slot is slot_b

        assert not slot_a.slot._selected
    finally:
        main_window.select_slot(None)


# ═══════════════════════════════════════════════════════════════════════════
# CLICK → COLOR DIALOG PATH (single_click_edit=True)
# ═══════════════════════════════════════════════════════════════════════════

def test_left_click_opens_picker_in_edit_mode(main_window, fresh_slot, qtbot, edit_mode):
    """Left-click in edit mode must invoke QColorDialog.exec()."""
    with mock.patch.object(QColorDialog, "exec", return_value=0) as mock_exec:
        qtbot.mouseClick(fresh_slot.slot, Qt.MouseButton.LeftButton)
        assert mock_exec.called


def test_color_dialog_accept_changes_slot_color(main_window, fresh_slot, qtbot, edit_mode):
    """When the picker returns a color, the slot's color must update."""
    new_color = QColor(50, 60, 70)

    with (
        mock.patch.object(QColorDialog, "exec", return_value=1),
        mock.patch.object(QColorDialog, "selectedColor", return_value=new_color),
    ):
        qtbot.mouseClick(fresh_slot.slot, Qt.MouseButton.LeftButton)

    assert fresh_slot.slot.color.red() == 50
    assert fresh_slot.slot.color.green() == 60
    assert fresh_slot.slot.color.blue() == 70


def test_color_dialog_reject_leaves_slot_unchanged(main_window, fresh_slot, qtbot, edit_mode):
    """When the picker is cancelled, the slot's color must remain unchanged."""
    original = QColor(fresh_slot.slot.color)

    with mock.patch.object(QColorDialog, "exec", return_value=0):
        qtbot.mouseClick(fresh_slot.slot, Qt.MouseButton.LeftButton)

    assert fresh_slot.slot.color.red() == original.red()
    assert fresh_slot.slot.color.green() == original.green()
    assert fresh_slot.slot.color.blue() == original.blue()


def test_locked_slot_blocks_color_change(main_window, fresh_slot, qtbot, edit_mode):
    """Clicking a locked slot must NOT open the color picker."""
    fresh_slot.locked = True

    with mock.patch.object(QColorDialog, "exec", return_value=1) as mock_exec:
        qtbot.mouseClick(fresh_slot.slot, Qt.MouseButton.LeftButton)

    assert not mock_exec.called


# ═══════════════════════════════════════════════════════════════════════════
# DOUBLE-CLICK
# ═══════════════════════════════════════════════════════════════════════════

def test_double_click_opens_picker_in_select_mode(main_window, fresh_slot, qtbot, select_mode):
    """Double-click must open the color picker even in select mode."""
    with mock.patch.object(QColorDialog, "exec", return_value=0) as mock_exec:
        qtbot.mouseDClick(fresh_slot.slot, Qt.MouseButton.LeftButton)
        assert mock_exec.called


# ═══════════════════════════════════════════════════════════════════════════
# RIGHT-CLICK CONTEXT MENU
# ═══════════════════════════════════════════════════════════════════════════

def test_right_click_invokes_context_menu(main_window, fresh_slot, qtbot):
    """Right-click on a slot must invoke _show_context_menu."""
    with mock.patch.object(
        type(fresh_slot), "_show_context_menu"
    ) as mock_menu:
        qtbot.mouseClick(fresh_slot.slot, Qt.MouseButton.RightButton)
        assert mock_menu.called
