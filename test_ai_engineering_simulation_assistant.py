from pathlib import Path
from tempfile import TemporaryDirectory

from engine.ai import (
    AIEngine,
    AIEngineeringSimulationAssistant,
    AI_ENGINEERING_SIMULATION_ASSISTANT_SETTINGS_KEY,
    EngineeringSimulationAssistantResponse,
)
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def _build_simulation_workspace():
    workspace = Workspace("AI Engineering Simulation Workspace")
    simulation = workspace.simulation_workspace.initialize()
    project = simulation.create_project("AI Simulation Project", "Release 1.8 Batch J")

    structural = simulation.create_structural_study(
        project,
        "Bracket Structural Study",
        target_geometry=[{"body_id": "bracket"}],
    )
    thermal = simulation.create_thermal_study(
        project,
        "Enclosure Thermal Study",
        target_geometry=[{"body_id": "enclosure"}],
    )
    daylight = simulation.create_daylight_study(
        project,
        "Atrium Daylight Study",
        target_geometry=[{"zone_id": "atrium"}],
    )
    energy = simulation.create_energy_study(
        project,
        "Building Energy Study",
        target_geometry=[{"building_id": "office"}],
    )
    cfd = simulation.create_cfd_study(
        project,
        "Room Airflow Study",
        target_geometry=[{"room_id": "conference"}],
    )
    motion = simulation.create_motion_study(
        project,
        "Hinge Motion Study",
        target_geometry=[{"assembly_id": "door"}],
    )
    optimization = simulation.create_optimization_study(
        project,
        "Envelope Optimization Study",
        target_geometry=[{"parameter_id": "wwr"}],
        solver_settings={"strategy": "Grid Search", "max_iterations": 3},
        visualization_settings={"optimization_dashboard": True},
    )
    simulation.create_optimization_design_variable(
        optimization,
        "Window Ratio",
        "Parameter",
        reference={"parameter": "wwr"},
        lower_bound=0.25,
        upper_bound=0.55,
        default_value=0.4,
        values=[0.25, 0.4, 0.55],
    )
    simulation.create_optimization_constraint(
        optimization,
        "Energy Cap",
        "Energy Constraint",
        "energy_use",
        "<=",
        12000.0,
    )
    simulation.create_optimization_objective(
        optimization,
        "Reduce Energy",
        "Minimum Energy Use",
        "energy_use",
        "minimize",
        weight=1.0,
    )

    simulation.create_result(structural, "Structural Result", scalars={"min_safety_factor": 2.0, "max_displacement": 0.012})
    simulation.create_result(thermal, "Thermal Result", scalars={"maximum_temperature": 32.0, "average_temperature": 26.0})
    simulation.create_result(daylight, "Daylight Result", scalars={"average_lux": 460.0, "uniformity": 0.42})
    simulation.create_result(energy, "Energy Result", scalars={"annual_energy_use": 9400.0, "operational_carbon": 710.0})
    simulation.create_result(cfd, "CFD Result", scalars={"average_velocity": 0.8, "air_change_rate": 3.2})
    simulation.create_result(motion, "Motion Result", scalars={"maximum_travel": 1.1})
    return workspace, optimization


def test_ai_engineering_simulation_assistant_orchestrates_existing_simulation_platform():
    workspace, optimization = _build_simulation_workspace()
    ai = AIEngine()
    assistant = ai.initialize_engineering_simulation_assistant(workspace)

    assert isinstance(assistant, AIEngineeringSimulationAssistant)
    session = assistant.start_session(workspace, {"preferred_units": "SI", "explanation_depth": "engineering"})

    recommendations = ai.recommend_simulation_studies(
        "Prepare a complete energy, daylight, airflow and optimization simulation package",
        workspace,
        session,
    )
    recommended_types = {item.study_type for item in recommendations}
    assert {"Energy", "Daylight", "CFD", "Optimization"}.issubset(recommended_types)
    assert all(item.confidence >= 0.86 for item in recommendations)

    guidance = ai.configure_engineering_simulation("Review optimization setup", workspace, session, optimization)
    assert guidance[0].study_type == "Optimization"
    assert any("Variables" in item or "variables" in item for item in guidance[0].boundary_conditions)
    assert guidance[0].validation_messages

    findings = ai.review_engineering_simulation_setup(workspace, session, optimization)
    assert findings
    assert all(item.study_id in {"", optimization.id} for item in findings)

    interpretations = ai.interpret_engineering_simulation_results(workspace, session)
    interpreted_types = {item.study_type for item in interpretations}
    assert {"Static Structural", "Thermal", "Daylight", "Energy", "CFD", "Motion"}.issubset(interpreted_types)
    assert any(item.recommendations for item in interpretations)

    response = ai.advise_engineering_simulation(
        "Explain the multi-study package and recommend what to run next",
        workspace,
        session,
        optimization,
    )
    assert isinstance(response, EngineeringSimulationAssistantResponse)
    payload = response.to_dict()
    assert payload["multi_simulation_insight"]["involved_study_types"]
    assert payload["report"]["executive_summary"]
    assert payload["diagnostics"]["planning_requests"] >= 1
    assert payload["diagnostics"]["knowledge_items"] >= 4

    pending = ai.execute_engineering_simulation_study(workspace, optimization, approved=False)
    assert pending["status"] == "Pending Approval"
    before_results = len(workspace.simulation_workspace.results)
    executed = ai.execute_engineering_simulation_study(workspace, optimization, approved=True, approved_by="engineer")
    assert executed["status"] == "Executed"
    assert executed["command_routed"] is True
    assert len(workspace.simulation_workspace.results) == before_results + 1
    assert workspace.command_manager.undo_stack

    diagnostics = ai.diagnostics()["engineering_simulation_assistant"]
    assert diagnostics["recommendations"] >= len(recommendations)
    assert diagnostics["configuration_guidance"] >= 1
    assert diagnostics["review_findings"] >= 1
    assert diagnostics["interpretations"] >= len(interpretations)
    assert diagnostics["multi_simulation_insights"] >= 1
    assert diagnostics["report_assistance"] >= 1
    assert diagnostics["command_routed_executions"] == 1

    assert AI_ENGINEERING_SIMULATION_ASSISTANT_SETTINGS_KEY in workspace.project_settings
    assert list(workspace.scene3d.entities()) == []
    assert getattr(workspace.product_manager, "bodies", []) == []
    assert getattr(workspace.product_manager, "features", []) == []

    with TemporaryDirectory() as directory:
        path = Path(directory) / "ai_engineering_simulation_assistant.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.simulation_workspace.load_from_settings()
    restored_assistant = AIEngineeringSimulationAssistant(ai)
    restored_assistant.load_from_settings(restored)

    assert restored_assistant.initialized is True
    assert len(restored_assistant.conversations) >= 1
    assert len(restored_assistant.recommendations) >= len(recommendations)
    assert len(restored_assistant.configuration_guidance) >= 1
    assert len(restored_assistant.review_findings) >= 1
    assert len(restored_assistant.interpretations) >= len(interpretations)
    assert len(restored_assistant.report_assistance) >= 1
    assert len(restored_assistant.execution_records) == 1
    assert restored.simulation_workspace.validate()["valid"] is True
    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []


if __name__ == "__main__":
    test_ai_engineering_simulation_assistant_orchestrates_existing_simulation_platform()
    print("ai-engineering-simulation-assistant-ok")
