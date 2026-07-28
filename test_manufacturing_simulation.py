from pathlib import Path
from tempfile import TemporaryDirectory

from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_manufacturing_simulation_replay_verification_reports_and_persistence():
    workspace = Workspace("Manufacturing Simulation Project")
    machine_workspace = workspace.machine_workspace.initialize()
    engine = workspace.manufacturing_engine.initialize()

    cnc_machine = machine_workspace.register_machine(
        "Simulation CNC",
        "CNC Mill",
        work_envelope={"x": 500, "y": 400, "z": 250},
        supported_materials=["Aluminum"],
        supported_tool_systems=["End Mill"],
    )
    fdm_machine = machine_workspace.register_machine(
        "Simulation FDM",
        "FDM Printer",
        work_envelope={"x": 220, "y": 220, "z": 220},
        supported_materials=["PLA"],
        supported_tool_systems=["Extruder"],
    )
    laser_machine = machine_workspace.register_machine(
        "Simulation Laser",
        "Laser Cutter",
        work_envelope={"x": 800, "y": 500, "z": 80},
        supported_materials=["Plywood"],
        supported_tool_systems=["Laser Lens"],
    )
    robot_machine = machine_workspace.register_machine(
        "Simulation Robot",
        "Robot",
        work_envelope={"x": 1200, "y": 1200, "z": 1200},
        supported_materials=["Payload"],
        supported_tool_systems=["Robot End Effector"],
    )
    tools = machine_workspace.create_tool_library("Simulation Tools")
    end_mill = machine_workspace.register_tool(tools, "6mm End Mill", "End Mill", diameter=6.0, length=50.0)
    machine_workspace.register_tool(tools, "0.4mm Nozzle", "Extruder", diameter=0.4, length=12.0)
    machine_workspace.register_tool(tools, "Laser Head", "Laser Lens", diameter=0.15, length=40.0)
    gripper = machine_workspace.register_tool(tools, "Robot Gripper", "Robot End Effector", diameter=60.0, length=120.0)
    aluminum = machine_workspace.register_material("Aluminum", "Aluminium", density=2700, compatible_machines=[cnc_machine])
    pla = machine_workspace.register_material("PLA", "Plastic", density=1240, compatible_machines=[fdm_machine])
    plywood = machine_workspace.register_material("Plywood", "Wood", density=650, compatible_machines=[laser_machine])
    payload = machine_workspace.register_material("Payload", "Custom Materials", density=1, compatible_machines=[robot_machine])
    cnc_profile = machine_workspace.create_profile(cnc_machine, "Simulation CNC Profile", tool_library=tools)
    fdm_profile = machine_workspace.create_profile(fdm_machine, "Simulation FDM Profile", tool_library=tools)
    laser_profile = machine_workspace.create_profile(laser_machine, "Simulation Laser Profile", tool_library=tools)
    robot_profile_record = machine_workspace.create_profile(robot_machine, "Simulation Robot Profile", tool_library=tools)

    cnc_job = engine.create_job("Simulation CNC Job", machine_profile=cnc_profile, material=aluminum)
    engine.create_stock(cnc_job, dimensions={"x": 80, "y": 50, "z": 12}, material=aluminum)
    engine.create_fixture(cnc_job, fixture_type="Vise")
    coordinate = engine.create_coordinate_system(cnc_job, "CNC WCS", "Work Coordinate System", activate=True)
    engine.create_work_offset(cnc_job, "G54", reference_system=coordinate["id"])
    engine.create_operation(
        cnc_job,
        "2D Profile",
        required_tool=end_mill,
        required_material=aluminum,
        feeds={"feed_rate": 600},
        speeds={"rpm": 8000},
        depth=2.0,
        cut_geometry={"points": [{"x": 0, "y": 0}, {"x": 80, "y": 0}, {"x": 80, "y": 50}, {"x": 0, "y": 50}, {"x": 0, "y": 0}]},
    )
    engine.plan_cam_job(cnc_job)
    engine.generate_toolpaths(cnc_job)
    engine.generate_gcode(cnc_job, "Generic ISO G-code", "SIM_CNC")

    fdm_job = engine.create_additive_job(
        "Simulation FDM Job",
        "FDM",
        machine_profile=fdm_profile,
        material=pla,
        model_dimensions={"x": 20, "y": 20, "z": 4},
    )
    fdm_params = engine.configure_print_parameters(fdm_job, technology="FDM", layer_height=0.2, print_speed=50)
    fdm_support = engine.generate_supports(fdm_job, support_type="Tree", density=10)
    engine.plan_build_plate(fdm_job)
    engine.slice_fdm(fdm_job, fdm_params, fdm_support)
    engine.generate_print_file(fdm_job, "Generic G-code")

    sheet_job = engine.create_sheet_job(
        "Simulation Sheet Job",
        "Laser",
        machine_profile=laser_profile,
        material=plywood,
        sheet_size={"x": 500, "y": 300},
        parts=[{"name": "Panel", "width": 100, "height": 60, "quantity": 1}],
    )
    sheet_params = engine.configure_sheet_parameters(sheet_job, process="Laser", kerf_width=0.15, speed=1000, power=50)
    sheet_layout = engine.nest_sheet(sheet_job)
    engine.generate_sheet_toolpaths(sheet_job, sheet_params, sheet_layout)
    engine.generate_sheet_program(sheet_job, "Generic G-code")

    robot_profile = engine.create_robot_profile(
        "Simulation Robot Arm",
        "6-axis",
        machine_profile=robot_profile_record,
        payload=5.0,
        reach=1200.0,
    )
    robot_job = engine.create_robot_job(
        "Simulation Robot Job",
        robot_profile,
        machine_profile=robot_profile_record,
        material=payload,
    )
    user_frame = engine.define_robot_frame(robot_job, "Simulation User Frame", "User Frame")
    engine.plan_robot_motion(robot_job, "Joint", {"x": 100, "y": 0, "z": 200}, [0, -10, 20, 0, 30, 0], user_frame, 200, 500, process={"pick_place": True})
    engine.plan_robot_motion(robot_job, "Linear", {"x": 200, "y": 50, "z": 200}, [5, -8, 18, 0, 25, 0], user_frame, 180, 450)
    engine.generate_robot_trajectory(robot_job)
    engine.generate_robot_program(robot_job, "Generic Robot Program")
    assert gripper.name == "Robot Gripper"

    reports = []
    for job in (cnc_job, fdm_job, sheet_job, robot_job):
        simulation = engine.create_simulation_job(job)
        session = engine.run_simulation(simulation)
        collision = engine.check_simulation_collisions(simulation)
        verification = engine.verify_simulation(simulation)
        report = engine.generate_simulation_report(simulation)
        assert simulation.valid is True
        assert session.valid is True
        assert session.progress == 1.0
        assert collision.valid is True
        assert verification.valid is True
        assert report.valid is True
        assert report.summary
        reports.append(report)

    validation = engine.validate()
    diagnostics = engine.diagnostics()

    assert validation.valid is True
    assert len(reports) == 4
    assert diagnostics.execution_plan_statistics["simulation_jobs"] == 4
    assert diagnostics.execution_plan_statistics["simulation_sessions"] == 4
    assert diagnostics.execution_plan_statistics["simulation_replay_steps"] > 0
    assert diagnostics.execution_plan_statistics["simulation_collision_reports"] == 4
    assert diagnostics.execution_plan_statistics["simulation_collisions"] == 0
    assert diagnostics.execution_plan_statistics["simulation_verification_reports"] == 4
    assert diagnostics.execution_plan_statistics["simulation_reports"] == 4
    assert diagnostics.execution_plan_statistics["simulation_estimated_cycle_time"] > 0
    assert diagnostics.execution_plan_statistics["simulation_estimated_print_time"] > 0
    assert diagnostics.execution_plan_statistics["simulation_estimated_cutting_time"] > 0

    assert list(workspace.scene3d.entities()) == []
    assert getattr(workspace.product_manager, "bodies", []) == []
    assert getattr(workspace.product_manager, "features", []) == []
    assert workspace.command_manager.undo_stack == []
    assert workspace.command_manager.redo_stack == []

    with TemporaryDirectory() as directory:
        path = Path(directory) / "manufacturing_simulation.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.machine_workspace.load_from_settings()
    restored_engine = restored.manufacturing_engine
    restored_engine.load_from_settings()

    assert len(restored_engine.simulation_jobs) == 4
    assert len(restored_engine.simulation_sessions) == 4
    assert len(restored_engine.simulation_collision_reports) == 4
    assert len(restored_engine.simulation_verification_reports) == 4
    assert len(restored_engine.simulation_reports) == 4
    assert restored_engine.validate().valid is True
    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []
    assert restored.command_manager.undo_stack == []
    assert restored.command_manager.redo_stack == []


if __name__ == "__main__":
    test_manufacturing_simulation_replay_verification_reports_and_persistence()
    print("manufacturing-simulation-ok")
