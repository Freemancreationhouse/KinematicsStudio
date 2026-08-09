from __future__ import annotations

import re
from dataclasses import dataclass

from engine.dynamic_input.expression_parser import ExpressionParser


class DynamicInputUnitError(ValueError):
    """Raised when unit-aware dynamic input cannot be parsed."""


@dataclass(frozen=True)
class ParsedUnitValue:
    """Unit-aware numeric value normalized for CAD operations."""

    raw_text: str
    expression: str
    value: float
    unit: str
    dimension: str


class UnitParser:
    """Parse CAD numeric input with length, angle, and scalar units."""

    _length_units: dict[str, float] = {
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
        "km": 1000000.0,
        "kilometer": 1000000.0,
        "kilometers": 1000000.0,
        "in": 25.4,
        "inch": 25.4,
        "inches": 25.4,
        "ft": 304.8,
        "foot": 304.8,
        "feet": 304.8,
    }
    _angle_units: set[str] = {"deg", "degree", "degrees", "°"}
    _scalar_units: set[str] = {"", "%", "x"}

    def __init__(self, expression_parser: ExpressionParser | None = None) -> None:
        """Create a parser using a safe expression evaluator."""

        self.expression_parser = expression_parser or ExpressionParser()

    def parse(
        self,
        text: str | int | float,
        *,
        expected_dimension: str = "length",
    ) -> ParsedUnitValue:
        """Parse text into a normalized unit value."""

        if isinstance(text, (int, float)):
            return ParsedUnitValue(
                raw_text=str(text),
                expression=str(text),
                value=float(text),
                unit="",
                dimension=expected_dimension,
            )

        raw_text = str(text).strip()
        if not raw_text:
            raise DynamicInputUnitError("Input is empty.")

        expression, unit = self._split_expression_and_unit(raw_text)
        try:
            expression_result = self.expression_parser.parse(expression)
        except ValueError as exc:
            raise DynamicInputUnitError(str(exc)) from exc

        dimension = self._dimension_for_unit(unit, expected_dimension)
        value = self._normalize(expression_result.value, unit, dimension)
        return ParsedUnitValue(
            raw_text=raw_text,
            expression=expression_result.expression,
            value=value,
            unit=unit,
            dimension=dimension,
        )

    def convert(self, value: float, from_unit: str, to_unit: str = "mm") -> float:
        """Convert a length value between supported units."""

        source = self._length_units.get(from_unit.strip().lower())
        target = self._length_units.get(to_unit.strip().lower())
        if source is None or target is None:
            raise DynamicInputUnitError("Unsupported length unit.")
        return float(value) * source / target

    def _split_expression_and_unit(self, text: str) -> tuple[str, str]:
        """Split an input string into arithmetic expression and suffix unit."""

        normalized = text.strip().replace("−", "-")
        match = re.fullmatch(r"(.+?)([a-zA-Z°%]*)", normalized)
        if match is None:
            raise DynamicInputUnitError("Invalid unit input.")

        expression = match.group(1).strip()
        unit = match.group(2).strip().lower()
        if not expression:
            raise DynamicInputUnitError("Input expression is empty.")
        return expression, unit

    def _dimension_for_unit(self, unit: str, expected_dimension: str) -> str:
        """Resolve the physical dimension represented by a unit suffix."""

        if unit in self._angle_units:
            return "angle"
        if unit in self._length_units:
            return expected_dimension if expected_dimension != "angle" else "angle"
        if unit in self._scalar_units:
            return expected_dimension
        raise DynamicInputUnitError(f"Unsupported unit: {unit}")

    def _normalize(self, value: float, unit: str, dimension: str) -> float:
        """Normalize a parsed value to internal CAD units."""

        if dimension == "angle":
            return float(value)
        if dimension == "scale":
            return float(value) / 100.0 if unit == "%" else float(value)
        if dimension in {"count", "index"}:
            return float(int(round(value)))
        factor = self._length_units.get(unit, 1.0)
        return float(value) * factor
