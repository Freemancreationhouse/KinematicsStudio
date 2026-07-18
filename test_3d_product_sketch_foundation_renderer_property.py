import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.geometry import Vector3
from engine.product import Constraint, ProductPart, Sketch, SketchDimension, SketchLine
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
manager = workspace.product_manager
manager.create_document("Rendered Sketch Product", "mm", 3)
part = manager.add_part(ProductPart("Rendered Sketch Part", "mesh-rendered-sketch", location=Vector3()))
sketch = manager.add_sketch_item(Sketch("Rendered Sketch", part.id, location=Vector3()))
line = manager.add_sketch_item(SketchLine("Rendered Sketch Line", sketch.id, Vector3(), Vector3(2.0, 0.0, 0.0)))
constraint = manager.add_sketch_constraint_item(Constraint("Horizontal", sketch.id, [line.id]))
dimension = manager.add_sketch_dimension_item(SketchDimension("Linear", 2.0, "mm", sketch.id, [line.id]))
manager.sketch_manager.activate(sketch)
workspace.selection.select(sketch)

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
panel.show_selection([part])
assert "Sketches: 1" in panel.radius.text()

panel.show_selection([sketch])
assert panel.type.text() == "Sketch"
assert "Geometry: 1" in panel.radius.text()
assert "Constraints: 1" in panel.radius.text()
assert "Dimensions: 1" in panel.radius.text()
assert panel.line_weight.text() == "Active"

panel.show_selection([line])
assert panel.type.text() == "SketchLine"
assert "Geometry: Line" in panel.line_type.text()

panel.show_selection([constraint])
assert panel.type.text() == "SketchConstraint"
assert "Constraint: Horizontal" in panel.line_type.text()

panel.show_selection([dimension])
assert panel.type.text() == "SketchDimension"
assert "Linear: 2.00 mm" in panel.length.text()

print("3d-product-sketch-foundation-renderer-property-ok")
