from engine.bim import BIMManager, BIMParametricDefinition
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.bim_manager
manager.initialize(
    "Release 1.9 BIM Element Library",
    project_units="meters",
    project_location={"latitude": 12.9716, "longitude": 77.5946},
    coordinate_system={"name": "Project Coordinates"},
)

project_node = manager.create_spatial_element("Project", "Element Project")
site = manager.create_spatial_element("Site", "Main Site", project_node.id)
building = manager.create_spatial_element("Building", "Tower A", site.id)
level = manager.create_spatial_element("Building Storey", "Level 01", building.id, elevation=0.0)

wall_type = manager.create_native_element_type(
    "Basic Wall 200mm",
    "Wall",
    "Architecture",
    material_id="mat-concrete",
    classification={"Uniclass": "Ss_25_10_30_25"},
    parameters=BIMParametricDefinition(thickness=0.2, height=3.2, length=6.0, material="Concrete"),
    catalog_metadata={"catalog": "Wall Types"},
)
door_type = manager.create_native_element_type(
    "Single Flush Door",
    "Door",
    "Architecture",
    material_id="mat-timber",
    parameters=BIMParametricDefinition(width=0.9, height=2.1, thickness=0.045, material="Timber"),
)
window_type = manager.create_native_element_type(
    "Fixed Window",
    "Window",
    "Architecture",
    material_id="mat-glass",
    parameters=BIMParametricDefinition(width=1.2, height=1.4, material="Glass"),
)
column_type = manager.create_native_element_type(
    "RC Column 300x300",
    "Column",
    "Structure",
    material_id="mat-concrete",
    parameters=BIMParametricDefinition(width=0.3, height=3.2, length=0.3, material="Concrete"),
)
beam_type = manager.create_native_element_type(
    "RC Beam 300x500",
    "Beam",
    "Structure",
    material_id="mat-concrete",
    parameters=BIMParametricDefinition(width=0.3, height=0.5, length=6.0, material="Concrete"),
)
duct_type = manager.create_native_element_type(
    "Rectangular Supply Duct",
    "Duct",
    "MEP",
    material_id="mat-galvanized-steel",
    parameters=BIMParametricDefinition(width=0.45, height=0.25, length=5.0, material="Galvanized Steel"),
)

library = manager.create_native_library(
    "Architectural + Structure + MEP Catalog",
    "Type Catalog",
    [wall_type.id, door_type.id, window_type.id, column_type.id, beam_type.id, duct_type.id],
    ["mat-concrete", "mat-timber", "mat-glass", "mat-galvanized-steel"],
    {"discipline": "Multi-discipline"},
)

wall = manager.create_architectural_element(
    "Wall",
    "Wall A",
    [{"body_id": "body-wall-a", "body_name": "Parametric wall body", "source": "BodyManager"}],
    element_type_id=wall_type.id,
    material_assignment_id="mat-concrete",
    level_id=level.id,
    parameters=BIMParametricDefinition(thickness=0.2, height=3.2, length=6.0, material="Concrete"),
)
door = manager.create_architectural_element(
    "Door",
    "Door A",
    [{"body_id": "body-door-a", "body_name": "Parametric door body", "source": "BodyManager"}],
    element_type_id=door_type.id,
    material_assignment_id="mat-timber",
    level_id=level.id,
    host_id=wall.id,
    parameters=BIMParametricDefinition(width=0.9, height=2.1, thickness=0.045, material="Timber"),
)
window = manager.create_architectural_element(
    "Window",
    "Window A",
    [{"body_id": "body-window-a", "body_name": "Parametric window body", "source": "BodyManager"}],
    element_type_id=window_type.id,
    material_assignment_id="mat-glass",
    level_id=level.id,
    host_id=wall.id,
    parameters=BIMParametricDefinition(width=1.2, height=1.4, material="Glass"),
)
column = manager.create_structural_element(
    "Column",
    "Column A",
    [{"body_id": "body-column-a", "body_name": "Parametric column body", "source": "BodyManager"}],
    element_type_id=column_type.id,
    material_assignment_id="mat-concrete",
    level_id=level.id,
    parameters=BIMParametricDefinition(width=0.3, height=3.2, length=0.3, material="Concrete"),
)
beam = manager.create_structural_element(
    "Beam",
    "Beam A",
    [{"body_id": "body-beam-a", "body_name": "Parametric beam body", "source": "BodyManager"}],
    element_type_id=beam_type.id,
    material_assignment_id="mat-concrete",
    level_id=level.id,
    parameters=BIMParametricDefinition(width=0.3, height=0.5, length=6.0, material="Concrete"),
)
duct = manager.create_mep_element(
    "Duct",
    "Supply Duct A",
    [{"body_id": "body-duct-a", "body_name": "Parametric duct body", "source": "BodyManager"}],
    element_type_id=duct_type.id,
    material_assignment_id="mat-galvanized-steel",
    level_id=level.id,
    parameters=BIMParametricDefinition(width=0.45, height=0.25, length=5.0, material="Galvanized Steel"),
    metadata={"connection_metadata": {"system": "Supply Air"}, "routing_metadata": {"route_locked": False}},
)

door_wall = manager.create_native_element_relationship(
    "DoorToWall",
    door.id,
    wall.id,
    opening_metadata={"opening_body_id": "opening-door-a"},
)
window_wall = manager.create_native_element_relationship(
    "WindowToWall",
    window.id,
    wall.id,
    opening_metadata={"opening_body_id": "opening-window-a"},
)
beam_column = manager.create_native_element_relationship(
    "BeamToColumn",
    beam.id,
    column.id,
    connection_metadata={"connection_type": "bearing"},
)

visualization = manager.native_bim_visualization_metadata()
validation = manager.validate_native_bim_elements()
diagnostics = manager.native_element_diagnostics_report()

assert wall.body_references[0].source == "BodyManager"
assert door.host_id == wall.id
assert window.host_id == wall.id
assert door_wall.id in door.host_relationship_ids
assert window_wall.id in wall.host_relationship_ids
assert beam_column.id in beam.host_relationship_ids
assert library.element_type_ids == [wall_type.id, door_type.id, window_type.id, column_type.id, beam_type.id, duct_type.id]
assert visualization["category_colors"][wall.id] == "#90caf9"
assert wall.id in visualization["element_filters"]["Architecture"]
assert column.id in visualization["element_filters"]["Structure"]
assert duct.id in visualization["element_filters"]["MEP"]
assert validation.valid, validation.issues
assert diagnostics.element_types == 6
assert diagnostics.elements == 6
assert diagnostics.architectural_elements == 3
assert diagnostics.structural_elements == 2
assert diagnostics.mep_elements == 1
assert diagnostics.relationships == 3
assert diagnostics.libraries == 1

persisted = manager.to_dict()
restored = BIMManager()
restored.from_dict(persisted)
restored_project = restored.active_project
restored_validation = restored.validate_native_bim_elements()

assert len(restored_project.native_elements) == 6
assert restored_project.native_elements[0].body_references[0].body_id == "body-wall-a"
assert restored_project.native_elements[-1].metadata["connection_metadata"]["system"] == "Supply Air"
assert restored_project.native_libraries[0].name == "Architectural + Structure + MEP Catalog"
assert restored_validation.valid, restored_validation.issues

assert workspace.scene3d.entities() == []
assert workspace.command_manager.undo_stack == []
assert workspace.command_manager.redo_stack == []

print("bim-element-library-native-components-ok")
