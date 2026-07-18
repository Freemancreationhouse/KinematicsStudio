from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from engine.commands import (
    RemoveReferenceModelCommand,
    SetReferenceIsolationCommand,
    UnloadReferenceCommand,
    UpdateReferenceModelCommand,
)
from engine.import3d import ImportSettings
from ui_v2.import_options_dialog import ImportOptionsDialog


class ReferenceBrowserPanel(QWidget):
    """Dockable browser for imported 3D references."""

    COLUMNS = ["Name", "Group", "Status", "Path", "Type", "Statistics"]

    def __init__(self, workspace, on_change=None):

        super().__init__()

        self.workspace = workspace
        self.on_change = on_change
        self._refreshing = False
        self._build()
        self._load_state()
        self.refresh()

    # --------------------------------

    def _build(self):

        layout = QVBoxLayout(self)
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search references")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Loaded", "Unloaded", "Missing", "Stale", "Error"])
        self.type_filter = QComboBox()
        self.type_filter.addItem("All")
        filters.addWidget(QLabel("Search"))
        filters.addWidget(self.search)
        filters.addWidget(QLabel("Status"))
        filters.addWidget(self.status_filter)
        filters.addWidget(QLabel("Type"))
        filters.addWidget(self.type_filter)
        layout.addLayout(filters)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(len(self.COLUMNS))
        self.tree.setHeaderLabels(self.COLUMNS)
        self.tree.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.tree)

        self.statistics = QLabel("")
        layout.addWidget(self.statistics)

        toolbar = QHBoxLayout()
        self.import_button = QPushButton("Import")
        self.reload_button = QPushButton("Reload")
        self.replace_button = QPushButton("Replace")
        self.unload_button = QPushButton("Unload")
        self.remove_button = QPushButton("Remove")
        self.visible_button = QPushButton("Visibility")
        self.lock_button = QPushButton("Lock")
        self.isolate_button = QPushButton("Isolate")
        self.properties_button = QPushButton("Properties")

        for button in (
            self.import_button,
            self.reload_button,
            self.replace_button,
            self.unload_button,
            self.remove_button,
            self.visible_button,
            self.lock_button,
            self.isolate_button,
            self.properties_button,
        ):
            toolbar.addWidget(button)

        layout.addLayout(toolbar)
        self.search.textChanged.connect(self.refresh)
        self.status_filter.currentTextChanged.connect(self.refresh)
        self.type_filter.currentTextChanged.connect(self.refresh)
        self.import_button.clicked.connect(self.import_reference)
        self.reload_button.clicked.connect(self.reload_reference)
        self.replace_button.clicked.connect(self.replace_reference)
        self.unload_button.clicked.connect(self.unload_reference)
        self.remove_button.clicked.connect(self.remove_reference)
        self.visible_button.clicked.connect(self.toggle_visibility)
        self.lock_button.clicked.connect(self.toggle_lock)
        self.isolate_button.clicked.connect(self.isolate_reference)
        self.properties_button.clicked.connect(self.show_properties)

    # --------------------------------

    def refresh(self):
        """Refresh reference browser rows."""

        if self._refreshing:
            return

        self._refreshing = True
        self._save_state()
        self._refresh_type_filter()
        self.tree.clear()

        for model in self._filtered_models():
            self._add_model_row(model)

        self.tree.resizeColumnToContents(0)
        self.statistics.setText(self._statistics_text())
        self._refreshing = False

    # --------------------------------

    def import_reference(self, path=None, settings=None):
        """Import a new reference through ImportManager and commands."""

        chosen = path or self._choose_import_path()

        if not chosen:
            return None

        import_settings = settings or self._import_settings(chosen)

        if import_settings is None:
            return None

        result = self.workspace.import_manager.create_reference(
            self.workspace,
            chosen,
            None,
            import_settings,
        )
        self._remember_import_settings(import_settings)
        self._changed()
        if self.workspace.reference_manager.models:
            self._select_model(self.workspace.reference_manager.models[-1])

        return result

    # --------------------------------

    def reload_reference(self):
        """Reload the selected reference."""

        model = self.selected_model()

        if model is None:
            return None

        result = self.workspace.import_manager.reload_reference(self.workspace, model)
        self._changed()

        return result

    # --------------------------------

    def replace_reference(self, path=None, settings=None):
        """Replace the selected reference path and import data."""

        model = self.selected_model()

        if model is None:
            return None

        chosen = path or self._choose_import_path()

        if not chosen:
            return None

        import_settings = settings or self._import_settings(chosen, model.import_settings)

        if import_settings is None:
            return None

        result = self.workspace.import_manager.replace_reference(
            self.workspace,
            model,
            chosen,
            import_settings,
        )
        self._remember_import_settings(import_settings)
        self._changed()

        return result

    # --------------------------------

    def unload_reference(self):
        """Unload the selected reference through the Command System."""

        model = self.selected_model()

        if model is not None:
            self.workspace.command_manager.execute(UnloadReferenceCommand(self.workspace, model))
            self._changed()

    # --------------------------------

    def remove_reference(self):
        """Remove the selected reference through the Command System."""

        model = self.selected_model()

        if model is not None:
            self.workspace.command_manager.execute(RemoveReferenceModelCommand(self.workspace, model))
            self._changed()

    # --------------------------------

    def toggle_visibility(self):
        """Toggle selected reference visibility through the Command System."""

        model = self.selected_model()

        if model is not None:
            self.workspace.command_manager.execute(UpdateReferenceModelCommand(
                model,
                {"visible": model.visible},
                {"visible": not model.visible},
            ))
            self._changed()

    # --------------------------------

    def toggle_lock(self):
        """Toggle selected reference lock state through the Command System."""

        model = self.selected_model()

        if model is not None:
            self.workspace.command_manager.execute(UpdateReferenceModelCommand(
                model,
                {"locked": model.locked},
                {"locked": not model.locked},
            ))
            self._changed()

    # --------------------------------

    def isolate_reference(self):
        """Isolate the selected reference through the Command System."""

        model = self.selected_model()
        self.workspace.command_manager.execute(SetReferenceIsolationCommand(self.workspace, model))
        self._changed()

    # --------------------------------

    def show_properties(self):
        """Select the first instance of the selected reference."""

        model = self.selected_model()

        if model is None:
            return

        instance = next(
            (
                item for item in self.workspace.reference_manager.instances
                if item.model_id == model.id
            ),
            None,
        )

        if instance is not None:
            self.workspace.selection.clear()
            self.workspace.selection.select(instance)
            self._changed()

    # --------------------------------

    def selected_model(self):
        """Return the currently selected reference model."""

        item = self.tree.currentItem()

        if item is None:
            selected = getattr(self.workspace.selection, "first", None)
            model_id = getattr(selected, "model_id", None)
            return self.workspace.reference_manager.get_model(model_id)

        return self.workspace.reference_manager.get_model(item.data(0, Qt.UserRole))

    # --------------------------------

    def _selection_changed(self):

        self.show_properties()

    # --------------------------------

    def _add_model_row(self, model):

        stats = model.import_statistics
        row = QTreeWidgetItem([
            model.name,
            model.group,
            model.status,
            model.path,
            model.reader_type or model.metadata.source_format,
            f"{stats.vertices} V / {stats.faces} F / {stats.warnings} W / {stats.errors} E",
        ])
        row.setData(0, Qt.UserRole, model.id)
        self.tree.addTopLevelItem(row)

    # --------------------------------

    def _select_model(self, model):

        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)

            if item.data(0, Qt.UserRole) == model.id:
                self.tree.setCurrentItem(item)
                return

    # --------------------------------

    def _filtered_models(self):

        query = self.search.text().strip().lower()
        status = self.status_filter.currentText()
        reader_type = self.type_filter.currentText()

        return [
            model for model in self.workspace.reference_manager.models
            if (
                (not query or self._matches_query(model, query)) and
                (status == "All" or model.status == status) and
                (reader_type == "All" or model.reader_type == reader_type)
            )
        ]

    # --------------------------------

    def _matches_query(self, model, query):

        return any(
            query in str(value).lower()
            for value in (model.name, model.group, model.category, model.path, model.reader_type)
        )

    # --------------------------------

    def _statistics_text(self):

        stats = self.workspace.reference_manager.statistics()
        visible = len(self.workspace.visible_references())

        return (
            f"References: {stats['models']} | Instances: {stats['instances']} | "
            f"Loaded: {stats['loaded']} | Unloaded: {stats['unloaded']} | Visible: {visible}"
        )

    # --------------------------------

    def _refresh_type_filter(self):

        if self._refreshing:
            pass

        current = self.type_filter.currentText()
        types = sorted({
            model.reader_type
            for model in self.workspace.reference_manager.models
            if model.reader_type
        })
        self.type_filter.blockSignals(True)
        self.type_filter.clear()
        self.type_filter.addItem("All")
        self.type_filter.addItems(types)
        self.type_filter.setCurrentText(current if current in ["All"] + types else "All")
        self.type_filter.blockSignals(False)

    # --------------------------------

    def _choose_import_path(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import 3D Reference",
            "",
            "3D References (*.obj *.stl *.ply *.off *.gltf *.glb *.fbx *.3ds *.step *.stp *.iges *.igs)",
        )

        return path

    # --------------------------------

    def _import_settings(self, path, settings=None):

        remembered = ImportSettings.from_dict(
            self.workspace.project_settings.get("import_options", {})
        )
        dialog = ImportOptionsDialog(self, settings or remembered, path)

        if dialog.exec() != dialog.Accepted:
            return None

        return dialog.settings()

    # --------------------------------

    def _remember_import_settings(self, settings):

        if settings.remember_settings:
            self.workspace.project_settings["import_options"] = settings.to_dict()

    # --------------------------------

    def _load_state(self):

        state = self.workspace.project_settings.get("reference_browser", {})
        self.search.setText(state.get("search", ""))
        self.status_filter.setCurrentText(state.get("status", "All"))
        self.type_filter.setCurrentText(state.get("type", "All"))

    # --------------------------------

    def _save_state(self):

        self.workspace.project_settings["reference_browser"] = {
            "search": self.search.text(),
            "status": self.status_filter.currentText(),
            "type": self.type_filter.currentText(),
        }

    # --------------------------------

    def _changed(self):

        self.refresh()

        if self.on_change:
            self.on_change()
