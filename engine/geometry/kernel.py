from __future__ import annotations

from typing import Any

from engine.geometry.context import GeometryContext
from engine.geometry.events import GeometryEvents
from engine.geometry.factory import GeometryFactory
from engine.geometry.observer import GeometryObserverRegistry
from engine.geometry.registry import GeometryRegistry
from engine.geometry.transaction import GeometryTransaction
from engine.geometry.validator import GeometryValidator, GeometryValidationResult


class GeometryKernel:
    """Application geometry framework facade for future editing operations."""

    def __init__(self, workspace: Any | None = None) -> None:
        """Create a geometry kernel bound optionally to a workspace."""

        self.events = GeometryEvents()
        self.factory = GeometryFactory()
        self.registry = GeometryRegistry()
        self.validator = GeometryValidator()
        self.observers = GeometryObserverRegistry(self.events)
        self.context = (
            GeometryContext.from_workspace(workspace)
            if workspace is not None
            else GeometryContext()
        )
        self._transactions: dict[str, GeometryTransaction] = {}

    def attach_workspace(self, workspace: Any) -> GeometryContext:
        """Attach the kernel to the active workspace services."""

        self.context = GeometryContext.from_workspace(workspace)
        self.events.emit(
            "GeometryWorkspaceAttached",
            source="GeometryKernel",
            payload={"workspace": getattr(workspace, "name", "")},
        )
        return self.context

    def begin_transaction(self, name: str) -> GeometryTransaction:
        """Open a framework transaction for geometry bookkeeping."""

        transaction = GeometryTransaction(name=name, context=self.context)
        self._transactions[transaction.transaction_id] = transaction
        self.events.emit(
            "GeometryTransactionOpened",
            source="GeometryKernel",
            payload={"transaction_id": transaction.transaction_id, "name": name},
        )
        return transaction

    def commit_transaction(self, transaction: GeometryTransaction) -> None:
        """Commit a framework transaction."""

        transaction.commit()
        self.events.emit(
            "GeometryTransactionCommitted",
            source="GeometryKernel",
            payload={"transaction_id": transaction.transaction_id},
        )

    def rollback_transaction(self, transaction: GeometryTransaction) -> None:
        """Rollback a framework transaction."""

        transaction.rollback()
        self.events.emit(
            "GeometryTransactionRolledBack",
            source="GeometryKernel",
            payload={"transaction_id": transaction.transaction_id},
        )

    def register_geometry(
        self,
        geometry: Any,
        *,
        geometry_id: str | None = None,
        owner_id: str = "",
        metadata: dict[str, Any] | None = None,
    ):
        """Validate and register geometry metadata without owning scene data."""

        result = self.validator.validate_geometry(geometry)
        if not result.valid:
            raise ValueError("; ".join(result.errors))
        record = self.registry.register(
            geometry,
            geometry_id=geometry_id,
            owner_id=owner_id,
            metadata=metadata,
        )
        self.events.emit(
            "GeometryRegistered",
            source="GeometryKernel",
            payload={"geometry_id": record.geometry_id},
        )
        return record

    def create_geometry(self, geometry_type: str, **parameters: Any) -> Any:
        """Create geometry through a registered builder."""

        context_result: GeometryValidationResult = self.validator.validate_context(
            self.context
        )
        if not context_result.valid:
            raise ValueError("; ".join(context_result.errors))
        geometry = self.factory.create(geometry_type, self.context, **parameters)
        self.register_geometry(geometry, metadata={"geometry_type": geometry_type})
        return geometry

    def clear(self) -> None:
        """Clear framework registry and open transaction bookkeeping."""

        self.registry.clear()
        self._transactions.clear()
        self.events.emit(
            "GeometryKernelCleared",
            source="GeometryKernel",
            payload={},
        )
