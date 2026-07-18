from engine.bim import (
    BIMElementDefinition,
    BIMInstance,
    BIMRelationship,
    Connection,
    ConnectionType,
    CutRelationship,
    HostObject,
    HostedObject,
    Opening,
    RelationshipType,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.bim_manager.create_project("Relationship Connectivity BIM")
wall_definition = workspace.bim_manager.add_element_definition(BIMElementDefinition("Wall", "Wall"))
door_definition = workspace.bim_manager.add_element_definition(BIMElementDefinition("Door", "Door"))
beam_definition = workspace.bim_manager.add_element_definition(BIMElementDefinition("Beam", "Beam"))

wall = BIMInstance("Wall A")
wall.element_definition_id = wall_definition.id
door = BIMInstance("Door A")
door.element_definition_id = door_definition.id
beam = BIMInstance("Beam A")
beam.element_definition_id = beam_definition.id
workspace.bim_manager.add_instance(wall)
workspace.bim_manager.add_instance(door)
workspace.bim_manager.add_instance(beam)

workspace.bim_manager.relationship_manager.ensure_default_types()
host_type = workspace.bim_manager.add_relationship_item(RelationshipType("Host", "Hosted", "Host"))
relationship = workspace.bim_manager.add_relationship_item(BIMRelationship(wall.id, door.id, "Host"))
host = workspace.bim_manager.add_relationship_item(HostObject(wall.id, [door.id]))
hosted = workspace.bim_manager.add_relationship_item(HostedObject(door.id, wall.id))
opening = workspace.bim_manager.add_relationship_item(Opening("Door Opening", wall.id, "", door.id))
cut = workspace.bim_manager.add_relationship_item(CutRelationship(wall.id, opening.id, door.id))
connection_type = workspace.bim_manager.add_connection_item(ConnectionType("Beam", "Structural"))
connection = workspace.bim_manager.add_connection_item(Connection(wall.id, beam.id, "Beam"))

relationship_stats = workspace.bim_manager.relationship_manager.statistics()
connection_stats = workspace.bim_manager.connectivity_manager.statistics()

assert host_type.name == "Host"
assert relationship in workspace.bim_manager.relationships_for(wall)
assert workspace.bim_manager.relationship_manager.validate_relationship(relationship) is True
assert workspace.bim_manager.hosted_objects_for(wall) == [door]
assert workspace.bim_manager.host_for(door) is wall
assert workspace.bim_manager.openings_for(wall) == [opening]
assert workspace.bim_manager.cut_relationships_for(wall) == [cut]
assert connection_type.name == "Beam"
assert workspace.bim_manager.connections_for(wall) == [connection]
assert workspace.bim_manager.connected_items(wall) == [beam]
assert relationship_stats.relationships == 1
assert relationship_stats.hosts == 1
assert relationship_stats.openings == 1
assert connection_stats.connections == 1
assert connection_stats.connected_elements == 2

print("3d-bim-relationship-connectivity-manager-ok")
