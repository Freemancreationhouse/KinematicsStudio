from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GizmoContext:
    """Dependency-injected services consumed by the transform gizmo."""

    workspace: Any = None
    selection_manager: Any = None
    transform_manager: Any = None
    snapping_manager: Any = None
    dynamic_input_manager: Any = None
    move_tool: Any = None
    rotate_tool: Any = None
    scale_tool: Any = None
    copy_tool: Any = None
    viewport_id: str = ""
    actor: str = "human"
    design_intent_graph_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_workspace(
        cls,
        workspace: Any,
        *,
        transform_manager: Any = None,
        snapping_manager: Any = None,
        dynamic_input_manager: Any = None,
        move_tool: Any = None,
        rotate_tool: Any = None,
        scale_tool: Any = None,
        copy_tool: Any = None,
        viewport_id: str = "",
        actor: str = "human",
        design_intent_graph_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> GizmoContext:
        """Create context by feature-detecting services on a workspace."""

        selection_manager = getattr(workspace, "selection", None)
        return cls(
            workspace=workspace,
            selection_manager=selection_manager,
            transform_manager=transform_manager
            or getattr(workspace, "transform_manager", None),
            snapping_manager=snapping_manager
            or getattr(workspace, "snapping_manager", None)
            or getattr(workspace, "snap_manager", None),
            dynamic_input_manager=dynamic_input_manager
            or getattr(workspace, "dynamic_input_manager", None),
            move_tool=move_tool,
            rotate_tool=rotate_tool,
            scale_tool=scale_tool,
            copy_tool=copy_tool,
            viewport_id=viewport_id,
            actor=actor,
            design_intent_graph_id=design_intent_graph_id,
            metadata=dict(metadata or {}),
        )

    def selected_entities(self) -> tuple[Any, ...]:
        """Return current selected entities without owning selection state."""

        selection = self.selection_manager
        if selection is None:
            return ()
        selected = getattr(selection, "selected", ())
        if callable(selected):
            selected = selected()
        return tuple(selected or ())
