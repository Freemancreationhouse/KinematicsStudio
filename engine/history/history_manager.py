from __future__ import annotations

from typing import Any

from engine.history.feature_history import FeatureHistory
from engine.history.history_events import HistoryEvents
from engine.history.history_node import HistoryNode


class HistoryManager:
    """Maintains action history and feature-history framework data."""

    def __init__(self) -> None:
        """Create an empty history manager."""

        self.entries: list[Any] = []
        self.events = HistoryEvents()
        self.feature_history = FeatureHistory()

    def add(self, action: Any) -> None:
        """Add a legacy history action entry."""

        self.entries.append(action)
        self.events.emit("HistoryActionAdded", "", {"action": action})

    def clear(self) -> None:
        """Clear action and feature history."""

        self.entries.clear()
        self.feature_history.clear()
        self.events.emit("HistoryCleared", "", {})

    @property
    def count(self) -> int:
        """Return legacy action history count."""

        return len(self.entries)

    @property
    def last(self) -> Any | None:
        """Return the last legacy action entry."""

        return self.entries[-1] if self.entries else None

    def add_node(self, node: HistoryNode) -> HistoryNode:
        """Add a feature-history node."""

        added = self.feature_history.add_node(node)
        self.events.emit("HistoryNodeAdded", added.node_id, {"node": added})
        return added

    def record_feature_event(self, event_name: str, feature: Any) -> HistoryNode:
        """Record a feature metadata event as a history node."""

        node = HistoryNode(
            name=event_name,
            feature_id=getattr(feature, "feature_id", ""),
            parent_ids=list(getattr(feature, "parent_ids", [])),
            metadata={
                "feature_name": getattr(feature, "name", ""),
                "feature_type": getattr(feature, "feature_type", ""),
            },
        )
        return self.add_node(node)
