from __future__ import annotations

from copy import deepcopy
from typing import Any

from engine.commands.command import Command
from engine.features import FeatureMetadata
from engine.geometry import Vector3
from engine.transform import TransformSpace, TransformTarget

from engine.tools.copy.copy_context import vector3, vector_to_data
from engine.tools.move.move_command import move_entity


class CopyCommand(Command):
    """Undoable command that commits copied entities through CommandManager."""

    def __init__(
        self,
        workspace: Any,
        entities: list[Any],
        delta: Vector3,
        *,
        copies: int = 1,
        spacing: float = 0.0,
        targets: tuple[TransformTarget, ...] = (),
        actor: str = "human",
        design_intent_graph_id: str = "",
        associative: bool = False,
        reference_copy: bool = False,
    ) -> None:
        """Create a copy command for selected transform targets."""

        self.workspace = workspace
        self.entities = list(entities)
        self.delta = vector3(delta)
        self.copies = max(1, int(copies))
        self.spacing = float(spacing)
        self.targets = tuple(targets)
        self.actor = actor
        self.design_intent_graph_id = design_intent_graph_id
        self.associative = bool(associative)
        self.reference_copy = bool(reference_copy)
        self.feature = None
        self._feature_recorded = False
        self._created_entities: list[Any] = []

    def execute(self) -> None:
        """Create copies and record feature-history metadata once."""

        if not self._created_entities:
            self._created_entities = self._build_copies()
        self._add_created_entities()
        self._restore_selection(self._created_entities)
        self._record_feature_history()

    def undo(self) -> None:
        """Undo the copy by removing created entities."""

        entities = self._workspace_entities()
        for entity in list(self._created_entities):
            if entity in entities:
                entities.remove(entity)
        self._restore_selection(self.entities)

    def redo(self) -> None:
        """Redo the copy using the originally created entities."""

        self._add_created_entities()
        self._restore_selection(self._created_entities)

    def copied_entities(self) -> tuple[Any, ...]:
        """Return entities created by this command."""

        return tuple(self._created_entities)

    def _build_copies(self) -> list[Any]:
        """Create translated entity copies without adding them to the workspace."""

        copied: list[Any] = []
        for copy_index in range(1, self.copies + 1):
            offset = self._offset_for_index(copy_index)
            for entity in self.entities:
                duplicate = clone_entity(entity)
                if duplicate is None:
                    continue
                move_entity(duplicate, offset)
                copied.append(duplicate)
        return copied

    def _offset_for_index(self, copy_index: int) -> Vector3:
        """Return offset for one created copy."""

        if self.spacing == 0.0:
            return self.delta * copy_index
        direction = self.delta.normalized()
        if direction.length_squared() == 0.0:
            direction = Vector3(1.0, 0.0, 0.0)
        return direction * (self.spacing * copy_index)

    def _add_created_entities(self) -> None:
        """Add created copies to the workspace once."""

        entities = self._workspace_entities()
        for entity in self._created_entities:
            if entity in entities:
                continue
            assign = getattr(self.workspace, "assign_layer", None)
            if callable(assign):
                assign(entity)
            entities.append(entity)

    def _workspace_entities(self) -> list[Any]:
        """Return the mutable workspace entity collection."""

        entities = getattr(self.workspace, "entities", None)
        if callable(entities):
            entities = entities()
        if entities is None:
            raise RuntimeError("CopyCommand requires workspace entities.")
        return entities

    def _restore_selection(self, entities: list[Any]) -> None:
        """Restore command targets as the active selection."""

        selection = getattr(self.workspace, "selection", None)
        if selection is None:
            return
        select_many = getattr(selection, "select_many", None)
        if callable(select_many):
            select_many(entities, False)

    def _record_feature_history(self) -> None:
        """Record one feature-history entry for the committed copy."""

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
                "operation": "Copy",
                "source_count": len(self.entities),
                "created_count": len(self._created_entities),
                "copy_count": self.copies,
                "associative": self.associative,
                "reference_copy": self.reference_copy,
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
            name="Copy",
            feature_type="Transform.Copy",
            parameters={
                "delta": vector_to_data(self.delta),
                "copies": self.copies,
                "spacing": self.spacing,
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


def clone_entity(entity: Any) -> Any:
    """Clone an entity using existing clone APIs before deepcopy fallback."""

    if entity is None or getattr(entity, "locked", False):
        return None

    clone = getattr(entity, "clone", None)
    if callable(clone):
        try:
            return clone()
        except TypeError:
            return None

    try:
        duplicate = deepcopy(entity)
    except (TypeError, ValueError, AttributeError):
        return None

    _clear_selection_state(duplicate)
    return duplicate


def _clear_selection_state(entity: Any) -> None:
    """Ensure a cloned entity does not inherit transient selection state."""

    if hasattr(entity, "selected"):
        entity.selected = False
