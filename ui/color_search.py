"""
Color Search & Filter bar for RNV Color Palette Manager.
Provides search by hex, RGB, color name, or group name.
Matching slots highlighted, non-matching dimmed.
Optimized for Python 3.13.
"""
from __future__ import annotations

import re

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QShortcut, QKeySequence

from core.color_math import ColorMath
from utils.logger import Logger, get_logger_instance

logger: Logger = get_logger_instance(__name__)

# CSS named colors (subset covering the most common names)
CSS_NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    "red": (255, 0, 0), "green": (0, 128, 0), "blue": (0, 0, 255),
    "white": (255, 255, 255), "black": (0, 0, 0), "yellow": (255, 255, 0),
    "cyan": (0, 255, 255), "magenta": (255, 0, 255), "orange": (255, 165, 0),
    "pink": (255, 192, 203), "purple": (128, 0, 128), "brown": (165, 42, 42),
    "gray": (128, 128, 128), "grey": (128, 128, 128),
    "navy": (0, 0, 128), "teal": (0, 128, 128), "maroon": (128, 0, 0),
    "olive": (128, 128, 0), "lime": (0, 255, 0), "aqua": (0, 255, 255),
    "silver": (192, 192, 192), "fuchsia": (255, 0, 255),
    "coral": (255, 127, 80), "salmon": (250, 128, 114),
    "gold": (255, 215, 0), "khaki": (240, 230, 140),
    "indigo": (75, 0, 130), "violet": (238, 130, 238),
    "plum": (221, 160, 221), "orchid": (218, 112, 214),
    "tan": (210, 180, 140), "beige": (245, 245, 220),
    "ivory": (255, 255, 240), "lavender": (230, 230, 250),
    "crimson": (220, 20, 60), "tomato": (255, 99, 71),
    "turquoise": (64, 224, 208), "sienna": (160, 82, 45),
    "chocolate": (210, 105, 30), "peru": (205, 133, 63),
    "wheat": (245, 222, 179), "linen": (250, 240, 230),
    "mint": (189, 252, 201), "peach": (255, 218, 185),
    "skyblue": (135, 206, 235), "steelblue": (70, 130, 180),
    "slategray": (112, 128, 144), "dimgray": (105, 105, 105),
    "darkred": (139, 0, 0), "darkgreen": (0, 100, 0),
    "darkblue": (0, 0, 139), "darkcyan": (0, 139, 139),
    "darkmagenta": (139, 0, 139), "darkorange": (255, 140, 0),
    "darkviolet": (148, 0, 211), "deeppink": (255, 20, 147),
    "deepskyblue": (0, 191, 255), "dodgerblue": (30, 144, 255),
    "firebrick": (178, 34, 34), "forestgreen": (34, 139, 34),
    "hotpink": (255, 105, 180), "lightblue": (173, 216, 230),
    "lightcoral": (240, 128, 128), "lightgreen": (144, 238, 144),
    "lightgray": (211, 211, 211), "lightgrey": (211, 211, 211),
    "lightpink": (255, 182, 193), "lightyellow": (255, 255, 224),
    "mediumblue": (0, 0, 205), "royalblue": (65, 105, 225),
    "seagreen": (46, 139, 87), "springgreen": (0, 255, 127),
    "darkgrey": (169, 169, 169), "darkgray": (169, 169, 169),
}

# Match distance threshold (Euclidean RGB distance)
# ~50 catches close matches without being too broad
MATCH_THRESHOLD: float = 50.0


class ColorSearchResult:
    """Result of a color search operation."""

    __slots__ = ("query", "target_rgb", "match_indices", "is_group_search")

    def __init__(self) -> None:
        self.query: str = ""
        self.target_rgb: tuple[int, int, int] | None = None
        self.match_indices: list[int] = []
        self.is_group_search: bool = False


def parse_color_query(query: str) -> tuple[int, int, int] | None:
    """
    Try to parse a search query as a color.

    Supports:
        - Hex: #ff0000, ff0000, #f00
        - RGB: 255,0,0  or  rgb(255,0,0)
        - Named: red, navy, coral
    Returns RGB tuple or None if not a color.
    """
    q = query.strip().lower()
    if not q:
        return None

    # Hex with or without #
    hex_match = re.match(r'^#?([0-9a-f]{6})$', q)
    if hex_match:
        return ColorMath.hex_to_rgb(f"#{hex_match.group(1)}")

    # Short hex (#f00)
    hex_short = re.match(r'^#?([0-9a-f]{3})$', q)
    if hex_short:
        h = hex_short.group(1)
        expanded = ''.join(c * 2 for c in h)
        return ColorMath.hex_to_rgb(f"#{expanded}")

    # RGB tuple: "255,0,0" or "255, 0, 0" or "rgb(255,0,0)"
    rgb_match = re.match(r'^(?:rgb\s*\()?\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)?$', q)
    if rgb_match:
        r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
        if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
            return (r, g, b)

    # Named color
    if q in CSS_NAMED_COLORS:
        return CSS_NAMED_COLORS[q]

    # Partial name match (e.g. "sky" matches "skyblue")
    for name, rgb in CSS_NAMED_COLORS.items():
        if q in name or name in q:
            return rgb

    return None


class ColorSearchBar(QFrame):
    """
    Collapsible search bar for filtering color slots.

    Signals:
        search_changed(str): Emitted when search text changes (debounced).
        search_cleared(): Emitted when search is cleared.
    """

    search_changed = pyqtSignal(str)
    search_cleared = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(32)
        self.setVisible(False)  # Start hidden

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        # Search icon / label
        self._icon_label = QLabel("🔍")
        self._icon_label.setFixedWidth(20)
        layout.addWidget(self._icon_label)

        # Search input
        self._input = QLineEdit()
        self._input.setPlaceholderText(
            "Search: hex (#ff0000), RGB (255,0,0), name (red), or group name..."
        )
        self._input.setClearButtonEnabled(True)
        self._input.setFrame(False)
        self._input.setToolTip("Search by hex, RGB, color name, or group name (Ctrl+F)")
        self._input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._input, stretch=1)

        # Match count label
        self._match_label = QLabel("")
        self._match_label.setFixedWidth(80)
        self._match_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self._match_label)

        # Close button
        self._close_btn = QPushButton("×")
        self._close_btn.setFixedSize(22, 22)
        self._close_btn.setFlat(True)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setToolTip("Close search (Esc)")
        self._close_btn.clicked.connect(self.close_search)
        layout.addWidget(self._close_btn)

        # Debounce timer for search-as-you-type
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(200)
        self._debounce.timeout.connect(self._emit_search)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def toggle(self) -> None:
        """Toggle visibility. Focus input when showing."""
        if self.isVisible():
            self.close_search()
        else:
            self.setVisible(True)
            self._input.setFocus()
            self._input.selectAll()

    def close_search(self) -> None:
        """Hide bar and clear search."""
        self._input.clear()
        self.setVisible(False)
        self.search_cleared.emit()

    def set_match_count(self, count: int, total: int) -> None:
        """Update the match count badge."""
        if count < 0:
            self._match_label.setText("")
        else:
            self._match_label.setText(f"{count}/{total}")

    def current_text(self) -> str:
        return self._input.text().strip()

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def apply_theme(self, theme: dict[str, str]) -> None:
        text_color = theme["text_color"]
        border_color = theme["border_color"]
        panel_bg = theme["panel_bg"]

        self.setStyleSheet(f"""
            ColorSearchBar {{
                background-color: {panel_bg};
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
        """)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                color: {text_color}; background: transparent;
                border: none; font-size: 12px;
            }}
        """)
        self._match_label.setStyleSheet(f"color: {text_color}; font-size: 11px;")
        self._icon_label.setStyleSheet(f"color: {text_color};")
        btn_style = f"""
            QPushButton {{
                color: {text_color}; background: transparent;
                border: none; font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {border_color}; border-radius: 3px;
            }}
        """
        self._close_btn.setStyleSheet(btn_style)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_text_changed(self, text: str) -> None:
        self._debounce.start()

    def _emit_search(self) -> None:
        text = self._input.text().strip()
        if text:
            self.search_changed.emit(text)
        else:
            self.search_cleared.emit()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close_search()
        else:
            super().keyPressEvent(event)