from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DynamicInputContext:
    """Application context consumed by dynamic input sessions."""

    workspace: Any = None
    tool_name: str = ""
    command_name: str = ""
    selection_manager: Any = None
    snapping_manager: Any = None
    transform_manager: Any = None
    viewport_id: str = ""
    coordinate_space: str = "World"
    units: str = "mm"
    actor: str = "human"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_workspace(
        cls,
        workspace: Any,
        *,
        tool_name: str = "",
        command_name: str = "",
        snapping_manager: Any = None,
        transform_manager: Any = None,
        viewport_id: str = "",
        coordinate_space: str = "World",
        units: str = "mm",
        actor: str = "human",
        metadata: dict[str, Any] | None = None,
    ) -> DynamicInputContext:
        """Build context by feature-detecting services on a workspace."""

        selection_manager = getattr(workspace, "selection_manager", None)
        if selection_manager is None:
            selection_manager = getattr(workspace, "selection", None)

        return cls(
            workspace=workspace,
            tool_name=tool_name,
            command_name=command_name,
            selection_manager=selection_manager,
            snapping_manager=snapping_manager,
            transform_manager=transform_manager,
            viewport_id=viewport_id,
            coordinate_space=coordinate_space,
            units=units,
            actor=actor,
            metadata=dict(metadata or {}),
        )
