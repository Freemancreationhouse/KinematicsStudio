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


class PatternManagerPanel(QWidget):
    """Dockable panel for workspace hatch pattern definitions."""

    COLUMNS = [
        "Current",
        "Pattern Name",
        "Type",
        "Scale",
        "Angle",
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
        self.new_button = QPushButton("New Pattern")
        self.current_button = QPushButton("Set Current Pattern")

        for button in (self.new_button, self.current_button):
            toolbar.addWidget(button)

        layout.addLayout(toolbar)

        self.new_button.clicked.connect(self.new_pattern)
        self.current_button.clicked.connect(self.set_current_pattern)

        self.refresh()

    # --------------------------------

    def refresh(self):
        """Reload pattern rows from the workspace PatternManager."""

        manager = self.workspace.pattern_manager
        self.table.setRowCount(0)

        for pattern in manager.patterns:
            self._add_pattern_row(pattern)

        self.table.resizeColumnsToContents()

    # --------------------------------

    def new_pattern(self):
        """Register a custom line pattern definition."""

        name, ok = QInputDialog.getText(
            self,
            "New Hatch Pattern",
            "Pattern Name",
            text=self._next_pattern_name(),
        )

        if ok and name.strip():
            self.workspace.pattern_manager.create(name.strip())
            self._changed()

    # --------------------------------

    def set_current_pattern(self):
        """Make the selected pattern current for future hatches."""

        pattern = self._selected_pattern()

        if pattern is not None and self.workspace.set_current_pattern(pattern):
            self._changed()

    # --------------------------------

    def _add_pattern_row(self, pattern):

        row = self.table.rowCount()
        self.table.insertRow(row)

        values = [
            "✓" if pattern is self.workspace.current_pattern else "",
            pattern.name,
            pattern.pattern_type,
            self._number(pattern.scale),
            self._number(pattern.angle),
        ]

        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, pattern.name)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, column, item)

    # --------------------------------

    def _selected_pattern(self):

        item = self.table.currentItem()

        if item is None:
            row = self.table.currentRow()
            item = self.table.item(row, 0) if row >= 0 else None

        if item is None:
            return None

        return self.workspace.pattern_manager.get(item.data(Qt.UserRole))

    # --------------------------------

    def _next_pattern_name(self):

        index = 1
        manager = self.workspace.pattern_manager

        while manager.get(f"Custom Pattern {index}") is not None:
            index += 1

        return f"Custom Pattern {index}"

    # --------------------------------

    def _changed(self):

        self.refresh()

        if self.on_change:
            self.on_change()

    # --------------------------------

    def _number(self, value):

        return f"{float(value):.2f}"
