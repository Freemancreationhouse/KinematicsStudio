from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from engine.geometry import Vector3
from engine.transform import TransformManager, TransformTarget, targets_from_selection

from engine.tools.move.move_context import (
    delta_changed,
    translation_matrix,
    vector3,
)
from engine.tools.move.move_events import MoveEvents
from engine.tools.move.move_numeric_input import MoveNumericInput
from engine.tools.move.move_operation import MoveOperation
from engine.tools.move.move_preview import MovePreview
from engine.tools.move.move_transaction import MoveTransaction


@dataclass
class MoveSession:
    """Professional move session backed by the Transform Framework."""

    workspace: Any
    entities: list[Any]
    start: Vector3
    transform_manager: TransformManager
    actor: str = "human"
    design_intent_graph_id: str = ""
    session_id: str = field(default_factory=lambda: str(uuid4()))
    operation: MoveOperation = field(default_factory=MoveOperation)
    events: MoveEvents = field(default_factory=MoveEvents)
    preview: MovePreview = field(init=False)
    framework_session: Any = field(init=False)
    delta: Vector3 = field(default_factory=Vector3)
    active: bool = True
    numeric_input: MoveNumericInput = field(default_factory=MoveNumericInput)

    def __post_init__(self) -> None:
        """Begin the underlying transform framework session."""

        selection = getattr(self.workspace, "selection", None)
        targets = targets_from_selection(selection)
        if not targets:
            targets = tuple(TransformTarget.from_entity(entity) for entity in self.entities)
        self.framework_session = self.transform_manager.begin_session(
            workspace=self.workspace,
            targets=targets,
            operation=self.operation,
            actor=self.actor,
            design_intent_graph_id=self.design_intent_graph_id,
        )
        self.preview = MovePreview(self.entities)
        self.events.emit("MoveStarted", self.session_id, {"target_count": len(targets)})

    def update_to(self, point: Vector3) -> None:
        """Update preview from a world point."""

        self.update_delta(point - self.start)

    def update_delta(self, delta: Vector3) -> None:
        """Update preview from a delta vector."""

        if not self.active:
            return
        self.delta = vector3(delta)
        self.framework_session.state.metadata["delta"] = self.delta
        self.framework_session.state.set_incremental(translation_matrix(self.delta))
        self.framework_session.state.enable_preview(translation_matrix(self.delta))
        self.preview.update(self.delta)
        self.events.emit("MoveUpdated", self.session_id, {"delta": self.delta})

    def set_numeric_input(
        self,
        *,
        x: float | str | None = None,
        y: float | str | None = None,
        z: float | str | None = None,
        delta_x: float | str | None = None,
        delta_y: float | str | None = None,
        delta_z: float | str | None = None,
        distance: float | str | None = None,
        absolute_position: Vector3 | None = None,
        relative_position: Vector3 | None = None,
    ) -> None:
        """Update preview from unit-aware numeric input values."""

        delta = self.numeric_input.delta_from_values(
            self.delta,
            self.start,
            x=x,
            y=y,
            z=z,
            delta_x=delta_x,
            delta_y=delta_y,
            delta_z=delta_z,
            distance=distance,
            absolute_position=absolute_position,
            relative_position=relative_position,
        )
        self.update_delta(delta)

    def commit(self) -> Any:
        """Commit the move through CommandManager and clear preview."""

        if not self.active:
            return None
        self.preview.clear()
        if not delta_changed(self.delta):
            self.active = False
            self.events.emit("MoveFinished", self.session_id, {})
            return None
        transaction = MoveTransaction(
            context=self.framework_session.context,
            targets=self.framework_session.targets,
            state=self.framework_session.state,
            operation=self.operation,
        )
        transaction.capture_before()
        self.framework_session.transaction = transaction
        result = transaction.commit()
        self.transform_manager.events.emit(
            "MoveSessionCommitted",
            self.framework_session.session_id,
            {"delta": self.delta},
        )
        self.events.emit("MoveCommitted", self.session_id, {"delta": self.delta})
        self.events.emit("MoveFinished", self.session_id, {})
        self.active = False
        return result

    def cancel(self) -> None:
        """Cancel the move session and restore previewed geometry."""

        self.preview.clear()
        self.framework_session.cancel()
        self.transform_manager.events.emit(
            "MoveSessionCancelled",
            self.framework_session.session_id,
            {},
        )
        self.events.emit("MoveCancelled", self.session_id, {})
        self.events.emit("MoveFinished", self.session_id, {})
        self.active = False
