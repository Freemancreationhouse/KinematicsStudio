from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FeatureMetadata:
    """Metadata describing feature intent, ownership and collaboration."""

    owner: str = "human"
    ai_generated: bool = False
    ai_model: str = ""
    design_intent_graph_id: str = ""
    source_prompt_id: str = ""
    collaborators: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)

    def mark_ai_owned(
        self,
        *,
        model: str = "",
        prompt_id: str = "",
        design_intent_graph_id: str = "",
    ) -> None:
        """Mark this feature as AI-authored metadata."""

        self.owner = "ai"
        self.ai_generated = True
        self.ai_model = model
        self.source_prompt_id = prompt_id
        self.design_intent_graph_id = design_intent_graph_id
