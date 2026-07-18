import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace("3D Transform Property Workspace")
entity = MeshEntity(MeshData.box(10, 10, 10))
workspace.add_3d_entity(entity)
workspace.selection.select(entity)

panel = PropertyPanel()
panel.set_workspace(workspace)
panel.show_selection([entity])

panel.x.setText("12")
panel._geometry_changed("x")
assert entity.position3d.x == 12.0
assert workspace.command_manager.undo_available

panel.length.setText("45")
panel._geometry_changed("length")
assert entity.rotation3d.x == 45.0

panel.width.setText("2")
panel._geometry_changed("width")
assert entity.scale3d.x == 2.0

workspace.command_manager.undo()
assert entity.scale3d.x == 1.0

print("3d-transform-property-panel-ok")
