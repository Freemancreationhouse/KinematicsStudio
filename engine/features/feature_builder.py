from __future__ import annotations

from typing import Any

from engine.features.feature import Feature
from engine.features.feature_metadata import FeatureMetadata


class FeatureBuilder:
    """Builds feature records without executing geometry generation."""

    def build(
        self,
        *,
        name: str,
        feature_type: str,
        parameters: dict[str, Any] | None = None,
        metadata: FeatureMetadata | None = None,
        parent_ids: list[str] | None = None,
    ) -> Feature:
        """Create a feature record for later command-system execution."""

        if not name.strip():
            raise ValueError("Feature name must not be empty.")
        if not feature_type.strip():
            raise ValueError("Feature type must not be empty.")
        return Feature(
            name=name,
            feature_type=feature_type,
            parameters=dict(parameters or {}),
            metadata=metadata or FeatureMetadata(),
            parent_ids=list(parent_ids or []),
        )
