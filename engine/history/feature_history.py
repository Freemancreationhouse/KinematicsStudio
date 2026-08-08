from __future__ import annotations

from engine.history.history_node import HistoryNode


class FeatureHistory:
    """Directed feature-history record store without solve algorithms."""

    def __init__(self) -> None:
        """Create an empty feature history."""

        self._nodes: dict[str, HistoryNode] = {}

    def add_node(self, node: HistoryNode) -> HistoryNode:
        """Add a history node and maintain parent child references."""

        self._nodes[node.node_id] = node
        for parent_id in node.parent_ids:
            parent = self._nodes.get(parent_id)
            if parent is not None and node.node_id not in parent.child_ids:
                parent.child_ids.append(node.node_id)
        return node

    def node(self, node_id: str) -> HistoryNode | None:
        """Return a history node by id."""

        return self._nodes.get(str(node_id))

    def nodes(self) -> tuple[HistoryNode, ...]:
        """Return all history nodes."""

        return tuple(self._nodes.values())

    def clear(self) -> None:
        """Clear all feature history nodes."""

        self._nodes.clear()
