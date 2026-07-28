from pathlib import Path
from tempfile import TemporaryDirectory

from engine.commands.structural_simulation_command import RunMotionStudyCommand
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_motion_mechanism_simulation_foundation_solver_reports_animation_and_persistence():
    workspace = Workspace("Motion Simulation Project")
    simulation = workspace.simulation_workspace.initialize()

    project = simulation.create_project("Motion Project", "Release 1.8 Batch H")
    study = simulation.create_motion_study(
        project,
        "Door Hinge Motion Study",
        "Mechanism Study",
        target_geometry=[{"assembly_id": "cabinet-door"}],
        solver_settings={"motion_accuracy": "kinematic"},
        visualization_settings={"motion_trails": True, "joint_visualization": True},
    )

    ground = simulation.create_motion_rigid_body(
        study,
        "Cabinet Frame",
        geometry_references=[{"body_id": "cabinet-frame"}],
        mass=12.0,
        center_of_gravity={"x": 0.0, "y": 0.0, "z": 0.0},
        inertia_metadata={"ixx": 1.0, "iyy": 1.2, "izz": 1.4},
        reference_frame={"x": 0.0, "y": 0.0, "z": 0.0, "rotation": 0.0},
        local_coordinate_systems=[{"name": "hinge-axis", "z": 1.0}],
        is_ground=True,
        group="cabinet",
    )
    door = simulation.create_motion_rigid_body(
        study,
        "Cabinet Door",
        geometry_references=[{"body_id": "cabinet-door"}],
        mass=4.0,
        center_of_gravity={"x": 0.45, "y": 0.0, "z": 0.75},
        inertia_metadata={"ixx": 0.4, "iyy": 0.9, "izz": 0.8},
        reference_frame={"x": 0.7, "y": 0.0, "z": 0.0, "rotation": 0.0},
        local_coordinate_systems=[{"name": "door-local"}],
        group="cabinet",
    )
    handle = simulation.create_motion_rigid_body(
        study,
        "Door Handle",
        geometry_references=[{"body_id": "door-handle"}],
        mass=0.3,
        reference_frame={"x": 0.9, "y": 0.0, "z": 0.6, "rotation": 0.0},
        group="cabinet",
    )
    hinge = simulation.create_motion_joint(
        study,
        "Main Hinge",
        "Revolute Joint",
        parent_body=ground,
        child_body=door,
        axis={"x": 0.0, "y": 0.0, "z": 1.0},
        origin={"x": 0.0, "y": 0.0, "z": 0.0},
        limits={"min": 0.0, "max": 1.5708},
        constraint_metadata={"radius": 0.7, "initial_position": 0.0},
    )
    fixed_handle = simulation.create_motion_joint(
        study,
        "Handle Attachment",
        "Fixed Joint",
        parent_body=door,
        child_body=handle,
        axis={"x": 1.0, "y": 0.0, "z": 0.0},
    )
    driver = simulation.create_motion_driver(
        study,
        "Open Door Motor",
        "Angular Motor",
        target=hinge,
        function={"type": "linear", "rate": 1.5708, "offset": 0.0},
        profile={"duration": 1.0},
        synchronization_group="door-open",
    )
    mechanism = simulation.create_motion_mechanism(
        study,
        "Door Hinge Mechanism",
        "Door Hinge",
        body_ids=[ground, door, handle],
        joint_ids=[hinge, fixed_handle],
        driver_ids=[driver],
        metadata={"mechanism_library": True},
    )
    animation = simulation.set_motion_animation(
        study,
        duration=1.0,
        time_step=0.25,
        loop=True,
        playback_speed=1.5,
        keyframes=[{"time": 0.0, "state": "closed"}, {"time": 1.0, "state": "open"}],
        camera_tracking_metadata={"target_body_id": door.id},
    )

    assert ground.is_ground is True
    assert hinge.joint_type == "Revolute Joint"
    assert mechanism.mechanism_type == "Door Hinge"
    assert animation.loop is True

    command = RunMotionStudyCommand(workspace, study)
    workspace.command_manager.execute(command)

    result = simulation.results[-1]
    report = result.reports[0]
    assert study.status == "Solved"
    assert result.result_type == "Motion Mechanism Result"
    assert result.scalars["body_count"] == 3
    assert result.scalars["joint_count"] == 2
    assert result.scalars["maximum_angular_displacement"] > 0.0
    assert "joint_states" in result.vectors
    assert "motion_history" in result.vectors
    assert "motion_trails" in result.vectors
    assert result.statistics["animation"]["loop"] is True
    assert result.statistics["timeline_data"]["duration"] == 1.0
    assert report["mechanism_summary"][0]["mechanism_type"] == "Door Hinge"
    assert simulation.visualizations[-1].display_settings["motion_trails"] is True
    assert simulation.motion_execution_history[-1].status == "Completed"

    workspace.command_manager.undo()
    assert workspace.simulation_workspace.results == []
    workspace.command_manager.redo()
    assert len(workspace.simulation_workspace.results) == 1

    with TemporaryDirectory() as directory:
        path = Path(directory) / "motion_simulation.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.simulation_workspace.load_from_settings()
    restored_simulation = restored.simulation_workspace
    assert len(restored_simulation.motion_rigid_bodies) == 3
    assert len(restored_simulation.motion_joints) == 2
    assert len(restored_simulation.motion_drivers) == 1
    assert len(restored_simulation.motion_mechanisms) == 1
    assert len(restored_simulation.motion_animation_settings) == 1
    assert len(restored_simulation.motion_execution_history) == 1
    assert len(restored_simulation.results) == 1
    assert restored_simulation.diagnostics().to_dict()["statistics"]["motion_solved_studies"] == 1

    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []


if __name__ == "__main__":
    test_motion_mechanism_simulation_foundation_solver_reports_animation_and_persistence()
    print("motion-mechanism-simulation-foundation-ok")
