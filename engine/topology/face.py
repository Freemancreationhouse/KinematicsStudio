from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.topology.persistent_id import PersistentTopologyId


@dataclass
class Face:
    """Topology face metadata referencing loops and surface identity."""

    id: PersistentTopologyId = field(default_factory=PersistentTopologyId)
    loop_ids: list[str] = field(default_factory=list)
    surface_ref: str = ""
    normal_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
