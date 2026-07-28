from pathlib import Path
from tempfile import TemporaryDirectory

from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_cnc_machining_toolpaths_gcode_and_persistence():
    workspace = Workspace("CNC Machining Project")
    machine_workspace = workspace.machine_workspace.initialize()
    engine = workspace.manufacturing_engine.initialize()

    machine = machine_workspace.register_machine(
        "KS CNC Pro",
        "CNC Mill",
        manufacturer="Kinematics Studio",
        model="CNC Pro",
        firmware="Haas",
        work_envelope={"x": 600, "y": 400, "z": 300},
        supported_materials=["Aluminum 6061"],
        supported_tool_systems=["End Mill", "Drill", "Chamfer Tool"],
        supported_file_formats=["NC", "TAP"],
    )
    tools = machine_workspace.create_tool_library("CNC Production Tools")
    end_mill = machine_workspace.register_tool(
        tools,
        "8mm Carbide End Mill",
        "End Mill",
        diameter=8.0,
        length=60.0,
        material="Carbide",
        operating_limits={"max_rpm": 18000, "max_feed": 3000},
    )
    drill = machine_workspace.register_tool(
        tools,
        "4.2mm Drill",
        "Drill",
        diameter=4.2,
        length=75.0,
        material="HSS",
        operating_limits={"max_rpm": 7000},
    )
    chamfer = machine_workspace.register_tool(
        tools,
        "90deg Chamfer Tool",
        "Chamfer Tool",
        diameter=10.0,
        length=50.0,
        material="Carbide",
        operating_limits={"max_rpm": 12000},
    )
    material = machine_workspace.register_material(
        "Aluminum 6061",
        "Aluminium",
        density=2700,
        compatible_machines=[machine],
        default_process_metadata={"surface_speed": 180, "chip_load": 0.04},
    )
    profile = machine_workspace.create_profile(
        machine,
        "Haas Aluminum CNC Profile",
        tool_library=tools,
        version="1.0",
    )
    machine_workspace.activate_profile(profile)

    job = engine.create_job(
        "CNC Bracket Program",
        description="Production CNC bracket.",
        machine_profile=profile,
        material=material,
        revision="A",
        version="1.0",
        status="Pending",
    )
    engine.create_stock(
        job,
        stock_type="Box",
        dimensions={"x": 100, "y": 70, "z": 16},
        material=material,
        allowance=0.5,
    )
    engine.create_fixture(
        job,
        fixture_type="Vise",
        clamping_method="Soft jaws",
        reference_surfaces=["bottom", "left"],
        alignment_method="Fixed stop",
        compatible_machines=[machine],
    )
    coordinate = engine.create_coordinate_system(
        job,
        "Top Work Coordinate",
        "Work Coordinate System",
        origin={"x": 0, "y": 0, "z": 16},
        activate=True,
    )
    engine.create_work_offset(
        job,
        "G54",
        translation={"x": 0, "y": 0, "z": 16},
        rotation={"x": 0, "y": 0, "z": 0},
        reference_system=coordinate["id"],
    )

    facing = engine.create_operation(
        job,
        "Facing",
        name="Face Top",
        required_machine=profile,
        required_tool=end_mill,
        required_material=material,
        feeds={"feed_rate": 850, "plunge_rate": 250},
        speeds={"rpm": 9000},
        coolant={"flood": True},
        depth=0.4,
        stepover=5.0,
        stepdown=0.4,
        tolerance=0.02,
        cut_geometry={"points": [{"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 100, "y": 70}, {"x": 0, "y": 70}, {"x": 0, "y": 0}]},
    )
    pocket = engine.create_operation(
        job,
        "2D Pocket",
        name="Pocket Relief",
        dependencies=[facing],
        required_machine=profile,
        required_tool=end_mill,
        required_material=material,
        depth=4.0,
        stepover=3.0,
        stepdown=1.0,
        tolerance=0.03,
        cut_geometry={"points": [{"x": 20, "y": 20}, {"x": 80, "y": 20}, {"x": 80, "y": 50}, {"x": 20, "y": 50}, {"x": 20, "y": 20}]},
    )
    drill_op = engine.create_operation(
        job,
        "Peck Drilling",
        name="Drill Holes",
        dependencies=[pocket],
        required_machine=profile,
        required_tool=drill,
        required_material=material,
        depth=10.0,
        cut_geometry={"points": [{"x": 20, "y": 20}, {"x": 80, "y": 20}, {"x": 80, "y": 50}, {"x": 20, "y": 50}]},
    )
    chamfer_op = engine.create_operation(
        job,
        "Chamfer",
        name="Chamfer Perimeter",
        dependencies=[drill_op],
        required_machine=profile,
        required_tool=chamfer,
        required_material=material,
        depth=0.5,
        stepover=1.0,
        stepdown=0.5,
        cut_geometry={"points": [{"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 100, "y": 70}, {"x": 0, "y": 70}, {"x": 0, "y": 0}]},
    )

    cam_plan = engine.plan_cam_job(job)
    toolpaths = engine.generate_toolpaths(job)
    generic = engine.generate_gcode(job, "Generic ISO G-code", "BRACKET_GENERIC")
    fanuc = engine.generate_gcode(job, "Fanuc", "BRACKET_FANUC")
    haas = engine.generate_gcode(job, "Haas", "BRACKET_HAAS")
    linuxcnc = engine.generate_gcode(job, "LinuxCNC", "BRACKET_LINUXCNC")
    mach3 = engine.generate_gcode(job, "Mach3", "BRACKET_MACH3")
    mach4 = engine.generate_gcode(job, "Mach4", "BRACKET_MACH4")
    grbl = engine.generate_gcode(job, "GRBL", "BRACKET_GRBL")
    validation = engine.validate()
    diagnostics = engine.diagnostics()

    assert cam_plan.valid is True
    assert len(cam_plan.operation_ids) == 4
    assert len(toolpaths) == 4
    assert all(path.valid for path in toolpaths)
    assert all(path.moves for path in toolpaths)
    assert toolpaths[0].cutting_parameters.rpm == 9000
    assert toolpaths[0].cutting_parameters.feed_rate == 850
    assert "G21" in generic.gcode
    assert "G90" in generic.gcode
    assert "M30" in generic.gcode
    assert "T" in fanuc.gcode and "M6" in fanuc.gcode
    assert "T" in haas.gcode and "M6" in haas.gcode
    assert "G81" in linuxcnc.gcode or "G83" in linuxcnc.gcode
    assert "M30" in mach3.gcode
    assert "M30" in mach4.gcode
    assert "M6" not in grbl.gcode
    assert validation.valid is True
    assert diagnostics.execution_plan_statistics["toolpaths"] == 4
    assert diagnostics.execution_plan_statistics["generated_programs"] == 7
    assert diagnostics.execution_plan_statistics["gcode_lines"] > 0

    with TemporaryDirectory() as directory:
        path = Path(directory) / "cnc_machining.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored_engine = restored.manufacturing_engine
    restored_engine.load_from_settings()
    assert len(restored_engine.cam_plans) == 1
    assert len(restored_engine.toolpaths) == 4
    assert len(restored_engine.generated_programs) == 7
    assert "BRACKET_HAAS" in restored_engine.generated_programs[2].gcode
    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []
    assert restored.command_manager.undo_stack == []
    assert restored.command_manager.redo_stack == []


if __name__ == "__main__":
    test_cnc_machining_toolpaths_gcode_and_persistence()
    print("cnc-machining-ok")
