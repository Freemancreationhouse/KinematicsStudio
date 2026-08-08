from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.topology.persistent_id import PersistentTopologyId


@dataclass
class Loop:
    """Ordered boundary loop metadata."""

    id: PersistentTopologyId = field(default_factory=PersistentTopologyId)
    edge_ids: list[str] = field(default_factory=list)
    closed: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
