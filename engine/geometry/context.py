from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class GeometryContext:
    """Workspace-scoped context for geometry framework operations."""

    workspace: Any | None = None
    command_manager: Any | None = None
    selection_manager: Any | None = None
    scene: Any | None = None
    actor: str = "human"
    design_intent_graph_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    context_id: str = field(default_factory=lambda: str(uuid4()))

    @classmethod
    def from_workspace(
        cls,
        workspace: Any,
        *,
        actor: str = "human",
        design_intent_graph_id: str = "",
    ) -> "GeometryContext":
        """Create a context by feature-detecting existing workspace services."""

        return cls(
            workspace=workspace,
            command_manager=getattr(workspace, "command_manager", None),
            selection_manager=getattr(workspace, "selection", None),
            scene=getattr(workspace, "scene", None),
            actor=actor,
            design_intent_graph_id=design_intent_graph_id,
        )

    def with_metadata(self, key: str, value: Any) -> "GeometryContext":
        """Attach metadata and return this context for fluent setup."""

        self.metadata[key] = value
        return self
