"""
test_qt_group_membership.py — slots stay in the groups they belong to
=====================================================================

- **Generate Gradient To...** The colors a gradient fills in are inserted
  right after the source slot, so they belong to the source's group. The
  gradient inserted them without adding them to that group's count, so with
  two or more groups the source group's last slots were pushed into the
  group after it.
- **Move to Group.** Moving a slot into a group further down placed it one
  position too early: into an empty group, the slot stayed behind at the end
  of the group before, and that group's last slot moved instead.
"""
from __future__ import annotations

from unittest import mock

import pytest
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QInputDialog

from conftest import _load_main_window


# Six warm and six cool colors, as RGB, told apart by which group holds them
WARM = [(192, 57, 43), (211, 84, 0), (230, 126, 34), (243, 156, 18), (241, 196, 15), (232, 197, 71)]
COOL = [(26, 188, 156), (22, 160, 133), (41, 128, 185), (47, 95, 168), (142, 68, 173), (44, 62, 80)]


@pytest.fixture
def main_window(qapp):
    """A MainWindow with session restore switched off."""
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
    win.deleteLater()


def _two_groups(win):
    """Twelve slots: six warm colors in "Warm", six cool ones in "Cool"."""
    while len(win.slots_widgets) < 12:
        win.add_slot()
    while len(win.slots_widgets) > 12:
        win._remove_slot_internal(win.slots_widgets[-1])
    for widget, rgb in zip(win.slots_widgets, WARM + COOL):
        widget.slot.color = QColor(*rgb)
        widget.slot._is_default_color = False
    warm = win.slot_groups[0]
    warm.name = "Warm"
    cool = win.add_group("Cool")
    warm.slot_count = 6
    cool.slot_count = 6
    win.update_grid()
    return warm, cool


def _members(win, group) -> list[tuple[int, int, int]]:
    start = win._flat_index_for_group_start(group)
    return [w.slot.color.getRgb()[:3]
            for w in win.slots_widgets[start:start + group.slot_count]]


def test_gradient_colors_join_the_source_group(main_window):
    win = main_window
    warm, cool = _two_groups(win)
    source, target = win.slots_widgets[0], win.slots_widgets[5]

    win.start_gradient_from(source)
    with mock.patch.object(QInputDialog, "getInt", return_value=(5, True)):
        target.slot.mousePressEvent(None)   # the click on the target slot

    # Three colors filled in between red and gold, all in Warm
    assert warm.slot_count == 9
    assert _members(win, warm)[0] == WARM[0]
    assert _members(win, warm)[4:] == WARM[1:]
    for widget in win.slots_widgets[1:4]:
        assert win.get_group_for_slot(widget) is warm
    # Cool keeps exactly its own six
    assert _members(win, cool) == COOL


def test_move_to_an_empty_later_group_moves_that_slot(main_window):
    win = main_window
    warm, cool = _two_groups(win)
    picks = win.add_group("Picks")          # empty, as Add New Group makes it
    moving = win.slots_widgets[1]

    win.move_slot_to_group(moving, picks)

    assert _members(win, picks) == [WARM[1]]
    assert win.get_group_for_slot(moving) is picks
    assert _members(win, warm) == [WARM[0]] + WARM[2:]
    assert _members(win, cool) == COOL


def test_move_to_a_later_group_puts_the_slot_at_its_end(main_window):
    win = main_window
    warm, cool = _two_groups(win)

    win.move_slot_to_group(win.slots_widgets[1], cool)

    assert _members(win, cool) == COOL + [WARM[1]]
    assert _members(win, warm) == [WARM[0]] + WARM[2:]


def test_move_to_an_earlier_group_puts_the_slot_at_its_end(main_window):
    win = main_window
    warm, cool = _two_groups(win)

    win.move_slot_to_group(win.slots_widgets[8], warm)

    assert _members(win, warm) == WARM + [COOL[2]]
    assert _members(win, cool) == COOL[:2] + COOL[3:]
