from __future__ import annotations

from typing import Any

from engine.dynamic_input import DynamicInputManager
from engine.geometry import Vector3

from engine.tools.copy.copy_context import vector3


class CopyNumericInput:
    """Routes copy numeric values through Dynamic Input parsing."""

    def __init__(self, dynamic_input_manager: DynamicInputManager | None = None) -> None:
        """Create numeric input support for copy sessions."""

        self.dynamic_input_manager = dynamic_input_manager or DynamicInputManager()

    def delta_from_values(
        self,
        current_delta: Vector3,
        base_point: Vector3,
        *,
        x: float | str | None = None,
        y: float | str | None = None,
        z: float | str | None = None,
        delta_x: float | str | None = None,
        delta_y: float | str | None = None,
        delta_z: float | str | None = None,
        distance: float | str | None = None,
        relative_offset: Vector3 | None = None,
        absolute_offset: Vector3 | None = None,
    ) -> Vector3:
        """Return a copy offset represented by Dynamic Input values."""

        if absolute_offset is not None:
            return vector3(absolute_offset) - base_point
        if relative_offset is not None:
            return vector3(relative_offset)

        delta = current_delta.copy()
        if x is not None:
            delta.x = self._length(x)
        if y is not None:
            delta.y = self._length(y)
        if z is not None:
            delta.z = self._length(z)
        if delta_x is not None:
            delta.x = self._length(delta_x)
        if delta_y is not None:
            delta.y = self._length(delta_y)
        if delta_z is not None:
            delta.z = self._length(delta_z)
        if distance is not None:
            direction = delta.normalized()
            if direction.length_squared() == 0.0:
                direction = Vector3(1.0, 0.0, 0.0)
            delta = direction * self._length(distance)
        return delta

    def count_from_value(self, value: int | str | None, default: int = 1) -> int:
        """Return a copy count from Dynamic Input parsing."""

        if value is None:
            return max(1, int(default))
        parsed = self.dynamic_input_manager.convert_units(
            value,
            expected_dimension="count",
        )
        return max(1, int(parsed.value))

    def spacing_from_value(self, value: float | str | None, default: float = 0.0) -> float:
        """Return copy spacing from Dynamic Input parsing."""

        if value is None:
            return float(default)
        return self._length(value)

    def _length(self, value: Any) -> float:
        """Parse one length value using Dynamic Input."""

        if isinstance(value, (int, float)):
            return float(value)
        return self.dynamic_input_manager.convert_units(value).value
