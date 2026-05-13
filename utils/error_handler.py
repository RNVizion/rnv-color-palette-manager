"""
RNV Color Palette Manager - Error Handler Module
Centralized error handling with safe execution wrappers and user-friendly dialogs.

Features:
- Safe execution wrappers for risky operations
- Automatic error logging with context
- User-friendly error dialogs
- Exception categorization
- Decorator for safe methods
- Context manager for exception handling
- Validation helpers for colors and files

Version: 1.0
"""
from __future__ import annotations

import os
from typing import Callable, Any, TypeVar
from functools import wraps

from PyQt6.QtWidgets import QMessageBox, QWidget

from utils.logger import Logger, get_logger_instance
from utils.dialog_helper import DialogHelper

logger: Logger = get_logger_instance(__name__)

T = TypeVar('T')


# ==================== Error Categories ====================

class ErrorCategory:
    """
    Error category classification for better error handling.

    Attributes:
        FILE_IO: File input/output errors
        IMAGE_PROCESSING: Image processing errors
        PALETTE: Palette import/export errors
        VALIDATION: Input validation errors
        PERMISSION: Permission/access errors
        UNKNOWN: Unclassified errors
        USER_CANCELLED: User cancelled operation
        RESOURCE: Resource exhaustion errors (memory, disk)
    """

    FILE_IO: str = "File I/O Error"
    IMAGE_PROCESSING: str = "Image Processing Error"
    PALETTE: str = "Palette Error"
    VALIDATION: str = "Validation Error"
    PERMISSION: str = "Permission Error"
    UNKNOWN: str = "Unknown Error"
    USER_CANCELLED: str = "User Cancelled"
    RESOURCE: str = "Resource Error"


# ==================== Error Handler Class ====================

class ErrorHandler:
    """
    Centralized error handling with logging and user notifications.

    Example:
        success, result = ErrorHandler.safe_execute(
            func=load_palette,
            operation_name="Importing palette",
            args=(file_path,),
            show_error_dialog=True,
            parent_widget=self,
        )
    """

    @staticmethod
    def safe_execute(
        func: Callable[..., T],
        operation_name: str,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
        default_return: Any = None,
        show_error_dialog: bool = False,
        parent_widget: QWidget | None = None,
        error_category: str = ErrorCategory.UNKNOWN,
        critical: bool = False,
    ) -> tuple[bool, Any]:
        """
        Execute a function safely with automatic error handling.

        Args:
            func: Function to execute.
            operation_name: Human-readable operation name for logging.
            args: Positional arguments for func.
            kwargs: Keyword arguments for func.
            default_return: Value to return on error.
            show_error_dialog: Whether to show error dialog to user.
            parent_widget: Parent widget for error dialog.
            error_category: Category of error for better handling.
            critical: Whether this is a critical error.

        Returns:
            Tuple of (success: bool, result or default_return).
        """
        if kwargs is None:
            kwargs = {}

        try:
            logger.debug(f"Executing: {operation_name}")
            result: T = func(*args, **kwargs)
            logger.debug(f"Success: {operation_name}")
            return True, result

        except FileNotFoundError as e:
            error_msg: str = f"File not found: {e}"
            ErrorHandler._handle_error(
                error=e, operation_name=operation_name,
                error_msg=error_msg, error_category=ErrorCategory.FILE_IO,
                show_dialog=show_error_dialog, parent=parent_widget, critical=critical,
            )
            return False, default_return

        except PermissionError as e:
            error_msg = f"Permission denied: {e}"
            ErrorHandler._handle_error(
                error=e, operation_name=operation_name,
                error_msg=error_msg, error_category=ErrorCategory.PERMISSION,
                show_dialog=show_error_dialog, parent=parent_widget, critical=critical,
            )
            return False, default_return

        except ValueError as e:
            error_msg = f"Invalid value: {e}"
            ErrorHandler._handle_error(
                error=e, operation_name=operation_name,
                error_msg=error_msg, error_category=ErrorCategory.VALIDATION,
                show_dialog=show_error_dialog, parent=parent_widget, critical=critical,
            )
            return False, default_return

        except MemoryError as e:
            error_msg = "Out of memory - file may be too large"
            ErrorHandler._handle_error(
                error=e, operation_name=operation_name,
                error_msg=error_msg, error_category=ErrorCategory.RESOURCE,
                show_dialog=show_error_dialog, parent=parent_widget, critical=True,
            )
            return False, default_return

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            ErrorHandler._handle_error(
                error=e, operation_name=operation_name,
                error_msg=error_msg, error_category=error_category,
                show_dialog=show_error_dialog, parent=parent_widget, critical=critical,
            )
            return False, default_return

    @staticmethod
    def _handle_error(
        error: Exception,
        operation_name: str,
        error_msg: str,
        error_category: str,
        show_dialog: bool,
        parent: QWidget | None,
        critical: bool,
    ) -> None:
        """Internal error handler -- logs and optionally shows dialog."""
        logger.error(f"{operation_name} failed: {error_msg}")
        logger.exception("Full stack trace:")

        if critical:
            logger.critical(f"CRITICAL ERROR in {operation_name}: {error_msg}")

        if show_dialog and parent:
            ErrorHandler.show_error_dialog(
                parent=parent,
                title=error_category,
                message=f"{operation_name} failed",
                details=error_msg,
                critical=critical,
            )

    @staticmethod
    def show_error_dialog(
        parent: QWidget,
        title: str,
        message: str,
        details: str = "",
        critical: bool = False,
    ) -> None:
        """
        Show a user-friendly error dialog.

        Args:
            parent: Parent widget.
            title: Dialog title.
            message: Main error message.
            details: Detailed error information.
            critical: Whether this is a critical error.
        """
        logger.debug(f"Showing error dialog: {title}")

        if critical:
            DialogHelper.show_error(
                parent, message, title=f"Critical Error: {title}",
                detailed_text=details,
            )
        else:
            DialogHelper.show_warning(
                parent, message, title=title,
                detailed_text=details,
            )

    @staticmethod
    def _get_error_suggestion(error_category: str, details: str) -> str:
        """Get helpful suggestion based on error type."""
        suggestions: dict[str, str] = {
            ErrorCategory.FILE_IO: (
                "Check that the file exists and is accessible. "
                "Verify the file path is correct."
            ),
            ErrorCategory.PERMISSION: (
                "Check that you have permission to access this file. "
                "Try running the application as administrator or check file permissions."
            ),
            ErrorCategory.IMAGE_PROCESSING: (
                "The image file may be corrupted or in an unsupported format. "
                "Try opening it in another program to verify it's valid."
            ),
            ErrorCategory.PALETTE: (
                "The palette file may be corrupted or in an unsupported format. "
                "Try a different palette format (GPL, JSON, or ASE recommended)."
            ),
            ErrorCategory.VALIDATION: (
                "Check that the input values are correct and within valid ranges."
            ),
            ErrorCategory.RESOURCE: (
                "Close other applications to free up memory or disk space. "
                "Consider using smaller image files."
            ),
        }

        for category, suggestion in suggestions.items():
            if category.lower() in error_category.lower():
                return suggestion

        details_lower: str = details.lower()
        if "disk" in details_lower or "space" in details_lower:
            return "Free up disk space and try again."
        if "memory" in details_lower:
            return "Close other applications and try again with smaller files."
        if "permission" in details_lower:
            return "Check file permissions and try running as administrator."

        return "Check the log files for more details."

    @staticmethod
    def confirm_action(
        parent: QWidget,
        title: str,
        message: str,
        details: str = "",
        default_yes: bool = False,
    ) -> bool:
        """
        Show confirmation dialog for potentially destructive actions.

        Returns:
            True if user confirmed, False otherwise.
        """
        logger.debug(f"Showing confirmation dialog: {title}")
        confirmed = DialogHelper.confirm(parent, message, title=title, default_yes=default_yes)
        logger.debug(f"User {'confirmed' if confirmed else 'cancelled'} action: {title}")
        return confirmed


# ==================== Decorator for Safe Methods ====================

def safe_method(
    operation_name: str | None = None,
    show_error: bool = False,
    default_return: Any = None,
    critical: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., Any]]:
    """
    Decorator for class methods that need safe execution.

    Example:
        @safe_method(operation_name="Loading palette", show_error=True)
        def load_palette(self):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            op_name: str = operation_name or f"{func.__name__}"
            parent: QWidget | None = self if isinstance(self, QWidget) else None

            success, result = ErrorHandler.safe_execute(
                func=lambda: func(self, *args, **kwargs),
                operation_name=op_name,
                show_error_dialog=show_error,
                parent_widget=parent,
                default_return=default_return,
                critical=critical,
            )
            return result

        return wrapper
    return decorator


# ==================== Safe File Operations ====================

class SafeFileOperations:
    """Safe wrappers for common file operations."""

    @staticmethod
    def safe_open_file(
        file_path: str,
        mode: str = 'r',
        encoding: str = 'utf-8',
        parent: QWidget | None = None,
    ) -> tuple[bool, Any]:
        """
        Safely open a file with error handling.

        Returns:
            Tuple of (success, file_handle or None).
        """
        def open_file() -> Any:
            if 'b' in mode:
                return open(file_path, mode)
            return open(file_path, mode, encoding=encoding)

        return ErrorHandler.safe_execute(
            func=open_file,
            operation_name=f"Opening file: {file_path}",
            show_error_dialog=parent is not None,
            parent_widget=parent,
            error_category=ErrorCategory.FILE_IO,
        )

    @staticmethod
    def safe_write_file(
        file_path: str,
        content: str,
        parent: QWidget | None = None,
    ) -> bool:
        """Safely write content to a file. Returns True if successful."""
        def write_file() -> bool:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        success, _ = ErrorHandler.safe_execute(
            func=write_file,
            operation_name=f"Writing file: {file_path}",
            show_error_dialog=parent is not None,
            parent_widget=parent,
            error_category=ErrorCategory.FILE_IO,
        )
        return success

    @staticmethod
    def safe_delete_file(
        file_path: str,
        confirm: bool = True,
        parent: QWidget | None = None,
    ) -> bool:
        """Safely delete a file with optional confirmation."""
        if confirm and parent:
            confirmed: bool = ErrorHandler.confirm_action(
                parent=parent,
                title="Confirm Deletion",
                message="Are you sure you want to delete this file?",
                details=file_path,
                default_yes=False,
            )
            if not confirmed:
                logger.info(f"File deletion cancelled by user: {file_path}")
                return False

        def delete_file() -> bool:
            os.remove(file_path)
            return True

        success, _ = ErrorHandler.safe_execute(
            func=delete_file,
            operation_name=f"Deleting file: {file_path}",
            show_error_dialog=parent is not None,
            parent_widget=parent,
            error_category=ErrorCategory.FILE_IO,
        )
        return success


# ==================== Validation Helpers ====================

class ValidationHelper:
    """Helper functions for input validation with error handling."""

    @staticmethod
    def validate_file_path(
        file_path: str,
        must_exist: bool = True,
        extensions: list[str] | None = None,
    ) -> tuple[bool, str]:
        """
        Validate a file path.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not file_path:
            return False, "File path is empty"

        if must_exist and not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"

        if extensions:
            file_ext: str = os.path.splitext(file_path)[1].lower()
            if file_ext not in extensions:
                valid_exts: str = ', '.join(extensions)
                return False, f"Invalid file type. Expected: {valid_exts}"

        return True, ""

    @staticmethod
    def validate_rgb_values(r: int, g: int, b: int) -> tuple[bool, str]:
        """
        Validate RGB color values.

        Args:
            r, g, b: Red, green, blue values.

        Returns:
            Tuple of (is_valid, error_message).

        Example:
            valid, error = ValidationHelper.validate_rgb_values(255, 128, 0)
        """
        try:
            r_int, g_int, b_int = int(r), int(g), int(b)
        except (TypeError, ValueError):
            return False, f"Invalid RGB values: ({r}, {g}, {b}) -- must be integers"

        for name, val in [("Red", r_int), ("Green", g_int), ("Blue", b_int)]:
            if not 0 <= val <= 255:
                return False, f"{name} value {val} out of range (0-255)"

        return True, ""

    @staticmethod
    def validate_hex_color(hex_color: str) -> tuple[bool, str]:
        """
        Validate a hex color string.

        Args:
            hex_color: Hex color string (e.g., "#FF8800" or "FF8800").

        Returns:
            Tuple of (is_valid, error_message).
        """
        import re

        if not hex_color:
            return False, "Hex color string is empty"

        cleaned = hex_color.lstrip('#')

        if len(cleaned) not in (3, 6):
            return False, f"Invalid hex color length: {hex_color}"

        if not re.match(r'^[0-9a-fA-F]+$', cleaned):
            return False, f"Invalid hex characters in: {hex_color}"

        return True, ""

    @staticmethod
    def validate_weight(weight: int, min_val: int = 0, max_val: int = 100) -> tuple[bool, str]:
        """
        Validate a color weight value.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            w = int(weight)
        except (TypeError, ValueError):
            return False, f"Invalid weight: {weight} -- must be integer"

        if not min_val <= w <= max_val:
            return False, f"Weight {w} out of range ({min_val}-{max_val})"

        return True, ""

    @staticmethod
    def validate_image_size(
        width: int,
        height: int,
        max_dimension: int = 3840,
    ) -> tuple[bool, str]:
        """
        Validate image dimensions for upload.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if width <= 0 or height <= 0:
            return False, f"Invalid dimensions: {width}x{height}"

        if width > max_dimension or height > max_dimension:
            return False, (
                f"Image too large: {width}x{height}. "
                f"Maximum dimension is {max_dimension}px."
            )

        return True, ""


# ==================== Exception Context Manager ====================

class exception_handler:
    """
    Context manager for safe code execution.

    Example:
        with exception_handler("Exporting palette", parent=self):
            export_palette(file_path)
    """

    def __init__(
        self,
        operation_name: str,
        parent: QWidget | None = None,
        show_error: bool = True,
        critical: bool = False,
    ) -> None:
        self.operation_name: str = operation_name
        self.parent: QWidget | None = parent
        self.show_error: bool = show_error
        self.critical: bool = critical

    def __enter__(self) -> exception_handler:
        logger.debug(f"Starting: {self.operation_name}")
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: Any,
    ) -> bool:
        if exc_type is not None:
            ErrorHandler._handle_error(
                error=exc_val if exc_val else Exception("Unknown error"),
                operation_name=self.operation_name,
                error_msg=str(exc_val) if exc_val else "Unknown error",
                error_category=ErrorCategory.UNKNOWN,
                show_dialog=self.show_error,
                parent=self.parent,
                critical=self.critical,
            )
            return True  # Suppress the exception

        logger.debug(f"Completed: {self.operation_name}")
        return False


# ==================== Styled Message Box Helper ====================

def get_message_box_style(parent: QWidget | None = None) -> str:
    """Get the appropriate message box style for the current theme."""
    return DialogHelper._get_style(parent)


def styled_message_box(
    parent: QWidget,
    icon: QMessageBox.Icon,
    title: str,
    text: str,
    informative_text: str = "",
    buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
) -> QMessageBox.StandardButton:
    """Create and show a styled QMessageBox that matches the current theme."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(icon)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)

    if informative_text:
        msg_box.setInformativeText(informative_text)

    msg_box.setStandardButtons(buttons)
    msg_box.setStyleSheet(get_message_box_style(parent))

    return msg_box.exec()


def styled_question_box(
    parent: QWidget,
    title: str,
    text: str,
    informative_text: str = "",
    buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.Yes,
) -> QMessageBox.StandardButton:
    """Create and show a styled Yes/No/Cancel question dialog."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Question)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)

    if informative_text:
        msg_box.setInformativeText(informative_text)

    msg_box.setStandardButtons(buttons)
    msg_box.setDefaultButton(default_button)
    msg_box.setStyleSheet(get_message_box_style(parent))

    return msg_box.exec()


# ==================== Module Exports ====================

__all__: list[str] = [
    'ErrorCategory',
    'ErrorHandler',
    'safe_method',
    'SafeFileOperations',
    'ValidationHelper',
    'exception_handler',
    'styled_message_box',
    'styled_question_box',
    'get_message_box_style',
]
