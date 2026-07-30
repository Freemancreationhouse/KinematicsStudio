from __future__ import annotations

from typing import Any

from engine.commands import (
    RotateEntity3DCommand,
    ScaleEntity3DCommand,
    TranslateEntity3DCommand,
    UpdateConstraintCommand,
    UpdateEntityCommand,
    UpdateLayerCommand,
)


class PropertyCommandService:
    """Executes property edit requests through the active workspace commands."""

    def __init__(self, workspace_provider: Any) -> None:
        """Store the provider used to resolve the current active workspace."""

        self.workspace_provider = workspace_provider

    @property
    def workspace(self) -> Any:
        """Return the current active workspace."""

        provider = self.workspace_provider
        current_workspace = getattr(provider, "current_workspace", None)
        if callable(current_workspace):
            return current_workspace()

        current = getattr(provider, "current", None)
        if current is not None:
            return current

        workspace = getattr(provider, "workspace", None)
        if workspace is not None:
            return workspace

        return provider

    def execute(self, request: dict[str, Any]) -> Any:
        """Execute a property edit request through the active workspace."""

        request_type = request.get("type")

        if request_type == "entity_update":
            return self._execute_entity_update(request)
        if request_type == "constraint_update":
            return self._execute_constraint_update(request)
        if request_type == "layer_update":
            return self._execute_layer_update(request)
        if request_type == "translate_3d":
            return self._execute_translate_3d(request)
        if request_type == "rotate_3d":
            return self._execute_rotate_3d(request)
        if request_type == "scale_3d":
            return self._execute_scale_3d(request)
        if request_type == "workspace_3d_context":
            return self._execute_workspace_3d_context(request)

        return None

    def _execute_entity_update(self, request: dict[str, Any]) -> Any:
        """Execute an entity property update request."""

        workspace = self.workspace
        command = UpdateEntityCommand(
            request["entity"],
            workspace=workspace,
            before=dict(request["before"]),
            after=dict(request["after"]),
        )
        workspace.command_manager.execute(command)
        return command

    def _execute_constraint_update(self, request: dict[str, Any]) -> Any:
        """Execute a constraint property update request."""

        workspace = self.workspace
        command = UpdateConstraintCommand(
            workspace,
            request["constraint"],
            dict(request["before"]),
            dict(request["after"]),
        )
        workspace.command_manager.execute(command)
        return command

    def _execute_layer_update(self, request: dict[str, Any]) -> Any:
        """Execute a layer property update request."""

        workspace = self.workspace
        command = UpdateLayerCommand(
            workspace,
            request["layer"],
            dict(request["before"]),
            dict(request["after"]),
        )
        workspace.command_manager.execute(command)
        return command

    def _execute_translate_3d(self, request: dict[str, Any]) -> Any:
        """Execute a 3D translation request."""

        workspace = self.workspace
        command = TranslateEntity3DCommand(
            workspace,
            list(request["entities"]),
            request["delta"],
        )
        workspace.command_manager.execute(command)
        return command

    def _execute_rotate_3d(self, request: dict[str, Any]) -> Any:
        """Execute a 3D rotation request."""

        workspace = self.workspace
        entities = list(request["entities"])
        pivot = self._pivot_for(workspace, entities)
        command = RotateEntity3DCommand(
            workspace,
            entities,
            request["rotation"],
            pivot=pivot,
        )
        workspace.command_manager.execute(command)
        return command

    def _execute_scale_3d(self, request: dict[str, Any]) -> Any:
        """Execute a 3D scale request."""

        workspace = self.workspace
        entities = list(request["entities"])
        pivot = self._pivot_for(workspace, entities)
        command = ScaleEntity3DCommand(
            workspace,
            entities,
            request["scale"],
            pivot=pivot,
        )
        workspace.command_manager.execute(command)
        return command

    def _execute_workspace_3d_context(self, request: dict[str, Any]) -> bool:
        """Apply workspace-owned 3D context settings from a property request."""

        workspace = self.workspace
        text = str(request.get("text", ""))
        lower_tokens = text.strip().lower().split()
        raw_tokens = text.strip().split()
        changed = False

        gizmo = getattr(workspace, "transform_gizmo", None)
        if gizmo is not None:
            for token in lower_tokens:
                if token in ("world", "local"):
                    gizmo.set_coordinate_mode(token)
                    changed = True
                elif token in (
                    "center",
                    "origin",
                    "individual",
                    "bounding_box_center",
                ):
                    gizmo.set_pivot_mode(token)
                    changed = True

        coordinate_manager = getattr(workspace, "coordinate_system_manager", None)
        if coordinate_manager is not None:
            for token in raw_tokens:
                if token in coordinate_manager.names():
                    coordinate_manager.activate(token)
                    changed = True

        plane_manager = getattr(workspace, "construction_plane_manager", None)
        if plane_manager is not None:
            for token in raw_tokens:
                if token in plane_manager.names():
                    plane_manager.set_active(token)
                    changed = True

        return changed

    def _pivot_for(self, workspace: Any, entities: list[Any]) -> Any:
        """Return the active transform pivot for a list of entities."""

        gizmo = getattr(workspace, "transform_gizmo", None)
        if gizmo is None:
            return None
        return gizmo.pivot_for_selection(entities)
