from __future__ import annotations

from copy import deepcopy
from typing import Any

from engine.commands.command import Command
from engine.features import FeatureMetadata
from engine.geometry import Vector3
from engine.transform import TransformSpace, TransformTarget

from engine.tools.scale.scale_context import (
    scale_changed,
    scale_matrix,
    scale_point_2d,
    scale_point_3d,
    scale_vector,
    vector_to_data,
)


class ScaleCommand(Command):
    """Undoable command that commits a scale through the command system."""

    def __init__(
        self,
        workspace: Any,
        entities: list[Any],
        factors: Vector3,
        *,
        pivot: Vector3 | None = None,
        mode: str | None = None,
        targets: tuple[TransformTarget, ...] = (),
        actor: str = "human",
        design_intent_graph_id: str = "",
    ) -> None:
        """Create a scale command for selected transform targets."""

        self.workspace = workspace
        self.entities = list(entities)
        self.factors = scale_vector(factors)
        self.pivot = scale_point_3d(pivot or Vector3(), Vector3(), Vector3(1.0, 1.0, 1.0))
        self.mode = str(mode or "Uniform")
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
        """Apply the scale and record feature-history metadata once."""

        if not scale_changed(self.factors):
            return
        if not self._before:
            self._before = {
                id(entity): capture_entity_state(entity)
                for entity in self.entities
            }
            self._prepare_targets()
        self._apply_replacements()
        for entity in self._in_place_entities:
            scale_entity(entity, self.factors, self.pivot)
        self._after = {
            id(entity): capture_entity_state(entity)
            for entity in self._in_place_entities
        }
        self._restore_selection(self._current_entities())
        self._record_feature_history()

    def undo(self) -> None:
        """Undo the scale and restore the scaled selection."""

        self._undo_replacements()
        for entity in self._in_place_entities:
            state = self._before.get(id(entity))
            if state is not None:
                restore_entity_state(entity, state)
        self._restore_selection(self.entities)

    def redo(self) -> None:
        """Redo the scale without recording duplicate history."""

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
        """Classify entities into replacement and in-place scale paths."""

        self._replacements.clear()
        self._in_place_entities.clear()
        for entity in self.entities:
            replacement = scaled_replacements(entity, self.pivot, self.factors)
            if replacement:
                self._replacements.append((entity, replacement))
            else:
                self._in_place_entities.append(entity)

    def _apply_replacements(self) -> None:
        """Replace supported 2D entities with scaled geometry."""

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
        """Restore source entities replaced by scaled 2D geometry."""

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
        """Record one feature-history entry for the committed scale."""

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
                "operation": "Scale",
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
            name="Scale",
            feature_type="Transform.Scale",
            parameters={
                "factors": vector_to_data(self.factors),
                "pivot": vector_to_data(self.pivot),
                "mode": self.mode,
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


def scale_entity(entity: Any, factors: Vector3, pivot: Vector3) -> None:
    """Scale an entity using existing entity APIs where available."""

    if getattr(entity, "locked", False):
        return

    if getattr(entity, "is_3d", False):
        _scale_3d_entity(entity, factors, pivot)
        return

    _scale_2d_entity(entity, factors, pivot)


def scaled_replacements(
    entity: Any,
    pivot: Vector3,
    factors: Vector3,
) -> list[Any]:
    """Return existing 2D replacement geometry when supported."""

    if getattr(entity, "is_3d", False):
        return []
    if abs(factors.x - factors.y) > 1e-9:
        return []

    try:
        from engine.geometry.scale import scale_entities

        replacements = scale_entities(entity, pivot, factors.x)
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


def _scale_2d_entity(entity: Any, factors: Vector3, pivot: Vector3) -> None:
    """Scale supported 2D entity attributes in the XY plane."""

    if _scale_vector_attribute(entity, "start", factors, pivot):
        _scale_vector_attribute(entity, "end", factors, pivot)
        return
    if _scale_vector_pair(entity, "p1", "p2", factors, pivot):
        return
    if _scale_vector_attribute(entity, "center", factors, pivot):
        _scale_radius(entity, "radius", factors)
        _scale_radius(entity, "radius_x", factors)
        _scale_radius(entity, "radius_y", factors)
        return
    if _scale_vector_list(entity, "points", factors, pivot):
        return
    if _scale_vector_list(entity, "control_points", factors, pivot):
        return
    if _scale_vector_list(entity, "_points", factors, pivot):
        return


def _scale_3d_entity(entity: Any, factors: Vector3, pivot: Vector3) -> None:
    """Scale 3D transform metadata without touching rendering code."""

    transform_state = getattr(entity, "transform_state", None)
    set_transform_state = getattr(entity, "set_transform_state", None)
    if callable(transform_state) and callable(set_transform_state):
        state = transform_state()
        position = scale_point_3d(
            state.get("position3d", getattr(entity, "position3d", Vector3())),
            pivot,
            factors,
        )
        current_scale = scale_vector(
            state.get("scale3d", getattr(entity, "scale3d", Vector3(1.0, 1.0, 1.0)))
        )
        set_transform_state(
            position=position,
            scale=Vector3(
                current_scale.x * factors.x,
                current_scale.y * factors.y,
                current_scale.z * factors.z,
            ),
        )
        return

    if _scale_vector_attribute(entity, "position3d", factors, pivot):
        current = scale_vector(getattr(entity, "scale3d", Vector3(1.0, 1.0, 1.0)))
        setattr(
            entity,
            "scale3d",
            Vector3(current.x * factors.x, current.y * factors.y, current.z * factors.z),
        )
    transform = getattr(entity, "transform", None)
    if transform is not None:
        entity.transform = scale_matrix(factors, pivot) @ transform


def _scale_vector_attribute(
    entity: Any,
    name: str,
    factors: Vector3,
    pivot: Vector3,
) -> bool:
    """Scale one vector-like attribute when present."""

    value = getattr(entity, name, None)
    if not _is_vector2_like(value):
        return False
    setattr(entity, name, scale_point_2d(value, pivot, factors))
    return True


def _scale_vector_pair(
    entity: Any,
    first_name: str,
    second_name: str,
    factors: Vector3,
    pivot: Vector3,
) -> bool:
    """Scale two vector-like endpoint attributes when present."""

    first = getattr(entity, first_name, None)
    second = getattr(entity, second_name, None)
    if not (_is_vector2_like(first) and _is_vector2_like(second)):
        return False
    setattr(entity, first_name, scale_point_2d(first, pivot, factors))
    setattr(entity, second_name, scale_point_2d(second, pivot, factors))
    return True


def _scale_vector_list(
    entity: Any,
    name: str,
    factors: Vector3,
    pivot: Vector3,
) -> bool:
    """Scale a vector-like point list when present."""

    values = getattr(entity, name, None)
    if callable(values):
        return False
    if (
        not isinstance(values, list)
        or not all(_is_vector2_like(item) for item in values)
    ):
        return False
    setattr(entity, name, [scale_point_2d(item, pivot, factors) for item in values])
    return True


def _scale_radius(entity: Any, name: str, factors: Vector3) -> None:
    """Scale a radius-like numeric attribute when present."""

    value = getattr(entity, name, None)
    if isinstance(value, (int, float)):
        setattr(entity, name, abs(value * max(abs(factors.x), abs(factors.y))))


def _is_vector2_like(value: Any) -> bool:
    """Return True for Vector2-like or Vector3-like values."""

    return hasattr(value, "x") and hasattr(value, "y")


def _copy_value(value: Any) -> Any:
    """Return a detached copy of a value when possible."""

    copy_method = getattr(value, "copy", None)
    if callable(copy_method):
        return copy_method()
    return deepcopy(value)
