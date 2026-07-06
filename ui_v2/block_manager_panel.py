from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from engine.entities import BlockReference


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
        """Placeholder for the future new-block workflow."""

        self._placeholder_changed()

    # --------------------------------

    def delete_block(self):
        """Placeholder for the future delete-block workflow."""

        self._placeholder_changed()

    # --------------------------------

    def rename_block(self):
        """Placeholder for the future rename-block workflow."""

        self._placeholder_changed()

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

    def _placeholder_changed(self):

        self.refresh()

        if self.on_change:
            self.on_change()
