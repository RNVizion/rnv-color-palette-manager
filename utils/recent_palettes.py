"""
Recent Palettes manager for RNV Color Palette Manager.
Persists recently opened/saved palette file paths in QSettings.
Optimized for Python 3.13.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QSettings

from utils.logger import Logger, get_logger_instance

logger: Logger = get_logger_instance(__name__)

MAX_ENTRIES_LIMIT: int = 30  # Hard cap regardless of user setting


@dataclass
class RecentPaletteEntry:
    """A single recent palette entry."""

    path: str
    name: str = ""           # Palette name from metadata, or filename stem
    format_ext: str = ""     # e.g. ".gpl", ".ase"
    color_count: int = 0
    timestamp: str = ""      # ISO format datetime string

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecentPaletteEntry:
        return cls(
            path=data.get("path", ""),
            name=data.get("name", ""),
            format_ext=data.get("format_ext", ""),
            color_count=data.get("color_count", 0),
            timestamp=data.get("timestamp", ""),
        )

    @property
    def exists(self) -> bool:
        """Check if the file still exists on disk."""
        return Path(self.path).exists()

    @property
    def display_name(self) -> str:
        """Name for display in menus: palette name or filename."""
        if self.name:
            return self.name
        return Path(self.path).stem

    @property
    def display_detail(self) -> str:
        """Secondary info: color count + format."""
        parts: list[str] = []
        if self.color_count > 0:
            parts.append(f"{self.color_count} colors")
        if self.format_ext:
            parts.append(self.format_ext.upper().lstrip("."))
        return " · ".join(parts) if parts else ""

    @property
    def folder(self) -> str:
        """Parent directory path."""
        return str(Path(self.path).parent)


class RecentPalettesManager:
    """
    Manages a list of recently opened/saved palette files.
    Persisted in QSettings as a JSON array.
    """

    SETTINGS_KEY: str = "recent_palettes/entries"

    def __init__(self, settings: QSettings, max_entries: int = 10) -> None:
        self._settings = settings
        self._max_entries = min(max_entries, MAX_ENTRIES_LIMIT)
        self._entries: list[RecentPaletteEntry] = []
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def entries(self) -> list[RecentPaletteEntry]:
        """Return current entries (most recent first)."""
        return list(self._entries)

    @property
    def max_entries(self) -> int:
        return self._max_entries

    @max_entries.setter
    def max_entries(self, value: int) -> None:
        self._max_entries = max(1, min(value, MAX_ENTRIES_LIMIT))
        self._trim()
        self._save()

    def add(
        self,
        path: str,
        name: str = "",
        format_ext: str = "",
        color_count: int = 0,
    ) -> None:
        """Add or update a recent palette entry (moves to top if exists)."""
        abs_path = str(Path(path).resolve())

        # Remove existing entry with same path
        self._entries = [e for e in self._entries if e.path != abs_path]

        entry = RecentPaletteEntry(
            path=abs_path,
            name=name,
            format_ext=format_ext,
            color_count=color_count,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )
        self._entries.insert(0, entry)
        self._trim()
        self._save()
        logger.debug(f"Recent palette added: {entry.display_name}")

    def remove(self, path: str) -> None:
        """Remove a specific entry by path."""
        abs_path = str(Path(path).resolve())
        self._entries = [e for e in self._entries if e.path != abs_path]
        self._save()

    def clear(self) -> None:
        """Remove all entries."""
        self._entries.clear()
        self._save()
        logger.info("Recent palettes cleared")

    def prune_missing(self) -> int:
        """Remove entries whose files no longer exist. Returns count removed."""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.exists]
        removed = before - len(self._entries)
        if removed > 0:
            self._save()
            logger.info(f"Pruned {removed} missing recent palette(s)")
        return removed

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load entries from QSettings."""
        try:
            raw = self._settings.value(self.SETTINGS_KEY, "[]")
            if isinstance(raw, str):
                data = json.loads(raw)
            elif isinstance(raw, list):
                data = raw
            else:
                data = []
            self._entries = [RecentPaletteEntry.from_dict(d) for d in data]
            self._trim()
        except Exception as e:
            logger.warning(f"Failed to load recent palettes: {e}")
            self._entries = []

    def _save(self) -> None:
        """Save entries to QSettings."""
        try:
            data = [e.to_dict() for e in self._entries]
            self._settings.setValue(self.SETTINGS_KEY, json.dumps(data))
        except Exception as e:
            logger.warning(f"Failed to save recent palettes: {e}")

    def _trim(self) -> None:
        """Trim entries to max_entries."""
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[: self._max_entries]


__all__: list[str] = [
    "RecentPalettesManager",
    "RecentPaletteEntry",
]
