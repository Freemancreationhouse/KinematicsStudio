from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.geometry import GeometryContext, GeometryKernel


@dataclass
class EditingContext:
    """Editing context bound to existing workspace and geometry services."""

    workspace: Any
    geometry_kernel: GeometryKernel
    command_manager: Any | None = None
    selection_manager: Any | None = None
    actor: str = "human"
    design_intent_graph_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_workspace(
        cls,
        workspace: Any,
        geometry_kernel: GeometryKernel,
        *,
        actor: str = "human",
        design_intent_graph_id: str = "",
    ) -> "EditingContext":
        """Create an editing context from existing workspace services."""

        return cls(
            workspace=workspace,
            geometry_kernel=geometry_kernel,
            command_manager=getattr(workspace, "command_manager", None),
            selection_manager=getattr(workspace, "selection", None),
            actor=actor,
            design_intent_graph_id=design_intent_graph_id,
        )

    def geometry_context(self) -> GeometryContext:
        """Return a GeometryContext view of this editing context."""

        return GeometryContext.from_workspace(
            self.workspace,
            actor=self.actor,
            design_intent_graph_id=self.design_intent_graph_id,
        )
