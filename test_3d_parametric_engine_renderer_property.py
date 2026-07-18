import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ParametricContext, ProductPart
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="Rendered Parametric Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
product_document = manager.create_document("Rendered Parametric Product")
part = manager.add_part(ProductPart("Rendered Parametric Part", "Rendered Parametric Mesh"))
engine = manager.parametric_manager.create_engine("Rendered Parametric Engine")
context = ParametricContext(product_document_id=product_document.id, product_part_id=part.id, mesh_entity_id=mesh.name)
parametric_document = manager.parametric_manager.create_document("Rendered Parametric Document", engine, context, [part])
parametric_workspace = manager.parametric_manager.create_workspace("Rendered Parametric Workspace", engine, parametric_document)
session = manager.parametric_manager.create_session("Rendered Parametric Session", engine, parametric_document, context, [part])
session.dirty_state.dirty = True
workspace.selection.select(session)

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

panel.show_selection([engine])
assert panel.type.text() == "ParametricEngine"
assert "Documents: 1" in panel.radius.text()
assert "No solver" in panel.line_weight.text()

panel.show_selection([parametric_document])
assert panel.type.text() == "ParametricDocument"
assert "Sessions: 1" in panel.radius.text()
assert "Relationship storage only" in panel.line_weight.text()

panel.show_selection([parametric_workspace])
assert panel.type.text() == "ParametricWorkspace"
assert "No duplicate Workspace" in panel.line_type.text()

panel.show_selection([session])
assert panel.type.text() == "ParametricSession"
assert "Dirty: True" in panel.height.text()
assert "Future solving placeholder only" in panel.line_weight.text()

assert session in workspace.visible_product_objects()
assert len(workspace.scene3d.entities()) == 1

print("3d-parametric-engine-renderer-property-ok")
