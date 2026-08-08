from __future__ import annotations

from typing import Any

from engine.transform.transform_constraints import TransformConstraints
from engine.transform.transform_context import TransformContext
from engine.transform.transform_events import TransformEvents
from engine.transform.transform_operation import TransformOperation
from engine.transform.transform_session import TransformSession
from engine.transform.transform_target import TransformTarget, targets_from_selection


class TransformManager:
    """Coordinates transform sessions through existing services."""

    def __init__(self, workspace: Any | None = None) -> None:
        """Create a passive transform manager."""

        self.workspace = workspace
        self.events = TransformEvents()
        self._sessions: dict[str, TransformSession] = {}
        self._active_session_id: str | None = None
        self._ai_requests: list[dict[str, Any]] = []

    def begin_session(
        self,
        *,
        workspace: Any | None = None,
        targets: tuple[TransformTarget, ...] | None = None,
        constraints: TransformConstraints | None = None,
        operation: TransformOperation | None = None,
        actor: str = "human",
        design_intent_graph_id: str = "",
    ) -> TransformSession:
        """Begin a transform session without mutating geometry."""

        active_workspace = workspace or self.workspace
        if active_workspace is None:
            raise RuntimeError("TransformManager requires a workspace.")

        context = TransformContext.from_workspace(
            active_workspace,
            actor=actor,
            design_intent_graph_id=design_intent_graph_id,
        )
        resolved_targets = targets
        if resolved_targets is None:
            resolved_targets = targets_from_selection(context.selection_manager)

        session = TransformSession(
            context=context,
            targets=tuple(resolved_targets),
            constraints=constraints or TransformConstraints(),
            operation=operation,
        )
        self._sessions[session.session_id] = session
        self._active_session_id = session.session_id
        self.events.emit(
            "TransformSessionStarted",
            session.session_id,
            {"target_count": len(session.targets), "actor": actor},
        )
        return session

    def active_session(self) -> TransformSession | None:
        """Return the active transform session."""

        if self._active_session_id is None:
            return None
        return self._sessions.get(self._active_session_id)

    def session(self, session_id: str) -> TransformSession | None:
        """Return a transform session by id."""

        return self._sessions.get(str(session_id))

    def set_operation(
        self,
        operation: TransformOperation,
        session_id: str | None = None,
    ) -> None:
        """Assign an operation to a transform session."""

        session = self._resolve_session(session_id)
        if session is None:
            raise RuntimeError("No transform session is active.")
        session.set_operation(operation)
        self.events.emit(
            "TransformOperationAssigned",
            session.session_id,
            {"operation": operation},
        )

    def preview(
        self,
        matrix: Any,
        session_id: str | None = None,
    ) -> None:
        """Store preview transform state for a session."""

        session = self._resolve_session(session_id)
        if session is None:
            raise RuntimeError("No transform session is active.")
        session.preview(matrix)
        self.events.emit(
            "TransformPreviewChanged",
            session.session_id,
            {"matrix": matrix},
        )

    def commit(self, session_id: str | None = None) -> Any:
        """Commit a session through its command-producing operation."""

        session = self._resolve_session(session_id)
        if session is None:
            return None
        result = session.commit()
        self.events.emit("TransformSessionCommitted", session.session_id, {})
        return result

    def cancel(self, session_id: str | None = None) -> None:
        """Cancel a transform session without model changes."""

        session = self._resolve_session(session_id)
        if session is None:
            return
        session.cancel()
        self.events.emit("TransformSessionCancelled", session.session_id, {})

    def end_session(self, session_id: str | None = None) -> None:
        """Remove a completed or cancelled transform session."""

        session = self._resolve_session(session_id)
        if session is None:
            return
        self._sessions.pop(session.session_id, None)
        if self._active_session_id == session.session_id:
            self._active_session_id = None
        self.events.emit("TransformSessionEnded", session.session_id, {})

    def sessions(self) -> tuple[TransformSession, ...]:
        """Return all known transform sessions."""

        return tuple(self._sessions.values())

    def clear(self) -> None:
        """Cancel and remove all transform sessions."""

        for session in tuple(self._sessions.values()):
            session.cancel()
        self._sessions.clear()
        self._active_session_id = None
        self.events.emit("TransformSessionsCleared", "", {})

    def request_ai_transform(
        self,
        operation_type: str,
        *,
        target_ids: tuple[str, ...] = (),
        parameters: dict[str, Any] | None = None,
        actor: str = "ai",
        design_intent_graph_id: str = "",
    ) -> dict[str, Any]:
        """Record an AI transform request without executing geometry changes."""

        request = {
            "operation_type": str(operation_type),
            "target_ids": tuple(target_ids),
            "parameters": dict(parameters or {}),
            "actor": actor,
            "design_intent_graph_id": design_intent_graph_id,
        }
        self._ai_requests.append(request)
        self.events.emit("TransformAIRequestRecorded", "", request)
        return request

    def ai_requests(self) -> tuple[dict[str, Any], ...]:
        """Return recorded AI transform integration requests."""

        return tuple(dict(request) for request in self._ai_requests)

    def _resolve_session(self, session_id: str | None) -> TransformSession | None:
        """Return a requested or active transform session."""

        if session_id is None:
            return self.active_session()
        return self.session(session_id)
