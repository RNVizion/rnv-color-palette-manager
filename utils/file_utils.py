"""
RNV Color Palette Manager - File Utilities Module
Generic file handling utilities for path validation, safe filename generation,
and common file operations.

Features:
- Path validation and extension handling
- Safe filename generation (removes invalid characters)
- Directory creation helpers
- File size utilities
- Backup file creation

Version: 1.0
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from utils.logger import Logger, get_logger_instance

logger: Logger = get_logger_instance(__name__)


class FileUtils:
    """
    Utilities for file operations and path handling.

    All methods are static for convenience.

    Example:
        if FileUtils.validate_file_path(path, must_exist=True):
            process_file(path)

        path = FileUtils.ensure_file_extension(path, ".gpl")

        safe_name = FileUtils.get_safe_filename("my:file*name.txt")
    """

    # Invalid characters for filenames (Windows)
    INVALID_FILENAME_CHARS: str = '<>:"/\\|?*'

    # Maximum filename length
    MAX_FILENAME_LENGTH: int = 255

    @staticmethod
    def ensure_file_extension(filepath: str, default_ext: str) -> str:
        """
        Ensure file has proper extension.

        Args:
            filepath: Original file path.
            default_ext: Default extension to add if missing (include the dot).

        Returns:
            File path with proper extension.

        Example:
            >>> FileUtils.ensure_file_extension("palette", ".gpl")
            'palette.gpl'
        """
        if not filepath:
            return filepath

        if not os.path.splitext(filepath)[1]:
            return filepath + default_ext
        return filepath

    @staticmethod
    def validate_file_path(
        filepath: str,
        must_exist: bool = False,
        check_writable: bool = False,
    ) -> bool:
        """
        Validate a file path.

        Args:
            filepath: Path to validate.
            must_exist: Whether file must already exist.
            check_writable: Whether to check if location is writable.

        Returns:
            True if path is valid.
        """
        if not filepath:
            return False

        try:
            path = Path(filepath)

            if must_exist and not path.exists():
                return False

            directory = path.parent
            if directory and str(directory) != '.' and not directory.exists():
                return False

            if check_writable and directory.exists():
                return os.access(directory, os.W_OK)

            return True

        except Exception as e:
            logger.debug(f"Path validation failed for '{filepath}': {e}")
            return False

    @staticmethod
    def get_safe_filename(
        filename: str,
        max_length: int | None = None,
        replacement: str = "_",
    ) -> str:
        """
        Create a safe filename by removing invalid characters.

        Args:
            filename: Original filename.
            max_length: Maximum filename length (default: 255).
            replacement: Character to replace invalid chars with.

        Returns:
            Safe filename.

        Example:
            >>> FileUtils.get_safe_filename('my:file*name.gpl')
            'my_file_name.gpl'
        """
        if not filename:
            return "unnamed"

        max_length = max_length or FileUtils.MAX_FILENAME_LENGTH

        safe_name = ''.join(
            replacement if c in FileUtils.INVALID_FILENAME_CHARS else c
            for c in filename
        )

        safe_name = safe_name.strip('. ')

        if len(safe_name) > max_length:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:max_length - len(ext)] + ext

        if not safe_name:
            safe_name = "unnamed"

        return safe_name

    @staticmethod
    def create_directory_if_not_exists(directory: str | Path) -> bool:
        """
        Create directory if it doesn't exist.

        Returns:
            True if directory exists or was created successfully.
        """
        try:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {e}")
            return False

    @staticmethod
    def get_file_size_bytes(filepath: str | Path) -> int:
        """Get file size in bytes, or 0 if file doesn't exist."""
        try:
            return os.path.getsize(filepath)
        except Exception as e:
            logger.debug(f"Could not get file size for '{filepath}': {e}")
            return 0

    @staticmethod
    def get_file_size_formatted(filepath: str | Path) -> str:
        """
        Get file size as formatted string (auto-selects unit).

        Returns:
            Formatted size string like "1.5 MB" or "256 KB".
        """
        try:
            size_bytes = os.path.getsize(filepath)

            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.2f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

        except Exception as e:
            logger.debug(f"Could not get file size for '{filepath}': {e}")
            return "Unknown"

    @staticmethod
    def backup_file(
        filepath: str | Path,
        backup_suffix: str = ".bak",
        max_backups: int = 5,
    ) -> str | None:
        """
        Create a backup copy of a file.

        Args:
            filepath: Original file path.
            backup_suffix: Suffix to add to backup filename.
            max_backups: Maximum number of backup files to keep.

        Returns:
            Backup file path or None if failed.
        """
        try:
            path = Path(filepath)

            if not path.exists():
                return None

            if max_backups == 1:
                backup_path = Path(str(filepath) + backup_suffix)
                shutil.copy2(filepath, backup_path)
                return str(backup_path)

            # Multiple backups with rotation
            for i in range(1, max_backups + 1):
                backup_path = Path(f"{filepath}{backup_suffix}{i}")
                if not backup_path.exists():
                    shutil.copy2(filepath, backup_path)
                    return str(backup_path)

            # All slots full -- rotate (delete oldest, shift others)
            oldest = Path(f"{filepath}{backup_suffix}1")
            if oldest.exists():
                oldest.unlink()

            for i in range(2, max_backups + 1):
                current = Path(f"{filepath}{backup_suffix}{i}")
                previous = Path(f"{filepath}{backup_suffix}{i-1}")
                if current.exists():
                    current.rename(previous)

            backup_path = Path(f"{filepath}{backup_suffix}{max_backups}")
            shutil.copy2(filepath, backup_path)
            return str(backup_path)

        except Exception as e:
            logger.error(f"Error creating backup of {filepath}: {e}")
            return None

    @staticmethod
    def get_unique_filename(
        directory: str | Path,
        base_name: str,
        extension: str,
    ) -> str:
        """
        Generate a unique filename in a directory.

        Returns:
            Unique filename (not full path).
        """
        directory = Path(directory)

        filename = f"{base_name}{extension}"
        if not (directory / filename).exists():
            return filename

        counter = 1
        while True:
            filename = f"{base_name}_{counter}{extension}"
            if not (directory / filename).exists():
                return filename
            counter += 1

            if counter > 9999:
                raise ValueError("Too many files with same base name")

    @staticmethod
    def get_file_extension(filepath: str | Path) -> str:
        """Get file extension (lowercase, with dot)."""
        return os.path.splitext(str(filepath))[1].lower()

    @staticmethod
    def is_valid_image_file(filepath: str | Path) -> bool:
        """Check if file has a valid image extension."""
        valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}
        return FileUtils.get_file_extension(filepath) in valid_extensions

    @staticmethod
    def is_valid_palette_file(filepath: str | Path) -> bool:
        """Check if file has a valid palette extension."""
        valid_extensions = {
            '.gpl', '.ase', '.aco', '.acb', '.clr', '.colors',
            '.css', '.json', '.xml', '.svg', '.hex', '.hsv',
            '.hsl', '.txt', '.swatches', '.afpalette',
        }
        return FileUtils.get_file_extension(filepath) in valid_extensions

    @staticmethod
    def copy_file(source: str | Path, destination: str | Path) -> bool:
        """Copy a file to a new location."""
        try:
            shutil.copy2(source, destination)
            return True
        except Exception as e:
            logger.error(f"Error copying {source} to {destination}: {e}")
            return False

    @staticmethod
    def move_file(source: str | Path, destination: str | Path) -> bool:
        """Move a file to a new location."""
        try:
            shutil.move(str(source), str(destination))
            return True
        except Exception as e:
            logger.error(f"Error moving {source} to {destination}: {e}")
            return False

    @staticmethod
    def delete_file(filepath: str | Path) -> bool:
        """Delete a file. Returns True if successful or file doesn't exist."""
        try:
            path = Path(filepath)
            if path.exists():
                path.unlink()
            return True
        except Exception as e:
            logger.error(f"Error deleting {filepath}: {e}")
            return False

    @staticmethod
    def list_files(
        directory: str | Path,
        pattern: str = "*",
        recursive: bool = False,
    ) -> list[Path]:
        """List files in a directory matching a pattern."""
        try:
            directory = Path(directory)
            if recursive:
                return list(directory.rglob(pattern))
            return list(directory.glob(pattern))
        except Exception as e:
            logger.error(f"Error listing files in {directory}: {e}")
            return []


# ==================== Convenience Functions ====================

def ensure_extension(filepath: str, ext: str) -> str:
    """Shorthand for FileUtils.ensure_file_extension()."""
    return FileUtils.ensure_file_extension(filepath, ext)


def safe_filename(name: str) -> str:
    """Shorthand for FileUtils.get_safe_filename()."""
    return FileUtils.get_safe_filename(name)


def file_exists(filepath: str) -> bool:
    """Check if file exists."""
    return FileUtils.validate_file_path(filepath, must_exist=True)


def mkdir(directory: str | Path) -> bool:
    """Shorthand for FileUtils.create_directory_if_not_exists()."""
    return FileUtils.create_directory_if_not_exists(directory)


# ==================== Module Exports ====================

__all__: list[str] = [
    'FileUtils',
    'ensure_extension',
    'safe_filename',
    'file_exists',
    'mkdir',
]
