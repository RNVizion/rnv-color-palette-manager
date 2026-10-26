"""
test_qt_mix_with.py — the six mixing algorithms, reached from the slot menu
===========================================================================

Right-click a slot → **Mix With...** → click a second slot → choose an
algorithm. The two colors are mixed in equal parts by the chosen function
in `core/color_math.py`, and the result is added as a new slot right after
the first one, in its group. Before this, the six functions were tested
but nothing in the app called them.
"""
from __future__ import annotations

from unittest import mock

import pytest
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QInputDialog, QMenu

from conftest import _load_main_window
from core.color_math import ColorMath


YELLOW = (245, 208, 0)
BLUE = (31, 79, 191)

FUNCTIONS = {
    "RGB Weighted": ColorMath.weighted_rgb_mix,
    "HSV Weighted": ColorMath.weighted_hsv_mix,
    "CIE LAB Perceptual": ColorMath.lab_perceptual_mix,
    "RYB Artist's Wheel": ColorMath.weighted_ryb_mix,
    "Subtractive CMY": ColorMath.subtractive_cmy_mix,
    "Kubelka-Munk": ColorMath.kubelka_munk_mix,
}


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


def _paint(widget, rgb) -> None:
    widget.slot.color = QColor(*rgb)
    widget.slot._is_default_color = False


def _menu_actions(widget) -> dict[str, object]:
    """Build the slot's context menu without showing it; return its actions."""
    captured: dict[str, object] = {}

    def fake_exec(menu, *args, **kwargs):
        for action in menu.actions():
            captured[action.text()] = action
        return None

    with mock.patch.object(QMenu, "exec", fake_exec):
        widget._show_context_menu(widget.mapToGlobal(widget.rect().center()))
    return captured


# ═══════════════════════════════════════════════════════════════════════════
# core: one name for each of the six functions
# ═══════════════════════════════════════════════════════════════════════════

def test_mix_names_cover_the_six_functions():
    assert ColorMath.MIX_NAMES == list(FUNCTIONS)


@pytest.mark.parametrize("name", list(FUNCTIONS))
def test_mix_dispatches_to_the_named_function(name):
    pair = [(YELLOW, 1), (BLUE, 1)]
    assert ColorMath.mix(name, pair) == FUNCTIONS[name](pair)


def test_mix_unknown_name_gives_none():
    assert ColorMath.mix("Watercolor", [(YELLOW, 1), (BLUE, 1)]) is None


# ═══════════════════════════════════════════════════════════════════════════
# The slot menu offers it
# ═══════════════════════════════════════════════════════════════════════════

def test_slot_menu_offers_mix_with(main_window):
    actions = _menu_actions(main_window.slots_widgets[0])
    assert "Mix With..." in actions
    assert actions["Mix With..."].isEnabled()


# ═══════════════════════════════════════════════════════════════════════════
# The whole flow: menu entry → click a target → choose → new slot
# ═══════════════════════════════════════════════════════════════════════════

def test_mix_with_adds_the_mix_after_the_source_in_its_group(main_window):
    win = main_window
    source, target = win.slots_widgets[0], win.slots_widgets[2]
    _paint(source, YELLOW)
    _paint(target, BLUE)
    count = len(win.slots_widgets)
    group = win.get_group_for_slot(source)
    group_count = group.slot_count

    _menu_actions(source)["Mix With..."].trigger()
    with mock.patch.object(
        QInputDialog, "getItem", return_value=("Kubelka-Munk", True)
    ) as prompt:
        # The user's click on the target slot, routed by the selection mode
        target.slot.mousePressEvent(None)

    assert prompt.call_args.args[3] == ColorMath.MIX_NAMES
    assert len(win.slots_widgets) == count + 1
    new = win.slots_widgets[1]
    expected = ColorMath.kubelka_munk_mix([(YELLOW, 1), (BLUE, 1)])
    assert (new.slot.color.red(), new.slot.color.green(), new.slot.color.blue()) == expected
    assert new.hex_label.text() == new.slot.color.name()
    assert win.get_group_for_slot(new) is group
    assert group.slot_count == group_count + 1
    # Selection mode is over: clicks go back to the slots' own handler
    assert all(w.slot.mousePressEvent == w._on_slot_press for w in win.slots_widgets)

    # One undo step takes it away again
    win.undo()
    assert len(win.slots_widgets) == count


def test_mix_with_cancelled_adds_nothing(main_window):
    win = main_window
    source, target = win.slots_widgets[0], win.slots_widgets[1]
    count = len(win.slots_widgets)
    win.start_mix_from(source)
    with mock.patch.object(QInputDialog, "getItem", return_value=("", False)):
        target.slot.mousePressEvent(None)
    assert len(win.slots_widgets) == count
    assert all(w.slot.mousePressEvent == w._on_slot_press for w in win.slots_widgets)
