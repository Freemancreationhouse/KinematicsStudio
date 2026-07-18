import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.bim import DrawingSheet, FloorPlanView, Level, ViewTemplate, ViewportReference
from engine.geometry import Vector3
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.bim_manager.create_project("Rendered Documentation BIM")
level = workspace.bim_manager.add_level(Level("Rendered Level", 0.0))
template = workspace.bim_manager.add_view_template(ViewTemplate("Rendered Plan Template", "FloorPlan"))
view = workspace.bim_manager.add_view(FloorPlanView("Rendered Plan", level.id, template.id, location=Vector3(15.0, 0.0, 0.0)))
sheet = DrawingSheet("Rendered Sheet", "A-401", "Rendered Title Block", Vector3(30.0, 0.0, 0.0))
sheet.add_viewport(ViewportReference(view.id))
workspace.bim_manager.add_sheet(sheet)
workspace.selection.select(view)

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
panel.show_selection([view])

assert panel.type.text() == "FloorPlanView"
assert panel.content.text() == "View: Rendered Plan"
assert panel.alignment.text() == "View Type: FloorPlan"
assert "Scale: 1:100" in panel.line_weight.text()

panel.show_selection([sheet])
assert panel.type.text() == "DrawingSheet"
assert panel.content.text() == "Sheet: A-401"
assert "Title Block: Rendered Title Block" in panel.alignment.text()
assert "Viewports: 1" in panel.dimension_style.text()

print("3d-bim-documentation-renderer-property-ok")
