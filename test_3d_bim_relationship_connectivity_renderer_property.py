import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.bim import BIMInstance, BIMRelationship, Connection, CutRelationship, HostObject, HostedObject, Opening
from engine.geometry import Vector3
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.bim_manager.create_project("Rendered Batch G BIM")
wall = BIMInstance("Rendered Wall", location=Vector3(0.0, 0.0, 0.0))
door = BIMInstance("Rendered Door", location=Vector3(10.0, 0.0, 0.0))
beam = BIMInstance("Rendered Beam", location=Vector3(20.0, 0.0, 0.0))
workspace.bim_manager.add_instance(wall)
workspace.bim_manager.add_instance(door)
workspace.bim_manager.add_instance(beam)
workspace.bim_manager.add_relationship_item(BIMRelationship(wall.id, door.id, "Host"))
workspace.bim_manager.add_relationship_item(HostObject(wall.id, [door.id]))
workspace.bim_manager.add_relationship_item(HostedObject(door.id, wall.id))
opening = workspace.bim_manager.add_relationship_item(Opening("Rendered Opening", wall.id, "", door.id))
workspace.bim_manager.add_relationship_item(CutRelationship(wall.id, opening.id, door.id))
workspace.bim_manager.add_connection_item(Connection(wall.id, beam.id, "Beam"))
workspace.selection.select(wall)

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
panel.show_selection([wall])

assert panel.type.text() == "BIMInstance"
assert panel.content.text() == "Rendered Wall"
assert "Relations: 1" in panel.radius.text()
assert "Hosted: 1" in panel.radius.text()
assert "Openings: 1" in panel.diameter.text()
assert "Connections: 1" in panel.diameter.text()

print("3d-bim-relationship-connectivity-renderer-property-ok")
