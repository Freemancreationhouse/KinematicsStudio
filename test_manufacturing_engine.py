from pathlib import Path
from tempfile import TemporaryDirectory

from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_manufacturing_engine_metadata_planning_and_persistence():
    workspace = Workspace("Manufacturing Engine Project")
    machine_workspace = workspace.machine_workspace.initialize()
    manufacturing_engine = workspace.manufacturing_engine.initialize()

    machine = machine_workspace.register_machine(
        "KS Mill 750",
        "CNC Mill",
        manufacturer="Kinematics Studio",
        model="Mill 750",
        firmware="GRBL",
        work_envelope={"x": 750, "y": 500, "z": 300},
        supported_materials=["Aluminum 6061"],
        supported_tool_systems=["End Mill", "Drill"],
        supported_file_formats=["STEP", "BREP"],
    )
    tools = machine_workspace.create_tool_library("Batch B Tools")
    end_mill = machine_workspace.register_tool(
        tools,
        "10mm End Mill",
        "End Mill",
        diameter=10.0,
        length=60.0,
        material="Carbide",
        operating_limits={"max_rpm": 18000},
    )
    drill = machine_workspace.register_tool(
        tools,
        "5mm Drill",
        "Drill",
        diameter=5.0,
        length=80.0,
        material="HSS",
        operating_limits={"max_rpm": 6000},
    )
    material = machine_workspace.register_material(
        "Aluminum 6061",
        "Aluminium",
        density=2700,
        color="#b0bec5",
        manufacturing_notes="CNC stock.",
        compatible_machines=[machine],
        default_process_metadata={"coolant": "Mist"},
    )
    profile = machine_workspace.create_profile(
        machine,
        "Mill Aluminum Profile",
        tool_library=tools,
        version="1.0",
    )
    machine_workspace.activate_profile(profile)

    job = manufacturing_engine.create_job(
        "Bracket Manufacturing Job",
        description="Batch B CNC planning job.",
        machine_profile=profile,
        material=material,
        revision="A",
        version="1.0",
        status="Pending",
    )
    manufacturing_engine.edit_job(job, status="Ready")
    duplicated = manufacturing_engine.duplicate_job(job, "Bracket Manufacturing Job Copy")
    assert duplicated.name == "Bracket Manufacturing Job Copy"
    assert manufacturing_engine.delete_job(duplicated) is True

    setup = manufacturing_engine.create_stock(
        job,
        stock_type="Box",
        dimensions={"x": 120, "y": 80, "z": 20},
        material=material,
        weight=0.52,
        origin={"x": 0, "y": 0, "z": 0},
        allowance=1.0,
        notes="Oversized billet.",
    )
    fixture = manufacturing_engine.create_fixture(
        job,
        fixture_type="Vise",
        clamping_method="Soft jaws",
        reference_surfaces=["top_face"],
        alignment_method="Fixed stop",
        offsets={"x": 1.0},
        notes="Use parallels.",
        compatible_machines=[machine],
    )
    coordinate = manufacturing_engine.create_coordinate_system(
        job,
        "Top WCS",
        "Work Coordinate System",
        origin={"x": 0, "y": 0, "z": 20},
        activate=True,
    )
    offset = manufacturing_engine.create_work_offset(
        job,
        "G54",
        translation={"x": 0, "y": 0, "z": 20},
        rotation={"x": 0, "y": 0, "z": 0},
        reference_system=coordinate["id"],
    )

    facing = manufacturing_engine.create_operation(
        job,
        "Facing",
        name="Face Stock",
        estimated_duration=6.0,
        required_machine=profile,
        required_tool=end_mill,
        required_material=material,
        status="Ready",
    )
    pocket = manufacturing_engine.create_operation(
        job,
        "Pocketing",
        name="Pocket Relief",
        dependencies=[facing],
        estimated_duration=12.0,
        required_machine=profile,
        required_tool=end_mill,
        required_material=material,
        status="Ready",
    )
    drill_op = manufacturing_engine.create_operation(
        job,
        "Drilling",
        name="Drill Mounting Holes",
        dependencies=[pocket],
        estimated_duration=8.0,
        required_machine=profile,
        required_tool=drill,
        required_material=material,
        status="Ready",
    )

    plan = manufacturing_engine.build_execution_plan(job)
    validation = manufacturing_engine.validate()
    diagnostics = manufacturing_engine.diagnostics()

    assert plan.valid is True
    assert plan.status == "Validated"
    assert plan.operation_ids == [facing.id, pocket.id, drill_op.id]
    assert fixture.fixture_type == "Vise"
    assert setup.stock.material_id == material.id
    assert offset.name == "G54"
    assert validation.valid is True
    assert diagnostics.jobs == 1
    assert diagnostics.operations == 3
    assert diagnostics.execution_plan_statistics["plans"] == 1

    manufacturing_engine.transition_job(job, "Validated")
    manufacturing_engine.transition_job(job, "Running")
    manufacturing_engine.transition_job(job, "Completed")
    manufacturing_engine.archive_job(job)
    assert job.metadata.status == "Archived"

    duplicate_checks = [
        lambda: manufacturing_engine.create_job("Bracket Manufacturing Job"),
        lambda: manufacturing_engine.create_operation(job, "Facing", name="Face Stock"),
        lambda: manufacturing_engine.create_coordinate_system(job, "Top WCS"),
        lambda: manufacturing_engine.create_work_offset(job, "G54"),
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
        path = Path(directory) / "manufacturing_engine.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored_engine = restored.manufacturing_engine
    restored_engine.load_from_settings()
    restored_job = restored_engine.job_for("Bracket Manufacturing Job")
    restored_plan = restored_engine.execution_plans[0]
    restored_validation = restored_engine.validate()
    restored_diagnostics = restored_engine.diagnostics()

    assert restored_job is not None
    assert restored_job.metadata.status == "Archived"
    assert restored_plan.status == "Validated"
    assert restored_validation.valid is True
    assert restored_diagnostics.jobs == 1
    assert restored_diagnostics.operations == 3
    assert len(restored_engine.coordinate_systems) == 1
    assert len([item for item in restored_engine.work_offsets if item.metadata.get("job_id")]) == 1
    assert list(restored.scene3d.entities()) == []


if __name__ == "__main__":
    test_manufacturing_engine_metadata_planning_and_persistence()
    print("manufacturing-engine-ok")
