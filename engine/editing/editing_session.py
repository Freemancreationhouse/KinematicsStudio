from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from engine.editing.editing_context import EditingContext
from engine.editing.editing_mode import EditingMode
from engine.editing.editing_operation import EditingOperation


@dataclass
class EditingSession:
    """Tracks a geometry editing session without mutating geometry directly."""

    context: EditingContext
    mode: EditingMode = EditingMode.SELECT
    session_id: str = field(default_factory=lambda: str(uuid4()))
    operations: list[EditingOperation] = field(default_factory=list)
    active: bool = True
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_operation(self, operation: EditingOperation) -> None:
        """Queue an editing operation for command-system execution."""

        if not self.active:
            raise RuntimeError("Cannot add operations to a closed editing session.")
        self.operations.append(operation)

    def close(self) -> None:
        """Mark the session closed."""

        self.active = False
