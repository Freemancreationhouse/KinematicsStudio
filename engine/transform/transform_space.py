from __future__ import annotations

from enum import Enum


class TransformSpace(str, Enum):
    """Coordinate spaces supported by the transform framework."""

    WORLD = "World"
    LOCAL = "Local"
    PARENT = "Parent"
    CUSTOM = "Custom"
