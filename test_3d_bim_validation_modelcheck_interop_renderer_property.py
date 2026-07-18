import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.bim import BIMInstance, ExchangeRule, ModelCheckRule, ValidationRule
from engine.geometry import Vector3
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.bim_manager.create_project("Rendered Batch K BIM")
instance = BIMInstance("Rendered Validation Item", location=Vector3(0.0, 0.0, 0.0))
workspace.bim_manager.add_instance(instance)
workspace.bim_manager.add_validation_item(ValidationRule("Rendered Classification", "Classification"))
workspace.bim_manager.validation_manager.run()
workspace.bim_manager.add_model_check_item(ModelCheckRule("Rendered Material", "Missing Materials"))
workspace.bim_manager.model_check_manager.run()
workspace.bim_manager.add_interoperability_item(ExchangeRule("Rendered IFC", "IFC readiness"))
workspace.bim_manager.interoperability_manager.statistics()
workspace.selection.select(instance)

renderer = Renderer3D()
renderer.camera = Camera3D()
renderer.camera.resize(640, 480)

image = QImage(640, 480, QImage.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer.render(painter, workspace, 640, 480)
painter.end()

panel = PropertyPanel()
panel.set_workspace(workspace)
panel.show_selection([instance])

assert panel.type.text() == "BIMInstance"
assert panel.content.text() == "Rendered Validation Item"
assert "Validation: 1" in panel.radius.text()
assert "Model Checks: 1" in panel.radius.text()
assert "Exchange Ready: 4" in panel.diameter.text()
assert "Blocked: 1" in panel.diameter.text()

print("3d-bim-validation-modelcheck-interop-renderer-property-ok")
