"""
Undo/Redo manager using the Command pattern.
Tracks reversible actions on the color palette with a configurable stack depth.
Optimized for Python 3.13.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from PyQt6.QtGui import QColor

from utils.logger import Logger, get_logger_instance

logger: Logger = get_logger_instance(__name__)

# Type alias for a serialised slot snapshot
type SlotSnapshot = dict[str, Any]


@dataclass
class PaletteState:
    """Complete snapshot of the palette at a point in time."""
    slots: list[SlotSnapshot] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    groups: list[dict[str, Any]] = field(default_factory=list)

    @staticmethod
    def capture(
        slots_widgets,
        metadata_dict: dict[str, Any] | None = None,
        groups_data: list[dict[str, Any]] | None = None,
    ) -> PaletteState:
        """Capture current state of all slot widgets."""
        snapshots: list[SlotSnapshot] = []
        for w in slots_widgets:
            snap: SlotSnapshot = {
                "r": w.slot.color.red(),
                "g": w.slot.color.green(),
                "b": w.slot.color.blue(),
                "a": w.slot.color.alpha(),
                "locked": w.locked,
                "has_image": w.slot.image_pixmap is not None,
                "hex_text": w.hex_label.text(),
                "is_default_color": getattr(w.slot, '_is_default_color', False),
            }
            snapshots.append(snap)
        return PaletteState(
            slots=snapshots,
            metadata=metadata_dict or {},
            groups=groups_data or [],
        )


class UndoManager:
    """
    Manages an undo/redo stack of PaletteState snapshots.

    Usage:
        1. Call ``push()`` BEFORE making a change (captures current state).
        2. The user performs the change.
        3. Call ``undo()`` to revert to the previous state.
        4. Call ``redo()`` to reapply a reverted change.

    The manager stores complete palette snapshots, which is simple and
    robust at the cost of slightly higher memory usage.  With a stack
    depth of 50 and <= 99 slots each holding ~6 fields the overhead is
    negligible.
    """

    MAX_DEPTH: int = 50

    def __init__(self) -> None:
        self._undo_stack: list[PaletteState] = []
        self._redo_stack: list[PaletteState] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def push(self, state: PaletteState) -> None:
        """
        Save a state snapshot onto the undo stack.

        Call this BEFORE making a change so the previous state can be
        restored later.  Clears the redo stack (new action branch).
        """
        self._undo_stack.append(state)
        if len(self._undo_stack) > self.MAX_DEPTH:
            self._undo_stack.pop(0)
        # New action invalidates redo history
        self._redo_stack.clear()
        logger.debug(f"Undo push (depth={len(self._undo_stack)})")

    def undo(self, current_state: PaletteState) -> PaletteState | None:
        """
        Pop the most recent state from the undo stack.

        The *current* state is pushed onto the redo stack so the user
        can redo later.

        Returns:
            The previous PaletteState to restore, or None if nothing to undo.
        """
        if not self._undo_stack:
            logger.debug("Nothing to undo")
            return None

        self._redo_stack.append(current_state)
        previous = self._undo_stack.pop()
        logger.debug(
            f"Undo (remaining={len(self._undo_stack)}, "
            f"redo={len(self._redo_stack)})"
        )
        return previous

    def redo(self, current_state: PaletteState) -> PaletteState | None:
        """
        Pop the most recent state from the redo stack.

        The *current* state is pushed back onto the undo stack.

        Returns:
            The PaletteState to restore, or None if nothing to redo.
        """
        if not self._redo_stack:
            logger.debug("Nothing to redo")
            return None

        self._undo_stack.append(current_state)
        next_state = self._redo_stack.pop()
        logger.debug(
            f"Redo (undo={len(self._undo_stack)}, "
            f"remaining={len(self._redo_stack)})"
        )
        return next_state

    def clear(self) -> None:
        """Clear both stacks."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        logger.debug("Undo/Redo stacks cleared")

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def undo_depth(self) -> int:
        return len(self._undo_stack)

    @property
    def redo_depth(self) -> int:
        return len(self._redo_stack)