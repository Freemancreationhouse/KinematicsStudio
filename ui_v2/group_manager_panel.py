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
    CreateGroupCommand,
    DeleteGroupCommand,
    RenameGroupCommand,
    UngroupCommand,
)


class GroupManagerPanel(QWidget):
    """Dockable panel for managing workspace groups."""

    COLUMNS = [
        "Group Name",
        "Group ID",
        "Entity Count",
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
        self.create_button = QPushButton("Create Group")
        self.rename_button = QPushButton("Rename Group")
        self.delete_button = QPushButton("Delete Group")
        self.ungroup_button = QPushButton("Ungroup")

        for button in (
            self.create_button,
            self.rename_button,
            self.delete_button,
            self.ungroup_button,
        ):
            toolbar.addWidget(button)

        layout.addLayout(toolbar)

        self.create_button.clicked.connect(self.create_group)
        self.rename_button.clicked.connect(self.rename_group)
        self.delete_button.clicked.connect(self.delete_group)
        self.ungroup_button.clicked.connect(self.ungroup)

        self.refresh()

    # --------------------------------

    def refresh(self):
        """Reload groups from the workspace GroupManager."""

        self._refreshing = True
        self.table.setRowCount(0)

        for group in self.workspace.group_manager.groups:
            self._add_group_row(group)

        self._select_current_group()
        self.table.resizeColumnsToContents()
        self._refreshing = False

    # --------------------------------

    def create_group(self):
        """Create a group from the current selection."""

        selected = list(getattr(self.workspace.selection, "selected", []))

        if not selected:
            self._changed()
            return

        name, ok = QInputDialog.getText(
            self,
            "Create Group",
            "Group Name",
            text=self.workspace.group_manager.unique_name("Group"),
        )

        if ok and name.strip():
            self.workspace.command_manager.execute(
                CreateGroupCommand(self.workspace, name, selected)
            )
            self._changed()

    # --------------------------------

    def rename_group(self):
        """Rename the selected group."""

        group = self._selected_group()

        if group is None:
            return

        name, ok = QInputDialog.getText(
            self,
            "Rename Group",
            "Group Name",
            text=group.name,
        )

        if ok and name.strip():
            self.workspace.command_manager.execute(
                RenameGroupCommand(self.workspace, group, name)
            )
            self._changed()

    # --------------------------------

    def delete_group(self):
        """Delete the selected group without deleting its entities."""

        group = self._selected_group()

        if group is not None:
            self.workspace.command_manager.execute(
                DeleteGroupCommand(self.workspace, group)
            )
            self._changed()

    # --------------------------------

    def ungroup(self):
        """Remove the selected group membership."""

        group = self._selected_group()

        if group is not None:
            self.workspace.command_manager.execute(
                UngroupCommand(self.workspace, group)
            )
            self._changed()

    # --------------------------------

    def _add_group_row(self, group):

        row = self.table.rowCount()
        self.table.insertRow(row)

        values = [
            group.name,
            str(group.id),
            str(group.count),
        ]

        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, group.id)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, column, item)

    # --------------------------------

    def _selected_group(self):

        item = self.table.currentItem()

        if item is None:
            row = self.table.currentRow()
            item = self.table.item(row, 0) if row >= 0 else None

        if item is None:
            return None

        return self.workspace.group_manager.get_by_id(item.data(Qt.UserRole))

    # --------------------------------

    def _selection_changed(self):

        if self._refreshing:
            return

        group = self._selected_group()

        if group is not None:
            self.workspace.group_manager.set_current(group)

    # --------------------------------

    def _select_current_group(self):

        current = self.workspace.group_manager.current

        if current is None:
            return

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)

            if item and item.data(Qt.UserRole) == current.id:
                self.table.setCurrentCell(row, 0)
                return

    # --------------------------------

    def _changed(self):

        self.refresh()

        if self.on_change:
            self.on_change()
