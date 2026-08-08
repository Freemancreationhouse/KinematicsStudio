from __future__ import annotations

import math
import re
from typing import Any


class RotateNumericInput:
    """Parses unit-aware rotate input without UI dependencies."""

    def angle_from_values(
        self,
        current_angle: float,
        *,
        degrees: float | str | None = None,
        radians: float | str | None = None,
        relative_angle: float | str | None = None,
        absolute_angle: float | str | None = None,
        clockwise: bool = False,
        counter_clockwise: bool = False,
    ) -> float:
        """Return the rotation angle represented by numeric input values."""

        angle = float(current_angle)
        if absolute_angle is not None:
            angle = angle_value(absolute_angle)
        if degrees is not None:
            angle = angle_value(degrees)
        if radians is not None:
            angle = math.degrees(float(radians))
        if relative_angle is not None:
            angle = float(current_angle) + angle_value(relative_angle)
        if clockwise:
            angle = -abs(angle)
        if counter_clockwise:
            angle = abs(angle)
        return angle


def angle_value(value: Any) -> float:
    """Return a numeric angle in degrees from common input formats."""

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value or "").strip().lower()
    match = re.fullmatch(r"([-+]?\d+(?:\.\d+)?)\s*([a-z°]*)", text)
    if match is None:
        return float(text)

    number = float(match.group(1))
    unit = match.group(2)
    if unit in ("rad", "radian", "radians"):
        return math.degrees(number)
    return number
