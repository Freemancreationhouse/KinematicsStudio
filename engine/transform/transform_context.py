from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TransformContext:
    """Runtime context that exposes existing services to transform sessions."""

    workspace: Any
    selection_manager: Any | None = None
    geometry_kernel: Any | None = None
    feature_history: Any | None = None
    command_manager: Any | None = None
    actor: str = "human"
    design_intent_graph_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_workspace(
        cls,
        workspace: Any,
        *,
        actor: str = "human",
        design_intent_graph_id: str = "",
    ) -> "TransformContext":
        """Create a transform context from current workspace services."""

        history_manager = getattr(workspace, "history_manager", None)
        return cls(
            workspace=workspace,
            selection_manager=getattr(workspace, "selection", None),
            geometry_kernel=getattr(workspace, "geometry_kernel", None),
            feature_history=getattr(history_manager, "feature_history", None),
            command_manager=getattr(workspace, "command_manager", None),
            actor=actor,
            design_intent_graph_id=design_intent_graph_id,
        )
