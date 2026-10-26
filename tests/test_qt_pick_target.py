"""
test_qt_pick_target.py — picking a target slot shows its hint, and Esc cancels
==============================================================================

Generate Gradient To..., Mix With... and Check Contrast With... each wait
for a click on a second slot. While they wait, the top-right overlay says
"Click target slot". That overlay is the size overlay, which is off by
default, so the hint used to be shown only to users who had turned the
size overlay on. It now shows whenever a target is being picked, and goes
back to the size overlay's setting when the pick ends.

Esc cancels the pick, leaving it the way each mode's own cancel does
(the slots take their own clicks again), before it closes the search bar
or deselects a slot.
"""
from __future__ import annotations

from unittest import mock

import pytest

from conftest import _load_main_window, _trigger_shortcut
from utils.dialog_helper import DialogHelper

HINT = "Click target slot"

#: (start method, the attribute that holds the source while picking,
#:  the mode's own cancel, which a click on a target also runs)
MODES = [
    ("start_gradient_from", "_gradient_source", "_cancel_gradient_mode"),
    ("start_mix_from", "_mix_source", "_cancel_mix_mode"),
    ("start_contrast_from", "_contrast_source", "_cancel_contrast_mode"),
]
IDS = [m[0] for m in MODES]


@pytest.fixture(scope="module")
def main_window(qapp):
    """Module-scoped MainWindow, shown, with the size overlay off."""
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
    win.resize(1280, 800)
    win.show()
    yield win
    win.hide()


@pytest.fixture(autouse=True)
def overlay_off(main_window):
    """Each test starts with the size overlay off and nothing being picked."""
    main_window.settings_manager.show_size_overlay = False
    main_window._apply_appearance_settings()
    yield
    for _start, attr, cancel in MODES:
        if getattr(main_window, attr, None) is not None:
            getattr(main_window, cancel)()
    if main_window.color_search_bar.isVisible():
        main_window.color_search_bar.close_search()


def _overlay_shown(win) -> bool:
    return not win.size_overlay.isHidden()


def _handlers_restored(win) -> bool:
    return all(w.slot.mousePressEvent == w._on_slot_press for w in win.slots_widgets)


# ═══════════════════════════════════════════════════════════════════════════
# The hint
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("start, attr, cancel", MODES, ids=IDS)
def test_hint_shows_while_picking_with_the_size_overlay_off(main_window, start, attr, cancel):
    win = main_window
    assert not _overlay_shown(win)

    getattr(win, start)(win.slots_widgets[0])

    assert getattr(win, attr) is win.slots_widgets[0]
    assert _overlay_shown(win), "the pick hint is hidden with the size overlay"
    assert win.size_overlay.text() == HINT


@pytest.mark.parametrize("start, attr, cancel", MODES, ids=IDS)
def test_overlay_goes_back_to_its_setting_when_the_pick_ends(main_window, start, attr, cancel):
    win = main_window
    getattr(win, start)(win.slots_widgets[0])
    assert _overlay_shown(win)
    getattr(win, cancel)()

    assert not _overlay_shown(win)
    assert win.size_overlay.text() != HINT

    # With the size overlay on, it shows the size again, not the hint
    win.settings_manager.show_size_overlay = True
    win._apply_appearance_settings()
    getattr(win, start)(win.slots_widgets[0])
    getattr(win, cancel)()
    assert _overlay_shown(win)
    assert win.size_overlay.text().endswith("%"), win.size_overlay.text()


def test_hint_stays_through_a_resize(main_window):
    win = main_window
    win.start_mix_from(win.slots_widgets[0])
    win.resize(1100, 760)
    win.resize(1280, 800)
    assert win.size_overlay.text() == HINT
    assert _overlay_shown(win)


def test_hint_stays_through_a_theme_change(main_window):
    win = main_window
    win.start_gradient_from(win.slots_widgets[0])
    for _ in range(3):           # all the way round, back to where it was
        win.cycle_theme()
        assert win.size_overlay.text() == HINT
        assert _overlay_shown(win)


def test_f12_while_picking_keeps_the_hint_and_sets_the_setting(main_window):
    win = main_window
    win.start_contrast_from(win.slots_widgets[0])
    _trigger_shortcut(win, "F12")
    assert win.settings_manager.show_size_overlay is True
    assert _overlay_shown(win) and win.size_overlay.text() == HINT
    win._cancel_contrast_mode()
    assert _overlay_shown(win)                      # the setting is now on
    _trigger_shortcut(win, "F12")
    assert win.settings_manager.show_size_overlay is False
    assert not _overlay_shown(win)


def test_a_finished_pick_takes_the_hint_away(main_window):
    win = main_window
    source, target = win.slots_widgets[0], win.slots_widgets[1]
    win.start_contrast_from(source)
    with mock.patch.object(DialogHelper, "show_info") as shown:
        target.slot.mousePressEvent(None)
    assert shown.called
    assert not _overlay_shown(win)
    assert win.size_overlay.text() != HINT


# ═══════════════════════════════════════════════════════════════════════════
# Esc
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("start, attr, cancel", MODES, ids=IDS)
def test_esc_cancels_the_pick(main_window, start, attr, cancel):
    win = main_window
    count = len(win.slots_widgets)
    getattr(win, start)(win.slots_widgets[0])

    _trigger_shortcut(win, "Escape")

    assert getattr(win, attr) is None
    # A click on another slot goes to the slot again, not to the pick
    assert _handlers_restored(win)
    assert not _overlay_shown(win)
    assert len(win.slots_widgets) == count


def test_esc_cancels_the_pick_before_closing_search(main_window):
    win = main_window
    win.color_search_bar.toggle()
    assert win.color_search_bar.isVisible()
    win.start_mix_from(win.slots_widgets[0])

    _trigger_shortcut(win, "Escape")
    assert win._mix_source is None
    assert win.color_search_bar.isVisible(), "the first Esc closed search, not the pick"

    _trigger_shortcut(win, "Escape")
    assert not win.color_search_bar.isVisible()


def test_esc_cancels_the_pick_and_keeps_the_selection(main_window):
    win = main_window
    win.select_slot(win.slots_widgets[2])
    win.start_gradient_from(win.slots_widgets[0])

    _trigger_shortcut(win, "Escape")
    assert win._gradient_source is None
    assert win._selected_slot is win.slots_widgets[2]

    _trigger_shortcut(win, "Escape")       # the next Esc deselects, as before
    assert win._selected_slot is None
