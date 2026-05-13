"""
RNV Color Palette Manager - About Dialog
Application information and help accessible via Ctrl+/ keyboard shortcut.

Displays:
- Application name, version, description
- Feature list
- Keyboard shortcuts reference
- System information
- Credits

Version: 1.0
"""
from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from utils.config import APP_NAME, APP_VERSION, ICONS_DIR
from utils.font_loader import get_font_family
from utils.logger import Logger, get_logger_instance
from ui.colors import BRAND_GOLD, ACCENT_PRESSED_TEXT_DARK, ACCENT_PRESSED_TEXT_LIGHT

logger: Logger = get_logger_instance("AboutDialog")


class AboutDialog(QDialog):
    """
    About dialog with application information, features, and keyboard shortcuts.

    Displays application metadata, feature overview, keyboard shortcuts reference,
    and credits in a tabbed interface. Accessible via Ctrl+/ shortcut.

    Example:
        >>> dialog = AboutDialog(parent=main_window, theme_name='dark')
        >>> dialog.exec()
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        theme_name: str = 'dark',
    ) -> None:
        # Don't pass parent to avoid stylesheet inheritance issues
        super().__init__(None)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self._theme_name: str = theme_name
        self._parent_ref = parent  # Keep ref for centering

        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(540, 700)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.MSWindowsFixedSizeDialogHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        self._build_ui()
        self._apply_theme()

        # Center on parent
        if parent is not None:
            parent_geo = parent.geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2,
            )

        logger.info("About dialog initialized")

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the about dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Header section with app name and version
        header = self._create_header()
        layout.addWidget(header)

        # Tab widget for organized content
        self.tabs = QTabWidget()

        self.tabs.addTab(self._create_about_tab(), "About")
        self.tabs.addTab(self._create_features_tab(), "Features")
        self.tabs.addTab(self._create_shortcuts_tab(), "Shortcuts")
        self.tabs.addTab(self._create_credits_tab(), "Credits")

        layout.addWidget(self.tabs, 1)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 35)
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _create_header(self) -> QWidget:
        """Create the header section with app name and logo."""
        header = QFrame()
        header.setObjectName("header_frame")
        header.setFrameShape(QFrame.Shape.NoFrame)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)

        # App icon
        icon_label = QLabel()
        icon_label.setStyleSheet("border: none; background: transparent;")
        icon_path = ICONS_DIR / "icon.png"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    64, 64,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                icon_label.setPixmap(scaled)
        icon_label.setFixedSize(70, 70)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)

        # App name and version
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)

        name_label = QLabel(APP_NAME)
        name_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; border: none; background: transparent;"
        )
        text_layout.addWidget(name_label)

        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setStyleSheet(
            f"font-size: 14px; color: {BRAND_GOLD}; border: none; background: transparent;"
        )
        text_layout.addWidget(version_label)

        desc_label = QLabel("Professional Color Palette Creation & Management")
        desc_label.setStyleSheet(
            "font-size: 12px; border: none; background: transparent;"
        )
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)

        text_layout.addStretch()
        header_layout.addLayout(text_layout, 1)

        return header

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------

    def _create_about_tab(self) -> QWidget:
        """Create the About tab with application description."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        python_ver = (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        try:
            from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
            qt_ver = QT_VERSION_STR
            pyqt_ver = PYQT_VERSION_STR
        except ImportError:
            qt_ver = "Unknown"
            pyqt_ver = "Unknown"

        about_html = f"""
<h3>Professional Color Palette Manager</h3>

<p>{APP_NAME} is a desktop application for creating, managing, and exporting
professional color palettes. Extract colors from images, mix and blend using
multiple algorithms, and export to formats used by Adobe, GIMP, Procreate,
Affinity, and web development tools.</p>

<h4>Core Capabilities:</h4>
<ul>
<li><b>Color Extraction</b> – Extract palettes from uploaded images</li>
<li><b>Multiple Mixing Algorithms</b> – RGB, HSV, LAB, RYB, CMY, Kubelka-Munk</li>
<li><b>Color Harmonies</b> – Complementary, analogous, triadic, split-complementary</li>
<li><b>16+ Export Formats</b> – ASE, ACO, GPL, Procreate, CSS, JSON, SVG, and more</li>
<li><b>Three Theme Modes</b> – Dark, Light, and custom Image Mode</li>
<li><b>Session Management</b> – Auto-save and restore your workspace</li>
</ul>

<h4>System Information:</h4>
<table>
<tr><td><b>Python:</b></td><td>&nbsp;&nbsp;{python_ver}</td></tr>
<tr><td><b>PyQt6:</b></td><td>&nbsp;&nbsp;{pyqt_ver}</td></tr>
<tr><td><b>Qt:</b></td><td>&nbsp;&nbsp;{qt_ver}</td></tr>
<tr><td><b>Platform:</b></td><td>&nbsp;&nbsp;{sys.platform}</td></tr>
</table>
"""

        label = QLabel(about_html)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll)

        return tab

    def _create_features_tab(self) -> QWidget:
        """Create the Features tab with feature list."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)

        features_html = """
<h3>Feature Overview</h3>

<h4>🎨 Color Palette Creation</h4>
<ul>
<li><b>Color Slots</b> – Add up to 99 individual color slots</li>
<li><b>Color Picker</b> – Full color dialog with hex, RGB, HSV input</li>
<li><b>Image Upload</b> – Use full images or extract average color</li>
<li><b>Palette Extraction</b> – Pull dominant colors from any image</li>
<li><b>Random Generation</b> – Quick-start with random color palettes</li>
</ul>

<h4>🔬 Color Mixing Algorithms</h4>
<ul>
<li><b>RGB Weighted</b> – Standard additive color mixing</li>
<li><b>HSV Weighted</b> – Perceptually-aware hue blending</li>
<li><b>CIE LAB</b> – Perceptually uniform color space mixing</li>
<li><b>RYB Artist's Wheel</b> – Traditional paint mixing (Yellow+Blue=Green)</li>
<li><b>Subtractive CMY</b> – Ink and dye simulation</li>
<li><b>Kubelka-Munk</b> – Realistic pigment/paint physics model</li>
</ul>

<h4>🌈 Color Harmonies</h4>
<ul>
<li><b>Complementary</b> – Opposite colors on the color wheel</li>
<li><b>Analogous</b> – Adjacent colors for smooth palettes</li>
<li><b>Triadic</b> – Three evenly-spaced colors</li>
<li><b>Split-Complementary</b> – Nuanced contrast</li>
<li><b>Tetradic / Square</b> – Four-color balanced schemes</li>
</ul>

<h4>📤 Export Formats (16+)</h4>
<ul>
<li><b>Adobe</b> – ASE (Swatch Exchange), ACO (Color), ACB (Color Book)</li>
<li><b>Open Source</b> – GPL (GIMP/Inkscape/Krita)</li>
<li><b>Procreate</b> – .swatches format</li>
<li><b>Affinity</b> – .afpalette format</li>
<li><b>Web</b> – CSS variables, JSON, XML, SVG, HEX, HSL, HSV</li>
<li><b>Text</b> – Plain text with multiple color representations</li>
</ul>

<h4>🖥️ Interface & Themes</h4>
<ul>
<li><b>Dark Mode</b> – Comfortable dark interface</li>
<li><b>Light Mode</b> – Clean light interface</li>
<li><b>Image Mode</b> – Custom background with transparent overlays</li>
<li><b>Zoomable Canvas</b> – Pan and zoom the color slot workspace</li>
<li><b>Live Preview Grid</b> – Real-time palette overview</li>
</ul>

<h4>💾 Session & History</h4>
<ul>
<li><b>Auto-Save</b> – Periodic session backup</li>
<li><b>Session Restore</b> – Resume where you left off</li>
<li><b>Undo/Redo</b> – Full action history</li>
<li><b>Export History</b> – Track all export operations</li>
</ul>
"""

        label = QLabel(features_html)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll)

        return tab

    def _create_shortcuts_tab(self) -> QWidget:
        """Create the Shortcuts tab with keyboard shortcuts."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)

        shortcuts_html = """
<h3>Keyboard Shortcuts</h3>

<h4>Color Slots</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+N</b></td><td>Add New Color Slot</td></tr>
<tr><td><b>Ctrl+D</b></td><td>Duplicate Selected Slot</td></tr>
<tr><td><b>Ctrl+C</b></td><td>Copy Color to Clipboard</td></tr>
<tr><td><b>Delete</b></td><td>Remove Selected Slot</td></tr>
<tr><td><b>Space</b></td><td>Toggle Lock on Selected Slot</td></tr>
<tr><td><b>Left / Right</b></td><td>Navigate Between Slots</td></tr>
</table>

<h4>Palette Operations</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+I</b></td><td>Import Palette</td></tr>
<tr><td><b>Ctrl+E</b></td><td>Export Palette</td></tr>
<tr><td><b>Ctrl+Shift+E</b></td><td>Batch Export (Multiple Formats)</td></tr>
<tr><td><b>Ctrl+S</b></td><td>Save Preview Image</td></tr>
</table>

<h4>Search &amp; Filter</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+F</b></td><td>Toggle Search / Filter Bar</td></tr>
<tr><td><b>Escape</b></td><td>Close Search Bar (if open)</td></tr>
</table>

<h4>Edit</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+Z</b></td><td>Undo</td></tr>
<tr><td><b>Ctrl+Shift+Z</b></td><td>Redo</td></tr>
<tr><td><b>Ctrl+Y</b></td><td>Redo (Alternate)</td></tr>
<tr><td><b>Escape</b></td><td>Deselect Current Slot</td></tr>
</table>

<h4>Application</h4>
<table width="100%">
<tr><td width="40%"><b>Ctrl+,</b></td><td>Open Settings</td></tr>
<tr><td><b>Ctrl+/</b></td><td>Open About Dialog (This Window)</td></tr>
<tr><td><b>Ctrl+T</b></td><td>Cycle Theme (Dark → Light → Image)</td></tr>
<tr><td><b>Ctrl+R</b></td><td>Reset Zoom / Pan</td></tr>
<tr><td><b>F10</b></td><td>Toggle Fullscreen</td></tr>
<tr><td><b>F11</b></td><td>Toggle Tooltips On/Off</td></tr>
<tr><td><b>F12</b></td><td>Toggle Size Percentage Overlay</td></tr>
</table>

<h4>Mouse Interactions</h4>
<table width="100%">
<tr><td width="40%"><b>Click Slot</b></td><td>Open Color Picker</td></tr>
<tr><td><b>Right-Click Slot</b></td><td>Context Menu (Harmonies, Copy, etc.)</td></tr>
<tr><td><b>Right-Click Add</b></td><td>Random Color Generation Menu</td></tr>
<tr><td><b>Right-Click Import</b></td><td>Recent Palettes Menu</td></tr>
<tr><td><b>Right-Click Export</b></td><td>Export Options (Single / Batch)</td></tr>
</table>
"""

        label = QLabel(shortcuts_html)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll)

        return tab

    def _create_credits_tab(self) -> QWidget:
        """Create the Credits tab with acknowledgments."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)

        credits_html = f"""
<h3>Credits & Acknowledgments</h3>

<h4>Development</h4>
<p>RNV Color Palette Manager was created with passion for helping artists,
designers, and developers work with color more effectively.</p>

<h4>Technologies</h4>
<table width="100%">
<tr><td width="40%"><b>Framework:</b></td><td>PyQt6</td></tr>
<tr><td><b>Language:</b></td><td>Python 3</td></tr>
<tr><td><b>Image Processing:</b></td><td>Pillow (PIL)</td></tr>
<tr><td><b>Color Science:</b></td><td>CIE LAB, Kubelka-Munk, RYB</td></tr>
</table>

<h4>Color Format Standards</h4>
<ul>
<li>Adobe Swatch Exchange (ASE) specification</li>
<li>Adobe Color (ACO) version 1 & 2 format</li>
<li>GIMP Palette (GPL) format</li>
<li>Procreate Swatches binary format</li>
<li>Affinity Designer palette JSON format</li>
</ul>

<h4>Color Science References</h4>
<ul>
<li>CIE 1976 L*a*b* color space for perceptual mixing</li>
<li>Kubelka-Munk theory for pigment simulation</li>
<li>RYB artist's color wheel model</li>
<li>sRGB gamma correction (IEC 61966-2-1)</li>
</ul>

<h4>Special Thanks</h4>
<ul>
<li>The PyQt community for excellent documentation</li>
<li>Pillow maintainers for image processing support</li>
<li>Color science researchers and open specifications</li>
<li>Beta testers and early adopters</li>
</ul>

<hr>

<p style="text-align: center; color: {BRAND_GOLD};">
<b>RNV Color Palette Manager</b><br>
Professional color palette creation for artists, designers, and developers<br>
&copy; 2026 RNV Development. All rights reserved.
</p>
"""

        label = QLabel(credits_html)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll)

        return tab

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def set_theme(self, theme_name: str) -> None:
        """Set the dialog theme."""
        self._theme_name = theme_name
        self._apply_theme()

    def _apply_theme(self) -> None:
        """Apply the current theme to the dialog.
        All colors pulled from the theme dict — no hardcoded values.
        """
        from ui.colors import get_theme_colors
        font_family = get_font_family()

        theme = get_theme_colors(self._theme_name)
        is_light = (self._theme_name == 'light')

        bg           = theme['window_bg']
        text         = theme['text_color']
        card_bg      = theme['card_bg']
        border       = theme['border_color']
        tab_hover    = theme.get('tab_hover',    theme['hover_color'])
        pane_bg      = theme.get('tab_pane_bg', theme['panel_bg'])
        scroll_bg    = theme['scroll_bg']
        scroll_handle = theme.get('scroll_handle', theme['scrollbar_handle'])
        btn_bg       = theme['button_bg']
        accent       = theme['accent']

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg};
                color: {text};
                font-family: '{font_family}';
            }}
            QFrame {{
                background-color: {card_bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QFrame#header_frame {{
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }}
            QTabWidget::pane {{
                background-color: {pane_bg};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 5px;
            }}
            QTabBar::tab {{
                background-color: {card_bg};
                color: {text};
                padding: 8px 16px;
                border: 1px solid {border};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {pane_bg};
                color: {accent};
                border-bottom: 2px solid {accent};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {card_bg};
                color: {accent};
            }}
            QLabel {{
                color: {text};
                background-color: transparent;
                border: none;
            }}
            QScrollArea {{
                background-color: {pane_bg};
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {pane_bg};
            }}
            QScrollBar:vertical {{
                background-color: {scroll_bg};
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {scroll_handle};
                border-radius: 5px;
                min-height: 20px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {accent};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background-color: transparent;
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {tab_hover};
                border-color: {accent};
                color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {accent};
                color: {ACCENT_PRESSED_TEXT_LIGHT if is_light else ACCENT_PRESSED_TEXT_DARK};
            }}
        """)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """Clean up resources before deletion."""
        try:
            for child in self.findChildren(QLabel):
                if child.pixmap() and not child.pixmap().isNull():
                    child.clear()
            logger.debug("AboutDialog cleanup complete")
        except Exception as e:
            logger.error(f"Error during AboutDialog cleanup: {e}")

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle dialog close."""
        self.cleanup()
        super().closeEvent(event)


# ==================== Module Exports ====================

__all__: list[str] = ["AboutDialog"]