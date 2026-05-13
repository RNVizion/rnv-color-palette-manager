"""
test_qt_drag_drop.py — Drag-and-drop event handler tests for ColorSlotWidget
=============================================================================
VERSION_MARKER: drag_drop_v3_real_thememanager
=============================================================================

If you grep this file for "VERSION_MARKER" and don't find that string,
you have the OLD file — please replace with this one.

Phase 8c. Tests slot reorder drag-drop event handlers directly with mock
events. ColorSlotWidget(slot, preview_grid, main_window) construction
requires a fully-keyed theme dict (consumed by ImageButton.apply_style),
so we use a REAL ThemeManager() — it produces a complete theme dict
guaranteed to satisfy all consumers.
"""
from __future__ import annotations

from unittest import mock

import pytest
from PyQt6.QtCore import QByteArray, QMimeData
from PyQt6.QtGui import QColor

# The MIME format used internally by ColorSlotWidget for slot reorder
SLOT_INDEX_MIME = "application/x-rnv-slot-index"


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _make_drag_event(mime_format=SLOT_INDEX_MIME, payload="3"):
    """Build a mock event with the MIME data the handler expects."""
    mime = QMimeData()
    if mime_format is not None:
        mime.setData(mime_format, QByteArray(payload.encode()))
    event = mock.MagicMock()
    event.mimeData.return_value = mime
    return event


def _make_main_window_with_real_theme():
    """Build a main_window stub using a REAL ThemeManager.

    Critical detail: ImageButton.apply_style() (called during ColorSlotWidget
    construction) accesses theme['button_bg'], theme['button_text'],
    theme['border_color'], theme['button_hover_bg'] as required keys, plus
    several optional ones via .get(). Hand-rolling the dict is fragile —
    a real ThemeManager produces the full dict.
    """
    from ui.theme_manager import ThemeManager

    mw = mock.MagicMock()
    mw.theme_manager = ThemeManager()  # ← REAL, not a Mock
    mw.settings_manager = mock.MagicMock()
    mw.settings_manager.single_click_edit = False
    mw.slots_widgets = []
    mw.reorder_slot = mock.MagicMock()
    # CRITICAL: ColorSlotWidget construction schedules a deferred
    # _sync_scroll_content_height callback via QTimer.singleShot. That
    # callback reads main_window.scroll_content and main_window.zoom_view,
    # then does numeric comparison against minimumHeight(). With a plain
    # MagicMock, those would auto-create child mocks and the `<` comparison
    # would crash. Setting them to None triggers the safe early-return at
    # color_slot.py line 905 (`if scroll_content is None: return`).
    mw.scroll_content = None
    mw.zoom_view = None
    return mw


def _make_slot_widget(qtbot, color=QColor(100, 150, 200)):
    """Construct a single ColorSlotWidget. Returns (widget, main_window)."""
    from core.color_slot import ColorSlot, ColorSlotWidget

    main_window = _make_main_window_with_real_theme()
    slot = ColorSlot(
        color=color,
        base_size=100,
        theme_manager=main_window.theme_manager,
    )
    preview_grid = mock.MagicMock()

    widget = ColorSlotWidget(slot, preview_grid, main_window)
    qtbot.addWidget(widget)
    main_window.slots_widgets = [widget]
    return widget, main_window


# ═══════════════════════════════════════════════════════════════════════════
# dragEnterEvent
# ═══════════════════════════════════════════════════════════════════════════

def test_drag_enter_accepts_slot_reorder_mime(qtbot):
    """dragEnterEvent should accept events carrying our slot-index MIME type."""
    widget, _ = _make_slot_widget(qtbot)
    event = _make_drag_event(mime_format=SLOT_INDEX_MIME, payload="0")
    widget.dragEnterEvent(event)
    event.acceptProposedAction.assert_called_once()
    event.ignore.assert_not_called()


def test_drag_enter_ignores_unknown_mime(qtbot):
    """dragEnterEvent should ignore events with unrecognized MIME types."""
    widget, _ = _make_slot_widget(qtbot)
    event = _make_drag_event(mime_format="text/plain", payload="something")
    widget.dragEnterEvent(event)
    event.acceptProposedAction.assert_not_called()
    event.ignore.assert_called_once()


def test_drag_enter_ignores_event_with_no_mime_data(qtbot):
    """dragEnterEvent should ignore events with no recognized data."""
    widget, _ = _make_slot_widget(qtbot)
    event = mock.MagicMock()
    event.mimeData.return_value = QMimeData()  # empty
    widget.dragEnterEvent(event)
    event.acceptProposedAction.assert_not_called()
    event.ignore.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════
# dragMoveEvent
# ═══════════════════════════════════════════════════════════════════════════

def test_drag_move_accepts_slot_reorder_mime(qtbot):
    """dragMoveEvent should accept slot-index MIME (consistency with dragEnter)."""
    widget, _ = _make_slot_widget(qtbot)
    event = _make_drag_event(SLOT_INDEX_MIME, "0")
    widget.dragMoveEvent(event)
    event.acceptProposedAction.assert_called_once()


def test_drag_move_ignores_unknown_mime(qtbot):
    """dragMoveEvent should ignore unknown MIME types."""
    widget, _ = _make_slot_widget(qtbot)
    event = _make_drag_event(mime_format="application/json", payload="{}")
    widget.dragMoveEvent(event)
    event.acceptProposedAction.assert_not_called()
    event.ignore.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════
# dropEvent
# ═══════════════════════════════════════════════════════════════════════════

def test_drop_calls_reorder_with_correct_indices(qtbot):
    """A valid drop with source != target invokes reorder_slot(source, target)."""
    from core.color_slot import ColorSlot, ColorSlotWidget

    main_window = _make_main_window_with_real_theme()
    preview_grid = mock.MagicMock()

    other_slot = ColorSlot(color=QColor(0, 0, 0), base_size=100,
                           theme_manager=main_window.theme_manager)
    target_slot = ColorSlot(color=QColor(255, 255, 255), base_size=100,
                            theme_manager=main_window.theme_manager)

    other_widget = ColorSlotWidget(other_slot, preview_grid, main_window)
    target_widget = ColorSlotWidget(target_slot, preview_grid, main_window)
    qtbot.addWidget(other_widget)
    qtbot.addWidget(target_widget)
    main_window.slots_widgets = [other_widget, target_widget]  # target at index 1

    event = _make_drag_event(SLOT_INDEX_MIME, payload="0")
    target_widget.dropEvent(event)

    main_window.reorder_slot.assert_called_once_with(0, 1)
    event.acceptProposedAction.assert_called_once()


def test_drop_ignores_when_source_equals_target(qtbot):
    """Dropping a slot onto itself must not trigger a reorder."""
    widget, main_window = _make_slot_widget(qtbot)
    event = _make_drag_event(SLOT_INDEX_MIME, payload="0")
    widget.dropEvent(event)
    main_window.reorder_slot.assert_not_called()
    event.ignore.assert_called_once()


def test_drop_ignores_unknown_mime(qtbot):
    """A drop event without our MIME type must be ignored."""
    widget, main_window = _make_slot_widget(qtbot)
    event = _make_drag_event(mime_format="text/plain", payload="hello")
    widget.dropEvent(event)
    main_window.reorder_slot.assert_not_called()
    event.ignore.assert_called_once()


def test_drop_ignores_malformed_payload(qtbot):
    """Non-integer payload in MIME data must be ignored, not crash."""
    widget, main_window = _make_slot_widget(qtbot)
    event = _make_drag_event(SLOT_INDEX_MIME, payload="not-a-number")
    widget.dropEvent(event)
    main_window.reorder_slot.assert_not_called()
    event.ignore.assert_called_once()


def test_drop_ignores_when_main_window_lacks_reorder_slot(qtbot):
    """If main_window has no reorder_slot attribute, drop is gracefully ignored.

    Uses a real class (not MagicMock) so hasattr returns False for the
    missing reorder_slot attribute.
    """
    from core.color_slot import ColorSlot, ColorSlotWidget
    from ui.theme_manager import ThemeManager

    class NoReorderMainWindow:
        """Stub main_window with all required attrs EXCEPT reorder_slot."""
        def __init__(self):
            self.theme_manager = ThemeManager()  # Real, fully-keyed theme
            self.settings_manager = mock.MagicMock()
            self.settings_manager.single_click_edit = False
            self.slots_widgets: list = []
        # NOTE: no reorder_slot attribute — hasattr will return False

    nrmw = NoReorderMainWindow()
    preview_grid = mock.MagicMock()

    other_slot = ColorSlot(color=QColor(0, 0, 0), base_size=100,
                           theme_manager=nrmw.theme_manager)
    target_slot = ColorSlot(color=QColor(255, 255, 255), base_size=100,
                            theme_manager=nrmw.theme_manager)
    other_widget = ColorSlotWidget(other_slot, preview_grid, nrmw)
    target_widget = ColorSlotWidget(target_slot, preview_grid, nrmw)
    qtbot.addWidget(other_widget)
    qtbot.addWidget(target_widget)
    nrmw.slots_widgets = [other_widget, target_widget]  # target at index 1

    event = _make_drag_event(SLOT_INDEX_MIME, payload="0")
    target_widget.dropEvent(event)

    event.ignore.assert_called_once()
    event.acceptProposedAction.assert_not_called()
