from __future__ import annotations

from enum import Enum


class TransformAxis(str, Enum):
    """Transform axis identifiers used by future transform tools."""

    X = "X"
    Y = "Y"
    Z = "Z"
    CUSTOM = "Custom"
