from __future__ import annotations

from typing import Any

from engine.dynamic_input.dynamic_input_fields import (
    DynamicInputField,
    DynamicInputFieldType,
)
from engine.dynamic_input.expression_parser import ExpressionParser, ExpressionResult
from engine.dynamic_input.unit_parser import ParsedUnitValue, UnitParser


class DynamicInputParser:
    """Parses field-specific HUD values into normalized CAD numbers."""

    _angle_fields = {DynamicInputFieldType.ANGLE}
    _scale_fields = {DynamicInputFieldType.SCALE}
    _count_fields = {
        DynamicInputFieldType.COPIES,
        DynamicInputFieldType.ROWS,
        DynamicInputFieldType.COLUMNS,
    }
    _length_fields = {
        DynamicInputFieldType.DELTA_X,
        DynamicInputFieldType.DELTA_Y,
        DynamicInputFieldType.DELTA_Z,
        DynamicInputFieldType.DISTANCE,
        DynamicInputFieldType.RADIUS,
        DynamicInputFieldType.OFFSET,
        DynamicInputFieldType.SPACING,
    }

    def __init__(
        self,
        expression_parser: ExpressionParser | None = None,
        unit_parser: UnitParser | None = None,
    ) -> None:
        """Create a reusable dynamic input parser."""

        self.expression_parser = expression_parser or ExpressionParser()
        self.unit_parser = unit_parser or UnitParser(self.expression_parser)

    def parse_field(self, field: DynamicInputField, text: Any) -> ParsedUnitValue:
        """Parse text according to the expected field dimension."""

        dimension = self.dimension_for_field(field.field_type)
        result = self.unit_parser.parse(text, expected_dimension=dimension)
        field.set_text(str(text))
        field.set_value(result.value, unit=result.unit)
        return result

    def parse_expression(self, text: Any) -> ExpressionResult:
        """Parse a raw arithmetic expression."""

        return self.expression_parser.parse(text)

    def parse_unit(
        self,
        text: Any,
        *,
        expected_dimension: str = "length",
    ) -> ParsedUnitValue:
        """Parse unit-aware input."""

        return self.unit_parser.parse(text, expected_dimension=expected_dimension)

    def dimension_for_field(self, field: DynamicInputFieldType) -> str:
        """Return the expected dimension for a HUD field."""

        if field in self._angle_fields:
            return "angle"
        if field in self._scale_fields:
            return "scale"
        if field in self._count_fields:
            return "count"
        if field in self._length_fields:
            return "length"
        return "scalar"
