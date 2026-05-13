"""
Preview grid widget for displaying color palette overview.
Supports color blindness simulation for accessibility.
Optimized for Python 3.13.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPixmap

from core.accessibility import Accessibility
from utils.config import ICONS_DIR
from ui.colors import PREVIEW_GRID_BORDER

if TYPE_CHECKING:
    from core.color_slot import ColorSlot


class PreviewGrid(QWidget):
    """Widget that displays a grid preview of all color slots"""
    
    def __init__(self, slots: list[ColorSlot] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.slots: list[ColorSlot] = slots or []
        self._simulation_mode: str = "none"
        self.setMinimumSize(300, 400)

        icon_path = Path(ICONS_DIR) / "special_slot.png"
        self.special_image = QPixmap(str(icon_path))

    @property
    def simulation_mode(self) -> str:
        return self._simulation_mode

    @simulation_mode.setter
    def simulation_mode(self, mode: str) -> None:
        if mode != self._simulation_mode:
            self._simulation_mode = mode
            self.update()

    def setSlots(self, slots: list[ColorSlot]) -> None:
        """Update the slots to display"""
        self.slots = slots
        self.update()

    def _get_display_color(self, slot_color: QColor) -> QColor:
        """Get the color to display, applying simulation if active."""
        if self._simulation_mode == "none":
            return slot_color
        rgb = (slot_color.red(), slot_color.green(), slot_color.blue())
        sim = Accessibility.simulate(rgb, self._simulation_mode)
        return QColor(*sim)

    def paintEvent(self, event) -> None:
        """Paint the grid of color slots"""
        if not self.slots:
            return
        painter = QPainter(self)
        rect = self.contentsRect()

        n = len(self.slots)
        padding = 2

        total_slots = min(n, 100) if n >= 99 else n

        cols = math.ceil(math.sqrt(total_slots))
        rows = math.ceil(total_slots / cols)

        side_w = (rect.width() - (cols - 1) * padding) / cols
        side_h = (rect.height() - (rows - 1) * padding) / rows
        side = max(10, min(side_w, side_h))

        total_width = cols * side + (cols - 1) * padding
        total_height = rows * side + (rows - 1) * padding
        x_offset = (rect.width() - total_width) / 2
        y_offset = (rect.height() - total_height) / 2

        for idx, slot in enumerate(self.slots):
            row = idx // cols
            col = idx % cols
            x = x_offset + col * (side + padding)
            y = y_offset + row * (side + padding)
            
            # Check if slot has an image
            if hasattr(slot, 'image_pixmap') and slot.image_pixmap and not slot.image_pixmap.isNull():
                scaled_pixmap = slot.image_pixmap.scaled(
                    int(side), int(side),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                img_x = x + (side - scaled_pixmap.width()) / 2
                img_y = y + (side - scaled_pixmap.height()) / 2
                painter.drawPixmap(int(img_x), int(img_y), scaled_pixmap)
            else:
                # Draw solid color (with simulation if active)
                display_color = self._get_display_color(slot.color)
                painter.fillRect(int(x), int(y), int(side), int(side), display_color)
            
            # Draw border
            painter.setPen(QColor(*PREVIEW_GRID_BORDER))
            painter.drawRect(int(x), int(y), int(side), int(side))

        # Draw special 99+ indicator if needed
        if n >= 99:
            idx = 99
            row = idx // cols
            col = idx % cols
            x = x_offset + col * (side + padding)
            y = y_offset + row * (side + padding)
            if not self.special_image.isNull():
                painter.drawPixmap(int(x), int(y), int(side), int(side), self.special_image)
            else:
                painter.fillRect(int(x), int(y), int(side), int(side), QColor(*PREVIEW_GRID_BORDER))
                painter.setPen(QColor(*PREVIEW_GRID_BORDER))
                painter.drawRect(int(x), int(y), int(side), int(side))