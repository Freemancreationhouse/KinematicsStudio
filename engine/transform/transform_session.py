from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from engine.geometry.matrix4 import Matrix4
from engine.transform.transform_constraints import TransformConstraints
from engine.transform.transform_context import TransformContext
from engine.transform.transform_operation import TransformOperation
from engine.transform.transform_state import TransformState
from engine.transform.transform_target import TransformTarget
from engine.transform.transform_transaction import TransformTransaction


@dataclass
class TransformSession:
    """Tracks one future transform operation without editing geometry."""

    context: TransformContext
    targets: tuple[TransformTarget, ...]
    constraints: TransformConstraints = field(default_factory=TransformConstraints)
    state: TransformState = field(default_factory=TransformState)
    operation: TransformOperation | None = None
    session_id: str = field(default_factory=lambda: str(uuid4()))
    active: bool = True
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)
    transaction: TransformTransaction | None = None

    def set_operation(self, operation: TransformOperation) -> None:
        """Assign the command-producing operation for this session."""

        if not self.active:
            raise RuntimeError("Cannot set operation on a closed transform session.")
        self.operation = operation
        self.transaction = None

    def begin_transaction(self) -> TransformTransaction:
        """Create transaction metadata for this session."""

        if not self.active:
            raise RuntimeError("Cannot begin transaction on a closed session.")
        transaction = TransformTransaction(
            context=self.context,
            targets=self.targets,
            state=self.state,
            operation=self.operation,
        )
        transaction.capture_before()
        self.transaction = transaction
        return transaction

    def preview(self, matrix: Matrix4) -> None:
        """Store a preview matrix without applying it to model geometry."""

        if not self.active:
            raise RuntimeError("Cannot preview a closed transform session.")
        self.state.enable_preview(matrix)
        if self.transaction is None:
            self.begin_transaction()
        if self.transaction is not None:
            self.transaction.preview()

    def commit(self) -> Any:
        """Commit through the future operation command."""

        if self.transaction is None:
            self.begin_transaction()
        if self.transaction is None:
            return None
        result = self.transaction.commit()
        self.active = False
        return result

    def cancel(self) -> None:
        """Cancel the session without applying model changes."""

        if self.transaction is not None:
            self.transaction.cancel()
        self.state.clear_preview()
        self.active = False
