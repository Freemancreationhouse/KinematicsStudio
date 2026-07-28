from engine.bim import BIMParametricDefinition
from engine.commands import (
    ChangeBIMElementLevelCommand,
    ChangeBIMElementMaterialCommand,
    ConnectBeamToColumnCommand,
    CreateBeamCommand,
    CreateColumnCommand,
    CreateDoorCommand,
    CreateSlabCommand,
    CreateWallCommand,
    CreateWindowCommand,
    HostDoorByWallCommand,
    HostWindowByWallCommand,
    ReplaceBIMElementTypeCommand,
    StartBIMAuthoringSessionCommand,
    UpdateBIMAuthoringContextCommand,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.bim_manager
manager.initialize("Release 1.9 BIM Authoring", project_units="meters")

project_node = manager.create_spatial_element("Project", "Authoring Project")
site = manager.create_spatial_element("Site", "Main Site", project_node.id)
building = manager.create_spatial_element("Building", "Tower A", site.id)
level_01 = manager.create_spatial_element("Building Storey", "Level 01", building.id)
level_02 = manager.create_spatial_element("Building Storey", "Level 02", building.id, elevation=3.2)

wall_type = manager.create_native_element_type(
    "Wall Type 200",
    "Wall",
    "Architecture",
    material_id="mat-concrete",
    parameters=BIMParametricDefinition(thickness=0.2, height=3.2, length=6.0),
)
door_type = manager.create_native_element_type(
    "Door Type 900",
    "Door",
    "Architecture",
    material_id="mat-timber",
    parameters=BIMParametricDefinition(width=0.9, height=2.1),
)
window_type = manager.create_native_element_type(
    "Window Type 1200",
    "Window",
    "Architecture",
    material_id="mat-glass",
    parameters=BIMParametricDefinition(width=1.2, height=1.4),
)
column_type = manager.create_native_element_type(
    "Column Type 300",
    "Column",
    "Structure",
    material_id="mat-concrete",
    parameters=BIMParametricDefinition(width=0.3, height=3.2, length=0.3),
)
beam_type = manager.create_native_element_type(
    "Beam Type 300x500",
    "Beam",
    "Structure",
    material_id="mat-concrete",
    parameters=BIMParametricDefinition(width=0.3, height=0.5, length=6.0),
)
slab_type = manager.create_native_element_type(
    "Slab Type 150",
    "Slab",
    "Architecture",
    material_id="mat-concrete",
    parameters=BIMParametricDefinition(thickness=0.15, length=6.0, width=4.0),
)

workspace.command_manager.execute(
    StartBIMAuthoringSessionCommand(
        workspace,
        "Create Wall",
        {
            "grid_snapping": True,
            "object_snapping": True,
            "level_id": level_01.id,
            "cursor_preview": {"element_type": "Wall", "body_reference": "body-wall-a"},
        },
    )
)
workspace.command_manager.execute(
    UpdateBIMAuthoringContextCommand(
        workspace,
        {
            "snapping_context": {"grid": "A-1", "axis_lock": "X"},
            "visualization_context": {
                "placement_preview": {"kind": "wall"},
                "host_highlighting": {"candidate": ""},
                "temporary_dimensions": {"length": 6.0},
                "creation_guides": {"baseline": "grid-A"},
            },
        },
    )
)

workspace.command_manager.execute(
    CreateWallCommand(
        workspace,
        "Wall A",
        [{"body_id": "body-wall-a", "body_name": "Parametric wall body", "source": "BodyManager"}],
        element_type_id=wall_type.id,
        material_assignment_id="mat-concrete",
        level_id=level_01.id,
        parameters=BIMParametricDefinition(thickness=0.2, height=3.2, length=6.0),
    )
)
wall = manager.active_project.native_elements[-1]

workspace.command_manager.execute(
    CreateDoorCommand(
        workspace,
        "Door A",
        [{"body_id": "body-door-a", "body_name": "Parametric door body", "source": "BodyManager"}],
        element_type_id=door_type.id,
        material_assignment_id="mat-timber",
        level_id=level_01.id,
        host_id=wall.id,
        parameters=BIMParametricDefinition(width=0.9, height=2.1),
    )
)
door = manager.active_project.native_elements[-1]
workspace.command_manager.execute(
    CreateWindowCommand(
        workspace,
        "Window A",
        [{"body_id": "body-window-a", "body_name": "Parametric window body", "source": "BodyManager"}],
        element_type_id=window_type.id,
        material_assignment_id="mat-glass",
        level_id=level_01.id,
        host_id=wall.id,
        parameters=BIMParametricDefinition(width=1.2, height=1.4),
    )
)
window = manager.active_project.native_elements[-1]
workspace.command_manager.execute(
    CreateColumnCommand(
        workspace,
        "Column A",
        [{"body_id": "body-column-a", "body_name": "Parametric column body", "source": "BodyManager"}],
        element_type_id=column_type.id,
        material_assignment_id="mat-concrete",
        level_id=level_01.id,
        parameters=BIMParametricDefinition(width=0.3, height=3.2, length=0.3),
    )
)
column = manager.active_project.native_elements[-1]
workspace.command_manager.execute(
    CreateBeamCommand(
        workspace,
        "Beam A",
        [{"body_id": "body-beam-a", "body_name": "Parametric beam body", "source": "BodyManager"}],
        element_type_id=beam_type.id,
        material_assignment_id="mat-concrete",
        level_id=level_01.id,
        parameters=BIMParametricDefinition(width=0.3, height=0.5, length=6.0),
    )
)
beam = manager.active_project.native_elements[-1]
workspace.command_manager.execute(
    CreateSlabCommand(
        workspace,
        "Slab A",
        [{"body_id": "body-slab-a", "body_name": "Parametric slab body", "source": "BodyManager"}],
        element_type_id=slab_type.id,
        material_assignment_id="mat-concrete",
        level_id=level_01.id,
        parameters=BIMParametricDefinition(thickness=0.15, length=6.0, width=4.0),
    )
)

workspace.command_manager.execute(
    HostDoorByWallCommand(workspace, door.id, wall.id, opening_metadata={"opening_body_id": "opening-door-a"})
)
workspace.command_manager.execute(
    HostWindowByWallCommand(workspace, window.id, wall.id, opening_metadata={"opening_body_id": "opening-window-a"})
)
workspace.command_manager.execute(
    ConnectBeamToColumnCommand(workspace, beam.id, column.id, connection_metadata={"connection_type": "bearing"})
)
workspace.command_manager.execute(ChangeBIMElementLevelCommand(workspace, wall, level_02.id))
workspace.command_manager.execute(ChangeBIMElementMaterialCommand(workspace, wall, "mat-brick"))
workspace.command_manager.execute(ReplaceBIMElementTypeCommand(workspace, wall, wall_type.id))

visualization = manager.bim_authoring_visualization_metadata()
validation = manager.validate_bim_authoring()
diagnostics = manager.authoring_manager.refresh_diagnostics()

assert len(manager.active_project.native_elements) == 6
assert wall.level_id == level_02.id
assert wall.material_assignment_id == "mat-brick"
assert door.host_id == wall.id
assert validation.valid, validation.issues
assert diagnostics.commands >= 9
assert diagnostics.created_elements == 6
assert diagnostics.relationships == 3
assert visualization["temporary_dimensions"]["length"] == 6.0
assert visualization["creation_guides"]["baseline"] == "grid-A"
assert workspace.command_manager.undo_count >= 13
assert workspace.command_manager.redo_count == 0
assert workspace.scene3d.entities() == []

workspace.command_manager.undo()
assert wall.element_type_id == wall_type.id
workspace.command_manager.undo()
assert wall.material_assignment_id == "mat-concrete"
workspace.command_manager.redo()
assert wall.material_assignment_id == "mat-brick"

persisted = manager.to_dict()
restored = manager.__class__()
restored.from_dict(persisted)
restored_validation = restored.validate_bim_authoring()

assert restored_validation.valid, restored_validation.issues
assert len(restored.active_project.authoring_sessions) == 1
assert len(restored.active_project.native_elements) == 6
assert restored.active_project.native_elements[0].body_references[0].source == "BodyManager"

print("bim-authoring-commands-ok")
