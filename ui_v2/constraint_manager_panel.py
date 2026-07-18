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

from engine.commands import (
    DeleteConstraintCommand,
    EnableConstraintCommand,
    RenameConstraintCommand,
)


class ConstraintManagerPanel(QWidget):
    """Dockable panel for workspace constraints."""

    COLUMNS = [
        "Type",
        "Name",
        "Status",
        "References",
        "Driven Value",
        "Suppressed",
    ]

    def __init__(self, workspace, on_change=None):

        super().__init__()
        self.workspace = workspace
        self.on_change = on_change

        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        layout.addWidget(self.table)

        toolbar = QHBoxLayout()
        self.enable_button = QPushButton("Enable")
        self.disable_button = QPushButton("Disable")
        self.delete_button = QPushButton("Delete")
        self.highlight_button = QPushButton("Highlight")
        self.rename_button = QPushButton("Rename")

        for button in (
            self.enable_button,
            self.disable_button,
            self.delete_button,
            self.highlight_button,
            self.rename_button,
        ):
            toolbar.addWidget(button)

        layout.addLayout(toolbar)

        self.enable_button.clicked.connect(lambda: self._set_enabled(True))
        self.disable_button.clicked.connect(lambda: self._set_enabled(False))
        self.delete_button.clicked.connect(self.delete_constraint)
        self.highlight_button.clicked.connect(self.highlight_constraint)
        self.rename_button.clicked.connect(self.rename_constraint)
        self.refresh()

    # --------------------------------

    def refresh(self):
        """Reload constraints from the workspace manager."""

        self.workspace.constraint_manager.validate()
        self.table.setRowCount(0)

        for constraint in self.workspace.constraint_manager.constraints:
            self._add_constraint_row(constraint)

        self.table.resizeColumnsToContents()

    # --------------------------------

    def delete_constraint(self):
        """Delete the selected constraint through commands."""

        constraint = self._selected_constraint()

        if constraint is None:
            return

        self.workspace.command_manager.execute(
            DeleteConstraintCommand(self.workspace, constraint)
        )
        self._changed()

    # --------------------------------

    def rename_constraint(self):
        """Rename the selected constraint through commands."""

        constraint = self._selected_constraint()

        if constraint is None:
            return

        name, ok = QInputDialog.getText(
            self,
            "Rename Constraint",
            "Constraint Name",
            text=constraint.name,
        )

        if ok and name.strip():
            self.workspace.command_manager.execute(
                RenameConstraintCommand(self.workspace, constraint, name)
            )
            self._changed()

    # --------------------------------

    def highlight_constraint(self):
        """Select the constraint so canvas/property panels highlight it."""

        constraint = self._selected_constraint()

        if constraint is None:
            return

        self.workspace.selection.select(constraint)
        self._changed()

    # --------------------------------

    def _set_enabled(self, enabled):

        constraint = self._selected_constraint()

        if constraint is None:
            return

        self.workspace.command_manager.execute(
            EnableConstraintCommand(self.workspace, constraint, enabled)
        )
        self._changed()

    # --------------------------------

    def _add_constraint_row(self, constraint):

        row = self.table.rowCount()
        self.table.insertRow(row)
        values = (
            constraint.constraint_type,
            constraint.name,
            constraint.status,
            str(constraint.referenced_entity_count()),
            "" if constraint.value is None else str(constraint.value),
            "Yes" if constraint.suppressed else "No",
        )

        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, constraint.id)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, column, item)

    # --------------------------------

    def _selected_constraint(self):

        item = self.table.currentItem()

        if item is None:
            row = self.table.currentRow()
            item = self.table.item(row, 0) if row >= 0 else None

        if item is None:
            return None

        return self.workspace.constraint_manager.get(item.data(Qt.UserRole))

    # --------------------------------

    def _changed(self):

        self.refresh()

        if self.on_change:
            self.on_change()
