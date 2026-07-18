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


class DimensionManagerPanel(QWidget):
    """Dockable panel for managing workspace dimension styles."""

    COLUMNS = [
        "Current",
        "Style Name",
        "Text Height",
        "Arrow Size",
        "Precision",
        "Units",
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
        self.new_button = QPushButton("New Style")
        self.rename_button = QPushButton("Rename Style")
        self.delete_button = QPushButton("Delete Style")
        self.current_button = QPushButton("Set Current Style")

        for button in (
            self.new_button,
            self.rename_button,
            self.delete_button,
            self.current_button,
        ):
            toolbar.addWidget(button)

        layout.addLayout(toolbar)

        self.new_button.clicked.connect(self.new_style)
        self.rename_button.clicked.connect(self.rename_style)
        self.delete_button.clicked.connect(self.delete_style)
        self.current_button.clicked.connect(self.set_current_style)

        self.refresh()

    # --------------------------------

    def refresh(self):
        """Reload dimension style rows from the workspace manager."""

        self._refreshing = True
        manager = self.workspace.dimension_style_manager
        self.table.setRowCount(0)

        for style in manager.styles:
            self._add_style_row(style)

        self.table.resizeColumnsToContents()
        self._refreshing = False

    # --------------------------------

    def new_style(self):
        """Create a uniquely named dimension style."""

        name, ok = QInputDialog.getText(
            self,
            "New Dimension Style",
            "Style Name",
            text=self._next_style_name(),
        )

        if ok and name.strip():
            self.workspace.create_dimension_style(name.strip())
            self._changed()

    # --------------------------------

    def rename_style(self):
        """Rename the selected non-default style."""

        style = self._selected_style()

        if style is None or style.name == "Standard":
            return

        name, ok = QInputDialog.getText(
            self,
            "Rename Dimension Style",
            "Style Name",
            text=style.name,
        )

        if ok and self.workspace.rename_dimension_style(style, name):
            self._changed()

    # --------------------------------

    def delete_style(self):
        """Delete the selected non-default style."""

        style = self._selected_style()

        if style is not None and self.workspace.delete_dimension_style(style):
            self._changed()

    # --------------------------------

    def set_current_style(self):
        """Make the selected style current for future dimensions."""

        style = self._selected_style()

        if style is not None and self.workspace.set_current_dimension_style(style):
            self._changed()

    # --------------------------------

    def _add_style_row(self, style):

        row = self.table.rowCount()
        self.table.insertRow(row)

        values = [
            "✓" if style is self.workspace.current_dimension_style else "",
            style.name,
            self._number(style.text_height),
            self._number(style.arrow_size),
            str(style.precision),
            style.units,
        ]

        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, style.id)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, column, item)

    # --------------------------------

    def _selected_style(self):

        item = self.table.currentItem()

        if item is None:
            row = self.table.currentRow()
            item = self.table.item(row, 0) if row >= 0 else None

        if item is None:
            return None

        return self.workspace.dimension_style_manager.get_by_id(item.data(Qt.UserRole))

    # --------------------------------

    def _next_style_name(self):

        index = 1
        manager = self.workspace.dimension_style_manager

        while manager.get(f"Dimension Style {index}") is not None:
            index += 1

        return f"Dimension Style {index}"

    # --------------------------------

    def _changed(self):

        self.refresh()

        if self.on_change:
            self.on_change()

    # --------------------------------

    def _number(self, value):

        return f"{float(value):.2f}"
