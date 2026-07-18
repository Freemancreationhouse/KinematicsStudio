import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.render import Renderer3D
from engine.scene_organization import ViewFilter
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

app = CADApplication()
mesh = MeshEntity(MeshData.box(20.0, 20.0, 20.0), name="Panel Mesh")
app.workspace.add_3d_entity(mesh)
collection = app.workspace.scene_collection_manager.create("Panel Collection")
app.workspace.scene_collection_manager.move_entity(mesh, collection)
app.workspace.view_filter_manager.add(ViewFilter("Panel Filter", entity_types=["MeshEntity"]))
app.workspace.display_preset_manager.save("Panel Preset", app.workspace)
app.workspace.selection.select(mesh)
app.camera3d.resize(320, 240)

renderer = Renderer3D()
renderer.camera = app.camera3d
image = QImage(320, 240, QImage.Format_ARGB32)
painter = QPainter(image)
renderer.render(painter, app.workspace, 320, 240)
painter.end()

panel = PropertyPanel()
panel.set_workspace(app.workspace)
panel.show_selection([mesh])

assert "Collection: Panel Collection" in panel.content.text()
assert "Filter: Panel Filter" in panel.alignment.text()
assert "Preset: Panel Preset" in panel.dimension_style.text()

print("3d-scene-organization-renderer-property-ok")
