from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from engine.transform.transform_context import TransformContext
from engine.transform.transform_operation import TransformOperation
from engine.transform.transform_state import TransformState
from engine.transform.transform_target import TransformTarget


@dataclass
class TransformTransaction:
    """Command-system transaction metadata for a transform session."""

    context: TransformContext
    targets: tuple[TransformTarget, ...]
    state: TransformState
    operation: TransformOperation | None = None
    transaction_id: str = field(default_factory=lambda: str(uuid4()))
    before_state: dict[str, dict[str, Any]] = field(default_factory=dict)
    after_state: dict[str, dict[str, Any]] = field(default_factory=dict)
    preview_active: bool = False
    committed: bool = False
    cancelled: bool = False

    def capture_before(self) -> None:
        """Capture non-owning before-state references for rollback metadata."""

        self.before_state = self._capture()

    def capture_after(self) -> None:
        """Capture non-owning after-state references for history metadata."""

        self.after_state = self._capture()

    def preview(self) -> None:
        """Mark the transaction as previewing a transform."""

        self.preview_active = True
        self.state.preview_enabled = True

    def clear_preview(self) -> None:
        """Clear preview transaction state."""

        self.preview_active = False
        self.state.clear_preview()

    def commit(self) -> Any:
        """Create and execute the operation command through CommandManager."""

        if self.cancelled:
            raise RuntimeError("Cannot commit a cancelled transform transaction.")
        if self.operation is None:
            raise RuntimeError("Transform transaction has no operation.")
        if not self.operation.validate(self.context, self.targets, self.state):
            raise ValueError("Transform operation failed validation.")

        command = self.operation.command(self)
        if command is None:
            raise RuntimeError("Transform operation did not provide a command.")

        command_manager = self.context.command_manager
        if command_manager is None:
            raise RuntimeError("Transform operation requires CommandManager.")

        result = command_manager.execute(command)
        self.committed = True
        self.clear_preview()
        self.capture_after()
        return result

    def cancel(self) -> None:
        """Cancel this transaction without mutating model data."""

        self.cancelled = True
        self.clear_preview()

    def _capture(self) -> dict[str, dict[str, Any]]:
        """Capture lightweight target transform metadata."""

        state: dict[str, dict[str, Any]] = {}
        for target in self.targets:
            key = target.persistent_id or str(id(target.entity))
            state[key] = self._snapshot_entity(target.entity)
        return state

    def _snapshot_entity(self, entity: Any) -> dict[str, Any]:
        """Return available transform-like metadata without copying geometry."""

        snapshot: dict[str, Any] = {}
        for name in ("transform", "matrix", "position", "rotation", "scale"):
            value = getattr(entity, name, None)
            if callable(value):
                try:
                    value = value()
                except TypeError:
                    continue
            copy_method = getattr(value, "copy", None)
            snapshot[name] = copy_method() if callable(copy_method) else value
        return snapshot
