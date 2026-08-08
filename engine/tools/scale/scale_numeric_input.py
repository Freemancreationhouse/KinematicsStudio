from __future__ import annotations

import re
from typing import Any

from engine.geometry import Vector3

from engine.tools.scale.scale_context import scale_vector


class ScaleNumericInput:
    """Parses reusable scale input without UI dependencies."""

    def factors_from_values(
        self,
        current_factors: Vector3,
        *,
        factor: float | str | None = None,
        percentage: float | str | None = None,
        absolute_size: float | str | Vector3 | None = None,
        relative_scale: float | str | Vector3 | None = None,
        x: float | str | None = None,
        y: float | str | None = None,
        z: float | str | None = None,
        xy: float | str | None = None,
        xz: float | str | None = None,
        yz: float | str | None = None,
    ) -> Vector3:
        """Return scale factors represented by numeric input values."""

        factors = scale_vector(current_factors)
        if factor is not None:
            uniform = scale_value(factor)
            factors = Vector3(uniform, uniform, uniform)
        if percentage is not None:
            uniform = scale_value(percentage) / 100.0
            factors = Vector3(uniform, uniform, uniform)
        if relative_scale is not None:
            factors = scale_vector(relative_scale)
        if absolute_size is not None:
            factors = scale_vector(absolute_size)
        if x is not None:
            factors.x = scale_value(x)
        if y is not None:
            factors.y = scale_value(y)
        if z is not None:
            factors.z = scale_value(z)
        if xy is not None:
            value = scale_value(xy)
            factors.x = value
            factors.y = value
        if xz is not None:
            value = scale_value(xz)
            factors.x = value
            factors.z = value
        if yz is not None:
            value = scale_value(yz)
            factors.y = value
            factors.z = value
        return factors


def scale_value(value: Any) -> float:
    """Return a numeric scale value from factor or percentage text."""

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value or "").strip().lower()
    match = re.fullmatch(r"([-+]?\d+(?:\.\d+)?)\s*(%|percent|percentage)?", text)
    if match is None:
        return float(text)

    number = float(match.group(1))
    unit = match.group(2)
    if unit in ("%", "percent", "percentage"):
        return number / 100.0
    return number
