from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.topology.persistent_id import PersistentTopologyId


@dataclass
class Shell:
    """Topology shell metadata containing faces."""

    id: PersistentTopologyId = field(default_factory=PersistentTopologyId)
    face_ids: list[str] = field(default_factory=list)
    closed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
