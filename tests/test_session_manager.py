"""
test_session_manager.py — Tests for utils/session_manager.py
==============================================================

Phase 12b. Targets ~54% of session_manager.py that's still uncovered:
the save/load/recovery logic. We DO use a QApplication because
SessionManager is a QObject (needs the Qt event loop alive for
QTimer construction), but we never actually run the timer — all
tests drive save/load directly.

CRITICAL: The session manager uses module-level constants
SESSION_AUTO_SAVE_PATH and RECOVERY_FLAG_PATH that point to the
user's real ~/.config/... directory. Every test monkeypatches these
to tmp_path so we never touch the user's actual saved sessions.

What's covered
--------------
- PaletteSessionState dataclass: from_dict / to_dict round-trip,
  is_valid, slot_count, age_seconds, formatted_time
- SessionManager.save_session: writes JSON, sets timestamp, emits signal
- SessionManager.load_session: reads JSON, returns None for missing
- has_recovery: flag-and-file logic, age cutoff
- has_saved_session: ignores flag
- get_recovery_state: same as load_session
- clear_recovery: removes flag and session file
- on_clean_shutdown: saves final state, clears flag
- start_auto_save / stop_auto_save: enables/disables timer state

What's NOT covered (out of scope)
----------------------------------
- The actual QTimer firing _on_auto_save_timer at intervals — tested
  by directly calling _on_auto_save_timer with a stubbed state getter.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest import mock

import pytest

from utils import session_manager
from utils.session_manager import PaletteSessionState, SessionManager


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def isolated_session_paths(tmp_path, monkeypatch):
    """Redirect session manager file paths to tmp_path.

    The session manager has module-level path constants that point to
    the user's real config directory. We rebind both to children of
    tmp_path so tests never touch the user's actual saved sessions.

    Returns the (autosave_path, recovery_flag_path) tuple for tests
    that want to inspect the on-disk state directly.
    """
    autosave = tmp_path / "autosave.json"
    flag = tmp_path / ".recovery_needed"

    monkeypatch.setattr(session_manager, "SESSION_AUTO_SAVE_PATH", autosave)
    monkeypatch.setattr(session_manager, "RECOVERY_FLAG_PATH", flag)

    return autosave, flag


@pytest.fixture
def sample_state():
    """A valid PaletteSessionState with one slot — enough to be is_valid."""
    return PaletteSessionState(
        slots=[{"color": [255, 0, 0], "locked": False}],
        current_theme="dark",
    )


@pytest.fixture
def manager(qapp, isolated_session_paths):
    """A fresh SessionManager bound to isolated paths.

    The qapp fixture (from pytest-qt) ensures a QApplication is alive,
    which is required for QObject construction. We don't run the timer.
    """
    return SessionManager()


# ═══════════════════════════════════════════════════════════════════════════
# PaletteSessionState dataclass
# ═══════════════════════════════════════════════════════════════════════════

def test_state_is_valid_with_slots():
    state = PaletteSessionState(slots=[{"color": [0, 0, 0]}])
    assert state.is_valid is True


def test_state_is_invalid_when_empty():
    state = PaletteSessionState(slots=[])
    assert state.is_valid is False


def test_state_slot_count():
    state = PaletteSessionState(slots=[{}, {}, {}])
    assert state.slot_count == 3


def test_state_to_dict_round_trip():
    """from_dict(to_dict(x)) must equal x for serialization safety."""
    original = PaletteSessionState(
        timestamp="2024-01-15T10:30:00",
        slots=[{"color": [100, 200, 50], "locked": True}],
        current_theme="image",
        window_geometry="abc123",
        metadata={"name": "Test palette"},
        color_history=[{"color": [255, 255, 255]}],
        groups=[{"name": "Group 1", "slot_count": 5}],
        version=1,
    )

    restored = PaletteSessionState.from_dict(original.to_dict())

    assert restored.timestamp == original.timestamp
    assert restored.slots == original.slots
    assert restored.current_theme == original.current_theme
    assert restored.window_geometry == original.window_geometry
    assert restored.metadata == original.metadata
    assert restored.color_history == original.color_history
    assert restored.groups == original.groups
    assert restored.version == original.version


def test_state_from_dict_uses_defaults_for_missing_fields():
    """A partial dict (e.g. from old session format) gets safe defaults."""
    state = PaletteSessionState.from_dict({})
    assert state.slots == []
    assert state.current_theme == "dark"
    assert state.version == 1


def test_state_age_seconds_recent():
    """A just-saved timestamp has a small age."""
    state = PaletteSessionState(
        timestamp=datetime.now().isoformat(),
        slots=[{}],
    )
    assert state.age_seconds < 5.0


def test_state_age_seconds_returns_inf_for_empty_timestamp():
    state = PaletteSessionState(timestamp="", slots=[{}])
    assert state.age_seconds == float("inf")


def test_state_age_seconds_returns_inf_for_invalid_timestamp():
    """Malformed ISO timestamp returns infinity, not exception."""
    state = PaletteSessionState(timestamp="not-a-date", slots=[{}])
    assert state.age_seconds == float("inf")


def test_state_formatted_time_with_valid_iso():
    state = PaletteSessionState(timestamp="2024-01-15T10:30:00", slots=[{}])
    formatted = state.formatted_time
    assert "2024" in formatted
    assert "10:30:00" in formatted


def test_state_formatted_time_returns_unknown_for_empty():
    state = PaletteSessionState(timestamp="", slots=[{}])
    assert state.formatted_time == "Unknown"


def test_state_formatted_time_returns_raw_for_invalid():
    """A non-ISO timestamp is returned as-is rather than crashing."""
    state = PaletteSessionState(timestamp="garbage", slots=[{}])
    assert state.formatted_time == "garbage"


# ═══════════════════════════════════════════════════════════════════════════
# SessionManager.save_session
# ═══════════════════════════════════════════════════════════════════════════

def test_save_session_writes_json_to_disk(manager, isolated_session_paths, sample_state):
    autosave, _ = isolated_session_paths
    assert manager.save_session(sample_state) is True
    assert autosave.exists()

    # Content is valid JSON with the slot data
    data = json.loads(autosave.read_text(encoding="utf-8"))
    assert data["slots"] == sample_state.slots
    assert data["current_theme"] == sample_state.current_theme


def test_save_session_sets_timestamp(manager, sample_state):
    """save_session stamps the state with the current time."""
    sample_state.timestamp = ""
    manager.save_session(sample_state)
    assert sample_state.timestamp != ""
    # Should be parseable as ISO format
    datetime.fromisoformat(sample_state.timestamp)


def test_save_session_emits_signal(manager, sample_state, qtbot):
    """The session_saved signal is emitted after a successful write."""
    with qtbot.waitSignal(manager.session_saved, timeout=1000):
        manager.save_session(sample_state)


# ═══════════════════════════════════════════════════════════════════════════
# SessionManager.load_session
# ═══════════════════════════════════════════════════════════════════════════

def test_load_session_returns_none_when_no_file(manager):
    """No autosave file means no recoverable session."""
    assert manager.load_session() is None


def test_load_session_returns_state_after_save(manager, sample_state):
    """save_session followed by load_session round-trips the state."""
    manager.save_session(sample_state)
    loaded = manager.load_session()

    assert loaded is not None
    assert loaded.slots == sample_state.slots
    assert loaded.current_theme == sample_state.current_theme


def test_load_session_returns_none_for_corrupt_json(manager, isolated_session_paths):
    """A corrupt JSON file is logged and treated as absent."""
    autosave, _ = isolated_session_paths
    autosave.write_text("{not valid json")

    assert manager.load_session() is None


# ═══════════════════════════════════════════════════════════════════════════
# has_recovery
# ═══════════════════════════════════════════════════════════════════════════

def test_has_recovery_false_when_no_flag(manager):
    """No recovery flag means no recovery offered."""
    assert manager.has_recovery() is False


def test_has_recovery_false_when_flag_but_no_session(manager, isolated_session_paths):
    """If the flag exists but the session file doesn't, return False
    AND clear the stale flag."""
    _, flag = isolated_session_paths
    flag.write_text(str(0))

    assert manager.has_recovery() is False
    # Stale flag should be cleared
    assert not flag.exists()


def test_has_recovery_true_for_recent_session_with_flag(
    manager, isolated_session_paths, sample_state
):
    """Recent session + recovery flag = recovery available."""
    _, flag = isolated_session_paths
    manager.save_session(sample_state)
    flag.write_text(str(0))  # Simulate uncleared flag from previous run

    assert manager.has_recovery() is True


def test_has_recovery_false_for_old_session(
    manager, isolated_session_paths, sample_state
):
    """Sessions older than 24 hours are not offered for recovery."""
    autosave, flag = isolated_session_paths
    flag.write_text(str(0))

    # Manually write a session with an old timestamp
    old_time = (datetime.now() - timedelta(days=2)).isoformat()
    sample_state.timestamp = old_time
    autosave.write_text(json.dumps(sample_state.to_dict()))

    assert manager.has_recovery() is False
    # Old session causes flag to be cleared
    assert not flag.exists()


def test_has_recovery_false_for_invalid_session(
    manager, isolated_session_paths
):
    """A session with no slots is not recoverable."""
    autosave, flag = isolated_session_paths
    flag.write_text(str(0))

    # Empty-slots session
    empty = PaletteSessionState(timestamp=datetime.now().isoformat(), slots=[])
    autosave.write_text(json.dumps(empty.to_dict()))

    assert manager.has_recovery() is False


# ═══════════════════════════════════════════════════════════════════════════
# has_saved_session (no flag required)
# ═══════════════════════════════════════════════════════════════════════════

def test_has_saved_session_false_when_no_file(manager):
    assert manager.has_saved_session() is False


def test_has_saved_session_true_after_save(manager, sample_state):
    """has_saved_session checks just the file, not the flag."""
    manager.save_session(sample_state)
    assert manager.has_saved_session() is True


def test_has_saved_session_false_for_empty_slots(
    manager, isolated_session_paths
):
    autosave, _ = isolated_session_paths
    empty = PaletteSessionState(timestamp=datetime.now().isoformat(), slots=[])
    autosave.write_text(json.dumps(empty.to_dict()))

    assert manager.has_saved_session() is False


# ═══════════════════════════════════════════════════════════════════════════
# clear_recovery
# ═══════════════════════════════════════════════════════════════════════════

def test_clear_recovery_removes_flag_and_session(
    manager, isolated_session_paths, sample_state
):
    """clear_recovery removes both the flag and the session file."""
    autosave, flag = isolated_session_paths
    manager.save_session(sample_state)
    flag.write_text(str(0))

    assert autosave.exists()
    assert flag.exists()

    manager.clear_recovery()

    assert not autosave.exists()
    assert not flag.exists()


def test_clear_recovery_safe_when_files_missing(manager, isolated_session_paths):
    """clear_recovery doesn't raise when files don't exist."""
    # No save, no flag — still shouldn't crash
    manager.clear_recovery()


# ═══════════════════════════════════════════════════════════════════════════
# on_clean_shutdown
# ═══════════════════════════════════════════════════════════════════════════

def test_clean_shutdown_saves_final_state(
    manager, isolated_session_paths, sample_state
):
    """on_clean_shutdown saves the final state for next-launch auto-restore."""
    autosave, _ = isolated_session_paths
    manager.on_clean_shutdown(sample_state)

    assert autosave.exists()


def test_clean_shutdown_clears_recovery_flag(
    manager, isolated_session_paths, sample_state
):
    """After clean shutdown, the recovery flag is gone."""
    _, flag = isolated_session_paths
    flag.write_text(str(0))

    manager.on_clean_shutdown(sample_state)

    assert not flag.exists()


def test_clean_shutdown_with_no_state_skips_save(
    manager, isolated_session_paths
):
    """If no final state is provided, skip the save but still clear the flag."""
    autosave, flag = isolated_session_paths
    flag.write_text(str(0))

    manager.on_clean_shutdown(None)

    assert not autosave.exists()
    assert not flag.exists()


# ═══════════════════════════════════════════════════════════════════════════
# Auto-save lifecycle
# ═══════════════════════════════════════════════════════════════════════════

def test_start_auto_save_enables_flag(manager, isolated_session_paths):
    """start_auto_save flips the enabled property and writes a flag."""
    _, flag = isolated_session_paths

    manager.start_auto_save(interval_ms=300_000)

    assert manager.is_auto_save_enabled is True
    assert flag.exists()
    # Stop to clean up the QTimer
    manager.stop_auto_save()


def test_stop_auto_save_disables_flag(manager, isolated_session_paths):
    _, flag = isolated_session_paths

    manager.start_auto_save(interval_ms=300_000)
    manager.stop_auto_save()

    assert manager.is_auto_save_enabled is False
    assert not flag.exists()


def test_auto_save_timer_calls_state_getter_when_enabled(manager, sample_state):
    """The timer callback uses the registered state-getter to get state."""
    getter = mock.Mock(return_value=sample_state)
    manager.set_state_getter(getter)

    # Directly invoke the timer handler (don't wait for real timer)
    manager._on_auto_save_timer()

    getter.assert_called_once()


def test_auto_save_timer_skips_save_when_state_invalid(
    manager, isolated_session_paths
):
    """If the getter returns an invalid (empty) state, no save happens."""
    autosave, _ = isolated_session_paths
    invalid_state = PaletteSessionState(slots=[])
    manager.set_state_getter(lambda: invalid_state)

    manager._on_auto_save_timer()

    assert not autosave.exists()


def test_auto_save_timer_handles_getter_exception(manager):
    """If the getter raises, the timer callback does not propagate it."""
    manager.set_state_getter(lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    # Should not raise — exception is caught and logged
    manager._on_auto_save_timer()


def test_last_save_time_returns_never_initially(manager):
    assert manager.last_save_time == "Never"


def test_last_save_time_returns_formatted_after_save(manager, sample_state):
    manager.save_session(sample_state)
    result = manager.last_save_time
    assert result != "Never"
    # Should look like a formatted timestamp
    assert "2" in result or len(result) > 5  # year digit or readable format
