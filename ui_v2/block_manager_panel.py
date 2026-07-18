from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from engine.commands import CreateBlockCommand
from engine.entities import BlockReference
from engine.geometry import Vector2


class BlockManagerPanel(QWidget):
    """Dockable panel that displays workspace block definitions."""

    COLUMNS = [
        "Block Name",
        "Block ID",
        "Entity Count",
        "Nested",
        "Reference Count",
        "Origin",
    ]

    def __init__(self, workspace, on_change=None):

        super().__init__()

        self.workspace = workspace
        self.on_change = on_change
        self._refreshing = False

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.table)

        toolbar = QHBoxLayout()
        self.new_button = QPushButton("New Block")
        self.delete_button = QPushButton("Delete Block")
        self.rename_button = QPushButton("Rename Block")

        for button in (
            self.new_button,
            self.delete_button,
            self.rename_button,
        ):
            toolbar.addWidget(button)

        layout.addLayout(toolbar)

        self.new_button.clicked.connect(self.new_block)
        self.delete_button.clicked.connect(self.delete_block)
        self.rename_button.clicked.connect(self.rename_block)

        self.refresh()

    # --------------------------------

    def refresh(self):
        """Reload block definition rows from the workspace BlockManager."""

        self._refreshing = True
        self.table.setRowCount(0)

        manager = getattr(self.workspace, "block_manager", None)

        for definition in getattr(manager, "definitions", []):
            self._add_definition_row(definition)

        self.table.resizeColumnsToContents()
        self._refreshing = False

    # --------------------------------

    def new_block(self):
        """Create a block definition from the current selection."""

        selection = getattr(self.workspace, "selection", None)
        selected = list(selection.selected) if selection else []

        if not selected:
            self._changed()
            return

        name, ok = QInputDialog.getText(
            self,
            "New Block",
            "Block Name",
            text=self._next_block_name(),
        )

        if not ok:
            return

        origin = self._selected_origin(selected)

        command = CreateBlockCommand(
            self.workspace,
            name,
            origin,
            selected,
            replace=True,
        )
        self.workspace.command_manager.execute(command)
        self._changed()

    # --------------------------------

    def delete_block(self):
        """Delete the selected unused block definition."""

        definition = self._selected_definition()

        if definition is None or self._reference_count(definition):
            self._changed()
            return

        self.workspace.block_manager.remove(definition)
        self._changed()

    # --------------------------------

    def rename_block(self):
        """Rename the selected block definition."""

        definition = self._selected_definition()

        if definition is None:
            return

        name, ok = QInputDialog.getText(
            self,
            "Rename Block",
            "Block Name",
            text=definition.name,
        )

        if ok and self.workspace.block_manager.rename(definition, name):
            self._changed()

    # --------------------------------

    def _add_definition_row(self, definition):

        row = self.table.rowCount()
        self.table.insertRow(row)

        values = [
            definition.name,
            str(definition.id),
            str(definition.count),
            "Yes" if self._has_nested_block(definition) else "No",
            str(self._reference_count(definition)),
            self._origin_text(definition),
        ]

        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, definition.id)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, column, item)

    # --------------------------------

    def _has_nested_block(self, definition):

        return any(
            isinstance(entity, BlockReference)
            for entity in definition.entities
        )

    # --------------------------------

    def _reference_count(self, definition):

        return sum(
            1 for entity in self.workspace.entities
            if (
                isinstance(entity, BlockReference) and
                entity.definition is definition
            )
        )

    # --------------------------------

    def _origin_text(self, definition):

        origin = definition.origin

        return f"{origin.x:.2f}, {origin.y:.2f}"

    # --------------------------------

    def _selected_definition(self):

        item = self.table.currentItem()

        if item is None:
            row = self.table.currentRow()
            item = self.table.item(row, 0) if row >= 0 else None

        if item is None:
            return None

        return self.workspace.block_manager.get_by_id(item.data(Qt.UserRole))

    # --------------------------------

    def _selection_changed(self):

        definition = self._selected_definition()

        if definition is not None:
            self.workspace.block_manager.set_current(definition)

    # --------------------------------

    def _selected_origin(self, selected):

        if not selected:
            return Vector2()

        box = selected[0].bounding_box
        left = box.min.x
        top = box.min.y
        right = box.max.x
        bottom = box.max.y

        for entity in selected[1:]:
            box = entity.bounding_box
            left = min(left, box.min.x)
            top = min(top, box.min.y)
            right = max(right, box.max.x)
            bottom = max(bottom, box.max.y)

        default = f"{(left + right) * 0.5:.2f},{(top + bottom) * 0.5:.2f}"
        text, ok = QInputDialog.getText(
            self,
            "Block Origin",
            "Origin X,Y",
            text=default,
        )

        if not ok:
            return Vector2((left + right) * 0.5, (top + bottom) * 0.5)

        parts = [part.strip() for part in text.split(",")]

        if len(parts) != 2:
            return Vector2((left + right) * 0.5, (top + bottom) * 0.5)

        try:
            return Vector2(float(parts[0]), float(parts[1]))
        except ValueError:
            return Vector2((left + right) * 0.5, (top + bottom) * 0.5)

    # --------------------------------

    def _next_block_name(self):

        return self.workspace.block_manager.unique_name("Block")

    # --------------------------------

    def _changed(self):

        self.refresh()

        if self.on_change:
            self.on_change()
