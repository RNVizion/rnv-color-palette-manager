"""
Configuration constants and paths for RNV Color Palette Manager.
Centralized settings, resource paths, and helper functions.
Optimized for Python 3.13.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

# ==================== Application Identity ====================
APP_NAME: Final[str] = "RNV Color Palette Manager"
APP_VERSION: Final[str] = "3.3.13"
APP_AUTHOR: Final[str] = "RNV"

# ==================== Resource Paths ====================
# Use pathlib for modern, cross-platform path handling.
# BASE_DIR resolves to the project root (parent of the utils/ package).
BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
RESOURCES_DIR: Final[Path] = BASE_DIR / "resources"
BUTTON_IMAGES_DIR: Final[Path] = RESOURCES_DIR / "button_images"
BACKGROUND_IMAGES_DIR: Final[Path] = RESOURCES_DIR / "background_images"
FONTS_DIR: Final[Path] = RESOURCES_DIR / "fonts"
ICONS_DIR: Final[Path] = RESOURCES_DIR / "icons"

# Direct file paths for commonly accessed resources
APP_ICON_PATH: Final[Path] = ICONS_DIR / "icon.png"
SPECIAL_SLOT_ICON_PATH: Final[Path] = ICONS_DIR / "special_slot.png"
BACKGROUND_IMAGE_PATH: Final[Path] = BACKGROUND_IMAGES_DIR / "background.png"
FONT_PATH: Final[Path] = FONTS_DIR / "Montserrat-Black.ttf"

# ==================== User Data Paths ====================
# Persistent data directory in the user's home folder.
USER_DATA_DIR: Final[Path] = Path.home() / ".rnv_color_palette_manager"
LOGS_DIR: Final[Path] = USER_DATA_DIR / "logs"
SESSIONS_DIR: Final[Path] = USER_DATA_DIR / "sessions"
EXPORT_HISTORY_PATH: Final[Path] = USER_DATA_DIR / "export_history.json"

# ==================== Window Settings ====================
MIN_WINDOW_WIDTH: Final[int] = 1000
MIN_WINDOW_HEIGHT: Final[int] = 700
REF_WIDTH: Final[int] = 1000
REF_HEIGHT: Final[int] = 700

# ==================== Slot Settings ====================
MIN_SLOT_SIZE: Final[int] = 100
MAX_SLOT_SIZE: Final[int] = 200
MAX_SLOTS: Final[int] = 99

# ==================== Image Settings ====================
MAX_IMAGE_DIMENSION: Final[int] = 3840

# ==================== Layout Settings ====================
SLOT_WIDGET_SPACING: Final[int] = 6

# ==================== Logging Settings ====================
DEFAULT_LOG_LEVEL: Final[int] = logging.INFO
LOG_FILE_MAX_SIZE: Final[int] = 5 * 1024 * 1024  # 5 MB
LOG_FILE_BACKUP_COUNT: Final[int] = 3
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ==================== Feature Flags ====================
DEBUG_MODE: Final[bool] = False
ENABLE_IMAGE_MODE: Final[bool] = True
ENABLE_THEME_CYCLING: Final[bool] = True
SHOW_TOOLTIPS: Final[bool] = True


# ==================== Helper Functions ====================

def ensure_directories() -> None:
    """Create required user data directories if they don't exist."""
    for directory in (USER_DATA_DIR, LOGS_DIR, SESSIONS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to a resource file.

    Args:
        relative_path: Path relative to the resources directory.

    Returns:
        Absolute Path to the resource.

    Example:
        icon = get_resource_path("icons/icon.png")
    """
    return RESOURCES_DIR / relative_path


def resource_exists(relative_path: str) -> bool:
    """
    Check if a resource file exists.

    Args:
        relative_path: Path relative to the resources directory.

    Returns:
        True if the resource file exists.
    """
    return (RESOURCES_DIR / relative_path).exists()


def get_button_image_paths(name: str) -> tuple[str | None, str | None, str | None]:
    """
    Get base, hover, and pressed image paths for a named button.
    Handles both underscore and hyphen naming conventions.

    Args:
        name: Button name (e.g. "upload", "clear", "clear_all", "lock").

    Returns:
        Tuple of (base_path, hover_path, pressed_path) as strings or None.
        hover and pressed fall back to base if their specific images aren't found.

    Example:
        base, hover, pressed = get_button_image_paths("upload")
        btn = ImageButton("Upload", base, hover, pressed)
    """
    button_dir = Path(BUTTON_IMAGES_DIR)
    name_underscore = name.lower().replace(' ', '_')

    def _find_image(prefix: str, suffix: str) -> str | None:
        """Try to find image with both naming conventions."""
        # Try underscore version first (e.g., "upload_base.png")
        path = button_dir / f"{prefix}_{suffix}.png"
        if path.exists():
            return str(path)

        # Try hyphen version (e.g., "clear-all_base.png")
        path = button_dir / f"{prefix.replace('_', '-')}_{suffix}.png"
        if path.exists():
            return str(path)

        # Try just the name without suffix (e.g., "upload.png") -- base only
        if suffix == "base":
            path = button_dir / f"{prefix}.png"
            if path.exists():
                return str(path)
            path = button_dir / f"{prefix.replace('_', '-')}.png"
            if path.exists():
                return str(path)

        return None

    base_img = _find_image(name_underscore, "base")
    hover_img = _find_image(name_underscore, "hover") or base_img
    pressed_img = _find_image(name_underscore, "pressed") or base_img

    return base_img, hover_img, pressed_img


def get_config_summary() -> str:
    """
    Get a human-readable summary of the current configuration.
    Useful for logging at startup or debugging.

    Returns:
        Multi-line string with key configuration values.
    """
    return (
        f"RNV Color Palette Manager v{APP_VERSION}\n"
        f"  Base directory:   {BASE_DIR}\n"
        f"  Resources:        {RESOURCES_DIR} (exists={RESOURCES_DIR.exists()})\n"
        f"  User data:        {USER_DATA_DIR}\n"
        f"  Logs:             {LOGS_DIR}\n"
        f"  Debug mode:       {DEBUG_MODE}\n"
        f"  Image mode:       {ENABLE_IMAGE_MODE}\n"
    )


# ==================== Module Initialization ====================
# Create user data directories on first import.
ensure_directories()


# ==================== Exports ====================
__all__ = [
    # Application identity
    "APP_NAME",
    "APP_VERSION",
    "APP_AUTHOR",
    # Resource paths
    "BASE_DIR",
    "RESOURCES_DIR",
    "BUTTON_IMAGES_DIR",
    "BACKGROUND_IMAGES_DIR",
    "FONTS_DIR",
    "ICONS_DIR",
    # Direct file paths
    "APP_ICON_PATH",
    "SPECIAL_SLOT_ICON_PATH",
    "BACKGROUND_IMAGE_PATH",
    "FONT_PATH",
    # User data paths
    "USER_DATA_DIR",
    "LOGS_DIR",
    "SESSIONS_DIR",
    "EXPORT_HISTORY_PATH",
    # Window settings
    "MIN_WINDOW_WIDTH",
    "MIN_WINDOW_HEIGHT",
    "REF_WIDTH",
    "REF_HEIGHT",
    # Slot settings
    "MIN_SLOT_SIZE",
    "MAX_SLOT_SIZE",
    "MAX_SLOTS",
    # Image settings
    "MAX_IMAGE_DIMENSION",
    # Layout settings
    "SLOT_WIDGET_SPACING",
    # Logging settings
    "DEFAULT_LOG_LEVEL",
    "LOG_FILE_MAX_SIZE",
    "LOG_FILE_BACKUP_COUNT",
    "LOG_FORMAT",
    # Feature flags
    "DEBUG_MODE",
    "ENABLE_IMAGE_MODE",
    "ENABLE_THEME_CYCLING",
    "SHOW_TOOLTIPS",
    # Helper functions
    "ensure_directories",
    "get_resource_path",
    "resource_exists",
    "get_button_image_paths",
    "get_config_summary",
]