import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.bim import BIMCategory, BIMInstance, BIMType, Building, GridSystem, Level, Site
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.bim_manager.create_project("Rendered BIM")
site = workspace.bim_manager.add_site(Site("Render Site"))
building = workspace.bim_manager.add_building(Building("Render Building", site.id))
level = workspace.bim_manager.add_level(Level("Render Level", 0.0, 3.0, building.id))
workspace.bim_manager.add_grid(GridSystem("Render Grid", building.id, 10.0, 3, 3))
category = workspace.bim_manager.add_category(BIMCategory("Columns"))
bim_type = workspace.bim_manager.add_type(BIMType("Concrete Column", category.id))
mesh = MeshEntity(MeshData.box(0.4, 0.4, 3.0), name="Rendered Column Mesh")
mesh.id = "rendered-column-mesh"
workspace.add_3d_entity(mesh)
instance = BIMInstance("Rendered Column", category.id, bim_type.id, mesh)
instance.level_id = level.id
instance.building_id = building.id
workspace.bim_manager.add_instance(instance)
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
assert panel.content.text() == "Rendered Column"
assert "Category: Columns" in panel.alignment.text()
assert "Type: Concrete Column" in panel.dimension_style.text()
assert "Level: Render Level" in panel.line_type.text()
assert "Building: Render Building" in panel.line_weight.text()
assert panel.diameter.text().startswith("GUID:")

print("3d-bim-foundation-renderer-property-ok")
