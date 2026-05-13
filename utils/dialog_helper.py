"""
RNV Color Palette Manager - Dialog Helper
Centralized dialog interface for consistent UX across the application.

Features:
- Consistent styling across all dialogs
- Theme-aware dialogs (dark/light/image)
- Less code duplication
- Simple API for common dialog patterns

Usage Examples:
    # Show error
    DialogHelper.show_error(self, "Failed to load file!")

    # Show warning
    DialogHelper.show_warning(self, "Image size out of range")

    # Show info
    DialogHelper.show_info(self, "Palette exported successfully!")

    # Show success (alias for info with "Success" title)
    DialogHelper.show_success(self, "Exported 12 colors to palette.gpl")

    # Confirm action
    if DialogHelper.confirm(self, "Clear all unlocked slots?"):
        clear_all()

    # Ask yes/no/cancel
    result = DialogHelper.ask_yes_no_cancel(self, "Save changes?")
    if result == DialogResult.YES:
        save()

Version: 1.0
"""
from __future__ import annotations

from enum import Enum

from PyQt6.QtWidgets import QMessageBox, QWidget

from utils.logger import Logger, get_logger_instance
from utils.font_loader import get_font_family

logger: Logger = get_logger_instance(__name__)


class DialogResult(Enum):
    """Dialog result options for multi-choice dialogs."""
    YES = 1
    NO = 2
    CANCEL = 3
    OK = 4


class DialogHelper:
    """
    Centralized dialog management for consistent UX.

    All methods are static for easy access without instantiation.
    Theme detection walks up the parent chain to find theme_manager.
    """

    # Default window titles
    DEFAULT_ERROR_TITLE = "Error"
    DEFAULT_WARNING_TITLE = "Warning"
    DEFAULT_INFO_TITLE = "Information"
    DEFAULT_CONFIRM_TITLE = "Confirm"
    DEFAULT_SUCCESS_TITLE = "Success"

    # =========================================================================
    # Theme Detection & Styling
    # =========================================================================

    @staticmethod
    def _is_dark_theme(parent: QWidget | None) -> bool:
        """
        Detect if the parent widget is using a dark theme.

        Walks up the widget parent chain looking for a theme_manager attribute.
        Falls back to palette luminance detection.

        Args:
            parent: Parent widget to check.

        Returns:
            True if dark theme, False if light theme.
        """
        if parent is None:
            return True  # Default to dark

        # Walk up the parent chain to find theme_manager
        widget = parent
        while widget is not None:
            if hasattr(widget, 'theme_manager'):
                theme_manager = widget.theme_manager
                if hasattr(theme_manager, 'current_theme'):
                    return theme_manager.current_theme != 'light'
                if hasattr(theme_manager, 'is_dark_mode'):
                    return theme_manager.is_dark_mode()
            widget = widget.parent() if hasattr(widget, 'parent') else None

        # Fallback: check the window's background color luminance
        try:
            palette = parent.palette()
            bg_color = palette.color(palette.ColorRole.Window)
            luminance = (
                bg_color.red() * 0.299
                + bg_color.green() * 0.587
                + bg_color.blue() * 0.114
            )
            return luminance < 128
        except Exception:
            return True  # Default to dark on error

    @staticmethod
    def _get_style(parent: QWidget | None) -> str:
        """
        Get the appropriate dialog style based on current theme.

        Args:
            parent: Parent widget to detect theme from.

        Returns:
            CSS stylesheet string.
        """
        if DialogHelper._is_dark_theme(parent):
            return DialogHelper._get_style_dark()
        return DialogHelper._get_style_light()

    @staticmethod
    def _get_style_dark() -> str:
        """Get dark theme dialog stylesheet."""
        # Lazy import to avoid circular dependency (utils -> ui -> utils)
        from ui.colors import (
            DARK_THEME_COLORS as colors,
            ACCENT_PRESSED_TEXT_DARK,
            TEXTEDIT_BG_DARK,
        )
        dialog_bg = colors['dialog_bg']
        text = colors['text_color']
        border = colors['border_color']
        accent = colors['accent']
        accent_dark = colors['accent_dark']
        card_bg = colors['card_bg']
        pressed_text = ACCENT_PRESSED_TEXT_DARK
        textedit_bg = TEXTEDIT_BG_DARK

        font_family = get_font_family()

        return f"""
            QMessageBox {{
                background-color: {dialog_bg};
                color: {text};
                font-family: '{font_family}';
            }}
            QMessageBox QLabel {{
                color: {text};
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {card_bg};
                color: {text};
                border: 1px solid {border};
                padding: 6px 16px;
                border-radius: 4px;
                min-width: 60px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {card_bg};
                color: {accent};
                border-color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {accent};
                color: {pressed_text};
                border-color: {accent};
            }}
            QPushButton:default {{
                border: 2px solid {accent_dark};
            }}
            QTextEdit {{
                background-color: {textedit_bg};
                color: {text};
                border: 1px solid {border};
            }}
        """

    @staticmethod
    def _get_style_light() -> str:
        """Get light theme dialog stylesheet."""
        from ui.colors import (
            LIGHT_THEME_COLORS as colors,
            ACCENT_PRESSED_TEXT_LIGHT,
            TEXTEDIT_BG_LIGHT,
        )
        dialog_bg = colors['dialog_bg']
        text = colors['text_color']
        btn_bg = colors['button_bg']
        border = colors['border_color']
        accent_dark = colors['accent_dark']
        pressed_text = ACCENT_PRESSED_TEXT_LIGHT
        textedit_bg = TEXTEDIT_BG_LIGHT

        font_family = get_font_family()

        return f"""
            QMessageBox {{
                background-color: {dialog_bg};
                color: {text};
                font-family: '{font_family}';
            }}
            QMessageBox QLabel {{
                color: {text};
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {text};
                border: 1px solid {border};
                padding: 6px 16px;
                border-radius: 4px;
                min-width: 60px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {btn_bg};
                color: {accent_dark};
                border-color: {accent_dark};
            }}
            QPushButton:pressed {{
                background-color: {accent_dark};
                color: {pressed_text};
                border-color: {accent_dark};
            }}
            QPushButton:default {{
                border: 2px solid {accent_dark};
            }}
            QTextEdit {{
                background-color: {textedit_bg};
                color: {text};
                border: 1px solid {border};
            }}
        """

    # =========================================================================
    # Public Dialog Methods
    # =========================================================================

    @staticmethod
    def show_error(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        detailed_text: str | None = None,
    ) -> None:
        """
        Show error dialog.

        Args:
            parent: Parent widget.
            message: Error message to display.
            title: Optional custom title (default: "Error").
            detailed_text: Optional detailed error info.

        Example:
            DialogHelper.show_error(self, "Failed to import palette!")
            DialogHelper.show_error(self, "File not found", detailed_text=str(e))
        """
        title = title or DialogHelper.DEFAULT_ERROR_TITLE
        logger.error(f"Dialog [{title}]: {message}")

        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(DialogHelper._get_style(parent))

        if detailed_text:
            msg_box.setDetailedText(detailed_text)

        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    @staticmethod
    def show_warning(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        detailed_text: str | None = None,
    ) -> None:
        """
        Show warning dialog.

        Args:
            parent: Parent widget.
            message: Warning message to display.
            title: Optional custom title (default: "Warning").
            detailed_text: Optional detailed warning info.

        Example:
            DialogHelper.show_warning(self, "Maximum 99 color slots allowed!")
        """
        title = title or DialogHelper.DEFAULT_WARNING_TITLE
        logger.warning(f"Dialog [{title}]: {message}")

        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(DialogHelper._get_style(parent))

        if detailed_text:
            msg_box.setDetailedText(detailed_text)

        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    @staticmethod
    def show_info(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        detailed_text: str | None = None,
    ) -> None:
        """
        Show information dialog.

        Args:
            parent: Parent widget.
            message: Information message to display.
            title: Optional custom title (default: "Information").
            detailed_text: Optional detailed info.

        Example:
            DialogHelper.show_info(self, "Preview saved to preview.png")
        """
        title = title or DialogHelper.DEFAULT_INFO_TITLE
        logger.info(f"Dialog [{title}]: {message}")

        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(DialogHelper._get_style(parent))

        if detailed_text:
            msg_box.setDetailedText(detailed_text)

        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    @staticmethod
    def show_success(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        detailed_text: str | None = None,
    ) -> None:
        """
        Show success dialog (information with "Success" title).

        Args:
            parent: Parent widget.
            message: Success message to display.
            title: Optional custom title (default: "Success").
            detailed_text: Optional detailed info.

        Example:
            DialogHelper.show_success(self, "Exported 12 colors to palette.gpl")
        """
        title = title or DialogHelper.DEFAULT_SUCCESS_TITLE
        DialogHelper.show_info(parent, message, title, detailed_text)

    @staticmethod
    def confirm(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        default_yes: bool = False,
    ) -> bool:
        """
        Show yes/no confirmation dialog.

        Args:
            parent: Parent widget.
            message: Question to ask.
            title: Optional custom title (default: "Confirm").
            default_yes: If True, Yes is the default button.

        Returns:
            True if user clicked Yes, False if No.

        Example:
            if DialogHelper.confirm(self, "Clear all unlocked slots?"):
                clear_all()
        """
        title = title or DialogHelper.DEFAULT_CONFIRM_TITLE

        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(DialogHelper._get_style(parent))
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if default_yes:
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        else:
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        result = msg_box.exec()
        return result == QMessageBox.StandardButton.Yes

    @staticmethod
    def show_question(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        default_yes: bool = False,
    ) -> bool:
        """
        Alias for confirm(). Shows a yes/no question dialog.

        Returns:
            True if user clicked Yes.
        """
        return DialogHelper.confirm(parent, message, title, default_yes)

    @staticmethod
    def ask_yes_no_cancel(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
    ) -> DialogResult:
        """
        Show yes/no/cancel dialog.

        Args:
            parent: Parent widget.
            message: Question to ask.
            title: Optional custom title (default: "Confirm").

        Returns:
            DialogResult.YES, DialogResult.NO, or DialogResult.CANCEL.

        Example:
            result = DialogHelper.ask_yes_no_cancel(self, "Save changes?")
            if result == DialogResult.YES:
                save_and_close()
            elif result == DialogResult.NO:
                close_without_saving()
        """
        title = title or DialogHelper.DEFAULT_CONFIRM_TITLE

        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(DialogHelper._get_style(parent))
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)

        result = msg_box.exec()

        if result == QMessageBox.StandardButton.Yes:
            return DialogResult.YES
        elif result == QMessageBox.StandardButton.No:
            return DialogResult.NO
        return DialogResult.CANCEL

    @staticmethod
    def show_custom(
        parent: QWidget | None,
        title: str,
        message: str,
        icon: QMessageBox.Icon = QMessageBox.Icon.Information,
        buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
        default_button: QMessageBox.StandardButton | None = None,
        detailed_text: str | None = None,
    ) -> QMessageBox.StandardButton:
        """
        Show custom dialog with full control.

        Args:
            parent: Parent widget.
            title: Dialog title.
            message: Message to display.
            icon: Icon type.
            buttons: Button combination.
            default_button: Default button.
            detailed_text: Optional detailed info.

        Returns:
            The button that was clicked.

        Example:
            result = DialogHelper.show_custom(
                self,
                "Custom Dialog",
                "Choose an option",
                icon=QMessageBox.Icon.Question,
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
        """
        msg_box = QMessageBox(parent)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(DialogHelper._get_style(parent))
        msg_box.setStandardButtons(buttons)

        if default_button:
            msg_box.setDefaultButton(default_button)

        if detailed_text:
            msg_box.setDetailedText(detailed_text)

        return msg_box.exec()


# ==================== Convenience Functions ====================
# Shorthand access for common operations

def error(parent: QWidget | None, message: str, title: str | None = None) -> None:
    """Shorthand for DialogHelper.show_error()."""
    DialogHelper.show_error(parent, message, title)


def warning(parent: QWidget | None, message: str, title: str | None = None) -> None:
    """Shorthand for DialogHelper.show_warning()."""
    DialogHelper.show_warning(parent, message, title)


def info(parent: QWidget | None, message: str, title: str | None = None) -> None:
    """Shorthand for DialogHelper.show_info()."""
    DialogHelper.show_info(parent, message, title)


def success(parent: QWidget | None, message: str, title: str | None = None) -> None:
    """Shorthand for DialogHelper.show_success()."""
    DialogHelper.show_success(parent, message, title)


def confirm(parent: QWidget | None, message: str, title: str | None = None) -> bool:
    """Shorthand for DialogHelper.confirm()."""
    return DialogHelper.confirm(parent, message, title)


# ==================== Module Exports ====================

__all__: list[str] = [
    "DialogResult",
    "DialogHelper",
    # Convenience functions
    "error",
    "warning",
    "info",
    "success",
    "confirm",
]