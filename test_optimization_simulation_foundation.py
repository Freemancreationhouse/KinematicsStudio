from pathlib import Path
from tempfile import TemporaryDirectory

from engine.commands.structural_simulation_command import RunOptimizationStudyCommand
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_optimization_simulation_foundation_reuses_studies_and_preserves_workspace():
    workspace = Workspace("Optimization Simulation Project")
    simulation = workspace.simulation_workspace.initialize()

    project = simulation.create_project("Optimization Project", "Release 1.8 Batch I")
    structural = simulation.create_structural_study(project, "Structural Context")
    thermal = simulation.create_thermal_study(project, "Thermal Context")
    daylight = simulation.create_daylight_study(project, "Daylight Context")
    energy = simulation.create_energy_study(project, "Energy Context")
    cfd = simulation.create_cfd_study(project, "CFD Context")
    motion = simulation.create_motion_study(project, "Motion Context")
    simulation.create_result(structural, "Structural Context Result", scalars={"min_safety_factor": 2.2, "max_displacement": 0.004})
    simulation.create_result(thermal, "Thermal Context Result", scalars={"maximum_temperature": 31.0})
    simulation.create_result(daylight, "Daylight Context Result", scalars={"average_lux": 420.0})
    simulation.create_result(energy, "Energy Context Result", scalars={"annual_energy_use": 9800.0, "operational_carbon": 760.0})
    simulation.create_result(cfd, "CFD Context Result", scalars={"average_velocity": 0.9, "air_change_rate": 3.5})
    simulation.create_result(motion, "Motion Context Result", scalars={"maximum_travel": 1.2})

    study = simulation.create_optimization_study(
        project,
        "Facade Performance Optimization",
        "Multi-Objective Optimization",
        target_geometry=[{"body_id": "facade-panel"}, {"parameter_id": "window_to_wall_ratio"}],
        solver_settings={"strategy": "Grid Search", "max_iterations": 9},
        visualization_settings={"optimization_dashboard": True, "pareto_visualization": True},
        metadata={"purpose": "balance energy, daylight, cost, and constructability"},
    )
    width = simulation.create_optimization_design_variable(
        study,
        "Panel Width",
        "Dimension",
        reference={"parameter": "panel_width"},
        lower_bound=0.6,
        upper_bound=1.2,
        default_value=0.9,
        values=[0.6, 0.9, 1.2],
        group="envelope",
    )
    depth = simulation.create_optimization_design_variable(
        study,
        "Shade Depth",
        "Dimension",
        reference={"parameter": "shade_depth"},
        lower_bound=0.2,
        upper_bound=0.8,
        default_value=0.5,
        values=[0.2, 0.5, 0.8],
        group="solar_control",
        dependencies=[{"depends_on": width.id}],
    )
    simulation.create_optimization_constraint(study, "Annual Energy Limit", "Energy Constraint", "energy_use", "<=", 12000.0, priority=2.0)
    simulation.create_optimization_constraint(study, "Displacement Limit", "Structural Constraint", "displacement", "<=", 0.05, priority=3.0)
    simulation.create_optimization_constraint(study, "Minimum Airflow", "CFD Constraint", "airflow", ">=", 0.5, priority=1.0)
    simulation.create_optimization_objective(study, "Minimize Energy", "Minimum Energy Use", "energy_use", "minimize", weight=1.5)
    simulation.create_optimization_objective(study, "Maximize Daylight", "Maximum Daylight", "daylight", "maximize", weight=0.4)
    simulation.create_optimization_objective(study, "Minimize Carbon", "Minimum Carbon", "carbon", "minimize", weight=0.8)
    simulation.create_optimization_objective(study, "Minimize Cost", "Minimum Cost", "cost", "minimize", weight=0.3)
    simulation.create_optimization_ai_hint(
        study,
        suggestions=[{"action": "compare_top_candidates", "reason": "Multiple feasible envelope options are available."}],
        explanations=[{"topic": "strategy", "text": "Grid search was selected for deterministic design-space coverage."}],
        recommendation_metadata={"approval_required_before_commands": True},
    )

    command = RunOptimizationStudyCommand(workspace, study)
    workspace.command_manager.execute(command)

    result = simulation.results[-1]
    report = result.reports[0]
    diagnostics = result.metadata["diagnostics"]
    assert study.status == "Solved"
    assert result.result_type == "Optimization Simulation Result"
    assert result.scalars["candidate_count"] == 9
    assert result.scalars["feasible_count"] >= 1
    assert result.scalars["objective_count"] == 4
    assert result.scalars["constraint_count"] == 3
    assert "optimization_history" in result.vectors
    assert "pareto_front_metadata" in result.vectors
    assert "candidate_ranking" in result.vectors
    assert result.statistics["best_design"]["variables"]
    assert result.statistics["simulation_summaries"]
    assert result.statistics["reuse_summary"]["structural"] is True
    assert result.statistics["reuse_summary"]["thermal"] is True
    assert result.statistics["reuse_summary"]["daylight"] is True
    assert result.statistics["reuse_summary"]["energy"] is True
    assert result.statistics["reuse_summary"]["cfd"] is True
    assert result.statistics["reuse_summary"]["motion"] is True
    assert result.statistics["ai_integration"]["hint_count"] == 1
    assert diagnostics["geometry_edited"] is False
    assert simulation.visualizations[-1].display_settings["optimization_dashboard"] is True
    assert simulation.optimization_execution_history[-1].status == "Completed"
    assert report["best_solution"]["score"] == result.statistics["best_design"]["score"]

    workspace.command_manager.undo()
    assert len(workspace.simulation_workspace.results) == 6
    workspace.command_manager.redo()
    assert len(workspace.simulation_workspace.results) == 7

    with TemporaryDirectory() as directory:
        path = Path(directory) / "optimization_simulation.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.simulation_workspace.load_from_settings()
    restored_simulation = restored.simulation_workspace
    assert len(restored_simulation.optimization_design_variables) == 2
    assert len(restored_simulation.optimization_constraints) == 3
    assert len(restored_simulation.optimization_objectives) == 4
    assert len(restored_simulation.optimization_ai_hints) == 1
    assert len(restored_simulation.optimization_execution_history) == 1
    assert restored_simulation.diagnostics().to_dict()["statistics"]["optimization_solved_studies"] == 1

    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []


if __name__ == "__main__":
    test_optimization_simulation_foundation_reuses_studies_and_preserves_workspace()
    print("optimization-simulation-foundation-ok")
