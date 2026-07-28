from pathlib import Path
from tempfile import TemporaryDirectory

from engine.ai import AIEngine
from engine.machine import ProductionExecutionPipeline, ProductionRuntimeReport
from engine.storage.project import ProjectSerializer
from test_ai_manufacturing_assistant import _build_ready_cnc_workspace


def test_production_manufacturing_runtime_pipeline_health_recovery_and_persistence():
    workspace, job, connection = _build_ready_cnc_workspace()
    ai = AIEngine()
    ai.initialize_manufacturing_assistant(workspace)
    session = ai.manufacturing_assistant.start_session(workspace)
    ai.plan_manufacturing_workflow("Run my CNC job in production", workspace, session, job)

    engine = workspace.manufacturing_engine
    state = engine.initialize_production_runtime()
    assert state.initialized is True
    assert state.status == "Ready"
    assert state.metadata["runtime_owner"] == "ManufacturingEngine"

    health = engine.production_runtime_health()
    assert health.status == "Healthy"
    assert health.subsystem_status["Manufacturing Engine"] is True
    assert health.subsystem_status["CAM"] is True
    assert health.subsystem_status["Simulation"] is True
    assert health.subsystem_status["Machine Communication"] is True
    assert health.subsystem_status["AI Manufacturing Assistant"] is True

    optimization = engine.optimize_production_runtime()
    assert optimization["execution_prioritization"]["simulation_ready_jobs"] >= 1
    assert optimization["execution_prioritization"]["program_ready_jobs"] >= 1
    assert optimization["resource_reuse"]["machine_connections"] == 1

    validation = engine.validate_production_runtime(job, require_execution=True)
    assert validation["valid"] is True
    assert validation["job_id"] == job.id

    pending = engine.execute_production_pipeline(job, connection, "CNC production", approved=False)
    assert isinstance(pending, ProductionExecutionPipeline)
    assert pending.status == "Awaiting Approval"
    assert pending.approval_status == "Pending"
    assert pending.report_id

    running = engine.execute_production_pipeline(job, connection, "CNC production", approved=True, approved_by="operator")
    assert running.status == "Running"
    assert running.approval_status == "Approved"
    assert running.communication_session_id
    assert running.monitoring_state_id
    assert running.report_id
    assert engine.communication_sessions[-1].state == "Running"
    assert engine.production_runtime_state.status == "Running"

    report = engine.generate_production_report(running)
    assert isinstance(report, ProductionRuntimeReport)
    assert report.valid is True
    assert report.execution_summary["pipeline_status"] == "Running"
    assert report.simulation_summary["manufacturing_job_id"] == job.id
    assert report.performance_metrics["resource_reuse"]["machine_connections"] == 1

    checkpoint = engine.recover_production_runtime()
    assert checkpoint["queue_items"] >= 1
    assert engine.production_runtime_state.status == "Recovered"

    shutdown = engine.shutdown_production_runtime(graceful=False)
    assert shutdown.status == "Shutdown"

    diagnostics = engine.diagnostics().to_dict()
    assert diagnostics["execution_plan_statistics"]["communication_sessions"] >= 1

    assert len(engine.production_runtime_events) >= 8
    assert len(engine.production_runtime_health_history) >= 3
    assert len(engine.production_execution_pipelines) == 2
    assert len(engine.production_runtime_reports) >= 3
    assert engine.production_recovery_checkpoints
    assert engine.validate().valid is True

    assert list(workspace.scene3d.entities()) == []
    assert getattr(workspace.product_manager, "bodies", []) == []
    assert getattr(workspace.product_manager, "features", []) == []
    assert workspace.command_manager.undo_stack == []
    assert workspace.command_manager.redo_stack == []

    with TemporaryDirectory() as directory:
        path = Path(directory) / "production_runtime.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.machine_workspace.load_from_settings()
    restored_engine = restored.manufacturing_engine
    restored_engine.load_from_settings()

    assert restored_engine.production_runtime_state.status == "Shutdown"
    assert len(restored_engine.production_runtime_events) >= 8
    assert len(restored_engine.production_runtime_health_history) >= 3
    assert len(restored_engine.production_execution_pipelines) == 2
    assert len(restored_engine.production_runtime_reports) >= 3
    assert restored_engine.production_recovery_checkpoints
    assert restored_engine.production_performance_cache
    assert restored_engine.validate().valid is True
    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []
    assert restored.command_manager.undo_stack == []
    assert restored.command_manager.redo_stack == []


if __name__ == "__main__":
    test_production_manufacturing_runtime_pipeline_health_recovery_and_persistence()
    print("production-manufacturing-runtime-ok")
