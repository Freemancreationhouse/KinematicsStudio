import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart, ViewportMetadata
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])
workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Rendered Live Preview Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Rendered Live Preview Part", "Rendered Live Preview Mesh"))
engine = manager.parametric_manager.create_engine("Rendered Preview Engine")
session = manager.parametric_manager.create_preview_session("Rendered Preview Session", engine)
request = manager.parametric_manager.create_preview_request(session, "Rendered Preview Request", "Viewport Refresh")
template = manager.parametric_manager.create_preview_template(session, "Rendered Preview Template")
workspace_sync = manager.parametric_manager.create_workspace_synchronization("Rendered Workspace Sync", engine)
viewport_sync = manager.parametric_manager.create_viewport_synchronization("Rendered Viewport Sync", engine, ViewportMetadata(refresh_requested=True, viewport_dirty=True))
property_sync = manager.parametric_manager.create_property_synchronization("Rendered Property Sync", engine)
update = manager.parametric_manager.create_update_coordination("Rendered Update Coordination", engine)

renderer = Renderer3D()
for item in (session, request, template, workspace_sync, viewport_sync, property_sync, update):
    assert renderer._product_color(item, manager).isValid()

panel = PropertyPanel()
panel.set_workspace(workspace)
for item in (session, request, template, workspace_sync, viewport_sync, property_sync, update):
    panel.show_selection([item])
    assert panel.radius.text()
    assert panel.line_weight.text()

assert session in workspace.visible_product_objects()
assert request in workspace.visible_product_objects()
assert update in workspace.visible_product_objects()
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "Rendered Live Preview Mesh"

print("3d-parametric-live-preview-workspace-renderer-property-ok")
