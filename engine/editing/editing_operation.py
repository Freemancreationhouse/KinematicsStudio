from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from engine.editing.editing_context import EditingContext


class EditingOperation(Protocol):
    """Protocol implemented by future concrete editing operations."""

    operation_id: str
    name: str

    def validate(self, context: "EditingContext") -> bool:
        """Return whether this operation can run in the context."""

    def command(self, context: "EditingContext") -> Any:
        """Return an undoable command for this operation."""
