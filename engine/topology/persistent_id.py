from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class PersistentTopologyId:
    """Stable topology identifier used across feature regeneration."""

    value: str = field(default_factory=lambda: str(uuid4()))
    source_feature_id: str = ""
    semantic_name: str = ""

    def __str__(self) -> str:
        """Return the persistent id value."""

        return self.value
