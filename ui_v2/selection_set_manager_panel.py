from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class SelectionSetManagerPanel(QWidget):
    """Dockable panel for named workspace selection sets."""

    COLUMNS = ["Selection Set", "Entity Count"]
    TYPE_FILTERS = [
        "All",
        "Lines",
        "Polylines",
        "Splines",
        "Rectangles",
        "Circles",
        "Arcs",
        "Blocks",
        "Groups",
        "Text",
        "MText",
        "Leaders",
        "Dimensions",
        "Hatches",
    ]

    def __init__(self, workspace, on_change=None):

        super().__init__()
        self.workspace = workspace
        self.on_change = on_change

        layout = QVBoxLayout(self)
        layout.addLayout(self._create_filter_bar())

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        layout.addWidget(self.table)

        toolbar = QHBoxLayout()
        self.create_button = QPushButton("Create")
        self.rename_button = QPushButton("Rename")
        self.delete_button = QPushButton("Delete")
        self.recall_button = QPushButton("Recall")
        self.update_button = QPushButton("Update")

        for button in (
            self.create_button,
            self.rename_button,
            self.delete_button,
            self.recall_button,
            self.update_button,
        ):
            toolbar.addWidget(button)

        layout.addLayout(toolbar)

        self.create_button.clicked.connect(self.create_set)
        self.rename_button.clicked.connect(self.rename_set)
        self.delete_button.clicked.connect(self.delete_set)
        self.recall_button.clicked.connect(self.recall_set)
        self.update_button.clicked.connect(self.update_set)
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        self.layer_filter.currentTextChanged.connect(self.apply_filters)
        self.lock_filter.currentTextChanged.connect(self.apply_filters)
        self.visibility_filter.currentTextChanged.connect(self.apply_filters)
        self.clear_filter_button.clicked.connect(self.clear_filters)
        self.refresh()

    # --------------------------------

    def _create_filter_bar(self):
        """Create controls for the shared SelectionManager filter."""

        filter_bar = QHBoxLayout()
        self.type_filter = QComboBox()
        self.type_filter.addItems(self.TYPE_FILTERS)
        self.layer_filter = QComboBox()
        self.lock_filter = QComboBox()
        self.lock_filter.addItems(["Any", "Locked", "Unlocked"])
        self.visibility_filter = QComboBox()
        self.visibility_filter.addItems(["Any", "Visible", "Hidden"])
        self.clear_filter_button = QPushButton("Clear Filters")

        for label, widget in (
            ("Type", self.type_filter),
            ("Layer", self.layer_filter),
            ("Lock", self.lock_filter),
            ("Visibility", self.visibility_filter),
        ):
            filter_bar.addWidget(QLabel(label))
            filter_bar.addWidget(widget)

        filter_bar.addWidget(self.clear_filter_button)

        return filter_bar

    # --------------------------------

    def refresh(self):
        """Reload selection sets from the workspace selection manager."""

        self._refresh_filter_options()
        self.table.setRowCount(0)

        for name in self.workspace.selection.set_names():
            selection_set = self.workspace.selection.selection_sets[name]
            self._add_set_row(selection_set)

        self.table.resizeColumnsToContents()

    # --------------------------------

    def apply_filters(self):
        """Apply panel controls to the workspace SelectionManager filter."""

        active_filter = self.workspace.selection.filter
        active_filter.type_filter = self.type_filter.currentText()
        active_filter.lock_state = self.lock_filter.currentText()
        active_filter.visibility = self.visibility_filter.currentText()
        layer_name = self.layer_filter.currentText()
        active_filter.layer_names = set() if layer_name == "All Layers" else {layer_name}

        if self.on_change:
            self.on_change()

    # --------------------------------

    def clear_filters(self):
        """Clear all selection filters."""

        self.workspace.selection.filter.reset()
        self._refresh_filter_options()

        if self.on_change:
            self.on_change()

    # --------------------------------

    def create_set(self):
        """Create a named set from the current selection."""

        if not self.workspace.selection.selected:
            self._changed()
            return

        name, ok = QInputDialog.getText(
            self,
            "Create Selection Set",
            "Selection Set Name",
            text=self._next_name(),
        )

        if ok and name.strip():
            self.workspace.selection.create_set(name)
            self._changed()

    # --------------------------------

    def rename_set(self):
        """Rename the selected set."""

        name = self._selected_name()

        if not name:
            return

        new_name, ok = QInputDialog.getText(
            self,
            "Rename Selection Set",
            "Selection Set Name",
            text=name,
        )

        if ok and new_name.strip():
            self.workspace.selection.rename_set(name, new_name)
            self._changed()

    # --------------------------------

    def delete_set(self):
        """Delete the selected set."""

        name = self._selected_name()

        if name:
            self.workspace.selection.delete_set(name)
            self._changed()

    # --------------------------------

    def recall_set(self):
        """Recall the selected set into the active selection."""

        name = self._selected_name()

        if name:
            self.workspace.selection.recall_set(name, self.workspace)
            self._changed()

    # --------------------------------

    def update_set(self):
        """Update the selected set from the current selection."""

        name = self._selected_name()

        if name:
            self.workspace.selection.update_set(name)
            self._changed()

    # --------------------------------

    def _refresh_filter_options(self):

        active_filter = self.workspace.selection.filter
        layers = ["All Layers"] + [
            layer.name
            for layer in self.workspace.layer_manager.layers
        ]
        layer_name = (
            next(iter(active_filter.layer_names))
            if active_filter.layer_names
            else "All Layers"
        )

        self.type_filter.blockSignals(True)
        self.layer_filter.blockSignals(True)
        self.lock_filter.blockSignals(True)
        self.visibility_filter.blockSignals(True)

        self.layer_filter.clear()
        self.layer_filter.addItems(layers)
        self.type_filter.setCurrentText(active_filter.type_filter)
        self.layer_filter.setCurrentText(
            layer_name if layer_name in layers else "All Layers"
        )
        self.lock_filter.setCurrentText(active_filter.lock_state)
        self.visibility_filter.setCurrentText(active_filter.visibility)

        self.type_filter.blockSignals(False)
        self.layer_filter.blockSignals(False)
        self.lock_filter.blockSignals(False)
        self.visibility_filter.blockSignals(False)

    # --------------------------------

    def _add_set_row(self, selection_set):

        row = self.table.rowCount()
        self.table.insertRow(row)

        for column, value in enumerate((selection_set.name, str(selection_set.count))):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, selection_set.name)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, column, item)

    # --------------------------------

    def _selected_name(self):

        item = self.table.currentItem()

        if item is None:
            row = self.table.currentRow()
            item = self.table.item(row, 0) if row >= 0 else None

        return item.data(Qt.UserRole) if item is not None else ""

    # --------------------------------

    def _next_name(self):

        index = 1

        while f"Selection Set {index}" in self.workspace.selection.selection_sets:
            index += 1

        return f"Selection Set {index}"

    # --------------------------------

    def _changed(self):

        self.refresh()

        if self.on_change:
            self.on_change()
