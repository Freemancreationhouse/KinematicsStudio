import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.geometry import Vector3
from engine.product import Constraint, ProductPart, SketchLine, SketchPlane
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])
workspace = Workspace()
manager = workspace.product_manager
manager.create_document("Rendered Sketch Solver", "mm", 3)
part = manager.add_part(ProductPart("Rendered Sketch Part", "rendered-sketch-mesh", location=Vector3()))
plane = manager.add_sketch_item(SketchPlane("Rendered Plane"))
sketch = manager.sketch_manager.create_sketch("Rendered Solver Sketch", part, plane)
line = manager.add_sketch_item(SketchLine("Rendered Solver Line", sketch.id, Vector3(), Vector3(2.0, 0.0, 0.0)))
manager.add_sketch_constraint_item(Constraint("Horizontal", sketch.id, [line.id]))

parametric_engine = manager.parametric_manager.create_engine("Rendered Sketch Engine")
execution_engine = manager.parametric_manager.create_execution_engine("Rendered Sketch Execution", parametric_engine)
live_solver = manager.parametric_manager.create_solver("Rendered Sketch Live Solver", parametric_engine)
sketch_solver = manager.parametric_manager.create_sketch_solver("Rendered Sketch Solver", parametric_engine, execution_engine, live_solver)
session = manager.parametric_manager.solve_sketch(sketch, sketch_solver, execution_engine=execution_engine)

renderer = Renderer3D()
for item in (sketch_solver, session):
    assert renderer._product_color(item, manager).isValid()

panel = PropertyPanel()
panel.set_workspace(workspace)
for item in (sketch_solver, session, sketch):
    panel.show_selection([item])
    assert panel.radius.text()
    assert panel.line_weight.text()

assert sketch_solver in workspace.visible_product_objects()
assert session in workspace.visible_product_objects()
assert len(workspace.scene3d.entities()) == 0
assert part.mesh_entity_id == "rendered-sketch-mesh"

print("3d-parametric-sketch-solver-renderer-property-ok")
