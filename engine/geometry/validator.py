from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GeometryValidationResult:
    """Validation result returned by geometry framework validators."""

    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class GeometryValidator:
    """Validates framework contracts without performing geometry algorithms."""

    def validate_geometry(self, geometry: Any) -> GeometryValidationResult:
        """Validate basic geometry object identity and protocol support."""

        errors: list[str] = []
        warnings: list[str] = []
        if geometry is None:
            errors.append("Geometry object is required.")
        if geometry is not None and not hasattr(geometry, "bounding_box"):
            warnings.append("Geometry object does not expose bounding_box().")
        return GeometryValidationResult(not errors, tuple(errors), tuple(warnings))

    def validate_context(self, context: Any) -> GeometryValidationResult:
        """Validate that a context can route through existing architecture."""

        errors: list[str] = []
        warnings: list[str] = []
        if context is None:
            errors.append("GeometryContext is required.")
            return GeometryValidationResult(False, tuple(errors), tuple(warnings))
        if getattr(context, "workspace", None) is None:
            warnings.append("GeometryContext has no workspace.")
        if getattr(context, "command_manager", None) is None:
            warnings.append("GeometryContext has no command manager.")
        return GeometryValidationResult(not errors, tuple(errors), tuple(warnings))
