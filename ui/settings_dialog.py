"""
RNV Color Palette Manager - Settings Dialog
Modal tabbed dialog for application preferences.

Tabs:
- General: Starting slot count, default color, auto-save settings
- Appearance: Slot borders, size, overlay visibility
- Export: Default format, default directory, clipboard format
- Display: Color info, accessibility simulation
- Details: Palette name, notes/description, author
- History: Color change history panel with max size setting

Optimized for Python 3.13.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QCheckBox, QLabel, QGridLayout, QSpinBox,
    QComboBox, QPushButton, QDoubleSpinBox, QColorDialog,
    QFrame, QListView, QLineEdit, QPlainTextEdit, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from core.palette_metadata import PaletteMetadata
from utils.logger import Logger, get_logger_instance
from utils.font_loader import get_font_family
from ui.colors import (
    BRAND_GOLD, BRAND_GOLD_DARK,
    ACCENT_PRESSED_TEXT_DARK, ACCENT_PRESSED_TEXT_LIGHT,
    SESSION_FALLBACK_COLOR, IMAGE_PREVIEW_BORDER,
)

if TYPE_CHECKING:
    from utils.settings_manager import SettingsManager
    from utils.export_history import ExportHistory

logger: Logger = get_logger_instance(__name__)


class SettingsDialog(QDialog):
    """
    Tabbed settings dialog for RNV Color Palette Manager.

    Reads current values from SettingsManager on open, writes
    them back on Apply or OK.

    Signals:
        settings_applied: Emitted when user clicks Apply or OK.
        auto_save_changed: Emitted with (enabled, interval_ms) when
            auto-save settings are modified.
        clear_history_requested: Emitted when user clicks Clear History.
    """

    settings_applied = pyqtSignal()
    auto_save_changed = pyqtSignal(bool, int)  # enabled, interval_ms
    clear_history_requested = pyqtSignal()

    def __init__(
        self,
        settings: SettingsManager,
        export_history: ExportHistory | None = None,
        parent: QWidget | None = None,
        theme_manager=None,
        palette_metadata: PaletteMetadata | None = None,
        color_history_panel=None,
        recent_palettes=None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.export_history = export_history
        self.theme_manager = theme_manager
        self.palette_metadata = palette_metadata or PaletteMetadata()
        self._color_history_panel = color_history_panel
        self._recent_palettes = recent_palettes

        self.setWindowTitle("Settings")
        self.setMinimumSize(520, 620)
        self.setMaximumSize(520, 620)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._build_ui()
        self._load_from_settings()
        self._apply_theme()

        logger.debug("Settings dialog created")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.tabBar().setUsesScrollButtons(False)
        self.general_tab = self._create_general_tab()
        self.appearance_tab = self._create_appearance_tab()
        self.export_tab = self._create_export_tab()
        self.display_tab = self._create_display_tab()
        self.details_tab = self._create_details_tab()

        self.tabs.addTab(self.general_tab, "General")
        self.tabs.addTab(self.appearance_tab, "Appearance")
        self.tabs.addTab(self.export_tab, "Export")
        self.tabs.addTab(self.display_tab, "Display")
        self.tabs.addTab(self.details_tab, "Details")

        # History tab (embeds the live color history panel)
        self.history_tab = self._create_history_tab()
        self.tabs.addTab(self.history_tab, "History")
        layout.addWidget(self.tabs)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_reset = QPushButton("Reset Defaults")
        self.btn_reset.setToolTip("Reset all settings to factory defaults")
        self.btn_reset.clicked.connect(self._on_reset)
        btn_layout.addWidget(self.btn_reset)

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setToolTip("Apply changes without closing")
        self.btn_apply.clicked.connect(self._on_apply)
        btn_layout.addWidget(self.btn_apply)

        self.btn_ok = QPushButton("OK")
        self.btn_ok.setToolTip("Apply changes and close")
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self._on_ok)
        btn_layout.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setToolTip("Discard changes and close")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # General tab
    # ------------------------------------------------------------------

    def _create_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # -- Slot defaults group --
        slot_group = QGroupBox("Slot Defaults")
        slot_grid = QGridLayout(slot_group)
        slot_grid.setSpacing(8)

        slot_grid.addWidget(QLabel("Starting rows:"), 0, 0)
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 10)
        self.spin_rows.setToolTip("Number of rows for the starting color grid")
        slot_grid.addWidget(self.spin_rows, 0, 1)

        slot_grid.addWidget(QLabel("Starting columns:"), 1, 0)
        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(1, 10)
        self.spin_cols.setToolTip("Number of columns for the starting color grid")
        slot_grid.addWidget(self.spin_cols, 1, 1)

        # Determine current theme display name for label
        theme_name = ""
        if self.theme_manager:
            match self.theme_manager.current_theme:
                case 'dark':
                    theme_name = " (Dark)"
                case 'light':
                    theme_name = " (Light)"
                case 'image':
                    theme_name = " (Image)"
        self.lbl_default_color = QLabel(f"Default color{theme_name}:")
        slot_grid.addWidget(self.lbl_default_color, 2, 0)
        color_row = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(28, 28)
        self.color_preview.setFrameShape(QFrame.Shape.Box)
        self._default_color = SESSION_FALLBACK_COLOR
        self._update_color_preview()
        color_row.addWidget(self.color_preview)

        self.btn_pick_color = QPushButton("Choose...")
        self.btn_pick_color.setMinimumWidth(90)
        self.btn_pick_color.setToolTip("Choose the default color for new slots")
        self.btn_pick_color.clicked.connect(self._pick_default_color)
        color_row.addWidget(self.btn_pick_color)
        color_row.addStretch()
        slot_grid.addLayout(color_row, 2, 1)

        self.chk_single_click = QCheckBox("Single-click to edit color")
        self.chk_single_click.setToolTip(
            "On: click opens color picker (default)\n"
            "Off: click selects slot, double-click edits"
        )
        slot_grid.addWidget(self.chk_single_click, 3, 0, 1, 2)

        layout.addWidget(slot_group)

        # -- Auto-save group --
        save_group = QGroupBox("Session Auto-Save")
        save_layout = QGridLayout(save_group)
        save_layout.setSpacing(8)

        self.chk_auto_save = QCheckBox("Enable auto-save")
        self.chk_auto_save.setToolTip("Automatically save your session at regular intervals")
        save_layout.addWidget(self.chk_auto_save, 0, 0, 1, 2)

        save_layout.addWidget(QLabel("Interval (minutes):"), 1, 0)
        self.spin_interval = QDoubleSpinBox()
        self.spin_interval.setRange(1.0, 60.0)
        self.spin_interval.setSingleStep(0.5)
        self.spin_interval.setDecimals(1)
        self.spin_interval.setToolTip("Auto-save frequency in minutes")
        save_layout.addWidget(self.spin_interval, 1, 1)

        self.chk_auto_restore = QCheckBox("Restore last session on startup")
        self.chk_auto_restore.setToolTip("Reload your previous session when the app starts")
        save_layout.addWidget(self.chk_auto_restore, 2, 0, 1, 2)

        layout.addWidget(save_group)
        layout.addStretch()

        return tab

    # ------------------------------------------------------------------
    # Appearance tab
    # ------------------------------------------------------------------

    def _create_appearance_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # -- Slot appearance group --
        slot_group = QGroupBox("Slot Appearance")
        slot_grid = QGridLayout(slot_group)
        slot_grid.setSpacing(8)

        slot_grid.addWidget(QLabel("Border style:"), 0, 0)
        self.combo_border_style = QComboBox()
        self.combo_border_style.setView(QListView())
        self.combo_border_style.addItems(["none", "thin", "thick"])
        self.combo_border_style.setToolTip(
            "none: No visible border around slots\n"
            "thin: 1px border (default)\n"
            "thick: 2px border"
        )
        slot_grid.addWidget(self.combo_border_style, 0, 1)

        slot_grid.addWidget(QLabel("Size preference:"), 1, 0)
        self.combo_size_pref = QComboBox()
        self.combo_size_pref.setView(QListView())
        self.combo_size_pref.addItems(["auto", "small", "medium", "large"])
        self.combo_size_pref.setToolTip(
            "auto: Dynamic sizing based on window size (default)\n"
            "small: Fixed 80px slots\n"
            "medium: Fixed 100px slots\n"
            "large: Fixed 140px slots"
        )
        slot_grid.addWidget(self.combo_size_pref, 1, 1)

        layout.addWidget(slot_group)

        # -- Layout group --
        layout_group = QGroupBox("Layout")
        layout_grid = QGridLayout(layout_group)
        layout_grid.setSpacing(8)

        self.chk_show_overlay = QCheckBox("Show size percentage overlay")
        self.chk_show_overlay.setToolTip(
            "Show or hide the window size percentage\n"
            "indicator in the top-left corner."
        )
        layout_grid.addWidget(self.chk_show_overlay, 0, 0, 1, 2)

        layout.addWidget(layout_group)
        layout.addStretch()

        return tab

    # ------------------------------------------------------------------
    # Export tab
    # ------------------------------------------------------------------

    def _create_export_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # -- Format group --
        fmt_group = QGroupBox("Default Export Format")
        fmt_layout = QGridLayout(fmt_group)
        fmt_layout.setSpacing(8)

        fmt_layout.addWidget(QLabel("Format:"), 0, 0)
        self.combo_format = QComboBox()
        self.combo_format.setView(QListView())
        self.combo_format.setToolTip("Default file format for palette exports")
        self.combo_format.addItems([
            ".json", ".ase", ".aco", ".acb", ".gpl",
            ".swatches", ".afpalette", ".clr", ".colors",
            ".css", ".xml", ".svg", ".hex", ".hsv",
            ".hsl", ".txt",
        ])
        fmt_layout.addWidget(self.combo_format, 0, 1)

        layout.addWidget(fmt_group)

        # -- Clipboard group --
        clip_group = QGroupBox("Clipboard Format")
        clip_layout = QGridLayout(clip_group)
        clip_layout.setSpacing(8)

        clip_layout.addWidget(QLabel("Copy format:"), 0, 0)
        self.combo_clipboard = QComboBox()
        self.combo_clipboard.setView(QListView())
        self.combo_clipboard.setToolTip("Format used when copying colors to clipboard (Ctrl+C)")
        self.combo_clipboard.addItems(["hex", "rgb", "hsl"])
        clip_layout.addWidget(self.combo_clipboard, 0, 1)

        self.lbl_clipboard_preview = QLabel("")
        self.lbl_clipboard_preview.setStyleSheet("color: grey; font-style: italic;")
        clip_layout.addWidget(self.lbl_clipboard_preview, 1, 0, 1, 2)
        self.combo_clipboard.currentTextChanged.connect(self._update_clipboard_preview)

        layout.addWidget(clip_group)

        # -- Export history group --
        hist_group = QGroupBox("Export History")
        hist_layout = QVBoxLayout(hist_group)

        self.lbl_history_count = QLabel("No exports recorded")
        hist_layout.addWidget(self.lbl_history_count)

        self.btn_clear_history = QPushButton("Clear History")
        self.btn_clear_history.setFixedWidth(150)
        self.btn_clear_history.setToolTip("Clear all export history records")
        self.btn_clear_history.clicked.connect(self._on_clear_history)
        hist_layout.addWidget(self.btn_clear_history)

        layout.addWidget(hist_group)

        # -- Recent Palettes group --
        recent_group = QGroupBox("Recent Palettes")
        recent_layout = QGridLayout(recent_group)
        recent_layout.setSpacing(8)

        recent_layout.addWidget(QLabel("Max recent entries:"), 0, 0)
        self.combo_max_recent = QComboBox()
        self.combo_max_recent.setView(QListView())
        self.combo_max_recent.setToolTip("Maximum number of recent palettes to remember")
        self.combo_max_recent.addItems(["5", "10", "20"])
        recent_layout.addWidget(self.combo_max_recent, 0, 1)

        self.lbl_recent_count = QLabel("No recent palettes")
        recent_layout.addWidget(self.lbl_recent_count, 1, 0, 1, 2)

        self.btn_clear_recent = QPushButton("Clear Recent List")
        self.btn_clear_recent.setFixedWidth(160)
        self.btn_clear_recent.setToolTip("Remove all entries from the recent palettes list")
        self.btn_clear_recent.clicked.connect(self._on_clear_recent)
        recent_layout.addWidget(self.btn_clear_recent, 2, 0, 1, 2)

        layout.addWidget(recent_group)
        layout.addStretch()

        return tab

    # ------------------------------------------------------------------
    # Display tab (reserved for Phase 5)
    # ------------------------------------------------------------------

    def _create_display_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        info_group = QGroupBox("Color Information")
        info_layout = QVBoxLayout(info_group)

        self.chk_show_color_info = QCheckBox(
            "Show expanded color info under slots (RGB, HSL)"
        )
        self.chk_show_color_info.setToolTip("Display additional color values below each slot")
        info_layout.addWidget(self.chk_show_color_info)

        layout.addWidget(info_group)

        # Color blindness simulation
        a11y_group = QGroupBox("Accessibility")
        a11y_layout = QGridLayout(a11y_group)
        a11y_layout.setSpacing(8)

        a11y_layout.addWidget(QLabel("Simulate color blindness:"), 0, 0)
        self.combo_blindness = QComboBox()
        self.combo_blindness.setView(QListView())
        self.combo_blindness.addItems([
            "none", "protanopia", "deuteranopia",
            "tritanopia", "achromatopsia",
        ])
        self.combo_blindness.setToolTip(
            "Preview grid shows how the palette looks\n"
            "under different color vision deficiencies.\n"
            "Actual slot colors are not changed."
        )
        a11y_layout.addWidget(self.combo_blindness, 0, 1)

        layout.addWidget(a11y_group)
        layout.addStretch()

        return tab

    # ------------------------------------------------------------------
    # Details tab
    # ------------------------------------------------------------------

    def _create_details_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # -- Palette identity group --
        identity_group = QGroupBox("Palette Identity")
        id_layout = QGridLayout(identity_group)
        id_layout.setSpacing(8)

        id_layout.addWidget(QLabel("Palette name:"), 0, 0)
        self.edit_palette_name = QLineEdit()
        self.edit_palette_name.setPlaceholderText("Untitled Palette")
        self.edit_palette_name.setMaxLength(120)
        self.edit_palette_name.setToolTip("Name for this palette (used in exports)")
        id_layout.addWidget(self.edit_palette_name, 0, 1)

        id_layout.addWidget(QLabel("Author:"), 1, 0)
        self.edit_author = QLineEdit()
        self.edit_author.setPlaceholderText("(optional)")
        self.edit_author.setMaxLength(80)
        self.edit_author.setToolTip("Author name embedded in exported palette files")
        id_layout.addWidget(self.edit_author, 1, 1)

        layout.addWidget(identity_group)

        # -- Notes group --
        notes_group = QGroupBox("Notes / Description")
        notes_layout = QVBoxLayout(notes_group)

        self.edit_notes = QPlainTextEdit()
        self.edit_notes.setPlaceholderText("Add palette notes or description...")
        self.edit_notes.setMinimumHeight(100)
        self.edit_notes.setTabChangesFocus(True)
        self.edit_notes.setToolTip("Optional notes or description for this palette")
        notes_layout.addWidget(self.edit_notes)

        layout.addWidget(notes_group)

        # -- Timestamps (read-only info) --
        info_group = QGroupBox("Info")
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(6)

        info_layout.addWidget(QLabel("Created:"), 0, 0)
        self.lbl_created = QLabel("—")
        self.lbl_created.setStyleSheet("color: grey; font-style: italic;")
        info_layout.addWidget(self.lbl_created, 0, 1)

        info_layout.addWidget(QLabel("Last modified:"), 1, 0)
        self.lbl_modified = QLabel("—")
        self.lbl_modified.setStyleSheet("color: grey; font-style: italic;")
        info_layout.addWidget(self.lbl_modified, 1, 1)

        layout.addWidget(info_group)
        layout.addStretch()

        return tab

    # ------------------------------------------------------------------
    # History tab
    # ------------------------------------------------------------------

    def _create_history_tab(self) -> QWidget:
        from utils.color_history import HistorySwatch, ColorHistoryEntry

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # Settings group
        settings_group = QGroupBox("History Settings")
        settings_layout = QGridLayout(settings_group)
        settings_layout.setSpacing(8)

        settings_layout.addWidget(QLabel("Max history entries:"), 0, 0)
        self.combo_history_size = QComboBox()
        self.combo_history_size.setView(QListView())
        self.combo_history_size.addItems(["50", "100", "200"])
        self.combo_history_size.setToolTip(
            "Maximum number of color changes to remember.\n"
            "Older entries are discarded when the limit is reached."
        )
        settings_layout.addWidget(self.combo_history_size, 0, 1)

        layout.addWidget(settings_group)

        # Header with count and clear button
        header = QHBoxLayout()
        header.setSpacing(4)

        entries: list[ColorHistoryEntry] = []
        if self._color_history_panel is not None:
            entries = self._color_history_panel.entries

        count_label = QLabel(f"Recorded changes: {len(entries)}")
        count_label.setStyleSheet("font-weight: bold;")
        header.addWidget(count_label, stretch=1)

        clear_btn = QPushButton("Clear History")
        clear_btn.setFixedWidth(150)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setToolTip("Clear all color history")
        clear_btn.clicked.connect(self._on_clear_history)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # Scrollable grid of swatches (read-only snapshot)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Use a grid layout for wrapping swatches
        swatch_container = QWidget()
        self._history_grid = QGridLayout(swatch_container)
        self._history_grid.setContentsMargins(4, 4, 4, 4)
        self._history_grid.setSpacing(4)

        cols = 16
        for i, entry in enumerate(entries):
            swatch = HistorySwatch(entry)
            self._history_grid.addWidget(swatch, i // cols, i % cols)

        if not entries:
            placeholder = QLabel("No color changes recorded yet.")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: grey; font-style: italic;")
            self._history_grid.addWidget(placeholder, 0, 0, 1, cols)

        scroll.setWidget(swatch_container)
        layout.addWidget(scroll, stretch=1)

        self._history_count_label = count_label

        return tab

    def _on_clear_history(self) -> None:
        """Clear the history panel and update the display."""
        if self._color_history_panel is not None:
            self._color_history_panel.clear()
        # Clear the swatch grid
        if hasattr(self, '_history_grid'):
            while self._history_grid.count():
                item = self._history_grid.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
            placeholder = QLabel("No color changes recorded yet.")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: grey; font-style: italic;")
            self._history_grid.addWidget(placeholder, 0, 0, 1, 16)
        if hasattr(self, '_history_count_label'):
            self._history_count_label.setText("Recorded changes: 0")

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def _load_from_settings(self) -> None:
        """Populate widgets from current SettingsManager values."""
        self.spin_rows.setValue(self.settings.starting_rows)
        self.spin_cols.setValue(self.settings.starting_cols)

        self._default_color = self.settings.default_slot_color_for_theme(
            self._current_theme_name()
        )
        self._update_color_preview()

        self.chk_auto_save.setChecked(self.settings.auto_save_enabled)
        self.spin_interval.setValue(self.settings.auto_save_interval)
        self.chk_auto_restore.setChecked(self.settings.auto_restore_session)
        self.chk_single_click.setChecked(self.settings.single_click_edit)

        idx = self.combo_format.findText(self.settings.last_export_format)
        if idx >= 0:
            self.combo_format.setCurrentIndex(idx)

        idx = self.combo_clipboard.findText(self.settings.clipboard_format)
        if idx >= 0:
            self.combo_clipboard.setCurrentIndex(idx)
        self._update_clipboard_preview(self.settings.clipboard_format)

        self.chk_show_color_info.setChecked(self.settings.show_color_info)

        idx = self.combo_blindness.findText(self.settings.color_blindness_mode)
        if idx >= 0:
            self.combo_blindness.setCurrentIndex(idx)

        # Appearance tab
        idx = self.combo_border_style.findText(self.settings.slot_border_style)
        if idx >= 0:
            self.combo_border_style.setCurrentIndex(idx)

        idx = self.combo_size_pref.findText(self.settings.slot_size_preference)
        if idx >= 0:
            self.combo_size_pref.setCurrentIndex(idx)

        self.chk_show_overlay.setChecked(self.settings.show_size_overlay)

        # Display tab
        idx = self.combo_history_size.findText(str(self.settings.max_history_size))
        if idx >= 0:
            self.combo_history_size.setCurrentIndex(idx)

        # Export history count
        if self.export_history:
            count = self.export_history.count
            self.lbl_history_count.setText(
                f"{count} {'entry' if count == 1 else 'entries'} recorded"
                if count > 0 else "No exports recorded"
            )

        # Recent palettes
        idx = self.combo_max_recent.findText(str(self.settings.max_recent_palettes))
        if idx >= 0:
            self.combo_max_recent.setCurrentIndex(idx)

        if self._recent_palettes:
            rcount = len(self._recent_palettes.entries)
            self.lbl_recent_count.setText(
                f"{rcount} recent {'palette' if rcount == 1 else 'palettes'}"
                if rcount > 0 else "No recent palettes"
            )

        # Details tab -- palette metadata
        self.edit_palette_name.setText(self.palette_metadata.name)
        self.edit_author.setText(self.palette_metadata.author)
        self.edit_notes.setPlainText(self.palette_metadata.description)
        self.lbl_created.setText(
            self.palette_metadata.created_at or "—"
        )
        self.lbl_modified.setText(
            self.palette_metadata.modified_at or "—"
        )

    def _save_to_settings(self) -> None:
        """Write widget values back to SettingsManager."""
        self.settings.starting_rows = self.spin_rows.value()
        self.settings.starting_cols = self.spin_cols.value()
        self.settings.set_default_slot_color_for_theme(
            self._current_theme_name(), self._default_color
        )
        self.settings.auto_save_enabled = self.chk_auto_save.isChecked()
        self.settings.auto_save_interval = self.spin_interval.value()
        self.settings.auto_restore_session = self.chk_auto_restore.isChecked()
        self.settings.single_click_edit = self.chk_single_click.isChecked()
        self.settings.last_export_format = self.combo_format.currentText()
        self.settings.clipboard_format = self.combo_clipboard.currentText()
        self.settings.show_color_info = self.chk_show_color_info.isChecked()
        self.settings.color_blindness_mode = self.combo_blindness.currentText()
        self.settings.slot_border_style = self.combo_border_style.currentText()
        self.settings.slot_size_preference = self.combo_size_pref.currentText()
        self.settings.show_size_overlay = self.chk_show_overlay.isChecked()
        self.settings.max_history_size = int(self.combo_history_size.currentText())

        # Recent palettes max count
        new_max = int(self.combo_max_recent.currentText())
        self.settings.max_recent_palettes = new_max
        if self._recent_palettes:
            self._recent_palettes.max_entries = new_max

        self.settings.sync()

        # Details tab -- write back to the palette metadata object
        self.palette_metadata.name = self.edit_palette_name.text().strip()
        self.palette_metadata.author = self.edit_author.text().strip()
        self.palette_metadata.description = self.edit_notes.toPlainText()
        self.palette_metadata.touch()

        logger.info("Settings saved")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _current_theme_name(self) -> str:
        """Get the current theme name from theme manager."""
        if self.theme_manager:
            return self.theme_manager.current_theme
        return 'dark'

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _on_apply(self) -> None:
        """Apply settings without closing."""
        self._save_to_settings()
        self.auto_save_changed.emit(
            self.chk_auto_save.isChecked(),
            int(self.spin_interval.value() * 60 * 1000),
        )
        self.settings_applied.emit()

    def _on_ok(self) -> None:
        """Apply settings and close."""
        self._on_apply()
        self.accept()

    def _on_reset(self) -> None:
        """Reset all settings to defaults."""
        self.settings.reset_to_defaults()
        self._load_from_settings()
        logger.info("Settings reset to defaults from dialog")

    def _on_clear_history(self) -> None:
        """Clear export history."""
        self.clear_history_requested.emit()
        if self.export_history:
            self.export_history.clear()
            self.lbl_history_count.setText("No exports recorded")

    def _on_clear_recent(self) -> None:
        """Clear recent palettes list."""
        if self._recent_palettes:
            self._recent_palettes.clear()
            self.lbl_recent_count.setText("No recent palettes")

    def _pick_default_color(self) -> None:
        """Open color picker for default slot color."""
        color = QColorDialog.getColor(
            QColor(self._default_color), self, "Default Slot Color"
        )
        if color.isValid():
            self._default_color = color.name()
            self._update_color_preview()

    def _update_color_preview(self) -> None:
        """Update the color preview swatch."""
        self.color_preview.setStyleSheet(
            f"background-color: {self._default_color}; border: 1px solid {IMAGE_PREVIEW_BORDER};"
        )

    def _update_clipboard_preview(self, fmt: str = "") -> None:
        """Show a preview of the clipboard format."""
        if not fmt:
            fmt = self.combo_clipboard.currentText()
        match fmt:
            case "hex":
                self.lbl_clipboard_preview.setText("Example: #4a90d9")
            case "rgb":
                self.lbl_clipboard_preview.setText("Example: rgb(74, 144, 217)")
            case "hsl":
                self.lbl_clipboard_preview.setText("Example: hsl(211 deg, 64%, 57%)")
            case _:
                self.lbl_clipboard_preview.setText("")

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_theme(self) -> None:
        """Apply current theme styling to the dialog with brand accents."""
        if not self.theme_manager:
            return

        theme = self.theme_manager.get_current_theme()
        if not theme:
            return

        # Image mode uses dark theme for settings panel (solid, readable)
        if self.theme_manager.is_image_mode():
            from ui.theme_manager import ThemeManager
            theme = ThemeManager.DARK_THEME

        # Brand gold constants from centralized colors module
        GOLD = BRAND_GOLD
        GOLD_DARK = BRAND_GOLD_DARK
        card_bg = theme.get('card_bg', theme['panel_bg'])
        input_bg = theme.get('input_bg', theme.get('card_bg', theme['button_bg']))
        text_secondary = theme.get('text_secondary', theme['text_color'])
        text_disabled = theme['text_disabled']

        # Button hover/pressed per theme:
        # Dark/image: hover = bg stays, gold text+border; press = gold bg, black text
        # Light:      hover = bg stays, dark-gold text+border; press = dark-gold bg, white text
        is_light = (self.theme_manager.current_theme == 'light')
        if is_light:
            accent = GOLD_DARK
            accent_dark = GOLD_DARK
            btn_hover_bg = card_bg                         # white stays
            btn_hover_text = GOLD_DARK                     # dark gold
            btn_hover_border = GOLD_DARK                   # dark gold
            btn_pressed_bg = GOLD_DARK                     # dark gold bg
            btn_pressed_text = ACCENT_PRESSED_TEXT_LIGHT   # white text
            btn_pressed_border = GOLD_DARK                 # unchanged
        else:
            accent = GOLD
            accent_dark = GOLD_DARK
            btn_hover_bg = card_bg                         # dark stays
            btn_hover_text = GOLD                          # gold
            btn_hover_border = GOLD                        # gold
            btn_pressed_bg = GOLD                          # gold bg
            btn_pressed_text = ACCENT_PRESSED_TEXT_DARK    # black text
            btn_pressed_border = GOLD                      # unchanged

        font_family = get_font_family()

        self.setStyleSheet(f"""
            /* ---- Dialog base ---- */
            QDialog {{
                background-color: {theme['panel_bg']};
                color: {theme['text_color']};
                font-family: '{font_family}';
            }}

            /* ---- Tab Widget ---- */
            QTabWidget::pane {{
                border: 1px solid {theme['border_color']};
                background-color: {theme['panel_bg']};
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: {card_bg};
                color: {theme['text_color']};
                padding: 6px 12px;
                border: 1px solid {theme['border_color']};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }}
            QTabBar::scroller {{
                width: 0px;
            }}
            QTabBar QToolButton {{
                width: 0px;
                border: none;
                background: none;
            }}
            QTabBar::tab:selected {{
                background-color: {theme['panel_bg']};
                color: {accent};
                border-bottom: 2px solid {accent};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {card_bg};
                color: {accent};
            }}

            /* ---- Group Boxes (gold titles) ---- */
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme['border_color']};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 18px;
                color: {accent};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: {accent};
            }}

            /* ---- Labels ---- */
            QLabel {{
                color: {theme['text_color']};
            }}

            /* ---- Checkboxes (gold checked state) ---- */
            QCheckBox {{
                color: {theme['text_color']};
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {theme['border_color']};
                border-radius: 3px;
                background-color: {input_bg};
            }}
            QCheckBox::indicator:hover {{
                border-color: {accent};
            }}
            QCheckBox::indicator:checked {{
                background-color: {accent};
                border-color: {accent_dark};
                image: none;
            }}

            /* ---- Inputs (spinbox, combo, line edit, text edit) ---- */
            QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit, QPlainTextEdit {{
                background-color: {input_bg};
                color: {theme['text_color']};
                border: 1px solid {theme['border_color']};
                padding: 4px 6px;
                border-radius: 3px;
                selection-background-color: {accent};
                selection-color: {ACCENT_PRESSED_TEXT_LIGHT if is_light else ACCENT_PRESSED_TEXT_DARK};
            }}
            QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus,
            QLineEdit:focus, QPlainTextEdit:focus {{
                border-color: {accent};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {card_bg};
                color: {theme['text_color']};
                border: 1px solid {theme['border_color']};
                selection-background-color: {accent};
                selection-color: {ACCENT_PRESSED_TEXT_LIGHT if is_light else ACCENT_PRESSED_TEXT_DARK};
            }}

            /* ---- Buttons ---- */
            QPushButton {{
                background-color: {card_bg};
                color: {theme['button_text']};
                border: 1px solid {theme['border_color']};
                padding: 5px 14px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {btn_hover_bg};
                color: {btn_hover_text};
                border-color: {btn_hover_border};
            }}
            QPushButton:pressed {{
                background-color: {btn_pressed_bg};
                color: {btn_pressed_text};
                border-color: {btn_pressed_border};
            }}

            /* ---- Sliders (gold handle) ---- */
            QSlider::groove:horizontal {{
                border: 1px solid {theme['border_color']};
                height: 6px;
                background: {input_bg};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                border: 1px solid {accent_dark};
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {accent_dark};
            }}
            QSlider::sub-page:horizontal {{
                background: {accent};
                border-radius: 3px;
            }}

            /* ---- Scrollbar ---- */
            QScrollBar:vertical {{
                background: {theme['panel_bg']};
                width: 10px;
                border: none;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme['scrollbar_handle']};
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme['scrollbar_handle_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        # Combo dropdown is a top-level popup (like QMenu) so it doesn't
        # inherit the dialog stylesheet. Apply directly to each view.
        combo_view_style = f"""
            QListView {{
                background-color: {card_bg};
                color: {theme['text_color']};
                border: 1px solid {theme['border_color']};
                font-family: '{font_family}';
            }}
            QListView::item {{
                padding: 4px 6px;
            }}
            QListView::item:selected {{
                background-color: {accent};
                color: {ACCENT_PRESSED_TEXT_LIGHT if is_light else ACCENT_PRESSED_TEXT_DARK};
            }}
            QListView::item:hover {{
                background-color: {accent};
                color: {ACCENT_PRESSED_TEXT_LIGHT if is_light else ACCENT_PRESSED_TEXT_DARK};
            }}
        """
        for combo in (self.combo_format, self.combo_clipboard, self.combo_blindness,
                      self.combo_border_style, self.combo_size_pref, self.combo_history_size):
            combo.view().setStyleSheet(combo_view_style)


# ==================== Module Exports ====================

__all__: list[str] = [
    "SettingsDialog",
]