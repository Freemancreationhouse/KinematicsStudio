from PySide6.QtWidgets import QFileDialog, QGridLayout, QPushButton, QWidget

from engine.commands import (
    SaveExchangeProfileCommand,
    StoreExchangeValidationReportCommand,
    UpdateExchangeSettingsCommand,
)
from engine.storage import ProjectTemplateManager
from ui_v2.exchange_dialogs import ExchangeExportDialog, ExchangeImportDialog, ExchangeValidationReportPanel
from ui_v2.import_options_dialog import ImportOptionsDialog


class ProjectRibbon(QWidget):
    """Ribbon section for project save, open, autosave and recovery actions."""

    def __init__(self, tool_manager):

        super().__init__()

        self.tool_manager = tool_manager
        layout = QGridLayout(self)

        buttons = [
            ("New Blank", self._new_blank),
            ("Architectural", self._new_architectural),
            ("Mechanical", self._new_mechanical),
            ("Save", self._save),
            ("Save As", self._save_as),
            ("Open", self._open),
            ("Export DXF", self._export_dxf),
            ("Export SVG", self._export_svg),
            ("Export PDF", self._export_pdf),
            ("Export PNG", self._export_png),
            ("Export EPS", self._export_eps),
            ("Export PSD", self._export_psd),
            ("Import 3D", self._import_3d),
            ("Import CAD", self._import_cad_exchange),
            ("Export CAD", self._export_cad_exchange),
            ("Validate Exchange", self._show_validation_report),
            ("Auto Save", self._toggle_autosave),
            ("Recover", self._recover),
        ]

        row = 0
        col = 0

        for text, callback in buttons:
            button = QPushButton(text)
            button.setMinimumHeight(42)
            button.setToolTip(self._tooltip(text))
            button.clicked.connect(callback)
            layout.addWidget(button, row, col)
            col += 1

            if col == 3:
                col = 0
                row += 1

        layout.setRowStretch(row + 1, 1)

    # --------------------------------

    def _save(self):

        app = self._app()

        if app is None:
            return

        if app.project_path is None:
            self._save_as()
            return

        app.save_project()
        self._refresh()

    # --------------------------------

    def _tooltip(self, text):

        hints = {
            "New Blank": "Create a blank project.",
            "Architectural": "Create a project from the architectural template.",
            "Mechanical": "Create a project from the mechanical template.",
            "Save": "Save the current project.",
            "Save As": "Save the current project to a chosen file.",
            "Open": "Open an existing Kinematics Studio project.",
            "Import 3D": "Import an external 3D reference through the ReferenceManager.",
            "Import CAD": "Import professional CAD exchange references through ImportManager.",
            "Export CAD": "Export professional CAD exchange data through ExportManager.",
            "Validate Exchange": "Show the latest import/export validation report.",
            "Auto Save": "Toggle background autosave.",
            "Recover": "Recover the latest autosave file when available.",
        }

        if text.startswith("Export "):
            return f"Export the current drawing as {text.removeprefix('Export ')}."

        return hints.get(text, text)

    # --------------------------------

    def _save_as(self):

        app = self._app()

        if app is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Kinematics Studio Project",
            "",
            "Kinematics Studio Project (*.ksproj)",
        )

        if path:
            app.save_project(path)
            self._refresh()

    # --------------------------------

    def _open(self):

        app = self._app()

        if app is None:
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Kinematics Studio Project",
            "",
            "Kinematics Studio Project (*.ksproj)",
        )

        if path:
            app.open_project(path)
            self._refresh(project_loaded=True)

    # --------------------------------

    def _new_blank(self):

        self._new_project(ProjectTemplateManager.BLANK)

    # --------------------------------

    def _new_architectural(self):

        self._new_project(ProjectTemplateManager.ARCHITECTURAL)

    # --------------------------------

    def _new_mechanical(self):

        self._new_project(ProjectTemplateManager.MECHANICAL)

    # --------------------------------

    def _new_project(self, template_name):

        app = self._app()

        if app is None:
            return

        app.new_project(template_name)
        self._refresh(project_loaded=True)

    # --------------------------------

    def _toggle_autosave(self):

        app = self._app()

        if app is None:
            return

        if app.autosave.enabled:
            app.autosave.stop()
        else:
            app.autosave.start()

        self._refresh()

    # --------------------------------

    def _export_dxf(self):

        self._export("dxf", "DXF Drawing (*.dxf)")

    # --------------------------------

    def _export_svg(self):

        self._export("svg", "SVG Drawing (*.svg)")

    # --------------------------------

    def _export_pdf(self):

        self._export("pdf", "PDF Drawing (*.pdf)")

    # --------------------------------

    def _export_png(self):

        self._export("png", "PNG Image (*.png)")

    # --------------------------------

    def _export_eps(self):

        self._export("eps", "EPS Vector Drawing (*.eps)")

    # --------------------------------

    def _export_psd(self):

        self._export("psd", "Photoshop Document (*.psd)")

    # --------------------------------

    def _export(self, format_name, file_filter):

        app = self._app()

        if app is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {format_name.upper()}",
            "",
            file_filter,
        )

        if path:
            if not path.lower().endswith(f".{format_name}"):
                path = f"{path}.{format_name}"

            app.export_project(path, format_name)
            self._refresh()

    # --------------------------------

    def _import_3d(self):

        app = self._app()

        if app is None:
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import 3D Reference",
            "",
            "3D References (*.obj *.stl *.ply *.off *.gltf *.glb *.fbx *.3ds *.step *.stp *.iges *.igs)",
        )

        if not path:
            return

        remembered = app.workspace.project_settings.get("import_options", {})
        dialog = ImportOptionsDialog(
            self,
            app.workspace.import_manager.last_result and getattr(
                app.workspace.import_manager.last_result,
                "settings",
                None,
            ) or None,
            path,
        )

        if remembered:
            from engine.import3d import ImportSettings

            dialog.set_settings(ImportSettings.from_dict(remembered))

        if dialog.exec() != dialog.Accepted:
            return

        settings = dialog.settings()
        app.workspace.import_manager.create_reference(app.workspace, path, None, settings)

        if settings.remember_settings:
            app.workspace.project_settings["import_options"] = settings.to_dict()

        self._refresh()

    # --------------------------------

    def _import_cad_exchange(self):

        app = self._app()

        if app is None:
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import CAD Exchange",
            "",
            "CAD Exchange (*.skp *.3dm *.step *.stp *.iges *.igs *.sat *.stl *.obj *.fbx *.abc)",
        )

        if not path:
            return

        remembered = app.workspace.import_manager.adapter_settings.get("cad_import", {})
        settings = None

        if remembered:
            from engine.import3d import ImportSettings

            settings = ImportSettings.from_dict(remembered)

        dialog = ExchangeImportDialog(self, app.workspace, path, settings)

        if dialog.exec() != dialog.Accepted:
            return

        import_settings = dialog.settings()
        app.workspace.import_manager.create_reference(app.workspace, path, None, import_settings)
        profile = {
            "units": import_settings.units,
            "scale": import_settings.scale,
            "up_axis": import_settings.up_axis,
            "forward_axis": import_settings.forward_axis,
        }
        app.workspace.command_manager.execute(SaveExchangeProfileCommand(
            app.workspace,
            dialog.profile_name(),
            profile,
        ))

        if import_settings.remember_settings:
            before = dict(app.workspace.import_manager.adapter_settings.get("cad_import", {}))
            app.workspace.command_manager.execute(UpdateExchangeSettingsCommand(
                app.workspace,
                "cad_import",
                before,
                import_settings.to_dict(),
            ))

        self._refresh()

    # --------------------------------

    def _export_cad_exchange(self):

        app = self._app()

        if app is None:
            return

        dialog = ExchangeExportDialog(self, app.workspace)

        if dialog.exec() != dialog.Accepted:
            return

        format_name = dialog.format_name()
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {format_name.upper()}",
            "",
            f"{format_name.upper()} Exchange (*.{format_name})",
        )

        if not path:
            return

        if not path.lower().endswith(f".{format_name}"):
            path = f"{path}.{format_name}"

        report = app.workspace.import_manager.validation_manager.validate_workspace(
            app.workspace,
            format_name,
        )
        app.workspace.command_manager.execute(StoreExchangeValidationReportCommand(app.workspace, report))
        app.export_project(path, format_name)
        before = dict(app.workspace.import_manager.adapter_settings.get("cad_export", {}))
        app.workspace.command_manager.execute(UpdateExchangeSettingsCommand(
            app.workspace,
            "cad_export",
            before,
            dialog.profile_settings(),
        ))
        self._refresh()

    # --------------------------------

    def _show_validation_report(self):

        app = self._app()

        if app is None:
            return

        panel = ExchangeValidationReportPanel(
            self,
            app.workspace.import_manager.validation_manager.last_report,
        )
        panel.exec()

    # --------------------------------

    def _recover(self):

        app = self._app()

        if app is None or not app.has_recovery():
            return

        app.recover_project()
        self._refresh(project_loaded=True)

    # --------------------------------

    def _app(self):

        return getattr(self.tool_manager, "app", None)

    # --------------------------------

    def _refresh(self, project_loaded=False):

        canvas = getattr(self.tool_manager, "canvas", None)

        if canvas is None:
            return

        if project_loaded and hasattr(canvas, "on_project_loaded"):
            canvas.on_project_loaded()
        elif hasattr(canvas, "on_project_state_changed"):
            canvas.on_project_state_changed()

        canvas._sync_selection_ui()
        canvas.update()
