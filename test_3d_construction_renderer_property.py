import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.render import Renderer3D
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

app = CADApplication()
entity = MeshEntity(MeshData.box(10, 10, 10))
app.workspace.add_3d_entity(entity)
app.workspace.selection.select(entity)
app.workspace.coordinate_system_manager.create_ucs("Render UCS", origin=Vector3(10.0, 0.0, 0.0))
app.workspace.coordinate_system_manager.activate("Render UCS")
app.workspace.construction_plane_manager.create_offset("XY Plane", "Render Plane", 5.0)
app.workspace.construction_plane_manager.set_active("Render Plane")
app.camera3d.resize(320, 240)

renderer = Renderer3D()
renderer.camera = app.camera3d
image = QImage(320, 240, QImage.Format_ARGB32)
painter = QPainter(image)
renderer.render(painter, app.workspace, 320, 240)
painter.end()

panel = PropertyPanel()
panel.set_workspace(app.workspace)
panel.show_selection([entity])

assert "UCS: Render UCS" in panel.dimension_style.text()
assert "Plane: Render Plane" in panel.line_type.text()

print("3d-construction-renderer-property-ok")
