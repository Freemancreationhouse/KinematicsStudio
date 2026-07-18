import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ComputedParameter, GlobalParameter, ParameterCategory, ProductPart
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="Rendered Parameter Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
document = manager.create_document("Rendered Parameter Product")
part = manager.add_part(ProductPart("Rendered Parameter Part", "Rendered Parameter Mesh"))
category = manager.parameter_manager.add_item(ParameterCategory("Rendered Category", "Length"))
width = manager.parameter_manager.add_item(GlobalParameter("Rendered Width", 42.0, parameter_type="Length", unit="mm", owner_id=document.id, category_id=category.id))
area = manager.parameter_manager.add_item(ComputedParameter("Rendered Area", 0.0, parameter_type="Area", unit="mm^2", owner_id=part.id, category_id=category.id))
expression = manager.parameter_manager.create_expression("Rendered Expression", "Rendered Width * 2", area, [width], [part], unit="mm^2")
binding = manager.parameter_manager.bind_parameter(width, area, "ParameterToExpression", expression)
workspace.selection.select(width)

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

panel.show_selection([width])
assert panel.type.text() == "Parameter"
assert "Type: Length" in panel.radius.text()
assert "No evaluation" in panel.line_weight.text()

panel.show_selection([category])
assert panel.type.text() == "ParameterCategory"
assert "Parameters: 2" in panel.height.text()

panel.show_selection([expression])
assert panel.type.text() == "Expression"
assert "No parsing" in panel.line_weight.text()

panel.show_selection([binding])
assert panel.type.text() == "ExpressionBinding"
assert "Relationship storage only" in panel.line_weight.text()

assert width in workspace.visible_product_objects()
assert expression in workspace.visible_product_objects()
assert len(workspace.scene3d.entities()) == 1

print("3d-parametric-parameters-renderer-property-ok")
