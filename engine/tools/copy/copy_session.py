from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from engine.dynamic_input import DynamicInputFieldType, DynamicInputManager
from engine.geometry import Vector3
from engine.snapping import SnappingManager
from engine.transform import TransformManager, TransformTarget, targets_from_selection

from engine.tools.copy.copy_context import delta_changed, translation_matrix, vector3
from engine.tools.copy.copy_events import CopyEvents
from engine.tools.copy.copy_numeric_input import CopyNumericInput
from engine.tools.copy.copy_operation import CopyOperation
from engine.tools.copy.copy_preview import CopyPreview
from engine.tools.copy.copy_transaction import CopyTransaction


@dataclass
class CopySession:
    """Professional copy session backed by Transform, Snap and HUD systems."""

    workspace: Any
    entities: list[Any]
    base_point: Vector3
    transform_manager: TransformManager
    snapping_manager: SnappingManager | None = None
    dynamic_input_manager: DynamicInputManager | None = None
    actor: str = "human"
    design_intent_graph_id: str = ""
    session_id: str = field(default_factory=lambda: str(uuid4()))
    operation: CopyOperation = field(default_factory=CopyOperation)
    events: CopyEvents = field(default_factory=CopyEvents)
    preview: CopyPreview = field(init=False)
    framework_session: Any = field(init=False)
    dynamic_input_session: Any = field(init=False, default=None)
    delta: Vector3 = field(default_factory=Vector3)
    copies: int = 1
    spacing: float = 0.0
    active: bool = True
    numeric_input: CopyNumericInput = field(init=False)

    def __post_init__(self) -> None:
        """Begin Transform and Dynamic Input sessions."""

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
        self.preview = CopyPreview(self.entities)
        self.dynamic_input_manager = (
            self.dynamic_input_manager or DynamicInputManager()
        )
        self.numeric_input = CopyNumericInput(self.dynamic_input_manager)
        self.dynamic_input_session = self.dynamic_input_manager.start_session(
            workspace=self.workspace,
            tool_name="CopyTool",
            command_name="Copy",
            fields=(
                DynamicInputFieldType.DELTA_X,
                DynamicInputFieldType.DELTA_Y,
                DynamicInputFieldType.DELTA_Z,
                DynamicInputFieldType.DISTANCE,
                DynamicInputFieldType.COPIES,
                DynamicInputFieldType.SPACING,
            ),
        )
        self.events.emit("CopyStarted", self.session_id, {"target_count": len(targets)})

    def update_to(self, point: Vector3) -> None:
        """Update preview from a world point, using snapping when available."""

        resolved = self._snap_point(point)
        self.update_delta(resolved - self.base_point)

    def update_delta(
        self,
        delta: Vector3,
        *,
        copies: int | None = None,
        spacing: float | None = None,
    ) -> None:
        """Update preview from an offset vector."""

        if not self.active:
            return
        self.delta = vector3(delta)
        if copies is not None:
            self.copies = max(1, int(copies))
        if spacing is not None:
            self.spacing = float(spacing)
        self.framework_session.state.metadata["delta"] = self.delta
        self.framework_session.state.metadata["copies"] = self.copies
        self.framework_session.state.metadata["spacing"] = self.spacing
        self.framework_session.state.set_incremental(translation_matrix(self.delta))
        self.framework_session.state.enable_preview(translation_matrix(self.delta))
        self.preview.update(self.delta, copies=self.copies, spacing=self.spacing)
        if self.dynamic_input_session is not None:
            self.dynamic_input_manager.update_cursor(self.base_point + self.delta)
        self.events.emit(
            "CopyUpdated",
            self.session_id,
            {"delta": self.delta, "copies": self.copies, "spacing": self.spacing},
        )

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
        copies: int | str | None = None,
        spacing: float | str | None = None,
        relative_offset: Vector3 | None = None,
        absolute_offset: Vector3 | None = None,
    ) -> None:
        """Update preview from unit-aware Dynamic Input values."""

        delta = self.numeric_input.delta_from_values(
            self.delta,
            self.base_point,
            x=x,
            y=y,
            z=z,
            delta_x=delta_x,
            delta_y=delta_y,
            delta_z=delta_z,
            distance=distance,
            relative_offset=relative_offset,
            absolute_offset=absolute_offset,
        )
        count = self.numeric_input.count_from_value(copies, self.copies)
        parsed_spacing = self.numeric_input.spacing_from_value(spacing, self.spacing)
        self.update_delta(delta, copies=count, spacing=parsed_spacing)

    def commit(self) -> Any:
        """Commit the copy through CommandManager and clear preview."""

        if not self.active:
            return None
        self.preview.clear()
        if not delta_changed(self.delta):
            self._end_dynamic_input(committed=False)
            self.active = False
            self.events.emit("CopyFinished", self.session_id, {})
            return None
        transaction = CopyTransaction(
            context=self.framework_session.context,
            targets=self.framework_session.targets,
            state=self.framework_session.state,
            operation=self.operation,
        )
        transaction.capture_before()
        self.framework_session.transaction = transaction
        result = transaction.commit()
        self._end_dynamic_input(committed=True)
        self.transform_manager.events.emit(
            "CopySessionCommitted",
            self.framework_session.session_id,
            {"delta": self.delta, "copies": self.copies},
        )
        self.events.emit("CopyCommitted", self.session_id, {"delta": self.delta})
        self.events.emit("CopyFinished", self.session_id, {})
        self.active = False
        return result

    def cancel(self) -> None:
        """Cancel the copy session and clear transient preview state."""

        self.preview.clear()
        self.framework_session.cancel()
        self._end_dynamic_input(committed=False)
        self.transform_manager.events.emit(
            "CopySessionCancelled",
            self.framework_session.session_id,
            {},
        )
        self.events.emit("CopyCancelled", self.session_id, {})
        self.events.emit("CopyFinished", self.session_id, {})
        self.active = False

    def _snap_point(self, point: Vector3) -> Vector3:
        """Resolve destination through Professional Snapping when available."""

        if self.snapping_manager is None:
            return vector3(point)
        try:
            result = self.snapping_manager.snap(point, self.workspace)
        except (AttributeError, TypeError, ValueError):
            return vector3(point)
        return vector3(getattr(result, "point", point))

    def _end_dynamic_input(self, *, committed: bool) -> None:
        """End the Dynamic Input session without changing geometry."""

        if self.dynamic_input_manager is None or self.dynamic_input_session is None:
            return
        session_id = self.dynamic_input_session.session_id
        if committed:
            self.dynamic_input_manager.commit(session_id)
        else:
            self.dynamic_input_manager.cancel(session_id)
        self.dynamic_input_session = None
