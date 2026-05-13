"""
Batch Export dialog for RNV Color Palette Manager.
Exports the current palette to multiple formats in a single folder.
Optimized for Python 3.13.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox,
    QLabel, QPushButton, QProgressBar, QFileDialog, QGridLayout,
    QWidget, QLineEdit, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from utils.logger import Logger, get_logger_instance
from ui.colors import (
    STATUS_ERROR_TEXT,
    ACCENT_PRESSED_TEXT_DARK,
    ACCENT_PRESSED_TEXT_LIGHT,
)

if TYPE_CHECKING:
    from utils.settings_manager import SettingsManager

logger: Logger = get_logger_instance(__name__)

# All exportable formats (exclude "All Files")
BATCH_FORMATS: list[tuple[str, str]] = [
    ("Adobe Swatch Exchange", ".ase"),
    ("Adobe Color", ".aco"),
    ("Adobe Color Book", ".acb"),
    ("GIMP Palette", ".gpl"),
    ("Procreate Swatches", ".swatches"),
    ("Affinity Palette", ".afpalette"),
    ("macOS Colors", ".clr"),
    ("Colors File", ".colors"),
    ("CSS Variables", ".css"),
    ("JSON", ".json"),
    ("XML", ".xml"),
    ("SVG Palette", ".svg"),
    ("HEX Text", ".hex"),
    ("HSV Text", ".hsv"),
    ("HSL Text", ".hsl"),
    ("Plain Text", ".txt"),
]


@dataclass
class BatchExportResult:
    """Result of a batch export operation."""

    succeeded: list[str]   # List of successfully exported file paths
    failed: list[tuple[str, str]]  # List of (format, error_message) for failures
    folder: str = ""

    @property
    def total(self) -> int:
        return len(self.succeeded) + len(self.failed)

    @property
    def summary(self) -> str:
        if not self.failed:
            return f"Successfully exported {len(self.succeeded)} format(s)."
        return (
            f"Exported {len(self.succeeded)}/{self.total} formats. "
            f"{len(self.failed)} failed:\n"
            + "\n".join(f"  • {fmt}: {err}" for fmt, err in self.failed)
        )


class BatchExportDialog(QDialog):
    """
    Dialog for exporting the current palette to multiple formats at once.

    Features:
        - Checkbox grid of all supported export formats
        - Folder picker for output directory
        - Palette name used as base filename
        - Progress bar during export
        - Select All / Deselect All buttons
        - Remembers last batch selection via settings
    """

    def __init__(
        self,
        palette_name: str = "palette",
        settings: SettingsManager | None = None,
        parent: QWidget | None = None,
        theme_manager=None,
    ) -> None:
        super().__init__(parent)
        self._palette_name = palette_name or "palette"
        self._settings = settings
        self._theme_manager = theme_manager
        self._folder: str = ""
        self._format_checks: dict[str, QCheckBox] = {}
        self._result: BatchExportResult | None = None

        self.setWindowTitle("Batch Export")
        self.setFixedSize(560, 480)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._build_ui()
        self._load_defaults()
        self._apply_theme()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header
        header = QLabel(f"Export \"{self._palette_name}\" to multiple formats")
        font = header.font()
        font.setBold(True)
        font.setPointSize(11)
        header.setFont(font)
        layout.addWidget(header)

        # Folder picker
        folder_group = QGroupBox("Output Folder")
        folder_layout = QHBoxLayout(folder_group)
        folder_layout.setSpacing(6)

        self._folder_input = QLineEdit()
        self._folder_input.setPlaceholderText("Choose output folder...")
        self._folder_input.setReadOnly(True)
        self._folder_input.setToolTip("Destination folder for all exported palette files")
        folder_layout.addWidget(self._folder_input, stretch=1)

        self._btn_browse = QPushButton("Browse...")
        self._btn_browse.setFixedWidth(90)
        self._btn_browse.setToolTip("Choose the output folder")
        self._btn_browse.clicked.connect(self._pick_folder)
        folder_layout.addWidget(self._btn_browse)

        layout.addWidget(folder_group)

        # Format checkboxes
        fmt_group = QGroupBox("Select Formats")
        fmt_layout = QVBoxLayout(fmt_group)
        fmt_layout.setSpacing(4)

        # Select/deselect buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self._btn_select_all = QPushButton("Select All")
        self._btn_select_all.setFixedWidth(110)
        self._btn_select_all.setToolTip("Check all export formats")
        self._btn_select_all.clicked.connect(self._select_all)
        btn_row.addWidget(self._btn_select_all)

        self._btn_deselect_all = QPushButton("Deselect All")
        self._btn_deselect_all.setFixedWidth(110)
        self._btn_deselect_all.setToolTip("Uncheck all export formats")
        self._btn_deselect_all.clicked.connect(self._deselect_all)
        btn_row.addWidget(self._btn_deselect_all)

        self._lbl_count = QLabel("0 selected")
        btn_row.addStretch()
        btn_row.addWidget(self._lbl_count)
        fmt_layout.addLayout(btn_row)

        # Checkbox grid (2 columns)
        grid = QGridLayout()
        grid.setSpacing(4)
        for i, (name, ext) in enumerate(BATCH_FORMATS):
            cb = QCheckBox(f"{name} ({ext})")
            cb.setProperty("format_ext", ext)
            cb.stateChanged.connect(self._update_count)
            self._format_checks[ext] = cb
            grid.addWidget(cb, i // 2, i % 2)
        fmt_layout.addLayout(grid)

        layout.addWidget(fmt_group)

        # Filename preview
        self._lbl_preview = QLabel("")
        self._lbl_preview.setStyleSheet("color: grey; font-style: italic; font-size: 11px;")
        layout.addWidget(self._lbl_preview)
        self._update_preview()

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(True)
        layout.addWidget(self._progress)

        # Status label
        self._lbl_status = QLabel("")
        self._lbl_status.setVisible(False)
        layout.addWidget(self._lbl_status)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self._btn_export = QPushButton("Export")
        self._btn_export.setFixedWidth(100)
        self._btn_export.setDefault(True)
        self._btn_export.setToolTip("Export palette to all selected formats")
        self._btn_export.clicked.connect(self.accept)
        btn_layout.addWidget(self._btn_export)

        self._btn_cancel = QPushButton("Cancel")
        self._btn_cancel.setFixedWidth(100)
        self._btn_cancel.setToolTip("Cancel batch export")
        self._btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self._btn_cancel)

        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def selected_formats(self) -> list[str]:
        """Return list of selected format extensions (e.g. ['.json', '.gpl'])."""
        return [
            ext for ext, cb in self._format_checks.items()
            if cb.isChecked()
        ]

    @property
    def output_folder(self) -> str:
        return self._folder

    @property
    def base_filename(self) -> str:
        """Sanitized palette name for use as filename."""
        # Remove characters invalid in filenames
        name = self._palette_name
        for ch in r'<>:"/\|?*':
            name = name.replace(ch, "_")
        return name.strip() or "palette"

    def set_progress(self, current: int, total: int, label: str = "") -> None:
        """Update progress bar from the caller."""
        self._progress.setVisible(True)
        self._progress.setMaximum(total)
        self._progress.setValue(current)
        if label:
            self._lbl_status.setText(label)
            self._lbl_status.setVisible(True)

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------

    def _load_defaults(self) -> None:
        """Load last-used batch settings."""
        if not self._settings:
            return
        # Load default folder
        folder = self._settings._settings.value("batch_export/folder", "")
        if folder and Path(folder).is_dir():
            self._folder = folder
            self._folder_input.setText(folder)

        # Load last-selected formats
        saved = self._settings._settings.value("batch_export/formats", "")
        if isinstance(saved, str) and saved:
            for ext in saved.split(","):
                ext = ext.strip()
                if ext in self._format_checks:
                    self._format_checks[ext].setChecked(True)

        self._update_count()

    def save_defaults(self) -> None:
        """Save current selections for next time."""
        if not self._settings:
            return
        self._settings._settings.setValue("batch_export/folder", self._folder)
        self._settings._settings.setValue(
            "batch_export/formats",
            ",".join(self.selected_formats),
        )

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _pick_folder(self) -> None:
        start = self._folder or ""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", start,
        )
        if folder:
            self._folder = folder
            self._folder_input.setText(folder)
            self._update_preview()

    def _select_all(self) -> None:
        for cb in self._format_checks.values():
            cb.setChecked(True)

    def _deselect_all(self) -> None:
        for cb in self._format_checks.values():
            cb.setChecked(False)

    def _update_count(self) -> None:
        count = len(self.selected_formats)
        self._lbl_count.setText(f"{count} selected")
        self._btn_export.setEnabled(count > 0)
        self._update_preview()

    def _update_preview(self) -> None:
        selected = self.selected_formats
        if not selected:
            self._lbl_preview.setText("Select at least one format to export.")
            return
        name = self.base_filename
        examples = ", ".join(f"{name}{ext}" for ext in selected[:3])
        if len(selected) > 3:
            examples += f", ... (+{len(selected) - 3} more)"
        folder = self._folder or "(choose folder)"
        self._lbl_preview.setText(f"Files: {examples}\nFolder: {folder}")

    def accept(self) -> None:
        """Validate before accepting."""
        if not self._folder or not Path(self._folder).is_dir():
            self._lbl_status.setText("⚠ Please select a valid output folder.")
            self._lbl_status.setVisible(True)
            self._lbl_status.setStyleSheet(f"color: {STATUS_ERROR_TEXT};")
            return
        if not self.selected_formats:
            self._lbl_status.setText("⚠ Select at least one format.")
            self._lbl_status.setVisible(True)
            self._lbl_status.setStyleSheet(f"color: {STATUS_ERROR_TEXT};")
            return
        self.save_defaults()
        super().accept()

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_theme(self) -> None:
        if not self._theme_manager:
            return
        theme = self._theme_manager.get_current_theme()
        if not theme:
            return

        text = theme["text_color"]
        bg = theme["window_bg"]
        panel = theme["panel_bg"]
        border = theme["border_color"]
        card_bg = theme["card_bg"]
        btn_text = theme["button_text"]

        # Brand accent (BRAND_GOLD on dark/image, BRAND_GOLD_DARK on light --
        # determined by the theme's own 'accent' key). Pressed text contrasts
        # with the gold background: white in light mode, black otherwise.
        accent = theme["accent"]
        is_light = (self._theme_manager.current_theme == 'light')
        pressed_text = ACCENT_PRESSED_TEXT_LIGHT if is_light else ACCENT_PRESSED_TEXT_DARK

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg}; color: {text};
            }}
            QGroupBox {{
                color: {text}; border: 1px solid {border};
                border-radius: 4px; margin-top: 8px; padding-top: 14px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; left: 10px; padding: 0 4px;
            }}
            QCheckBox {{ color: {text}; spacing: 5px; }}
            QCheckBox::indicator {{
                width: 14px; height: 14px;
                border: 1px solid {border}; border-radius: 2px;
                background-color: {panel};
            }}
            QCheckBox::indicator:checked {{
                background-color: {accent}; border-color: {accent};
            }}
            QLabel {{ color: {text}; }}
            QLineEdit {{
                color: {text}; background-color: {panel};
                border: 1px solid {border}; border-radius: 3px;
                padding: 4px;
            }}
            QLineEdit:focus {{
                border: 1px solid {accent};
            }}
            /* Dialog button pattern: card_bg base, gold hover, gold press */
            QPushButton {{
                background-color: {card_bg}; color: {btn_text};
                border: 1px solid {border}; border-radius: 4px;
                padding: 4px 10px; font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {card_bg}; color: {accent};
                border-color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {accent}; color: {pressed_text};
                border-color: {accent};
            }}
            QPushButton:default {{
                border-color: {accent};
            }}
            QPushButton:disabled {{
                color: {theme["text_disabled"]};
                border-color: {border};
            }}
            QProgressBar {{
                border: 1px solid {border}; border-radius: 4px;
                text-align: center; color: {text};
                background-color: {panel};
            }}
            QProgressBar::chunk {{
                background-color: {accent}; border-radius: 3px;
            }}
        """)


__all__: list[str] = [
    "BatchExportDialog",
    "BatchExportResult",
    "BATCH_FORMATS",
]