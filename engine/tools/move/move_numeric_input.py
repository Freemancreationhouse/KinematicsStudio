from __future__ import annotations

import re
from typing import Any

from engine.geometry import Vector3

from engine.tools.move.move_context import vector3


class MoveNumericInput:
    """Parses unit-aware move input without UI dependencies."""

    def delta_from_values(
        self,
        current_delta: Vector3,
        start: Vector3,
        *,
        x: float | str | None = None,
        y: float | str | None = None,
        z: float | str | None = None,
        delta_x: float | str | None = None,
        delta_y: float | str | None = None,
        delta_z: float | str | None = None,
        distance: float | str | None = None,
        absolute_position: Vector3 | None = None,
        relative_position: Vector3 | None = None,
    ) -> Vector3:
        """Return the move delta represented by numeric input values."""

        if absolute_position is not None:
            return vector3(absolute_position) - start
        if relative_position is not None:
            return vector3(relative_position)

        delta = current_delta.copy()
        if x is not None:
            delta.x = unit_value(x)
        if y is not None:
            delta.y = unit_value(y)
        if z is not None:
            delta.z = unit_value(z)
        if delta_x is not None:
            delta.x = unit_value(delta_x)
        if delta_y is not None:
            delta.y = unit_value(delta_y)
        if delta_z is not None:
            delta.z = unit_value(delta_z)
        if distance is not None:
            direction = delta.normalized()
            if direction.length_squared() == 0.0:
                direction = Vector3(1.0, 0.0, 0.0)
            delta = direction * unit_value(distance)
        return delta


def unit_value(value: Any) -> float:
    """Return a numeric distance from common unit-aware input."""

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value or "").strip().lower()
    match = re.fullmatch(r"([-+]?\d+(?:\.\d+)?)\s*([a-z]*)", text)
    if match is None:
        return float(text)

    number = float(match.group(1))
    unit = match.group(2)
    factors = {
        "": 1.0,
        "mm": 1.0,
        "millimeter": 1.0,
        "millimeters": 1.0,
        "cm": 10.0,
        "centimeter": 10.0,
        "centimeters": 10.0,
        "m": 1000.0,
        "meter": 1000.0,
        "meters": 1000.0,
        "in": 25.4,
        "inch": 25.4,
        "inches": 25.4,
        "ft": 304.8,
        "foot": 304.8,
        "feet": 304.8,
    }
    return number * factors.get(unit, 1.0)
