from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GizmoSettings:
    """User-configurable transform gizmo settings."""

    enabled: bool = True
    screen_size: float = 120.0
    handle_pick_tolerance: float = 14.0
    show_on_selection: bool = True
    highlight_hovered_handle: bool = True
    highlight_active_handle: bool = True
    screen_size_invariant: bool = True
    dpi_scale: float = 1.0
    anti_aliasing: bool = True

    def normalized_size(self) -> float:
        """Return DPI-aware gizmo size."""

        return max(24.0, float(self.screen_size) * max(0.1, float(self.dpi_scale)))
