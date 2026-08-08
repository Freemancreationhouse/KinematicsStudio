from __future__ import annotations

from dataclasses import dataclass, field

from engine.snapping.snapping_target import SnappingTarget


@dataclass
class SnappingCache:
    """Small workspace-scoped snap candidate cache."""

    workspace_id: int | None = None
    revision: int | None = None
    targets: list[SnappingTarget] = field(default_factory=list)

    def valid_for(self, workspace: object, revision: int | None = None) -> bool:
        """Return True when cached targets are valid for a workspace."""

        if revision is None:
            return False
        return self.workspace_id == id(workspace) and self.revision == revision

    def store(
        self,
        workspace: object,
        targets: list[SnappingTarget],
        revision: int | None = None,
    ) -> None:
        """Store snap targets for a workspace."""

        self.workspace_id = id(workspace)
        self.revision = revision
        self.targets = list(targets)

    def clear(self) -> None:
        """Clear cached snap targets."""

        self.workspace_id = None
        self.revision = None
        self.targets.clear()
