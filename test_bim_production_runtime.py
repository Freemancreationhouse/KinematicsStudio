from engine.bim import BIMParametricDefinition, BIMProject
from engine.commands import (
    CertifyBIMCompatibilityCommand,
    CertifyBIMReleaseCommand,
    CreateWallCommand,
    GenerateBIMDrawingCommand,
    GenerateBIMScheduleCommand,
    InitializeBIMProductionRuntimeCommand,
    OptimizeBIMProjectCommand,
    RunBIMDocumentationTakeoffCommand,
    RunBIMProductionRegressionCommand,
    ValidateBIMRuntimeCommand,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.bim_manager
manager.initialize("Release 1.9 Production BIM Runtime", project_units="meters")

project_node = manager.create_spatial_element("Project", "Production BIM Project")
site = manager.create_spatial_element("Site", "Main Site", project_node.id)
building = manager.create_spatial_element("Building", "Certified Building", site.id)
level = manager.create_spatial_element("Building Storey", "Level 01", building.id)

wall_type = manager.create_native_element_type(
    "Wall Type 200",
    "Wall",
    "Architecture",
    material_id="mat-concrete",
    parameters=BIMParametricDefinition(thickness=0.2, height=3.2, length=8.0),
)
property_set = manager.create_bim_property_set(
    "Runtime Wall Properties",
    {"FireRating": {"type": "Text", "value": "2h"}, "AssetCriticality": "Normal"},
)

workspace.command_manager.execute(
    CreateWallCommand(
        workspace,
        "Wall Runtime 01",
        [{"body_id": "body-runtime-wall", "body_name": "Parametric runtime wall body", "source": "BodyManager"}],
        element_type_id=wall_type.id,
        material_assignment_id="mat-concrete",
        level_id=level.id,
        parameters=BIMParametricDefinition(thickness=0.2, height=3.2, length=8.0),
        property_set_ids=[property_set.id],
    )
)
wall = manager.active_project.native_elements[-1]
manager.create_classification_assignment("Uniclass", "Ss_25_10", "Walls", target_id=wall.id)

workspace.command_manager.execute(
    GenerateBIMDrawingCommand(
        workspace,
        "3D View",
        "Runtime Coordination View",
        [wall.id],
        "",
        "",
        "1:100",
    )
)
workspace.command_manager.execute(
    GenerateBIMScheduleCommand(
        workspace,
        "Wall",
        "Runtime Wall Schedule",
        [("Name", "name"), ("Type", "element_type"), ("Level", "level"), ("Length", "length")],
    )
)
workspace.command_manager.execute(RunBIMDocumentationTakeoffCommand(workspace))

workspace.command_manager.execute(
    InitializeBIMProductionRuntimeCommand(
        workspace,
        {
            "lazy_loading": True,
            "cache_enabled": True,
            "background_tasks_enabled": True,
            "performance_thresholds": {"max_validation_issues": 0, "min_health_score": 70.0},
            "cleanup_policy": {"mode": "metadata-only"},
            "recovery_metadata": {"last_checkpoint": "startup"},
            "version_metadata": {"release": "1.9", "batch": "F"},
        },
    )
)
workspace.command_manager.execute(OptimizeBIMProjectCommand(workspace))
workspace.command_manager.execute(ValidateBIMRuntimeCommand(workspace))
runtime_validation = manager.active_project.production_runtime_validation_report
assert runtime_validation.valid, runtime_validation.issues

workspace.command_manager.execute(RunBIMProductionRegressionCommand(workspace))
regression = manager.active_project.production_regression_results[-1]
assert regression.passed, regression.failures
assert {check["name"] for check in regression.checks}.issuperset(
    {
        "BIM Core",
        "Native BIM Elements",
        "BIM Authoring",
        "IFC & Documentation",
        "BIM Intelligence",
        "Schedules",
        "Quantity Takeoff",
        "Digital Twin",
        "Issue Management",
        "Persistence",
        "Undo/Redo Metadata",
        "History Metadata",
        "Project Loading",
        "Project Saving",
    }
)

workspace.command_manager.execute(CertifyBIMCompatibilityCommand(workspace))
compatibility = manager.active_project.production_compatibility_reports[-1]
assert compatibility.compatible
assert all(item["compatible"] for item in compatibility.release_matrix.values())

workspace.command_manager.execute(CertifyBIMReleaseCommand(workspace))
certification = manager.active_project.production_certification_records[-1]
assert certification.status == "Certified", certification.notes
assert certification.production_readiness
assert certification.architecture_compliance["body_manager_geometry_owner"]

visualization = manager.bim_production_visualization_metadata()
diagnostics = manager.bim_production_diagnostics_report()

assert diagnostics.runtime_status == "Certified"
assert diagnostics.certification_records >= 1
assert diagnostics.regression_runs >= 1
assert diagnostics.performance_reports >= 1
assert visualization["production_performance_overlays"]
assert visualization["production_validation_overlays"]["valid"]
assert visualization["production_certification_summaries"]
assert workspace.scene3d.entities() == []
assert workspace.command_manager.undo_count >= 9

workspace.command_manager.undo()
assert len(manager.active_project.production_certification_records) == 0
workspace.command_manager.redo()
assert manager.active_project.production_certification_records[-1].status == "Certified"

persisted = manager.to_dict()
restored = manager.__class__()
restored.from_dict(persisted)
assert isinstance(restored.active_project, BIMProject)
assert restored.active_project.production_certification_records[-1].production_readiness
assert restored.active_project.production_regression_results[-1].passed
assert restored.bim_production_diagnostics_report().certification_records >= 1

print("bim-production-runtime-ok")
