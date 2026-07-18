from engine.bim import (
    AreaBoundary,
    AreaRegion,
    BIMInstance,
    Room,
    RoomBoundary,
    RoomMetadata,
    Space,
    SpaceBoundary,
    SpaceMetadata,
    Zone,
    ZoneGroup,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.bim_manager.create_project("Room Space Zone BIM")
wall = workspace.bim_manager.add_instance(BIMInstance("Boundary Wall"))
room_element = workspace.bim_manager.add_instance(BIMInstance("Room Element"))
space_element = workspace.bim_manager.add_instance(BIMInstance("Space Element"))

room = workspace.bim_manager.add_room_item(
    Room("101", "Conference", "", room_element.id, 120.0, RoomMetadata("Admin", "6", "Paint", 360.0))
)
room_boundary = workspace.bim_manager.add_room_item(RoomBoundary(room.id, [wall.id]))
space = workspace.bim_manager.add_space_item(
    Space("MEP Conference", room.id, space_element.id, 110.0, SpaceMetadata("MEP", 330.0, 3.0))
)
space_boundary = workspace.bim_manager.add_space_item(SpaceBoundary(space.id, [wall.id]))
zone = workspace.bim_manager.add_zone_item(Zone("Admin Zone", [room.id], [space.id]))
zone_group = workspace.bim_manager.add_zone_item(ZoneGroup("Level Zones", [zone.id]))
region = workspace.bim_manager.add_area_item(AreaRegion("Gross Conference", "Gross Area", [room.id], [space.id]))
area_boundary = workspace.bim_manager.add_area_item(AreaBoundary(region.id, [wall.id]))
summary = workspace.bim_manager.area_analysis_manager.recalculate()

room_stats = workspace.bim_manager.room_manager.statistics()
space_stats = workspace.bim_manager.space_manager.statistics()
zone_stats = workspace.bim_manager.zone_manager.statistics()
area_stats = workspace.bim_manager.active_project.area_statistics

assert room.boundary_id == room_boundary.id
assert space.boundary_id == space_boundary.id
assert workspace.bim_manager.rooms_for(room_element) == [room]
assert workspace.bim_manager.spaces_for(space_element) == [space]
assert workspace.bim_manager.zones_for(room) == [zone]
assert workspace.bim_manager.zones_for(space) == [zone]
assert zone_group.zone_ids == [zone.id]
assert region.area == 230.0
assert summary.gross_area == 230.0
assert area_boundary.boundary_ids == [wall.id]
assert room_stats.rooms == 1
assert room_stats.total_volume == 360.0
assert space_stats.total_volume == 330.0
assert zone_stats.room_memberships == 1
assert area_stats.total_area == 230.0

print("3d-bim-room-space-zone-area-manager-ok")
