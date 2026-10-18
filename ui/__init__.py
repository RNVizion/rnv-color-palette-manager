"""
UI modules for RNV Color Palette Manager.
Contains theme manager, buttons, dialogs, and UI widgets.
"""
from __future__ import annotations

from ui.theme_manager import ThemeManager
from ui.image_button import ImageButton
from ui.image_upload_dialog import ImageUploadDialog
from ui.preview_grid import PreviewGrid
from ui.zoomable_graphics_view import ZoomableGraphicsView
from ui.settings_dialog import SettingsDialog
from ui.about_dialog import AboutDialog
from ui.slot_group import SlotGroupInfo, SlotGroupData, SlotGroupHeader
from ui.color_search import ColorSearchBar
from ui.batch_export_dialog import BatchExportDialog, BatchExportResult

__all__ = [
    # Theme manager
    "ThemeManager",
    # Buttons & widgets
    "ImageButton",
    "PreviewGrid",
    "ZoomableGraphicsView",
    "ColorSearchBar",
    # Dialogs
    "ImageUploadDialog",
    "SettingsDialog",
    "AboutDialog",
    "BatchExportDialog",
    "BatchExportResult",
    # Slot groups
    "SlotGroupInfo",
    "SlotGroupData",
    "SlotGroupHeader",
]
