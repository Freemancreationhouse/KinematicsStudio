from pathlib import Path
from tempfile import TemporaryDirectory

from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_sheet_manufacturing_laser_plasma_waterjet_programs_and_persistence():
    workspace = Workspace("Sheet Manufacturing Project")
    machine_workspace = workspace.machine_workspace.initialize()
    engine = workspace.manufacturing_engine.initialize()

    laser_machine = machine_workspace.register_machine(
        "KS Laser Pro",
        "Laser Cutter",
        manufacturer="Kinematics Studio",
        model="Laser Pro",
        firmware="GRBL",
        work_envelope={"x": 900, "y": 600, "z": 80},
        supported_materials=["Birch Plywood"],
        supported_tool_systems=["CO2 Laser"],
        supported_file_formats=["GCODE"],
    )
    plasma_machine = machine_workspace.register_machine(
        "KS Plasma Pro",
        "Plasma Cutter",
        manufacturer="Kinematics Studio",
        model="Plasma Pro",
        firmware="LinuxCNC",
        work_envelope={"x": 1200, "y": 900, "z": 120},
        supported_materials=["Mild Steel"],
        supported_tool_systems=["Plasma Torch"],
        supported_file_formats=["NGC"],
    )
    waterjet_machine = machine_workspace.register_machine(
        "KS Waterjet Pro",
        "Waterjet",
        manufacturer="Kinematics Studio",
        model="Waterjet Pro",
        firmware="Mach4",
        work_envelope={"x": 1500, "y": 1000, "z": 150},
        supported_materials=["Aluminum Sheet"],
        supported_tool_systems=["Waterjet Nozzle"],
        supported_file_formats=["TAP"],
    )
    tools = machine_workspace.create_tool_library("Sheet Fabrication Tools")
    laser_tool = machine_workspace.register_tool(
        tools,
        "CO2 Laser Head",
        "Laser Lens",
        diameter=0.15,
        length=50.0,
        material="Optics",
        operating_limits={"max_power": 100},
    )
    plasma_tool = machine_workspace.register_tool(
        tools,
        "45A Plasma Torch",
        "Nozzle",
        diameter=1.0,
        length=80.0,
        material="Copper",
        operating_limits={"max_current": 45},
    )
    waterjet_tool = machine_workspace.register_tool(
        tools,
        "0.8mm Waterjet Nozzle",
        "Nozzle",
        diameter=0.8,
        length=75.0,
        material="Ruby",
        operating_limits={"max_pressure": 60000},
    )
    plywood = machine_workspace.register_material(
        "Birch Plywood",
        "Wood",
        density=650,
        compatible_machines=[laser_machine],
        default_process_metadata={
            "sheet_thickness": 6.0,
            "laser": {"power": 65, "speed": 1200, "pierce": 0.2},
            "cut_quality": "Clean edge",
        },
    )
    steel = machine_workspace.register_material(
        "Mild Steel",
        "Steel",
        density=7850,
        compatible_machines=[plasma_machine],
        default_process_metadata={
            "sheet_thickness": 3.0,
            "plasma": {"speed": 900, "pierce_height": 4.0, "cut_height": 1.5},
            "cut_quality": "Production",
        },
    )
    aluminum = machine_workspace.register_material(
        "Aluminum Sheet",
        "Aluminium",
        density=2700,
        compatible_machines=[waterjet_machine],
        default_process_metadata={
            "sheet_thickness": 5.0,
            "waterjet": {"quality": 4, "low_pressure_pierce": True, "high_pressure_cutting": True},
            "cut_quality": "Fine",
        },
    )
    laser_profile = machine_workspace.create_profile(laser_machine, "Laser Plywood Profile", tool_library=tools)
    plasma_profile = machine_workspace.create_profile(plasma_machine, "Plasma Steel Profile", tool_library=tools)
    waterjet_profile = machine_workspace.create_profile(waterjet_machine, "Waterjet Aluminum Profile", tool_library=tools)

    laser_job = engine.create_sheet_job(
        "Laser Sign Panel",
        "Laser",
        machine_profile=laser_profile,
        material=plywood,
        sheet_size={"x": 900, "y": 600},
        thickness=6.0,
        parts=[
            {"name": "Letter A", "width": 120, "height": 80, "quantity": 2, "priority": 1, "group": "Letters"},
            {"name": "Border", "width": 220, "height": 120, "quantity": 1, "priority": 0, "group": "Frame"},
        ],
    )
    laser_params = engine.configure_sheet_parameters(
        laser_job,
        operation_type="Vector Cut",
        process="Laser",
        kerf_width=0.15,
        compensation="Outside",
        power=65,
        speed=1200,
        pass_count=2,
        pierce={"delay": 0.2, "height": 1.0},
        lead_in={"length": 4.0, "angle": 45.0},
        lead_out={"length": 3.0, "angle": 45.0},
        gas={"air_assist": True, "pressure": 3.0},
        raster={"enabled": True, "dpi": 300},
        corner_optimization=True,
    )
    laser_layout = engine.nest_sheet(laser_job, spacing=5.0)
    laser_paths = engine.generate_sheet_toolpaths(laser_job, laser_params, laser_layout)
    laser_program = engine.generate_sheet_program(laser_job, "GRBL Laser")
    generic_laser = engine.generate_sheet_program(laser_job, "Generic G-code")

    assert laser_layout.valid is True
    assert len(laser_paths) == 3
    assert all(path.valid for path in laser_paths)
    assert laser_paths[0].compensated_points != laser_paths[0].points
    assert laser_paths[0].lead_in and laser_paths[0].lead_out
    assert laser_program.valid is True
    assert "M4 S65" in laser_program.content
    assert "G21" in generic_laser.content
    assert laser_tool.metadata.properties["operating_limits"]["max_power"] == 100

    plasma_job = engine.create_sheet_job(
        "Plasma Bracket Plate",
        "Plasma",
        machine_profile=plasma_profile,
        material=steel,
        sheet_size={"x": 1200, "y": 900},
        thickness=3.0,
        parts=[{"name": "Bracket", "width": 180, "height": 120, "quantity": 2, "priority": 0}],
    )
    plasma_params = engine.configure_sheet_parameters(
        plasma_job,
        process="Plasma",
        kerf_width=1.2,
        compensation="Outside",
        speed=900,
        pierce={"delay": 0.8, "height": 4.0},
        lead_in={"length": 8.0, "angle": 30.0},
        lead_out={"length": 5.0, "angle": 30.0},
        height_control={"enabled": True, "cut_height": 1.5},
        consumable={"nozzle": "45A", "electrode": "standard"},
        corner_slowdown=True,
    )
    plasma_layout = engine.nest_sheet(plasma_job, spacing=8.0)
    plasma_paths = engine.generate_sheet_toolpaths(plasma_job, plasma_params, plasma_layout)
    plasma_program = engine.generate_sheet_program(plasma_job, "LinuxCNC")
    plasma_metadata_program = engine.generate_sheet_program(plasma_job, "Plasma controller metadata")

    assert plasma_layout.valid is True
    assert len(plasma_paths) == 2
    assert plasma_paths[0].metadata["corner_slowdown"] is True
    assert "PLASMA_CONTROLLER_METADATA" in plasma_program.content
    assert "PLASMA_CONTROLLER_METADATA" in plasma_metadata_program.content
    assert plasma_tool.metadata.properties["operating_limits"]["max_current"] == 45

    waterjet_job = engine.create_sheet_job(
        "Waterjet Mount Plate",
        "Waterjet",
        machine_profile=waterjet_profile,
        material=aluminum,
        sheet_size={"x": 1500, "y": 1000},
        thickness=5.0,
        parts=[{"name": "Mount Plate", "width": 240, "height": 160, "quantity": 1, "priority": 0}],
    )
    waterjet_params = engine.configure_sheet_parameters(
        waterjet_job,
        process="Waterjet",
        kerf_width=0.8,
        compensation="Centerline",
        speed=700,
        pierce={"delay": 1.4, "height": 2.0},
        waterjet={"quality": 4, "low_pressure_pierce": True, "high_pressure_cutting": True},
        taper={"compensation": "standard"},
    )
    waterjet_layout = engine.nest_sheet(waterjet_job, spacing=10.0)
    waterjet_paths = engine.generate_sheet_toolpaths(waterjet_job, waterjet_params, waterjet_layout)
    waterjet_program = engine.generate_sheet_program(waterjet_job, "Mach4")
    waterjet_metadata_program = engine.generate_sheet_program(waterjet_job, "Waterjet controller metadata")

    assert waterjet_layout.valid is True
    assert len(waterjet_paths) == 1
    assert waterjet_paths[0].points == waterjet_paths[0].compensated_points
    assert "WATERJET_CONTROLLER_METADATA" in waterjet_program.content
    assert "WATERJET_CONTROLLER_METADATA" in waterjet_metadata_program.content
    assert waterjet_tool.metadata.properties["operating_limits"]["max_pressure"] == 60000

    validation = engine.validate()
    diagnostics = engine.diagnostics()

    assert validation.valid is True
    assert diagnostics.execution_plan_statistics["sheet_nest_layouts"] == 3
    assert diagnostics.execution_plan_statistics["sheet_cut_paths"] == 6
    assert diagnostics.execution_plan_statistics["sheet_programs"] == 6
    assert diagnostics.execution_plan_statistics["sheet_program_lines"] > 0
    assert diagnostics.execution_plan_statistics["sheet_pierces"] >= 6
    assert diagnostics.execution_plan_statistics["sheet_estimated_cutting_time"] > 0
    assert diagnostics.execution_plan_statistics["sheet_material_utilization"] > 0
    assert diagnostics.execution_plan_statistics["sheet_kerf_paths"] == 6
    assert len(workspace.product_manager.laser_jobs) == 1
    assert len(workspace.product_manager.plasma_jobs) == 1
    assert len(workspace.product_manager.nesting_jobs) == 3

    assert list(workspace.scene3d.entities()) == []
    assert getattr(workspace.product_manager, "bodies", []) == []
    assert getattr(workspace.product_manager, "features", []) == []
    assert workspace.command_manager.undo_stack == []
    assert workspace.command_manager.redo_stack == []

    with TemporaryDirectory() as directory:
        path = Path(directory) / "sheet_manufacturing.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.machine_workspace.load_from_settings()
    restored_engine = restored.manufacturing_engine
    restored_engine.load_from_settings()

    assert len(restored_engine.sheet_parameters) == 3
    assert len(restored_engine.sheet_material_profiles) == 3
    assert len(restored_engine.sheet_nest_layouts) == 3
    assert len(restored_engine.sheet_cut_paths) == 6
    assert len(restored_engine.sheet_programs) == 6
    assert restored_engine.validate().valid is True
    assert len(restored.product_manager.laser_jobs) == 1
    assert len(restored.product_manager.plasma_jobs) == 1
    assert len(restored.product_manager.nesting_jobs) == 3
    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []
    assert restored.command_manager.undo_stack == []
    assert restored.command_manager.redo_stack == []


if __name__ == "__main__":
    test_sheet_manufacturing_laser_plasma_waterjet_programs_and_persistence()
    print("sheet-manufacturing-ok")
