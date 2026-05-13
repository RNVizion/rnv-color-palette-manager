"""
RNV Color Palette Manager - Settings Manager Module
Persistent user preferences using QSettings.

Stores application preferences in the OS-native location:
- Windows: Registry (HKEY_CURRENT_USER\\Software\\RNV\\ColorPaletteManager)
- macOS: ~/Library/Preferences/com.rnv.ColorPaletteManager.plist
- Linux: ~/.config/RNV/ColorPaletteManager.conf

Features:
- Last used import/export directories
- Last used export format
- Default starting slot count
- Window geometry persistence
- Auto-save settings
- Clipboard format preference

Optimized for Python 3.13.
"""
from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QSettings, QByteArray

from utils.config import APP_AUTHOR, APP_NAME
from utils.logger import Logger, get_logger_instance
from ui.colors import SESSION_FALLBACK_COLOR, SESSION_FALLBACK_COLOR_IMAGE

logger: Logger = get_logger_instance(__name__)


# ==================== Default Values ====================

class Defaults:
    """Default values for all settings."""

    # General
    STARTING_ROWS: int = 3
    STARTING_COLS: int = 4
    DEFAULT_SLOT_COLOR_DARK: str = SESSION_FALLBACK_COLOR    # darkgrey for Dark Mode
    DEFAULT_SLOT_COLOR_LIGHT: str = SESSION_FALLBACK_COLOR   # darkgrey for Light Mode
    DEFAULT_SLOT_COLOR_IMAGE: str = SESSION_FALLBACK_COLOR_IMAGE  # black (semi-transparent) for Image Mode
    SINGLE_CLICK_EDIT: bool = True  # True=click opens picker, False=click selects

    # Auto-save
    AUTO_SAVE_ENABLED: bool = True
    AUTO_SAVE_INTERVAL_MIN: float = 5.0
    AUTO_RESTORE_SESSION: bool = True

    # Export
    LAST_EXPORT_DIR: str = ""
    LAST_IMPORT_DIR: str = ""
    LAST_EXPORT_FORMAT: str = ".json"

    # Clipboard
    CLIPBOARD_FORMAT: str = "hex"  # hex, rgb, hsl

    # Display
    SHOW_COLOR_INFO: bool = False
    COLOR_BLINDNESS_MODE: str = "none"  # none, protanopia, deuteranopia, tritanopia, achromatopsia

    # Appearance
    SLOT_BORDER_STYLE: str = "none"       # none, thin, thick
    SLOT_SIZE_PREFERENCE: str = "auto"    # auto, small, medium, large
    SHOW_SIZE_OVERLAY: bool = False

    # Color History
    MAX_HISTORY_SIZE: int = 100           # 50, 100, 200

    # Recent Palettes
    MAX_RECENT_PALETTES: int = 10         # 5, 10, 20


# ==================== Settings Keys ====================

class Keys:
    """QSettings key constants to avoid string typos."""

    # General group
    STARTING_ROWS = "general/starting_rows"
    STARTING_COLS = "general/starting_cols"
    DEFAULT_SLOT_COLOR_DARK = "general/default_slot_color_dark"
    DEFAULT_SLOT_COLOR_LIGHT = "general/default_slot_color_light"
    DEFAULT_SLOT_COLOR_IMAGE = "general/default_slot_color_image"
    SINGLE_CLICK_EDIT = "general/single_click_edit"

    # Auto-save group
    AUTO_SAVE_ENABLED = "autosave/enabled"
    AUTO_SAVE_INTERVAL = "autosave/interval_minutes"
    AUTO_RESTORE_SESSION = "autosave/auto_restore"

    # Export group
    LAST_EXPORT_DIR = "export/last_directory"
    LAST_IMPORT_DIR = "import/last_directory"
    LAST_EXPORT_FORMAT = "export/last_format"

    # Clipboard group
    CLIPBOARD_FORMAT = "clipboard/format"

    # Window group
    WINDOW_GEOMETRY = "window/geometry"
    WINDOW_STATE = "window/state"

    # Display group
    SHOW_COLOR_INFO = "display/show_color_info"
    COLOR_BLINDNESS_MODE = "display/color_blindness_mode"

    # Appearance group
    SLOT_BORDER_STYLE = "appearance/slot_border_style"
    SLOT_SIZE_PREFERENCE = "appearance/slot_size_preference"
    SHOW_SIZE_OVERLAY = "appearance/show_size_overlay"

    # Color History group
    MAX_HISTORY_SIZE = "history/max_size"

    # Recent Palettes group
    MAX_RECENT_PALETTES = "recent_palettes/max_count"


class SettingsManager:
    """
    Manages persistent application settings using QSettings.

    All settings have sensible defaults and are type-safe.
    Settings are automatically persisted to the OS-native store.

    Example:
        >>> settings = SettingsManager()
        >>> settings.last_export_dir = "/path/to/exports"
        >>> print(settings.last_export_dir)
        '/path/to/exports'
    """

    def __init__(self) -> None:
        """Initialize QSettings with application identity."""
        self._settings = QSettings(APP_AUTHOR, APP_NAME)
        logger.debug("Settings manager initialized")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, key: str, default: Any, type_: type | None = None) -> Any:
        """Get a setting with type coercion."""
        value = self._settings.value(key, default)
        if type_ is not None and not isinstance(value, type_):
            try:
                # QSettings can return strings for everything on some platforms
                if type_ is bool:
                    # QSettings stores bools as "true"/"false" strings
                    if isinstance(value, str):
                        return value.lower() in ("true", "1", "yes")
                    return bool(value)
                if type_ is int:
                    return int(value)
                if type_ is float:
                    return float(value)
                return type_(value)
            except (TypeError, ValueError):
                return default
        return value

    def _set(self, key: str, value: Any) -> None:
        """Set a setting and sync."""
        self._settings.setValue(key, value)

    # ------------------------------------------------------------------
    # General settings
    # ------------------------------------------------------------------

    @property
    def starting_rows(self) -> int:
        """Number of starting rows for color slots."""
        return self._get(Keys.STARTING_ROWS, Defaults.STARTING_ROWS, int)

    @starting_rows.setter
    def starting_rows(self, value: int) -> None:
        self._set(Keys.STARTING_ROWS, max(1, min(10, value)))

    @property
    def starting_cols(self) -> int:
        """Number of starting columns for color slots."""
        return self._get(Keys.STARTING_COLS, Defaults.STARTING_COLS, int)

    @starting_cols.setter
    def starting_cols(self, value: int) -> None:
        self._set(Keys.STARTING_COLS, max(1, min(10, value)))

    @property
    def default_slot_color_dark(self) -> str:
        """Default hex color for new slots in Dark Mode."""
        return self._get(Keys.DEFAULT_SLOT_COLOR_DARK, Defaults.DEFAULT_SLOT_COLOR_DARK, str)

    @default_slot_color_dark.setter
    def default_slot_color_dark(self, value: str) -> None:
        self._set(Keys.DEFAULT_SLOT_COLOR_DARK, value)

    @property
    def default_slot_color_light(self) -> str:
        """Default hex color for new slots in Light Mode."""
        return self._get(Keys.DEFAULT_SLOT_COLOR_LIGHT, Defaults.DEFAULT_SLOT_COLOR_LIGHT, str)

    @default_slot_color_light.setter
    def default_slot_color_light(self, value: str) -> None:
        self._set(Keys.DEFAULT_SLOT_COLOR_LIGHT, value)

    @property
    def default_slot_color_image(self) -> str:
        """Default hex color for new slots in Image Mode."""
        return self._get(Keys.DEFAULT_SLOT_COLOR_IMAGE, Defaults.DEFAULT_SLOT_COLOR_IMAGE, str)

    @default_slot_color_image.setter
    def default_slot_color_image(self, value: str) -> None:
        self._set(Keys.DEFAULT_SLOT_COLOR_IMAGE, value)

    def default_slot_color_for_theme(self, theme_name: str) -> str:
        """Get the default slot color for a given theme name."""
        match theme_name:
            case 'dark':
                return self.default_slot_color_dark
            case 'light':
                return self.default_slot_color_light
            case 'image':
                return self.default_slot_color_image
            case _:
                return Defaults.DEFAULT_SLOT_COLOR_DARK

    def set_default_slot_color_for_theme(self, theme_name: str, value: str) -> None:
        """Set the default slot color for a given theme name."""
        match theme_name:
            case 'dark':
                self.default_slot_color_dark = value
            case 'light':
                self.default_slot_color_light = value
            case 'image':
                self.default_slot_color_image = value

    @property
    def single_click_edit(self) -> bool:
        """True = single-click opens color picker. False = click selects slot."""
        return self._get(Keys.SINGLE_CLICK_EDIT, Defaults.SINGLE_CLICK_EDIT, bool)

    @single_click_edit.setter
    def single_click_edit(self, value: bool) -> None:
        self._set(Keys.SINGLE_CLICK_EDIT, value)

    # ------------------------------------------------------------------
    # Auto-save settings
    # ------------------------------------------------------------------

    @property
    def auto_save_enabled(self) -> bool:
        """Whether session auto-save is enabled."""
        return self._get(Keys.AUTO_SAVE_ENABLED, Defaults.AUTO_SAVE_ENABLED, bool)

    @auto_save_enabled.setter
    def auto_save_enabled(self, value: bool) -> None:
        self._set(Keys.AUTO_SAVE_ENABLED, value)

    @property
    def auto_save_interval(self) -> float:
        """Auto-save interval in minutes."""
        return self._get(Keys.AUTO_SAVE_INTERVAL, Defaults.AUTO_SAVE_INTERVAL_MIN, float)

    @auto_save_interval.setter
    def auto_save_interval(self, value: float) -> None:
        self._set(Keys.AUTO_SAVE_INTERVAL, max(1.0, min(60.0, value)))

    @property
    def auto_save_interval_ms(self) -> int:
        """Auto-save interval in milliseconds (convenience)."""
        return int(self.auto_save_interval * 60 * 1000)

    @property
    def auto_restore_session(self) -> bool:
        """Whether to automatically restore last session on startup."""
        return self._get(Keys.AUTO_RESTORE_SESSION, Defaults.AUTO_RESTORE_SESSION, bool)

    @auto_restore_session.setter
    def auto_restore_session(self, value: bool) -> None:
        self._set(Keys.AUTO_RESTORE_SESSION, value)

    # ------------------------------------------------------------------
    # Export / Import directory settings
    # ------------------------------------------------------------------

    @property
    def last_export_dir(self) -> str:
        """Last used export directory path."""
        return self._get(Keys.LAST_EXPORT_DIR, Defaults.LAST_EXPORT_DIR, str)

    @last_export_dir.setter
    def last_export_dir(self, value: str) -> None:
        self._set(Keys.LAST_EXPORT_DIR, value)

    @property
    def last_import_dir(self) -> str:
        """Last used import directory path."""
        return self._get(Keys.LAST_IMPORT_DIR, Defaults.LAST_IMPORT_DIR, str)

    @last_import_dir.setter
    def last_import_dir(self, value: str) -> None:
        self._set(Keys.LAST_IMPORT_DIR, value)

    @property
    def last_export_format(self) -> str:
        """Last used export format extension (e.g. '.json')."""
        return self._get(Keys.LAST_EXPORT_FORMAT, Defaults.LAST_EXPORT_FORMAT, str)

    @last_export_format.setter
    def last_export_format(self, value: str) -> None:
        self._set(Keys.LAST_EXPORT_FORMAT, value)

    # ------------------------------------------------------------------
    # Clipboard settings
    # ------------------------------------------------------------------

    @property
    def clipboard_format(self) -> str:
        """Preferred clipboard format: 'hex', 'rgb', or 'hsl'."""
        return self._get(Keys.CLIPBOARD_FORMAT, Defaults.CLIPBOARD_FORMAT, str)

    @clipboard_format.setter
    def clipboard_format(self, value: str) -> None:
        if value in ("hex", "rgb", "hsl"):
            self._set(Keys.CLIPBOARD_FORMAT, value)

    # ------------------------------------------------------------------
    # Window geometry
    # ------------------------------------------------------------------

    def save_window_geometry(self, geometry: QByteArray, state: QByteArray | None = None) -> None:
        """
        Save window geometry (and optionally state) for restore on next launch.

        Args:
            geometry: QMainWindow.saveGeometry() result.
            state: QMainWindow.saveState() result (optional).
        """
        self._settings.setValue(Keys.WINDOW_GEOMETRY, geometry)
        if state is not None:
            self._settings.setValue(Keys.WINDOW_STATE, state)

    def restore_window_geometry(self) -> QByteArray | None:
        """
        Get saved window geometry.

        Returns:
            QByteArray for QMainWindow.restoreGeometry(), or None.
        """
        value = self._settings.value(Keys.WINDOW_GEOMETRY)
        if isinstance(value, QByteArray) and not value.isEmpty():
            return value
        return None

    def restore_window_state(self) -> QByteArray | None:
        """
        Get saved window state.

        Returns:
            QByteArray for QMainWindow.restoreState(), or None.
        """
        value = self._settings.value(Keys.WINDOW_STATE)
        if isinstance(value, QByteArray) and not value.isEmpty():
            return value
        return None

    # ------------------------------------------------------------------
    # Display settings (reserved for Phase 5)
    # ------------------------------------------------------------------

    @property
    def show_color_info(self) -> bool:
        """Whether to show expanded color info under slots."""
        return self._get(Keys.SHOW_COLOR_INFO, Defaults.SHOW_COLOR_INFO, bool)

    @show_color_info.setter
    def show_color_info(self, value: bool) -> None:
        self._set(Keys.SHOW_COLOR_INFO, value)

    @property
    def color_blindness_mode(self) -> str:
        """Active color blindness simulation mode."""
        return self._get(Keys.COLOR_BLINDNESS_MODE, Defaults.COLOR_BLINDNESS_MODE, str)

    @color_blindness_mode.setter
    def color_blindness_mode(self, value: str) -> None:
        valid = ("none", "protanopia", "deuteranopia", "tritanopia", "achromatopsia")
        if value in valid:
            self._set(Keys.COLOR_BLINDNESS_MODE, value)

    # ------------------------------------------------------------------
    # Appearance settings
    # ------------------------------------------------------------------

    @property
    def slot_border_style(self) -> str:
        """Slot border style: 'none', 'thin', or 'thick'."""
        return self._get(Keys.SLOT_BORDER_STYLE, Defaults.SLOT_BORDER_STYLE, str)

    @slot_border_style.setter
    def slot_border_style(self, value: str) -> None:
        if value in ("none", "thin", "thick"):
            self._set(Keys.SLOT_BORDER_STYLE, value)

    @property
    def slot_size_preference(self) -> str:
        """Slot size preference: 'auto', 'small', 'medium', or 'large'."""
        return self._get(Keys.SLOT_SIZE_PREFERENCE, Defaults.SLOT_SIZE_PREFERENCE, str)

    @slot_size_preference.setter
    def slot_size_preference(self, value: str) -> None:
        if value in ("auto", "small", "medium", "large"):
            self._set(Keys.SLOT_SIZE_PREFERENCE, value)

    @property
    def show_size_overlay(self) -> bool:
        """Whether to show the size percentage overlay in the corner."""
        return self._get(Keys.SHOW_SIZE_OVERLAY, Defaults.SHOW_SIZE_OVERLAY, bool)

    @show_size_overlay.setter
    def show_size_overlay(self, value: bool) -> None:
        self._set(Keys.SHOW_SIZE_OVERLAY, value)

    # ------------------------------------------------------------------
    # Color History settings
    # ------------------------------------------------------------------

    @property
    def max_history_size(self) -> int:
        """Maximum number of color history entries to keep."""
        return self._get(Keys.MAX_HISTORY_SIZE, Defaults.MAX_HISTORY_SIZE, int)

    @max_history_size.setter
    def max_history_size(self, value: int) -> None:
        if value in (50, 100, 200):
            self._set(Keys.MAX_HISTORY_SIZE, value)

    # ------------------------------------------------------------------
    # Recent Palettes settings
    # ------------------------------------------------------------------

    @property
    def max_recent_palettes(self) -> int:
        """Maximum number of recent palette entries to keep."""
        return self._get(Keys.MAX_RECENT_PALETTES, Defaults.MAX_RECENT_PALETTES, int)

    @max_recent_palettes.setter
    def max_recent_palettes(self, value: int) -> None:
        if value in (5, 10, 20):
            self._set(Keys.MAX_RECENT_PALETTES, value)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        self._settings.clear()
        logger.info("All settings reset to defaults")

    def sync(self) -> None:
        """Force settings to be written to storage."""
        self._settings.sync()

    def get_summary(self) -> str:
        """Get a human-readable summary of current settings."""
        return (
            f"Settings Summary:\n"
            f"  Starting grid:      {self.starting_rows} x {self.starting_cols}\n"
            f"  Default color:      dark={self.default_slot_color_dark}"
            f"  light={self.default_slot_color_light}"
            f"  image={self.default_slot_color_image}\n"
            f"  Auto-save:          {'ON' if self.auto_save_enabled else 'OFF'}"
            f" ({self.auto_save_interval:.1f} min)\n"
            f"  Auto-restore:       {'ON' if self.auto_restore_session else 'OFF'}\n"
            f"  Clipboard format:   {self.clipboard_format}\n"
            f"  Last export dir:    {self.last_export_dir or '(none)'}\n"
            f"  Last import dir:    {self.last_import_dir or '(none)'}\n"
            f"  Last export format: {self.last_export_format}\n"
            f"  Slot border style:  {self.slot_border_style}\n"
            f"  Slot size pref:     {self.slot_size_preference}\n"
            f"  Size overlay:       {'ON' if self.show_size_overlay else 'OFF'}\n"
            f"  Max history size:   {self.max_history_size}\n"
        )


# ==================== Module Exports ====================

__all__: list[str] = [
    "SettingsManager",
    "Defaults",
    "Keys",
]