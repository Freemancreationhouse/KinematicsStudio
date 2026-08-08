from __future__ import annotations

from typing import Any

from engine.features.feature import Feature
from engine.features.feature_builder import FeatureBuilder
from engine.features.feature_metadata import FeatureMetadata
from engine.features.feature_registry import FeatureRegistry


class FeatureManager:
    """Coordinates feature records with geometry/topology/history services."""

    def __init__(
        self,
        *,
        geometry_kernel: Any | None = None,
        topology_manager: Any | None = None,
        history_manager: Any | None = None,
    ) -> None:
        """Create a feature manager with optional framework dependencies."""

        self.registry = FeatureRegistry()
        self.builder = FeatureBuilder()
        self.geometry_kernel = geometry_kernel
        self.topology_manager = topology_manager
        self.history_manager = history_manager

    def create_feature(
        self,
        *,
        name: str,
        feature_type: str,
        parameters: dict[str, Any] | None = None,
        metadata: FeatureMetadata | None = None,
        parent_ids: list[str] | None = None,
    ) -> Feature:
        """Create and register a feature record."""

        feature = self.builder.build(
            name=name,
            feature_type=feature_type,
            parameters=parameters,
            metadata=metadata,
            parent_ids=parent_ids,
        )
        self.registry.register(feature)
        self._record_history("FeatureCreated", feature)
        return feature

    def add_feature(self, feature: Feature) -> Feature:
        """Register an externally constructed feature record."""

        self.registry.register(feature)
        self._record_history("FeatureRegistered", feature)
        return feature

    def feature(self, feature_id: str) -> Feature | None:
        """Return a feature by id."""

        return self.registry.get(feature_id)

    def suppress(self, feature_id: str, suppressed: bool = True) -> None:
        """Set feature suppression metadata without regenerating geometry."""

        feature = self.feature(feature_id)
        if feature is None:
            return
        feature.suppressed = bool(suppressed)
        self._record_history("FeatureSuppressionChanged", feature)

    def features(self) -> tuple[Feature, ...]:
        """Return all feature records."""

        return self.registry.features()

    def clear(self) -> None:
        """Clear all feature records."""

        self.registry.clear()

    def _record_history(self, event_name: str, feature: Feature) -> None:
        """Record feature metadata in the optional history manager."""

        if self.history_manager is None:
            return
        record = getattr(self.history_manager, "record_feature_event", None)
        if callable(record):
            record(event_name, feature)
