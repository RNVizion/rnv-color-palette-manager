"""
Color slot widgets for RNV Color Palette Manager.
Contains the visual color square and its control buttons.
Features: clipboard copy, image upload with palette extraction, context menu.
Optimized for Python 3.13.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QFrame, QWidget, QVBoxLayout, QLabel,
    QSizePolicy, QColorDialog, QFileDialog, QMenu, QApplication,
)
from PyQt6.QtCore import Qt, QSize, QTimer, QMimeData, QPoint
from PyQt6.QtGui import QPainter, QColor, QPixmap, QAction, QPalette, QDrag
from PIL import Image

from ui.image_button import ImageButton
from ui.image_upload_dialog import ImageUploadDialog
from core.color_extractor import ColorExtractor
from core.color_harmonies import ColorHarmonies
from core.color_math import ColorMath
from core.accessibility import Accessibility
from utils.config import get_button_image_paths, MAX_SLOTS
from ui.colors import (
    SLOT_BORDER_THIN_COLOR, SLOT_BORDER_THICK_COLOR,
    SEARCH_HIGHLIGHT_COLOR, SEARCH_DIM_OVERLAY,
    BRAND_GOLD_RGB, BRAND_GOLD_DARK_RGB,
    TRANSPARENT_RGBA,
    DEFAULT_SLOT_COLOR, DEFAULT_SLOT_COLOR_IMAGE_RGB,
)
from utils.logger import Logger, get_logger_instance
from utils.dialog_helper import DialogHelper

if TYPE_CHECKING:
    from ui.preview_grid import PreviewGrid
    from ui.theme_manager import ThemeManager
    from RNV_Color_Palette_Manager import MainWindow

logger: Logger = get_logger_instance(__name__)

# Fixed pixel heights — labels cannot grow and push buttons out of view.
_HEX_LABEL_H: int = 18
_RGB_LABEL_H: int = 15
_HSL_LABEL_H: int = 15
_SMALL_PT:    int = 7


class ColorSlot(QFrame):
    """Visual color square that displays a color or image."""

    def __init__(
        self,
        color: QColor | None = None,
        base_size: int = 100,
        max_size: int = 200,
        parent: QWidget | None = None,
        theme_manager: ThemeManager | None = None,
    ) -> None:
        super().__init__(parent)
        self.theme_manager = theme_manager

        # Set default color based on theme
        if color is None:
            if theme_manager and theme_manager.is_image_mode():
                self.color = QColor(*DEFAULT_SLOT_COLOR_IMAGE_RGB)
            else:
                self.color = QColor(DEFAULT_SLOT_COLOR)
        else:
            self.color = color

        self.base_size = base_size
        self.max_size = max_size
        self.image_pixmap: QPixmap | None = None
        self._selected: bool = False
        self._is_default_color: bool = (color is None)  # Track if still using default
        self._border_style: str = "none"  # none, thin, thick
        self._search_highlight: bool = False  # Phase 6: search match glow
        self._search_dimmed: bool = False     # Phase 6: non-match dim
        self.setMinimumSize(base_size, base_size)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    @property
    def border_style(self) -> str:
        """Slot border style: 'none', 'thin', or 'thick'."""
        return self._border_style

    @border_style.setter
    def border_style(self, value: str) -> None:
        if value in ("none", "thin", "thick"):
            self._border_style = value
            self.update()

    def paintEvent(self, event) -> None:
        """Paint the color slot -- either solid color or image."""
        painter = QPainter(self)

        if self.image_pixmap and not self.image_pixmap.isNull():
            scaled_pixmap = self.image_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            painter.fillRect(self.rect(), self.color)

        # Draw slot border based on style
        match self._border_style:
            case "thin":
                pen = painter.pen()
                pen.setColor(QColor(*SLOT_BORDER_THIN_COLOR))
                pen.setWidth(1)
                painter.setPen(pen)
                painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
            case "thick":
                pen = painter.pen()
                pen.setColor(QColor(*SLOT_BORDER_THICK_COLOR))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawRect(1, 1, self.width() - 3, self.height() - 3)
            case _:  # "none"
                pass

        # Draw selection border (overrides slot border).
        # Dark/Image mode: light gold (BRAND_GOLD_RGB) — visible on dark bg.
        # Light mode: dark gold (BRAND_GOLD_DARK_RGB) — visible on light bg.
        if self._selected:
            is_light = (
                self.theme_manager is not None
                and not self.theme_manager.is_image_mode()
                and getattr(self.theme_manager, 'current_theme', 'dark') == 'light'
            )
            sel_color = BRAND_GOLD_DARK_RGB if is_light else BRAND_GOLD_RGB
            pen = painter.pen()
            pen.setColor(QColor(*sel_color))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawRect(1, 1, self.width() - 3, self.height() - 3)

        # Phase 6: Search highlight glow
        if self._search_highlight:
            pen = painter.pen()
            pen.setColor(QColor(*SEARCH_HIGHLIGHT_COLOR))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawRect(1, 1, self.width() - 3, self.height() - 3)

        # Phase 6: Search dim overlay (semi-transparent dark)
        if self._search_dimmed:
            painter.fillRect(self.rect(), QColor(*SEARCH_DIM_OVERLAY))

    def sizeHint(self) -> QSize:
        return QSize(self.base_size, self.base_size)

    def resize_to_fit(self, target_size: int, max_override: int | None = None) -> None:
        """Resize the slot to fit a target size."""
        max_size = max_override if max_override is not None else self.max_size
        side = max(self.base_size, min(target_size, max_size))
        self.setFixedSize(side, side)
        self.update()


class ColorSlotWidget(QWidget):
    """Complete color slot with controls (upload, clear, lock buttons)."""

    FIXED_DISTANCE = 6

    def __init__(self, slot: ColorSlot, preview_grid: PreviewGrid, main_window: MainWindow) -> None:
        super().__init__()
        self.slot = slot
        self.preview_grid = preview_grid
        self.main_window = main_window
        self.locked = False

        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(self.FIXED_DISTANCE)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        main_layout.addWidget(self.slot, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.slot.setToolTip("Click to open color picker\nRight-click for options")

        self._group_container = QWidget()
        group_layout = QVBoxLayout(self._group_container)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(4)
        group_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Clickable hex label
        theme_color = self.main_window.theme_manager.get_current_theme()['text_color']
        self.hex_label = QLabel(self.slot.color.name())
        self.hex_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hex_label.setFixedHeight(_HEX_LABEL_H)
        self.hex_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hex_label.setToolTip("Click to copy color")
        self.hex_label.setStyleSheet(f"color: {theme_color};")
        self.hex_label.mousePressEvent = self._on_hex_label_clicked
        group_layout.addWidget(self.hex_label)

        # RGB label — fixed height, hidden until "Show expanded color info" enabled
        self.rgb_label = QLabel("")
        self.rgb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rgb_label.setFixedHeight(_RGB_LABEL_H)
        self.rgb_label.setStyleSheet(f"color: {theme_color}; font-size: {_SMALL_PT}pt;")
        self.rgb_label.hide()
        group_layout.addWidget(self.rgb_label)

        # HSL label — fixed height, hidden until "Show expanded color info" enabled
        self.hsl_label = QLabel("")
        self.hsl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hsl_label.setFixedHeight(_HSL_LABEL_H)
        self.hsl_label.setStyleSheet(f"color: {theme_color}; font-size: {_SMALL_PT}pt;")
        self.hsl_label.hide()
        group_layout.addWidget(self.hsl_label)

        # Create buttons with proper image paths from config helper
        upload_base, upload_hover, upload_pressed = get_button_image_paths("upload")
        clear_base, clear_hover, clear_pressed = get_button_image_paths("clear")
        lock_base, lock_hover, lock_pressed = get_button_image_paths("lock")

        self.btn_upload = ImageButton("Upload", upload_base, upload_hover, upload_pressed)
        self.btn_clear = ImageButton("Clear", clear_base, clear_hover, clear_pressed)
        self.btn_lock = ImageButton("Lock", lock_base, lock_hover, lock_pressed)

        self.btn_upload.setToolTip("Upload image to this slot")
        self.btn_clear.setToolTip("Remove this color slot (Delete)")
        self.btn_lock.setToolTip("Lock/unlock this slot (Space)")
        self.update_lock_button()
        self.button_list = [self.btn_upload, self.btn_clear, self.btn_lock]

        for b in self.button_list:
            b.set_theme_manager(main_window.theme_manager)
            b.setFixedSize(100, 25)
            group_layout.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)

        main_layout.addWidget(self._group_container, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Connect signals
        self.slot.mousePressEvent = self._on_slot_press
        self.slot.mouseMoveEvent = self._on_slot_move
        self.slot.mouseReleaseEvent = self._on_slot_release
        self.slot.mouseDoubleClickEvent = self._on_slot_double_click
        self.btn_clear.clicked.connect(lambda: self.main_window.remove_slot(self))
        self.btn_upload.clicked.connect(self.upload_image)
        self.btn_lock.clicked.connect(self.toggle_lock)

        # Drag state
        self._drag_start_pos: QPoint | None = None
        self._drag_active: bool = False
        self._pending_click_button: Qt.MouseButton | None = None
        self._copying: bool = False  # True during the 800ms "Copied!" flash

        # Accept drops on this widget
        self.setAcceptDrops(True)

        # Set initial minimum size so grid layout never compresses us
        self._update_minimum_size()

    # ==================================================================
    # Step 5: Clipboard Copy
    # ==================================================================

    def _on_hex_label_clicked(self, event) -> None:
        """Copy current color to clipboard in preferred format."""
        if self.hex_label.text() == "Image":
            return

        color = self.slot.color
        rgb = (color.red(), color.green(), color.blue())

        # Get clipboard format from settings if available
        fmt = "hex"
        if hasattr(self.main_window, "settings_manager"):
            fmt = self.main_window.settings_manager.clipboard_format

        match fmt:
            case "rgb":
                text = f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"
            case "hsl":
                h, l, s = ColorMath.rgb_to_hsl(rgb)
                text = f"hsl({h * 360:.0f}, {s * 100:.0f}%, {l * 100:.0f}%)"
            case _:
                text = color.name()

        clipboard = QApplication.clipboard()
        clipboard.setText(text)

        # Visual feedback: flash "Copied!" then revert
        self._copying = True
        self.hex_label.setText("Copied!")
        def _revert1() -> None:
            self._copying = False
            self.refresh_color_info()
        QTimer.singleShot(800, _revert1)

        logger.debug(f"Copied to clipboard: {text}")

    # ==================================================================
    # Phase 4 (roadmap): Drag-and-Drop Slot Reordering
    # ==================================================================

    DRAG_THRESHOLD = 12  # pixels before drag starts

    def _on_slot_press(self, event) -> None:
        """Store press position; defer click until release (to allow drag)."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._drag_active = False
            self._pending_click_button = Qt.MouseButton.LeftButton
        elif event.button() == Qt.MouseButton.RightButton:
            # Right-click handled immediately (context menu)
            self._show_context_menu(event.globalPosition().toPoint())

    def _on_slot_move(self, event) -> None:
        """If pressed and moved beyond threshold, initiate drag."""
        if self._drag_start_pos is None:
            return
        if self._drag_active:
            return  # Already dragging via QDrag

        distance = (event.pos() - self._drag_start_pos).manhattanLength()
        if distance >= self.DRAG_THRESHOLD:
            self._start_drag()

    def _on_slot_release(self, event) -> None:
        """If no drag occurred, handle as a normal click."""
        if event.button() == Qt.MouseButton.LeftButton and not self._drag_active:
            if self._pending_click_button == Qt.MouseButton.LeftButton:
                self._handle_left_click()
        # Reset drag state
        self._drag_start_pos = None
        self._drag_active = False
        self._pending_click_button = None

    def _handle_left_click(self) -> None:
        """Execute a deferred left-click action (color pick or select)."""
        single_click = True
        if hasattr(self.main_window, "settings_manager"):
            single_click = self.main_window.settings_manager.single_click_edit
        if single_click:
            self.change_color(None)
        else:
            self.main_window.select_slot(self)

    def _start_drag(self) -> None:
        """Initiate a QDrag for reordering this slot."""
        if self.locked:
            self._drag_start_pos = None
            return

        self._drag_active = True
        self._pending_click_button = None

        drag = QDrag(self.slot)
        mime = QMimeData()
        mime.setData("application/x-rnv-slot-index", str(self._get_slot_index()).encode())
        drag.setMimeData(mime)

        # Create ghost pixmap from the slot
        pixmap = self.slot.grab()
        # Make it semi-transparent
        ghost = QPixmap(pixmap.size())
        ghost.fill(QColor(*TRANSPARENT_RGBA))
        painter = QPainter(ghost)
        painter.setOpacity(0.6)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        drag.setPixmap(ghost)
        drag.setHotSpot(QPoint(ghost.width() // 2, ghost.height() // 2))

        logger.debug(f"Drag started from slot {self._get_slot_index()}")
        drag.exec(Qt.DropAction.MoveAction)

        # Reset after drag completes.
        # Reset hover state on ALL slot buttons — Qt never fires leaveEvent
        # during QDrag.exec(), so hovered buttons stay visually stuck.
        self._drag_start_pos = None
        self._drag_active = False
        for w in self.main_window.slots_widgets:
            for btn in w.button_list:
                btn.reset_hover_state()

    # -- Drop handling on this widget --

    def dragEnterEvent(self, event) -> None:
        """Accept slot reorder drags."""
        if event.mimeData().hasFormat("application/x-rnv-slot-index"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        """Accept continued drag movement."""
        if event.mimeData().hasFormat("application/x-rnv-slot-index"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        """Handle drop: reorder the slot to this position."""
        if not event.mimeData().hasFormat("application/x-rnv-slot-index"):
            event.ignore()
            return

        source_idx_str = bytes(event.mimeData().data("application/x-rnv-slot-index")).decode()
        try:
            source_idx = int(source_idx_str)
        except ValueError:
            event.ignore()
            return

        target_idx = self._get_slot_index()
        if source_idx == target_idx or source_idx < 0 or target_idx < 0:
            event.ignore()
            return

        # Delegate reorder to main window
        if hasattr(self.main_window, 'reorder_slot'):
            self.main_window.reorder_slot(source_idx, target_idx)
            event.acceptProposedAction()
            logger.debug(f"Dropped slot {source_idx} → {target_idx}")
        else:
            event.ignore()

    # ==================================================================
    # Step 7: Right-Click Context Menu
    # ==================================================================

    def _on_slot_click(self, event) -> None:
        """Handle left-click (select or edit) and right-click (context menu)."""
        if event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
        elif event.button() == Qt.MouseButton.LeftButton:
            # Check setting: single-click edits or selects?
            single_click = True
            if hasattr(self.main_window, "settings_manager"):
                single_click = self.main_window.settings_manager.single_click_edit
            if single_click:
                self.change_color(event)
            else:
                self.main_window.select_slot(self)

    def _on_slot_double_click(self, event) -> None:
        """Double-click always opens color picker (when single-click selects)."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.change_color(event)

    def set_selected(self, selected: bool) -> None:
        """Set visual selection state on this slot."""
        self.slot._selected = selected
        self.slot.update()

    def _show_context_menu(self, pos) -> None:
        """Show right-click context menu on color slot."""
        # Parent to main window so menu isn't clipped by the graphics view proxy
        menu = QMenu(self.main_window)
        menu.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint
        )
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        if not self.main_window.theme_manager.is_image_mode():
            menu.setAutoFillBackground(False)
            p = menu.palette()
            p.setColor(QPalette.ColorRole.Window, QColor(*TRANSPARENT_RGBA))
            menu.setPalette(p)

        # Copy actions
        copy_hex = QAction("Copy Hex", self)
        copy_hex.triggered.connect(lambda: self._copy_color("hex"))
        menu.addAction(copy_hex)

        copy_rgb = QAction("Copy RGB", self)
        copy_rgb.triggered.connect(lambda: self._copy_color("rgb"))
        menu.addAction(copy_rgb)

        copy_hsl = QAction("Copy HSL", self)
        copy_hsl.triggered.connect(lambda: self._copy_color("hsl"))
        menu.addAction(copy_hsl)

        menu.addSeparator()

        # Slot management
        duplicate_action = QAction("Duplicate Slot", self)
        duplicate_action.triggered.connect(self._duplicate_slot)
        if len(self.main_window.slots_widgets) >= MAX_SLOTS:
            duplicate_action.setEnabled(False)
        menu.addAction(duplicate_action)

        move_left = QAction("Move Left", self)
        move_left.triggered.connect(lambda: self._move_slot(-1))
        move_right = QAction("Move Right", self)
        move_right.triggered.connect(lambda: self._move_slot(1))

        idx = self.main_window.slots_widgets.index(self) if self in self.main_window.slots_widgets else -1
        if idx <= 0:
            move_left.setEnabled(False)
        if idx < 0 or idx >= len(self.main_window.slots_widgets) - 1:
            move_right.setEnabled(False)

        menu.addAction(move_left)
        menu.addAction(move_right)

        # Move to Group submenu (Phase 5)
        if len(self.main_window.slot_groups) > 1:
            group_menu = menu.addMenu("Move to Group")
            group_menu.setWindowFlags(
                Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint
            )
            group_menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            if not self.main_window.theme_manager.is_image_mode():
                group_menu.setAutoFillBackground(False)
                gp = group_menu.palette()
                gp.setColor(QPalette.ColorRole.Window, QColor(*TRANSPARENT_RGBA))
                group_menu.setPalette(gp)
            current_group = self.main_window.get_group_for_slot(self)
            for i, group in enumerate(self.main_window.slot_groups):
                label = group.name or f"Group {i + 1}"
                action = QAction(label, self)
                action.triggered.connect(
                    lambda checked, g=group: self.main_window.move_slot_to_group(self, g)
                )
                if group is current_group:
                    action.setEnabled(False)
                    action.setText(f"✓ {label}")
                group_menu.addAction(action)

        menu.addSeparator()

        # Generate Harmony submenu (Step 8)
        harmony_menu = menu.addMenu("Generate Harmony")
        harmony_menu.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint
        )
        harmony_menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        if not self.main_window.theme_manager.is_image_mode():
            harmony_menu.setAutoFillBackground(False)
            hp = harmony_menu.palette()
            hp.setColor(QPalette.ColorRole.Window, QColor(*TRANSPARENT_RGBA))
            harmony_menu.setPalette(hp)
        for harmony_name in ColorHarmonies.HARMONY_NAMES:
            action = QAction(harmony_name, self)
            action.triggered.connect(
                lambda checked, n=harmony_name: self._generate_harmony(n)
            )
            harmony_menu.addAction(action)

        # Gradient (Step 9)
        gradient_action = QAction("Generate Gradient To...", self)
        gradient_action.triggered.connect(self._start_gradient_selection)
        if len(self.main_window.slots_widgets) < 2:
            gradient_action.setEnabled(False)
        menu.addAction(gradient_action)

        # Contrast checker (Step 15)
        contrast_action = QAction("Check Contrast With...", self)
        contrast_action.triggered.connect(self._start_contrast_check)
        if len(self.main_window.slots_widgets) < 2:
            contrast_action.setEnabled(False)
        menu.addAction(contrast_action)

        menu.exec(pos)

    def _copy_color(self, fmt: str) -> None:
        """Copy color in specified format to clipboard."""
        if self.hex_label.text() == "Image":
            return

        color = self.slot.color
        rgb = (color.red(), color.green(), color.blue())

        match fmt:
            case "rgb":
                text = f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"
            case "hsl":
                h, l, s = ColorMath.rgb_to_hsl(rgb)
                text = f"hsl({h * 360:.0f}, {s * 100:.0f}%, {l * 100:.0f}%)"
            case _:
                text = color.name()

        QApplication.clipboard().setText(text)
        self._copying = True
        self.hex_label.setText("Copied!")
        def _revert2() -> None:
            self._copying = False
            self.refresh_color_info()
        QTimer.singleShot(800, _revert2)
        logger.debug(f"Copied ({fmt}): {text}")

    def _duplicate_slot(self) -> None:
        """Duplicate this slot's color into a new slot."""
        if len(self.main_window.slots_widgets) >= MAX_SLOTS:
            return
        self.main_window.duplicate_slot(self)

    def _move_slot(self, direction: int) -> None:
        """Move this slot left (-1) or right (+1) in the grid."""
        self.main_window.move_slot(self, direction)

    # ==================================================================
    # Step 8: Harmony Generation
    # ==================================================================

    def _generate_harmony(self, harmony_name: str) -> None:
        """Generate harmony colors from this slot and add as new slots."""
        rgb = (self.slot.color.red(), self.slot.color.green(), self.slot.color.blue())
        new_colors = ColorHarmonies.generate(harmony_name, rgb)

        if not new_colors:
            return

        if hasattr(self.main_window, '_push_undo'):
            self.main_window._push_undo()

        for color_rgb in new_colors:
            if len(self.main_window.slots_widgets) >= MAX_SLOTS:
                break
            self.main_window.add_slot_with_color(QColor(*color_rgb))

        self.update_preview()
        logger.info(f"Generated {harmony_name}: {len(new_colors)} colors")

    # ==================================================================
    # Step 9: Gradient Generation
    # ==================================================================

    def _start_gradient_selection(self) -> None:
        """Enter gradient target selection mode via main window."""
        self.main_window.start_gradient_from(self)

    # ==================================================================
    # Theme and Lock
    # ==================================================================

    def apply_theme(self) -> None:
        """Apply current theme to this widget."""
        theme = self.main_window.theme_manager.get_current_theme()
        tc = theme['text_color']
        self.hex_label.setStyleSheet(f"color: {tc};")
        self.rgb_label.setStyleSheet(f"color: {tc}; font-size: {_SMALL_PT}pt;")
        self.hsl_label.setStyleSheet(f"color: {tc}; font-size: {_SMALL_PT}pt;")
        self.update_lock_button()

    def update_lock_button(self) -> None:
        """Update lock button text and state."""
        self.btn_lock.setText("Unlock" if self.locked else "Lock")
        self.btn_lock.set_locked_state(self.locked)

    def toggle_lock(self) -> None:
        """Toggle the locked state."""
        self.locked = not self.locked
        self.update_lock_button()

    def refresh_color_info(self) -> None:
        """Update hex/RGB/HSL labels. Fixed-height labels prevent button push-out."""
        if self.hex_label.text() == "Image" or self._copying:
            return

        color = self.slot.color
        rgb = (color.red(), color.green(), color.blue())

        self.hex_label.setText(color.name())

        show_info = False
        if hasattr(self.main_window, "settings_manager"):
            show_info = self.main_window.settings_manager.show_color_info

        if show_info:
            h, l, s = ColorMath.rgb_to_hsl(rgb)
            self.rgb_label.setText(f"RGB({rgb[0]}, {rgb[1]}, {rgb[2]})")
            self.hsl_label.setText(f"HSL({h * 360:.0f}°, {s * 100:.0f}%, {l * 100:.0f}%)")
            self.rgb_label.show()
            self.hsl_label.show()
        else:
            self.rgb_label.hide()
            self.hsl_label.hide()

        self._update_minimum_size()

    def _start_contrast_check(self) -> None:
        """Enter contrast target selection mode via main window."""
        self.main_window.start_contrast_from(self)

    # ==================================================================
    # Color Picker
    # ==================================================================

    def change_color(self, event) -> None:
        """Open color picker to change slot color."""
        if self.locked:
            return
        old_color_hex = self.slot.color.name()
        dialog = QColorDialog(self.slot.color, self.main_window)
        dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        if dialog.exec():
            color = dialog.selectedColor()
            if color.isValid():
                if hasattr(self.main_window, '_push_undo'):
                    self.main_window._push_undo()
                self.slot.color = color
                self.slot._is_default_color = False
                self.slot.image_pixmap = None
                self.refresh_color_info()
                self.slot.update()
                self.update_preview()
                # Record in color history
                slot_idx = self._get_slot_index()
                if hasattr(self.main_window, 'record_color_change'):
                    self.main_window.record_color_change(
                        old_color_hex, color.name(), slot_idx
                    )

    # ==================================================================
    # Image Upload (with Extract Palette -- Step 6)
    # ==================================================================

    def upload_image(self) -> None:
        """Upload and process an image for this slot."""
        if self.locked:
            return

        logger.debug("Opening file dialog...")
        start_dir = Path.home()
        pictures_dir = start_dir / "Pictures"
        if pictures_dir.exists():
            start_dir = pictures_dir

        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Select Image",
            str(start_dir),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*.*)",
        )

        if not file_path:
            logger.debug("No file selected")
            return

        try:
            image = Image.open(file_path).convert("RGB")
            logger.debug(f"Image loaded: {image.size}")

            dialog = ImageUploadDialog(file_path, image, self.main_window)
            result = dialog.exec()

            if result:
                dialog_result = dialog.get_result()
                logger.debug(f"Dialog result: {dialog_result}")

                match dialog_result['mode']:
                    case 'average':
                        self._apply_average_color(image)

                    case 'image':
                        self._apply_image(file_path)

                    case 'extract':
                        self._apply_extract_palette(
                            image, dialog_result.get('extract_count', 5)
                        )
            else:
                logger.debug("Dialog was cancelled")

        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            logger.exception("Upload image traceback:")
            DialogHelper.show_error(self, f"Failed to load image: {str(e)}")

    def _apply_average_color(self, image: Image.Image) -> None:
        """Apply average color from image to this slot."""
        old_color_hex = self.slot.color.name()
        max_calc_size = 200
        calc_image = image.copy()
        if calc_image.width > max_calc_size or calc_image.height > max_calc_size:
            ratio = min(max_calc_size / calc_image.width, max_calc_size / calc_image.height)
            new_size = (int(calc_image.width * ratio), int(calc_image.height * ratio))
            calc_image = calc_image.resize(new_size, Image.Resampling.LANCZOS)

        pixels = list(calc_image.getdata())
        avg_color = tuple(sum(c[i] for c in pixels) // len(pixels) for i in range(3))

        self.slot.color = QColor(*avg_color)
        self.slot._is_default_color = False
        self.slot.image_pixmap = None
        self.refresh_color_info()
        self.slot.update()
        self.update_preview()
        logger.debug(f"Average color applied: {avg_color}")

        # Record in color history
        if hasattr(self.main_window, 'record_color_change'):
            self.main_window.record_color_change(
                old_color_hex, self.slot.color.name(), self._get_slot_index()
            )

    def _apply_image(self, file_path: str) -> None:
        """Store image pixmap on this slot."""
        pixmap = QPixmap(file_path)
        max_size = self.slot.max_size
        if pixmap.width() > max_size or pixmap.height() > max_size:
            pixmap = pixmap.scaled(
                max_size, max_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self.slot.image_pixmap = pixmap
        self.slot._is_default_color = False
        self.hex_label.setText("Image")
        self.rgb_label.hide()
        self.hsl_label.hide()
        self.slot.update()
        self.update_preview()
        logger.debug("Image applied")

    def _apply_extract_palette(self, image: Image.Image, count: int) -> None:
        """Extract dominant colors and fill slots."""
        colors = ColorExtractor.extract_palette(image, num_colors=count)

        if not colors:
            DialogHelper.show_warning(self, "Could not extract colors from this image.")
            return

        if hasattr(self.main_window, '_push_undo'):
            self.main_window._push_undo()

        # Apply first color to this slot
        old_color_hex = self.slot.color.name()
        first_color = colors[0]
        self.slot.color = QColor(*first_color)
        self.slot._is_default_color = False
        self.slot.image_pixmap = None
        self.refresh_color_info()
        self.slot.update()

        # Record first color in history
        if hasattr(self.main_window, 'record_color_change'):
            self.main_window.record_color_change(
                old_color_hex, self.slot.color.name(), self._get_slot_index()
            )

        # Add remaining colors as new slots via main window
        for rgb in colors[1:]:
            if len(self.main_window.slots_widgets) >= MAX_SLOTS:
                break
            self.main_window.add_slot_with_color(QColor(*rgb))

        self.update_preview()
        logger.success(f"Extracted {len(colors)} colors from image")

    # ==================================================================
    # Helpers
    # ==================================================================

    def _get_slot_index(self) -> int:
        """Return this widget's index in the main window slot list, or -1."""
        if hasattr(self.main_window, 'slots_widgets'):
            try:
                return self.main_window.slots_widgets.index(self)
            except ValueError:
                pass
        return -1

    # ==================================================================
    # Size / Preview
    # ==================================================================

    def sizeHint(self) -> QSize:
        """Calculate size hint from fixed label heights + visible extras + buttons."""
        if not self.slot:
            return super().sizeHint()

        labels_h = _HEX_LABEL_H
        n_extra = 0
        if self.rgb_label.isVisible():
            labels_h += _RGB_LABEL_H
            n_extra += 1
        if self.hsl_label.isVisible():
            labels_h += _HSL_LABEL_H
            n_extra += 1

        buttons_h = len(self.button_list) * 25
        gaps_h = (1 + n_extra + len(self.button_list) - 1) * 4
        gc_height = labels_h + buttons_h + gaps_h

        total_height = 4 + self.slot.height() + self.FIXED_DISTANCE + gc_height + 4
        total_width  = max(self.slot.width(), 100) + 8

        return QSize(total_width, total_height)

    def _update_minimum_size(self) -> None:
        """Set minimum size and schedule a scroll_content height sync."""
        hint = self.sizeHint()
        self.setMinimumSize(hint)
        self.updateGeometry()
        QTimer.singleShot(0, self._sync_scroll_content_height)

    def _sync_scroll_content_height(self) -> None:
        """Recalculate scroll_content.minimumHeight from the live grid layout."""
        scroll_content = getattr(self.main_window, 'scroll_content', None)
        if scroll_content is None:
            return
        grid = scroll_content.layout()
        if grid is None:
            return
        grid.activate()
        needed = grid.sizeHint().height()
        if scroll_content.minimumHeight() < needed:
            scroll_content.setMinimumHeight(needed)
        zoom_view = getattr(self.main_window, 'zoom_view', None)
        if zoom_view and hasattr(zoom_view, 'update_scene_rect'):
            zoom_view.update_scene_rect()

    def update_preview(self) -> None:
        """Update the preview grid with current slots."""
        all_slots = [w.slot for w in self.main_window.slots_widgets]
        self.preview_grid.setSlots(all_slots)