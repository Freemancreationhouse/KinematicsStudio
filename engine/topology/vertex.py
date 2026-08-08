from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.topology.persistent_id import PersistentTopologyId


@dataclass
class Vertex:
    """Topology vertex metadata referencing model-space geometry externally."""

    id: PersistentTopologyId = field(default_factory=PersistentTopologyId)
    point_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
