from __future__ import annotations

from engine.tools.scale import (
    ScaleCommand,
    ScaleContext,
    ScaleEvent,
    ScaleEvents,
    ScaleNumericInput,
    ScaleOperation,
    ScalePreview,
    ScaleSession,
    ScaleTool,
    ScaleTransaction,
    capture_entity_state,
    constrain_scale,
    point_to_vector3,
    restore_entity_state,
    scale_changed,
    scale_entity,
    scale_matrix,
    scale_point_2d,
    scale_point_3d,
    scale_value,
    scale_vector,
    scaled_replacements,
    vector_to_data,
)

_capture_entity_state = capture_entity_state
_constrain_scale = constrain_scale
_point_to_vector3 = point_to_vector3
_restore_entity_state = restore_entity_state
_scale_changed = scale_changed
_scale_entity = scale_entity
_scale_matrix = scale_matrix
_scale_point_2d = scale_point_2d
_scale_point_3d = scale_point_3d
_scale_value = scale_value
_scale_vector = scale_vector
_scaled_replacements = scaled_replacements
_vector_to_data = vector_to_data

__all__ = [
    "ScaleCommand",
    "ScaleContext",
    "ScaleEvent",
    "ScaleEvents",
    "ScaleNumericInput",
    "ScaleOperation",
    "ScalePreview",
    "ScaleSession",
    "ScaleTool",
    "ScaleTransaction",
    "capture_entity_state",
    "constrain_scale",
    "point_to_vector3",
    "restore_entity_state",
    "scale_changed",
    "scale_entity",
    "scale_matrix",
    "scale_point_2d",
    "scale_point_3d",
    "scale_value",
    "scale_vector",
    "scaled_replacements",
    "vector_to_data",
    "_capture_entity_state",
    "_constrain_scale",
    "_point_to_vector3",
    "_restore_entity_state",
    "_scale_changed",
    "_scale_entity",
    "_scale_matrix",
    "_scale_point_2d",
    "_scale_point_3d",
    "_scale_value",
    "_scale_vector",
    "_scaled_replacements",
    "_vector_to_data",
]
