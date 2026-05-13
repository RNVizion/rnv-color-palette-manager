"""
Utility modules for RNV Color Palette Manager.
"""
from __future__ import annotations

from utils.config import (
    BASE_DIR,
    RESOURCES_DIR,
    BUTTON_IMAGES_DIR,
    BACKGROUND_IMAGES_DIR,
    FONTS_DIR,
    ICONS_DIR,
    APP_NAME,
    APP_VERSION,
    APP_ICON_PATH,
    BACKGROUND_IMAGE_PATH,
    FONT_PATH,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    REF_WIDTH,
    REF_HEIGHT,
    MIN_SLOT_SIZE,
    MAX_SLOT_SIZE,
    MAX_SLOTS,
    MAX_IMAGE_DIMENSION,
    SLOT_WIDGET_SPACING,
    get_button_image_paths,
)
from utils.font_loader import (
    load_embedded_font,
    get_bold_font,
    get_regular_font,
    get_monospace_font,
    get_font_family,
)
from utils.logger import Logger, get_logger_instance, setup_logger, get_logger
from utils.dialog_helper import DialogHelper, DialogResult
from utils.error_handler import ErrorHandler, ErrorCategory, safe_method, ValidationHelper
from utils.file_utils import FileUtils
from utils.pixmap_cache import QPixmapCache, ImagePixmapCache, ThumbnailCache
from utils.settings_manager import SettingsManager
from utils.session_manager import SessionManager, PaletteSessionState
from utils.export_history import ExportHistory
from utils.undo_manager import UndoManager, PaletteState
from utils.recent_palettes import RecentPalettesManager, RecentPaletteEntry
from utils.color_history import ColorHistoryPanel, ColorHistoryEntry

__all__ = [
    # Config
    "BASE_DIR",
    "RESOURCES_DIR",
    "BUTTON_IMAGES_DIR",
    "BACKGROUND_IMAGES_DIR",
    "FONTS_DIR",
    "ICONS_DIR",
    "APP_NAME",
    "APP_VERSION",
    "APP_ICON_PATH",
    "BACKGROUND_IMAGE_PATH",
    "FONT_PATH",
    "MIN_WINDOW_WIDTH",
    "MIN_WINDOW_HEIGHT",
    "REF_WIDTH",
    "REF_HEIGHT",
    "MIN_SLOT_SIZE",
    "MAX_SLOT_SIZE",
    "MAX_SLOTS",
    "MAX_IMAGE_DIMENSION",
    "SLOT_WIDGET_SPACING",
    "get_button_image_paths",
    # Font loader
    "load_embedded_font",
    "get_bold_font",
    "get_regular_font",
    "get_monospace_font",
    "get_font_family",
    # Logger
    "Logger",
    "get_logger_instance",
    "setup_logger",
    "get_logger",
    # Dialog helper
    "DialogHelper",
    "DialogResult",
    # Error handler
    "ErrorHandler",
    "ErrorCategory",
    "safe_method",
    "ValidationHelper",
    # File utils
    "FileUtils",
    # Pixmap cache
    "QPixmapCache",
    "ImagePixmapCache",
    "ThumbnailCache",
    # Settings manager
    "SettingsManager",
    # Session manager
    "SessionManager",
    "PaletteSessionState",
    # Export history
    "ExportHistory",
    # Undo manager
    "UndoManager",
    "PaletteState",
    # Recent palettes
    "RecentPalettesManager",
    "RecentPaletteEntry",
    # Color history
    "ColorHistoryPanel",
    "ColorHistoryEntry",
]
