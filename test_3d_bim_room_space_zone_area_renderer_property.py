import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.bim import AreaRegion, BIMInstance, Room, Space, Zone
from engine.geometry import Vector3
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.bim_manager.create_project("Rendered Batch I BIM")
room_element = BIMInstance("Rendered Room Element", location=Vector3(0.0, 0.0, 0.0))
space_element = BIMInstance("Rendered Space Element", location=Vector3(10.0, 0.0, 0.0))
workspace.bim_manager.add_instance(room_element)
workspace.bim_manager.add_instance(space_element)
room = workspace.bim_manager.add_room_item(Room("401", "Rendered Room", element_id=room_element.id, area=60.0))
space = workspace.bim_manager.add_space_item(Space("Rendered Space", room.id, space_element.id, 55.0))
workspace.bim_manager.add_zone_item(Zone("Rendered Zone", [room.id], [space.id]))
workspace.bim_manager.add_area_item(AreaRegion("Rendered Rentable", "Rentable Area", [room.id], [space.id]))
workspace.selection.select(room_element)

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
panel.show_selection([room_element])

assert panel.type.text() == "BIMInstance"
assert panel.content.text() == "Rendered Room Element"
assert "Rooms: 1" in panel.length.text()
assert "Zones: 1" in panel.angle.text()
assert "Area Regions: 1" in panel.angle.text()

print("3d-bim-room-space-zone-area-renderer-property-ok")
