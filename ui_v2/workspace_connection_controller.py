from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QFileDialog

from engine.commands import (
    CancelAITaskCommand,
    CancelManufacturingJobCommand,
    CaptureAIDiagnosticsCommand,
    CaptureAIContextCommand,
    CaptureMachineDiagnosticsCommand,
    CreateAISessionCommand,
    CreateMachineProfileCommand,
    CreateManufacturingJobCommand,
    ExecuteManufacturingJobCommand,
    ExportManufacturingJobCommand,
    GenerateToolpathCommand,
    PauseManufacturingJobCommand,
    PostProcessManufacturingJobCommand,
    QueueManufacturingJobCommand,
    ResumeManufacturingJobCommand,
    RetryAIPromptCommand,
    SaveExchangeProfileCommand,
    SimulateManufacturingJobCommand,
    StoreExchangeValidationReportCommand,
    SubmitAIPromptCommand,
    UpdateExchangeSettingsCommand,
    ValidateAIProvidersCommand,
    ValidateAIPromptCommand,
    CreatePrimitiveCommand,
)
from engine.commands.delete_command import DeleteCommand
from engine.commands.occ_boolean_command import OCCBooleanCommand
from engine.commands.occ_import_command import ImportOCCShapeCommand
from engine.geometry import BoundingBox, BoundingBox3D, Vector2, Vector3
from engine.storage import ProjectTemplateManager
from ui_v2.exchange_dialogs import (
    ExchangeExportDialog,
    ExchangeImportDialog,
    ExchangeValidationReportPanel,
)
from ui_v2.import_options_dialog import ImportOptionsDialog


class WorkspaceConnectionController(QObject):
    """Central UI orchestration layer for injected workspace shell objects."""

    panelsRequested = Signal()
    focusModeRequested = Signal()
    actionRequested = Signal(str)
    commandEntered = Signal(str)

    PRIMITIVE_TOOL_SPECS = {
        "CubePrimitiveTool": ("cube", {"size": 100.0}),
        "BoxPrimitiveTool": ("box", {"width": 100.0, "depth": 80.0, "height": 60.0}),
        "SpherePrimitiveTool": ("sphere", {"radius": 50.0, "segments": 24, "rings": 12}),
        "ConePrimitiveTool": ("cone", {"radius": 50.0, "height": 100.0, "segments": 24}),
        "CylinderPrimitiveTool": ("cylinder", {"radius": 50.0, "height": 100.0, "segments": 24}),
        "PlanePrimitiveTool": ("plane", {"width": 100.0, "depth": 100.0}),
        "TorusPrimitiveTool": (
            "torus",
            {
                "major_radius": 60.0,
                "minor_radius": 15.0,
                "major_segments": 24,
                "minor_segments": 12,
            },
        ),
        "PyramidPrimitiveTool": ("pyramid", {"width": 100.0, "depth": 100.0, "height": 100.0}),
        "PrismPrimitiveTool": ("prism", {"radius": 50.0, "height": 100.0, "sides": 6}),
        "CapsulePrimitiveTool": ("capsule", {"radius": 30.0, "height": 120.0, "segments": 24, "rings": 12}),
    }

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
        project_service: Any | None = None,
        property_command_service: Any | None = None,
        selection_service: Any | None = None,
        viewport_synchronization_service: Any | None = None,
        command_manager: Any | None = None,
        workspace: Any | None = None,
        workspace_provider: Any | None = None,
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
        self.project_service = project_service
        self.property_command_service = property_command_service
        self.selection_service = selection_service
        self.viewport_synchronization_service = viewport_synchronization_service
        self.app = app
        self.tool_manager = tool_manager
        self.workspace_provider = workspace_provider or app or workspace
        self._fallback_command_manager = command_manager

        self._qt_connections: list[tuple[Any, Callable[..., Any]]] = []
        self._previous_callbacks: dict[tuple[int, str], tuple[Any, str, Any]] = {}
        self._connected = False
        self._property_edit_connected = False
        self._project_lifecycle_connected = False
        self._has_activated_3d_view = False

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
        self._connect_project_lifecycle()
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
        if self._project_lifecycle_connected:
            self._call_if_available(
                self.project_service,
                "remove_lifecycle_callback",
                self._handle_project_service_lifecycle,
            )
        self._connected = False
        self._property_edit_connected = False
        self._project_lifecycle_connected = False

    def refresh_all(self) -> None:
        """Refresh all synchronized UI surfaces."""

        self.synchronize_ui("FullRefresh")

    def synchronize_ui(self, event_name: str, payload: Any | None = None) -> None:
        """Synchronize UI surfaces for one application event."""

        surfaces = self._synchronization_surfaces(event_name)
        if "property_panel" in surfaces:
            self._update_property_panel()
        if "status_bar" in surfaces:
            self._update_status_bar(payload)
        if "panels" in surfaces:
            self._refresh_panels()
        if "viewport" in surfaces:
            self._refresh_viewport(event_name, payload)

    def _synchronization_surfaces(self, event_name: str) -> set[str]:
        """Return the UI surfaces affected by a synchronization event."""

        all_surfaces = {"property_panel", "status_bar", "panels", "viewport"}
        event_map = {
            "FullRefresh": all_surfaces,
            "ProjectOpened": all_surfaces,
            "ProjectClosed": all_surfaces,
            "WorkspaceChanged": all_surfaces,
            "SceneChanged": {"status_bar", "panels", "viewport"},
            "EntityAdded": {"status_bar", "panels", "viewport"},
            "EntityRemoved": {"status_bar", "panels", "viewport"},
            "EntityModified": {"status_bar", "panels", "viewport"},
            "SelectionChanged": {"property_panel", "status_bar", "viewport"},
            "CameraChanged": {"status_bar", "viewport"},
            "ActiveToolChanged": {"property_panel", "status_bar"},
            "DocumentModified": {"status_bar", "panels", "viewport"},
            "CommandHistoryChanged": {"status_bar", "panels", "viewport"},
            "PropertyChanged": {"property_panel", "status_bar", "panels", "viewport"},
            "LayerChanged": {"property_panel", "status_bar", "panels", "viewport"},
            "ViewChanged": {"status_bar", "viewport"},
            "PanelChanged": {"status_bar"},
        }
        return set(event_map.get(event_name, all_surfaces))

    def route_action(self, action_id: str) -> None:
        """Route a public workspace action without exposing widget internals."""

        if action_id.startswith("panel:"):
            self._toggle_panel(action_id.removeprefix("panel:"))
            return
        if action_id == "view_2d":
            self._sync_2d_center_from_3d()
            self._call_if_available(self.viewport_area, "show_2d")
            self._call_if_available(self.left_toolbox, "set_active_action", action_id)
            self._focus_active_view()
            self.synchronize_ui("ViewChanged")
            return
        if action_id == "view_3d":
            self._sync_3d_target_from_2d()
            self._call_if_available(self.viewport_area, "show_3d")
            if not self._has_activated_3d_view:
                self._zoom_extents_3d()
                self._has_activated_3d_view = True
            self._call_if_available(self.left_toolbox, "set_active_action", action_id)
            self._focus_active_view()
            self.synchronize_ui("ViewChanged")
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
        if action_id == "command:delete":
            self._delete_selection()
            return

        self._handle_action(action_id)

    def _connect_ribbon(self) -> None:
        """Connect ribbon-level action signals when exposed by the ribbon."""

        self._connect_signal(
            getattr(self.ribbon, "actionTriggered", None),
            self.route_action,
        )
        self._connect_signal(
            getattr(self.ribbon, "toolSelected", None),
            self._handle_tool_selected,
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
        self._connect_signal(
            getattr(self._canvas(), "deleteRequested", None),
            self._delete_selection,
        )
        self._connect_signal(
            getattr(self._viewport3d(), "deleteRequested", None),
            self._delete_selection,
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
            self.workspace_provider,
            self._handle_property_changed,
        )
        if not self._property_edit_connected:
            self._connect_signal(
                getattr(self.property_panel, "editRequested", None),
                self._handle_property_edit_requested,
            )
            self._property_edit_connected = True

        service_selection = getattr(self.selection_service, "selection", None)
        selection = (
            service_selection()
            if callable(service_selection)
            else getattr(self.workspace, "selection", None)
        )
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

    def _connect_project_lifecycle(self) -> None:
        """Refresh routed UI state after project-service lifecycle operations."""

        if not self._project_lifecycle_connected:
            self._call_if_available(
                self.project_service,
                "add_lifecycle_callback",
                self._handle_project_service_lifecycle,
            )
            self._project_lifecycle_connected = True

    def _update_property_panel(self) -> None:
        """Push current selection state into the property panel."""

        selection = self._current_selection()
        if self._call_if_available(self.property_panel, "show_selection", selection):
            return
        self._call_if_available(self.property_panel, "refresh")

    def _update_status_bar(self, payload: Any | None = None) -> None:
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
        tool = payload if payload is not None else active_tool
        if tool is not None:
            self._call_if_available(self.status_bar, "show_tool", tool)

    def _refresh_panels(self) -> None:
        """Refresh all opened on-demand panels through the panel manager."""

        self._call_if_available(self.panel_manager, "refresh_all")

    def _refresh_viewport(
        self,
        event_name: str = "FullRefresh",
        payload: Any | None = None,
    ) -> None:
        """Refresh synchronized viewports when a state event needs repaint."""

        if self.viewport_synchronization_service is not None:
            self._call_if_available(
                self.viewport_synchronization_service,
                "synchronize",
                event_name,
                payload,
            )
            return

        for accessor_name in ("canvas", "viewport3d"):
            accessor = getattr(self.viewport_area, accessor_name, None)
            viewport = accessor() if callable(accessor) else accessor
            self._call_if_available(viewport, "update")

    def _handle_left_toolbox_action(self, action_id: str) -> None:
        """Route an action emitted by the left toolbox."""

        self.route_action(action_id)

    def _handle_action(self, action_id: str) -> None:
        """Route a generic action request through application services."""

        if action_id.startswith("project:new:"):
            self._new_project(action_id.removeprefix("project:new:"))
            return
        if action_id == "project:open":
            self._open_project()
            return
        if action_id == "project:save":
            self._save_project()
            return
        if action_id == "project:save_as":
            self._save_project_as()
            return
        if action_id == "project:close":
            self._close_project()
            return
        if action_id == "project:recover":
            self._recover_project()
            return
        if action_id == "project:toggle_autosave":
            self._toggle_autosave()
            return
        if action_id == "import:3d":
            self._import_3d()
            return
        if action_id == "import:cad_exchange":
            self._import_cad_exchange()
            return
        if action_id == "export:cad_exchange":
            self._export_cad_exchange()
            return
        if action_id.startswith("export:"):
            self._export_project(action_id.removeprefix("export:"))
            return
        if action_id == "exchange:show_validation_report":
            self._show_validation_report()
            return
        if action_id == "command:undo":
            self._undo()
            return
        if action_id == "command:redo":
            self._redo()
            return
        if action_id == "view:fit":
            self._fit_view()
            return
        if action_id == "view:home":
            self._home_view()
            return
        if action_id == "view:zoom_extents":
            self._zoom_extents()
            return
        if action_id == "view:zoom_selected":
            self._zoom_selected()
            return
        if action_id.startswith("boolean:"):
            self._boolean(action_id.removeprefix("boolean:"))
            return
        if action_id.startswith("ai:"):
            self._route_ai_action(action_id.removeprefix("ai:"))
            return
        if action_id.startswith("machine:"):
            self._route_machine_action(action_id.removeprefix("machine:"))
            return

        self.actionRequested.emit(action_id)

    def _handle_tool_selected(self, tool_name: str) -> None:
        """Activate a tool selected by a presentation widget."""

        self._call_if_available(self.tool_manager, "activate", tool_name)
        if tool_name in self.PRIMITIVE_TOOL_SPECS:
            self._create_primitive(tool_name)
            return
        self.synchronize_ui("ActiveToolChanged")

    def _create_primitive(self, tool_name: str) -> None:
        """Create a 3D primitive through the existing command pipeline."""

        workspace = self.workspace
        command_manager = getattr(workspace, "command_manager", None)
        if workspace is None or command_manager is None:
            return

        primitive_type, parameters = self.PRIMITIVE_TOOL_SPECS[tool_name]
        command = CreatePrimitiveCommand(
            workspace,
            primitive_type,
            dict(parameters),
            name=f"{primitive_type.title()} Primitive",
        )
        command_manager.execute(command)
        self._call_if_available(self.project_service, "mark_dirty")
        self.synchronize_ui("EntityAdded", command.entity)
        self.synchronize_ui("SelectionChanged", command.entity)

    def _new_project(self, template_name: str) -> None:
        """Create a project through the project service."""

        template_map = {
            "blank": ProjectTemplateManager.BLANK,
            "architectural": ProjectTemplateManager.ARCHITECTURAL,
            "mechanical": ProjectTemplateManager.MECHANICAL,
        }
        self._call_if_available(
            self.project_service,
            "new_project",
            template_map.get(template_name, template_name),
        )

    def _open_project(self) -> None:
        """Open a project selected by the user."""

        service = self.project_service
        if service is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self._dialog_parent(),
            "Open Kinematics Studio Project",
            "",
            "Kinematics Studio Project (*.ksproj)",
        )
        if path:
            service.open_project(path)

    def _save_project(self) -> None:
        """Save the active project through the application facade."""

        service = self.project_service
        if service is None:
            return
        if service.project_path() is None:
            self._save_project_as()
            return
        service.save()

    def _save_project_as(self) -> None:
        """Save the active project to a user-selected path."""

        service = self.project_service
        if service is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self._dialog_parent(),
            "Save Kinematics Studio Project",
            "",
            "Kinematics Studio Project (*.ksproj)",
        )
        if path:
            service.save_as(path)

    def _recover_project(self) -> None:
        """Recover the latest autosave when one exists."""

        service = self.project_service
        if service is not None and service.has_recovery():
            service.recover_project()

    def _close_project(self) -> None:
        """Close the active project through the project service."""

        self._call_if_available(self.project_service, "close_project")

    def _toggle_autosave(self) -> None:
        """Toggle autosave through the application facade."""

        service = self.project_service
        if service is None:
            return
        if service.autosave_enabled():
            service.set_autosave_enabled(False)
            self._show_status("Autosave disabled.")
        else:
            service.set_autosave_enabled(True)
            self._show_status("Autosave enabled.")

    def _export_project(self, format_name: str) -> None:
        """Export the active project through the application facade."""

        filters = {
            "dxf": "DXF Drawing (*.dxf)",
            "svg": "SVG Drawing (*.svg)",
            "pdf": "PDF Drawing (*.pdf)",
            "png": "PNG Image (*.png)",
        }
        file_filter = filters.get(format_name, f"{format_name.upper()} (*.{format_name})")
        app = self.app
        if app is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self._dialog_parent(),
            f"Export {format_name.upper()}",
            "",
            file_filter,
        )
        if path:
            if not path.lower().endswith(f".{format_name}"):
                path = f"{path}.{format_name}"
            app.export_project(path, format_name)

    def _import_3d(self) -> None:
        """Import an external 3D reference through the active workspace."""

        workspace = self.workspace
        if workspace is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self._dialog_parent(),
            "Import 3D Reference",
            "",
            "3D References (*.obj *.stl *.ply *.off *.gltf *.glb *.fbx *.3ds *.step *.stp *.iges *.igs)",
        )
        if not path:
            return

        remembered = workspace.project_settings.get("import_options", {})
        dialog = ImportOptionsDialog(
            self._dialog_parent(),
            workspace.import_manager.last_result
            and getattr(workspace.import_manager.last_result, "settings", None)
            or None,
            path,
        )
        if remembered:
            from engine.import3d import ImportSettings

            dialog.set_settings(ImportSettings.from_dict(remembered))

        if dialog.exec() != dialog.Accepted:
            return

        settings = dialog.settings()
        workspace.import_manager.create_reference(
            workspace,
            path,
            None,
            settings,
        )
        if settings.remember_settings:
            workspace.project_settings["import_options"] = settings.to_dict()

    def _import_cad_exchange(self) -> None:
        """Import professional CAD exchange references."""

        app = self.app
        workspace = self.workspace
        if app is None or workspace is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self._dialog_parent(),
            "Import CAD Exchange",
            "",
            "CAD Exchange (*.skp *.3dm *.step *.stp *.brep *.iges *.igs *.sat *.stl *.obj *.fbx *.abc)",
        )
        if not path:
            return

        settings = None
        remembered = workspace.import_manager.adapter_settings.get("cad_import", {})
        if remembered:
            from engine.import3d import ImportSettings

            settings = ImportSettings.from_dict(remembered)

        dialog = ExchangeImportDialog(self._dialog_parent(), workspace, path, settings)
        if dialog.exec() != dialog.Accepted:
            return

        import_settings = dialog.settings()
        is_occ_exchange = Path(path).suffix.lower() in (".step", ".stp", ".brep")

        if is_occ_exchange:
            workspace.command_manager.execute(
                ImportOCCShapeCommand(app.engine, workspace, path)
            )
        else:
            workspace.import_manager.create_reference(
                workspace,
                path,
                None,
                import_settings,
            )

        profile = {
            "units": import_settings.units,
            "scale": import_settings.scale,
            "up_axis": import_settings.up_axis,
            "forward_axis": import_settings.forward_axis,
        }
        workspace.command_manager.execute(
            SaveExchangeProfileCommand(
                workspace,
                dialog.profile_name(),
                profile,
            )
        )
        if import_settings.remember_settings:
            before = dict(workspace.import_manager.adapter_settings.get("cad_import", {}))
            workspace.command_manager.execute(
                UpdateExchangeSettingsCommand(
                    workspace,
                    "cad_import",
                    before,
                    import_settings.to_dict(),
                )
            )

    def _export_cad_exchange(self) -> None:
        """Export professional CAD exchange data."""

        app = self.app
        workspace = self.workspace
        if app is None or workspace is None:
            return
        dialog = ExchangeExportDialog(self._dialog_parent(), workspace)
        if dialog.exec() != dialog.Accepted:
            return

        format_name = dialog.format_name()
        extension = "step" if format_name == "step" else format_name
        path, _ = QFileDialog.getSaveFileName(
            self._dialog_parent(),
            f"Export {format_name.upper()}",
            "",
            f"{format_name.upper()} Exchange (*.{extension})",
        )
        if not path:
            return
        if not path.lower().endswith(f".{extension}"):
            path = f"{path}.{extension}"

        report = workspace.import_manager.validation_manager.validate_workspace(
            workspace,
            format_name,
        )
        workspace.command_manager.execute(
            StoreExchangeValidationReportCommand(workspace, report)
        )
        if format_name in ("step", "brep"):
            app.engine.export_model(path)
        else:
            app.export_project(path, format_name)

        before = dict(workspace.import_manager.adapter_settings.get("cad_export", {}))
        workspace.command_manager.execute(
            UpdateExchangeSettingsCommand(
                workspace,
                "cad_export",
                before,
                dialog.profile_settings(),
            )
        )

    def _show_validation_report(self) -> None:
        """Show the latest import/export validation report."""

        workspace = self.workspace
        if workspace is None:
            return
        panel = ExchangeValidationReportPanel(
            self._dialog_parent(),
            workspace.import_manager.validation_manager.last_report,
        )
        panel.exec()

    def _undo(self) -> None:
        """Undo the latest command."""

        manager = self.command_manager
        if manager is not None:
            manager.undo()

    def _redo(self) -> None:
        """Redo the latest command."""

        manager = self.command_manager
        if manager is not None:
            manager.redo()

    def _delete_selection(self) -> None:
        """Delete the current selection through the active command manager."""

        workspace = self.workspace
        manager = self.command_manager
        if workspace is None or manager is None:
            return

        selected = [
            entity
            for entity in list(self._current_selection() or [])
            if entity is not None
        ]
        if not selected:
            return

        engine = getattr(self.app, "engine", None)
        shapes = []
        occ = getattr(engine, "occ", None) if engine is not None else None
        if occ is not None:
            shapes = getattr(occ, "shapes", [])
            if callable(shapes):
                shapes = shapes()
            if shapes is None:
                shapes = []

        for entity in selected:
            command_target = (
                engine
                if occ is not None and entity in shapes
                else workspace
            )
            manager.execute(DeleteCommand(command_target, entity))

        selection = getattr(workspace, "selection", None)
        if selection is not None:
            self._call_if_available(selection, "clear")
        self._call_if_available(self.project_service, "mark_dirty")
        self.synchronize_ui("EntityRemoved")
        self.synchronize_ui("SelectionChanged")
        self.synchronize_ui("CommandHistoryChanged")

    def _fit_view(self) -> None:
        """Fit the active viewport view."""

        self._zoom_extents()

    def _zoom_extents(self) -> None:
        """Zoom the active viewport to model extents."""

        if self._is_3d_active():
            self._zoom_extents_3d()
        else:
            self._zoom_extents_2d()
        self.synchronize_ui("CameraChanged")

    def _home_view(self) -> None:
        """Reset 2D and 3D cameras to the production home view."""

        canvas = self._canvas()
        if canvas is not None:
            self._call_if_available(canvas, "home_view")

        camera3d = getattr(self.app, "camera3d", None)
        if camera3d is not None:
            self._call_if_available(camera3d, "home_view")

        self._refresh_viewport("CameraChanged")
        self._update_status_bar()

    def _zoom_extents_2d(self) -> None:
        """Zoom the 2D canvas to workspace extents."""

        canvas = self._canvas()
        if canvas is not None:
            canvas.zoom_extents()

    def _zoom_extents_3d(self) -> None:
        """Zoom the 3D camera to shared workspace extents."""

        camera3d = getattr(self.app, "camera3d", None)
        if camera3d is None:
            return

        camera3d.fit_bounds(self._workspace_bounds3d())
        self._call_if_available(self._viewport3d(), "update")

    def _zoom_selected(self) -> None:
        """Zoom the active viewport to the current selection."""

        selected = list(self._current_selection() or [])
        if not selected:
            self._zoom_extents()
            return

        if self._is_3d_active():
            camera3d = getattr(self.app, "camera3d", None)
            if camera3d is not None:
                camera3d.fit_bounds(self._bounds3d(selected))
                self._call_if_available(self._viewport3d(), "update")
        else:
            canvas = self._canvas()
            camera = getattr(canvas, "camera", None)
            if canvas is not None and camera is not None:
                camera.fit_to_bounds(
                    self._bounds2d(selected),
                    canvas.width(),
                    canvas.height(),
                )
                self._call_if_available(canvas, "update")

        self.synchronize_ui("CameraChanged")

    def _boolean(self, operation: str) -> None:
        """Execute a Boolean operation on two selected OCC solids."""

        app = self.app
        workspace = self.workspace
        engine = getattr(app, "engine", None)
        if app is None or workspace is None or engine is None:
            return

        shapes = getattr(getattr(engine, "occ", None), "shapes", [])
        selected = [
            item
            for item in list(workspace.selection.selected)
            if item in shapes
        ]
        if len(selected) != 2:
            self._show_status("Select exactly two OCC solids for Boolean operation.")
            return

        workspace.command_manager.execute(
            OCCBooleanCommand(engine, workspace, operation, selected[0], selected[1])
        )
        self._show_status(f"Boolean {operation} completed.")

    def _route_ai_action(self, action_id: str) -> None:
        """Route AI ribbon actions through workspace commands."""

        handlers = {
            "capture_context": self._capture_context,
            "new_session": self._new_ai_session,
            "validate_prompt": self._validate_prompt,
            "queue_prompt": self._queue_prompt,
            "cancel_task": self._cancel_ai_task,
            "retry_task": self._retry_ai_task,
            "validate_providers": self._validate_providers,
            "diagnostics": self._ai_diagnostics,
        }
        handler = handlers.get(action_id)
        if handler is not None:
            handler()

    def _capture_context(self) -> None:
        """Capture AI project context."""

        self._execute_ai(
            CaptureAIContextCommand(
                self._ai_engine(),
                self.workspace,
                "AI Ribbon Context",
            ),
            "AI context captured.",
        )

    def _new_ai_session(self) -> None:
        """Create an AI session."""

        self._execute_ai(
            CreateAISessionCommand(
                self._ai_engine(),
                self.workspace,
                "AI Ribbon Session",
            ),
            "AI session created.",
        )

    def _validate_prompt(self) -> None:
        """Validate the default AI prompt."""

        self._execute_ai(
            ValidateAIPromptCommand(
                self._ai_engine(),
                self.workspace,
                self._default_prompt(),
                capability="chat",
            ),
            "AI prompt validation completed.",
        )

    def _queue_prompt(self) -> None:
        """Queue the default AI prompt."""

        self._execute_ai(
            SubmitAIPromptCommand(
                self._ai_engine(),
                self.workspace,
                self._default_prompt(),
                capability="chat",
                background=True,
            ),
            "AI prompt queued.",
        )

    def _cancel_ai_task(self) -> None:
        """Cancel the latest AI task."""

        task = self._latest_ai_task()
        if task is None:
            self._show_status("No AI task is available to cancel.")
            return
        self._execute_ai(
            CancelAITaskCommand(self._ai_engine(), self.workspace, task.id),
            "AI task cancellation requested.",
        )

    def _retry_ai_task(self) -> None:
        """Retry the latest AI task."""

        task = self._latest_ai_task()
        if task is None:
            self._show_status("No AI task is available to retry.")
            return
        self._execute_ai(
            RetryAIPromptCommand(self._ai_engine(), self.workspace, task.id),
            "AI task retry submitted.",
        )

    def _validate_providers(self) -> None:
        """Validate AI providers."""

        self._execute_ai(
            ValidateAIProvidersCommand(self._ai_engine(), self.workspace),
            "AI provider validation completed.",
        )

    def _ai_diagnostics(self) -> None:
        """Capture AI diagnostics."""

        self._execute_ai(
            CaptureAIDiagnosticsCommand(self._ai_engine(), self.workspace),
            "AI diagnostics captured.",
        )

    def _execute_ai(self, command: Any, message: str) -> None:
        """Execute an AI command through the workspace command manager."""

        workspace = self.workspace
        if workspace is None or command is None:
            return
        workspace.command_manager.execute(command)
        self._show_status(message)

    def _latest_ai_task(self) -> Any:
        """Return the latest AI runtime task."""

        runtime = getattr(self._ai_engine(), "runtime", None)
        tasks = list(getattr(runtime, "tasks", {}).values())
        return tasks[-1] if tasks else None

    def _default_prompt(self) -> str:
        """Return the default engineering AI prompt."""

        return "Review the current project context and report infrastructure readiness."

    def _ai_engine(self) -> Any:
        """Return the active AI engine when available."""

        return getattr(getattr(self.app, "engine", None), "ai_engine", None)

    def _route_machine_action(self, action_id: str) -> None:
        """Route Machine/CAM ribbon actions through workspace commands."""

        factories = {
            "profile": CreateMachineProfileCommand,
            "create_job": CreateManufacturingJobCommand,
            "generate_toolpath": GenerateToolpathCommand,
            "simulate": SimulateManufacturingJobCommand,
            "post_process": PostProcessManufacturingJobCommand,
            "export": ExportManufacturingJobCommand,
            "queue_job": QueueManufacturingJobCommand,
            "execute_job": ExecuteManufacturingJobCommand,
            "pause": PauseManufacturingJobCommand,
            "resume": ResumeManufacturingJobCommand,
            "cancel_job": CancelManufacturingJobCommand,
            "diagnostics": CaptureMachineDiagnosticsCommand,
        }
        messages = {
            "profile": "Machine profile ready.",
            "create_job": "Manufacturing job created.",
            "generate_toolpath": "Toolpath generated.",
            "simulate": "Manufacturing simulation completed.",
            "post_process": "G-code generated.",
            "export": "Manufacturing program exported.",
            "queue_job": "Manufacturing job queued.",
            "execute_job": "Manufacturing job execution started.",
            "pause": "Manufacturing job paused.",
            "resume": "Manufacturing job resumed.",
            "cancel_job": "Manufacturing job cancelled.",
            "diagnostics": "Machine/CAM diagnostics captured.",
        }
        factory = factories.get(action_id)
        if factory is not None:
            self._execute_machine(factory(self.workspace), messages[action_id])

    def _execute_machine(self, command: Any, message: str) -> None:
        """Execute a Machine/CAM command through the command manager."""

        workspace = self.workspace
        if workspace is None or command is None:
            return
        workspace.command_manager.execute(command)
        self._show_status(message)

    def _show_status(self, message: str) -> None:
        """Show a routed status-bar message."""

        self._call_if_available(self.status_bar, "show_status_text", message)

    def _canvas(self) -> Any:
        """Return the active 2D canvas when exposed by the viewport area."""

        canvas = getattr(self.viewport_area, "canvas", None)
        if callable(canvas):
            return canvas()
        return canvas

    def _dialog_parent(self) -> Any:
        """Return a stable parent widget for routed dialogs."""

        parent = self.parent()
        return parent if parent is not None else self.ribbon

    def _handle_active_view_changed(self, view_name: str) -> None:
        """Update UI state after the active viewport changes."""

        if view_name == "2d":
            self._call_if_available(self.left_toolbox, "set_active_action", "view_2d")
        elif view_name == "3d":
            self._call_if_available(self.left_toolbox, "set_active_action", "view_3d")
        self.synchronize_ui("ViewChanged")

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

        self.synchronize_ui("CommandHistoryChanged")

    def _handle_tool_changed(self, tool: Any = None, *args: Any) -> None:
        """Refresh shell state when the active tool changes."""

        if tool is None:
            tool = getattr(self.tool_manager, "active_tool", None)
        self.synchronize_ui("ActiveToolChanged", tool)

    def _handle_selection_changed(self, *args: Any) -> None:
        """Refresh shell state when selection changes."""

        self.synchronize_ui("SelectionChanged")

    def _handle_property_changed(self, *args: Any) -> None:
        """Refresh routed shell state after a property edit."""

        self.synchronize_ui("PropertyChanged")

    def _handle_property_edit_requested(self, request: Any) -> None:
        """Execute a property-panel edit through the application service."""

        service = self.property_command_service
        if service is None:
            return
        self._call_if_available(service, "execute", request)
        self.synchronize_ui("DocumentModified")

    def _handle_project_loaded(self, *args: Any) -> None:
        """Refresh routed shell state after project loading."""

        event_name = self._project_synchronization_event(args)
        lifecycle_event = str(args[0]) if args else ""
        self._has_activated_3d_view = (
            lifecycle_event in ("open_project", "recover_project") and
            self._workspace_has_3d_camera_state()
        )
        self._connect_command_manager()
        self._connect_workspace()
        self._call_if_available(
            self.property_panel,
            "set_workspace",
            self.workspace_provider,
            self._handle_property_changed,
        )
        if lifecycle_event in ("new_project", "close_project"):
            self._home_view()
        self.synchronize_ui(event_name)

    def _handle_project_service_lifecycle(self, *args: Any) -> None:
        """Refresh routed shell state after project-service lifecycle events."""

        self._handle_project_loaded(*args)

    def _project_synchronization_event(self, args: tuple[Any, ...]) -> str:
        """Return the UI synchronization event for a project lifecycle callback."""

        lifecycle_event = str(args[0]) if args else ""
        if lifecycle_event in ("new_project", "open_project", "recover_project"):
            return "ProjectOpened"
        if lifecycle_event == "close_project":
            return "ProjectClosed"
        if lifecycle_event == "save_project":
            return "DocumentModified"
        return "WorkspaceChanged"

    def _handle_panel_opened(self, *args: Any) -> None:
        """Refresh status after a panel is opened."""

        self.synchronize_ui("PanelChanged")

    def _handle_panel_closed(self, *args: Any) -> None:
        """Refresh status after a panel is closed."""

        self.synchronize_ui("PanelChanged")

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

    def _is_3d_active(self) -> bool:
        """Return True when the active viewport is the injected 3D viewport."""

        active_view_method = getattr(self.viewport_area, "active_view", None)
        active_view = active_view_method() if callable(active_view_method) else None
        return active_view is self._viewport3d()

    def _viewport3d(self) -> Any:
        """Return the injected 3D viewport widget when available."""

        accessor = getattr(self.viewport_area, "viewport3d", None)
        return accessor() if callable(accessor) else accessor

    def _sync_3d_target_from_2d(self) -> None:
        """Preserve the 2D view center as the 3D camera target when switching."""

        canvas = self._canvas()
        camera = getattr(canvas, "camera", None)
        camera3d = getattr(self.app, "camera3d", None)
        if canvas is None or camera is None or camera3d is None:
            return

        center = camera.screen_to_world(
            Vector2(canvas.width() * 0.5, canvas.height() * 0.5)
        )
        camera3d.state.target = Vector3(
            center.x,
            center.y,
            getattr(camera3d.state.target, "z", 0.0),
        )

    def _sync_2d_center_from_3d(self) -> None:
        """Preserve the 3D camera target as the 2D view center when switching."""

        canvas = self._canvas()
        camera = getattr(canvas, "camera", None)
        camera3d = getattr(self.app, "camera3d", None)
        if canvas is None or camera is None or camera3d is None:
            return

        target = camera3d.state.target
        camera.position = Vector2(
            target.x - canvas.width() / (2 * max(camera.zoom, 0.01)),
            target.y - canvas.height() / (2 * max(camera.zoom, 0.01)),
        )

    def _workspace_bounds3d(self) -> Any:
        """Return 3D bounds for visible shared-scene entities."""

        workspace = self.workspace
        entities = (
            workspace.visible_3d_entities()
            if workspace is not None and hasattr(workspace, "visible_3d_entities")
            else []
        )
        return self._bounds3d(entities)

    def _workspace_has_3d_camera_state(self) -> bool:
        """Return True when the active workspace has persisted 3D camera data."""

        workspace = self.workspace
        settings = getattr(workspace, "project_settings", {}) if workspace is not None else {}
        view_state = settings.get("view3d", {}) if isinstance(settings, dict) else {}
        return bool(isinstance(view_state, dict) and view_state.get("camera"))

    def _bounds3d(self, entities: Any) -> Any:
        """Build 3D bounds from entity bounding boxes."""

        bounds = BoundingBox3D()
        for entity in entities:
            box = getattr(entity, "bounding_box3d", None)
            if callable(box):
                box = box()
            if box is None or not getattr(box, "valid", False):
                continue
            for corner in box.corners():
                bounds.add(corner)
        return bounds

    def _bounds2d(self, entities: Any) -> Any:
        """Build 2D bounds from entity projected bounding boxes."""

        bounds = BoundingBox()
        for entity in entities:
            box = getattr(entity, "bounding_box", None)
            if callable(box):
                box = box()
            if box is None:
                continue
            bounds.add(box.min)
            bounds.add(box.max)
        if bounds.min.x == float("inf"):
            return None
        return bounds

    def _current_selection(self) -> Any:
        """Return the current workspace selection payload."""

        selected = getattr(self.selection_service, "selected", None)
        if callable(selected):
            return selected()

        selection = getattr(self.workspace, "selection", None)
        if selection is None:
            return None
        selected = getattr(selection, "selected", selection)
        if callable(selected):
            return selected()
        return selected

    @property
    def workspace(self) -> Any:
        """Return the current active workspace without storing it."""

        provider = self.workspace_provider
        if provider is None:
            return None

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

    @property
    def command_manager(self) -> Any:
        """Return the command manager for the current active workspace."""

        workspace = self.workspace
        manager = getattr(workspace, "command_manager", None)
        if manager is not None:
            return manager
        return self._fallback_command_manager

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

    def _chain_method(
        self,
        obj: Any,
        method_name: str,
        after_call: Callable[..., Any],
    ) -> None:
        """Wrap an object method and run a callback after successful execution."""

        if obj is None or not hasattr(obj, method_name):
            return

        key = (id(obj), method_name)
        if key in self._previous_callbacks:
            return

        previous = getattr(obj, method_name)
        if not callable(previous):
            return

        self._previous_callbacks[key] = (obj, method_name, previous)

        def chained_method(*args: Any, **kwargs: Any) -> Any:
            result = previous(*args, **kwargs)
            after_call(result)
            return result

        setattr(obj, method_name, chained_method)

    def _call_if_available(self, obj: Any, method_name: str, *args: Any) -> bool:
        """Call a named method when present and callable."""

        method = getattr(obj, method_name, None)
        if not callable(method):
            return False
        method(*args)
        return True
