from pathlib import Path
from tempfile import TemporaryDirectory

from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_machine_workspace_foundation_configuration_and_persistence():
    workspace = Workspace("Manufacturing Project")
    machine_workspace = workspace.machine_workspace.initialize()

    machine_workspace.switch_to("Machine Workspace")
    assert machine_workspace.state.active is True
    assert machine_workspace.state.workspace_name == "Machine Workspace"

    fdm = machine_workspace.register_machine(
        "KS FDM 300",
        "FDM Printer",
        manufacturer="Kinematics Studio",
        model="FDM 300",
        firmware="Marlin",
        work_envelope={"x": 300, "y": 300, "z": 300},
        supported_materials=["PLA", "PETG"],
        supported_tool_systems=["Extruder"],
        supported_file_formats=["3MF", "STL"],
    )
    mill = machine_workspace.register_machine(
        "KS Mill 500",
        "CNC Mill",
        manufacturer="Kinematics Studio",
        model="Mill 500",
        firmware="GRBL",
        work_envelope={"x": 500, "y": 400, "z": 250},
        supported_materials=["Aluminum"],
        supported_tool_systems=["End Mill", "Drill"],
        supported_file_formats=["STEP", "BREP"],
    )
    tools = machine_workspace.create_tool_library("Production Tools")
    end_mill = machine_workspace.register_tool(
        tools,
        "6mm Carbide End Mill",
        "End Mill",
        diameter=6.0,
        length=50.0,
        material="Carbide",
        operating_limits={"max_rpm": 24000, "max_feed": 2500},
        manufacturer="Kinematics Studio",
        status="Available",
    )
    nozzle = machine_workspace.register_tool(
        tools,
        "0.4mm Brass Nozzle",
        "Extruder",
        diameter=0.4,
        length=12.0,
        material="Brass",
        operating_limits={"max_temperature": 300},
        status="Available",
    )
    pla = machine_workspace.register_material(
        "PLA",
        "Plastic",
        density=1240,
        color="#4dd0e1",
        manufacturing_notes="FDM-ready thermoplastic.",
        compatible_machines=[fdm],
        default_process_metadata={"bed_temperature": 60, "nozzle_temperature": 205},
    )
    aluminum = machine_workspace.register_material(
        "Aluminum 6061",
        "Aluminium",
        density=2700,
        color="#b0bec5",
        manufacturing_notes="CNC machining stock.",
        compatible_machines=[mill],
        default_process_metadata={"coolant": "Mist"},
    )

    profile = machine_workspace.create_profile(
        fdm,
        "FDM PLA Production",
        tool_library=tools,
        version="1.0",
    )
    cloned = machine_workspace.clone_profile(profile, "FDM PLA Draft")
    machine_workspace.edit_profile(cloned, version="1.1", enabled=False)
    machine_workspace.activate_profile(profile)
    machine_workspace.set_preferences(
        preferred_units="mm",
        preferred_material_id=pla,
        preferred_workflow="FDM",
        preferred_safety_profile="Standard",
    )

    validation = machine_workspace.validate()
    diagnostics = machine_workspace.diagnostics()

    assert validation.valid is True
    assert diagnostics.registered_machines == 2
    assert diagnostics.profiles == 2
    assert diagnostics.tools == 2
    assert diagnostics.materials == 2
    assert machine_workspace.state.active_profile_id == profile.id
    assert machine_workspace.preferences.preferred_material_id == pla.id
    assert end_mill.metadata.properties["status"] == "Available"
    assert nozzle.metadata.properties["operating_limits"]["max_temperature"] == 300
    assert aluminum.metadata.properties["default_process_metadata"]["coolant"] == "Mist"

    duplicate_checks = [
        lambda: machine_workspace.register_machine("KS FDM 300", "FDM Printer"),
        lambda: machine_workspace.create_tool_library("Production Tools"),
        lambda: machine_workspace.register_tool(tools, "6mm Carbide End Mill", "End Mill"),
        lambda: machine_workspace.register_material("PLA", "Plastic"),
        lambda: machine_workspace.create_profile(fdm, "FDM PLA Production"),
    ]
    for operation in duplicate_checks:
        try:
            operation()
        except ValueError:
            pass
        else:
            raise AssertionError("Duplicate manufacturing metadata was not rejected.")

    assert list(workspace.scene3d.entities()) == []
    assert getattr(workspace.product_manager, "bodies", []) == []
    assert getattr(workspace.product_manager, "features", []) == []
    assert workspace.command_manager.undo_stack == []
    assert workspace.command_manager.redo_stack == []

    with TemporaryDirectory() as directory:
        path = Path(directory) / "machine_workspace.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored_machine_workspace = restored.machine_workspace
    restored_machine_workspace.load_from_settings()
    restored_validation = restored_machine_workspace.validate()
    restored_diagnostics = restored_machine_workspace.diagnostics()

    assert restored_validation.valid is True
    assert restored_machine_workspace.state.active is True
    assert restored_machine_workspace.state.active_profile_id == profile.id
    assert restored_machine_workspace.preferences.preferred_material_id == pla.id
    assert restored_diagnostics.registered_machines == 2
    assert restored_diagnostics.profiles == 2
    assert restored_diagnostics.tools == 2
    assert restored_diagnostics.materials == 2
    assert list(restored.scene3d.entities()) == []


if __name__ == "__main__":
    test_machine_workspace_foundation_configuration_and_persistence()
    print("machine-workspace-foundation-ok")
