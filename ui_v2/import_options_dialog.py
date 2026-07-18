from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from engine.import3d import ImportSettings


class ImportOptionsDialog(QDialog):
    """Dialog for configuring external 3D reference import options."""

    def __init__(self, parent=None, settings=None, path=""):

        super().__init__(parent)

        self.setWindowTitle("Import 3D Reference")
        self.path = QLineEdit(path)
        self.path.setReadOnly(True)
        self.units = QComboBox()
        self.units.addItems(["model", "millimeter", "centimeter", "meter", "inch", "foot"])
        self.scale = QDoubleSpinBox()
        self.scale.setRange(0.0001, 1000000.0)
        self.scale.setDecimals(4)
        self.scale.setValue(1.0)
        self.up_axis = QComboBox()
        self.up_axis.addItems(["X", "Y", "Z"])
        self.forward_axis = QComboBox()
        self.forward_axis.addItems(["X", "Y", "Z", "-X", "-Y", "-Z"])
        self.center_model = QCheckBox()
        self.merge_meshes = QCheckBox()
        self.keep_hierarchy = QCheckBox()
        self.generate_normals = QCheckBox()
        self.generate_bounds = QCheckBox()
        self.import_hidden_objects = QCheckBox()
        self.preview_metadata = QLabel("")
        self.remember_settings = QCheckBox()

        self._build()
        self.set_settings(settings or ImportSettings())

    # --------------------------------

    def _build(self):

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)
        form.addRow("Path", self.path)
        form.addRow("Units", self.units)
        form.addRow("Scale", self.scale)
        form.addRow("Up Axis", self.up_axis)
        form.addRow("Forward Axis", self.forward_axis)
        form.addRow("Center Model", self.center_model)
        form.addRow("Merge Meshes", self.merge_meshes)
        form.addRow("Keep Hierarchy", self.keep_hierarchy)
        form.addRow("Generate Normals", self.generate_normals)
        form.addRow("Generate Bounds", self.generate_bounds)
        form.addRow("Import Hidden Objects", self.import_hidden_objects)
        form.addRow("Preview Metadata", self.preview_metadata)
        form.addRow("Remember Settings", self.remember_settings)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # --------------------------------

    def set_settings(self, settings):
        """Populate controls from import settings."""

        self.units.setCurrentText(settings.units)
        self.scale.setValue(settings.scale)
        self.up_axis.setCurrentText(settings.up_axis)
        self.forward_axis.setCurrentText(settings.forward_axis)
        self.center_model.setChecked(settings.center_model)
        self.merge_meshes.setChecked(settings.merge_meshes)
        self.keep_hierarchy.setChecked(settings.keep_hierarchy)
        self.generate_normals.setChecked(settings.generate_normals)
        self.generate_bounds.setChecked(settings.generate_bounds)
        self.import_hidden_objects.setChecked(settings.import_hidden_objects)
        self.remember_settings.setChecked(settings.remember_settings)
        self.preview_metadata.setText(self._metadata_text(settings))

    # --------------------------------

    def settings(self):
        """Return configured import settings."""

        return ImportSettings(
            self.units.currentText(),
            self.scale.value(),
            self.up_axis.currentText(),
            self.forward_axis.currentText(),
            self.center_model.isChecked(),
            self.merge_meshes.isChecked(),
            self.keep_hierarchy.isChecked(),
            self.generate_normals.isChecked(),
            self.generate_bounds.isChecked(),
            self.import_hidden_objects.isChecked(),
            True,
            self.remember_settings.isChecked(),
        )

    # --------------------------------

    def _metadata_text(self, settings):

        return (
            f"Units: {settings.units} | Scale: {settings.scale:g} | "
            f"Axes: {settings.up_axis} up / {settings.forward_axis} forward"
        )
