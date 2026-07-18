import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

mesh = MeshData.box(100, 80, 60)
assert len(mesh.vertices) == 8
assert len(mesh.edges) == 12
assert len(mesh.faces) == 6
assert len(mesh.triangle_indices) == 12
assert mesh.bounding_box3d.valid
assert mesh.bounding_sphere.radius > 0
assert all(vertex.normal.length() > 0 for vertex in mesh.vertices)

entity = MeshEntity(mesh, display_mode="shaded")
assert entity.type_name == "MeshEntity"
assert len(entity.triangles()) == 12
assert len(entity.segments()) == 12
assert entity.bounding_box3d.valid
assert entity.bounding_sphere.radius > 0

workspace = Workspace("Mesh Workspace")
workspace.add_3d_entity(entity)
assert entity.layer_name == "0"
workspace.selection.select(entity)
assert entity.selected

panel = PropertyPanel()
panel.set_workspace(workspace)
panel.show_selection([entity])
assert panel.type.text() == "MeshEntity"
assert "Display: shaded" in panel.content.text()
assert "Vertices:" in panel.alignment.text()

print("3d-mesh-foundation-ok")
