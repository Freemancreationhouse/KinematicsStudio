from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QWidget,
)


class ProjectManagerPanel(QWidget):
    """Dockable panel that displays active project metadata."""

    FIELDS = [
        ("current_project", "Current Project"),
        ("file_path", "File Path"),
        ("version", "Version"),
        ("last_save_time", "Last Save Time"),
        ("autosave_status", "Autosave Status"),
        ("entity_count", "Entity Count"),
        ("layer_count", "Layer Count"),
        ("block_count", "Block Count"),
        ("group_count", "Group Count"),
    ]

    def __init__(self, app):

        super().__init__()

        self.app = app
        self._fields = {}

        layout = QFormLayout(self)
        layout.addRow(QLabel("Project"), QLabel("Status"))

        for key, label in self.FIELDS:
            field = QLineEdit()
            field.setReadOnly(True)
            self._fields[key] = field
            layout.addRow(label, field)

        self.refresh()

    # --------------------------------

    def refresh(self):
        """Refresh project metadata from the CAD application facade."""

        info = self.app.project_info()

        for key, field in self._fields.items():
            field.setText(str(info.get(key, "")))

    # --------------------------------

    def value(self, key):
        """Return displayed text for tests and lightweight UI checks."""

        field = self._fields.get(key)

        return field.text() if field is not None else ""
