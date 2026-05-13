"""
Dialog for choosing how to use an uploaded image.
Supports: Use Image, Use Average Color, Extract Palette (k-means).
Optimized for Python 3.13.
"""
from __future__ import annotations

from typing import Literal, TypedDict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox,
)
from PyQt6.QtCore import Qt, QEventLoop
from PyQt6.QtGui import QPixmap
from PIL import Image

from utils.logger import Logger, get_logger_instance
from ui.colors import IMAGE_PREVIEW_BORDER, IMAGE_PREVIEW_BG

logger: Logger = get_logger_instance(__name__)


class DialogResult(TypedDict):
    """Type definition for dialog result."""
    mode: Literal['image', 'average', 'extract'] | None
    extract_count: int


class ImageUploadDialog(QWidget):
    """Dialog for choosing how to use an uploaded image."""

    def __init__(self, file_path: str, pil_image: Image.Image, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.file_path = file_path
        self.pil_image = pil_image
        self.result_mode: Literal['image', 'average', 'extract'] | None = None
        self.extract_count: int = 5
        self.accepted = False
        self.loop: QEventLoop | None = None

        self.setWindowTitle("Upload Image")

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title label
        title_label = QLabel("How would you like to use this image?")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title_label.font()
        font.setPointSize(12)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        # Image preview
        preview_label = QLabel()
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(file_path)
        preview_size = 300
        if pixmap.width() > preview_size or pixmap.height() > preview_size:
            pixmap = pixmap.scaled(
                preview_size, preview_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        preview_label.setPixmap(pixmap)
        preview_label.setStyleSheet(
            f"border: 2px solid {IMAGE_PREVIEW_BORDER}; background-color: {IMAGE_PREVIEW_BG}; padding: 5px;"
        )
        layout.addWidget(preview_label)

        # Top row: Use Image / Use Average Color
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        self.use_image_btn = QPushButton("Use Image")
        self.use_image_btn.setMinimumHeight(40)
        self.use_image_btn.setToolTip("Display the image directly in the color slot")
        self.use_image_btn.clicked.connect(self.on_use_image)

        self.use_avg_btn = QPushButton("Use Average Color")
        self.use_avg_btn.setMinimumHeight(40)
        self.use_avg_btn.setToolTip("Fill the slot with the average color of this image")
        self.use_avg_btn.clicked.connect(self.on_use_average)

        row1.addWidget(self.use_image_btn)
        row1.addWidget(self.use_avg_btn)
        layout.addLayout(row1)

        # Bottom row: Extract Palette with count spinner + Cancel
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        self.extract_btn = QPushButton("Extract Palette")
        self.extract_btn.setMinimumHeight(40)
        self.extract_btn.setToolTip("Extract dominant colors using k-means clustering")
        self.extract_btn.clicked.connect(self.on_extract)

        self.count_spinner = QSpinBox()
        self.count_spinner.setRange(3, 12)
        self.count_spinner.setValue(5)
        self.count_spinner.setSuffix(" colors")
        self.count_spinner.setMinimumHeight(40)
        self.count_spinner.setFixedWidth(110)
        self.count_spinner.setToolTip("Number of dominant colors to extract")

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setToolTip("Cancel and close this dialog")
        self.cancel_btn.clicked.connect(self.on_cancel)

        row2.addWidget(self.extract_btn)
        row2.addWidget(self.count_spinner)
        row2.addWidget(self.cancel_btn)
        layout.addLayout(row2)

        self.adjustSize()

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def on_use_image(self) -> None:
        logger.debug("Use Image clicked")
        self.result_mode = 'image'
        self.accepted = True
        self.hide()
        if self.loop:
            self.loop.quit()

    def on_use_average(self) -> None:
        logger.debug("Use Average clicked")
        self.result_mode = 'average'
        self.accepted = True
        self.hide()
        if self.loop:
            self.loop.quit()

    def on_extract(self) -> None:
        logger.debug("Extract Palette clicked")
        self.result_mode = 'extract'
        self.extract_count = self.count_spinner.value()
        self.accepted = True
        self.hide()
        if self.loop:
            self.loop.quit()

    def on_cancel(self) -> None:
        logger.debug("Cancel clicked")
        self.accepted = False
        self.hide()
        if self.loop:
            self.loop.quit()

    # ------------------------------------------------------------------
    # Dialog lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        logger.debug(f"Dialog closing, accepted={self.accepted}, mode={self.result_mode}")
        if self.loop:
            self.loop.quit()
        event.accept()

    def exec(self) -> bool:
        logger.debug("Dialog exec() called")
        self.show()
        self.raise_()
        self.activateWindow()

        self.loop = QEventLoop()
        logger.debug("Starting event loop")
        self.loop.exec()
        logger.debug(f"Event loop finished, returning {self.accepted}")

        return self.accepted

    def get_result(self) -> DialogResult:
        return {
            'mode': self.result_mode,
            'extract_count': self.extract_count,
        }