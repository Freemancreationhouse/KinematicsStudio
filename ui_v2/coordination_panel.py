from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)
from datetime import datetime, timezone
from uuid import uuid4

from engine.commands import UpdateCoordinationUICommand
from engine.references3d import CoordinationRule


class CoordinationPanel(QWidget):
    """Dockable panel for reference alignment and coordination settings."""

    def __init__(self, workspace, on_change=None):

        super().__init__()

        self.workspace = workspace
        self.on_change = on_change
        self._build()
        self.refresh()

    # --------------------------------

    def _build(self):

        layout = QFormLayout(self)
        self.reference = QComboBox()
        self.alignment = QComboBox()
        self.alignment.addItems(["WCS", "Shared Coordinates", "UCS", "Manual"])
        self.origin_mapping = QComboBox()
        self.origin_mapping.addItems(["Model Origin", "World Origin", "Shared Origin", "Manual Origin"])
        self.coordinate_display = QComboBox()
        self.coordinate_display.addItems(["WCS", "UCS", "Local Reference"])
        self.offset_x = self._number()
        self.offset_y = self._number()
        self.offset_z = self._number()
        self.rotation_x = self._number()
        self.rotation_y = self._number()
        self.rotation_z = self._number()
        self.scale_x = self._number(1.0)
        self.scale_y = self._number(1.0)
        self.scale_z = self._number(1.0)
        self.validation = QLabel("Unchecked")
        self.conflict = QLabel("")
        buttons = QHBoxLayout()
        self.apply_button = QPushButton("Apply Coordination")
        self.validate_button = QPushButton("Validate")
        self.conflict_button = QPushButton("Conflict Placeholder")
        buttons.addWidget(self.apply_button)
        buttons.addWidget(self.validate_button)
        buttons.addWidget(self.conflict_button)

        layout.addRow("Reference", self.reference)
        layout.addRow("Alignment", self.alignment)
        layout.addRow("Origin Mapping", self.origin_mapping)
        layout.addRow("Coordinate Display", self.coordinate_display)
        layout.addRow("Offset X", self.offset_x)
        layout.addRow("Offset Y", self.offset_y)
        layout.addRow("Offset Z", self.offset_z)
        layout.addRow("Rotation X", self.rotation_x)
        layout.addRow("Rotation Y", self.rotation_y)
        layout.addRow("Rotation Z", self.rotation_z)
        layout.addRow("Scale X", self.scale_x)
        layout.addRow("Scale Y", self.scale_y)
        layout.addRow("Scale Z", self.scale_z)
        layout.addRow("Validation Status", self.validation)
        layout.addRow("Conflict", self.conflict)
        layout.addRow(buttons)

        self.reference.currentTextChanged.connect(self._reference_changed)
        self.apply_button.clicked.connect(self.apply_coordination)
        self.validate_button.clicked.connect(self.validate_reference)
        self.conflict_button.clicked.connect(self.add_conflict_placeholder)

    # --------------------------------

    def refresh(self):
        """Refresh selectable references."""

        current = self.reference.currentData()
        self.reference.blockSignals(True)
        self.reference.clear()

        for model in self.workspace.reference_manager.models:
            self.reference.addItem(model.name, model.id)

        if current:
            index = self.reference.findData(current)

            if index >= 0:
                self.reference.setCurrentIndex(index)

        self.reference.blockSignals(False)
        self._reference_changed()

    # --------------------------------

    def apply_coordination(self):
        """Apply reference alignment, offset, rotation and scale settings."""

        model = self.selected_model()

        if model is None:
            return

        before = dict(model.coordination_ui_settings)
        after = self._settings()
        rule = CoordinationRule(
            "Reference Coordination",
            "Reference Coordination",
            settings={
                "reference_id": model.id,
                "alignment": after["alignment"],
                "origin_mapping": after["origin_mapping"],
                "coordinate_display": after["coordinate_display"],
                "offset": after["offset"],
                "rotation": after["rotation"],
                "scale": after["scale"],
            },
        )
        self.workspace.command_manager.execute(
            UpdateCoordinationUICommand(self.workspace, model, before, after, rule)
        )
        self._changed()

    # --------------------------------

    def validate_reference(self):
        """Store successful validation status for the selected reference."""

        model = self.selected_model()

        if model is None:
            return

        before = dict(model.coordination_ui_settings)
        after = dict(before)
        after["validation_status"] = "Valid"
        self.workspace.command_manager.execute(
            UpdateCoordinationUICommand(self.workspace, model, before, after)
        )
        self._changed()

    # --------------------------------

    def add_conflict_placeholder(self, text="Potential reference conflict"):
        """Store a future-ready reference conflict placeholder."""

        model = self.selected_model()

        if model is None:
            return

        before = dict(model.coordination_ui_settings)
        conflict = {
            "id": str(uuid4()),
            "description": text,
            "status": "Placeholder",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        after = dict(before)
        after["conflict_placeholder"] = conflict["description"]
        self.workspace.command_manager.execute(
            UpdateCoordinationUICommand(self.workspace, model, before, after, conflict=conflict)
        )
        self._changed()

    # --------------------------------

    def selected_model(self):
        """Return the selected reference model."""

        return self.workspace.reference_manager.get_model(self.reference.currentData())

    # --------------------------------

    def _reference_changed(self):

        model = self.selected_model()

        if model is None:
            return

        settings = model.coordination_ui_settings
        self.alignment.setCurrentText(settings.get("alignment", "WCS"))
        self.origin_mapping.setCurrentText(settings.get("origin_mapping", "Model Origin"))
        self.coordinate_display.setCurrentText(settings.get("coordinate_display", "WCS"))
        self.validation.setText(settings.get("validation_status", "Unchecked"))
        self.conflict.setText(settings.get("conflict_placeholder", ""))

    # --------------------------------

    def _settings(self):

        return {
            "alignment": self.alignment.currentText(),
            "origin_mapping": self.origin_mapping.currentText(),
            "coordinate_display": self.coordinate_display.currentText(),
            "offset": self._vector(self.offset_x, self.offset_y, self.offset_z),
            "rotation": self._vector(self.rotation_x, self.rotation_y, self.rotation_z),
            "scale": self._vector(self.scale_x, self.scale_y, self.scale_z),
            "validation_status": "Valid",
            "conflict_placeholder": self.conflict.text(),
        }

    # --------------------------------

    def _number(self, value=0.0):

        field = QDoubleSpinBox()
        field.setRange(-1000000.0, 1000000.0)
        field.setDecimals(4)
        field.setValue(value)

        return field

    # --------------------------------

    def _vector(self, x, y, z):

        return {
            "x": x.value(),
            "y": y.value(),
            "z": z.value(),
        }

    # --------------------------------

    def _changed(self):

        self.refresh()

        if self.on_change:
            self.on_change()
