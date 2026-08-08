from __future__ import annotations

from copy import deepcopy
from typing import Any

from engine.commands.command import Command
from engine.features import FeatureMetadata
from engine.geometry import Vector3
from engine.transform import TransformSpace, TransformTarget

from engine.tools.rotate.rotate_context import (
    angle_changed,
    axis_vector,
    rotate_point_2d,
    rotate_point_3d,
    rotation_matrix,
    rotation_vector,
    vector3,
    vector_to_data,
)


class RotateCommand(Command):
    """Undoable command that commits a rotate through the command system."""

    def __init__(
        self,
        workspace: Any,
        entities: list[Any],
        angle_degrees: float,
        *,
        pivot: Vector3 | None = None,
        axis: Any | None = None,
        targets: tuple[TransformTarget, ...] = (),
        actor: str = "human",
        design_intent_graph_id: str = "",
    ) -> None:
        """Create a rotate command for selected transform targets."""

        self.workspace = workspace
        self.entities = list(entities)
        self.angle_degrees = float(angle_degrees)
        self.pivot = vector3(pivot or Vector3())
        self.axis = axis_vector(axis)
        self.targets = tuple(targets)
        self.actor = actor
        self.design_intent_graph_id = design_intent_graph_id
        self.feature = None
        self._feature_recorded = False
        self._before: dict[int, dict[str, Any]] = {}
        self._after: dict[int, dict[str, Any]] = {}
        self._replacements: list[tuple[Any, list[Any]]] = []
        self._in_place_entities: list[Any] = []
        self._indexes: dict[int, int] = {}

    def execute(self) -> None:
        """Apply the rotation and record feature-history metadata once."""

        if not angle_changed(self.angle_degrees):
            return
        if not self._before:
            self._before = {
                id(entity): capture_entity_state(entity)
                for entity in self.entities
            }
            self._prepare_targets()
        self._apply_replacements()
        for entity in self._in_place_entities:
            rotate_entity(entity, self.angle_degrees, self.pivot, self.axis)
        self._after = {
            id(entity): capture_entity_state(entity)
            for entity in self._in_place_entities
        }
        self._restore_selection(self._current_entities())
        self._record_feature_history()

    def undo(self) -> None:
        """Undo the rotation and restore the rotated selection."""

        self._undo_replacements()
        for entity in self._in_place_entities:
            state = self._before.get(id(entity))
            if state is not None:
                restore_entity_state(entity, state)
        self._restore_selection(self.entities)

    def redo(self) -> None:
        """Redo the rotation without recording duplicate history."""

        if self._after:
            self._apply_replacements()
            for entity in self._in_place_entities:
                state = self._after.get(id(entity))
                if state is not None:
                    restore_entity_state(entity, state)
            self._restore_selection(self._current_entities())
            return
        self.execute()

    def _prepare_targets(self) -> None:
        """Classify entities into replacement and in-place rotate paths."""

        self._replacements.clear()
        self._in_place_entities.clear()
        for entity in self.entities:
            replacement = rotated_replacements(entity, self.pivot, self.angle_degrees)
            if replacement:
                self._replacements.append((entity, replacement))
            else:
                self._in_place_entities.append(entity)

    def _apply_replacements(self) -> None:
        """Replace supported 2D entities with rotated geometry."""

        entities = getattr(self.workspace, "entities", None)
        if entities is None:
            return

        for source, result in self._replacements:
            if source not in entities:
                continue
            index = entities.index(source)
            self._indexes.setdefault(id(source), index)
            entities.pop(index)
            assign = getattr(self.workspace, "assign_replacement_layer", None)
            if callable(assign):
                assign(source, result)
            for offset, entity in enumerate(result):
                entities.insert(index + offset, entity)

    def _undo_replacements(self) -> None:
        """Restore source entities replaced by rotated 2D geometry."""

        entities = getattr(self.workspace, "entities", None)
        if entities is None:
            return

        for source, result in reversed(self._replacements):
            for entity in list(result):
                if entity in entities:
                    entities.remove(entity)
            index = self._indexes.get(id(source), len(entities))
            if source not in entities:
                entities.insert(index, source)

    def _current_entities(self) -> list[Any]:
        """Return entities currently present after execute or redo."""

        current = list(self._in_place_entities)
        for source, result in self._replacements:
            current.extend(result or [source])
        return current

    def _restore_selection(self, entities: list[Any]) -> None:
        """Restore command targets as the active selection."""

        selection = getattr(self.workspace, "selection", None)
        if selection is None:
            return
        select_many = getattr(selection, "select_many", None)
        if callable(select_many):
            select_many(entities, False)

    def _record_feature_history(self) -> None:
        """Record one feature-history entry for the committed rotation."""

        if self._feature_recorded:
            return
        manager = getattr(self.workspace, "feature_manager", None)
        create_feature = getattr(manager, "create_feature", None)
        if not callable(create_feature):
            self._feature_recorded = True
            return

        metadata = FeatureMetadata(
            owner=self.actor,
            design_intent_graph_id=self.design_intent_graph_id,
            properties={
                "operation": "Rotate",
                "target_count": len(self.entities),
                "target_ids": [
                    target.persistent_id
                    for target in self.targets
                    if target.persistent_id
                ],
            },
        )
        if self.actor == "ai":
            metadata.mark_ai_owned(
                design_intent_graph_id=self.design_intent_graph_id,
            )

        self.feature = create_feature(
            name="Rotate",
            feature_type="Transform.Rotate",
            parameters={
                "angle_degrees": self.angle_degrees,
                "pivot": vector_to_data(self.pivot),
                "axis": vector_to_data(self.axis),
                "space": TransformSpace.WORLD.value,
                "target_ids": [
                    target.persistent_id
                    for target in self.targets
                    if target.persistent_id
                ],
            },
            metadata=metadata,
            parent_ids=[
                target.feature_id
                for target in self.targets
                if target.feature_id
            ],
        )
        self._feature_recorded = True


def rotate_entity(
    entity: Any,
    angle_degrees: float,
    pivot: Vector3,
    axis: Any | None = None,
) -> None:
    """Rotate an entity by angle using existing entity APIs."""

    if getattr(entity, "locked", False):
        return

    if getattr(entity, "is_3d", False):
        _rotate_3d_entity(entity, angle_degrees, pivot, axis)
        return

    _rotate_2d_entity(entity, angle_degrees, pivot)


def rotated_replacements(
    entity: Any,
    pivot: Vector3,
    angle_degrees: float,
) -> list[Any]:
    """Return existing 2D replacement geometry when supported."""

    if getattr(entity, "is_3d", False):
        return []

    try:
        from engine.geometry.rotate import rotate_entities

        replacements = rotate_entities(entity, pivot, angle_degrees)
    except (ImportError, AttributeError, TypeError, ValueError):
        return []

    return list(replacements or [])


def capture_entity_state(entity: Any) -> dict[str, Any]:
    """Capture editable entity state for undo, redo and preview rollback."""

    state: dict[str, Any] = {}
    for name, value in vars(entity).items():
        if name.startswith("_") or callable(value):
            continue
        state[name] = _copy_value(value)
    return state


def restore_entity_state(entity: Any, state: dict[str, Any]) -> None:
    """Restore a state captured by capture_entity_state."""

    for name, value in state.items():
        setattr(entity, name, _copy_value(value))


def _rotate_2d_entity(entity: Any, angle_degrees: float, pivot: Vector3) -> None:
    """Rotate supported 2D entity attributes in the XY plane."""

    if _rotate_vector_attribute(entity, "start", angle_degrees, pivot):
        _rotate_vector_attribute(entity, "end", angle_degrees, pivot)
        return
    if _rotate_vector_pair(entity, "p1", "p2", angle_degrees, pivot):
        return
    if _rotate_vector_attribute(entity, "center", angle_degrees, pivot):
        _increment_angle(entity, "rotation", angle_degrees)
        _increment_angle(entity, "start_angle", angle_degrees)
        _increment_angle(entity, "end_angle", angle_degrees)
        return
    if _rotate_vector_list(entity, "points", angle_degrees, pivot):
        return
    if _rotate_vector_list(entity, "control_points", angle_degrees, pivot):
        return
    if _rotate_vector_list(entity, "_points", angle_degrees, pivot):
        return


def _rotate_3d_entity(
    entity: Any,
    angle_degrees: float,
    pivot: Vector3,
    axis: Any | None,
) -> None:
    """Rotate 3D transform metadata without touching rendering code."""

    rotation = rotation_vector(angle_degrees, axis)
    transform_state = getattr(entity, "transform_state", None)
    set_transform_state = getattr(entity, "set_transform_state", None)
    if callable(transform_state) and callable(set_transform_state):
        state = transform_state()
        position = rotate_point_3d(
            state.get("position3d", getattr(entity, "position3d", Vector3())),
            pivot,
            angle_degrees,
            axis,
        )
        current_rotation = vector3(
            state.get("rotation3d", getattr(entity, "rotation3d", Vector3()))
        )
        set_transform_state(position=position, rotation=current_rotation + rotation)
        return

    if _rotate_vector_attribute(entity, "position3d", angle_degrees, pivot):
        current = vector3(getattr(entity, "rotation3d", Vector3()))
        setattr(entity, "rotation3d", current + rotation)
    transform = getattr(entity, "transform", None)
    if transform is not None:
        entity.transform = rotation_matrix(angle_degrees, pivot, axis) @ transform


def _rotate_vector_attribute(
    entity: Any,
    name: str,
    angle_degrees: float,
    pivot: Vector3,
) -> bool:
    """Rotate one vector-like attribute when present."""

    value = getattr(entity, name, None)
    if not _is_vector2_like(value):
        return False
    setattr(entity, name, rotate_point_2d(value, pivot, angle_degrees))
    return True


def _rotate_vector_pair(
    entity: Any,
    first_name: str,
    second_name: str,
    angle_degrees: float,
    pivot: Vector3,
) -> bool:
    """Rotate two vector-like endpoint attributes when present."""

    first = getattr(entity, first_name, None)
    second = getattr(entity, second_name, None)
    if not (_is_vector2_like(first) and _is_vector2_like(second)):
        return False
    setattr(entity, first_name, rotate_point_2d(first, pivot, angle_degrees))
    setattr(entity, second_name, rotate_point_2d(second, pivot, angle_degrees))
    return True


def _rotate_vector_list(
    entity: Any,
    name: str,
    angle_degrees: float,
    pivot: Vector3,
) -> bool:
    """Rotate a vector-like point list when present."""

    values = getattr(entity, name, None)
    if callable(values):
        return False
    if (
        not isinstance(values, list)
        or not all(_is_vector2_like(item) for item in values)
    ):
        return False
    setattr(entity, name, [rotate_point_2d(item, pivot, angle_degrees) for item in values])
    return True


def _increment_angle(entity: Any, name: str, angle_degrees: float) -> None:
    """Increment a numeric angle attribute when present."""

    value = getattr(entity, name, None)
    if isinstance(value, (int, float)):
        setattr(entity, name, value + angle_degrees)


def _is_vector2_like(value: Any) -> bool:
    """Return True for Vector2-like or Vector3-like values."""

    return hasattr(value, "x") and hasattr(value, "y")


def _copy_value(value: Any) -> Any:
    """Return a detached copy of a value when possible."""

    copy_method = getattr(value, "copy", None)
    if callable(copy_method):
        return copy_method()
    return deepcopy(value)
