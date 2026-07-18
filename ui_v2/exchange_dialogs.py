from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)

from engine.import3d import ImportSettings


class ExchangeImportDialog(QDialog):
    """Professional CAD exchange import dialog using ImportSettings."""

    def __init__(self, parent=None, workspace=None, path="", settings=None):

        super().__init__(parent)

        self.workspace = workspace
        self.setWindowTitle("Import CAD Exchange")
        self.path = QLineEdit(path)
        self.path.setReadOnly(True)
        self.profile = QComboBox()
        self.format = QComboBox()
        self.format.addItems(["Auto", "SKP", "3DM", "STEP", "IGES", "SAT", "STL", "OBJ", "FBX", "Alembic"])
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
        self.reference_import = QCheckBox()
        self.merge_meshes = QCheckBox()
        self.keep_hierarchy = QCheckBox()
        self.center_model = QCheckBox()
        self.remember_settings = QCheckBox()
        self.metadata_preview = QLabel("")
        self.summary = QLabel("")
        self._build()
        self._load_profiles()
        self.set_settings(settings or ImportSettings())

    def _build(self):

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)
        form.addRow("Path", self.path)
        form.addRow("Profile", self.profile)
        form.addRow("Format", self.format)
        form.addRow("Units", self.units)
        form.addRow("Scale", self.scale)
        form.addRow("Up Axis", self.up_axis)
        form.addRow("Forward Axis", self.forward_axis)
        form.addRow("Reference Import", self.reference_import)
        form.addRow("Merge Meshes", self.merge_meshes)
        form.addRow("Keep Hierarchy", self.keep_hierarchy)
        form.addRow("Center Model", self.center_model)
        form.addRow("Remember Last Settings", self.remember_settings)
        form.addRow("Metadata Preview", self.metadata_preview)
        form.addRow("Exchange Summary", self.summary)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def set_settings(self, settings):
        """Populate controls from settings."""

        self.units.setCurrentText(settings.units)
        self.scale.setValue(settings.scale)
        self.up_axis.setCurrentText(settings.up_axis)
        self.forward_axis.setCurrentText(settings.forward_axis)
        self.center_model.setChecked(settings.center_model)
        self.merge_meshes.setChecked(settings.merge_meshes)
        self.keep_hierarchy.setChecked(settings.keep_hierarchy)
        self.reference_import.setChecked(True)
        self.remember_settings.setChecked(settings.remember_settings)
        self.metadata_preview.setText(self._metadata_text())
        self.summary.setText(self._summary_text(settings))

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
            True,
            True,
            False,
            True,
            self.remember_settings.isChecked(),
        )

    def profile_name(self):
        """Return selected profile name."""

        return self.profile.currentText() or "Default"

    def _load_profiles(self):

        self.profile.clear()
        profiles = {}

        if self.workspace is not None:
            profiles = self.workspace.import_manager.validation_manager.profiles

        self.profile.addItems(sorted(profiles.keys()) or ["Default"])

    def _metadata_text(self):

        return f"Format: {self.format.currentText()} | Path: {self.path.text() or 'Not selected'}"

    def _summary_text(self, settings):

        return (
            f"Units: {settings.units} | Scale: {settings.scale:g} | "
            f"Axes: {settings.up_axis}/{settings.forward_axis}"
        )


class ExchangeExportDialog(QDialog):
    """Professional CAD exchange export dialog using ExportManager formats."""

    def __init__(self, parent=None, workspace=None, path=""):

        super().__init__(parent)

        self.workspace = workspace
        self.setWindowTitle("Export CAD Exchange")
        self.path = QLineEdit(path)
        self.path.setReadOnly(True)
        self.profile = QComboBox()
        self.format = QComboBox()
        self.format.addItems(["STEP", "IGES", "SAT", "OBJ", "STL", "SKP", "3DM", "FBX", "Alembic"])
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
        self.merge_meshes = QCheckBox()
        self.metadata_preview = QLabel("")
        self.summary = QLabel("")
        self.remember_settings = QCheckBox()
        self._build()
        self._load_profiles()

    def _build(self):

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)
        form.addRow("Path", self.path)
        form.addRow("Profile", self.profile)
        form.addRow("Format", self.format)
        form.addRow("Units", self.units)
        form.addRow("Scale", self.scale)
        form.addRow("Up Axis", self.up_axis)
        form.addRow("Forward Axis", self.forward_axis)
        form.addRow("Merge Options", self.merge_meshes)
        form.addRow("Metadata Preview", self.metadata_preview)
        form.addRow("Exchange Summary", self.summary)
        form.addRow("Remember Last Settings", self.remember_settings)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.format.currentTextChanged.connect(self._refresh_summary)
        self._refresh_summary()

    def format_name(self):
        """Return selected export format."""

        mapping = {"Alembic": "abc"}

        return mapping.get(self.format.currentText(), self.format.currentText().lower())

    def profile_settings(self):
        """Return profile settings for persistence."""

        return {
            "format": self.format.currentText(),
            "units": self.units.currentText(),
            "scale": self.scale.value(),
            "up_axis": self.up_axis.currentText(),
            "forward_axis": self.forward_axis.currentText(),
            "merge_meshes": self.merge_meshes.isChecked(),
        }

    def _load_profiles(self):

        self.profile.clear()
        profiles = {}

        if self.workspace is not None:
            profiles = self.workspace.import_manager.validation_manager.profiles

        self.profile.addItems(sorted(profiles.keys()) or ["Default"])

    def _refresh_summary(self):

        self.metadata_preview.setText(f"Format: {self.format.currentText()}")
        self.summary.setText(
            f"Export {self.format.currentText()} using existing ExportManager."
        )


class ExchangeValidationReportPanel(QDialog):
    """Simple validation report viewer."""

    def __init__(self, parent=None, report=None):

        super().__init__(parent)

        self.report = report
        self.setWindowTitle("Exchange Validation Report")
        layout = QVBoxLayout(self)
        self.summary = QLabel(self._summary())
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlainText(self._details())
        layout.addWidget(self.summary)
        layout.addWidget(self.details)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _summary(self):

        if self.report is None:
            return "No validation report."

        summary = self.report.summary

        return (
            f"Issues: {summary.get('issues', 0)} | "
            f"Warnings: {summary.get('warnings', 0)} | "
            f"Errors: {summary.get('errors', 0)}"
        )

    def _details(self):

        if self.report is None:
            return ""

        return "\n".join(
            f"[{issue.severity}] {issue.category}: {issue.message}"
            for issue in self.report.issues
        )
