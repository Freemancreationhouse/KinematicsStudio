import os
import tempfile

from engine.bim import AreaRegion, BIMInstance, Room, RoomBoundary, Space, Zone
from engine.cad.application import CADApplication


app = CADApplication()
workspace = app.workspace
workspace.bim_manager.create_project("Persisted Batch I BIM")
boundary = workspace.bim_manager.add_instance(BIMInstance("Persisted Boundary"))
room_element = workspace.bim_manager.add_instance(BIMInstance("Persisted Room Element"))
space_element = workspace.bim_manager.add_instance(BIMInstance("Persisted Space Element"))
room = workspace.bim_manager.add_room_item(Room("301", "Persisted Room", element_id=room_element.id, area=95.0))
workspace.bim_manager.add_room_item(RoomBoundary(room.id, [boundary.id]))
space = workspace.bim_manager.add_space_item(Space("Persisted Space", room.id, space_element.id, 85.0))
zone = workspace.bim_manager.add_zone_item(Zone("Persisted Zone", [room.id], [space.id]))
workspace.bim_manager.add_area_item(AreaRegion("Persisted Net", "Net Area", [room.id], [space.id]))
workspace.selection.select(room_element)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "bim_batch_i.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    project = restored_workspace.bim_manager.active_project
    restored_room_element = project.instances[1]
    restored_room = project.rooms[0]
    restored_space = project.spaces[0]

    assert restored_room.number == "301"
    assert project.room_boundaries[0].boundary_ids == [project.instances[0].id]
    assert restored_workspace.bim_manager.rooms_for(restored_room_element) == [restored_room]
    assert restored_workspace.bim_manager.zones_for(restored_space)[0].name == zone.name
    assert project.area_summary.net_area == 180.0
    assert restored_room_element.selected is True

print("3d-bim-room-space-zone-area-persistence-ok")
