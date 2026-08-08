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

from engine.tools.scale.scale_command import ScaleCommand
from engine.tools.scale.scale_context import scale_changed, scale_vector


class ScaleOperation(TransformOperation):
    """Command-producing transform operation for scale sessions."""

    def __init__(self) -> None:
        """Create a scale operation descriptor."""

        self.operation_id = str(uuid4())
        self.name = "Scale"
        self.operation_type = "Scale"

    def validate(
        self,
        context: TransformContext,
        targets: tuple[TransformTarget, ...],
        state: TransformState,
    ) -> bool:
        """Return True when the scale can be committed."""

        factors = scale_vector(state.metadata.get("factors", Vector3(1.0, 1.0, 1.0)))
        return (
            context.command_manager is not None
            and bool(targets)
            and scale_changed(factors)
        )

    def command(self, transaction: TransformTransaction) -> ScaleCommand:
        """Return an undoable ScaleCommand for this transaction."""

        factors = scale_vector(transaction.state.metadata.get("factors", Vector3(1.0, 1.0, 1.0)))
        pivot = transaction.state.metadata.get("pivot", Vector3())
        mode = str(transaction.state.metadata.get("mode", "Uniform"))
        return ScaleCommand(
            transaction.context.workspace,
            [target.entity for target in transaction.targets],
            factors,
            pivot=pivot,
            mode=mode,
            targets=transaction.targets,
            actor=transaction.context.actor,
            design_intent_graph_id=transaction.context.design_intent_graph_id,
        )
