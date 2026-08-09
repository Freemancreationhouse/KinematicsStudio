from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.gizmo.gizmo_state import GizmoState


@dataclass(frozen=True)
class GizmoRenderPacket:
    """Renderer-facing metadata for drawing a transform gizmo."""

    visible: bool
    origin: tuple[float, float, float]
    handles: tuple[dict[str, Any], ...]
    screen_size: float
    anti_aliasing: bool
    metadata: dict[str, Any]


class GizmoRenderer:
    """Produces renderer metadata without owning rendering code."""

    def packet(
        self,
        state: GizmoState,
        *,
        screen_size: float = 120.0,
        anti_aliasing: bool = True,
    ) -> GizmoRenderPacket:
        """Return a draw packet for the current gizmo state."""

        return GizmoRenderPacket(
            visible=state.visible,
            origin=state.origin.to_tuple(),
            handles=tuple(handle.to_dict() for handle in state.handles.values()),
            screen_size=float(screen_size),
            anti_aliasing=bool(anti_aliasing),
            metadata=state.snapshot(),
        )
