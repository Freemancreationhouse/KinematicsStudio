from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from engine.commands import (
    SaveReferenceDisplayPresetCommand,
    UpdateReferenceLayerMappingCommand,
    UpdateReferenceStyleCommand,
)


class ReferenceLayerPanel(QWidget):
    """Dockable panel for reference layer mapping and styling."""

    COLUMNS = ["Reference", "Layer", "Target Layer", "Visible", "Locked", "Isolated", "Color"]

    def __init__(self, workspace, on_change=None):

        super().__init__()

        self.workspace = workspace
        self.on_change = on_change
        self._refreshing = False
        self._build()
        self.refresh()

    # --------------------------------

    def _build(self):

        layout = QVBoxLayout(self)
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search reference layers")
        self.filter = QComboBox()
        self.filter.addItems(["All", "Visible", "Hidden", "Locked", "Unlocked", "Isolated"])
        filters.addWidget(QLabel("Search"))
        filters.addWidget(self.search)
        filters.addWidget(QLabel("Filter"))
        filters.addWidget(self.filter)
        layout.addLayout(filters)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(len(self.COLUMNS))
        self.tree.setHeaderLabels(self.COLUMNS)
        layout.addWidget(self.tree)
        self.statistics = QLabel("")
        layout.addWidget(self.statistics)

        toolbar = QHBoxLayout()
        self.visible_button = QPushButton("Visibility")
        self.lock_button = QPushButton("Lock")
        self.isolate_button = QPushButton("Isolate")
        self.color_button = QPushButton("Color Override")
        self.style_button = QPushButton("Style")
        self.preset_button = QPushButton("Save Preset")

        for button in (
            self.visible_button,
            self.lock_button,
            self.isolate_button,
            self.color_button,
            self.style_button,
            self.preset_button,
        ):
            toolbar.addWidget(button)

        layout.addLayout(toolbar)
        self.search.textChanged.connect(self.refresh)
        self.filter.currentTextChanged.connect(self.refresh)
        self.visible_button.clicked.connect(self.toggle_visibility)
        self.lock_button.clicked.connect(self.toggle_lock)
        self.isolate_button.clicked.connect(self.toggle_isolation)
        self.color_button.clicked.connect(self.set_color_override)
        self.style_button.clicked.connect(self.apply_style)
        self.preset_button.clicked.connect(self.save_preset)

    # --------------------------------

    def refresh(self):
        """Refresh reference layer mappings."""

        if self._refreshing:
            return

        self._refreshing = True
        self.tree.clear()

        for model, mapping in self._filtered_mappings():
            self._add_mapping_row(model, mapping)

        self.statistics.setText(self._statistics_text())
        self.tree.resizeColumnToContents(0)
        self._refreshing = False

    # --------------------------------

    def toggle_visibility(self):
        """Toggle selected reference layer visibility."""

        self._update_mapping({"visible": not self.selected_mapping()[1].visible})

    # --------------------------------

    def toggle_lock(self):
        """Toggle selected reference layer lock."""

        self._update_mapping({"locked": not self.selected_mapping()[1].locked})

    # --------------------------------

    def toggle_isolation(self):
        """Toggle selected reference layer isolation."""

        self._update_mapping({"isolated": not self.selected_mapping()[1].isolated})

    # --------------------------------

    def set_color_override(self, color=None):
        """Set reference layer color override."""

        if color is None:
            chosen = QColorDialog.getColor(parent=self)

            if not chosen.isValid():
                return

            color = chosen.name()

        self._update_mapping({"color_override": color})

    # --------------------------------

    def apply_style(self, **changes):
        """Apply style overrides to the selected reference."""

        model, _ = self.selected_mapping()

        if model is None:
            return

        before = model.style_overrides.to_dict()
        after = dict(before)
        after.update(changes or {"wireframe_override": True})
        self.workspace.command_manager.execute(
            UpdateReferenceStyleCommand(self.workspace, model, before, after)
        )
        self._changed()

    # --------------------------------

    def save_preset(self, name="Reference Preset"):
        """Save current reference style as a display preset."""

        model, _ = self.selected_mapping()

        if model is not None:
            self.workspace.command_manager.execute(
                SaveReferenceDisplayPresetCommand(self.workspace, model, name)
            )
            self._changed()

    # --------------------------------

    def selected_mapping(self):
        """Return selected model and layer mapping."""

        item = self.tree.currentItem()

        if item is None and self.tree.topLevelItemCount() == 1:
            item = self.tree.topLevelItem(0)

        if item is None:
            return None, None

        model = self.workspace.reference_manager.get_model(item.data(0, Qt.UserRole))
        layer_name = item.data(1, Qt.UserRole)
        mapping = None

        if model is not None:
            mapping = model.layer_mappings.get(layer_name)

        return model, mapping

    # --------------------------------

    def _update_mapping(self, changes):

        model, mapping = self.selected_mapping()

        if model is None or mapping is None:
            return

        before = mapping.to_dict()
        after = dict(before)
        after.update(changes)
        self.workspace.command_manager.execute(
            UpdateReferenceLayerMappingCommand(
                self.workspace,
                model,
                mapping.name,
                before,
                after,
            )
        )
        self._changed()

    # --------------------------------

    def _add_mapping_row(self, model, mapping):

        item = QTreeWidgetItem([
            model.name,
            mapping.name,
            mapping.target_layer,
            "Yes" if mapping.visible else "No",
            "Yes" if mapping.locked else "No",
            "Yes" if mapping.isolated else "No",
            mapping.color_override or model.style_overrides.display_color,
        ])
        item.setData(0, Qt.UserRole, model.id)
        item.setData(1, Qt.UserRole, mapping.name)
        self.tree.addTopLevelItem(item)

    # --------------------------------

    def _filtered_mappings(self):

        query = self.search.text().strip().lower()
        filter_name = self.filter.currentText()
        rows = []

        for model in self.workspace.reference_manager.models:
            for mapping in self.workspace.reference_manager.reference_layer_mappings(model):
                if query and query not in f"{model.name} {mapping.name} {mapping.target_layer}".lower():
                    continue

                if not self._passes_filter(mapping, filter_name):
                    continue

                rows.append((model, mapping))

        return rows

    # --------------------------------

    def _passes_filter(self, mapping, filter_name):

        return (
            filter_name == "All" or
            (filter_name == "Visible" and mapping.visible) or
            (filter_name == "Hidden" and not mapping.visible) or
            (filter_name == "Locked" and mapping.locked) or
            (filter_name == "Unlocked" and not mapping.locked) or
            (filter_name == "Isolated" and mapping.isolated)
        )

    # --------------------------------

    def _statistics_text(self):

        stats = self.workspace.reference_manager.layer_statistics()

        return (
            f"Layers: {stats['layers']} | Visible: {stats['visible']} | "
            f"Locked: {stats['locked']} | Isolated: {stats['isolated']}"
        )

    # --------------------------------

    def _changed(self):

        self.refresh()

        if self.on_change:
            self.on_change()
