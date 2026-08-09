from __future__ import annotations

from typing import Any

from engine.dynamic_input.dynamic_input_context import DynamicInputContext
from engine.dynamic_input.dynamic_input_events import DynamicInputEvents
from engine.dynamic_input.dynamic_input_fields import (
    DynamicInputField,
    DynamicInputFieldType,
)
from engine.dynamic_input.dynamic_input_overlay import DynamicInputOverlay
from engine.dynamic_input.dynamic_input_parser import DynamicInputParser
from engine.dynamic_input.dynamic_input_session import DynamicInputSession
from engine.dynamic_input.expression_parser import ExpressionResult
from engine.dynamic_input.unit_parser import ParsedUnitValue


class DynamicInputManager:
    """Authoritative manager for reusable dynamic numeric CAD input."""

    def __init__(
        self,
        parser: DynamicInputParser | None = None,
        events: DynamicInputEvents | None = None,
    ) -> None:
        """Create an engine-level dynamic input manager."""

        self.parser = parser or DynamicInputParser()
        self.events = events or DynamicInputEvents()
        self.overlay = DynamicInputOverlay()
        self._sessions: dict[str, DynamicInputSession] = {}
        self._active_session_id: str | None = None
        self._ai_requests: list[dict[str, Any]] = []
        self.events.subscribe("*", self._sync_overlay)

    def start_session(
        self,
        *,
        workspace: Any = None,
        tool_name: str = "",
        command_name: str = "",
        snapping_manager: Any = None,
        transform_manager: Any = None,
        viewport_id: str = "",
        coordinate_space: str = "World",
        units: str = "mm",
        fields: tuple[DynamicInputField | DynamicInputFieldType | str, ...] = (),
        actor: str = "human",
        metadata: dict[str, Any] | None = None,
    ) -> DynamicInputSession:
        """Begin a dynamic input session for an active tool."""

        context = DynamicInputContext.from_workspace(
            workspace,
            tool_name=tool_name,
            command_name=command_name,
            snapping_manager=snapping_manager,
            transform_manager=transform_manager,
            viewport_id=viewport_id,
            coordinate_space=coordinate_space,
            units=units,
            actor=actor,
            metadata=metadata,
        )
        session = DynamicInputSession(context, self.parser, self.events)
        self._sessions[session.session_id] = session
        self._active_session_id = session.session_id
        if fields:
            session.show_fields(fields)
        else:
            session.show()
        self.events.emit(
            "DynamicInputSessionStarted",
            session.session_id,
            {"tool_name": tool_name, "command_name": command_name, "actor": actor},
        )
        return session

    def end_session(self, session_id: str | None = None) -> None:
        """End and remove a dynamic input session."""

        session = self._resolve_session(session_id)
        if session is None:
            return
        session.hide()
        self._sessions.pop(session.session_id, None)
        if self._active_session_id == session.session_id:
            self._active_session_id = None
        self.events.emit("DynamicInputSessionEnded", session.session_id, {})

    def active_session(self) -> DynamicInputSession | None:
        """Return the active dynamic input session."""

        if self._active_session_id is None:
            return None
        return self._sessions.get(self._active_session_id)

    def session(self, session_id: str) -> DynamicInputSession | None:
        """Return a session by identifier."""

        return self._sessions.get(str(session_id))

    def sessions(self) -> tuple[DynamicInputSession, ...]:
        """Return all live dynamic input sessions."""

        return tuple(self._sessions.values())

    def set_fields(
        self,
        fields: tuple[DynamicInputField | DynamicInputFieldType | str, ...],
        session_id: str | None = None,
    ) -> None:
        """Set active HUD fields for a session."""

        session = self._require_session(session_id)
        session.show_fields(fields)

    def update_cursor(self, position: Any, session_id: str | None = None) -> None:
        """Update HUD cursor position for a session."""

        session = self._require_session(session_id)
        session.update_cursor(position)

    def input_text(
        self,
        text: str,
        *,
        field_id: str | None = None,
        session_id: str | None = None,
    ) -> Any:
        """Route typed input to a session field."""

        session = self._require_session(session_id)
        return session.input_text(text, field_id=field_id)

    def handle_key(
        self,
        key: str,
        *,
        shift: bool = False,
        session_id: str | None = None,
    ) -> bool:
        """Route HUD keyboard navigation to a session."""

        session = self._resolve_session(session_id)
        if session is None:
            return False
        return session.handle_key(key, shift=shift)

    def commit(self, session_id: str | None = None) -> dict[str, Any]:
        """Commit a dynamic input session."""

        session = self._require_session(session_id)
        values = session.commit()
        self.end_session(session.session_id)
        return values

    def cancel(self, session_id: str | None = None) -> None:
        """Cancel a dynamic input session."""

        session = self._resolve_session(session_id)
        if session is None:
            return
        session.cancel()
        self.end_session(session.session_id)

    def evaluate_expression(self, expression: Any) -> float:
        """Evaluate an arithmetic expression for AI and tools."""

        return self.parser.parse_expression(expression).value

    def expression_result(self, expression: Any) -> ExpressionResult:
        """Return full expression evaluation metadata."""

        return self.parser.parse_expression(expression)

    def convert_units(
        self,
        text: Any,
        *,
        expected_dimension: str = "length",
    ) -> ParsedUnitValue:
        """Parse and normalize unit-aware input for AI and tools."""

        return self.parser.parse_unit(text, expected_dimension=expected_dimension)

    def request_ai_session(
        self,
        tool_name: str,
        *,
        fields: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record an AI dynamic-input request without editing geometry."""

        request = {
            "tool_name": str(tool_name),
            "fields": tuple(fields),
            "metadata": dict(metadata or {}),
        }
        self._ai_requests.append(request)
        self.events.emit("DynamicInputAIRequestRecorded", "", request)
        return request

    def ai_requests(self) -> tuple[dict[str, Any], ...]:
        """Return recorded AI dynamic-input integration requests."""

        return tuple(dict(request) for request in self._ai_requests)

    def clear(self) -> None:
        """Cancel and remove all dynamic input sessions."""

        for session in tuple(self._sessions.values()):
            session.cancel()
        self._sessions.clear()
        self._active_session_id = None
        self.overlay.hide()
        self.events.emit("DynamicInputSessionsCleared", "", {})

    def _resolve_session(self, session_id: str | None) -> DynamicInputSession | None:
        """Return a session by id or the active session."""

        if session_id is not None:
            return self._sessions.get(str(session_id))
        return self.active_session()

    def _require_session(self, session_id: str | None) -> DynamicInputSession:
        """Return a session or raise when no session is active."""

        session = self._resolve_session(session_id)
        if session is None:
            raise RuntimeError("No dynamic input session is active.")
        return session

    def _sync_overlay(self, event: Any) -> None:
        """Synchronize the presentation model after session events."""

        session_id = getattr(event, "session_id", "")
        session = self._sessions.get(session_id)
        if session is None:
            if session_id == "" and self._active_session_id is None:
                self.overlay.hide()
            return
        self.overlay.update_from_state(session.state)
