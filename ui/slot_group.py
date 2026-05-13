"""
Slot Group data model and header widget for RNV Color Palette Manager.
Groups are a metadata layer — headers are inserted as spanning rows
in the main window's flat QGridLayout. No nested layouts.
Optimized for Python 3.13.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from utils.logger import Logger, get_logger_instance

logger: Logger = get_logger_instance(__name__)


# ==================== Data Model ====================

@dataclass
class SlotGroupData:
    """Serializable group metadata for session save/restore."""
    name: str = ""
    collapsed: bool = False
    slot_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "collapsed": self.collapsed,
            "slot_count": self.slot_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SlotGroupData:
        return cls(
            name=data.get("name", ""),
            collapsed=data.get("collapsed", False),
            slot_count=data.get("slot_count", 0),
        )


class SlotGroupInfo:
    """
    Pure data object tracking a named group of color slots.

    Does NOT own any widgets or layouts — it simply records:
    - name, collapsed state
    - slot_count (how many contiguous slots from the flat list belong here)
    - a header widget reference (created/managed by the main window)
    """

    def __init__(self, name: str = "", slot_count: int = 0) -> None:
        self.name: str = name
        self.collapsed: bool = False
        self.slot_count: int = slot_count
        self.header: SlotGroupHeader | None = None  # set by main window

    def to_data(self) -> SlotGroupData:
        return SlotGroupData(
            name=self.name,
            collapsed=self.collapsed,
            slot_count=self.slot_count,
        )

    @classmethod
    def from_data(cls, data: SlotGroupData) -> SlotGroupInfo:
        info = cls(name=data.name, slot_count=data.slot_count)
        info.collapsed = data.collapsed
        return info


# ==================== Group Header Widget ====================

class SlotGroupHeader(QFrame):
    """
    Lightweight header bar inserted as a grid-spanning row.
    Shows: [▼/▶ toggle] [editable name] [slot count] [× delete]
    """

    toggle_requested = pyqtSignal(object)      # emits the SlotGroupInfo
    name_changed = pyqtSignal(object, str)     # emits (SlotGroupInfo, new_name)
    delete_requested = pyqtSignal(object)      # emits the SlotGroupInfo
    add_slot_requested = pyqtSignal(object)    # emits the SlotGroupInfo

    def __init__(self, group_info: SlotGroupInfo, parent: QWidget | None = None):
        super().__init__(parent)
        self.group_info = group_info
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(28)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 8, 2)
        layout.setSpacing(6)

        # Toggle button
        self._toggle_btn = QPushButton("▼")
        self._toggle_btn.setFixedSize(22, 22)
        self._toggle_btn.setFlat(True)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setToolTip("Collapse / Expand group")
        self._toggle_btn.clicked.connect(
            lambda: self.toggle_requested.emit(self.group_info)
        )
        layout.addWidget(self._toggle_btn)

        # Editable name
        self._name_edit = QLineEdit(group_info.name)
        self._name_edit.setPlaceholderText("Unnamed Group")
        self._name_edit.setMaxLength(60)
        self._name_edit.setFrame(False)
        self._name_edit.setToolTip("Click to rename this group")
        self._name_edit.editingFinished.connect(self._on_name_edited)
        layout.addWidget(self._name_edit, stretch=1)

        # Slot count badge
        self._count_label = QLabel(str(group_info.slot_count))
        self._count_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._count_label.setFixedWidth(30)
        self._count_label.setToolTip("Number of slots in this group")
        layout.addWidget(self._count_label)

        # Add slot to this group button
        self._add_btn = QPushButton("+")
        self._add_btn.setFixedSize(22, 22)
        self._add_btn.setFlat(True)
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.setToolTip("Add a new color slot to this group")
        self._add_btn.clicked.connect(
            lambda: self.add_slot_requested.emit(self.group_info)
        )
        layout.addWidget(self._add_btn)

        # Delete group button
        self._delete_btn = QPushButton("×")
        self._delete_btn.setFixedSize(22, 22)
        self._delete_btn.setFlat(True)
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_btn.setToolTip("Delete this group (slots move to previous group)")
        self._delete_btn.clicked.connect(
            lambda: self.delete_requested.emit(self.group_info)
        )
        layout.addWidget(self._delete_btn)

        self._sync_visuals()

    # ------------------------------------------------------------------

    def _on_name_edited(self) -> None:
        new_name = self._name_edit.text()
        self.group_info.name = new_name
        self.name_changed.emit(self.group_info, new_name)

    def _sync_visuals(self) -> None:
        self._toggle_btn.setText("▶" if self.group_info.collapsed else "▼")
        self._count_label.setText(str(self.group_info.slot_count))
        self._name_edit.setText(self.group_info.name)

    def refresh(self) -> None:
        """Re-sync from group_info data."""
        self._sync_visuals()

    def set_delete_visible(self, visible: bool) -> None:
        self._delete_btn.setVisible(visible)

    def apply_theme(self, theme: dict[str, str]) -> None:
        text_color = theme["text_color"]
        border_color = theme["border_color"]
        panel_bg = theme["panel_bg"]

        self.setStyleSheet(f"""
            SlotGroupHeader {{
                background-color: {panel_bg};
                border: 1px solid {border_color};
                border-radius: 3px;
            }}
        """)
        btn_style = f"""
            QPushButton {{
                color: {text_color}; background: transparent;
                border: none; font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {border_color};
                border-radius: 3px;
            }}
        """
        self._toggle_btn.setStyleSheet(btn_style)
        self._add_btn.setStyleSheet(btn_style)
        self._delete_btn.setStyleSheet(btn_style)
        self._name_edit.setStyleSheet(f"""
            QLineEdit {{
                color: {text_color}; background: transparent;
                font-weight: bold; border: none;
            }}
        """)
        self._count_label.setStyleSheet(f"color: {text_color};")


__all__: list[str] = [
    "SlotGroupInfo",
    "SlotGroupData",
    "SlotGroupHeader",
]