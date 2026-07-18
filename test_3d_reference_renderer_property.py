import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.geometry import Vector3
from engine.render import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.references3d import ReferenceTransform
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
model = workspace.reference_manager.create_model("Site Model", "C:/refs/site.ifc")
instance = workspace.reference_manager.create_instance(
    model,
    ReferenceTransform(Vector3(0.0, 0.0, 0.0)),
)
workspace.assign_layer(instance)
workspace.selection.select(instance)

renderer = Renderer3D()
renderer.camera = Camera3D()
image = QImage(320, 240, QImage.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer.render(painter, workspace, 320, 240)
painter.end()

panel = PropertyPanel()
panel.set_workspace(workspace)
panel.show_selection([instance])

assert instance in workspace.visible_references()
assert instance in workspace.selectable_3d_entities()
assert panel.type.text() == "ReferenceInstance"
assert panel.content.text() == "Site Model"

print("3d-reference-renderer-property-ok")
