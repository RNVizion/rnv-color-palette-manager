"""
test_qt_search_and_workflows.py — Search bar interaction tests
================================================================

Phase 7. Real-keyboard-input tests against ColorSearchBar plus
end-to-end "type a color, get highlights" workflow tests against
MainWindow.

Why side-effect verification (not mock.patch) for handler tests
----------------------------------------------------------------
PyQt6 captures bound method objects at signal-connect time. Patching
`main_window._on_search_changed` AFTER __init__ already connected the
original bound method does not intercept the connection — the signal
still fires the original. To verify the handler ran, we observe its
side effects (e.g. `slot._search_highlight = True` for matching slots).

Cleanup safety
--------------
Cleanup loops are BOUNDED (max 5 iterations) so they can't hang the
test runner if undo() can't reduce slot count further.
"""
from __future__ import annotations

from unittest import mock

import pytest
from PyQt6.QtGui import QColor

from conftest import _load_main_window, _trigger_shortcut


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def main_window(qapp):
    """Module-scoped MainWindow."""
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


def _undo_until(main_window, target_count: int, max_iters: int = 5) -> None:
    """Bounded undo to prevent cleanup hangs. See test_qt_main_window."""
    for _ in range(max_iters):
        if len(main_window.slots_widgets) <= target_count:
            return
        main_window.undo()


# ═══════════════════════════════════════════════════════════════════════════
# SEARCH BAR — direct API tests (no main window)
# ═══════════════════════════════════════════════════════════════════════════

def test_search_bar_emits_search_changed_signal(qapp, qtbot):
    """Typing in the search bar must emit search_changed(text)."""
    from ui.color_search import ColorSearchBar

    bar = ColorSearchBar()
    qtbot.addWidget(bar)
    bar.show()
    qtbot.waitExposed(bar, timeout=1000)

    with qtbot.waitSignal(bar.search_changed, timeout=2000) as blocker:
        qtbot.keyClicks(bar._input, "red")

    assert blocker.args is not None
    assert "red" in blocker.args[0].lower()


def test_search_bar_close_emits_search_cleared(qapp, qtbot):
    """close_search() must emit search_cleared signal."""
    from ui.color_search import ColorSearchBar

    bar = ColorSearchBar()
    qtbot.addWidget(bar)
    bar.show()
    qtbot.waitExposed(bar, timeout=1000)

    with qtbot.waitSignal(bar.search_cleared, timeout=1000):
        bar.close_search()


def test_search_bar_current_text_reflects_input(qapp, qtbot):
    """The current_text property must mirror what's in the input field."""
    from ui.color_search import ColorSearchBar

    bar = ColorSearchBar()
    qtbot.addWidget(bar)

    bar._input.setText("test query")
    assert bar.current_text() == "test query"


def test_search_bar_set_match_count_does_not_crash(qapp, qtbot):
    """set_match_count(n, total) must not crash for various inputs."""
    from ui.color_search import ColorSearchBar

    bar = ColorSearchBar()
    qtbot.addWidget(bar)

    bar.set_match_count(0, 10)
    bar.set_match_count(5, 10)
    bar.set_match_count(10, 10)
    bar.set_match_count(0, 0)


# ═══════════════════════════════════════════════════════════════════════════
# SEARCH WORKFLOW — verify handlers ran via observable side effects
# ═══════════════════════════════════════════════════════════════════════════

def test_search_changed_propagates_and_highlights_matching_slot(main_window, qtbot):
    """Emitting search_changed should propagate to MainWindow's handler.

    Side effect verified: `_on_search_changed` sets `slot._search_highlight`
    to True for matching slots. Uses an existing slot rather than adding
    a new one to avoid offscreen-Qt's update_grid() hangs on large slot
    counts.
    """
    bar = main_window.color_search_bar

    # Use an existing slot — change its color to red rather than adding.
    target_slot = main_window.slots_widgets[0]
    original_color = QColor(target_slot.slot.color)
    target_slot.slot.color = QColor(255, 0, 0)  # red

    try:
        # Reset highlight state on the target slot.
        target_slot.slot._search_highlight = False
        target_slot.slot._search_dimmed = False

        # Trigger search via the real signal path.
        with qtbot.waitSignal(bar.search_changed, timeout=2000):
            bar._input.setText("red")
            bar._emit_search()

        # If MainWindow's _on_search_changed ran, the red slot should be
        # highlighted.
        assert target_slot.slot._search_highlight, (
            "Red slot was not highlighted after searching 'red'. "
            "search_changed → _on_search_changed connection appears broken."
        )
    finally:
        # Reset state on all slots and restore the target slot's color.
        for w in main_window.slots_widgets:
            w.slot._search_highlight = False
            w.slot._search_dimmed = False
        target_slot.slot.color = original_color
        bar._input.clear()


def test_search_cleared_propagates_and_clears_highlights(main_window, qtbot):
    """Emitting search_cleared should propagate to MainWindow's handler.

    Side effect verified: `_on_search_cleared` resets `slot._search_highlight`
    and `slot._search_dimmed` to False on every slot.
    """
    bar = main_window.color_search_bar

    # Manually set highlight state on a slot, simulating a previous search.
    target_slot = main_window.slots_widgets[0]
    target_slot.slot._search_highlight = True
    target_slot.slot._search_dimmed = True

    try:
        with qtbot.waitSignal(bar.search_cleared, timeout=1000):
            bar.close_search()

        assert not target_slot.slot._search_highlight, (
            "_search_highlight was not cleared by search_cleared. "
            "Connection to _on_search_cleared appears broken."
        )
        assert not target_slot.slot._search_dimmed
    finally:
        target_slot.slot._search_highlight = False
        target_slot.slot._search_dimmed = False


# ═══════════════════════════════════════════════════════════════════════════
# COLOR QUERY PARSING
# ═══════════════════════════════════════════════════════════════════════════

def test_parse_color_query_handles_hex(qapp):
    """parse_color_query should parse #RRGGBB format."""
    from ui.color_search import parse_color_query

    result = parse_color_query("#ff0000")
    assert result == (255, 0, 0)


def test_parse_color_query_handles_named_colors(qapp):
    """parse_color_query should resolve a named color to RGB."""
    from ui.color_search import parse_color_query

    result = parse_color_query("red")
    assert result is not None
    assert result[0] > result[1] and result[0] > result[2]


def test_parse_color_query_returns_none_on_garbage(qapp):
    """parse_color_query should return None for unparseable input."""
    from ui.color_search import parse_color_query

    assert parse_color_query("notacolor") is None
    assert parse_color_query("") is None


# ═══════════════════════════════════════════════════════════════════════════
# UNDO/REDO INTEGRATION via keyboard shortcuts
# ═══════════════════════════════════════════════════════════════════════════

def test_undo_redo_through_keyboard_workflow(main_window):
    """Full keyboard-driven workflow: add, undo, redo, all via shortcuts."""
    from utils.dialog_helper import DialogHelper

    with mock.patch.object(DialogHelper, "show_warning"):
        before = len(main_window.slots_widgets)
        try:
            _trigger_shortcut(main_window, "Ctrl+N")
            assert len(main_window.slots_widgets) == before + 1

            _trigger_shortcut(main_window, "Ctrl+Z")
            assert len(main_window.slots_widgets) == before

            _trigger_shortcut(main_window, "Ctrl+Shift+Z")
            assert len(main_window.slots_widgets) == before + 1
        finally:
            _undo_until(main_window, before)
