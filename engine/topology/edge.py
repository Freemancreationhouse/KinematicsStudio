from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.topology.persistent_id import PersistentTopologyId


@dataclass
class Edge:
    """Topology edge metadata connecting persistent vertex ids."""

    id: PersistentTopologyId = field(default_factory=PersistentTopologyId)
    start_vertex_id: str = ""
    end_vertex_id: str = ""
    curve_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
