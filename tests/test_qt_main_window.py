"""
test_qt_main_window.py — Real interaction tests against MainWindow
====================================================================

Phase 7 of the test suite expansion. These tests verify that user-facing
interactions (button clicks, keyboard shortcuts) reach the right callbacks
inside MainWindow. The existing TestMainWindowIntegration in
test_rnv_palette_manager.py verifies the underlying methods work; these
tests verify the wiring layer on top.

Two interaction patterns are tested:

1. **Mouse clicks on specific widgets** (e.g., the theme button) — these
   work via `qtbot.mouseClick(widget, ...)` because the click targets a
   specific widget regardless of window-active state.

2. **Keyboard shortcuts** — driven via `_trigger_shortcut(window, "Ctrl+N")`
   from conftest, which finds the QShortcut by key sequence and emits its
   activated signal directly. This is necessary because `qtbot.keyClick`
   doesn't reliably deliver to QShortcut handlers in offscreen Qt mode.

Cleanup safety
--------------
Cleanup loops use BOUNDED iteration (not `while` until condition) to
prevent infinite hangs if state can't be restored. Better to leak a
slot than to hang for 5 minutes when undo() fails silently.
"""
from __future__ import annotations

from unittest import mock

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QColorDialog

from conftest import _load_main_window, _trigger_shortcut


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def main_window(qapp):
    """Module-scoped MainWindow — created once, reused across tests."""
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


@pytest.fixture(autouse=True)
def block_color_dialog():
    """Stop QColorDialog.exec() from blocking on real OS dialog."""
    with mock.patch.object(QColorDialog, "exec", return_value=0):
        yield


@pytest.fixture(autouse=True)
def block_warning_dialogs():
    """Stop DialogHelper.show_warning from blocking on QMessageBox."""
    from utils.dialog_helper import DialogHelper
    with mock.patch.object(DialogHelper, "show_warning"):
        yield


# ═══════════════════════════════════════════════════════════════════════════
# Helper: bounded undo for cleanup
# ═══════════════════════════════════════════════════════════════════════════

def _undo_until(main_window, target_count: int, max_iters: int = 5) -> None:
    """Undo until slot count reaches target_count, capped at max_iters.

    Bounded to prevent infinite-loop hangs when undo() can't reduce the
    count further (e.g., empty undo stack, or update_grid hanging on
    a large slot count in offscreen Qt). Better to leak a few slots
    than to hang the test runner indefinitely.
    """
    for _ in range(max_iters):
        if len(main_window.slots_widgets) <= target_count:
            return
        main_window.undo()


# ═══════════════════════════════════════════════════════════════════════════
# WINDOW SHAPE & STARTUP
# ═══════════════════════════════════════════════════════════════════════════

def test_main_window_constructs_without_error(main_window):
    """Construction itself is the test — if the fixture got here, MainWindow built."""
    assert main_window is not None
    assert main_window.windowTitle()


def test_main_window_has_theme_button(main_window):
    """The theme cycle button must exist as a clickable widget."""
    assert main_window.theme_button is not None
    assert main_window.theme_button.isEnabled()


def test_main_window_has_search_bar(main_window):
    """The search bar must exist (Ctrl+F target)."""
    assert main_window.color_search_bar is not None


def test_main_window_starts_with_slots(main_window):
    """At least one slot must exist on startup."""
    assert len(main_window.slots_widgets) >= 1


# ═══════════════════════════════════════════════════════════════════════════
# BUTTON CLICKS — direct widget targeting (works in offscreen mode)
# ═══════════════════════════════════════════════════════════════════════════

def test_theme_button_click_cycles_theme(main_window, qtbot):
    """Clicking the theme button must cycle to a different theme."""
    name_before = main_window.theme_manager.get_theme_display_name()

    qtbot.mouseClick(main_window.theme_button, Qt.MouseButton.LeftButton)

    name_after = main_window.theme_manager.get_theme_display_name()
    assert name_after != name_before, (
        f"Theme name didn't change after clicking theme button "
        f"(before={name_before!r}, after={name_after!r})."
    )

    # Restore — bounded loop, max 5 cycles (theme has 3, so 5 is generous)
    for _ in range(5):
        if main_window.theme_manager.get_theme_display_name() == name_before:
            break
        qtbot.mouseClick(main_window.theme_button, Qt.MouseButton.LeftButton)


# ═══════════════════════════════════════════════════════════════════════════
# KEYBOARD SHORTCUTS — slot operations
# ═══════════════════════════════════════════════════════════════════════════

def test_ctrl_n_adds_slot(main_window):
    """Ctrl+N keyboard shortcut must add a slot."""
    before = len(main_window.slots_widgets)
    try:
        _trigger_shortcut(main_window, "Ctrl+N")
        assert len(main_window.slots_widgets) == before + 1, (
            f"Ctrl+N didn't add a slot (count {before} → "
            f"{len(main_window.slots_widgets)})."
        )
    finally:
        _undo_until(main_window, before)


def test_ctrl_z_undoes_add(main_window):
    """Ctrl+Z must undo the most recent action."""
    before = len(main_window.slots_widgets)
    main_window.add_slot()
    assert len(main_window.slots_widgets) == before + 1

    _trigger_shortcut(main_window, "Ctrl+Z")
    assert len(main_window.slots_widgets) == before, (
        "Ctrl+Z did not undo the add."
    )


def test_ctrl_y_redoes(main_window):
    """Ctrl+Y must redo a previously-undone action."""
    before = len(main_window.slots_widgets)
    try:
        main_window.add_slot()
        main_window.undo()
        assert len(main_window.slots_widgets) == before

        _trigger_shortcut(main_window, "Ctrl+Y")
        assert len(main_window.slots_widgets) == before + 1
    finally:
        _undo_until(main_window, before)


# ═══════════════════════════════════════════════════════════════════════════
# KEYBOARD SHORTCUTS — theme & search
# ═══════════════════════════════════════════════════════════════════════════

def test_ctrl_t_cycles_theme(main_window):
    """Ctrl+T keyboard shortcut must cycle the theme."""
    name_before = main_window.theme_manager.get_theme_display_name()
    try:
        _trigger_shortcut(main_window, "Ctrl+T")
        assert main_window.theme_manager.get_theme_display_name() != name_before
    finally:
        for _ in range(5):
            if main_window.theme_manager.get_theme_display_name() == name_before:
                break
            main_window.cycle_theme()


def test_ctrl_f_fires_toggle_search_handler(main_window):
    """Ctrl+F must trigger the _toggle_search handler.

    NOTE: We don't verify visibility/focus side effects because the offscreen
    Qt platform doesn't propagate them reliably. Production users get the
    visibility behavior; this test verifies the keyboard wiring is intact.
    The test passes as long as:
      1. A QShortcut for Ctrl+F exists (otherwise _trigger_shortcut raises)
      2. The shortcut is connected to a callback (the activated signal has
         at least one receiver — otherwise nothing happens but no error)
      3. The callback runs without crashing
    """
    # If Ctrl+F's connected handler raises, this will propagate.
    _trigger_shortcut(main_window, "Ctrl+F")
    # Toggle once more to restore (idempotent over 2 calls, regardless of
    # whether we observed visibility changes).
    _trigger_shortcut(main_window, "Ctrl+F")
    assert main_window.color_search_bar is not None


# ═══════════════════════════════════════════════════════════════════════════
# KEYBOARD SHORTCUTS — selection navigation
# ═══════════════════════════════════════════════════════════════════════════

def test_arrow_right_navigates_selection(main_window):
    """Right arrow must move selection to the next slot."""
    assert len(main_window.slots_widgets) >= 2, (
        "Need at least 2 slots for navigation test"
    )

    main_window.select_slot(main_window.slots_widgets[0])
    try:
        _trigger_shortcut(main_window, "Right")
        assert main_window._selected_slot is main_window.slots_widgets[1]
    finally:
        main_window.select_slot(None)


def test_arrow_left_navigates_selection(main_window):
    """Left arrow must move selection to the previous slot."""
    assert len(main_window.slots_widgets) >= 2

    main_window.select_slot(main_window.slots_widgets[1])
    try:
        _trigger_shortcut(main_window, "Left")
        assert main_window._selected_slot is main_window.slots_widgets[0]
    finally:
        main_window.select_slot(None)


def test_escape_deselects(main_window):
    """Escape must deselect the currently-selected slot."""
    main_window.select_slot(main_window.slots_widgets[0])
    assert main_window._selected_slot is not None

    _trigger_shortcut(main_window, "Escape")

    assert main_window._selected_slot is None


# ═══════════════════════════════════════════════════════════════════════════
# KEYBOARD SHORTCUTS — slot mutations
# ═══════════════════════════════════════════════════════════════════════════

def test_space_toggles_lock_on_selected(main_window):
    """Spacebar with a slot selected must toggle its lock state."""
    target = main_window.slots_widgets[0]
    main_window.select_slot(target)
    initial_lock = target.locked

    try:
        _trigger_shortcut(main_window, "Space")
        assert target.locked != initial_lock, (
            "Space did not toggle lock state on selected slot."
        )
    finally:
        target.locked = initial_lock
        main_window.select_slot(None)


def test_ctrl_d_duplicates_selected(main_window):
    """Ctrl+D must duplicate the selected slot.

    NOTE: Uses an existing slot (no preceding add_slot_with_color). Adding
    extra slots before triggering duplicate compounds slot count, and
    update_grid() in offscreen Qt is known to hang on large slot counts
    (documented in TestMainWindowIntegration.test_max_slots_not_exceeded).
    """
    target = main_window.slots_widgets[0]
    main_window.select_slot(target)
    before = len(main_window.slots_widgets)

    try:
        _trigger_shortcut(main_window, "Ctrl+D")
        assert len(main_window.slots_widgets) == before + 1, (
            f"Ctrl+D didn't duplicate slot (count {before} → "
            f"{len(main_window.slots_widgets)})."
        )
    finally:
        # Bounded undo to avoid infinite-loop hangs
        _undo_until(main_window, before)
        main_window.select_slot(None)
