"""
RNV Color Palette Manager - Export History Module
Tracks recent palette export operations.

Features:
- Records export path, format, timestamp, color count
- Persists history to JSON file
- Configurable max entries (default 20)
- Provides formatted display strings for UI

Optimized for Python 3.13.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.config import USER_DATA_DIR
from utils.logger import Logger, get_logger_instance

logger: Logger = get_logger_instance(__name__)

# History file location
EXPORT_HISTORY_PATH = USER_DATA_DIR / "export_history.json"
MAX_HISTORY_ENTRIES: int = 20


@dataclass
class ExportEntry:
    """Single export history record."""

    path: str
    format_ext: str
    timestamp: str
    color_count: int
    file_size_bytes: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExportEntry:
        return cls(
            path=data.get("path", ""),
            format_ext=data.get("format_ext", ""),
            timestamp=data.get("timestamp", ""),
            color_count=data.get("color_count", 0),
            file_size_bytes=data.get("file_size_bytes", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def filename(self) -> str:
        """Just the filename portion of the path."""
        return Path(self.path).name

    @property
    def directory(self) -> str:
        """Parent directory of the export."""
        return str(Path(self.path).parent)

    @property
    def formatted_time(self) -> str:
        """Human-readable timestamp."""
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return self.timestamp

    @property
    def display_string(self) -> str:
        """Formatted string for UI display."""
        return (
            f"{self.filename}  "
            f"({self.color_count} colors, "
            f"{self.format_ext})  "
            f"-- {self.formatted_time}"
        )

    @property
    def file_exists(self) -> bool:
        """Check if the exported file still exists on disk."""
        return Path(self.path).exists()


class ExportHistory:
    """
    Manages a persistent list of recent palette exports.

    The history is stored as a JSON array in the user data directory.
    New entries are prepended; the list is trimmed to MAX_HISTORY_ENTRIES.

    Example:
        >>> history = ExportHistory()
        >>> history.add_entry("/path/to/palette.json", ".json", 12)
        >>> for entry in history.get_history():
        ...     print(entry.display_string)
    """

    def __init__(self, max_entries: int = MAX_HISTORY_ENTRIES) -> None:
        self._max_entries = max_entries
        self._entries: list[ExportEntry] = []
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load history from disk."""
        if not EXPORT_HISTORY_PATH.exists():
            self._entries = []
            return
        try:
            with open(EXPORT_HISTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._entries = [ExportEntry.from_dict(d) for d in data]
            logger.success(
                f"Loaded {len(self._entries)} export history "
                f"{'entry' if len(self._entries) == 1 else 'entries'}"
            )
        except Exception as e:
            logger.warning(f"Failed to load export history: {e}")
            self._entries = []

    def _save(self) -> None:
        """Persist history to disk."""
        try:
            USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(EXPORT_HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in self._entries], f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save export history: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_entry(
        self,
        path: str,
        format_ext: str,
        color_count: int,
        file_size_bytes: int = 0,
    ) -> None:
        """
        Record a new export.

        Args:
            path: Full path to the exported file.
            format_ext: File extension (e.g. '.json', '.ase').
            color_count: Number of colors exported.
            file_size_bytes: Size of the output file in bytes.
        """
        entry = ExportEntry(
            path=path,
            format_ext=format_ext,
            timestamp=datetime.now().isoformat(),
            color_count=color_count,
            file_size_bytes=file_size_bytes,
        )
        # Prepend (most recent first)
        self._entries.insert(0, entry)

        # Trim to max
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[: self._max_entries]

        self._save()
        logger.debug(f"Export recorded: {entry.filename} ({format_ext})")

    def get_history(self, limit: int | None = None) -> list[ExportEntry]:
        """
        Get the export history list (newest first).

        Args:
            limit: Maximum entries to return. None = all.

        Returns:
            List of ExportEntry objects.
        """
        if limit is not None:
            return self._entries[:limit]
        return list(self._entries)

    def get_last_entry(self) -> ExportEntry | None:
        """Get the most recent export entry, or None."""
        return self._entries[0] if self._entries else None

    def get_last_directory(self) -> str:
        """Get the directory of the most recent export."""
        if self._entries:
            return self._entries[0].directory
        return ""

    def get_last_format(self) -> str:
        """Get the format extension of the most recent export."""
        if self._entries:
            return self._entries[0].format_ext
        return ""

    def clear(self) -> None:
        """Clear all export history."""
        self._entries.clear()
        self._save()
        logger.info("Export history cleared")

    @property
    def count(self) -> int:
        """Number of history entries."""
        return len(self._entries)

    @property
    def is_empty(self) -> bool:
        """True if no history entries exist."""
        return len(self._entries) == 0


# ==================== Module Exports ====================

__all__: list[str] = [
    "ExportHistory",
    "ExportEntry",
    "EXPORT_HISTORY_PATH",
    "MAX_HISTORY_ENTRIES",
]
