"""
RNV Color Palette Manager
A professional color palette management application with theme support.
Optimized for Python 3.13.
"""
from __future__ import annotations

import logging
import sys
import math
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QSizePolicy, QFrame,
    QFileDialog, QLabel, QMenu, QInputDialog,
)
from PyQt6.QtCore import Qt, QSize, QTimer, QRectF, QPoint, QEvent
from PyQt6.QtGui import (
    QPalette, QColor, QIcon, QBrush, QPixmap, QShortcut, QKeySequence,
    QCursor, QPainter, QPen, QPainterPath,
)

# Import from refactored modules
from ui.theme_manager import ThemeManager
from ui.image_button import ImageButton
from ui.preview_grid import PreviewGrid
from ui.zoomable_graphics_view import ZoomableGraphicsView
from ui.settings_dialog import SettingsDialog
from ui.about_dialog import AboutDialog
from utils.color_history import ColorHistoryPanel, ColorHistoryEntry
from core.color_slot import ColorSlot, ColorSlotWidget
from core.color_harmonies import ColorHarmonies
from core.palette_formats import PaletteFormats, ImportResult
from core.palette_metadata import PaletteMetadata
from core.accessibility import Accessibility
from utils.config import (
    APP_NAME, APP_VERSION, APP_ICON_PATH,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
    REF_WIDTH, REF_HEIGHT, MIN_SLOT_SIZE, MAX_SLOT_SIZE, MAX_SLOTS,
    get_button_image_paths,
)
from utils.font_loader import load_embedded_font, get_font_family
from utils.logger import Logger, get_logger_instance, setup_logger
from utils.dialog_helper import DialogHelper
from utils.settings_manager import SettingsManager
from utils.session_manager import SessionManager, PaletteSessionState
from utils.export_history import ExportHistory
from utils.undo_manager import UndoManager, PaletteState
from utils.recent_palettes import RecentPalettesManager
from ui.slot_group import SlotGroupInfo, SlotGroupData, SlotGroupHeader
from ui.color_search import ColorSearchBar, parse_color_query, MATCH_THRESHOLD
from ui.batch_export_dialog import BatchExportDialog, BatchExportResult
from core.color_math import ColorMath
from ui.colors import (
    BRAND_GOLD, BRAND_GOLD_DARK, DARK_THEME_COLORS,
    ACCENT_PRESSED_TEXT_DARK, ACCENT_PRESSED_TEXT_LIGHT,
    SELECTION_OVERLAY_COLOR, SELECTION_OVERLAY_TEXT,
    SIZE_OVERLAY_BG, SESSION_FALLBACK_COLOR, TRANSPARENT_RGBA,
)

logger: Logger = get_logger_instance(__name__)


class _ThemedToolTip(QLabel):
    """
    Custom tooltip that bypasses native Windows tooltip rendering.

    Native QToolTip on Windows creates an OS-level popup window with its own
    frame that cannot be styled via CSS. This class creates a frameless Qt
    widget with WA_TranslucentBackground and paints its own rounded-rect
    background, giving pixel-perfect themed tooltips in all modes.
    """

    _instance: '_ThemedToolTip | None' = None
    _OFFSET_X: int = 16
    _OFFSET_Y: int = 20
    _HIDE_DELAY_MS: int = 5000
    _MAX_WIDTH: int = 400
    _BORDER_RADIUS: int = 4

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWordWrap(True)
        self.setMaximumWidth(self._MAX_WIDTH)
        self.hide()

        # Colors for paintEvent (updated on each show)
        self._bg_color = QColor(DARK_THEME_COLORS['card_bg'])
        self._border_color = QColor(BRAND_GOLD)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

        # Enabled flag — toggled by F11
        self._enabled: bool = True

    @classmethod
    def instance(cls) -> '_ThemedToolTip':
        """Get or create the singleton tooltip instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def paintEvent(self, event) -> None:
        """Paint rounded-rect background and border manually."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw filled rounded rectangle
        path = QPainterPath()
        rect = self.rect().adjusted(1, 1, -1, -1)
        path.addRoundedRect(float(rect.x()), float(rect.y()),
                           float(rect.width()), float(rect.height()),
                           self._BORDER_RADIUS, self._BORDER_RADIUS)
        painter.fillPath(path, self._bg_color)

        # Draw border
        painter.setPen(QPen(self._border_color, 1.0))
        painter.drawPath(path)
        painter.end()

        # Let QLabel paint the text on top
        super().paintEvent(event)

    def show_tip(self, global_pos: QPoint, text: str,
                 colors: dict, font_family: str) -> None:
        """Show themed tooltip at the given global position."""
        if not self._enabled:
            return

        # Store colors for paintEvent
        # Map to this app's color keys: card_bg, accent, text_color
        self._bg_color = QColor(colors['card_bg'])
        self._border_color = QColor(colors['accent'])

        # Title case the tooltip text
        self.setText(text.title())

        # Stylesheet for text only (background/border painted in paintEvent)
        self.setStyleSheet(
            f"color: {colors['text_color']};"
            f"padding: 4px 8px;"
            f"font-family: '{font_family}';"
            f"background: transparent;"
        )
        self.adjustSize()

        # Position below-right of cursor
        x = global_pos.x() + self._OFFSET_X
        y = global_pos.y() + self._OFFSET_Y

        # Keep tooltip on screen
        screen = QApplication.screenAt(global_pos)
        if screen:
            rect = screen.availableGeometry()
            if x + self.width() > rect.right():
                x = global_pos.x() - self.width() - 4
            if y + self.height() > rect.bottom():
                y = global_pos.y() - self.height() - 4

        self.move(x, y)
        self.show()
        self._hide_timer.start(self._HIDE_DELAY_MS)

    def hide_tip(self) -> None:
        """Hide the tooltip and cancel auto-hide timer."""
        self._hide_timer.stop()
        self.hide()


class MainWindow(QMainWindow):
    """Main application window for RNV Color Palette Manager"""

    def __init__(self) -> None:
        super().__init__()
        logger.info("Creating main window...")
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.ref_width = REF_WIDTH
        self.ref_height = REF_HEIGHT

        # Phase 1: Initialize managers
        self.settings_manager = SettingsManager()
        self.export_history = ExportHistory()
        self.session_manager = SessionManager(parent=self)
        self.session_manager.set_state_getter(self._get_session_state)
        self.palette_metadata = PaletteMetadata()
        self.recent_palettes = RecentPalettesManager(
            settings=self.settings_manager._settings,
            max_entries=self.settings_manager.max_recent_palettes,
        )
        logger.info("Managers initialized (settings, session, export history, recent palettes)")

        # Initialize theme manager
        self.theme_manager = ThemeManager()
        self.theme_manager.detect_image_resources()

        # Set application icon
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
            logger.success("Loaded application icon")
        else:
            logger.warning(f"Icon not found at {APP_ICON_PATH}")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.background_label = QLabel(self)
        self.background_label.setScaledContents(True)
        self.background_label.lower()
        self.background_label.hide()

        # Main layout (horizontal: grid left, panel right)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)

        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.slots_widgets: list[ColorSlotWidget] = []
        self.slot_groups: list[SlotGroupInfo] = []
        self._group_headers: list[SlotGroupHeader] = []  # header widgets in the grid
        self._gradient_source: ColorSlotWidget | None = None  # Gradient selection mode
        self._selected_slot: ColorSlotWidget | None = None  # Currently selected slot
        self.undo_manager = UndoManager()
        self.rows = self.settings_manager.starting_rows
        self.cols = self.settings_manager.starting_cols
        self.preview_grid = PreviewGrid()

        for _ in range(self.rows * self.cols):
            slot = ColorSlot(base_size=MIN_SLOT_SIZE, max_size=MAX_SLOT_SIZE, theme_manager=self.theme_manager)
            slot.color = self._get_default_slot_color()
            widget = ColorSlotWidget(slot, self.preview_grid, self)
            widget.hex_label.setText(slot.color.name())
            self.slots_widgets.append(widget)

        # Create default group containing all initial slots
        self._init_default_group()

        self.update_grid()
        self.zoom_view = ZoomableGraphicsView(self.scroll_content)

        # Right/bottom panel (wrapped in QWidget for easy layout switching)
        self.right_panel = QWidget()
        right_panel_layout = QVBoxLayout(self.right_panel)
        right_panel_layout.setSpacing(8)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_frame = QFrame()
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(4, 4, 4, 4)
        preview_layout.setSpacing(0)

        self.preview_grid.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_grid.setToolTip("Palette preview grid")
        preview_layout.addWidget(self.preview_grid, stretch=1)
        right_panel_layout.addWidget(self.preview_frame, stretch=1)

        # Color history panel (not displayed in main UI; shown in Settings → History tab)
        self.color_history_panel = ColorHistoryPanel(
            max_entries=self.settings_manager.max_history_size,
        )
        self.color_history_panel.set_theme_manager(self.theme_manager)
        self.color_history_panel._tooltip_callback = self._show_tooltip_at

        right_buttons = [
            ("Add Color Slot", "add"),
            ("Import Palette", "import"),
            ("Export Palette", "export"),
            ("Clear All", "clear_all"),
            ("Reset Zoom/Pan", "reset"),
            ("Save Preview", "save"),
        ]

        self.right_buttons_dict: dict[str, ImageButton] = {}

        for text, img_name in right_buttons:
            base_img, hover_img, pressed_img = get_button_image_paths(img_name)

            btn = ImageButton(text, base_img, hover_img, pressed_img)
            btn.set_theme_manager(self.theme_manager)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(35)
            right_panel_layout.addWidget(btn)
            self.right_buttons_dict[text] = btn

        # Connect button signals
        self.right_buttons_dict["Add Color Slot"].clicked.connect(self.add_slot)
        self.right_buttons_dict["Add Color Slot"].setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.right_buttons_dict["Add Color Slot"].customContextMenuRequested.connect(
            self._show_add_menu
        )
        self.right_buttons_dict["Import Palette"].clicked.connect(self.import_palette)
        self.right_buttons_dict["Import Palette"].setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.right_buttons_dict["Import Palette"].customContextMenuRequested.connect(
            self._show_recent_palettes_menu
        )
        self.right_buttons_dict["Export Palette"].clicked.connect(self.export_palette)
        self.right_buttons_dict["Export Palette"].setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.right_buttons_dict["Export Palette"].customContextMenuRequested.connect(
            self._show_export_menu
        )
        self.right_buttons_dict["Save Preview"].clicked.connect(self.save_preview)
        self.right_buttons_dict["Reset Zoom/Pan"].clicked.connect(lambda: self.zoom_view.reset_view())
        self.right_buttons_dict["Clear All"].clicked.connect(self.clear_all_unlocked_slots)

        # Tooltips for right panel buttons
        self.right_buttons_dict["Add Color Slot"].setToolTip("Add new color slot (Ctrl+N)\nRight-click: Random color options")
        self.right_buttons_dict["Import Palette"].setToolTip("Import palette from file (Ctrl+I)\nRight-click: Recent palettes")
        self.right_buttons_dict["Export Palette"].setToolTip("Export palette to file (Ctrl+E)\nRight-click: Batch export")
        self.right_buttons_dict["Clear All"].setToolTip("Clear all unlocked color slots")
        self.right_buttons_dict["Reset Zoom/Pan"].setToolTip("Reset zoom and pan (Ctrl+R)")
        self.right_buttons_dict["Save Preview"].setToolTip("Save preview grid as image (Ctrl+S)")

        right_panel_layout.addStretch()

        # Add widgets to main layout — left panel with search bar + zoom view
        self.color_search_bar = ColorSearchBar(parent=None)
        self.color_search_bar.search_changed.connect(self._on_search_changed)
        self.color_search_bar.search_cleared.connect(self._on_search_cleared)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(self.color_search_bar)
        left_layout.addWidget(self.zoom_view, stretch=1)

        main_layout.addWidget(left_panel, stretch=3)
        main_layout.addWidget(self.right_panel, stretch=2)

        # Theme button (bottom-right corner)
        self.theme_button = QPushButton(self.theme_manager.get_theme_display_name(), self)
        self.theme_button.clicked.connect(self.cycle_theme)
        self.theme_button.setToolTip("Cycle theme (Ctrl+T)")
        self.theme_button.raise_()

        # Settings gear icon (top-right corner, floating -- always uses images)
        settings_base, settings_hover, settings_pressed = get_button_image_paths("settings_gear")
        self.btn_settings = ImageButton("", settings_base, settings_hover, settings_pressed, parent=self)
        self.btn_settings._always_use_images = True
        self.btn_settings.set_theme_manager(self.theme_manager)
        self.btn_settings.setFixedSize(30, 30)
        self.btn_settings.setToolTip("Settings (Ctrl+,)")
        self.btn_settings.clicked.connect(self.open_settings)
        # Force icon on regardless of theme mode
        if settings_base and Path(settings_base).exists():
            self.btn_settings._icon = QIcon(settings_base)
            self.btn_settings.setIcon(self.btn_settings._icon)
            self.btn_settings.setIconSize(QSize(30, 30))
        self.btn_settings.raise_()

        # Size overlay
        self.size_overlay = QLabel(self)
        self.size_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.size_overlay.setFixedSize(120, 40)
        self.size_overlay.setToolTip("Window size percentage (F12 to toggle)")
        self.size_overlay.raise_()

        self.apply_theme()

        # Apply initial appearance settings (border style, overlay visibility, etc.)
        self._apply_appearance_settings()

        # Phase 1: Restore window geometry from settings
        saved_geometry = self.settings_manager.restore_window_geometry()
        if saved_geometry:
            self.restoreGeometry(saved_geometry)
            logger.debug("Restored window geometry from settings")

        # Phase 1: Session restore logic
        self._try_restore_session()

        # Phase 1: Start auto-save if enabled
        if self.settings_manager.auto_save_enabled:
            self.session_manager.start_auto_save(
                interval_ms=self.settings_manager.auto_save_interval_ms
            )

        # Phase 4: Register keyboard shortcuts
        self._setup_shortcuts()

        # Phase 5: Apply saved color blindness simulation
        saved_mode = self.settings_manager.color_blindness_mode
        if saved_mode and saved_mode != "none":
            self.preview_grid.simulation_mode = saved_mode

        # Install application-level event filter for custom themed tooltips
        # (bypasses native Windows tooltip rendering that ignores CSS border-radius)
        QApplication.instance().installEventFilter(self)

        logger.success("Application initialized successfully")

    def showEvent(self, event) -> None:
        """Handle show event - fix layout after initial display"""
        super().showEvent(event)
        QTimer.singleShot(0, self._post_show_fix)

    def _post_show_fix(self) -> None:
        """Post-show layout fixes"""
        self.update_all_slot_sizes()
        if hasattr(self, "zoom_view"):
            self.zoom_view.update_scene_rect()
        # Fix overlay position on first show
        self._update_overlay_positions()
        # Refresh expanded color info + force slot repaint
        self.refresh_all_color_info()
        for w in self.slots_widgets:
            w.slot.update()
        # Re-sync scene rect after labels may have changed height
        if hasattr(self, "zoom_view"):
            self.zoom_view.update_scene_rect()
        # Image mode: apply the backing-store rebuild INLINE at 0ms so the
        # first paint the user perceives is already correct. The 400ms and
        # 1000ms passes below remain as insurance against harder-to-pin
        # timing edge cases on slower hardware.
        if self.theme_manager.is_image_mode():
            self._force_image_mode_refresh()
            QTimer.singleShot(400, self._post_show_fix_image)

    def _post_show_fix_image(self) -> None:
        """Second-pass repaint for image mode compositor settling.

        The slots live inside a QGraphicsProxyWidget, and on cold start
        the proxy's first rasterization can produce solid-black slots
        instead of the intended semi-transparent fills. A user-triggered
        theme cycle reliably clears the bug; calling apply_theme() alone
        from a QTimer does not. The missing ingredient is the forced
        WA_TranslucentBackground False->True toggle on scroll_content /
        preview_frame that a real cycle performs (when going through a
        non-image theme), which rebuilds Qt's backing stores. We
        reproduce that toggle explicitly here via _force_image_mode_refresh.
        """
        self.refresh_all_color_info()
        if self.theme_manager.is_image_mode():
            self._force_image_mode_refresh()
        for w in self.slots_widgets:
            w.slot.update()
        if hasattr(self, "zoom_view"):
            self.zoom_view.update_scene_rect()
            self.zoom_view.reset_view()
        # Belt-and-suspenders: schedule a final insurance pass at ~1000ms
        # total elapsed from show. If the 400ms pass caught it this is a
        # visual no-op; if not, this gets another shot against a
        # more-settled pipeline.
        QTimer.singleShot(600, self._post_show_fix_image_final)

    def _post_show_fix_image_final(self) -> None:
        """Third-pass insurance repaint for slower hardware.

        Only runs if still in image mode (user may have cycled themes
        during the 600ms window). Same backing-store rebuild pattern as
        the 400ms pass. Deliberately omits scene-rect and view-reset so
        we don't disrupt any zoom/pan the user may have initiated.
        """
        if not self.theme_manager.is_image_mode():
            return
        self._force_image_mode_refresh()
        for w in self.slots_widgets:
            w.slot.update()

    def _force_image_mode_refresh(self) -> None:
        """Reproduce a user-triggered theme cycle's rendering-state reset.

        Calling apply_theme() alone while already in image mode is not
        enough because Qt treats setAttribute(WA_TranslucentBackground,
        True) as a no-op when the attribute is already True -- no backing
        store rebuild happens. A real user cycle goes image -> non-image
        -> ... -> image, which forces the attribute through True -> False
        -> ... -> True on scroll_content and preview_frame, rebuilding
        their backing stores. We reproduce that False -> True transition
        here explicitly, then run the same tail sequence that cycle_theme
        uses (apply_theme + update_slot_colors_for_theme + update +
        processEvents) so the rendering state is reset identically.
        """
        # Force backing-store rebuild on the translucent widgets by
        # toggling the attribute off, pumping events so Qt acts on it,
        # then toggling it back on.
        self.scroll_content.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, False
        )
        self.preview_frame.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, False
        )
        QApplication.processEvents()
        self.scroll_content.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, True
        )
        self.preview_frame.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, True
        )
        # Mirror cycle_theme()'s tail: re-apply theme, refresh slot colors,
        # repaint main window, pump events synchronously.
        self.apply_theme()
        self.update_slot_colors_for_theme()
        self.update()
        QApplication.processEvents()

    # ==================================================================
    # Appearance Settings
    # ==================================================================

    def _apply_border_style(self, style: str = "thin") -> None:
        """Apply border style to all color slots."""
        for widget in self.slots_widgets:
            widget.slot.border_style = style
        logger.debug(f"Slot border style set to: {style}")

    def _apply_size_overlay_visibility(self, visible: bool = True) -> None:
        """Show or hide the size percentage overlay."""
        self.size_overlay.setVisible(visible)
        logger.debug(f"Size overlay visible: {visible}")

    def _toggle_size_overlay(self) -> None:
        """Toggle size overlay visibility (F12)."""
        new_state = not self.size_overlay.isVisible()
        self.size_overlay.setVisible(new_state)
        self.settings_manager.show_size_overlay = new_state
        logger.debug(f"Size overlay toggled: {new_state}")

    def _toggle_tooltips(self) -> None:
        """Toggle tooltips on/off application-wide (F11)."""
        tip = _ThemedToolTip.instance()
        tip._enabled = not tip._enabled
        if not tip._enabled:
            tip.hide_tip()  # Immediately hide if currently showing
        logger.debug(f"Tooltips {'enabled' if tip._enabled else 'disabled'}")

    def _show_tooltip_at(self, global_pos: QPoint, text: str) -> None:
        """Show a themed tooltip programmatically (e.g. 'Copied #hex')."""
        theme = self.theme_manager.get_current_theme()
        if theme:
            _ThemedToolTip.instance().show_tip(
                global_pos, text, theme, get_font_family(),
            )

    def _update_overlay_positions(self) -> None:
        """Reposition floating overlays based on current window size."""
        if hasattr(self, "btn_settings"):
            self.btn_settings.move(
                self.width() - self.btn_settings.width() - 20, 20,
            )
            self.size_overlay.move(
                self.btn_settings.x() - self.size_overlay.width() - 4, 20,
            )

    def _apply_appearance_settings(self) -> None:
        """Apply all appearance settings from SettingsManager."""
        self._apply_border_style(self.settings_manager.slot_border_style)
        self._apply_size_overlay_visibility(self.settings_manager.show_size_overlay)
        self.update_all_slot_sizes()

    # ==================================================================
    # Phase 4: Keyboard Shortcuts
    # ==================================================================

    def _setup_shortcuts(self) -> None:
        """Register all keyboard shortcuts."""
        shortcuts = {
            "Ctrl+Z": self.undo,
            "Ctrl+Shift+Z": self.redo,
            "Ctrl+Y": self.redo,
            "Ctrl+N": self.add_slot,
            "Ctrl+I": self.import_palette,
            "Ctrl+E": self.export_palette,
            "Ctrl+Shift+E": self.batch_export,
            "Ctrl+S": self.save_preview,
            "Ctrl+D": self._shortcut_duplicate,
            "Ctrl+C": self._shortcut_copy,
            "Ctrl+T": self.cycle_theme,
            "Ctrl+,": self.open_settings,
            "Ctrl+/": self.open_about,
            "Ctrl+R": lambda: self.zoom_view.reset_view(),
            "Delete": self._shortcut_delete,
            "Space": self._shortcut_toggle_lock,
            "Escape": self._shortcut_escape,
            "Left": lambda: self._shortcut_navigate(-1),
            "Right": lambda: self._shortcut_navigate(1),
            "F10": self._toggle_fullscreen,
            "F11": self._toggle_tooltips,
            "F12": self._toggle_size_overlay,
            "Ctrl+F": self._toggle_search,
        }
        for key, callback in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)

    # ==================================================================
    # Phase 4: Selection
    # ==================================================================

    def select_slot(self, widget: ColorSlotWidget | None) -> None:
        """Select a slot (deselecting any previously selected)."""
        if self._selected_slot is not None:
            self._selected_slot.set_selected(False)
        self._selected_slot = widget
        if widget is not None:
            widget.set_selected(True)

    # ==================================================================
    # Phase 4: Undo / Redo
    # ==================================================================

    def _push_undo(self) -> None:
        """Capture current state and push onto undo stack."""
        groups_data = [g.to_data().to_dict() for g in self.slot_groups]
        state = PaletteState.capture(
            self.slots_widgets, self.palette_metadata.to_dict(), groups_data
        )
        self.undo_manager.push(state)

    def undo(self) -> None:
        """Undo the last action."""
        groups_data = [g.to_data().to_dict() for g in self.slot_groups]
        current = PaletteState.capture(
            self.slots_widgets, self.palette_metadata.to_dict(), groups_data
        )
        previous = self.undo_manager.undo(current)
        if previous is not None:
            self._restore_palette_state(previous)

    def redo(self) -> None:
        """Redo the last undone action."""
        groups_data = [g.to_data().to_dict() for g in self.slot_groups]
        current = PaletteState.capture(
            self.slots_widgets, self.palette_metadata.to_dict(), groups_data
        )
        next_state = self.undo_manager.redo(current)
        if next_state is not None:
            self._restore_palette_state(next_state)

    def _restore_palette_state(self, state: PaletteState) -> None:
        """Restore the palette to a saved state."""
        # Remove all current slots
        for w in self.slots_widgets[:]:
            self.grid_layout.removeWidget(w)
            w.hide()
            w.setParent(None)
            w.deleteLater()
        self.slots_widgets.clear()
        self._selected_slot = None

        # Clear groups and headers
        self._destroy_headers()
        self.slot_groups.clear()

        # Recreate slots from state
        for snap in state.slots:
            slot = ColorSlot(
                base_size=MIN_SLOT_SIZE, max_size=MAX_SLOT_SIZE,
                theme_manager=self.theme_manager,
            )
            slot.color = QColor(snap["r"], snap["g"], snap["b"], snap["a"])
            slot._is_default_color = snap.get("is_default_color", False)
            widget = ColorSlotWidget(slot, self.preview_grid, self)
            widget.hex_label.setText(snap.get("hex_text", slot.color.name()))
            widget.locked = snap.get("locked", False)
            widget.update_lock_button()
            self.slots_widgets.append(widget)

        # Restore groups from state (or default single group)
        if state.groups:
            self._restore_groups_from_data(state.groups)
        else:
            self._init_default_group()

        # Restore metadata if present
        if state.metadata:
            self._set_metadata(PaletteMetadata.from_dict(state.metadata))

        self.update_grid()
        logger.debug("Palette state restored")

    # ==================================================================
    # Palette Metadata
    # ==================================================================

    def _set_metadata(self, metadata: PaletteMetadata) -> None:
        """Replace current metadata and update the window title."""
        self.palette_metadata = metadata
        self._update_window_title()

    def _reset_metadata(self) -> None:
        """Reset metadata to defaults (new palette)."""
        self._set_metadata(PaletteMetadata())

    def _update_window_title(self) -> None:
        """Update the window title to reflect the current palette name."""
        name = self.palette_metadata.display_name
        if name and name != "Untitled Palette":
            self.setWindowTitle(f"{name} — {APP_NAME}")
        else:
            self.setWindowTitle(APP_NAME)

    # ==================================================================
    # Phase 4: Shortcut Helpers
    # ==================================================================

    def _shortcut_escape(self) -> None:
        """Escape: close search if open, otherwise deselect slot."""
        if self.color_search_bar.isVisible():
            self.color_search_bar.close_search()
        else:
            self.select_slot(None)

    def _shortcut_duplicate(self) -> None:
        if self._selected_slot:
            self._push_undo()
            self.duplicate_slot(self._selected_slot)

    def _shortcut_copy(self) -> None:
        if self._selected_slot:
            self._selected_slot._on_hex_label_clicked(None)

    def _shortcut_delete(self) -> None:
        if self._selected_slot and not self._selected_slot.locked:
            self._push_undo()
            self.remove_slot(self._selected_slot)
            self._selected_slot = None

    def _shortcut_toggle_lock(self) -> None:
        if self._selected_slot:
            self._selected_slot.toggle_lock()

    def _shortcut_navigate(self, direction: int) -> None:
        """Navigate slot selection with arrow keys."""
        if not self.slots_widgets:
            return
        if self._selected_slot is None:
            self.select_slot(self.slots_widgets[0])
            return
        idx = self.slots_widgets.index(self._selected_slot) if self._selected_slot in self.slots_widgets else -1
        new_idx = max(0, min(len(self.slots_widgets) - 1, idx + direction))
        self.select_slot(self.slots_widgets[new_idx])

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def apply_theme_button_style(self) -> None:
        """Apply current theme to the theme toggle button"""
        theme = self.theme_manager.get_current_theme()
        if not theme:
            return

        self.theme_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['button_bg']};
                color: {theme['button_text']};
                border: 1px solid {theme['border_color']};
                padding: 2px 6px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover_bg']};
                color: {theme.get('button_hover_text', theme['button_text'])};
            }}
            QPushButton:pressed {{
                background-color: {theme['button_pressed_bg']};
                color: {theme.get('button_pressed_text', theme['button_text'])};
            }}
        """)

    def cycle_theme(self) -> None:
        """Cycle through available themes"""
        self.theme_manager.cycle_theme()
        self.theme_button.setText(self.theme_manager.get_theme_display_name())
        self.apply_theme()
        self.update_slot_colors_for_theme()
        self.update()
        QApplication.processEvents()

    def update_slot_colors_for_theme(self) -> None:
        """Update default-colored slots when theme changes."""
        for widget in self.slots_widgets:
            slot = widget.slot
            if slot._is_default_color:
                slot.color = self._get_default_slot_color()
                widget.hex_label.setText(slot.color.name())
                slot.update()

        self.update_preview()

    def apply_theme(self) -> None:
        """Apply current theme to all UI components"""
        theme = self.theme_manager.get_current_theme()
        is_image = self.theme_manager.is_image_mode()

        # For context menus and dialogs in image mode, use dark theme colors
        menu_theme = ThemeManager.DARK_THEME if is_image else theme

        # Set palette
        palette = QPalette()
        window_color = QColor(theme['window_bg'])
        text_color = QColor(theme['text_color'])

        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, window_color)
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, text_color)
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, window_color)
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, text_color)

        # Replace OS blue with brand gold — only safe roles that don't break QColorDialog.
        is_light_theme = (not is_image and self.theme_manager.current_theme == 'light')
        gold      = QColor(BRAND_GOLD_DARK) if is_light_theme else QColor(BRAND_GOLD)
        gold_dark = QColor(BRAND_GOLD_DARK)
        on_gold   = QColor(ACCENT_PRESSED_TEXT_DARK)

        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive,
                      QPalette.ColorGroup.Disabled):
            palette.setColor(group, QPalette.ColorRole.Highlight,       gold)
            palette.setColor(group, QPalette.ColorRole.HighlightedText, on_gold)
            palette.setColor(group, QPalette.ColorRole.Link,            gold)
            palette.setColor(group, QPalette.ColorRole.LinkVisited,     gold_dark)

        QApplication.instance().setPalette(palette)

        # Get scrollbar styles
        if is_image:
            scrollbar_style = ThemeManager.SCROLLBAR_IMAGE
        elif self.theme_manager.current_theme == 'dark':
            scrollbar_style = ThemeManager.SCROLLBAR_DARK
        else:
            scrollbar_style = ThemeManager.SCROLLBAR_LIGHT

        # Build QMenu stylesheet (theme-aware)
        # Applied at QApplication level because QMenu popups are top-level
        # windows that don't inherit QMainWindow stylesheets.
        # Note: QToolTip styling is handled by _ThemedToolTip class, not CSS.
        card_bg = menu_theme.get('card_bg', menu_theme['button_bg'])

        # Brand gold constants from centralized colors module
        GOLD = BRAND_GOLD
        GOLD_DARK = BRAND_GOLD_DARK

        # Dark/image hover: bg stays dark, gold text+border; press: gold bg, black text
        # Light hover: white bg, dark-gold text+border; press: dark-gold bg, white text
        is_light = (not is_image and self.theme_manager.current_theme == 'light')

        if is_light:
            menu_hover_bg = menu_theme['button_bg']       # white stays
            menu_hover_text = GOLD_DARK                    # dark gold
            menu_hover_border = GOLD_DARK
            menu_pressed_bg = GOLD_DARK                    # dark gold bg
            menu_pressed_text = ACCENT_PRESSED_TEXT_LIGHT  # white text
            menu_pressed_border = GOLD_DARK
            accent = GOLD_DARK                             # for selection highlight
        else:
            menu_hover_bg = menu_theme['button_bg']       # black stays
            menu_hover_text = GOLD                         # gold
            menu_hover_border = GOLD
            menu_pressed_bg = GOLD                         # gold bg
            menu_pressed_text = ACCENT_PRESSED_TEXT_DARK   # black text
            menu_pressed_border = GOLD
            accent = GOLD                                  # for selection highlight

        menu_bg = 'transparent' if is_image else menu_theme['button_bg']

        # Selection/highlight colors: gold bg with contrasting text
        sel_bg = accent
        sel_text = ACCENT_PRESSED_TEXT_DARK if not is_light else ACCENT_PRESSED_TEXT_LIGHT

        # Get the loaded font family for stylesheet propagation
        font_family = get_font_family()

        app_wide_style = f"""
            /* ---- Global font (ensures popups/dialogs inherit) ---- */
            * {{
                font-family: '{font_family}';
            }}

            /* ---- Global text selection colors ---- */
            QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {{
                selection-background-color: {sel_bg};
                selection-color: {sel_text};
            }}

            /* ---- ComboBox dropdown list ---- */
            QComboBox QAbstractItemView {{
                selection-background-color: {sel_bg};
                selection-color: {sel_text};
            }}

            QMenu {{
                background-color: {menu_bg};
                color: {menu_theme['button_text']};
                border: none;
                padding: 0px;
            }}
            QMenu::item {{
                background-color: transparent;
                color: {menu_theme['button_text']};
                padding: 6px 24px 6px 12px;
                border: 1px solid transparent;
                margin: 0px;
            }}
            QMenu::item:selected {{
                background-color: {menu_hover_bg};
                color: {menu_hover_text};
                border: 1px solid {menu_hover_border};
            }}
            QMenu::item:pressed {{
                background-color: {menu_pressed_bg};
                color: {menu_pressed_text};
                border: 1px solid {menu_pressed_border};
            }}
            QMenu::item:disabled {{
                color: {menu_theme['text_disabled']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {menu_theme['border_color']};
                margin: 4px 8px;
            }}

            /* ---- QColorDialog buttons: match dialog button style (card_bg + gold) ---- */
            QColorDialog QPushButton {{
                background-color: {theme['card_bg']};
                color: {theme['button_text']};
                border: 1px solid {theme['border_color']};
                border-radius: 4px;
                padding: 4px 16px;
                min-width: 60px;
                font-weight: bold;
            }}
            QColorDialog QPushButton:hover {{
                background-color: {theme['card_bg']};
                color: {accent};
                border-color: {accent};
            }}
            QColorDialog QPushButton:pressed {{
                background-color: {accent};
                color: {ACCENT_PRESSED_TEXT_LIGHT if is_light else ACCENT_PRESSED_TEXT_DARK};
                border-color: {accent};
            }}
            QColorDialog QPushButton:default {{
                border-color: {accent};
            }}
            QColorDialog QSpinBox:focus,
            QColorDialog QLineEdit:focus {{
                border: 1px solid {accent};
                outline: none;
            }}
             /* ---- QInputDialog buttons: match dialog button style (card_bg + gold) ---- */
            QInputDialog QPushButton {{
                background-color: {theme['card_bg']};
                color: {theme['button_text']};
                border: 1px solid {theme['border_color']};
                border-radius: 4px;
                padding: 4px 16px;
                min-width: 60px;
                font-weight: bold;
            }}
            QInputDialog QPushButton:hover {{
                background-color: {theme['card_bg']};
                color: {accent};
                border-color: {accent};
            }}
            QInputDialog QPushButton:pressed {{
                background-color: {accent};
                color: {ACCENT_PRESSED_TEXT_LIGHT if is_light else ACCENT_PRESSED_TEXT_DARK};
                border-color: {accent};
            }}
            QInputDialog QPushButton:default {{
                border-color: {accent};
            }}
            QInputDialog QSpinBox:focus,
            QInputDialog QLineEdit:focus {{
                border: 1px solid {accent};
                outline: none;
            }}
        """
        QApplication.instance().setStyleSheet(app_wide_style)

        # Main window background
        self.background_label.hide()

        if is_image and self.theme_manager.background_pixmap:
            self.background_label.setPixmap(self.theme_manager.background_pixmap)
            self.background_label.setGeometry(0, 0, self.width(), self.height())
            self.background_label.show()
            self.setStyleSheet(scrollbar_style)
        else:
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {theme['window_bg']};
                }}
                {scrollbar_style}
            """)

        # Scroll/grid background
        if is_image:
            self.scroll_content.setStyleSheet("background: transparent;")
        else:
            self.scroll_content.setStyleSheet(f"""
                QWidget {{
                    background-color: {theme['scroll_bg']};
                }}
            """)

        # Preview frame
        self.preview_frame.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {theme['border_color']};
                background-color: {theme['panel_bg']};
            }}
        """)

        # Zoom view background
        if is_image and self.theme_manager.background_pixmap:
            self.scroll_content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.zoom_view.setStyleSheet("background: transparent; border: none;")
            self.zoom_view.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
            if hasattr(self.zoom_view, 'scene') and self.zoom_view.scene:
                self.zoom_view.scene.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
            self.preview_frame.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setStyleSheet(scrollbar_style)
        else:
            self.scroll_content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.zoom_view.setStyleSheet(f"background-color: {theme['scroll_bg']};")
            self.zoom_view.setBackgroundBrush(QBrush(QColor(theme['scroll_bg'])))
            if hasattr(self.zoom_view, 'scene') and self.zoom_view.scene:
                self.zoom_view.scene.setBackgroundBrush(QBrush(QColor(theme['scroll_bg'])))
            self.preview_frame.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {theme['window_bg']};
                }}
                {scrollbar_style}
            """)

        # Theme button
        self.apply_theme_button_style()

        # Size overlay
        self.size_overlay.setStyleSheet(f"""
            background-color: {SIZE_OVERLAY_BG};
            color: {theme['text_color']};
            font-weight: bold;
            padding: 4px;
            border-radius: 4px;
        """)

        # Update all buttons
        for btn in self.right_buttons_dict.values():
            btn.apply_style()

        # Settings gear -- always use images, transparent background
        if hasattr(self, 'btn_settings'):
            self.btn_settings.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                }
            """)

        for widget in self.slots_widgets:
            for btn in widget.button_list:
                btn.apply_style()

        self.theme_button.repaint()

        for widget in self.slots_widgets:
            widget.apply_theme()

        # Theme the color history panel
        if hasattr(self, 'color_history_panel'):
            self.color_history_panel.apply_theme()

        # Theme group headers
        for hdr in self._group_headers:
            hdr.apply_theme(theme)

        # Theme search bar
        self.color_search_bar.apply_theme(theme)

    def compute_slot_size(self) -> int:
        """Compute appropriate slot size based on preference and window size."""
        # Check for fixed size preference
        pref = self.settings_manager.slot_size_preference
        match pref:
            case "small":
                return 80
            case "medium":
                return 100
            case "large":
                return 140

        # "auto" — dynamic sizing based on window size
        min_slot = MIN_SLOT_SIZE
        max_slot = MAX_SLOT_SIZE
        min_width, min_height = self.ref_width, self.ref_height
        max_width, max_height = self.ref_width * 1.92, self.ref_height * 1.45
        width_factor = (self.width() - min_width) / (max_width - min_width) if max_width != min_width else 0
        height_factor = (self.height() - min_height) / (max_height - min_height) if max_height != min_height else 0
        scale_factor = max(0.0, min(1.0, max(width_factor, height_factor)))
        return int(min_slot + (max_slot - min_slot) * scale_factor)

    def update_all_slot_sizes(self) -> None:
        """Update all color slot sizes based on count and window size"""
        count = len(self.slots_widgets)
        match count:
            case 1:
                for widget in self.slots_widgets:
                    widget.slot.resize_to_fit(400, max_override=400)
                    widget._update_minimum_size()
                    widget.updateGeometry()
            case 2:
                for widget in self.slots_widgets:
                    widget.slot.resize_to_fit(200, max_override=200)
                    widget._update_minimum_size()
                    widget.updateGeometry()
            case _:
                target_size = self.compute_slot_size()
                for widget in self.slots_widgets:
                    widget.slot.resize_to_fit(target_size)
                    widget._update_minimum_size()
                    widget.updateGeometry()

    def update_grid(self) -> None:
        """Update the grid layout with current slots, inserting group headers when needed."""
        # Ensure at least one group exists
        if not self.slot_groups:
            self._init_default_group()

        # Sync group slot counts so they sum to len(slots_widgets)
        self._sync_group_counts()

        # Clear entire grid
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and (w := item.widget()):
                self.grid_layout.removeWidget(w)

        # Reset row minimum heights from previous layout
        for row in range(self.grid_layout.rowCount()):
            self.grid_layout.setRowMinimumHeight(row, 0)

        # Remove old header widgets
        for hdr in self._group_headers:
            hdr.hide()
            hdr.setParent(None)
            hdr.deleteLater()
        self._group_headers.clear()

        multi_group = len(self.slot_groups) > 1
        grid_row = 0
        slot_offset = 0

        for gi, group in enumerate(self.slot_groups):
            # Insert header row when multiple groups exist
            if multi_group:
                header = SlotGroupHeader(group, parent=self.scroll_content)
                header.toggle_requested.connect(self._on_group_toggle)
                header.name_changed.connect(self._on_group_name_changed)
                header.delete_requested.connect(self._on_group_delete_requested)
                header.add_slot_requested.connect(self._on_group_add_slot)
                header.set_delete_visible(multi_group)
                theme = self.theme_manager.get_current_theme()
                if theme:
                    header.apply_theme(theme)
                self._group_headers.append(header)
                group.header = header
                # Span header across enough columns
                span_cols = max(4, (group.slot_count + self.rows - 1) // self.rows) if group.slot_count else 4
                self.grid_layout.addWidget(header, grid_row, 0, 1, span_cols)
                grid_row += 1

            # Place slots for this group (skip if collapsed)
            if not group.collapsed:
                for local_idx in range(group.slot_count):
                    flat_idx = slot_offset + local_idx
                    if flat_idx >= len(self.slots_widgets):
                        break
                    widget = self.slots_widgets[flat_idx]
                    row_in_group = local_idx % self.rows
                    col_in_group = local_idx // self.rows
                    actual_row = grid_row + row_in_group
                    self.grid_layout.addWidget(
                        widget, actual_row, col_in_group,
                    )
                    widget.show()

                # Advance grid_row past this group's rows
                if group.slot_count > 0:
                    rows_used = min(self.rows, group.slot_count)
                    grid_row += rows_used
            else:
                # Collapsed — hide all slots in this group
                for local_idx in range(group.slot_count):
                    flat_idx = slot_offset + local_idx
                    if flat_idx < len(self.slots_widgets):
                        self.slots_widgets[flat_idx].hide()

            slot_offset += group.slot_count

        # Refresh header badges
        for hdr in self._group_headers:
            hdr.refresh()

        self.update_preview()
        self.update_all_slot_sizes()

        # Compute per-row maximum widget heights AFTER slot sizing is finalized
        _row_max_heights: dict[int, int] = {}
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), ColorSlotWidget):
                row, col, _, _ = self.grid_layout.getItemPosition(i)
                h = item.widget().sizeHint().height()
                if row not in _row_max_heights or h > _row_max_heights[row]:
                    _row_max_heights[row] = h

        # Set explicit row minimum heights so grid cells aren't clipped
        for row_idx, row_h in _row_max_heights.items():
            self.grid_layout.setRowMinimumHeight(row_idx, row_h)

        # Minimum height for scroll content
        if self.slots_widgets:
            spacing = self.grid_layout.spacing()
            total_row_height = sum(_row_max_heights.values())
            total_row_spacing = max(0, len(_row_max_heights) - 1) * spacing
            header_height = 32 * len(self._group_headers)
            margins = self.grid_layout.contentsMargins()
            self.scroll_content.setMinimumHeight(
                total_row_height + total_row_spacing + header_height
                + margins.top() + margins.bottom()
            )
        else:
            self.scroll_content.setMinimumHeight(0)

        # Apply current border style to all slots
        if hasattr(self, 'settings_manager'):
            border_style = self.settings_manager.slot_border_style
            for widget in self.slots_widgets:
                widget.slot.border_style = border_style

        # Re-run active search if search bar is visible
        if hasattr(self, 'color_search_bar') and self.color_search_bar.isVisible():
            query = self.color_search_bar.current_text()
            if query:
                self._on_search_changed(query)

        if hasattr(self, "zoom_view") and isinstance(self.zoom_view, ZoomableGraphicsView):
            self.zoom_view.update_scene_rect()

    def _remove_slot_internal(self, slot_widget: ColorSlotWidget) -> None:
        """Remove a slot without pushing undo (for batch operations)."""
        if slot_widget is self._selected_slot:
            self._selected_slot = None
        if slot_widget in self.slots_widgets:
            # Find which group owns this slot and decrement its count
            idx = self.slots_widgets.index(slot_widget)
            offset = 0
            for group in self.slot_groups:
                if offset <= idx < offset + group.slot_count:
                    group.slot_count -= 1
                    break
                offset += group.slot_count
            self.slots_widgets.remove(slot_widget)
        self.grid_layout.removeWidget(slot_widget)
        slot_widget.hide()
        slot_widget.setParent(None)
        slot_widget.deleteLater()

    def remove_slot(self, slot_widget: ColorSlotWidget) -> None:
        """Remove a color slot from the grid (pushes undo)."""
        self._push_undo()
        self._remove_slot_internal(slot_widget)
        self.update_grid()

    def clear_all_unlocked_slots(self) -> None:
        """Clear all unlocked color slots (single undo point)."""
        unlocked = [w for w in self.slots_widgets if not w.locked]
        if not unlocked:
            return
        self._push_undo()
        for widget in unlocked:
            self._remove_slot_internal(widget)
        self.update_grid()

    # ==================================================================
    # Drag-and-Drop Slot Reordering
    # ==================================================================

    def reorder_slot(self, source_idx: int, target_idx: int) -> None:
        """Move a slot from source_idx to target_idx position."""
        if source_idx == target_idx:
            return
        if not (0 <= source_idx < len(self.slots_widgets)):
            return
        if not (0 <= target_idx < len(self.slots_widgets)):
            return

        self._push_undo()

        widget = self.slots_widgets.pop(source_idx)
        self.slots_widgets.insert(target_idx, widget)
        self.update_grid()
        logger.info(f"Slot reordered: {source_idx} → {target_idx}")

    # ==================================================================
    # Slot Groups
    # ==================================================================

    def _init_default_group(self) -> None:
        """Create a single default group containing all current slots."""
        self._destroy_headers()
        self.slot_groups.clear()
        group = SlotGroupInfo(name="", slot_count=len(self.slots_widgets))
        self.slot_groups.append(group)

    def _destroy_headers(self) -> None:
        """Destroy all header widgets."""
        for hdr in self._group_headers:
            hdr.hide()
            hdr.setParent(None)
            hdr.deleteLater()
        self._group_headers.clear()

    def _sync_group_counts(self) -> None:
        """Ensure group slot_counts sum to len(slots_widgets).
        Any excess slots go to the last group."""
        total = sum(g.slot_count for g in self.slot_groups)
        diff = len(self.slots_widgets) - total
        if diff != 0 and self.slot_groups:
            self.slot_groups[-1].slot_count += diff
            # Clamp to zero minimum
            if self.slot_groups[-1].slot_count < 0:
                self.slot_groups[-1].slot_count = 0

    def _groups_data(self) -> list[dict]:
        """Return serializable list of current group data."""
        return [g.to_data().to_dict() for g in self.slot_groups]

    def _restore_groups_from_data(self, groups_data: list[dict]) -> None:
        """Rebuild SlotGroupInfo objects from serialized data."""
        self._destroy_headers()
        self.slot_groups.clear()
        for gd in groups_data:
            data = SlotGroupData.from_dict(gd)
            info = SlotGroupInfo.from_data(data)
            self.slot_groups.append(info)
        # Sync counts to actual slot list
        self._sync_group_counts()

    def _flat_index_for_group_end(self, group: SlotGroupInfo) -> int:
        """Return the flat-list index just past the last slot of the given group."""
        offset = 0
        for g in self.slot_groups:
            offset += g.slot_count
            if g is group:
                return offset
        return len(self.slots_widgets)

    def _flat_index_for_group_start(self, group: SlotGroupInfo) -> int:
        """Return the flat-list index of the first slot in the given group."""
        offset = 0
        for g in self.slot_groups:
            if g is group:
                return offset
            offset += g.slot_count
        return offset

    def add_group(self, name: str = "") -> SlotGroupInfo:
        """Add a new empty group at the end."""
        self._push_undo()
        group = SlotGroupInfo(name=name, slot_count=0)
        self.slot_groups.append(group)
        self.update_grid()
        logger.info(f"Added group: '{name or 'Unnamed'}'")
        return group

    def _on_group_toggle(self, group: SlotGroupInfo) -> None:
        """Toggle collapse state for a group."""
        group.collapsed = not group.collapsed
        self.update_grid()

    def _on_group_name_changed(self, group: SlotGroupInfo, new_name: str) -> None:
        """Handle group rename."""
        group.name = new_name
        logger.debug(f"Group renamed: '{new_name}'")

    def _on_group_add_slot(self, group: SlotGroupInfo) -> None:
        """Add a new color slot directly into a specific group."""
        if len(self.slots_widgets) >= MAX_SLOTS:
            DialogHelper.show_warning(self, f"Maximum {MAX_SLOTS} color slots allowed!")
            return
        self._push_undo()
        slot = ColorSlot(base_size=MIN_SLOT_SIZE, max_size=MAX_SLOT_SIZE, theme_manager=self.theme_manager)
        slot.color = self._get_default_slot_color()
        widget = ColorSlotWidget(slot, self.preview_grid, self)
        widget.hex_label.setText(slot.color.name())
        self._insert_into_group(widget, group)
        self.update_grid()

    def _on_group_delete_requested(self, group: SlotGroupInfo) -> None:
        """Handle group deletion — merge its slots into the adjacent group."""
        if len(self.slot_groups) <= 1:
            return
        self._push_undo()
        idx = self.slot_groups.index(group)
        # Merge slot_count into previous group (or next if first)
        target = self.slot_groups[idx - 1] if idx > 0 else self.slot_groups[idx + 1]
        target.slot_count += group.slot_count
        self.slot_groups.remove(group)
        self.update_grid()
        logger.info(f"Deleted group '{group.name}', slots merged")

    def move_slot_to_group(self, slot_widget: ColorSlotWidget, target_group: SlotGroupInfo) -> None:
        """Move a slot from its current group to a target group."""
        if slot_widget.locked:
            return
        if slot_widget not in self.slots_widgets:
            return

        # Find source group
        source_group = self.get_group_for_slot(slot_widget)
        if source_group is target_group or source_group is None:
            return

        self._push_undo()

        # Remove from flat list
        old_idx = self.slots_widgets.index(slot_widget)
        self.slots_widgets.remove(slot_widget)
        source_group.slot_count -= 1

        # Insert at end of target group's range
        insert_at = self._flat_index_for_group_end(target_group)
        # Adjust if we removed before the insert point
        if old_idx < insert_at:
            insert_at -= 1
        self.slots_widgets.insert(insert_at, slot_widget)
        target_group.slot_count += 1

        self.update_grid()
        logger.info(f"Moved slot to group '{target_group.name or 'Unnamed'}'")

    def get_group_for_slot(self, slot_widget: ColorSlotWidget) -> SlotGroupInfo | None:
        """Return the group that contains the given slot widget."""
        if slot_widget not in self.slots_widgets:
            return None
        idx = self.slots_widgets.index(slot_widget)
        offset = 0
        for g in self.slot_groups:
            if offset <= idx < offset + g.slot_count:
                return g
            offset += g.slot_count
        return None

    def get_group_names(self) -> list[str]:
        """Return list of all group names (for context menus)."""
        return [g.name or f"Group {i + 1}" for i, g in enumerate(self.slot_groups)]

    # ==================================================================

    def _get_active_group(self) -> SlotGroupInfo:
        """Return the group to add new slots to.
        Uses the selected slot's group, or the last group as fallback."""
        if self._selected_slot:
            group = self.get_group_for_slot(self._selected_slot)
            if group:
                return group
        return self.slot_groups[-1]

    def _insert_into_group(self, widget: ColorSlotWidget, group: SlotGroupInfo) -> None:
        """Insert a widget into the flat list at the end of the given group
        and increment the group's slot count."""
        insert_at = self._flat_index_for_group_end(group)
        self.slots_widgets.insert(insert_at, widget)
        group.slot_count += 1

    # ==================================================================
    # Phase 6: Color Search & Filter
    # ==================================================================

    def _toggle_search(self) -> None:
        """Toggle the search bar (Ctrl+F)."""
        self.color_search_bar.toggle()

    def _on_search_changed(self, query: str) -> None:
        """Handle search input — highlight matching slots, dim the rest."""
        if not query:
            self._on_search_cleared()
            return

        # Check if query matches a group name first
        query_lower = query.lower()
        group_match_indices: set[int] = set()
        offset = 0
        for group in self.slot_groups:
            group_name = (group.name or "").lower()
            if query_lower in group_name and group_name:
                for i in range(group.slot_count):
                    group_match_indices.add(offset + i)
            offset += group.slot_count

        # Try to parse as a color
        target_rgb = parse_color_query(query)

        match_indices: list[int] = []

        for i, widget in enumerate(self.slots_widgets):
            slot = widget.slot
            is_match = False

            # Group name match
            if i in group_match_indices:
                is_match = True

            # Color match (hex exact, name exact, or distance-based)
            if target_rgb is not None and not is_match:
                slot_rgb = (slot.color.red(), slot.color.green(), slot.color.blue())
                distance = ColorMath.color_distance(slot_rgb, target_rgb)
                if distance <= MATCH_THRESHOLD:
                    is_match = True

            # Substring match on hex value (e.g. "d" matches #1d1d1d, "ff00" matches #ff0000)
            if not is_match:
                slot_hex = slot.color.name().lower()  # e.g. "#a9a9a9"
                slot_hex_bare = slot_hex.lstrip("#")   # e.g. "a9a9a9"
                query_bare = query_lower.lstrip("#")
                if query_bare and (query_bare in slot_hex_bare or query_bare in slot_hex):
                    is_match = True

            if is_match:
                match_indices.append(i)
                slot._search_highlight = True
                slot._search_dimmed = False
            else:
                slot._search_highlight = False
                slot._search_dimmed = True
            slot.update()

        # Update match count badge
        self.color_search_bar.set_match_count(len(match_indices), len(self.slots_widgets))

        # Scroll first match into view
        if match_indices:
            first_widget = self.slots_widgets[match_indices[0]]
            # Map the slot's position to scene coordinates for the graphics view
            try:
                pos = first_widget.mapTo(self.scroll_content, QPoint(0, 0))
                rect = QRectF(pos.x(), pos.y(), first_widget.width(), first_widget.height())
                self.zoom_view.ensureVisible(rect, 50, 50)
            except Exception:
                pass  # Widget may not be in hierarchy yet

        logger.debug(f"Search '{query}': {len(match_indices)} matches")

    def _on_search_cleared(self) -> None:
        """Clear all search highlighting."""
        for widget in self.slots_widgets:
            widget.slot._search_highlight = False
            widget.slot._search_dimmed = False
            widget.slot.update()
        self.color_search_bar.set_match_count(-1, 0)

    def _get_default_slot_color(self) -> QColor:
        """Get the default color for new slots based on current theme's setting."""
        theme_name = self.theme_manager.current_theme
        hex_color = self.settings_manager.default_slot_color_for_theme(theme_name)
        color = QColor(hex_color)
        if self.theme_manager.is_image_mode():
            # Image mode uses semi-transparent version
            color.setAlpha(171)
        return color

    def add_slot(self) -> None:
        """Add a new color slot to the active group."""
        if len(self.slots_widgets) >= MAX_SLOTS:
            DialogHelper.show_warning(self, f"Maximum {MAX_SLOTS} color slots allowed!")
            return
        self._push_undo()
        slot = ColorSlot(base_size=MIN_SLOT_SIZE, max_size=MAX_SLOT_SIZE, theme_manager=self.theme_manager)
        slot.color = self._get_default_slot_color()
        widget = ColorSlotWidget(slot, self.preview_grid, self)
        widget.hex_label.setText(slot.color.name())
        self._insert_into_group(widget, self._get_active_group())
        self.update_grid()

    def add_slot_with_color(self, color: QColor) -> None:
        """Add a new slot pre-filled with a specific color (used by palette extraction)."""
        if len(self.slots_widgets) >= MAX_SLOTS:
            return
        slot = ColorSlot(base_size=MIN_SLOT_SIZE, max_size=MAX_SLOT_SIZE, theme_manager=self.theme_manager)
        slot.color = color
        slot._is_default_color = False
        widget = ColorSlotWidget(slot, self.preview_grid, self)
        widget.hex_label.setText(color.name())
        self._insert_into_group(widget, self._get_active_group())
        self.update_grid()

    def duplicate_slot(self, source_widget: ColorSlotWidget) -> None:
        """Duplicate a slot's color into a new adjacent slot."""
        if len(self.slots_widgets) >= MAX_SLOTS:
            DialogHelper.show_warning(self, f"Maximum {MAX_SLOTS} color slots allowed!")
            return
        self._push_undo()
        slot = ColorSlot(base_size=MIN_SLOT_SIZE, max_size=MAX_SLOT_SIZE, theme_manager=self.theme_manager)
        slot.color = QColor(source_widget.slot.color)
        slot._is_default_color = False
        widget = ColorSlotWidget(slot, self.preview_grid, self)
        widget.hex_label.setText(slot.color.name())
        # Insert right after the source in the flat list
        idx = self.slots_widgets.index(source_widget) + 1
        self.slots_widgets.insert(idx, widget)
        # Also register with the source's group
        source_group = self.get_group_for_slot(source_widget)
        if source_group:
            source_group.slot_count += 1
        self.update_grid()

    def move_slot(self, widget: ColorSlotWidget, direction: int) -> None:
        """Move a slot left (-1) or right (+1) in the grid."""
        if widget not in self.slots_widgets:
            return
        idx = self.slots_widgets.index(widget)
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self.slots_widgets):
            return
        self._push_undo()
        self.slots_widgets[idx], self.slots_widgets[new_idx] = (
            self.slots_widgets[new_idx],
            self.slots_widgets[idx],
        )
        self.update_grid()

    # ==================================================================
    # Step 9: Gradient Generation
    # ==================================================================

    def start_gradient_from(self, source_widget: ColorSlotWidget) -> None:
        """Enter gradient selection mode -- next slot click picks the target."""
        self._gradient_source = source_widget
        # Visual hint: change status overlay
        self.size_overlay.setText("Click target slot")
        self.size_overlay.setStyleSheet(
            f"background-color: {SELECTION_OVERLAY_COLOR}; color: {SELECTION_OVERLAY_TEXT}; "
            "font-weight: bold; padding: 4px; border-radius: 4px;"
        )

        # Temporarily re-route left clicks on all other slots
        for w in self.slots_widgets:
            if w is not source_widget:
                w.slot.mousePressEvent = lambda ev, target=w: self._gradient_target_selected(target)

    def _gradient_target_selected(self, target_widget: ColorSlotWidget) -> None:
        """Target slot was clicked -- ask for step count and generate gradient."""
        source = self._gradient_source
        self._cancel_gradient_mode()

        if source is None or source is target_widget:
            return

        # Ask for number of intermediate steps
        count, ok = QInputDialog.getInt(
            self, "Gradient Steps",
            "Number of colors (including start and end):",
            value=5, min=3, max=20,
        )
        if not ok:
            return

        self._push_undo()
        rgb_a = (source.slot.color.red(), source.slot.color.green(), source.slot.color.blue())
        rgb_b = (target_widget.slot.color.red(), target_widget.slot.color.green(), target_widget.slot.color.blue())

        gradient_colors = ColorHarmonies.gradient(rgb_a, rgb_b, steps=count)

        # Insert intermediate colors (skip first and last which are source/target)
        src_idx = self.slots_widgets.index(source) if source in self.slots_widgets else -1
        insert_pos = src_idx + 1 if src_idx >= 0 else len(self.slots_widgets)

        for rgb in gradient_colors[1:-1]:
            if len(self.slots_widgets) >= MAX_SLOTS:
                break
            slot = ColorSlot(
                base_size=MIN_SLOT_SIZE, max_size=MAX_SLOT_SIZE,
                theme_manager=self.theme_manager,
            )
            slot.color = QColor(*rgb)
            slot._is_default_color = False
            widget = ColorSlotWidget(slot, self.preview_grid, self)
            widget.hex_label.setText(slot.color.name())
            self.slots_widgets.insert(insert_pos, widget)
            insert_pos += 1

        self.update_grid()
        logger.info(f"Generated gradient with {count} steps")

    def _cancel_gradient_mode(self) -> None:
        """Exit gradient selection mode and restore normal click handlers."""
        self._gradient_source = None
        # Restore normal click routing on all slots
        for w in self.slots_widgets:
            w.slot.mousePressEvent = w._on_slot_press
        # Reset overlay style
        theme = self.theme_manager.get_current_theme()
        self.size_overlay.setStyleSheet(
            f"background-color: {SIZE_OVERLAY_BG}; color: {theme['text_color']}; "
            "font-weight: bold; padding: 4px; border-radius: 4px;"
        )

    # ==================================================================
    # Step 15: Contrast Checker
    # ==================================================================

    def start_contrast_from(self, source_widget: ColorSlotWidget) -> None:
        """Enter contrast target selection mode."""
        self._contrast_source = source_widget
        self.size_overlay.setText("Click target slot")
        self.size_overlay.setStyleSheet(
            f"background-color: {SELECTION_OVERLAY_COLOR}; color: {SELECTION_OVERLAY_TEXT}; "
            "font-weight: bold; padding: 4px; border-radius: 4px;"
        )
        for w in self.slots_widgets:
            if w is not source_widget:
                w.slot.mousePressEvent = (
                    lambda ev, target=w: self._contrast_target_selected(target)
                )

    def _contrast_target_selected(self, target_widget: ColorSlotWidget) -> None:
        """Target slot was clicked -- compute and show contrast ratio."""
        source = getattr(self, "_contrast_source", None)
        self._cancel_contrast_mode()
        if source is None or source is target_widget:
            return

        rgb_a = (source.slot.color.red(), source.slot.color.green(), source.slot.color.blue())
        rgb_b = (target_widget.slot.color.red(), target_widget.slot.color.green(), target_widget.slot.color.blue())
        result = Accessibility.contrast_ratio(rgb_a, rgb_b)

        DialogHelper.show_info(self, result.summary, title="WCAG Contrast Check")

    def _cancel_contrast_mode(self) -> None:
        """Exit contrast selection mode."""
        self._contrast_source = None
        for w in self.slots_widgets:
            w.slot.mousePressEvent = w._on_slot_press
        theme = self.theme_manager.get_current_theme()
        self.size_overlay.setStyleSheet(
            f"background-color: {SIZE_OVERLAY_BG}; color: {theme['text_color']}; "
            "font-weight: bold; padding: 4px; border-radius: 4px;"
        )

    # ==================================================================
    # Step 16: Color Blindness Simulation
    # ==================================================================

    def set_simulation_mode(self, mode: str) -> None:
        """Set color blindness simulation mode on the preview grid."""
        self.preview_grid.simulation_mode = mode
        self.settings_manager.color_blindness_mode = mode

    def refresh_all_color_info(self) -> None:
        """Refresh all slot hex labels (after settings change)."""
        for w in self.slots_widgets:
            w.refresh_color_info()

    # ==================================================================
    # Step 10: Add Slot Menu (with random options)
    # ==================================================================

    def _show_add_menu(self, pos=None) -> None:
        """Show right-click context menu for Add Color Slot button."""
        btn = self.right_buttons_dict["Add Color Slot"]
        menu = QMenu(self)
        menu.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint
        )
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Palette transparency trick removes native border in dark/light modes.
        # Image mode already handles this via DWM compositing, so skip it there
        # to prevent the background image bleeding through the menu.
        if not self.theme_manager.is_image_mode():
            menu.setAutoFillBackground(False)
            p = menu.palette()
            p.setColor(QPalette.ColorRole.Window, QColor(*TRANSPARENT_RGBA))
            menu.setPalette(p)

        add_random = menu.addAction("Add Random Color")
        add_random.triggered.connect(self._add_random_color)

        add_3 = menu.addAction("Generate 3 Random Colors")
        add_3.triggered.connect(lambda: self._add_random_palette(3))

        add_6 = menu.addAction("Generate 6 Random Colors")
        add_6.triggered.connect(lambda: self._add_random_palette(6))

        add_9 = menu.addAction("Generate 9 Random Colors")
        add_9.triggered.connect(lambda: self._add_random_palette(9))

        menu.addSeparator()
        add_group = menu.addAction("Add New Group")
        add_group.triggered.connect(self._prompt_add_group)

        # Show menu below the button
        global_pos = btn.mapToGlobal(btn.rect().bottomLeft())
        menu.exec(global_pos)

    def _prompt_add_group(self) -> None:
        """Prompt for group name and create a new group."""
        name, ok = QInputDialog.getText(
            self, "New Group", "Group name:", text=""
        )
        if ok:
            self.add_group(name.strip())

    def _add_random_color(self) -> None:
        """Add a single vivid random color slot."""
        if len(self.slots_widgets) >= MAX_SLOTS:
            DialogHelper.show_warning(self, f"Maximum {MAX_SLOTS} color slots allowed!")
            return
        self._push_undo()
        rgb = ColorHarmonies.random_single()
        self.add_slot_with_color(QColor(*rgb))

    def _add_random_palette(self, count: int = 5) -> None:
        """Generate a harmonious random palette with the specified number of colors."""
        self._push_undo()
        colors = ColorHarmonies.random_harmonious(count)
        for rgb in colors:
            if len(self.slots_widgets) >= MAX_SLOTS:
                break
            self.add_slot_with_color(QColor(*rgb))

    def update_preview(self) -> None:
        """Update the preview grid"""
        all_slots = [w.slot for w in self.slots_widgets]
        self.preview_grid.setSlots(all_slots)

    def save_preview(self) -> None:
        """Save the preview grid as an image"""
        pixmap = QPixmap(self.preview_grid.size())
        self.preview_grid.render(pixmap)
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Preview", "", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)",
        )
        if file_path:
            pixmap.save(file_path)
            DialogHelper.show_success(self, f"Preview saved to {file_path}")

    def import_palette(self) -> None:
        """Import a color palette from file"""
        try:
            start_dir = self.settings_manager.last_import_dir or ""
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Palette",
                start_dir,
                ";;".join([f"{name} ({ext})" for name, ext in PaletteFormats.get_import_formats()]),
            )

            if not file_path:
                return

            # Remember the directory
            self.settings_manager.last_import_dir = str(Path(file_path).parent)

            # Import the palette (returns ImportResult with colors + metadata)
            result = PaletteFormats.import_palette(file_path)

            if result.is_empty:
                DialogHelper.show_warning(self, "No colors found in the palette file.")
                return

            self._push_undo()

            # Clear existing slots and reset to single group
            self.clear_all_unlocked_slots()
            if not any(w.locked for w in self.slots_widgets):
                # All slots were cleared — reset groups
                self._destroy_headers()
                self.slot_groups.clear()
                self._init_default_group()

            # Add slots for imported colors
            for color, weight in result.colors:
                if len(self.slots_widgets) >= MAX_SLOTS:
                    break

                slot = ColorSlot(base_size=MIN_SLOT_SIZE, max_size=MAX_SLOT_SIZE, theme_manager=self.theme_manager)
                slot.color = QColor(*color)
                slot._is_default_color = False
                widget = ColorSlotWidget(slot, self.preview_grid, self)
                widget.hex_label.setText(slot.color.name())
                self.slots_widgets.append(widget)

            # Apply imported metadata (or use filename as fallback name)
            if result.metadata:
                self._set_metadata(result.metadata)
            else:
                # Use filename (without extension) as palette name
                fallback_name = Path(file_path).stem
                self._set_metadata(PaletteMetadata(name=fallback_name))

            self.update_grid()

            # Record in recent palettes
            self.recent_palettes.add(
                path=file_path,
                name=self.palette_metadata.name or Path(file_path).stem,
                format_ext=Path(file_path).suffix.lower(),
                color_count=len(result.colors),
            )

            DialogHelper.show_success(
                self,
                f"Imported {len(result.colors)} colors from {Path(file_path).name}",
            )

        except Exception as e:
            DialogHelper.show_error(self, f"Failed to import palette: {str(e)}")
            logger.error(f"Import error: {e}")
            logger.exception("Import palette traceback:")

    def export_palette(self) -> None:
        """Export current palette to file"""
        try:
            if not self.slots_widgets:
                DialogHelper.show_warning(self, "No color slots to export.")
                return

            start_dir = self.settings_manager.last_export_dir or ""
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "Export Palette",
                start_dir,
                ";;".join([f"{name} ({ext})" for name, ext in PaletteFormats.get_export_formats()]),
            )

            if not file_path:
                return

            # Remember the directory and format
            file_path_obj = Path(file_path)
            self.settings_manager.last_export_dir = str(file_path_obj.parent)
            self.settings_manager.last_export_format = file_path_obj.suffix.lower()

            # Prepare colors for export
            colors_weights = []
            for widget in self.slots_widgets:
                slot = widget.slot
                color = (slot.color.red(), slot.color.green(), slot.color.blue())
                weight = 50
                colors_weights.append((color, weight))

            # Export the palette with metadata
            self.palette_metadata.touch()
            PaletteFormats.export_palette(file_path, colors_weights, self.palette_metadata)

            # Record in export history
            file_size = file_path_obj.stat().st_size if file_path_obj.exists() else 0
            self.export_history.add_entry(
                path=file_path,
                format_ext=file_path_obj.suffix.lower(),
                color_count=len(colors_weights),
                file_size_bytes=file_size,
            )

            # Record in recent palettes
            self.recent_palettes.add(
                path=file_path,
                name=self.palette_metadata.name or file_path_obj.stem,
                format_ext=file_path_obj.suffix.lower(),
                color_count=len(colors_weights),
            )

            DialogHelper.show_success(
                self,
                f"Exported {len(colors_weights)} colors to {file_path_obj.name}",
            )

        except Exception as e:
            DialogHelper.show_error(self, f"Failed to export palette: {str(e)}")
            logger.error(f"Export error: {e}")
            logger.exception("Export palette traceback:")

    def _show_export_menu(self, pos) -> None:
        """Show context menu with export options on the Export button."""
        menu = QMenu(self)
        single_action = menu.addAction("Export to single format...")
        single_action.triggered.connect(self.export_palette)
        batch_action = menu.addAction("Batch Export to multiple formats...")
        batch_action.triggered.connect(self.batch_export)
        sender = self.right_buttons_dict.get("Export Palette")
        if sender:
            menu.exec(sender.mapToGlobal(pos))

    def batch_export(self) -> None:
        """Export current palette to multiple formats in a single folder."""
        try:
            if not self.slots_widgets:
                DialogHelper.show_warning(self, "No color slots to export.")
                return

            palette_name = self.palette_metadata.name or "palette"
            dialog = BatchExportDialog(
                palette_name=palette_name,
                settings=self.settings_manager,
                parent=self,
                theme_manager=self.theme_manager,
            )

            if not dialog.exec():
                return

            formats = dialog.selected_formats
            folder = dialog.output_folder
            base_name = dialog.base_filename

            if not formats or not folder:
                return

            # Prepare colors
            colors_weights = []
            for widget in self.slots_widgets:
                slot = widget.slot
                color = (slot.color.red(), slot.color.green(), slot.color.blue())
                colors_weights.append((color, 50))

            self.palette_metadata.touch()

            # Export each format
            succeeded: list[str] = []
            failed: list[tuple[str, str]] = []

            dialog.show()  # Keep dialog visible for progress
            for i, ext in enumerate(formats):
                file_path = str(Path(folder) / f"{base_name}{ext}")
                dialog.set_progress(i, len(formats), f"Exporting {base_name}{ext}...")
                QApplication.processEvents()

                try:
                    PaletteFormats.export_palette(file_path, colors_weights, self.palette_metadata)
                    succeeded.append(file_path)

                    # Record each in export history
                    file_path_obj = Path(file_path)
                    file_size = file_path_obj.stat().st_size if file_path_obj.exists() else 0
                    self.export_history.add_entry(
                        path=file_path,
                        format_ext=ext,
                        color_count=len(colors_weights),
                        file_size_bytes=file_size,
                    )

                    # Record in recent palettes
                    self.recent_palettes.add(
                        path=file_path,
                        name=palette_name,
                        format_ext=ext,
                        color_count=len(colors_weights),
                    )

                except Exception as e:
                    failed.append((ext, str(e)))
                    logger.warning(f"Batch export failed for {ext}: {e}")

            dialog.set_progress(len(formats), len(formats), "Done!")
            dialog.hide()

            # Show result
            result = BatchExportResult(
                succeeded=succeeded, failed=failed, folder=folder,
            )
            if failed:
                DialogHelper.show_warning(self, result.summary)
            else:
                DialogHelper.show_success(self, result.summary)

            logger.info(f"Batch export: {len(succeeded)}/{result.total} to {folder}")

        except Exception as e:
            DialogHelper.show_error(self, f"Batch export error: {str(e)}")
            logger.error(f"Batch export error: {e}")

    # ==================================================================
    # Phase 7: Recent Palettes
    # ==================================================================

    def _show_recent_palettes_menu(self, pos) -> None:
        """Show context menu with recent palettes on the Import button."""
        entries = self.recent_palettes.entries
        menu = QMenu(self)

        if not entries:
            no_action = menu.addAction("No recent palettes")
            no_action.setEnabled(False)
        else:
            for entry in entries:
                label = entry.display_name
                detail = entry.display_detail
                if detail:
                    label = f"{label}  ({detail})"
                if not entry.exists:
                    label = f"⚠ {label}"

                action = menu.addAction(label)
                action.setEnabled(entry.exists)
                path = entry.path
                action.triggered.connect(lambda checked, p=path: self._load_recent_palette(p))

            menu.addSeparator()

            # Open containing folder for first entry
            if entries[0].exists:
                folder_action = menu.addAction(f"Open folder: {entries[0].display_name}")
                folder_path = entries[0].folder
                folder_action.triggered.connect(
                    lambda checked, f=folder_path: self._open_folder(f)
                )
                menu.addSeparator()

            # Prune missing
            prune_action = menu.addAction("Remove missing files")
            prune_action.triggered.connect(self._prune_recent_palettes)

            # Clear all
            clear_action = menu.addAction("Clear recent list")
            clear_action.triggered.connect(self._clear_recent_palettes)

        sender = self.right_buttons_dict.get("Import Palette")
        if sender:
            menu.exec(sender.mapToGlobal(pos))

    def _load_recent_palette(self, path: str) -> None:
        """Load a palette from recent palettes list."""
        if not Path(path).exists():
            DialogHelper.show_warning(self, f"File no longer exists:\n{path}")
            self.recent_palettes.remove(path)
            return

        try:
            result = PaletteFormats.import_palette(path)
            if result.is_empty:
                DialogHelper.show_warning(self, "No colors found in the palette file.")
                return

            self._push_undo()

            # Clear existing slots and reset groups
            self.clear_all_unlocked_slots()
            if not any(w.locked for w in self.slots_widgets):
                self._destroy_headers()
                self.slot_groups.clear()
                self._init_default_group()

            # Add slots
            for color, weight in result.colors:
                if len(self.slots_widgets) >= MAX_SLOTS:
                    break
                slot = ColorSlot(
                    base_size=MIN_SLOT_SIZE, max_size=MAX_SLOT_SIZE,
                    theme_manager=self.theme_manager,
                )
                slot.color = QColor(*color)
                slot._is_default_color = False
                widget = ColorSlotWidget(slot, self.preview_grid, self)
                widget.hex_label.setText(slot.color.name())
                self.slots_widgets.append(widget)

            # Apply metadata
            if result.metadata:
                self._set_metadata(result.metadata)
            else:
                self._set_metadata(PaletteMetadata(name=Path(path).stem))

            self.update_grid()

            # Update the entry (moves to top, refreshes count)
            self.recent_palettes.add(
                path=path,
                name=self.palette_metadata.name or Path(path).stem,
                format_ext=Path(path).suffix.lower(),
                color_count=len(result.colors),
            )

            DialogHelper.show_success(
                self,
                f"Loaded {len(result.colors)} colors from {Path(path).name}",
            )

        except Exception as e:
            DialogHelper.show_error(self, f"Failed to load palette: {str(e)}")
            logger.error(f"Recent palette load error: {e}")

    def _open_folder(self, folder_path: str) -> None:
        """Open a folder in the system file manager."""
        import os
        import subprocess
        import sys as _sys
        try:
            match _sys.platform:
                case "darwin":
                    subprocess.Popen(["open", folder_path])
                case "win32":
                    os.startfile(folder_path)
                case _:
                    subprocess.Popen(["xdg-open", folder_path])
        except Exception as e:
            logger.warning(f"Failed to open folder: {e}")

    def _prune_recent_palettes(self) -> None:
        """Remove entries for files that no longer exist."""
        removed = self.recent_palettes.prune_missing()
        if removed:
            DialogHelper.show_success(self, f"Removed {removed} missing file(s).")
        else:
            DialogHelper.show_success(self, "All recent files still exist.")

    def _clear_recent_palettes(self) -> None:
        """Clear the recent palettes list."""
        self.recent_palettes.clear()
        DialogHelper.show_success(self, "Recent palettes list cleared.")

    # ==================================================================
    # Phase 1: Settings, Session, Export History
    # ==================================================================

    def open_settings(self) -> None:
        """Open the settings dialog."""
        dialog = SettingsDialog(
            settings=self.settings_manager,
            export_history=self.export_history,
            parent=self,
            theme_manager=self.theme_manager,
            palette_metadata=self.palette_metadata,
            color_history_panel=self.color_history_panel,
            recent_palettes=self.recent_palettes,
        )
        dialog.auto_save_changed.connect(self._on_auto_save_settings_changed)
        dialog.settings_applied.connect(self._apply_settings_changes)
        dialog.exec()

        # Read back metadata (may have been edited in Details tab)
        self._update_window_title()

        # Apply all settings that may have changed (covers OK + Cancel case)
        self._apply_settings_changes()

    def _on_auto_save_settings_changed(self, enabled: bool, interval_ms: int) -> None:
        """Handle auto-save setting changes from the settings dialog."""
        if enabled:
            self.session_manager.stop_auto_save()
            self.session_manager.start_auto_save(interval_ms=interval_ms)
            logger.info(f"Auto-save updated: {interval_ms / 60000:.1f} min interval")
        else:
            self.session_manager.stop_auto_save()
            logger.info("Auto-save disabled")

    def _apply_settings_changes(self) -> None:
        """Apply all settings that may have changed after the settings dialog closes."""
        # Update default-colored slots to the new default color
        new_default = self._get_default_slot_color()
        for widget in self.slots_widgets:
            if widget.slot._is_default_color:
                widget.slot.color = new_default
                widget.hex_label.setText(new_default.name())
                widget.slot.update()

        # Refresh color info display (show_color_info may have changed)
        self.refresh_all_color_info()

        # Update color blindness simulation
        self.set_simulation_mode(self.settings_manager.color_blindness_mode)

        # Apply appearance settings (border style, size, overlay, layout)
        self._apply_appearance_settings()

        # Update history panel max entries
        if hasattr(self, 'color_history_panel'):
            self.color_history_panel.max_entries = self.settings_manager.max_history_size

        # Update preview to reflect any changes
        self.update_preview()

    # ==================================================================
    # Color History
    # ==================================================================

    def record_color_change(
        self, old_color: str, new_color: str, slot_index: int = -1
    ) -> None:
        """Record a color change in the history panel."""
        if hasattr(self, 'color_history_panel'):
            self.color_history_panel.record(old_color, new_color, slot_index)

    def open_about(self) -> None:
        """Open the about dialog."""
        dialog = AboutDialog(
            parent=self,
            theme_name=self.theme_manager.current_theme,
        )
        dialog.exec()

    def _get_session_state(self) -> PaletteSessionState:
        """Build current palette state for session save."""
        slots_data = []
        for widget in self.slots_widgets:
            slot = widget.slot
            slot_info: dict = {
                "color": slot.color.name(),
                "locked": widget.locked,
                "has_image": slot.image_pixmap is not None and not slot.image_pixmap.isNull(),
                "is_default_color": getattr(slot, '_is_default_color', False),
            }
            slots_data.append(slot_info)

        return PaletteSessionState(
            slots=slots_data,
            current_theme=self.theme_manager.current_theme,
            metadata=self.palette_metadata.to_dict(),
            color_history=(
                self.color_history_panel.to_list()
                if hasattr(self, 'color_history_panel') else []
            ),
            groups=self._groups_data(),
        )

    def _try_restore_session(self) -> None:
        """Attempt to restore a previous session on startup."""
        # Check for crash recovery first
        if self.session_manager.has_recovery():
            state = self.session_manager.get_recovery_state()
            if state and state.is_valid:
                reply = DialogHelper.show_question(
                    self,
                    f"A previous session ({state.slot_count} colors, "
                    f"saved {state.formatted_time}) was found.\n\n"
                    f"Restore it?",
                )
                if reply:
                    self._restore_session_state(state)
                    self.session_manager.clear_recovery()
                    logger.success(f"Recovered session: {state.slot_count} slots")
                    return
                else:
                    self.session_manager.clear_recovery()
                    return

        # Otherwise check for normal auto-restore
        if self.settings_manager.auto_restore_session:
            if self.session_manager.has_saved_session():
                state = self.session_manager.load_session()
                if state and state.is_valid:
                    self._restore_session_state(state)
                    logger.success(f"Auto-restored session: {state.slot_count} slots")

    def _restore_session_state(self, state: PaletteSessionState) -> None:
        """Apply a saved session state to the workspace."""
        # Clear current slots and groups
        for widget in self.slots_widgets[:]:
            self._remove_slot_internal(widget)
        self.slots_widgets.clear()
        self._destroy_headers()
        self.slot_groups.clear()

        # Recreate slots from state
        for slot_data in state.slots:
            if len(self.slots_widgets) >= MAX_SLOTS:
                break

            slot = ColorSlot(
                base_size=MIN_SLOT_SIZE,
                max_size=MAX_SLOT_SIZE,
                theme_manager=self.theme_manager,
            )
            color_hex = slot_data.get("color", SESSION_FALLBACK_COLOR)
            slot.color = QColor(color_hex)
            slot._is_default_color = slot_data.get("is_default_color", False)

            widget = ColorSlotWidget(slot, self.preview_grid, self)
            widget.hex_label.setText(slot.color.name())

            if slot_data.get("locked", False):
                widget.locked = True
                widget.update_lock_button()

            self.slots_widgets.append(widget)

        # Restore groups (or default single group)
        if state.groups:
            self._restore_groups_from_data(state.groups)
        else:
            self._init_default_group()

        self.update_grid()

        # Restore metadata if present
        if state.metadata:
            self._set_metadata(PaletteMetadata.from_dict(state.metadata))
        else:
            self._reset_metadata()

        # Restore color history if present
        if state.color_history and hasattr(self, 'color_history_panel'):
            entries = ColorHistoryPanel.entries_from_list(state.color_history)
            self.color_history_panel.set_entries(entries)

        # Restore theme if different
        saved_theme = state.current_theme
        if saved_theme and saved_theme != self.theme_manager.current_theme:
            while self.theme_manager.current_theme != saved_theme:
                self.theme_manager.cycle_theme()
            self.theme_button.setText(self.theme_manager.get_theme_display_name())
            self.apply_theme()
            self.update_slot_colors_for_theme()

    def eventFilter(self, obj, event) -> bool:
        """
        Application-level event filter for custom themed tooltips.

        Intercepts QEvent.ToolTip to show our custom _ThemedToolTip
        instead of the native OS tooltip (which ignores CSS border-radius
        on Windows Light/Image modes).
        """
        event_type = event.type()

        if event_type == QEvent.Type.ToolTip:
            if isinstance(obj, QWidget) and obj.toolTip():
                theme = self.theme_manager.get_current_theme()
                if theme:
                    _ThemedToolTip.instance().show_tip(
                        QCursor.pos(),
                        obj.toolTip(),
                        theme,
                        get_font_family(),
                    )
                return True  # Consume event — prevent native tooltip
        elif event_type in (QEvent.Type.Leave, QEvent.Type.MouseButtonPress,
                            QEvent.Type.WindowDeactivate, QEvent.Type.Wheel):
            _ThemedToolTip.instance().hide_tip()

        return super().eventFilter(obj, event)

    def closeEvent(self, event) -> None:
        """Handle application close -- save session and geometry."""
        # Remove event filter and hide custom tooltip
        QApplication.instance().removeEventFilter(self)
        _ThemedToolTip.instance().hide_tip()

        # Save window geometry
        self.settings_manager.save_window_geometry(self.saveGeometry())

        # Save final session state for restore on next launch
        final_state = self._get_session_state()
        self.session_manager.on_clean_shutdown(final_state=final_state)

        self.settings_manager.sync()
        logger.info("Application closing -- session and geometry saved")
        super().closeEvent(event)

    # ==================================================================

    def resizeEvent(self, event) -> None:
        """Handle window resize"""
        super().resizeEvent(event)

        self.update_all_slot_sizes()

        width_pct = int((self.width() / self.ref_width) * 100)
        height_pct = int((self.height() / self.ref_height) * 100)

        # Always update text (so it's current when toggled visible)
        self.size_overlay.setText(f"{width_pct}% \u00d7 {height_pct}%")

        # Position settings gear (top-right corner)
        self.btn_settings.move(
            self.width() - self.btn_settings.width() - 20,
            20,
        )

        # Position size overlay to the left of settings gear (always update position)
        self.size_overlay.move(
            self.btn_settings.x() - self.size_overlay.width() - 4,
            20,
        )

        # Position theme button (bottom-right)
        margin = 20
        self.theme_button.move(
            self.width() - self.theme_button.width() - margin,
            self.height() - self.theme_button.height() - margin,
        )

        if self.theme_manager.is_image_mode() and self.background_label.isVisible():
            self.background_label.setGeometry(0, 0, self.width(), self.height())


def main() -> None:
    """Main application entry point"""
    setup_logger(level=logging.INFO)

    # Startup banner
    logger.separator()
    logger.header(f"{APP_NAME} v{APP_VERSION}")
    logger.separator()

    logger.info("Starting application...")
    logger.info("Loading custom font...")

    app = QApplication(sys.argv)

    font = load_embedded_font()
    app.setFont(font)
    logger.success("Font applied to application")

    window = MainWindow()
    window.show()

    logger.separator()
    logger.success("Application ready!")
    logger.separator()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()