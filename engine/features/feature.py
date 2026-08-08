from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from engine.features.feature_metadata import FeatureMetadata


@dataclass
class Feature:
    """Feature record used by future feature-based CAD editing."""

    name: str
    feature_type: str
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: FeatureMetadata = field(default_factory=FeatureMetadata)
    feature_id: str = field(default_factory=lambda: str(uuid4()))
    parent_ids: list[str] = field(default_factory=list)
    result_geometry_ids: list[str] = field(default_factory=list)
    result_topology_ids: list[str] = field(default_factory=list)
    suppressed: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
