import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.references3d import ReferenceModel
from engine.workspace.workspace import Workspace
from ui_v2.coordination_panel import CoordinationPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
model = workspace.reference_manager.add_model(ReferenceModel("Coord Ref", "coord.obj"))
workspace.reference_manager.create_instance(model)
panel = CoordinationPanel(workspace)
panel.reference.setCurrentText("Coord Ref")
panel.alignment.setCurrentText("Shared Coordinates")
panel.origin_mapping.setCurrentText("Shared Origin")
panel.coordinate_display.setCurrentText("Local Reference")
panel.offset_x.setValue(10.0)
panel.rotation_z.setValue(45.0)
panel.scale_x.setValue(2.0)
panel.apply_coordination()

assert model.coordination_ui_settings["alignment"] == "Shared Coordinates"
assert model.coordination_ui_settings["offset"]["x"] == 10.0
assert model.coordination_ui_settings["rotation"]["z"] == 45.0
assert model.coordination_ui_settings["scale"]["x"] == 2.0
assert workspace.coordination_manager.rules[-1].rule_type == "Reference Coordination"

workspace.command_manager.undo()
assert model.coordination_ui_settings["alignment"] == "WCS"

panel.validate_reference()
assert model.coordination_ui_settings["validation_status"] == "Valid"

panel.add_conflict_placeholder("Coordination placeholder")
assert workspace.coordination_manager.conflicts[-1]["description"] == "Coordination placeholder"
assert model.coordination_ui_settings["conflict_placeholder"] == "Coordination placeholder"
workspace.command_manager.undo()
assert workspace.coordination_manager.conflicts == []

print("3d-reference-coordination-ui-ok")
