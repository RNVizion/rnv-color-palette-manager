"""
Custom button widget with image mode support for RNV Color Palette Manager.
Optimized for Python 3.13.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QPushButton, QWidget
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QIcon

if TYPE_CHECKING:
    from ui.theme_manager import ThemeManager


class ImageButton(QPushButton):
    """QPushButton that fully fills the button area with icon in Image Mode."""
    
    def __init__(
        self,
        text: str = "",
        base_img: str | None = None,
        hover_img: str | None = None,
        pressed_img: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)

        self.base_img = base_img
        self.hover_img = hover_img
        self.pressed_img = pressed_img
        self.theme_manager: ThemeManager | None = None
        self._icon: QIcon | None = None
        self._is_locked: bool = False  # Track locked state for toggle buttons
        self._is_pressed: bool = False  # Track if button is currently pressed
        self._always_use_images: bool = False  # Force image display in all themes

        font = self.font()
        font.setBold(True)
        self.setFont(font)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(28)
        
        # Enable mouse tracking to detect when mouse leaves during press
        self.setMouseTracking(True)

        # DON'T set icon here - wait for theme manager to be set
        # Icon will be set in apply_style() based on theme mode

        self.apply_style()

    @property
    def _use_images(self) -> bool:
        """Whether this button should display images (image mode or forced)."""
        if self._always_use_images:
            return True
        return bool(self.theme_manager and self.theme_manager.is_image_mode())

    def setIcon(self, icon: QIcon) -> None:
        """Store icon and repaint."""
        self._icon = icon
        super().setIcon(icon)
        self.update()
    
    def set_locked_state(self, is_locked: bool) -> None:
        """Set the locked state for toggle behavior in image mode"""
        self._is_locked = is_locked
        if self._use_images:
            if is_locked and self.pressed_img and Path(self.pressed_img).exists():
                self._icon = QIcon(self.pressed_img)
                self.setIcon(self._icon)
            elif not is_locked and self.base_img and Path(self.base_img).exists():
                self._icon = QIcon(self.base_img)
                self.setIcon(self._icon)

    def reset_hover_state(self) -> None:
        """Reset hover/press visual state after a drag operation.
        Called on all buttons when a slot drag ends so none get stuck
        in hover state (Qt does not fire leaveEvent during QDrag.exec).
        """
        self._is_pressed = False
        if self._use_images:
            if not self._is_locked and self.base_img and Path(self.base_img).exists():
                self._icon = QIcon(self.base_img)
                self.setIcon(self._icon)
        self.update()

    def paintEvent(self, event) -> None:
        """Custom paint for Image Mode - fill button with icon"""
        if self._use_images and self._icon:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            rect = self.rect()
            # Get pixmap and scale it to full rect ignoring aspect ratio
            pixmap = self._icon.pixmap(QSize(rect.width(), rect.height()))
            painter.drawPixmap(rect, pixmap)
        else:
            super().paintEvent(event)

    def enterEvent(self, event) -> None:
        if self._use_images:
            # Don't change image if locked
            if not self._is_locked:
                # If we're re-entering while pressed, show pressed image
                if self._is_pressed:
                    if self.pressed_img and Path(self.pressed_img).exists():
                        self._icon = QIcon(self.pressed_img)
                        self.setIcon(self._icon)
                else:
                    # Otherwise show hover image
                    if self.hover_img and Path(self.hover_img).exists():
                        self._icon = QIcon(self.hover_img)
                        self.setIcon(self._icon)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if self._use_images:
            # Don't change image if locked
            if not self._is_locked:
                # Always reset to base image when leaving the button area
                if self.base_img and Path(self.base_img).exists():
                    self._icon = QIcon(self.base_img)
                    self.setIcon(self._icon)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if self._use_images:
            # Don't change image if locked (already showing pressed state)
            if not self._is_locked:
                self._is_pressed = True
                if self.pressed_img and Path(self.pressed_img).exists():
                    self._icon = QIcon(self.pressed_img)
                    self.setIcon(self._icon)
        else:
            self._is_pressed = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._is_pressed = False
        if self._use_images:
            # Don't change image if locked
            if not self._is_locked:
                # Check if mouse is still over the button
                if self.rect().contains(event.pos()):
                    # Mouse is still over button, show hover image
                    if self.hover_img and Path(self.hover_img).exists():
                        self._icon = QIcon(self.hover_img)
                        self.setIcon(self._icon)
                else:
                    # Mouse is not over button, show base image
                    if self.base_img and Path(self.base_img).exists():
                        self._icon = QIcon(self.base_img)
                        self.setIcon(self._icon)
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse movement to detect when mouse leaves during press"""
        if self._use_images:
            if not self._is_locked and self._is_pressed:
                # Check if mouse is still within button bounds
                if not self.rect().contains(event.pos()):
                    # Mouse left button area while pressed, reset to base
                    if self.base_img and Path(self.base_img).exists():
                        self._icon = QIcon(self.base_img)
                        self.setIcon(self._icon)
                else:
                    # Mouse is still within bounds and pressed, show pressed image
                    if self.pressed_img and Path(self.pressed_img).exists():
                        self._icon = QIcon(self.pressed_img)
                        self.setIcon(self._icon)
        super().mouseMoveEvent(event)

    def set_theme_manager(self, theme_manager: ThemeManager) -> None:
        """Set theme manager for this button"""
        self.theme_manager = theme_manager
        self.apply_style()
        
        # Set icon only if in Image Mode
        if self._use_images:
            if self.base_img and Path(self.base_img).exists():
                self._icon = QIcon(self.base_img)
                self.setIcon(self._icon)

    def apply_style(self) -> None:
        """Apply current theme styling to this button"""
        if self._use_images:
            # IMAGE/ALWAYS-IMAGE MODE - Show icons
            theme = self.theme_manager.get_current_theme() if self.theme_manager else None
            
            # Set icon based on locked state
            if self._is_locked:
                # If locked, show pressed image
                if self.pressed_img and Path(self.pressed_img).exists():
                    self._icon = QIcon(self.pressed_img)
                    self.setIcon(self._icon)
            else:
                # If not locked, show base image
                if self.base_img and Path(self.base_img).exists():
                    self._icon = QIcon(self.base_img)
                    self.setIcon(self._icon)
            
            if theme:
                self.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {theme['button_bg']};
                        color: {theme['button_text']};
                        border: 1px solid {theme['border_color']};
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {theme['button_hover_bg']};
                        color: {theme.get('button_hover_text', theme['button_text'])};
                    }}
                    QPushButton:pressed {{
                        background-color: {theme.get('button_pressed_bg', theme['button_hover_bg'])};
                        color: {theme.get('button_pressed_text', theme['button_text'])};
                    }}
                """)
            return

        # DARK/LIGHT MODE - Remove icons, show text
        if self._icon:
            self.setIcon(QIcon())  # Clear the icon
            self._icon = None

        if not self.theme_manager:
            return

        theme = self.theme_manager.get_current_theme()
        if not theme:
            return

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['button_bg']};
                color: {theme['button_text']};
                border: 1px solid {theme['border_color']};
                padding: 2px 8px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover_bg']};
                color: {theme.get('button_hover_text', theme['button_text'])};
            }}
            QPushButton:pressed {{
                background-color: {theme.get('button_pressed_bg', theme['button_hover_bg'])};
                color: {theme.get('button_pressed_text', theme['button_text'])};
            }}
        """)