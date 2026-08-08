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

from engine.tools.rotate.rotate_command import RotateCommand
from engine.tools.rotate.rotate_context import (
    angle_changed,
    axis_vector,
    vector3,
)


class RotateOperation(TransformOperation):
    """Command-producing transform operation for rotate sessions."""

    def __init__(self) -> None:
        """Create a rotate operation descriptor."""

        self.operation_id = str(uuid4())
        self.name = "Rotate"
        self.operation_type = "Rotate"

    def validate(
        self,
        context: TransformContext,
        targets: tuple[TransformTarget, ...],
        state: TransformState,
    ) -> bool:
        """Return True when the rotation can be committed."""

        angle = float(state.metadata.get("angle_degrees", 0.0))
        return (
            context.command_manager is not None
            and bool(targets)
            and angle_changed(angle)
        )

    def command(self, transaction: TransformTransaction) -> RotateCommand:
        """Return an undoable RotateCommand for this transaction."""

        angle = float(transaction.state.metadata.get("angle_degrees", 0.0))
        pivot = vector3(transaction.state.metadata.get("pivot", Vector3()))
        axis = axis_vector(transaction.state.metadata.get("axis", Vector3(0.0, 0.0, 1.0)))
        return RotateCommand(
            transaction.context.workspace,
            [target.entity for target in transaction.targets],
            angle,
            pivot=pivot,
            axis=axis,
            targets=transaction.targets,
            actor=transaction.context.actor,
            design_intent_graph_id=transaction.context.design_intent_graph_id,
        )
