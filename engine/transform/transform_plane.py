from __future__ import annotations

from enum import Enum


class TransformPlane(str, Enum):
    """Reference planes used by constrained transform sessions."""

    XY = "XY"
    YZ = "YZ"
    XZ = "XZ"
    CUSTOM = "Custom"
