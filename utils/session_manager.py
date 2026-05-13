"""
RNV Color Palette Manager - Session Manager Module
Handles automatic session backup and crash recovery.

Features:
- Timer-based auto-save (configurable interval)
- Palette state persistence (colors, locked states, order)
- Crash recovery detection
- Clean shutdown handling

Optimized for Python 3.13.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from utils.config import SESSIONS_DIR
from utils.logger import Logger, get_logger_instance

logger: Logger = get_logger_instance(__name__)

# Session file paths
SESSION_AUTO_SAVE_PATH = SESSIONS_DIR / "autosave.json"
RECOVERY_FLAG_PATH = SESSIONS_DIR / ".recovery_needed"

# Default auto-save interval (5 minutes in milliseconds)
DEFAULT_AUTO_SAVE_INTERVAL: int = 5 * 60 * 1000


@dataclass
class PaletteSessionState:
    """
    Represents the saved state of the palette workspace.

    Attributes:
        timestamp: ISO format time of when the session was saved.
        slots: List of slot data dicts with color/locked/image info.
        current_theme: Active theme name ('dark', 'light', 'image').
        window_geometry: Saved window position and size bytes (hex encoded).
        metadata: Palette metadata dict (name, description, author, timestamps).
        color_history: List of color history entry dicts.
        groups: List of slot group data dicts (name, collapsed, slot_count).
        version: Session format version for forward compatibility.
    """

    timestamp: str = ""
    slots: list[dict[str, Any]] = field(default_factory=list)
    current_theme: str = "dark"
    window_geometry: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    color_history: list[dict[str, Any]] = field(default_factory=list)
    groups: list[dict[str, Any]] = field(default_factory=list)
    version: int = 1

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PaletteSessionState:
        """Create state from a loaded JSON dictionary."""
        return cls(
            timestamp=data.get("timestamp", ""),
            slots=data.get("slots", []),
            current_theme=data.get("current_theme", "dark"),
            window_geometry=data.get("window_geometry", ""),
            metadata=data.get("metadata", {}),
            color_history=data.get("color_history", []),
            groups=data.get("groups", []),
            version=data.get("version", 1),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return asdict(self)

    @property
    def is_valid(self) -> bool:
        """True if session has at least one slot to restore."""
        return bool(self.slots)

    @property
    def slot_count(self) -> int:
        """Number of slots in the session."""
        return len(self.slots)

    @property
    def age_seconds(self) -> float:
        """How old the session is, in seconds."""
        if not self.timestamp:
            return float("inf")
        try:
            saved_time = datetime.fromisoformat(self.timestamp)
            return (datetime.now() - saved_time).total_seconds()
        except ValueError:
            return float("inf")

    @property
    def formatted_time(self) -> str:
        """Human-readable save time."""
        if not self.timestamp:
            return "Unknown"
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return self.timestamp


class SessionManager(QObject):
    """
    Manages palette session auto-save and crash recovery.

    Periodically captures the full palette state (colors, lock states,
    theme) and writes it to a JSON file. On startup, detects whether
    the previous session ended cleanly and offers recovery.

    Signals:
        session_saved: Emitted after every successful save.
        recovery_available: Emitted with PaletteSessionState when a
            recoverable session is detected at startup.

    Example:
        >>> manager = SessionManager()
        >>> manager.set_state_getter(my_getter_fn)
        >>> manager.start_auto_save(interval_ms=300_000)
    """

    session_saved = pyqtSignal()
    recovery_available = pyqtSignal(object)  # PaletteSessionState

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self._on_auto_save_timer)

        self._current_state: PaletteSessionState | None = None
        self._state_getter: callable | None = None
        self._is_auto_save_enabled: bool = False

        self._ensure_directory()
        logger.debug("Session manager initialized")

    # ------------------------------------------------------------------
    # Directory management
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_directory() -> None:
        """Ensure the sessions directory exists."""
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # State getter
    # ------------------------------------------------------------------

    def set_state_getter(self, getter: callable) -> None:
        """
        Register a callback that returns the current PaletteSessionState.

        The MainWindow provides this so the timer can capture state
        without the session manager needing to know about widgets.
        """
        self._state_getter = getter

    # ------------------------------------------------------------------
    # Auto-save lifecycle
    # ------------------------------------------------------------------

    def start_auto_save(self, interval_ms: int = DEFAULT_AUTO_SAVE_INTERVAL) -> None:
        """Start the periodic auto-save timer."""
        self._is_auto_save_enabled = True
        self._auto_save_timer.start(interval_ms)

        # Set recovery flag so we can detect a crash next launch
        self._set_recovery_flag()

        interval_min = interval_ms / 60_000
        logger.success(f"Auto-save started (every {interval_min:.1f} minutes)")

    def stop_auto_save(self) -> None:
        """Stop the auto-save timer."""
        self._is_auto_save_enabled = False
        self._auto_save_timer.stop()
        self._clear_recovery_flag()
        logger.debug("Auto-save stopped")

    def _on_auto_save_timer(self) -> None:
        """Timer tick handler -- captures and persists current state."""
        if self._state_getter:
            try:
                state = self._state_getter()
                if state and state.is_valid:
                    self.save_session(state)
            except Exception as e:
                logger.warning(f"Auto-save failed: {e}")

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------

    def save_session(self, state: PaletteSessionState) -> bool:
        """
        Write session state to disk (synchronous).

        Args:
            state: The palette state to persist.

        Returns:
            True on success.
        """
        self._ensure_directory()
        try:
            state.timestamp = datetime.now().isoformat()
            with open(SESSION_AUTO_SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, indent=2)

            self._current_state = state
            self.session_saved.emit()
            logger.debug(f"Session saved: {state.slot_count} slots")
            return True
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")
            return False

    def load_session(self) -> PaletteSessionState | None:
        """
        Read session state from disk.

        Returns:
            PaletteSessionState or None if no session exists.
        """
        if not SESSION_AUTO_SAVE_PATH.exists():
            return None
        try:
            with open(SESSION_AUTO_SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            state = PaletteSessionState.from_dict(data)
            logger.debug(f"Session loaded: {state.slot_count} slots")
            return state
        except Exception as e:
            logger.warning(f"Failed to load session: {e}")
            return None

    # ------------------------------------------------------------------
    # Recovery flag
    # ------------------------------------------------------------------

    @staticmethod
    def _set_recovery_flag() -> None:
        """Mark that the application is running (for crash detection)."""
        try:
            RECOVERY_FLAG_PATH.write_text(str(time.time()))
        except Exception as e:
            logger.debug(f"Could not set recovery flag: {e}")

    @staticmethod
    def _clear_recovery_flag() -> None:
        """Remove the recovery flag (clean shutdown)."""
        try:
            if RECOVERY_FLAG_PATH.exists():
                RECOVERY_FLAG_PATH.unlink()
        except Exception as e:
            logger.debug(f"Could not clear recovery flag: {e}")

    # ------------------------------------------------------------------
    # Recovery detection
    # ------------------------------------------------------------------

    def has_recovery(self) -> bool:
        """
        Check whether a recoverable session exists from a previous crash.

        A recovery is available when:
        1. The recovery flag file exists (app didn't shut down cleanly).
        2. An autosave JSON exists with valid slot data.
        3. The session is less than 24 hours old.
        """
        if not RECOVERY_FLAG_PATH.exists():
            return False

        if not SESSION_AUTO_SAVE_PATH.exists():
            self._clear_recovery_flag()
            return False

        state = self.load_session()
        if not state or not state.is_valid:
            self._clear_recovery_flag()
            return False

        # Ignore sessions older than 24 hours
        if state.age_seconds > 24 * 60 * 60:
            logger.debug("Recovery session too old, ignoring")
            self._clear_recovery_flag()
            return False

        return True

    def has_saved_session(self) -> bool:
        """
        Check whether any saved session exists (for auto-restore).

        Unlike has_recovery(), this does NOT require the recovery flag --
        it simply checks if a session file exists and is valid.
        Used for the "auto-restore last session" setting.
        """
        if not SESSION_AUTO_SAVE_PATH.exists():
            return False
        state = self.load_session()
        return state is not None and state.is_valid

    def get_recovery_state(self) -> PaletteSessionState | None:
        """Load the recoverable session state."""
        return self.load_session()

    def clear_recovery(self) -> None:
        """Discard recovery data after restore or decline."""
        self._clear_recovery_flag()
        try:
            if SESSION_AUTO_SAVE_PATH.exists():
                SESSION_AUTO_SAVE_PATH.unlink()
        except Exception as e:
            logger.debug(f"Could not clear saved session: {e}")

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    def on_clean_shutdown(self, final_state: PaletteSessionState | None = None) -> None:
        """
        Called when the application shuts down normally.

        Saves one final snapshot (for auto-restore on next launch),
        then clears the crash-recovery flag.
        """
        if final_state and final_state.is_valid:
            self.save_session(final_state)
        self.stop_auto_save()
        self._clear_recovery_flag()
        logger.debug("Clean shutdown recorded")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_auto_save_enabled(self) -> bool:
        return self._is_auto_save_enabled

    @property
    def last_save_time(self) -> str:
        if self._current_state:
            return self._current_state.formatted_time
        return "Never"


# ==================== Module Exports ====================

__all__: list[str] = [
    "SessionManager",
    "PaletteSessionState",
    "SESSION_AUTO_SAVE_PATH",
    "DEFAULT_AUTO_SAVE_INTERVAL",
]