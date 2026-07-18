import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductCurve, ProductPart, RouterBit
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(8.0, 4.0, 1.0), name="Rendered Router Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Rendered Router Product")
part = manager.add_part(ProductPart("Rendered Router Part", "Rendered Router Mesh"))
curve = manager.curve_manager.add_item(ProductCurve("Rendered Router Curve", part.id))
cam_document = manager.cam_manager.create_document("Rendered Router CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Rendered Router CAM Job", [part, curve])
setup = manager.manufacturing_setup_manager.create_setup(cam_job, [part], "Box", name="Rendered Router Setup")
library = manager.tool_library_manager.create_library("Rendered Router Tools")
category = manager.tool_library_manager.create_category(library, "Rendered Bits")
router_bit = manager.tool_library_manager.create_tool(RouterBit, library, category, "Rendered Compression Bit")
feed_speed = manager.tool_library_manager.create_feed_speed_profile(router_bit, name="Rendered Feed")
dust = manager.router_manager.create_dust_collection_profile("Rendered Dust")
profile = manager.router_manager.create_metadata_profile(
    "Rendered Router Profile",
    safe_height=15.0,
    clearance_height=7.5,
    tab_count=2,
    tabs_enabled=True,
    bridge_count=1,
    bridges_enabled=True,
    dust_collection_profile=dust,
)
fixture = manager.router_manager.create_fixture("Rendered Fixture", [part])
clamp = manager.router_manager.create_clamp_avoidance_region("Rendered Clamp", [curve])
router_job = manager.router_manager.create_router_job(cam_job, "Rendered Router Job")
operation = manager.router_manager.create_operation(
    router_job,
    setup,
    "Pocket Router",
    [part, curve],
    "Rendered Pocket Router",
    router_bit,
    feed_speed_profile=feed_speed,
    router_profile=profile,
    fixtures=[fixture],
    clamp_avoidance_regions=[clamp],
    cut_depth=4.0,
    step_down=1.0,
    step_over=0.8,
    pass_count=2,
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
assert "Router: Pocket Router" in panel.radius.text()
assert "Depth:" in panel.width.text()
assert "Passes: 2" in panel.height.text()
assert "Tabs: 2" in panel.line_type.text()
assert "Fixtures: 1" in panel.angle.text()

panel.show_selection([router_job])
assert "Router Job: 1 operations" in panel.radius.text()

panel.show_selection([fixture])
assert "Fixture:" in panel.radius.text()

panel.show_selection([clamp])
assert "Clamp Region:" in panel.radius.text()

panel.show_selection([profile])
assert "Safe:" in panel.radius.text()
assert "Tabs: 2" in panel.width.text()

panel.show_selection([dust])
assert "Dust Collection" in panel.width.text()
assert len(workspace.scene3d.entities()) == 1

print("3d-cam-router-renderer-property-ok")
