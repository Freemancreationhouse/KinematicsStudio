from __future__ import annotations

from engine.features.feature import Feature


class FeatureRegistry:
    """Registry of feature definitions and dependency references."""

    def __init__(self) -> None:
        """Create an empty feature registry."""

        self._features: dict[str, Feature] = {}

    def register(self, feature: Feature) -> Feature:
        """Register a feature record."""

        self._features[feature.feature_id] = feature
        return feature

    def unregister(self, feature_id: str) -> Feature | None:
        """Remove a feature record."""

        return self._features.pop(str(feature_id), None)

    def get(self, feature_id: str) -> Feature | None:
        """Return a feature by id."""

        return self._features.get(str(feature_id))

    def features(self) -> tuple[Feature, ...]:
        """Return all registered features."""

        return tuple(self._features.values())

    def by_owner(self, owner: str) -> tuple[Feature, ...]:
        """Return all features by owner label."""

        return tuple(
            feature for feature in self._features.values()
            if feature.metadata.owner == owner
        )

    def clear(self) -> None:
        """Clear all registered feature records."""

        self._features.clear()
