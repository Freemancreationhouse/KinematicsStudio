from pathlib import Path
from tempfile import TemporaryDirectory

from engine.ai import AIEngine, ManufacturingWorkflowPlan
from engine.ai.manufacturing_assistant import AI_MANUFACTURING_ASSISTANT_SETTINGS_KEY, AIManufacturingAssistant
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def _build_ready_cnc_workspace():
    workspace = Workspace("AI Manufacturing Workspace")
    machine_workspace = workspace.machine_workspace.initialize()
    manufacturing_engine = workspace.manufacturing_engine.initialize()

    tools = machine_workspace.create_tool_library("AI Manufacturing Tools")
    machine = machine_workspace.register_machine(
        "AI CNC",
        "CNC Mill",
        firmware="GRBL",
        work_envelope={"x": 300, "y": 200, "z": 100},
        supported_materials=["Aluminum"],
        supported_tool_systems=["End Mill"],
        supported_file_formats=["GCODE"],
    )
    tool = machine_workspace.register_tool(tools, "6mm End Mill", "End Mill", diameter=6.0, length=45.0)
    material = machine_workspace.register_material("Aluminum", "Aluminium", compatible_machines=[machine])
    profile = machine_workspace.create_profile(machine, "AI CNC Profile", tool_library=tools)

    job = manufacturing_engine.create_job("AI CNC Job", machine_profile=profile, material=material)
    manufacturing_engine.create_stock(job, dimensions={"x": 50, "y": 35, "z": 8}, material=material)
    manufacturing_engine.create_fixture(job, fixture_type="Vise")
    coordinate = manufacturing_engine.create_coordinate_system(job, "AI WCS", "Work Coordinate System", activate=True)
    manufacturing_engine.create_work_offset(job, "G54", reference_system=coordinate["id"])
    manufacturing_engine.create_operation(
        job,
        "2D Profile",
        required_tool=tool,
        required_material=material,
        cut_geometry={"points": [{"x": 0, "y": 0}, {"x": 50, "y": 0}, {"x": 50, "y": 35}, {"x": 0, "y": 35}, {"x": 0, "y": 0}]},
    )
    manufacturing_engine.plan_cam_job(job)
    manufacturing_engine.generate_toolpaths(job)
    manufacturing_engine.generate_gcode(job, "GRBL", "AI_CNC")
    simulation = manufacturing_engine.create_simulation_job(job)
    manufacturing_engine.run_simulation(simulation)
    manufacturing_engine.check_simulation_collisions(simulation)
    manufacturing_engine.verify_simulation(simulation)
    manufacturing_engine.generate_simulation_report(simulation)
    connection = manufacturing_engine.create_machine_connection(profile, "GRBL", "Serial", {"port": "COM9", "baud": 115200})
    return workspace, job, connection


def test_ai_manufacturing_assistant_orchestrates_existing_manufacturing_systems():
    workspace, job, connection = _build_ready_cnc_workspace()
    ai = AIEngine()
    assistant = ai.initialize_manufacturing_assistant(workspace)

    assert isinstance(assistant, AIManufacturingAssistant)
    session = assistant.start_session(workspace, {"preferred_units": "mm"})

    prompts = {
        "Machine this aluminum part on the CNC and estimate time": "CNC",
        "Print this part with FDM": "FDM",
        "Prepare this for SLA resin": "SLA",
        "Laser cut this panel": "Laser",
        "Plasma cut this bracket": "Plasma",
        "Waterjet this plate": "Waterjet",
        "Plan robot pick and place": "Robotics",
    }
    for prompt, process in prompts.items():
        intent = assistant.interpret_request(prompt, workspace, session)
        assert intent.process == process
        assert intent.workflow
        assert intent.confidence >= 0.9

    plan = ai.plan_manufacturing_workflow("Run my CNC job in production", workspace, session, job)
    assert isinstance(plan, ManufacturingWorkflowPlan)
    assert plan.process == "CNC"
    assert plan.job_id == job.id
    assert plan.existing_systems == ["Manufacturing Engine", "CAM Planner", "Simulation Engine", "Communication Engine"]
    assert plan.readiness["generated_program"] is True
    assert plan.readiness["simulation_report"] is True
    assert plan.readiness["communication_connection"] is True
    assert plan.validation["valid"] is True

    validation = assistant.validate_workflow(plan, workspace)
    assert validation["valid"] is True

    recommendations = assistant.recommend_optimizations(plan, workspace, job)
    assert recommendations
    assert all(item.source == "AI Manufacturing Assistant" for item in recommendations)

    pending = ai.orchestrate_manufacturing_execution(plan, workspace, connection, approved=False)
    assert pending.status == "Pending Approval"
    assert not workspace.manufacturing_engine.communication_sessions

    approved = ai.orchestrate_manufacturing_execution(plan, workspace, connection, approved=True, approved_by="operator")
    assert approved.status == "Execution Started"
    assert approved.execution_session_id
    assert workspace.manufacturing_engine.communication_sessions[-1].state == "Running"
    assert workspace.manufacturing_engine.communication_queue[-1].status in {"Uploaded", "Running"}

    response = ai.advise_manufacturing("Can this be machined faster on CNC?", workspace, session, job)
    assert response["explanation"]["geometry_modified"] is False
    assert response["explanation"]["meshentity_modified"] is False
    assert response["workflow_plan"]["existing_systems"][0] == "Manufacturing Engine"

    diagnostics = ai.diagnostics()["manufacturing_assistant"]
    assert diagnostics["intents"] >= 9
    assert diagnostics["workflow_plans"] >= 2
    assert diagnostics["recommendations"] >= 6
    assert diagnostics["validation_decisions"] >= 2
    assert diagnostics["simulation_requests"] >= 2
    assert diagnostics["execution_requests"] == 1
    assert diagnostics["approval_history"] == 2

    assert AI_MANUFACTURING_ASSISTANT_SETTINGS_KEY in workspace.project_settings
    assert list(workspace.scene3d.entities()) == []
    assert getattr(workspace.product_manager, "bodies", []) == []
    assert getattr(workspace.product_manager, "features", []) == []
    assert workspace.command_manager.undo_stack == []
    assert workspace.command_manager.redo_stack == []

    with TemporaryDirectory() as directory:
        path = Path(directory) / "ai_manufacturing_assistant.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.machine_workspace.load_from_settings()
    restored.manufacturing_engine.load_from_settings()
    restored_assistant = AIManufacturingAssistant(ai)
    restored_assistant.load_from_settings(restored)

    assert restored_assistant.initialized is True
    assert len(restored_assistant.intents) >= 9
    assert len(restored_assistant.workflow_plans) >= 2
    assert len(restored_assistant.recommendations) >= 6
    assert len(restored_assistant.approvals) == 2
    assert restored_assistant.approvals[-1].status == "Execution Started"
    assert restored.manufacturing_engine.validate().valid is True
    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []
    assert restored.command_manager.undo_stack == []
    assert restored.command_manager.redo_stack == []


if __name__ == "__main__":
    test_ai_manufacturing_assistant_orchestrates_existing_manufacturing_systems()
    print("ai-manufacturing-assistant-ok")
