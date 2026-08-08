from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.topology.persistent_id import PersistentTopologyId


@dataclass
class Body:
    """Topology body metadata for a model body or generated feature result."""

    id: PersistentTopologyId = field(default_factory=PersistentTopologyId)
    name: str = "Body"
    shell_ids: list[str] = field(default_factory=list)
    feature_id: str = ""
    entity_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
