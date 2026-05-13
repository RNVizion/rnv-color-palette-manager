"""
Color History Panel for RNV Color Palette Manager.
Records color changes and displays them as a scrollable strip of swatches.
Click a swatch to copy its hex to clipboard.
Optimized for Python 3.13.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QApplication, QFrame, QToolTip,
)
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QPainter, QColor, QCursor

from utils.logger import Logger, get_logger_instance
from ui.colors import DATA_DEFAULT_COLOR, HISTORY_SWATCH_BORDER

logger: Logger = get_logger_instance(__name__)


# ==================== Data Model ====================

@dataclass
class ColorHistoryEntry:
    """A single recorded color change."""

    timestamp: str = ""
    old_color: str = DATA_DEFAULT_COLOR      # hex
    new_color: str = DATA_DEFAULT_COLOR      # hex
    slot_index: int = -1            # -1 = unknown

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ColorHistoryEntry:
        return cls(
            timestamp=data.get("timestamp", ""),
            old_color=data.get("old_color", DATA_DEFAULT_COLOR),
            new_color=data.get("new_color", DATA_DEFAULT_COLOR),
            slot_index=data.get("slot_index", -1),
        )

    @staticmethod
    def now() -> str:
        """Current timestamp as ISO string."""
        return datetime.now().isoformat(timespec="seconds")


# ==================== Swatch Widget ====================

class HistorySwatch(QWidget):
    """Small clickable color swatch for the history strip."""

    SWATCH_SIZE = 22

    def __init__(self, entry: ColorHistoryEntry, parent: QWidget | None = None):
        super().__init__(parent)
        self.entry = entry
        self.color = QColor(entry.new_color)
        self.setFixedSize(self.SWATCH_SIZE, self.SWATCH_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(
            f"{entry.new_color}\n"
            f"From: {entry.old_color}\n"
            f"Slot #{entry.slot_index + 1}"
        )

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill with the new color
        painter.fillRect(1, 1, self.width() - 2, self.height() - 2, self.color)

        # Border
        painter.setPen(QColor(*HISTORY_SWATCH_BORDER))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def mousePressEvent(self, event) -> None:
        """Copy hex to clipboard on click."""
        if event.button() == Qt.MouseButton.LeftButton:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(self.entry.new_color)
                QToolTip.showText(
                    QCursor.pos(),
                    f"Copied {self.entry.new_color}",
                    self,
                )
                logger.debug(f"Copied history color {self.entry.new_color} to clipboard")
        super().mousePressEvent(event)


# ==================== History Panel ====================

class ColorHistoryPanel(QFrame):
    """
    Collapsible panel showing a scrollable strip of recent color changes.

    Sits in the right panel below the preview grid. The header toggles
    collapse/expand and a clear button resets the history.
    """

    def __init__(self, max_entries: int = 100, parent: QWidget | None = None):
        super().__init__(parent)
        self._entries: list[ColorHistoryEntry] = []
        self._max_entries: int = max_entries
        self._collapsed: bool = False
        self._theme_manager = None

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # Main layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(4)

        # Header row
        header = QHBoxLayout()
        header.setSpacing(4)

        self._toggle_btn = QPushButton("▼ Color History")
        self._toggle_btn.setFlat(True)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._toggle_collapse)
        self._toggle_btn.setStyleSheet("font-weight: bold; text-align: left; padding: 2px;")
        header.addWidget(self._toggle_btn, stretch=1)

        self._count_label = QLabel("0")
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_label.setFixedWidth(30)
        self._count_label.setToolTip("Number of recorded color changes")
        header.addWidget(self._count_label)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedWidth(50)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.clicked.connect(self.clear)
        self._clear_btn.setToolTip("Clear color history")
        header.addWidget(self._clear_btn)

        self._layout.addLayout(header)

        # Scrollable swatch strip
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_area.setMinimumHeight(0)
        self._scroll_area.setMaximumHeight(120)

        self._swatch_container = QWidget()
        self._swatch_layout = QHBoxLayout(self._swatch_container)
        self._swatch_layout.setContentsMargins(2, 2, 2, 2)
        self._swatch_layout.setSpacing(3)
        self._swatch_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Enable horizontal wrapping via a flow-like layout
        self._swatch_container.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self._scroll_area.setWidget(self._swatch_container)
        self._layout.addWidget(self._scroll_area)

        # Start expanded
        self._update_header_text()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def entries(self) -> list[ColorHistoryEntry]:
        """Get all history entries (most recent first)."""
        return list(self._entries)

    @property
    def max_entries(self) -> int:
        return self._max_entries

    @max_entries.setter
    def max_entries(self, value: int) -> None:
        self._max_entries = max(10, min(500, value))
        self._trim()

    def record(
        self,
        old_color: str,
        new_color: str,
        slot_index: int = -1,
    ) -> None:
        """Record a color change in the history."""
        # Skip if colors are the same
        if old_color.lower() == new_color.lower():
            return

        entry = ColorHistoryEntry(
            timestamp=ColorHistoryEntry.now(),
            old_color=old_color,
            new_color=new_color,
            slot_index=slot_index,
        )
        self._entries.insert(0, entry)  # Most recent first
        self._trim()
        self._add_swatch(entry, prepend=True)
        self._update_header_text()

    def clear(self) -> None:
        """Clear all history entries and swatches."""
        self._entries.clear()
        self._clear_swatches()
        self._update_header_text()
        logger.debug("Color history cleared")

    def set_entries(self, entries: list[ColorHistoryEntry]) -> None:
        """Bulk-set entries (e.g. from session restore). Most-recent-first order."""
        self._entries = list(entries[: self._max_entries])
        self._rebuild_swatches()

    def to_list(self) -> list[dict[str, Any]]:
        """Serialize entries for session save."""
        return [e.to_dict() for e in self._entries]

    @staticmethod
    def entries_from_list(data: list[dict[str, Any]]) -> list[ColorHistoryEntry]:
        """Deserialize entries from session data."""
        return [ColorHistoryEntry.from_dict(d) for d in data]

    # ------------------------------------------------------------------
    # Theme support
    # ------------------------------------------------------------------

    def set_theme_manager(self, tm) -> None:
        self._theme_manager = tm
        self.apply_theme()

    def apply_theme(self) -> None:
        """Apply current theme styling."""
        if not self._theme_manager:
            return
        theme = self._theme_manager.get_current_theme()
        if not theme:
            return

        text_color = theme["text_color"]
        border_color = theme["border_color"]
        panel_bg = theme["panel_bg"]
        btn_bg = theme["button_bg"]
        btn_text = theme["button_text"]
        btn_hover = theme["button_hover_bg"]

        self.setStyleSheet(f"""
            ColorHistoryPanel {{
                border: 1px solid {border_color};
                background-color: {panel_bg};
            }}
        """)

        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                font-weight: bold;
                text-align: left;
                padding: 2px 4px;
                color: {text_color};
                background: transparent;
                border: none;
            }}
        """)
        self._count_label.setStyleSheet(f"color: {text_color};")

        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_text};
                border: 1px solid {border_color};
                border-radius: 3px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
        """)

        self._scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
        """)
        self._swatch_container.setStyleSheet("background: transparent;")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _trim(self) -> None:
        """Trim entries to max size."""
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[: self._max_entries]

    def _add_swatch(self, entry: ColorHistoryEntry, prepend: bool = False) -> None:
        """Add a single swatch widget."""
        swatch = HistorySwatch(entry)
        if prepend:
            self._swatch_layout.insertWidget(0, swatch)
        else:
            self._swatch_layout.addWidget(swatch)

        # Remove excess swatch widgets
        while self._swatch_layout.count() > self._max_entries:
            item = self._swatch_layout.takeAt(self._swatch_layout.count() - 1)
            if item and item.widget():
                item.widget().deleteLater()

    def _clear_swatches(self) -> None:
        """Remove all swatch widgets."""
        while self._swatch_layout.count():
            item = self._swatch_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _rebuild_swatches(self) -> None:
        """Rebuild all swatches from entries list."""
        self._clear_swatches()
        for entry in self._entries:
            self._add_swatch(entry)
        self._update_header_text()

    def _update_header_text(self) -> None:
        """Update the toggle button text and count."""
        arrow = "▶" if self._collapsed else "▼"
        self._toggle_btn.setText(f"{arrow} Color History")
        self._count_label.setText(str(len(self._entries)))

    def _toggle_collapse(self) -> None:
        """Toggle the swatch strip visibility."""
        self._collapsed = not self._collapsed
        self._scroll_area.setVisible(not self._collapsed)
        self._update_header_text()


# ==================== Module Exports ====================

__all__: list[str] = [
    "ColorHistoryEntry",
    "ColorHistoryPanel",
]