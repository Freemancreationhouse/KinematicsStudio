import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import LaserTool, PlasmaTool, ProductPart
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(6.0, 4.0, 1.0), name="Rendered Laser Plasma Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Rendered Laser Plasma Product")
part = manager.add_part(ProductPart("Rendered Laser Plasma Part", "Rendered Laser Plasma Mesh"))
cam_document = manager.cam_manager.create_document("Rendered Laser Plasma CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Rendered Laser Plasma CAM Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(cam_job, [part], "Box", name="Rendered Setup")
library = manager.tool_library_manager.create_library("Rendered Laser Plasma Tools")
category = manager.tool_library_manager.create_category(library, "Rendered Cutting")
laser_tool = manager.tool_library_manager.create_tool(LaserTool, library, category, "Rendered Laser")
plasma_tool = manager.tool_library_manager.create_tool(PlasmaTool, library, category, "Rendered Plasma")
material = manager.laser_plasma_manager.create_material_profile("Rendered Acrylic", "Acrylic", 3.0)
cutting = manager.laser_plasma_manager.create_cutting_profile(material, "Rendered Cut", cut_speed=15.0, travel_speed=90.0, pass_count=2, kerf_width=0.2)
power = manager.laser_plasma_manager.create_power_profile("Rendered Power", 5.0, 60.0, 50.0)
gas = manager.laser_plasma_manager.create_gas_profile("Rendered Gas", "Air", 4.5)
laser_job = manager.laser_plasma_manager.create_laser_job(cam_job, "Rendered Laser Job")
plasma_job = manager.laser_plasma_manager.create_plasma_job(cam_job, "Rendered Plasma Job")
laser_operation = manager.laser_plasma_manager.create_laser_operation(
    laser_job,
    setup,
    "Vector Engrave",
    [part],
    "Rendered Vector Engrave",
    laser_tool,
    material,
    cutting,
    power,
    laser_power=50.0,
    cut_speed=15.0,
    pass_count=2,
)
plasma_operation = manager.laser_plasma_manager.create_plasma_operation(
    plasma_job,
    setup,
    "Plasma Cut",
    [part],
    "Rendered Plasma Cut",
    plasma_tool,
    material,
    cutting,
    gas_profile=gas,
    pierce_height=3.0,
    cut_height=1.0,
    kerf_width=1.0,
)
workspace.selection.select(laser_operation)

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
panel.show_selection([laser_operation])

assert panel.type.text() == "OperationDefinition"
assert "Laser: Vector Engrave" in panel.radius.text()
assert "Power:" in panel.width.text()
assert "Passes: 2" in panel.height.text()
assert "Enabled" in panel.line_weight.text()

panel.show_selection([plasma_operation])
assert "Plasma: Plasma Cut" in panel.radius.text()
assert "Kerf:" in panel.height.text()
assert "Direction:" in panel.angle.text()

panel.show_selection([material])
assert "Material: Acrylic" in panel.radius.text()

panel.show_selection([cutting])
assert "Cut Speed:" in panel.radius.text()

panel.show_selection([power])
assert "Power:" in panel.radius.text()
assert len(workspace.scene3d.entities()) == 1

print("3d-cam-laser-plasma-renderer-property-ok")
