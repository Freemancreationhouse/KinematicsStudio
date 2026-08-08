from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class GeometryTransactionState(str, Enum):
    """Lifecycle state for geometry framework transactions."""

    OPEN = "Open"
    COMMITTED = "Committed"
    ROLLED_BACK = "Rolled Back"


@dataclass
class GeometryTransaction:
    """Records reversible framework-level geometry bookkeeping changes."""

    name: str
    context: Any
    transaction_id: str = field(default_factory=lambda: str(uuid4()))
    state: GeometryTransactionState = GeometryTransactionState.OPEN
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)
    _rollback_actions: list[Callable[[], None]] = field(default_factory=list)

    def add_rollback(self, action: Callable[[], None]) -> None:
        """Register a rollback action for framework bookkeeping."""

        if self.state is not GeometryTransactionState.OPEN:
            raise RuntimeError("Cannot modify a closed geometry transaction.")
        self._rollback_actions.append(action)

    def commit(self) -> None:
        """Commit the transaction bookkeeping."""

        if self.state is not GeometryTransactionState.OPEN:
            return
        self.state = GeometryTransactionState.COMMITTED
        self._rollback_actions.clear()

    def rollback(self) -> None:
        """Rollback framework bookkeeping in reverse order."""

        if self.state is not GeometryTransactionState.OPEN:
            return
        for action in reversed(self._rollback_actions):
            action()
        self.state = GeometryTransactionState.ROLLED_BACK
        self._rollback_actions.clear()
