import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import EndMill, EngineeringMaterial, ProductPart
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(5.0, 3.0, 1.0), name="Rendered 25 Axis Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Rendered 25 Axis Product")
part = manager.add_part(ProductPart("Rendered 25 Axis Part", "Rendered 25 Axis Mesh"))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("Rendered Aluminium", "Aluminium"))
cam_document = manager.cam_manager.create_document("Rendered 25 Axis CAM")
job = manager.cam_manager.create_job(cam_document, "Rendered 25 Axis Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(job, [part], "Box", material, "Rendered 25 Axis Setup")
library = manager.tool_library_manager.create_library("Rendered 25 Axis Tools")
category = manager.tool_library_manager.create_category(library, "Rendered Mills")
tool = manager.tool_library_manager.create_tool(EndMill, library, category, "Rendered End Mill", diameter=10.0)
profile = manager.tool_library_manager.create_feed_speed_profile(tool, material, "Rendered Feeds")
operation = manager.operation_manager.create_milling_operation(
    job,
    setup,
    "Pocket",
    [part],
    "Rendered Pocket",
    tool,
    profile,
    depth=4.0,
    step_down=1.0,
    step_over=0.5,
    group="Milling",
)
workspace.selection.select(operation)

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
panel.show_selection([operation])

assert panel.type.text() == "OperationDefinition"
assert "Operation: Pocket" in panel.radius.text()
assert "Depth:" in panel.width.text()
assert "Step Down:" in panel.height.text()
assert "Group: Milling" in panel.line_type.text()
assert "Enabled" in panel.line_weight.text()
assert "Feed/Speed:" in panel.angle.text()
assert len(workspace.scene3d.entities()) == 1

print("3d-cam-25-axis-renderer-property-ok")
