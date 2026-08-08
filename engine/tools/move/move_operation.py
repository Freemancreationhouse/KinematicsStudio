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

from engine.tools.move.move_command import MoveCommand
from engine.tools.move.move_context import delta_changed, vector3


class MoveOperation(TransformOperation):
    """Command-producing transform operation for move sessions."""

    def __init__(self) -> None:
        """Create a move operation descriptor."""

        self.operation_id = str(uuid4())
        self.name = "Move"
        self.operation_type = "Move"

    def validate(
        self,
        context: TransformContext,
        targets: tuple[TransformTarget, ...],
        state: TransformState,
    ) -> bool:
        """Return True when the move can be committed."""

        delta = vector3(state.metadata.get("delta", Vector3()))
        return (
            context.command_manager is not None
            and bool(targets)
            and delta_changed(delta)
        )

    def command(self, transaction: TransformTransaction) -> MoveCommand:
        """Return an undoable MoveCommand for this transaction."""

        delta = vector3(transaction.state.metadata.get("delta", Vector3()))
        return MoveCommand(
            transaction.context.workspace,
            [target.entity for target in transaction.targets],
            delta,
            targets=transaction.targets,
            actor=transaction.context.actor,
            design_intent_graph_id=transaction.context.design_intent_graph_id,
        )
