from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from engine.transform.transform_context import TransformContext
    from engine.transform.transform_state import TransformState
    from engine.transform.transform_target import TransformTarget
    from engine.transform.transform_transaction import TransformTransaction


class TransformOperation(Protocol):
    """Protocol for future command-producing transform operations."""

    operation_id: str
    name: str
    operation_type: str

    def validate(
        self,
        context: "TransformContext",
        targets: tuple["TransformTarget", ...],
        state: "TransformState",
    ) -> bool:
        """Return True when this operation is valid for the context."""

    def command(self, transaction: "TransformTransaction") -> Any:
        """Return an undoable command for the transform transaction."""
