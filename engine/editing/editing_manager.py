from __future__ import annotations

from typing import Any

from engine.editing.editing_context import EditingContext
from engine.editing.editing_events import EditingEvents
from engine.editing.editing_mode import EditingMode
from engine.editing.editing_session import EditingSession
from engine.geometry import GeometryKernel


class EditingManager:
    """Coordinates editing sessions through existing command architecture."""

    def __init__(
        self,
        workspace: Any,
        geometry_kernel: GeometryKernel | None = None,
    ) -> None:
        """Create an editing manager for a workspace."""

        self.workspace = workspace
        self.geometry_kernel = geometry_kernel or GeometryKernel(workspace)
        self.events = EditingEvents()
        self._sessions: dict[str, EditingSession] = {}
        self._active_session_id: str | None = None

    def begin_session(
        self,
        mode: EditingMode | str = EditingMode.SELECT,
        *,
        actor: str = "human",
        design_intent_graph_id: str = "",
    ) -> EditingSession:
        """Begin an editing session using current workspace services."""

        normalized = mode if isinstance(mode, EditingMode) else EditingMode(str(mode))
        context = EditingContext.from_workspace(
            self.workspace,
            self.geometry_kernel,
            actor=actor,
            design_intent_graph_id=design_intent_graph_id,
        )
        session = EditingSession(context=context, mode=normalized)
        self._sessions[session.session_id] = session
        self._active_session_id = session.session_id
        self.events.emit("EditingSessionStarted", session.session_id, {"mode": mode})
        return session

    def active_session(self) -> EditingSession | None:
        """Return the active editing session."""

        if self._active_session_id is None:
            return None
        return self._sessions.get(self._active_session_id)

    def commit_session(self, session_id: str | None = None) -> None:
        """Commit queued operations through the existing CommandManager."""

        session = self._session(session_id)
        if session is None:
            return
        command_manager = session.context.command_manager
        for operation in tuple(session.operations):
            if not operation.validate(session.context):
                raise ValueError(f"Editing operation failed validation: {operation}")
            command = operation.command(session.context)
            if command is None:
                continue
            if command_manager is None:
                raise RuntimeError("Editing operation requires CommandManager.")
            command_manager.execute(command)
        session.close()
        self.events.emit("EditingSessionCommitted", session.session_id, {})

    def cancel_session(self, session_id: str | None = None) -> None:
        """Cancel a session without executing queued operations."""

        session = self._session(session_id)
        if session is None:
            return
        session.operations.clear()
        session.close()
        self.events.emit("EditingSessionCancelled", session.session_id, {})

    def sessions(self) -> tuple[EditingSession, ...]:
        """Return all editing sessions."""

        return tuple(self._sessions.values())

    def clear(self) -> None:
        """Cancel and remove all editing sessions."""

        for session in self._sessions.values():
            session.operations.clear()
            session.close()
        self._sessions.clear()
        self._active_session_id = None
        self.events.emit("EditingSessionsCleared", "", {})

    def _session(self, session_id: str | None) -> EditingSession | None:
        """Return a session by id or the active session."""

        if session_id is None:
            return self.active_session()
        return self._sessions.get(session_id)
