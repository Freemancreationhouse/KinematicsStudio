import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.geometry import Vector3
from engine.product import Component, ComponentCategory, ComponentType, ProductPart
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.product_manager.create_document("Rendered Product", "mm", 3)
part = ProductPart("Rendered Part", "mesh-rendered", location=Vector3(0.0, 0.0, 0.0))
workspace.product_manager.add_part(part)
category = workspace.product_manager.add_component_item(ComponentCategory("Mechanical Parts", color="#4db6ac"))
component_type = workspace.product_manager.add_component_item(ComponentType("Rendered Type", category.id))
component = workspace.product_manager.add_component_item(
    Component("Rendered Component", part.id, component_type.id, category.id)
)
workspace.selection.select(part)

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

assert part in workspace.selectable_3d_entities()
assert component in workspace.selectable_3d_entities()
assert panel.type.text() == "ProductPart"
assert panel.content.text() == "Rendered Part"
assert "Components: 1" in panel.radius.text()
assert "Parts: 1" in panel.diameter.text()
assert "Components: 1" in panel.diameter.text()

panel.show_selection([component])
assert panel.type.text() == "Component"
assert "Type: Rendered Type" in panel.line_type.text()
assert "Category: Mechanical Parts" in panel.line_weight.text()

print("3d-product-foundation-renderer-property-ok")
