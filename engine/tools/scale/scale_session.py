from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from engine.geometry import Vector3
from engine.transform import TransformManager, TransformTarget, targets_from_selection

from engine.tools.scale.scale_context import (
    point_to_vector3,
    scale_changed,
    scale_matrix,
    scale_vector,
)
from engine.tools.scale.scale_events import ScaleEvents
from engine.tools.scale.scale_numeric_input import ScaleNumericInput
from engine.tools.scale.scale_operation import ScaleOperation
from engine.tools.scale.scale_preview import ScalePreview
from engine.tools.scale.scale_transaction import ScaleTransaction


@dataclass
class ScaleSession:
    """Professional scale session backed by the Transform Framework."""

    workspace: Any
    entities: list[Any]
    pivot: Vector3
    transform_manager: TransformManager
    reference: Vector3 | None = None
    mode: str = "Uniform"
    actor: str = "human"
    design_intent_graph_id: str = ""
    session_id: str = field(default_factory=lambda: str(uuid4()))
    operation: ScaleOperation = field(default_factory=ScaleOperation)
    events: ScaleEvents = field(default_factory=ScaleEvents)
    preview: ScalePreview = field(init=False)
    framework_session: Any = field(init=False)
    factors: Vector3 = field(default_factory=lambda: Vector3(1.0, 1.0, 1.0))
    active: bool = True
    numeric_input: ScaleNumericInput = field(default_factory=ScaleNumericInput)

    def __post_init__(self) -> None:
        """Begin the underlying transform framework session."""

        self.pivot = point_to_vector3(self.pivot)
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
        self.preview = ScalePreview(self.entities, self.pivot)
        self._sync_state()
        self.events.emit("ScaleStarted", self.session_id, {"target_count": len(targets)})

    def update_to(self, point: Any) -> None:
        """Update preview from a world point."""

        target = point_to_vector3(point)
        if self.reference is None:
            self.reference = target
            return
        reference_distance = self.pivot.distance_to(self.reference)
        current_distance = self.pivot.distance_to(target)
        factor = 1.0 if reference_distance <= 1e-9 else current_distance / reference_distance
        self.update_factors(Vector3(factor, factor, factor))

    def update_factors(self, factors: Vector3) -> None:
        """Update preview from scale factors."""

        if not self.active:
            return
        self.factors = scale_vector(factors)
        self._sync_state()
        self.preview.update(self.factors)
        self.events.emit("ScaleUpdated", self.session_id, {"factors": self.factors})

    def set_numeric_input(
        self,
        *,
        factor: float | str | None = None,
        percentage: float | str | None = None,
        absolute_size: float | str | Vector3 | None = None,
        relative_scale: float | str | Vector3 | None = None,
        x: float | str | None = None,
        y: float | str | None = None,
        z: float | str | None = None,
        xy: float | str | None = None,
        xz: float | str | None = None,
        yz: float | str | None = None,
    ) -> None:
        """Update preview from numeric scale input values."""

        factors = self.numeric_input.factors_from_values(
            self.factors,
            factor=factor,
            percentage=percentage,
            absolute_size=absolute_size,
            relative_scale=relative_scale,
            x=x,
            y=y,
            z=z,
            xy=xy,
            xz=xz,
            yz=yz,
        )
        self.update_factors(factors)

    def commit(self) -> Any:
        """Commit the scale through CommandManager and clear preview."""

        if not self.active:
            return None
        self.preview.clear()
        if not scale_changed(self.factors):
            self.active = False
            self.events.emit("ScaleFinished", self.session_id, {})
            return None
        transaction = ScaleTransaction(
            context=self.framework_session.context,
            targets=self.framework_session.targets,
            state=self.framework_session.state,
            operation=self.operation,
        )
        transaction.capture_before()
        self.framework_session.transaction = transaction
        result = transaction.commit()
        self.transform_manager.events.emit(
            "ScaleSessionCommitted",
            self.framework_session.session_id,
            {"factors": self.factors},
        )
        self.events.emit("ScaleCommitted", self.session_id, {"factors": self.factors})
        self.events.emit("ScaleFinished", self.session_id, {})
        self.active = False
        return result

    def cancel(self) -> None:
        """Cancel the scale session and restore previewed geometry."""

        self.preview.clear()
        self.framework_session.cancel()
        self.transform_manager.events.emit(
            "ScaleSessionCancelled",
            self.framework_session.session_id,
            {},
        )
        self.events.emit("ScaleCancelled", self.session_id, {})
        self.events.emit("ScaleFinished", self.session_id, {})
        self.active = False

    def draw_preview(self, painter: Any) -> None:
        """Draw non-mutating replacement preview geometry."""

        self.preview.draw(painter)

    def _sync_state(self) -> None:
        """Synchronize scale metadata into the transform state."""

        state = self.framework_session.state
        state.metadata["factors"] = self.factors.copy()
        state.metadata["pivot"] = self.pivot.copy()
        state.metadata["mode"] = self.mode
        state.pivot = self.pivot.copy()
        matrix = scale_matrix(self.factors, self.pivot)
        state.set_incremental(matrix)
        state.enable_preview(matrix)
