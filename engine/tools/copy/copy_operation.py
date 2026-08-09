from __future__ import annotations

from uuid import uuid4

from engine.geometry import Vector3
from engine.transform import (
    TransformContext,
    TransformOperation,
    TransformState,
    TransformTarget,
    TransformTransaction,
)

from engine.tools.copy.copy_command import CopyCommand
from engine.tools.copy.copy_context import delta_changed, vector3


class CopyOperation(TransformOperation):
    """Command-producing transform operation for copy sessions."""

    def __init__(self) -> None:
        """Create a copy operation descriptor."""

        self.operation_id = str(uuid4())
        self.name = "Copy"
        self.operation_type = "Copy"

    def validate(
        self,
        context: TransformContext,
        targets: tuple[TransformTarget, ...],
        state: TransformState,
    ) -> bool:
        """Return True when the copy can be committed."""

        delta = vector3(state.metadata.get("delta", Vector3()))
        return (
            context.command_manager is not None
            and bool(targets)
            and delta_changed(delta)
        )

    def command(self, transaction: TransformTransaction) -> CopyCommand:
        """Return an undoable CopyCommand for this transaction."""

        delta = vector3(transaction.state.metadata.get("delta", Vector3()))
        return CopyCommand(
            transaction.context.workspace,
            [target.entity for target in transaction.targets],
            delta,
            copies=int(transaction.state.metadata.get("copies", 1)),
            spacing=float(transaction.state.metadata.get("spacing", 0.0)),
            targets=transaction.targets,
            actor=transaction.context.actor,
            design_intent_graph_id=transaction.context.design_intent_graph_id,
            associative=bool(transaction.state.metadata.get("associative", False)),
            reference_copy=bool(transaction.state.metadata.get("reference_copy", False)),
        )
