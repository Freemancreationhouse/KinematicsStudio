from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TransformTarget:
    """Persistent transform target reference derived from selection."""

    entity: Any
    persistent_id: str
    topology_id: str = ""
    feature_id: str = ""
    selection_mode: str = "Object"
    layer_name: str = ""
    material_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_entity(
        cls,
        entity: Any,
        *,
        selection_mode: str = "Object",
    ) -> "TransformTarget":
        """Create a transform target from an entity-like object."""

        return cls(
            entity=entity,
            persistent_id=_read_text(
                entity,
                (
                    "persistent_topology_id",
                    "topology_id",
                    "persistent_id",
                    "id",
                    "name",
                ),
            ),
            topology_id=_read_text(
                entity,
                ("topology_id", "persistent_topology_id", "topology_ref"),
            ),
            feature_id=_read_text(entity, ("feature_id", "source_feature_id")),
            selection_mode=selection_mode,
            layer_name=_read_text(entity, ("layer_name", "layer")),
            material_id=_read_text(entity, ("material_id", "material")),
            metadata={
                "class": entity.__class__.__name__,
                "locked": bool(getattr(entity, "locked", False)),
                "suppressed": bool(getattr(entity, "suppressed", False)),
            },
        )

    @classmethod
    def from_selection_target(cls, target: Any) -> "TransformTarget":
        """Create a transform target from a SelectionTarget-like object."""

        entity = getattr(target, "entity", target)
        mode = getattr(target, "mode", "Object")
        mode_value = getattr(mode, "value", mode)
        return cls(
            entity=entity,
            persistent_id=str(getattr(target, "persistent_id", "") or ""),
            topology_id=str(getattr(target, "topology_id", "") or ""),
            feature_id=str(getattr(target, "feature_id", "") or ""),
            selection_mode=str(mode_value or "Object"),
            layer_name=str(getattr(target, "layer_name", "") or ""),
            material_id=str(getattr(target, "material_id", "") or ""),
            metadata=dict(getattr(target, "metadata", {}) or {}),
        )


def targets_from_selection(selection_manager: Any) -> tuple[TransformTarget, ...]:
    """Return transform targets from an existing selection manager."""

    targets = getattr(selection_manager, "targets", None)
    if callable(targets):
        return tuple(TransformTarget.from_selection_target(item) for item in targets())

    selected = getattr(selection_manager, "selected", [])
    if callable(selected):
        selected = selected()
    mode = getattr(selection_manager, "selection_mode", None)
    if callable(mode):
        mode = mode()
    mode_value = getattr(mode, "value", mode) or "Object"
    return tuple(
        TransformTarget.from_entity(entity, selection_mode=str(mode_value))
        for entity in list(selected or [])
    )


def _read_text(entity: Any, names: tuple[str, ...]) -> str:
    """Read the first available text-like attribute from an entity."""

    for name in names:
        value = getattr(entity, name, "")
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        if value is not None and str(value):
            return str(value)
    return ""
