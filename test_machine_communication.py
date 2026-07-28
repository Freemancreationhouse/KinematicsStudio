from pathlib import Path
from tempfile import TemporaryDirectory

from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_machine_communication_dispatch_monitoring_events_and_persistence():
    workspace = Workspace("Machine Communication Project")
    machine_workspace = workspace.machine_workspace.initialize()
    engine = workspace.manufacturing_engine.initialize()

    tools = machine_workspace.create_tool_library("Communication Tools")
    cnc_machine = machine_workspace.register_machine(
        "Communication CNC",
        "CNC Mill",
        firmware="GRBL",
        work_envelope={"x": 300, "y": 250, "z": 120},
        supported_materials=["Aluminum"],
        supported_tool_systems=["End Mill"],
        supported_file_formats=["GCODE"],
    )
    fdm_machine = machine_workspace.register_machine(
        "Communication FDM",
        "FDM Printer",
        firmware="Klipper",
        work_envelope={"x": 220, "y": 220, "z": 220},
        supported_materials=["PLA"],
        supported_tool_systems=["Extruder"],
        supported_file_formats=["GCODE"],
    )
    laser_machine = machine_workspace.register_machine(
        "Communication Laser",
        "Laser Cutter",
        firmware="LinuxCNC",
        work_envelope={"x": 700, "y": 400, "z": 60},
        supported_materials=["Plywood"],
        supported_tool_systems=["Laser Lens"],
        supported_file_formats=["NGC"],
    )
    robot_machine = machine_workspace.register_machine(
        "Communication Robot",
        "Robot",
        firmware="Fanuc",
        work_envelope={"x": 1200, "y": 1200, "z": 1200},
        supported_materials=["Payload"],
        supported_tool_systems=["Robot End Effector"],
        supported_file_formats=["TP"],
    )
    end_mill = machine_workspace.register_tool(tools, "6mm End Mill", "End Mill", diameter=6.0, length=45.0)
    machine_workspace.register_tool(tools, "0.4mm Nozzle", "Extruder", diameter=0.4, length=12.0)
    machine_workspace.register_tool(tools, "Laser Head", "Laser Lens", diameter=0.15, length=35.0)
    machine_workspace.register_tool(tools, "Robot Gripper", "Robot End Effector", diameter=50.0, length=120.0)
    aluminum = machine_workspace.register_material("Aluminum", "Aluminium", compatible_machines=[cnc_machine])
    pla = machine_workspace.register_material("PLA", "Plastic", compatible_machines=[fdm_machine])
    plywood = machine_workspace.register_material("Plywood", "Wood", compatible_machines=[laser_machine])
    payload = machine_workspace.register_material("Payload", "Custom Materials", compatible_machines=[robot_machine])
    cnc_profile = machine_workspace.create_profile(cnc_machine, "Communication CNC Profile", tool_library=tools)
    fdm_profile = machine_workspace.create_profile(fdm_machine, "Communication FDM Profile", tool_library=tools)
    laser_profile = machine_workspace.create_profile(laser_machine, "Communication Laser Profile", tool_library=tools)
    robot_profile_record = machine_workspace.create_profile(robot_machine, "Communication Robot Profile", tool_library=tools)

    cnc_job = engine.create_job("Communication CNC Job", machine_profile=cnc_profile, material=aluminum)
    engine.create_stock(cnc_job, dimensions={"x": 60, "y": 40, "z": 10}, material=aluminum)
    engine.create_fixture(cnc_job, fixture_type="Vise")
    coordinate = engine.create_coordinate_system(cnc_job, "Communication WCS", "Work Coordinate System", activate=True)
    engine.create_work_offset(cnc_job, "G54", reference_system=coordinate["id"])
    engine.create_operation(
        cnc_job,
        "2D Profile",
        required_tool=end_mill,
        required_material=aluminum,
        cut_geometry={"points": [{"x": 0, "y": 0}, {"x": 60, "y": 0}, {"x": 60, "y": 40}, {"x": 0, "y": 40}, {"x": 0, "y": 0}]},
    )
    engine.plan_cam_job(cnc_job)
    engine.generate_toolpaths(cnc_job)
    engine.generate_gcode(cnc_job, "GRBL", "COMM_CNC")

    fdm_job = engine.create_additive_job(
        "Communication FDM Job",
        "FDM",
        machine_profile=fdm_profile,
        material=pla,
        model_dimensions={"x": 20, "y": 20, "z": 3},
    )
    fdm_params = engine.configure_print_parameters(fdm_job, technology="FDM", layer_height=0.2)
    engine.plan_build_plate(fdm_job)
    engine.slice_fdm(fdm_job, fdm_params)
    engine.generate_print_file(fdm_job, "Klipper G-code")

    sheet_job = engine.create_sheet_job(
        "Communication Sheet Job",
        "Laser",
        machine_profile=laser_profile,
        material=plywood,
        sheet_size={"x": 400, "y": 250},
        parts=[{"name": "Panel", "width": 80, "height": 50, "quantity": 1}],
    )
    sheet_params = engine.configure_sheet_parameters(sheet_job, process="Laser", kerf_width=0.15, speed=900, power=45)
    layout = engine.nest_sheet(sheet_job)
    engine.generate_sheet_toolpaths(sheet_job, sheet_params, layout)
    engine.generate_sheet_program(sheet_job, "LinuxCNC")

    robot_profile = engine.create_robot_profile(
        "Communication Robot Arm",
        "6-axis",
        machine_profile=robot_profile_record,
        payload=5.0,
        reach=1200.0,
    )
    robot_job = engine.create_robot_job(
        "Communication Robot Job",
        robot_profile,
        machine_profile=robot_profile_record,
        material=payload,
    )
    frame = engine.define_robot_frame(robot_job, "Communication User Frame", "User Frame")
    engine.plan_robot_motion(robot_job, "Joint", {"x": 120, "y": 0, "z": 200}, [0, -10, 20, 0, 30, 0], frame, 200, 500)
    engine.generate_robot_trajectory(robot_job)
    engine.generate_robot_program(robot_job, "Fanuc TP metadata")

    jobs_and_connections = [
        (cnc_job, engine.create_machine_connection(cnc_profile, "GRBL", "Serial", {"port": "COM1", "baud": 115200})),
        (fdm_job, engine.create_machine_connection(fdm_profile, "Klipper", "TCP/IP", {"host": "127.0.0.1", "port": 7125})),
        (sheet_job, engine.create_machine_connection(laser_profile, "LinuxCNC", "TCP/IP", {"host": "127.0.0.1", "port": 5007})),
        (robot_job, engine.create_machine_connection(robot_profile_record, "Fanuc foundation", "Network", {"host": "192.168.0.10"})),
    ]

    extra_protocols = [
        engine.create_machine_connection(cnc_profile, "Marlin", "Serial", {"port": "COM2"}),
        engine.create_machine_connection(cnc_profile, "Mach3", "USB", {"port": "USB0"}),
        engine.create_machine_connection(cnc_profile, "Mach4", "TCP/IP", {"host": "127.0.0.1"}),
        engine.create_machine_connection(cnc_profile, "Haas foundation", "Network", {"host": "192.168.0.20"}),
        engine.create_machine_connection(cnc_profile, "Siemens foundation", "Network", {"host": "192.168.0.30"}),
    ]
    assert all(connection.valid for connection in extra_protocols)

    sessions = []
    for index, (job, connection) in enumerate(jobs_and_connections):
        engine.connect_machine(connection)
        engine.heartbeat_machine(connection)
        queue_item = engine.queue_machine_job(job, connection, priority=10 - index, max_retries=2)
        session = engine.upload_machine_job(queue_item)
        engine.start_machine_job(session)
        engine.pause_machine_job(session)
        engine.resume_machine_job(session)
        engine.stop_machine_job(session)
        status = engine.machine_status(connection)
        assert status.connection_id == connection.id
        assert status.current_job_id == job.id
        assert session.uploaded_program_id
        assert queue_item.status == "Stopped"
        engine.disconnect_machine(connection)
        sessions.append(session)

    emergency_connection = engine.connect_machine(extra_protocols[0])
    engine.emergency_stop_machine(emergency_connection, "Validation emergency stop")

    validation = engine.validate()
    diagnostics = engine.diagnostics()

    assert validation.valid is True
    assert len(sessions) == 4
    assert diagnostics.execution_plan_statistics["machine_connections"] == 9
    assert diagnostics.execution_plan_statistics["communication_sessions"] == 4
    assert diagnostics.execution_plan_statistics["communication_queue"] == 4
    assert diagnostics.execution_plan_statistics["communication_events"] >= 25
    assert diagnostics.execution_plan_statistics["monitoring_states"] >= 5
    assert diagnostics.execution_plan_statistics["recent_machines"] >= 5
    assert diagnostics.execution_plan_statistics["emergency_stop_events"] == 1
    assert diagnostics.execution_plan_statistics["protocols"] == 9

    assert list(workspace.scene3d.entities()) == []
    assert getattr(workspace.product_manager, "bodies", []) == []
    assert getattr(workspace.product_manager, "features", []) == []
    assert workspace.command_manager.undo_stack == []
    assert workspace.command_manager.redo_stack == []

    with TemporaryDirectory() as directory:
        path = Path(directory) / "machine_communication.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.machine_workspace.load_from_settings()
    restored_engine = restored.manufacturing_engine
    restored_engine.load_from_settings()

    assert len(restored_engine.machine_connections) == 9
    assert len(restored_engine.communication_sessions) == 4
    assert len(restored_engine.communication_queue) == 4
    assert len(restored_engine.machine_monitoring) >= 5
    assert len(restored_engine.communication_events) >= 25
    assert len(restored_engine.recent_machines) >= 5
    assert restored_engine.validate().valid is True
    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []
    assert restored.command_manager.undo_stack == []
    assert restored.command_manager.redo_stack == []


if __name__ == "__main__":
    test_machine_communication_dispatch_monitoring_events_and_persistence()
    print("machine-communication-ok")
