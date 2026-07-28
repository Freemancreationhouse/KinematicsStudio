from engine.bim import BIMManager
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.bim_manager

workspace_state = manager.initialize(
    "Release 1.9 BIM Core",
    project_units="meters",
    project_location={"latitude": 12.9716, "longitude": 77.5946, "elevation": 920.0},
    coordinate_system={"name": "Project North", "true_north_degrees": 0.0},
    building_metadata={"building_name": "Studio Test Building", "discipline": "Architecture"},
    site_metadata={"site_name": "Main Site", "address": "Validation Campus"},
    preferences={"classification": "Uniclass", "ifc_schema": "IFC4"},
)

project = manager.active_project
assert workspace_state.active
assert workspace_state.project_id == project.id
assert project.settings.units == "meters"

spatial_project = manager.create_spatial_element(
    "Project",
    "Studio Project",
    metadata={"classification": "IfcProject"},
)
site = manager.create_spatial_element(
    "Site",
    "Main Site",
    spatial_project.id,
    metadata={"classification": "IfcSite"},
)
building = manager.create_spatial_element(
    "Building",
    "Tower A",
    site.id,
    metadata={"classification": "IfcBuilding"},
)
storey = manager.create_spatial_element(
    "Building Storey",
    "Level 01",
    building.id,
    elevation=0.0,
    metadata={"color": "#90caf9", "classification": "IfcBuildingStorey"},
)
space = manager.create_spatial_element(
    "Space",
    "Lobby",
    storey.id,
    metadata={"classification": "IfcSpace", "gross_area": 38.0},
)
zone = manager.create_spatial_element(
    "Zone",
    "Public Zone",
    storey.id,
    metadata={"zone_type": "Occupancy"},
)

classification = manager.create_classification_assignment(
    "Uniclass",
    "Ss_25_10_30_25",
    "External walls",
    ["Systems", "Walls"],
)

wall = manager.create_building_object(
    "External Wall A",
    "Wall",
    [
        {
            "body_id": "body-wall-a",
            "body_name": "Exact wall body from BodyManager",
            "source": "BodyManager",
            "revision": "A",
        }
    ],
    spatial_container_id=storey.id,
    classification_id=classification.id,
    tag="W-001",
    description="External wall metadata referencing existing exact CAD geometry.",
    properties={
        "FireRating": {"type": "Enumeration", "value": "2h"},
        "IsExternal": {"type": "Boolean", "value": True},
        "LayerNames": {"type": "List", "value": ["finish", "core", "finish"]},
        "GrossArea": {"type": "Quantity", "value": 42.5, "unit": "m2"},
        "ReferenceType": {"type": "Reference", "value": "Basic Wall Type A"},
    },
)
classification.target_id = wall.id

relationships = []
relationships.extend(manager.create_bim_relationship("Contains", storey.id, [wall.id]))
relationships.extend(manager.create_bim_relationship("ServesZone", zone.id, [space.id]))

ifc_wall = manager.create_ifc_entity(
    "IfcWall",
    object_id=wall.id,
    property_set_ids=list(wall.property_set_ids),
    relationship_ids=[relationship.id for relationship in relationships],
    type_metadata={"predefined_type": "STANDARD"},
    serialization_metadata={"schema": "IFC4", "export_ready": False},
)

visualization = manager.bim_visualization_metadata()
validation = manager.validate_bim_core()
diagnostics = manager.bim_core_diagnostics()

assert wall.body_references[0].source == "BodyManager"
assert not getattr(wall, "entity", None)
assert ifc_wall.global_id == wall.global_id
assert visualization["hierarchy"][storey.id]["objects"] == [wall.id]
assert visualization["storey_colors"][storey.id] == "#90caf9"
assert validation.valid, validation.issues
assert diagnostics.projects == 1
assert diagnostics.spatial_elements == 6
assert diagnostics.building_objects == 1
assert diagnostics.property_sets >= 1
assert diagnostics.classifications == 1
assert diagnostics.relationships == 2
assert diagnostics.ifc_entities == 1

persisted = manager.to_dict()
restored = BIMManager()
restored.from_dict(persisted)
restored_project = restored.active_project
restored_validation = restored.validate_bim_core()

assert restored_project.bim_workspace.project_id == project.id
assert restored_project.building_objects[0].body_references[0].body_id == "body-wall-a"
assert restored_project.core_ifc_entities[0].entity_type == "IfcWall"
assert restored_validation.valid, restored_validation.issues

assert workspace.bim_manager is manager
assert workspace.scene3d.entities() == []
assert workspace.command_manager.undo_stack == []
assert workspace.command_manager.redo_stack == []

print("bim-core-ifc-foundation-ok")
