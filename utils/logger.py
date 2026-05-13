"""
RNV Color Palette Manager - Logging Module
Provides centralized logging functionality with console and file output.

Features:
- Colored console output for different log levels
- File logging with rotation
- Easy-to-use setup function
- Per-module loggers
- Logger class wrapper for cleaner API

Version: 1.0
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


# ==================== Color Codes for Console ====================

class LogColors:
    """ANSI color codes for terminal output (used for terminals that support it)."""

    RESET: str = '\033[0m'
    BOLD: str = '\033[1m'
    DIM: str = '\033[2m'

    # Log level colors
    DEBUG: str = '\033[36m'      # Cyan
    INFO: str = '\033[32m'       # Green
    WARNING: str = '\033[33m'    # Yellow
    ERROR: str = '\033[31m'      # Red
    CRITICAL: str = '\033[35m'   # Magenta

    # Symbol colors
    SUCCESS: str = '\033[92m'    # Bright Green
    FAIL: str = '\033[91m'       # Bright Red
    CAUTION: str = '\033[93m'    # Bright Yellow

    # Additional bright colors
    BRIGHT_CYAN: str = '\033[96m'
    BRIGHT_WHITE: str = '\033[97m'


def _check_color_support() -> bool:
    """Check if terminal supports ANSI colors."""
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False

    # Check for Windows -- disable colors by default for cleaner output
    if os.name == 'nt':
        # Only enable colors if explicitly in Windows Terminal or VS Code
        wt_session = os.environ.get('WT_SESSION')
        term_program = os.environ.get('TERM_PROGRAM', '')
        if wt_session or term_program == 'vscode':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except Exception:
                return False
        return False

    return True


# Check color support once at module load
_COLORS_SUPPORTED: bool = _check_color_support()


def _get_short_name(full_name: str) -> str:
    """
    Convert full module name to short display name.

    Examples:
        'RNV_Color_Palette_Manager.__main__' -> 'Application'
        'core.color_slot' -> 'ColorSlot'
        'ui.theme_manager' -> 'ThemeManager'
        'utils.font_loader' -> 'FontLoader'
        'PaletteFormats' -> 'PaletteFormats' (already PascalCase)
    """
    # Handle __main__ specially
    if '__main__' in full_name:
        return 'Application'

    # Get the last part of the module path
    last_part = full_name.split('.')[-1]

    # If already has mixed case (PascalCase), return as-is
    if any(c.isupper() for c in last_part[1:]):
        return last_part

    # Convert snake_case to PascalCase
    words = last_part.split('_')
    pascal_case = ''.join(word.capitalize() for word in words)

    return pascal_case


# ==================== Custom Formatters ====================

class CleanFormatter(logging.Formatter):
    """
    Clean formatter for console output without ANSI codes.

    Produces output like:
        INFO     | Application          | Starting application...
        SUCCESS  | FontLoader           | + Loaded Montserrat-Black (file)
    """

    LEVEL_WIDTH: int = 8
    NAME_WIDTH: int = 20

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with clean aligned columns."""
        short_name = _get_short_name(record.name)
        level_name = record.levelname
        message = record.getMessage()

        # Check if this is a success message (starts with + )
        if message.startswith('+ '):
            level_name = 'SUCCESS'

        return (
            f"{level_name:<{self.LEVEL_WIDTH}} | "
            f"{short_name:<{self.NAME_WIDTH}} | "
            f"{message}"
        )


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for terminals that support ANSI codes.
    Falls back to CleanFormatter behavior when colors aren't supported.
    """

    LEVEL_WIDTH: int = 8
    NAME_WIDTH: int = 20

    LEVEL_COLORS: dict[int, str] = {
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors if supported."""
        short_name = _get_short_name(record.name)
        level_name = record.levelname
        message = record.getMessage()

        # Check if this is a success message
        if message.startswith('+ '):
            level_name = 'SUCCESS'
            color = LogColors.SUCCESS
        else:
            color = self.LEVEL_COLORS.get(record.levelno, '')

        if _COLORS_SUPPORTED and color:
            return (
                f"{color}{level_name:<{self.LEVEL_WIDTH}}{LogColors.RESET} | "
                f"{short_name:<{self.NAME_WIDTH}} | "
                f"{message}"
            )
        return (
            f"{level_name:<{self.LEVEL_WIDTH}} | "
            f"{short_name:<{self.NAME_WIDTH}} | "
            f"{message}"
        )


class FileFormatter(logging.Formatter):
    """
    Formatter for file output (no colors).
    Uses a standard format with timestamp for log files.
    """

    LEVEL_WIDTH: int = 8
    NAME_WIDTH: int = 20

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for file output."""
        short_name = _get_short_name(record.name)
        level_name = record.levelname
        message = record.getMessage()

        if message.startswith('+ '):
            level_name = 'SUCCESS'

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return (
            f"{timestamp} | "
            f"{level_name:<{self.LEVEL_WIDTH}} | "
            f"{short_name:<{self.NAME_WIDTH}} | "
            f"{message}"
        )


# ==================== Logger Setup ====================

def setup_logger(
    name: str = 'RNV_Color_Palette_Manager',
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_dir: Path | None = None,
    max_file_size: int | None = None,
    backup_count: int | None = None,
) -> logging.Logger:
    """
    Setup and configure application logger.

    Args:
        name: Logger name (typically application root name).
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_to_file: Whether to log to file in addition to console.
        log_dir: Directory for log files. Defaults to config LOGS_DIR.
        max_file_size: Max size of log file before rotation (bytes).
                       Defaults to config LOG_FILE_MAX_SIZE.
        backup_count: Number of backup log files to keep.
                      Defaults to config LOG_FILE_BACKUP_COUNT.

    Returns:
        Configured logger instance.

    Example:
        >>> logger = setup_logger(level=logging.DEBUG)
        >>> logger.info("Application started")
    """
    # Import config here to avoid circular imports at module level
    from utils.config import LOGS_DIR, LOG_FILE_MAX_SIZE, LOG_FILE_BACKUP_COUNT

    logger: logging.Logger = logging.getLogger(name)

    # Don't add handlers if already configured
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_to_file:
        if log_dir is None:
            log_dir = LOGS_DIR
        else:
            log_dir = Path(log_dir)

        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp: str = datetime.now().strftime('%Y%m%d')
        log_file: Path = log_dir / f'palette_manager_{timestamp}.log'

        file_size = max_file_size if max_file_size is not None else LOG_FILE_MAX_SIZE
        file_count = backup_count if backup_count is not None else LOG_FILE_BACKUP_COUNT

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=file_size,
            backupCount=file_count,
            encoding='utf-8',
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(FileFormatter())
        logger.addHandler(file_handler)

        logger.debug(f"Log file created: {log_file}")

    return logger


# ==================== Convenience Functions ====================

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Module name (use __name__ from calling module).

    Returns:
        Logger instance for the specified module.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    return logging.getLogger(f'RNV_Color_Palette_Manager.{name}')


def set_log_level(level: int) -> None:
    """
    Change the logging level for all loggers.

    Args:
        level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Example:
        >>> set_log_level(logging.DEBUG)  # Enable debug output
    """
    root_logger: logging.Logger = logging.getLogger('RNV_Color_Palette_Manager')
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        handler.setLevel(level)


# ==================== Logger Class Wrapper ====================

class Logger:
    """
    Logger class wrapper providing a cleaner API for logging.

    Wraps the standard Python logging module with convenience methods
    like success(), header(), separator() for better developer experience.

    Usage:
        logger = Logger("ModuleName")
        logger.info("Starting operation...")
        logger.success("Operation complete!")
        logger.warning("Something might be wrong")
        logger.error("Operation failed", error=exception)
        logger.header("Section Title")
        logger.separator()
    """

    # Windows-compatible symbols
    SYMBOL_SUCCESS: str = "+"
    SYMBOL_FAIL: str = "X"
    SYMBOL_WARNING: str = "!"
    SYMBOL_INFO: str = ">"
    SYMBOL_DEBUG: str = "."

    def __init__(self, name: str) -> None:
        """
        Initialize logger wrapper.

        Args:
            name: Logger name (typically module name).
        """
        self.name = name
        self._logger = get_logger(name)
        self._use_colors = _COLORS_SUPPORTED

    @property
    def underlying_logger(self) -> logging.Logger:
        """Get the underlying Python logging.Logger instance."""
        return self._logger

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._logger.debug(message)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._logger.info(message)

    def success(self, message: str, details: str | None = None, **kwargs: Any) -> None:
        """
        Log success message with plus symbol.
        The formatter will display this as SUCCESS level.

        Args:
            message: Success message.
            details: Optional additional details.

        Example:
            logger.success("File saved", details="palette.gpl")
        """
        full_message = f"+ {message}"
        if details:
            full_message += f"  ({details})"
        self._logger.info(full_message)

    def warning(self, message: str, details: str | None = None, **kwargs: Any) -> None:
        """
        Log warning message.

        Args:
            message: Warning message.
            details: Optional additional details.
        """
        if details:
            message = f"{message} ({details})"
        self._logger.warning(message)

    def error(
        self,
        message: str,
        error: Exception | None = None,
        details: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Log error message with optional exception details.

        Args:
            message: Error message.
            error: Optional exception object.
            details: Optional additional details.

        Example:
            try:
                load_file()
            except Exception as e:
                logger.error("Failed to load file", error=e)
        """
        full_message = f"X {message}"

        if error:
            error_type = type(error).__name__
            full_message += f" [{error_type}: {error}]"

        if details:
            full_message += f" ({details})"

        self._logger.error(full_message)

    def exception(
        self,
        message: str,
        error: Exception | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Log error message with full stack trace.

        Uses logging.exception() which automatically captures and formats
        the current exception traceback. Should be called from within an
        except block.

        Args:
            message: Error message describing what failed.
            error: Optional exception object (for additional context).

        Example:
            try:
                process_file()
            except Exception as e:
                logger.exception("Full stack trace:")
        """
        full_message = f"X {message}"

        if error:
            error_type = type(error).__name__
            full_message += f" [{error_type}: {error}]"

        self._logger.exception(full_message)

    def critical(
        self,
        message: str,
        error: Exception | None = None,
        details: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Log critical error message.

        Args:
            message: Critical error message.
            error: Optional exception object.
            details: Optional additional details.
        """
        full_message = message

        if error:
            error_type = type(error).__name__
            full_message += f" [{error_type}: {error}]"

        if details:
            full_message += f" ({details})"

        self._logger.critical(full_message)

    def separator(self, char: str = "=", length: int = 60) -> None:
        """Print a separator line."""
        print(char * length)

    def header(self, message: str, char: str = "=", length: int = 60) -> None:
        """
        Print a header with separators.

        Args:
            message: Header text.
            char: Character to use for separator.
            length: Total length of header line.
        """
        self.separator(char, length)
        padding = (length - len(message) - 2) // 2
        centered = f"{char * padding} {message} {char * padding}"
        if len(centered) < length:
            centered += char
        print(centered)
        self.separator(char, length)

    def blank(self) -> None:
        """Print a blank line."""
        print()

    def indent(self, message: str, level: int = 1) -> None:
        """
        Print an indented message.

        Args:
            message: Message to print.
            level: Indentation level (each level = 2 spaces).
        """
        indent_str = "  " * level
        print(f"{indent_str}{message}")


# ==================== Global Logger Registry ====================

_logger_instances: dict[str, Logger] = {}


def get_logger_instance(name: str) -> Logger:
    """
    Get or create a Logger class instance by name.
    Caches instances so the same name always returns the same Logger.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Logger class instance.

    Example:
        logger = get_logger_instance(__name__)
        logger.success("Module loaded")
    """
    if name not in _logger_instances:
        _logger_instances[name] = Logger(name)
    return _logger_instances[name]


# ==================== Exports ====================

__all__ = [
    # Classes
    "LogColors",
    "CleanFormatter",
    "ColoredFormatter",
    "FileFormatter",
    "Logger",
    # Setup
    "setup_logger",
    "get_logger",
    "get_logger_instance",
    "set_log_level",
]