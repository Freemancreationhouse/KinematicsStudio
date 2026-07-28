from pathlib import Path
from tempfile import TemporaryDirectory

from engine.ai import AIEngine
from engine.simulation import ProductionSimulationRuntime, SimulationReleaseCertification
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def _build_release_18_workspace():
    workspace = Workspace("Production Simulation Runtime Workspace")
    simulation = workspace.simulation_workspace.initialize()
    project = simulation.create_project("Production Simulation Project", "Release 1.8 Batch K")

    structural = simulation.create_structural_study(project, "Structural Runtime Study", target_geometry=[{"body_id": "bracket"}])
    simulation.create_building_structural_study(project, "Building Runtime Study", "Office Tower", storeys=[{"name": "L1", "height": 3.2}], target_geometry=[{"building_id": "office"}])
    thermal = simulation.create_thermal_study(project, "Thermal Runtime Study", target_geometry=[{"body_id": "enclosure"}])
    daylight = simulation.create_daylight_study(project, "Daylight Runtime Study", target_geometry=[{"zone_id": "atrium"}])
    energy = simulation.create_energy_study(project, "Energy Runtime Study", target_geometry=[{"building_id": "office"}])
    cfd = simulation.create_cfd_study(project, "CFD Runtime Study", target_geometry=[{"room_id": "conference"}])
    motion = simulation.create_motion_study(project, "Motion Runtime Study", target_geometry=[{"assembly_id": "hinge"}])
    optimization = simulation.create_optimization_study(
        project,
        "Runtime Optimization Study",
        target_geometry=[{"parameter_id": "panel_depth"}],
        solver_settings={"strategy": "Grid Search", "max_iterations": 3},
        visualization_settings={"optimization_dashboard": True},
    )
    simulation.create_optimization_design_variable(
        optimization,
        "Panel Depth",
        "Dimension",
        reference={"parameter": "panel_depth"},
        lower_bound=0.2,
        upper_bound=0.6,
        default_value=0.4,
        values=[0.2, 0.4, 0.6],
    )
    simulation.create_optimization_constraint(optimization, "Energy Cap", "Energy Constraint", "energy_use", "<=", 12000.0)
    simulation.create_optimization_objective(optimization, "Minimum Energy", "Minimum Energy Use", "energy_use", "minimize")

    simulation.create_result(structural, "Structural Runtime Result", scalars={"min_safety_factor": 2.1, "max_displacement": 0.01})
    simulation.create_result(thermal, "Thermal Runtime Result", scalars={"maximum_temperature": 30.0})
    simulation.create_result(daylight, "Daylight Runtime Result", scalars={"average_lux": 430.0})
    simulation.create_result(energy, "Energy Runtime Result", scalars={"annual_energy_use": 9100.0, "operational_carbon": 680.0})
    simulation.create_result(cfd, "CFD Runtime Result", scalars={"average_velocity": 0.75, "air_change_rate": 3.0})
    simulation.create_result(motion, "Motion Runtime Result", scalars={"maximum_travel": 1.0})
    return workspace, optimization


def test_production_simulation_runtime_certifies_release_18_without_geometry_changes():
    workspace, optimization = _build_release_18_workspace()
    simulation = workspace.simulation_workspace
    runtime = simulation.production_runtime.initialize()
    ai = AIEngine()
    ai.initialize_engineering_simulation_assistant(workspace)

    assert isinstance(runtime, ProductionSimulationRuntime)
    assert runtime.state.initialized is True

    job = runtime.queue_study(optimization, priority=9, metadata={"batch": "1.8K"})
    assert job.status == "Queued"
    validation = runtime.validate_job(job)
    assert validation["valid"] is True
    assert validation["solver_validation"] is True

    execution = runtime.execute_next()
    completed_job = execution["job"]
    result = execution["result"]
    certification = execution["certification"]
    assert completed_job.status == "Completed"
    assert result.result_type == "Optimization Simulation Result"
    assert certification.verification_status == "Verified"
    assert certification.validation_status == "Valid"
    assert certification.quality_score == 1.0

    dashboard = runtime.dashboard()
    assert dashboard["runtime_dashboard"] is True
    assert dashboard["execution_status"]["Completed"] == 1
    assert dashboard["certification_badges"]
    assert dashboard["solver_status"]
    assert completed_job.id in dashboard["progress_overlays"]

    report = runtime.production_report()
    assert report.simulation_summary["studies"] >= 8
    assert report.certification_summary["certifications"] >= 1
    assert report.performance_summary["executions"] == 1
    assert report.validation_results["valid"] is True

    recovery = runtime.recover()
    assert recovery.status == "Recovered"
    assert recovery.consistency_validation["valid"] is True

    release = runtime.release_certification(ai)
    assert isinstance(release, SimulationReleaseCertification)
    assert release.release == "1.8"
    assert release.status == "Certified"
    assert release.integrated_platform_certification["certified"] is True
    assert release.integrated_platform_certification["geometry_ownership_unchanged"] is True
    assert release.module_certifications["Structural certification"]["certified"] is True
    assert release.module_certifications["Building Structural certification"]["certified"] is True
    assert release.module_certifications["Thermal certification"]["certified"] is True
    assert release.module_certifications["Daylighting certification"]["certified"] is True
    assert release.module_certifications["Energy certification"]["certified"] is True
    assert release.module_certifications["CFD certification"]["certified"] is True
    assert release.module_certifications["Motion certification"]["certified"] is True
    assert release.module_certifications["Optimization certification"]["certified"] is True
    assert release.module_certifications["AI Assistant certification"]["certified"] is True

    diagnostics = simulation.diagnostics().to_dict()["statistics"]
    assert diagnostics["production_runtime_initialized"] is True
    assert diagnostics["production_runtime_jobs"] == 1
    assert diagnostics["production_runtime_certifications"] >= 1
    assert diagnostics["release_certifications"] == 1

    assert list(workspace.scene3d.entities()) == []
    assert getattr(workspace.product_manager, "bodies", []) == []
    assert getattr(workspace.product_manager, "features", []) == []

    with TemporaryDirectory() as directory:
        path = Path(directory) / "production_simulation_runtime.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.simulation_workspace.load_from_settings()
    restored_runtime = restored.simulation_workspace.production_runtime
    assert restored_runtime.state.initialized is True
    assert len(restored_runtime.jobs) == 1
    assert len(restored_runtime.sessions) == 1
    assert len(restored_runtime.certifications) >= 1
    assert len(restored_runtime.performance_history) == 1
    assert len(restored_runtime.recovery_history) == 1
    assert len(restored_runtime.production_reports) == 1
    assert len(restored_runtime.release_certifications) == 1
    assert restored_runtime.release_certifications[-1].status == "Certified"
    assert restored.simulation_workspace.validate()["valid"] is True
    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []


if __name__ == "__main__":
    test_production_simulation_runtime_certifies_release_18_without_geometry_changes()
    print("production-simulation-runtime-ok")
