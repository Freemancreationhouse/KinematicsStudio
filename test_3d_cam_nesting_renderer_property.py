import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(7.0, 5.0, 2.0), name="Rendered Nesting Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Rendered Nesting Product")
part = manager.add_part(ProductPart("Rendered Nesting Part", "Rendered Nesting Mesh"))
cam_document = manager.cam_manager.create_document("Rendered Nesting CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Rendered Nesting CAM Job", [part])
stock_library = manager.nesting_manager.create_stock_library("Rendered Stock Library")
stock_profile = manager.nesting_manager.create_stock_profile(stock_library, "Rendered Sheet", "Sheet Stock", 100.0, 80.0, 3.0, quantity=5, grain_direction="Long")
nesting_profile = manager.nesting_manager.create_profile("Rendered Nest Profile", [stock_profile], estimated_waste_percentage=11.0)
nesting_job = manager.nesting_manager.create_job(cam_job, nesting_profile, "Rendered Nest Job")
placement = manager.nesting_manager.create_part_placement(part, stock_profile)
cut_list = manager.nesting_manager.create_cut_list("Rendered Cut List", [part], [placement])
panel_layout = manager.nesting_manager.create_panel_layout(stock_profile, [placement], "Rendered Panel")
plan = manager.nesting_manager.create_fabrication_plan(cam_job, "Rendered Fabrication Plan", [cut_list], [panel_layout])
workspace.selection.select(nesting_job)

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

panel.show_selection([stock_profile])
assert "Sheet Stock" in panel.radius.text()
assert "Thickness:" in panel.height.text()
assert "Grain: Long" in panel.line_weight.text()

panel.show_selection([nesting_profile])
assert "Stock Profiles: 1" in panel.radius.text()
assert "Nesting Profile" in panel.line_type.text()

panel.show_selection([nesting_job])
assert "Nesting Job:" in panel.radius.text()
assert "no nesting execution" in panel.line_weight.text()

panel.show_selection([plan])
assert "Cut Lists: 1" in panel.radius.text()
assert "Fabrication Plan" in panel.line_type.text()

panel.show_selection([cut_list])
assert "Cut List" in panel.line_type.text()
assert "No cutting path generation" in panel.line_weight.text()

panel.show_selection([panel_layout])
assert "Panel Layout" in panel.line_type.text()
assert "No nesting preview" in panel.line_weight.text()
assert len(workspace.scene3d.entities()) == 1

print("3d-cam-nesting-renderer-property-ok")
