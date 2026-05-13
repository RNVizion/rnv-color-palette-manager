"""
Theme management for RNV Color Palette Manager.
Handles Dark Mode, Light Mode, and Image Mode themes.
Optimized for Python 3.13.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PyQt6.QtCore import QByteArray
from PyQt6.QtGui import QPixmap
from PIL import Image

from ui.colors import (
    ThemeName,
    ThemeDict,
    DARK_THEME_COLORS,
    LIGHT_THEME_COLORS,
    IMAGE_MODE_COLORS,
)
from utils.config import BACKGROUND_IMAGE_PATH, BUTTON_IMAGES_DIR, MAX_IMAGE_DIMENSION
from utils.logger import Logger, get_logger_instance

logger: Logger = get_logger_instance(__name__)


class ThemeManager:
    """Manages application themes with Dark Mode, Light Mode, and Image Mode"""

    # Reference theme dicts from centralized colors module
    DARK_THEME: ThemeDict = DARK_THEME_COLORS
    LIGHT_THEME: ThemeDict = LIGHT_THEME_COLORS
    IMAGE_THEME: ThemeDict = IMAGE_MODE_COLORS

    # Pre-built scrollbar styles — generated once from theme dicts at class load.
    # All color values come from the centralized colors module.
    @staticmethod
    def _build_scrollbar_style(theme: ThemeDict) -> str:
        """Generate a scrollbar stylesheet from a theme dictionary.

        Reads scrollbar_bg, scrollbar_handle, scrollbar_handle_hover,
        and scrollbar_border from the supplied theme dict.
        """
        bg = theme['scrollbar_bg']
        handle = theme['scrollbar_handle']
        handle_hover = theme['scrollbar_handle_hover']
        border = theme['scrollbar_border']

        return f"""
        QScrollBar:vertical {{
            background: {bg};
            width: 12px;
            margin: 0px;
            border: 1px solid {border};
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical {{
            background: {handle};
            min-height: 20px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {handle_hover};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        QScrollBar:horizontal {{
            background: {bg};
            height: 12px;
            margin: 0px;
            border: 1px solid {border};
            border-radius: 6px;
        }}
        QScrollBar::handle:horizontal {{
            background: {handle};
            min-width: 20px;
            border-radius: 5px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {handle_hover};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
    """

    # Class-level cached scrollbar styles (built from theme dicts)
    SCROLLBAR_DARK: str = _build_scrollbar_style.__func__(DARK_THEME_COLORS)
    SCROLLBAR_LIGHT: str = _build_scrollbar_style.__func__(LIGHT_THEME_COLORS)
    SCROLLBAR_IMAGE: str = _build_scrollbar_style.__func__(IMAGE_MODE_COLORS)

    def __init__(self) -> None:
        self.current_theme: ThemeName = 'dark'
        self.image_mode_available: bool = False
        self.image_mode_active: bool = False
        self.background_pixmap: QPixmap | None = None
        logger.info("ThemeManager initialized")

    def detect_image_resources(self) -> bool:
        """Check if custom images are available"""
        has_background = False

        if BACKGROUND_IMAGE_PATH.exists():
            try:
                img = Image.open(BACKGROUND_IMAGE_PATH)
                original_size = (img.width, img.height)

                if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
                    ratio = min(MAX_IMAGE_DIMENSION / img.width, MAX_IMAGE_DIMENSION / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    logger.info(
                        f"Resized background image "
                        f"({new_size[0]}x{new_size[1]})"
                    )

                buffer = QByteArray()
                bio = BytesIO()
                img.save(bio, format="PNG")
                buffer.append(bio.getvalue())

                pixmap = QPixmap()
                pixmap.loadFromData(buffer)

                self.background_pixmap = pixmap
                has_background = True
                logger.success(
                    f"Loaded background image "
                    f"({original_size[0]}x{original_size[1]})"
                )

            except Exception as e:
                logger.error(f"Failed to load background image: {e}")

        button_dir = Path(BUTTON_IMAGES_DIR)
        button_names = ['add', 'import', 'export', 'clear_all', 'reset', 'save']
        button_count = sum(
            1 for name in button_names
            if (button_dir / f"{name}.png").exists()
        )

        self.image_mode_available = has_background or button_count >= 3

        if self.image_mode_available:
            self.image_mode_active = True
            self.current_theme = 'image'
            logger.success(
                f"Image Mode available "
                f"(background: {has_background})"
            )
        else:
            logger.debug("Image Mode not available (missing resources)")

        return self.image_mode_available

    def cycle_theme(self) -> ThemeName:
        """Cycle through available themes"""
        if self.image_mode_available:
            match self.current_theme:
                case 'image':
                    self.current_theme = 'dark'
                    self.image_mode_active = False
                case 'dark':
                    self.current_theme = 'light'
                case _:  # 'light' or any other
                    self.current_theme = 'image'
                    self.image_mode_active = True
        else:
            self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'

        logger.debug(f"Theme cycled to: {self.current_theme}")
        return self.current_theme

    def get_current_theme(self) -> ThemeDict | None:
        """Get current theme dictionary"""
        match self.current_theme:
            case 'dark':
                return self.DARK_THEME
            case 'light':
                return self.LIGHT_THEME
            case 'image':
                return self.IMAGE_THEME
            case _:
                return None

    def get_theme_display_name(self) -> str:
        """Get display name for current theme"""
        match self.current_theme:
            case 'image':
                return "Image Mode"
            case 'dark':
                return "Dark Mode"
            case _:
                return "Light Mode"

    def is_image_mode(self) -> bool:
        """Check if image mode is active"""
        return self.image_mode_active