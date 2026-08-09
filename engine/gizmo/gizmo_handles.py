from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from engine.geometry import Vector3


class GizmoType(str, Enum):
    """Supported professional transform gizmo types."""

    MOVE = "move"
    ROTATE = "rotate"
    SCALE = "scale"
    UNIVERSAL = "universal"


class GizmoHandleKind(str, Enum):
    """Supported transform gizmo handle categories."""

    MOVE_AXIS = "move_axis"
    MOVE_PLANE = "move_plane"
    MOVE_CENTER = "move_center"
    ROTATE_RING = "rotate_ring"
    SCALE_AXIS = "scale_axis"
    SCALE_PLANE = "scale_plane"
    SCALE_UNIFORM = "scale_uniform"


class GizmoAxis(str, Enum):
    """Supported transform axes."""

    X = "x"
    Y = "y"
    Z = "z"
    SCREEN = "screen"
    FREE = "free"


class GizmoPlane(str, Enum):
    """Supported transform planes."""

    XY = "xy"
    XZ = "xz"
    YZ = "yz"


@dataclass
class GizmoHandle:
    """Interactive handle metadata for a transform gizmo."""

    handle_id: str
    kind: GizmoHandleKind
    label: str
    axis: GizmoAxis | None = None
    plane: GizmoPlane | None = None
    direction: Vector3 = field(default_factory=Vector3)
    color: tuple[int, int, int] = (210, 210, 210)
    screen_size: float = 1.0
    enabled: bool = True
    visible: bool = True
    hovered: bool = False
    active: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe handle metadata for viewport presenters."""

        return {
            "handle_id": self.handle_id,
            "kind": self.kind.value,
            "label": self.label,
            "axis": self.axis.value if self.axis else "",
            "plane": self.plane.value if self.plane else "",
            "direction": self.direction.to_tuple(),
            "color": self.color,
            "screen_size": self.screen_size,
            "enabled": self.enabled,
            "visible": self.visible,
            "hovered": self.hovered,
            "active": self.active,
            "metadata": dict(self.metadata),
        }


def standard_handles(gizmo_type: GizmoType | str) -> tuple[GizmoHandle, ...]:
    """Return the standard handle set for a gizmo type."""

    resolved = _gizmo_type(gizmo_type)
    handles: list[GizmoHandle] = []

    if resolved in {GizmoType.MOVE, GizmoType.UNIVERSAL}:
        handles.extend(_move_handles())
    if resolved in {GizmoType.ROTATE, GizmoType.UNIVERSAL}:
        handles.extend(_rotate_handles())
    if resolved in {GizmoType.SCALE, GizmoType.UNIVERSAL}:
        handles.extend(_scale_handles())

    return tuple(handles)


def _move_handles() -> list[GizmoHandle]:
    """Return standard move handles."""

    return [
        GizmoHandle(
            "move_x",
            GizmoHandleKind.MOVE_AXIS,
            "X Axis Arrow",
            axis=GizmoAxis.X,
            direction=Vector3(1.0, 0.0, 0.0),
            color=(235, 78, 78),
        ),
        GizmoHandle(
            "move_y",
            GizmoHandleKind.MOVE_AXIS,
            "Y Axis Arrow",
            axis=GizmoAxis.Y,
            direction=Vector3(0.0, 1.0, 0.0),
            color=(80, 200, 120),
        ),
        GizmoHandle(
            "move_z",
            GizmoHandleKind.MOVE_AXIS,
            "Z Axis Arrow",
            axis=GizmoAxis.Z,
            direction=Vector3(0.0, 0.0, 1.0),
            color=(82, 150, 245),
        ),
        GizmoHandle(
            "move_xy",
            GizmoHandleKind.MOVE_PLANE,
            "XY Plane Handle",
            plane=GizmoPlane.XY,
            color=(235, 215, 90),
        ),
        GizmoHandle(
            "move_xz",
            GizmoHandleKind.MOVE_PLANE,
            "XZ Plane Handle",
            plane=GizmoPlane.XZ,
            color=(190, 105, 235),
        ),
        GizmoHandle(
            "move_yz",
            GizmoHandleKind.MOVE_PLANE,
            "YZ Plane Handle",
            plane=GizmoPlane.YZ,
            color=(85, 210, 210),
        ),
        GizmoHandle(
            "move_center",
            GizmoHandleKind.MOVE_CENTER,
            "Center Handle",
            color=(235, 235, 235),
        ),
    ]


def _rotate_handles() -> list[GizmoHandle]:
    """Return standard rotate handles."""

    return [
        GizmoHandle(
            "rotate_x",
            GizmoHandleKind.ROTATE_RING,
            "X Rotation Ring",
            axis=GizmoAxis.X,
            direction=Vector3(1.0, 0.0, 0.0),
            color=(235, 78, 78),
        ),
        GizmoHandle(
            "rotate_y",
            GizmoHandleKind.ROTATE_RING,
            "Y Rotation Ring",
            axis=GizmoAxis.Y,
            direction=Vector3(0.0, 1.0, 0.0),
            color=(80, 200, 120),
        ),
        GizmoHandle(
            "rotate_z",
            GizmoHandleKind.ROTATE_RING,
            "Z Rotation Ring",
            axis=GizmoAxis.Z,
            direction=Vector3(0.0, 0.0, 1.0),
            color=(82, 150, 245),
        ),
        GizmoHandle(
            "rotate_screen",
            GizmoHandleKind.ROTATE_RING,
            "Screen Rotation Ring",
            axis=GizmoAxis.SCREEN,
            color=(235, 235, 235),
        ),
        GizmoHandle(
            "rotate_free",
            GizmoHandleKind.ROTATE_RING,
            "Free Rotation Ring",
            axis=GizmoAxis.FREE,
            color=(240, 180, 80),
        ),
    ]


def _scale_handles() -> list[GizmoHandle]:
    """Return standard scale handles."""

    return [
        GizmoHandle(
            "scale_uniform",
            GizmoHandleKind.SCALE_UNIFORM,
            "Uniform Scale Handle",
            color=(235, 235, 235),
        ),
        GizmoHandle(
            "scale_x",
            GizmoHandleKind.SCALE_AXIS,
            "X Scale",
            axis=GizmoAxis.X,
            direction=Vector3(1.0, 0.0, 0.0),
            color=(235, 78, 78),
        ),
        GizmoHandle(
            "scale_y",
            GizmoHandleKind.SCALE_AXIS,
            "Y Scale",
            axis=GizmoAxis.Y,
            direction=Vector3(0.0, 1.0, 0.0),
            color=(80, 200, 120),
        ),
        GizmoHandle(
            "scale_z",
            GizmoHandleKind.SCALE_AXIS,
            "Z Scale",
            axis=GizmoAxis.Z,
            direction=Vector3(0.0, 0.0, 1.0),
            color=(82, 150, 245),
        ),
        GizmoHandle(
            "scale_xy",
            GizmoHandleKind.SCALE_PLANE,
            "XY Scale",
            plane=GizmoPlane.XY,
            color=(235, 215, 90),
        ),
        GizmoHandle(
            "scale_xz",
            GizmoHandleKind.SCALE_PLANE,
            "XZ Scale",
            plane=GizmoPlane.XZ,
            color=(190, 105, 235),
        ),
        GizmoHandle(
            "scale_yz",
            GizmoHandleKind.SCALE_PLANE,
            "YZ Scale",
            plane=GizmoPlane.YZ,
            color=(85, 210, 210),
        ),
    ]


def _gizmo_type(value: GizmoType | str) -> GizmoType:
    """Return a GizmoType from enum or string input."""

    if isinstance(value, GizmoType):
        return value
    normalized = str(value).strip().lower()
    aliases = {
        "translate": GizmoType.MOVE,
        "translation": GizmoType.MOVE,
        "all": GizmoType.UNIVERSAL,
    }
    return aliases.get(normalized, GizmoType(normalized))
