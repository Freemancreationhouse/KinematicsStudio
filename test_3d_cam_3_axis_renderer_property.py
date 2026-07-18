import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import EndMill, EngineeringMaterial, ProductCurve, ProductPart, SurfaceBody
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(5.0, 4.0, 2.0), name="Rendered 3 Axis Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Rendered 3 Axis Product")
part = manager.add_part(ProductPart("Rendered 3 Axis Part", "Rendered 3 Axis Mesh"))
surface_body = manager.surface_manager.add_item(SurfaceBody("Rendered 3 Axis Surface", part.id, mesh.name))
curve = manager.curve_manager.add_item(ProductCurve("Rendered 3 Axis Boundary Curve", part.id))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("Rendered 3 Axis Aluminium", "Aluminium"))
cam_document = manager.cam_manager.create_document("Rendered 3 Axis CAM")
job = manager.cam_manager.create_job(cam_document, "Rendered 3 Axis Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(job, [part], "Box", material, "Rendered 3 Axis Setup")
library = manager.tool_library_manager.create_library("Rendered 3 Axis Tools")
category = manager.tool_library_manager.create_category(library, "Rendered 3 Axis Mills")
tool = manager.tool_library_manager.create_tool(EndMill, library, category, "Rendered 3 Axis Tool", diameter=6.0)
profile = manager.tool_library_manager.create_feed_speed_profile(tool, material, "Rendered 3 Axis Feeds")
selection = manager.three_axis_operation_manager.create_surface_selection(part, [surface_body], mesh_entities=[mesh], face_ids=["f1", "f2"])
region = manager.three_axis_operation_manager.create_machining_region(part, [surface_body], face_ids=["f1"])
boundary = manager.three_axis_operation_manager.create_boundary(part, "Containment", [curve], name="Rendered 3 Axis Boundary")
operation = manager.three_axis_operation_manager.create_operation(
    job,
    setup,
    "Scallop",
    [part],
    "Rendered Scallop",
    tool,
    profile,
    selection,
    region,
    [boundary],
    tolerance=0.01,
    stepover=0.3,
    stepdown=0.7,
    maximum_cusp_height=0.02,
    boundary_mode="Inside",
    cut_direction="Zig Zag",
    group="3 Axis",
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
assert "3 Axis: Scallop" in panel.radius.text()
assert "Tolerance:" in panel.width.text()
assert "Step Down:" in panel.height.text()
assert "Boundary: Inside" in panel.line_type.text()
assert "Boundaries: 1" in panel.line_weight.text()
assert "Surface:" in panel.angle.text()

panel.show_selection([selection])
assert "Faces: 2" in panel.radius.text()
assert "Surface Selection" in panel.line_type.text()

panel.show_selection([boundary])
assert "Boundary: Containment" in panel.radius.text()
assert "Curves: 1" in panel.width.text()
assert len(workspace.scene3d.entities()) == 1

print("3d-cam-3-axis-renderer-property-ok")
