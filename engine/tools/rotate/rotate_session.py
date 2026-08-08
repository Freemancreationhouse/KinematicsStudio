from __future__ import annotations

from dataclasses import dataclass, field
from math import atan2, degrees
from typing import Any
from uuid import uuid4

from engine.geometry import Vector3
from engine.transform import TransformManager, TransformTarget, targets_from_selection

from engine.tools.rotate.rotate_context import (
    angle_changed,
    axis_vector,
    point_to_vector3,
    rotation_matrix,
    vector3,
)
from engine.tools.rotate.rotate_events import RotateEvents
from engine.tools.rotate.rotate_numeric_input import RotateNumericInput
from engine.tools.rotate.rotate_operation import RotateOperation
from engine.tools.rotate.rotate_preview import RotatePreview
from engine.tools.rotate.rotate_transaction import RotateTransaction


@dataclass
class RotateSession:
    """Professional rotate session backed by the Transform Framework."""

    workspace: Any
    entities: list[Any]
    pivot: Vector3
    transform_manager: TransformManager
    axis: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 1.0))
    reference: Vector3 | None = None
    actor: str = "human"
    design_intent_graph_id: str = ""
    session_id: str = field(default_factory=lambda: str(uuid4()))
    operation: RotateOperation = field(default_factory=RotateOperation)
    events: RotateEvents = field(default_factory=RotateEvents)
    preview: RotatePreview = field(init=False)
    framework_session: Any = field(init=False)
    angle_degrees: float = 0.0
    active: bool = True
    numeric_input: RotateNumericInput = field(default_factory=RotateNumericInput)

    def __post_init__(self) -> None:
        """Begin the underlying transform framework session."""

        self.pivot = vector3(self.pivot)
        self.axis = axis_vector(self.axis)
        if self.reference is not None:
            self.reference = point_to_vector3(self.reference)
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
        self.preview = RotatePreview(self.entities, self.pivot, self.axis)
        self._sync_state()
        self.events.emit("RotateStarted", self.session_id, {"target_count": len(targets)})

    def update_to(self, point: Any) -> None:
        """Update preview from a world point."""

        target = point_to_vector3(point)
        if self.reference is None:
            self.reference = target
            return
        self.update_angle(self._angle_between(self.reference, target))

    def update_angle(self, angle_degrees: float) -> None:
        """Update preview from an angle in degrees."""

        if not self.active:
            return
        self.angle_degrees = float(angle_degrees)
        self._sync_state()
        self.preview.update(self.angle_degrees)
        self.events.emit(
            "RotateUpdated",
            self.session_id,
            {"angle_degrees": self.angle_degrees},
        )

    def set_numeric_input(
        self,
        *,
        degrees: float | str | None = None,
        radians: float | str | None = None,
        relative_angle: float | str | None = None,
        absolute_angle: float | str | None = None,
        clockwise: bool = False,
        counter_clockwise: bool = False,
    ) -> None:
        """Update preview from unit-aware numeric angle values."""

        angle = self.numeric_input.angle_from_values(
            self.angle_degrees,
            degrees=degrees,
            radians=radians,
            relative_angle=relative_angle,
            absolute_angle=absolute_angle,
            clockwise=clockwise,
            counter_clockwise=counter_clockwise,
        )
        self.update_angle(angle)

    def commit(self) -> Any:
        """Commit the rotation through CommandManager and clear preview."""

        if not self.active:
            return None
        self.preview.clear()
        if not angle_changed(self.angle_degrees):
            self.active = False
            self.events.emit("RotateFinished", self.session_id, {})
            return None
        transaction = RotateTransaction(
            context=self.framework_session.context,
            targets=self.framework_session.targets,
            state=self.framework_session.state,
            operation=self.operation,
        )
        transaction.capture_before()
        self.framework_session.transaction = transaction
        result = transaction.commit()
        self.transform_manager.events.emit(
            "RotateSessionCommitted",
            self.framework_session.session_id,
            {"angle_degrees": self.angle_degrees},
        )
        self.events.emit(
            "RotateCommitted",
            self.session_id,
            {"angle_degrees": self.angle_degrees},
        )
        self.events.emit("RotateFinished", self.session_id, {})
        self.active = False
        return result

    def cancel(self) -> None:
        """Cancel the rotate session and restore previewed geometry."""

        self.preview.clear()
        self.framework_session.cancel()
        self.transform_manager.events.emit(
            "RotateSessionCancelled",
            self.framework_session.session_id,
            {},
        )
        self.events.emit("RotateCancelled", self.session_id, {})
        self.events.emit("RotateFinished", self.session_id, {})
        self.active = False

    def draw_preview(self, painter: Any) -> None:
        """Draw non-mutating replacement preview geometry."""

        self.preview.draw(painter)

    def _sync_state(self) -> None:
        """Synchronize rotate metadata into the transform state."""

        state = self.framework_session.state
        state.metadata["angle_degrees"] = self.angle_degrees
        state.metadata["pivot"] = self.pivot.copy()
        state.metadata["axis"] = self.axis.copy()
        state.pivot = self.pivot.copy()
        state.reference_axis = self.axis.copy()
        matrix = rotation_matrix(self.angle_degrees, self.pivot, self.axis)
        state.set_incremental(matrix)
        state.enable_preview(matrix)

    def _angle_between(self, start: Vector3, current: Vector3) -> float:
        """Return signed XY angle between reference and current points."""

        start_vector = start - self.pivot
        current_vector = current - self.pivot
        start_angle = atan2(start_vector.y, start_vector.x)
        current_angle = atan2(current_vector.y, current_vector.x)
        return degrees(current_angle - start_angle)
