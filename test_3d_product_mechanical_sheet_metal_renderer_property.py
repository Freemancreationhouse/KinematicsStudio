import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import EngineeringMaterial, ProductPart
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(4.0, 2.0, 0.5), name="Rendered Mechanical Sheet Mesh")
workspace.add_3d_entity(mesh)
manager = workspace.product_manager
manager.create_document("Rendered Mechanical Sheet Product")
part = manager.add_part(ProductPart("Rendered Sheet Part", "Rendered Mechanical Sheet Mesh"))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("Rendered Aluminium", density=2700.0))
library = manager.mechanical_library_manager.create_library("Rendered Library")
category = manager.mechanical_library_manager.create_category(library, "Gears")
family = manager.mechanical_library_manager.create_family(library, category, "Spur Gears")
component = manager.mechanical_library_manager.create_component(library, category, family, part, "20T Spur Gear")
rule = manager.sheet_metal_rule_manager.create_rule("Rendered Rule", material, 2.5, 1.25, 0.4)
sheet_part = manager.sheet_metal_manager.convert_part(part, rule, "Rendered Sheet Metal")
sheet_body = manager.sheet_metal_manager.create_body(sheet_part, part, "Rendered Mechanical Sheet Mesh", operation="Corner Relief")
flat_pattern = manager.sheet_metal_manager.create_flat_pattern(sheet_part, sheet_body)
workspace.selection.select(component)

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

panel.show_selection([library])
assert panel.type.text() == "MechanicalLibrary"
assert "Components: 1" in panel.radius.text()

panel.show_selection([component])
assert panel.type.text() == "MechanicalComponent"
assert "Product Part:" in panel.radius.text()
assert "Family:" in panel.width.text()

panel.show_selection([sheet_part])
assert panel.type.text() == "SheetMetalPart"
assert "Bodies: 1" in panel.radius.text()
assert "Flat Patterns: 1" in panel.radius.text()

panel.show_selection([sheet_body])
assert panel.type.text() == "SheetMetalBody"
assert "Operation: Corner Relief" in panel.line_type.text()

panel.show_selection([flat_pattern])
assert panel.type.text() == "FlatPattern"
assert "Metadata Only" in panel.radius.text()

panel.show_selection([rule])
assert panel.type.text() == "SheetMetalRule"
assert "Thickness:" in panel.radius.text()
assert "K-Factor:" in panel.line_type.text()

panel.show_selection([part])
assert "Library: 1" in panel.radius.text()
assert "Sheet Metal: 1" in panel.radius.text()

print("3d-product-mechanical-sheet-metal-renderer-property-ok")
