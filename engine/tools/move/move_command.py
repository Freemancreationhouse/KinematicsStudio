from __future__ import annotations

from typing import Any

from engine.commands.command import Command
from engine.features import FeatureMetadata
from engine.geometry import Vector3
from engine.transform import TransformSpace, TransformTarget

from engine.tools.move.move_context import vector3, vector_to_data


class MoveCommand(Command):
    """Undoable command that commits a move through the command system."""

    def __init__(
        self,
        workspace: Any,
        entities: list[Any],
        delta: Vector3,
        *,
        targets: tuple[TransformTarget, ...] = (),
        actor: str = "human",
        design_intent_graph_id: str = "",
    ) -> None:
        """Create a move command for selected transform targets."""

        self.workspace = workspace
        self.entities = list(entities)
        self.delta = vector3(delta)
        self.targets = tuple(targets)
        self.actor = actor
        self.design_intent_graph_id = design_intent_graph_id
        self.feature = None
        self._feature_recorded = False

    def execute(self) -> None:
        """Apply the move and record feature-history metadata once."""

        for entity in self.entities:
            move_entity(entity, self.delta)
        self._restore_selection()
        self._record_feature_history()

    def undo(self) -> None:
        """Undo the move and restore the moved selection."""

        inverse = Vector3(-self.delta.x, -self.delta.y, -self.delta.z)
        for entity in self.entities:
            move_entity(entity, inverse)
        self._restore_selection()

    def _restore_selection(self) -> None:
        """Restore command targets as the active selection."""

        selection = getattr(self.workspace, "selection", None)
        if selection is None:
            return
        select_many = getattr(selection, "select_many", None)
        if callable(select_many):
            select_many(self.entities, False)

    def _record_feature_history(self) -> None:
        """Record one feature-history entry for the committed move."""

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
                "operation": "Move",
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
            name="Move",
            feature_type="Transform.Move",
            parameters={
                "delta": vector_to_data(self.delta),
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


def move_entity(entity: Any, delta: Vector3) -> None:
    """Move an entity by a 3D delta using existing entity APIs."""

    if getattr(entity, "locked", False):
        return

    if getattr(entity, "is_3d", False):
        _move_3d_entity(entity, delta)
        return

    move = getattr(entity, "move", None)
    if callable(move):
        move(delta.x, delta.y)
        return

    _move_3d_entity(entity, delta)


def _move_3d_entity(entity: Any, delta: Vector3) -> None:
    """Move 3D transform metadata without touching rendering code."""

    if _move_vector_attribute(entity, "position", delta):
        return
    if _move_vector_attribute(entity, "origin", delta):
        return
    if _move_vector_pair(entity, "start", "end", delta):
        return
    if _move_vector_list(entity, "_points", delta):
        return

    transform_state = getattr(entity, "transform_state", None)
    set_transform_state = getattr(entity, "set_transform_state", None)
    if callable(transform_state) and callable(set_transform_state):
        state = transform_state()
        position = state.get("position3d", Vector3()) + delta
        set_transform_state(position=position)
        return

    position = getattr(entity, "position3d", None)
    if position is not None:
        entity.position3d = position + delta


def _move_vector_attribute(entity: Any, name: str, delta: Vector3) -> bool:
    """Move a Vector3-like entity attribute when present."""

    value = getattr(entity, name, None)
    if not _is_vector3_like(value):
        return False
    setattr(entity, name, value + delta)
    return True


def _move_vector_pair(
    entity: Any,
    first_name: str,
    second_name: str,
    delta: Vector3,
) -> bool:
    """Move two Vector3-like endpoint attributes when present."""

    first = getattr(entity, first_name, None)
    second = getattr(entity, second_name, None)
    if not (_is_vector3_like(first) and _is_vector3_like(second)):
        return False
    setattr(entity, first_name, first + delta)
    setattr(entity, second_name, second + delta)
    return True


def _move_vector_list(entity: Any, name: str, delta: Vector3) -> bool:
    """Move a list of Vector3-like points when present."""

    values = getattr(entity, name, None)
    if (
        not isinstance(values, list)
        or not all(_is_vector3_like(item) for item in values)
    ):
        return False
    setattr(entity, name, [item + delta for item in values])
    return True


def _is_vector3_like(value: Any) -> bool:
    """Return True for Vector3-like values."""

    return (
        hasattr(value, "x")
        and hasattr(value, "y")
        and hasattr(value, "z")
        and hasattr(value, "__add__")
    )
