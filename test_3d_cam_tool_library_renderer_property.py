import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import CuttingData, EndMill, EngineeringMaterial, ProductPart, ToolMetadata
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(4.0, 4.0, 1.0), name="Rendered Tool Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Rendered Tool Product")
part = manager.add_part(ProductPart("Rendered Tool Part", "Rendered Tool Mesh"))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("Rendered Aluminium", "Aluminium"))
library = manager.tool_library_manager.create_library("Rendered Tool Library")
category = manager.tool_library_manager.create_category(library, "Rendered Mills")
tool = manager.tool_library_manager.create_tool(
    EndMill,
    library,
    category,
    "Rendered End Mill",
    diameter=10.0,
    flute_length=25.0,
    overall_length=75.0,
    flutes=4,
    metadata=ToolMetadata(material="Carbide", coating="TiN"),
)
holder = manager.holder_manager.create_holder(library, "Rendered Collet", "Collet", 70.0, 50.0)
profile = manager.tool_library_manager.create_feed_speed_profile(
    tool,
    material,
    "Rendered Feeds",
    CuttingData(spindle_speed=11000.0, feed_rate=700.0, plunge_rate=180.0),
)
preset = manager.tool_library_manager.create_preset(tool, holder, profile, "Rendered Preset", 4, 14, 24)
workspace.selection.select(preset)

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
assert panel.type.text() == "ToolLibrary"
assert "Tools: 1" in panel.radius.text()
assert "Holders: 1" in panel.radius.text()

panel.show_selection([category])
assert panel.type.text() == "ToolCategory"
assert "Tools: 1" in panel.radius.text()

panel.show_selection([tool])
assert panel.type.text() == "ToolDefinition"
assert "Diameter:" in panel.radius.text()
assert "Tool: EndMill" in panel.line_type.text()

panel.show_selection([holder])
assert panel.type.text() == "ToolHolder"
assert "Holder:" in panel.radius.text()

panel.show_selection([profile])
assert panel.type.text() == "FeedSpeedProfile"
assert "Feed:" in panel.width.text()

panel.show_selection([preset])
assert panel.type.text() == "ToolPreset"
assert "Tool Number: 4" in panel.radius.text()

panel.show_selection([part])
assert "Tool Profiles: 0" in panel.radius.text()

assert len(workspace.scene3d.entities()) == 1

print("3d-cam-tool-library-renderer-property-ok")
