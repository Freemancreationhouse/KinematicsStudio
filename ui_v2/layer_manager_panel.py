from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QHBoxLayout,
    QInputDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class LayerManagerPanel(QWidget):
    """Dockable panel for managing workspace layers."""

    COLUMNS = [
        "Current",
        "Layer Name",
        "Visibility",
        "Lock",
        "Color",
        "Line Type",
        "Line Weight",
    ]

    def __init__(self, workspace, on_change=None):

        super().__init__()

        self.workspace = workspace
        self.on_change = on_change
        self._refreshing = False

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.itemChanged.connect(self._item_changed)
        self.table.itemDoubleClicked.connect(self._item_double_clicked)
        layout.addWidget(self.table)

        toolbar = QHBoxLayout()
        self.new_button = QPushButton("New Layer")
        self.delete_button = QPushButton("Delete Layer")
        self.rename_button = QPushButton("Rename Layer")
        self.current_button = QPushButton("Set Current Layer")

        for button in (
            self.new_button,
            self.delete_button,
            self.rename_button,
            self.current_button,
        ):
            toolbar.addWidget(button)

        layout.addLayout(toolbar)

        self.new_button.clicked.connect(self.new_layer)
        self.delete_button.clicked.connect(self.delete_layer)
        self.rename_button.clicked.connect(self.rename_layer)
        self.current_button.clicked.connect(self.set_current_layer)

        self.refresh()

    # --------------------------------

    def refresh(self):
        """Reload layer rows from the workspace LayerManager."""

        self._refreshing = True
        manager = self.workspace.layer_manager
        self.table.setRowCount(0)

        for layer in manager.layers:
            self._add_layer_row(layer)

        self.table.resizeColumnsToContents()
        self._refreshing = False

    # --------------------------------

    def new_layer(self):
        """Create a uniquely named layer."""

        name, ok = QInputDialog.getText(
            self,
            "New Layer",
            "Layer Name",
            text=self._next_layer_name(),
        )

        if ok and name.strip():
            self.workspace.create_layer(name.strip())
            self._changed()

    # --------------------------------

    def delete_layer(self):
        """Delete the selected layer unless it is Layer 0."""

        layer = self._selected_layer()

        if layer is not None and self.workspace.delete_layer(layer):
            self._changed()

    # --------------------------------

    def rename_layer(self):
        """Rename the selected non-default layer."""

        layer = self._selected_layer()

        if layer is None or layer.name == "0":
            return

        name, ok = QInputDialog.getText(
            self,
            "Rename Layer",
            "Layer Name",
            text=layer.name,
        )

        if ok and self.workspace.rename_layer(layer, name):
            self._changed()

    # --------------------------------

    def set_current_layer(self):
        """Make the selected layer current for future entities."""

        layer = self._selected_layer()

        if layer is not None:
            self.workspace.set_current_layer(layer)
            self._changed()

    # --------------------------------

    def _add_layer_row(self, layer):

        row = self.table.rowCount()
        self.table.insertRow(row)

        current = QTableWidgetItem("✓" if layer is self.workspace.current_layer else "")
        current.setData(Qt.UserRole, layer.id)
        current.setFlags(current.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, 0, current)

        name = QTableWidgetItem(layer.name)
        name.setData(Qt.UserRole, layer.id)
        name.setFlags(name.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, 1, name)

        visible = self._checkbox_item(layer.visible, layer.id)
        self.table.setItem(row, 2, visible)

        locked = self._checkbox_item(layer.locked, layer.id)
        self.table.setItem(row, 3, locked)

        self.table.setItem(row, 4, self._editable_item(layer.color, layer.id))
        self.table.setItem(row, 5, self._editable_item(layer.line_type, layer.id))
        self.table.setItem(row, 6, self._editable_item(str(layer.line_weight), layer.id))

    # --------------------------------

    def _checkbox_item(self, checked, layer_id):

        item = QTableWidgetItem()
        item.setData(Qt.UserRole, layer_id)
        item.setFlags(
            (item.flags() | Qt.ItemIsUserCheckable) & ~Qt.ItemIsEditable
        )
        item.setCheckState(Qt.Checked if checked else Qt.Unchecked)

        return item

    # --------------------------------

    def _read_only_item(self, text, layer_id):

        item = QTableWidgetItem(text)
        item.setData(Qt.UserRole, layer_id)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        return item

    # --------------------------------

    def _editable_item(self, text, layer_id):

        item = QTableWidgetItem(text)
        item.setData(Qt.UserRole, layer_id)

        return item

    # --------------------------------

    def _item_changed(self, item):

        if self._refreshing:
            return

        layer = self._layer_for_item(item)

        if layer is None:
            return

        if item.column() == 2:
            layer.visible = item.checkState() == Qt.Checked
            self._changed()

        elif item.column() == 3:
            layer.locked = item.checkState() == Qt.Checked
            self._changed()

        elif item.column() == 4:
            self.workspace.update_layer_properties(
                layer,
                color=item.text()
            )
            self._changed()

        elif item.column() == 5:
            self.workspace.update_layer_properties(
                layer,
                line_type=item.text()
            )
            self._changed()

        elif item.column() == 6:
            if self.workspace.update_layer_properties(
                layer,
                line_weight=item.text()
            ):
                self._changed()
            else:
                self.refresh()

    # --------------------------------

    def _item_double_clicked(self, item):

        layer = self._layer_for_item(item)

        if layer is None or item.column() != 4:
            return

        color = QColorDialog.getColor(
            initial=QColor(layer.color),
            parent=self,
            title="Layer Color"
        )

        if color.isValid():
            self.workspace.update_layer_properties(
                layer,
                color=color.name()
            )
            self._changed()

    # --------------------------------

    def _selected_layer(self):

        item = self.table.currentItem()

        if item is None:
            row = self.table.currentRow()
            item = self.table.item(row, 0) if row >= 0 else None

        return self._layer_for_item(item)

    # --------------------------------

    def _layer_for_item(self, item):

        if item is None:
            return None

        return self.workspace.layer_manager.get_by_id(item.data(Qt.UserRole))

    # --------------------------------

    def _next_layer_name(self):

        index = 1
        manager = self.workspace.layer_manager

        while manager.get(f"Layer {index}") is not None:
            index += 1

        return f"Layer {index}"

    # --------------------------------

    def _changed(self):

        self.refresh()

        if self.on_change:
            self.on_change()
