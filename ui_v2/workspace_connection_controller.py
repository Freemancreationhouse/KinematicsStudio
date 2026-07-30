from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, Signal


class WorkspaceConnectionController(QObject):
    """Central UI orchestration layer for injected workspace shell objects."""

    panelsRequested = Signal()
    focusModeRequested = Signal()
    actionRequested = Signal(str)
    commandEntered = Signal(str)

    def __init__(
        self,
        *,
        ribbon: Any,
        left_toolbox: Any,
        viewport_area: Any,
        property_panel: Any,
        command_bar: Any,
        status_bar: Any,
        command_palette: Any,
        panel_manager: Any,
        tool_manager: Any,
        command_manager: Any,
        workspace: Any,
        app: Any | None = None,
        parent: QObject | None = None,
    ) -> None:
        """Store injected UI and backend dependencies without taking ownership."""

        super().__init__(parent)

        self.ribbon = ribbon
        self.left_toolbox = left_toolbox
        self.viewport_area = viewport_area
        self.property_panel = property_panel
        self.command_bar = command_bar
        self.status_bar = status_bar
        self.command_palette = command_palette
        self.panel_manager = panel_manager
        self.app = app
        self.tool_manager = tool_manager
        self.command_manager = command_manager
        self.workspace = workspace

        self._qt_connections: list[tuple[Any, Callable[..., Any]]] = []
        self._previous_callbacks: dict[tuple[int, str], tuple[Any, str, Any]] = {}
        self._connected = False

    def connect_all(self) -> None:
        """Connect all injected objects through this controller."""

        if self._connected:
            return

        self._connect_ribbon()
        self._connect_left_toolbox()
        self._connect_viewport()
        self._connect_command_bar()
        self._connect_command_palette()
        self._connect_command_manager()
        self._connect_tool_manager()
        self._connect_workspace()
        self._connect_panel_manager()
        self._connected = True
        self.refresh_all()

    def disconnect_all(self) -> None:
        """Disconnect all routes established by this controller."""

        for signal, slot in reversed(self._qt_connections):
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError):
                pass
        self._qt_connections.clear()

        for obj, attr_name, previous_value in self._previous_callbacks.values():
            if getattr(obj, attr_name, None) is not previous_value:
                setattr(obj, attr_name, previous_value)
        self._previous_callbacks.clear()
        self._connected = False

    def refresh_all(self) -> None:
        """Refresh property, status, and on-demand panels."""

        self._update_property_panel()
        self._update_status_bar()
        self._refresh_panels()

    def route_action(self, action_id: str) -> None:
        """Route a public workspace action without exposing widget internals."""

        if action_id.startswith("panel:"):
            self._toggle_panel(action_id.removeprefix("panel:"))
            return
        if action_id == "view_2d":
            self._call_if_available(self.viewport_area, "show_2d")
            self._call_if_available(self.left_toolbox, "set_active_action", action_id)
            self._focus_active_view()
            return
        if action_id == "view_3d":
            self._call_if_available(self.viewport_area, "show_3d")
            self._call_if_available(self.left_toolbox, "set_active_action", action_id)
            self._focus_active_view()
            return
        if action_id == "panels":
            self.panelsRequested.emit()
            return
        if action_id == "command_palette":
            self._show_command_palette()
            return
        if action_id == "focus_mode":
            self._enter_focus_mode()
            return
        if action_id == "presentation_mode":
            self._enter_presentation_mode()
            return
        if action_id == "reset_workspace_layout":
            self._reset_workspace_layout()
            return

        self._handle_action(action_id)

    def _connect_ribbon(self) -> None:
        """Connect ribbon-level action signals when exposed by the ribbon."""

        self._connect_signal(
            getattr(self.ribbon, "actionTriggered", None),
            self._handle_action,
        )

    def _connect_left_toolbox(self) -> None:
        """Connect left-toolbox action routing."""

        self._connect_signal(
            getattr(self.left_toolbox, "actionTriggered", None),
            self._handle_left_toolbox_action,
        )

    def _connect_viewport(self) -> None:
        """Connect viewport area state changes."""

        self._connect_signal(
            getattr(self.viewport_area, "active_view_changed", None),
            self._handle_active_view_changed,
        )

    def _connect_command_bar(self) -> None:
        """Connect command-bar text submission when available."""

        command_input = getattr(self.command_bar, "command", None)
        self._connect_signal(
            getattr(command_input, "returnPressed", None),
            self._handle_command_entered,
        )

    def _connect_command_palette(self) -> None:
        """Connect command-palette action routing when exposed."""

        self._connect_signal(
            getattr(self.command_palette, "actionTriggered", None),
            self._handle_action,
        )

    def _connect_command_manager(self) -> None:
        """Connect command-history change notifications."""

        self._chain_callback(
            self.command_manager,
            "on_change",
            self._handle_command_history_changed,
        )
        self._connect_signal(
            getattr(self.command_manager, "changed", None),
            self._handle_command_history_changed,
        )

    def _connect_tool_manager(self) -> None:
        """Connect tool-change notifications."""

        self._chain_callback(
            self.tool_manager,
            "on_change",
            self._handle_tool_changed,
        )
        self._connect_signal(
            getattr(self.tool_manager, "toolChanged", None),
            self._handle_tool_changed,
        )

    def _connect_workspace(self) -> None:
        """Connect workspace and selection notifications when available."""

        self._call_if_available(
            self.property_panel,
            "set_workspace",
            self.workspace,
            self._handle_property_changed,
        )

        selection = getattr(self.workspace, "selection", None)
        self._chain_callback(
            selection,
            "on_change",
            self._handle_selection_changed,
        )
        self._connect_signal(
            getattr(selection, "changed", None),
            self._handle_selection_changed,
        )
        self._connect_signal(
            getattr(self.workspace, "selectionChanged", None),
            self._handle_selection_changed,
        )
        self._connect_signal(
            getattr(self.workspace, "projectLoaded", None),
            self._handle_project_loaded,
        )

    def _connect_panel_manager(self) -> None:
        """Connect panel-manager notifications when exposed."""

        self._connect_signal(
            getattr(self.panel_manager, "panelOpened", None),
            self._handle_panel_opened,
        )
        self._connect_signal(
            getattr(self.panel_manager, "panelClosed", None),
            self._handle_panel_closed,
        )

    def _update_property_panel(self) -> None:
        """Push current selection state into the property panel."""

        selection = self._current_selection()
        if self._call_if_available(self.property_panel, "show_selection", selection):
            return
        self._call_if_available(self.property_panel, "refresh")

    def _update_status_bar(self) -> None:
        """Push current command, selection, and tool state into the status bar."""

        self._call_if_available(
            self.status_bar,
            "show_command_state",
            self.command_manager,
        )
        self._call_if_available(
            self.status_bar,
            "show_selection",
            self._current_selection(),
        )

        active_tool = getattr(self.tool_manager, "active_tool", None)
        if active_tool is None:
            active_tool = getattr(self.tool_manager, "current_tool", None)
        if active_tool is not None:
            self._call_if_available(self.status_bar, "show_tool", active_tool)

    def _refresh_panels(self) -> None:
        """Refresh all opened on-demand panels through the panel manager."""

        self._call_if_available(self.panel_manager, "refresh_all")

    def _handle_left_toolbox_action(self, action_id: str) -> None:
        """Route an action emitted by the left toolbox."""

        self.route_action(action_id)

    def _handle_action(self, action_id: str) -> None:
        """Publish a generic action request for higher-level routing."""

        self.actionRequested.emit(action_id)

    def _handle_active_view_changed(self, view_name: str) -> None:
        """Update UI state after the active viewport changes."""

        if view_name == "2d":
            self._call_if_available(self.left_toolbox, "set_active_action", "view_2d")
        elif view_name == "3d":
            self._call_if_available(self.left_toolbox, "set_active_action", "view_3d")
        self._update_status_bar()

    def _handle_command_entered(self) -> None:
        """Emit command text submitted from the command bar."""

        command_input = getattr(self.command_bar, "command", None)
        text = ""
        if command_input is not None:
            text = str(command_input.text()).strip()
            command_input.clear()
        if text:
            self.commandEntered.emit(text)

    def _handle_command_history_changed(self, *args: Any) -> None:
        """Refresh shell state when command history changes."""

        self._update_status_bar()
        self._refresh_panels()

    def _handle_tool_changed(self, tool: Any = None, *args: Any) -> None:
        """Refresh shell state when the active tool changes."""

        if tool is None:
            tool = getattr(self.tool_manager, "active_tool", None)
        self._call_if_available(self.status_bar, "show_tool", tool)
        self._update_property_panel()

    def _handle_selection_changed(self, *args: Any) -> None:
        """Refresh shell state when selection changes."""

        self._update_property_panel()
        self._update_status_bar()

    def _handle_property_changed(self, *args: Any) -> None:
        """Refresh routed shell state after a property edit."""

        self._refresh_panels()
        self._update_status_bar()

    def _handle_project_loaded(self, *args: Any) -> None:
        """Refresh routed shell state after project loading."""

        self._call_if_available(
            self.property_panel,
            "set_workspace",
            self.workspace,
            self._handle_property_changed,
        )
        self.refresh_all()

    def _handle_panel_opened(self, *args: Any) -> None:
        """Refresh status after a panel is opened."""

        self._update_status_bar()

    def _handle_panel_closed(self, *args: Any) -> None:
        """Refresh status after a panel is closed."""

        self._update_status_bar()

    def _show_command_palette(self) -> None:
        """Open the injected command palette using its public widget API."""

        self._call_if_available(self.command_palette, "rebuild_actions")
        search = getattr(self.command_palette, "search", None)
        if search is not None:
            self._call_if_available(search, "clear")
        self._call_if_available(self.command_palette, "refresh")
        self._call_if_available(self.command_palette, "show")
        self._call_if_available(self.command_palette, "raise_")
        self._call_if_available(self.command_palette, "activateWindow")
        if search is not None:
            self._call_if_available(search, "setFocus")

    def _enter_focus_mode(self) -> None:
        """Route the shell into focus mode."""

        self._call_if_available(self.ribbon, "setVisible", True)
        self._call_if_available(self.left_toolbox, "setVisible", True)
        self._call_if_available(self.property_panel, "setVisible", False)
        self._call_if_available(self.command_bar, "setVisible", False)
        self._call_if_available(self.status_bar, "show_status_text", "Focus Mode")
        self.focusModeRequested.emit()

    def _enter_presentation_mode(self) -> None:
        """Route the shell into presentation mode."""

        self._call_if_available(self.ribbon, "setVisible", False)
        self._call_if_available(self.left_toolbox, "setVisible", False)
        self._call_if_available(self.property_panel, "setVisible", False)
        self._call_if_available(self.command_bar, "setVisible", False)
        self._call_if_available(
            self.status_bar,
            "show_status_text",
            "Presentation Mode",
        )

    def _reset_workspace_layout(self) -> None:
        """Route the shell back to the default workspace layout."""

        self._call_if_available(self.ribbon, "setVisible", True)
        self._call_if_available(self.left_toolbox, "setVisible", True)
        self._call_if_available(self.property_panel, "setVisible", True)
        self._call_if_available(self.command_bar, "setVisible", True)
        self._call_if_available(self.viewport_area, "show_2d")
        self._call_if_available(
            self.status_bar,
            "show_status_text",
            "Workspace layout reset",
        )

    def _toggle_panel(self, panel_id: str) -> None:
        """Route a panel toggle request through the panel manager."""

        self._call_if_available(self.panel_manager, "toggle_panel", panel_id)

    def _focus_active_view(self) -> None:
        """Focus and refresh the currently active viewport when supported."""

        active_view = None
        active_view_method = getattr(self.viewport_area, "active_view", None)
        if callable(active_view_method):
            active_view = active_view_method()
        if active_view is not None:
            self._call_if_available(active_view, "setFocus")
            self._call_if_available(active_view, "update")

    def _current_selection(self) -> Any:
        """Return the current workspace selection payload."""

        selection = getattr(self.workspace, "selection", None)
        if selection is None:
            return None
        return getattr(selection, "selected", selection)

    def _connect_signal(self, signal: Any, slot: Callable[..., Any]) -> None:
        """Connect a Qt signal and track it for safe disconnection."""

        if signal is None or not hasattr(signal, "connect"):
            return
        signal.connect(slot)
        self._qt_connections.append((signal, slot))

    def _chain_callback(
        self,
        obj: Any,
        attr_name: str,
        callback: Callable[..., Any],
    ) -> None:
        """Replace an object callback while preserving any previous callback."""

        if obj is None or not hasattr(obj, attr_name):
            return

        key = (id(obj), attr_name)
        if key in self._previous_callbacks:
            return

        previous = getattr(obj, attr_name)
        self._previous_callbacks[key] = (obj, attr_name, previous)

        def chained_callback(*args: Any, **kwargs: Any) -> None:
            if callable(previous):
                previous(*args, **kwargs)
            callback(*args, **kwargs)

        setattr(obj, attr_name, chained_callback)

    def _call_if_available(self, obj: Any, method_name: str, *args: Any) -> bool:
        """Call a named method when present and callable."""

        method = getattr(obj, method_name, None)
        if not callable(method):
            return False
        method(*args)
        return True
