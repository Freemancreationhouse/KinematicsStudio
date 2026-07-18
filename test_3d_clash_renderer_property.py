import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.commands import RunClashDetectionCommand
from engine.geometry import Vector3
from engine.references3d import ReferenceTransform
from engine.render import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
model_a = workspace.reference_manager.create_model("A", "a.obj")
model_b = workspace.reference_manager.create_model("B", "b.obj")
workspace.reference_manager.create_instance(model_a, ReferenceTransform(Vector3()))
workspace.reference_manager.create_instance(model_b, ReferenceTransform(Vector3()))
workspace.command_manager.execute(RunClashDetectionCommand(workspace))
clash = workspace.clash_manager.results[0]
workspace.selection.select(clash)

renderer = Renderer3D()
renderer.camera = Camera3D()
image = QImage(320, 240, QImage.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer.render(painter, workspace, 320, 240)
painter.end()

panel = PropertyPanel()
panel.set_workspace(workspace)
panel.show_selection([clash])

assert clash in workspace.selectable_3d_entities()
assert panel.type.text() == "ClashResult"
assert "Reference Clash" in panel.alignment.text()
assert "vs" in panel.line_type.text()

print("3d-clash-renderer-property-ok")
