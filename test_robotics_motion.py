from pathlib import Path
from tempfile import TemporaryDirectory

from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_robotics_motion_profiles_trajectories_programs_and_persistence():
    workspace = Workspace("Robotics Motion Project")
    machine_workspace = workspace.machine_workspace.initialize()
    engine = workspace.manufacturing_engine.initialize()

    robot_machine = machine_workspace.register_machine(
        "KS Robot Cell",
        "Robot",
        manufacturer="Kinematics Studio",
        model="KS-6R",
        firmware="Robot Controller",
        work_envelope={"x": 1600, "y": 1600, "z": 1600},
        supported_materials=["Payload Fixture"],
        supported_tool_systems=["Gripper", "Welder", "Dispenser"],
        supported_file_formats=["RAPID", "KRL", "SCRIPT"],
    )
    tools = machine_workspace.create_tool_library("Robot End Effectors")
    gripper = machine_workspace.register_tool(
        tools,
        "Parallel Gripper",
        "Robot End Effector",
        diameter=80.0,
        length=180.0,
        material="Aluminum",
        operating_limits={"payload": 8.0},
    )
    payload = machine_workspace.register_material(
        "Payload Fixture",
        "Custom Materials",
        density=1.0,
        compatible_machines=[robot_machine],
        default_process_metadata={"payload": 5.0, "fixture": "tray"},
    )
    machine_profile = machine_workspace.create_profile(robot_machine, "Robot Cell Profile", tool_library=tools)

    six_axis = engine.create_robot_profile(
        "KS 6R Arm",
        "6-axis",
        machine_profile=machine_profile,
        payload=10.0,
        reach=1600.0,
        tcp={"x": 0, "y": 0, "z": 180, "rx": 0, "ry": 0, "rz": 0},
        tool_frame={"x": 0, "y": 0, "z": 180, "rx": 0, "ry": 0, "rz": 0},
    )
    scara = engine.create_robot_profile("KS SCARA", "SCARA", machine_profile=machine_profile, payload=4.0, reach=700.0)
    delta = engine.create_robot_profile("KS Delta", "Delta", machine_profile=machine_profile, payload=2.0, reach=500.0)
    cartesian = engine.create_robot_profile("KS Cartesian", "Cartesian", machine_profile=machine_profile, payload=20.0, reach=1200.0)
    custom = engine.create_robot_profile("KS Custom Robot", "Custom", machine_profile=machine_profile, payload=15.0, reach=1000.0)

    assert len(six_axis.joint_limits) == 6
    assert len(scara.joint_limits) == 4
    assert len(delta.joint_limits) == 3
    assert len(cartesian.joint_limits) == 3
    assert len(custom.joint_limits) == 6

    job = engine.create_robot_job(
        "Robot Pick Inspect Place",
        six_axis,
        process="Pick & Place",
        machine_profile=machine_profile,
        material=payload,
        description="Pick, inspect and place robot program.",
    )
    machine_frame = engine.define_robot_frame(
        job,
        "Machine Frame",
        "Machine Coordinate System",
        origin={"x": 0, "y": 0, "z": 0, "rx": 0, "ry": 0, "rz": 0},
    )
    user_frame = engine.define_robot_frame(
        job,
        "Tray User Frame",
        "User Frame",
        origin={"x": 250, "y": 120, "z": 40, "rx": 0, "ry": 0, "rz": 90},
        parent_frame=machine_frame,
    )
    tool_frame = engine.define_robot_frame(
        job,
        "Gripper TCP",
        "Tool Frame",
        origin={"x": 0, "y": 0, "z": 180, "rx": 0, "ry": 0, "rz": 0},
        tool_id=gripper.id,
    )
    work_offset = engine.define_robot_frame(
        job,
        "Pallet Offset",
        "Work Offset",
        origin={"x": 25, "y": 30, "z": 0, "rx": 0, "ry": 0, "rz": 0},
        parent_frame=user_frame,
    )

    motions = [
        engine.plan_robot_motion(job, "Approach", {"x": 300, "y": 120, "z": 300, "rx": 180, "ry": 0, "rz": 90}, [0, -20, 40, 0, 60, 0], user_frame, 250, 600, blend_radius=20),
        engine.plan_robot_motion(job, "Joint", {"x": 320, "y": 120, "z": 220, "rx": 180, "ry": 0, "rz": 90}, [5, -15, 35, 0, 55, 5], user_frame, 220, 500, process={"pick_place": True}),
        engine.plan_robot_motion(job, "Linear", {"x": 420, "y": 180, "z": 220, "rx": 180, "ry": 0, "rz": 90}, [10, -10, 30, 0, 50, 10], user_frame, 180, 450, blend_radius=5),
        engine.plan_robot_motion(job, "Circular", {"x": 500, "y": 220, "z": 240, "rx": 180, "ry": 0, "rz": 90}, [15, -5, 25, 5, 45, 15], user_frame, 160, 400, metadata={"center": {"x": 460, "y": 200, "z": 230}}),
        engine.plan_robot_motion(job, "Spline", {"x": 600, "y": 260, "z": 260, "rx": 180, "ry": 0, "rz": 90}, [20, 0, 20, 10, 40, 20], user_frame, 140, 350, blend_radius=10),
        engine.plan_robot_motion(job, "Retract", {"x": 600, "y": 260, "z": 420, "rx": 180, "ry": 0, "rz": 90}, [20, 0, 10, 0, 35, 0], work_offset, 260, 600),
        engine.plan_robot_motion(job, "Safe", {"x": 150, "y": 80, "z": 500, "rx": 180, "ry": 0, "rz": 0}, [0, -30, 20, 0, 30, 0], machine_frame, 300, 700),
    ]

    assert all(not motion.metadata["validation_errors"] for motion in motions)
    assert motions[0].metadata["inverse_kinematics_foundation"]["reachable"] is True
    assert motions[0].metadata["forward_kinematics"]["within_limits"] is True

    trajectory = engine.generate_robot_trajectory(job)
    generic = engine.generate_robot_program(job, "Generic Robot Program")
    rapid = engine.generate_robot_program(job, "ABB RAPID foundation")
    krl = engine.generate_robot_program(job, "KUKA KRL foundation")
    fanuc = engine.generate_robot_program(job, "Fanuc TP metadata")
    urscript = engine.generate_robot_program(job, "URScript foundation")
    inform = engine.generate_robot_program(job, "Yaskawa INFORM metadata")

    assert trajectory.valid is True
    assert len(trajectory.waypoints) == 7
    assert len(trajectory.joint_path) == 7
    assert trajectory.linear_path
    assert trajectory.circular_path
    assert trajectory.estimated_cycle_time > 0
    assert generic.valid is True and "PROGRAM" in generic.content
    assert rapid.valid is True and "MODULE" in rapid.content and "Move" in rapid.content
    assert krl.valid is True and "DEF" in krl.content
    assert fanuc.valid is True and "/PROG" in fanuc.content
    assert urscript.valid is True and "def robot_pick_inspect_place" in urscript.content
    assert inform.valid is True and "/JOB" in inform.content
    assert tool_frame.metadata["tool_id"] == gripper.id

    validation = engine.validate()
    diagnostics = engine.diagnostics()

    assert validation.valid is True
    assert diagnostics.execution_plan_statistics["robot_profiles"] == 5
    assert diagnostics.execution_plan_statistics["robot_frames"] >= 6
    assert diagnostics.execution_plan_statistics["robot_motions"] == 7
    assert diagnostics.execution_plan_statistics["robot_trajectories"] == 1
    assert diagnostics.execution_plan_statistics["robot_programs"] == 6
    assert diagnostics.execution_plan_statistics["robot_waypoints"] == 7
    assert diagnostics.execution_plan_statistics["robot_estimated_cycle_time"] > 0
    assert diagnostics.execution_plan_statistics["robot_program_lines"] > 0
    assert diagnostics.execution_plan_statistics["robot_utilization"] > 0

    assert list(workspace.scene3d.entities()) == []
    assert getattr(workspace.product_manager, "bodies", []) == []
    assert getattr(workspace.product_manager, "features", []) == []
    assert workspace.command_manager.undo_stack == []
    assert workspace.command_manager.redo_stack == []

    with TemporaryDirectory() as directory:
        path = Path(directory) / "robotics_motion.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.machine_workspace.load_from_settings()
    restored_engine = restored.manufacturing_engine
    restored_engine.load_from_settings()

    assert len(restored_engine.robot_profiles) == 5
    assert len(restored_engine.robot_frames) >= 6
    assert len(restored_engine.robot_motions) == 7
    assert len(restored_engine.robot_trajectories) == 1
    assert len(restored_engine.robot_programs) == 6
    assert restored_engine.validate().valid is True
    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []
    assert restored.command_manager.undo_stack == []
    assert restored.command_manager.redo_stack == []


if __name__ == "__main__":
    test_robotics_motion_profiles_trajectories_programs_and_persistence()
    print("robotics-motion-ok")
