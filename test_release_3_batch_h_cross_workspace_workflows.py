import json
import os
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.ai.providers import AIProvider, AIProviderCapabilities
from engine.bcf import BCFTopic
from engine.commands import (
    AddBCFTopicCommand,
    AddEntityCommand,
    AddSiteBoundaryCommand,
    AnalyzeSiteDrainageCommand,
    CaptureAIContextCommand,
    CaptureMachineDiagnosticsCommand,
    CreateBIMProjectCommand,
    CreateGISProjectCommand,
    CreateMachineProfileCommand,
    CreateManufacturingJobCommand,
    CreateSolidFeatureCommand,
    CreateTerrainProjectCommand,
    ExportManufacturingJobCommand,
    GenerateToolpathCommand,
    ImportGISFileCommand,
    ImportTerrainFileCommand,
    PostProcessManufacturingJobCommand,
    SimulateManufacturingJobCommand,
)
from engine.entities import LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.product import FeatureOptions
from engine.storage import ProjectSerializer
from engine.workflow_certification import (
    release_3_cross_workspace_workflow_matrix,
    workflow_summary,
)
from engine.workspace.workspace import Workspace
from ui_v2.main_window import MainWindow


class WorkflowCertificationProvider(AIProvider):
    """Provider used only to prove cross-workspace AI context routing."""

    provider_id = "workflow-certification"
    display_name = "Workflow Certification Provider"

    @property
    def capabilities(self):
        return AIProviderCapabilities(chat=True, structured_output=True)

    def execute(self, task, progress):
        progress(1.0, "workflow context accepted")
        return {"provider_id": self.provider_id, "context_keys": sorted(task.context)}


LAST_PERFORMANCE_SUMMARY = {}


def _write_geojson(path):
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"name": "Workflow Parcel"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[0, 0], [24, 0], [24, 24], [0, 24], [0, 0]]],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_terrain(path):
    path.write_text(
        "\n".join(
            [
                "ncols 3",
                "nrows 3",
                "xllcorner 0",
                "yllcorner 0",
                "cellsize 10",
                "NODATA_value -9999",
                "12 11 10",
                "11 10 9",
                "10 9 8",
            ]
        ),
        encoding="utf-8",
    )


def test_release_3_batch_h_workflow_inventory_is_complete():
    matrix = release_3_cross_workspace_workflow_matrix()
    names = {record.name for record in matrix}
    assert {
        "2D CAD to Product to Simulation to Machine/CAM",
        "GIS to Terrain to Site Engineering to BIM Coordination to BCF",
        "AI Context to Parametric/Product Geometry to Rendering",
        "Parametric to Geometry to Optimization to Manufacturing",
        "Rendering to Export to Documentation",
        "Data Exchange to Every Workspace",
    } <= names
    assert all(record.status == "PASS" for record in matrix)
    assert all(len(record.workspaces) >= 2 for record in matrix)
    assert all(record.entry_points for record in matrix)
    assert all(record.data_exchanged for record in matrix)
    assert workflow_summary() == {
        "total": len(matrix),
        "passed": len(matrix),
        "partial": 0,
        "broken": 0,
        "not_implemented": 0,
    }


def test_release_3_batch_h_cross_workspace_scenarios(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    try:
        workspace = window.canvas.app.workspace
        timings = {}

        cad_start = time.perf_counter()
        sketch = RectangleEntity(Vector2(0, 0), Vector2(30, 20))
        workspace.command_manager.execute(AddEntityCommand(workspace.entities, sketch))
        workspace.selection.select(sketch)
        workspace.command_manager.execute(
            CreateSolidFeatureCommand(
                workspace,
                "Extrude",
                options=FeatureOptions(distance=40.0, direction="Positive"),
                parameters={"profile": [(0, 0, 0), (30, 0, 0), (30, 20, 0), (0, 20, 0)]},
                name="Workflow Extrude",
            )
        )
        assert workspace.product_manager.features[-1].feature_type == "Extrude"
        assert workspace.product_manager.bodies

        simulation = workspace.simulation_workspace.initialize()
        sim_project = simulation.create_project("Workflow Simulation", "Batch H")
        study = simulation.create_structural_study(
            sim_project,
            "Workflow Structural Study",
            target_geometry=[{"body_id": workspace.product_manager.bodies[-1].id}],
        )
        solver = simulation.register_solver("Workflow Solver", "Structural", ["Static Structural"])
        simulation.select_solver(study, solver)
        simulation.manager.schedule_execution(study)
        simulation.create_result(study, "Workflow Result", scalars={"max_displacement": 0.0})
        assert simulation.validate()["valid"] is True

        profile_command = CreateMachineProfileCommand(workspace)
        workspace.command_manager.execute(profile_command)
        job_command = CreateManufacturingJobCommand(workspace)
        workspace.command_manager.execute(job_command)
        toolpath_command = GenerateToolpathCommand(workspace, job_command.job)
        workspace.command_manager.execute(toolpath_command)
        simulation_command = SimulateManufacturingJobCommand(workspace, job_command.job)
        workspace.command_manager.execute(simulation_command)
        post_command = PostProcessManufacturingJobCommand(workspace, job_command.job, "GRBL")
        workspace.command_manager.execute(post_command)
        export_path = Path(tmp_path) / "workflow_cam.gcode"
        workspace.command_manager.execute(ExportManufacturingJobCommand(workspace, export_path, job_command.job, "GRBL"))
        assert export_path.exists()
        assert toolpath_command.toolpaths
        timings["cad_product_sim_machine_seconds"] = time.perf_counter() - cad_start

        gis_start = time.perf_counter()
        geojson_path = Path(tmp_path) / "workflow_site.geojson"
        terrain_path = Path(tmp_path) / "workflow_terrain.asc"
        _write_geojson(geojson_path)
        _write_terrain(terrain_path)
        workspace.command_manager.execute(CreateGISProjectCommand(workspace, "Workflow GIS", "EPSG:4326"))
        workspace.command_manager.execute(ImportGISFileCommand(workspace, geojson_path, "Workflow Parcel Layer"))
        workspace.command_manager.execute(CreateTerrainProjectCommand(workspace, "Workflow Terrain"))
        terrain_import = ImportTerrainFileCommand(workspace, terrain_path, "Workflow Surface")
        workspace.command_manager.execute(terrain_import)
        workspace.command_manager.execute(AddSiteBoundaryCommand(workspace, "Workflow Boundary", "Construction Limit", [[0, 0], [24, 0], [24, 24], [0, 24]]))
        workspace.command_manager.execute(AnalyzeSiteDrainageCommand(workspace, terrain_import.surface, "Workflow Drainage"))

        workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Workflow BIM"))
        workspace.bim_manager.initialize("Workflow BIM", project_units="meters")
        storey = workspace.bim_manager.create_spatial_element("Building Storey", "Workflow Level", elevation=0.0)
        wall = workspace.bim_manager.create_building_object(
            "Workflow Wall",
            "Wall",
            [{"body_id": workspace.product_manager.bodies[-1].id, "source": "BodyManager"}],
            spatial_container_id=storey.id,
        )
        workspace.bim_manager.create_bim_relationship("Contains", storey.id, [wall.id])

        topic = BCFTopic("Workflow Coordination Topic", "GIS/Terrain/Site/BIM coordination")
        workspace.command_manager.execute(AddBCFTopicCommand(workspace, topic))
        assert topic in workspace.bcf_manager.topics()
        assert workspace.gis_manager.active_project is not None
        assert workspace.gis_manager.terrain_manager.active_project is not None
        assert workspace.gis_manager.terrain_manager.site_engineering_manager.active_project is not None
        assert workspace.bim_manager.active_project is not None
        timings["gis_terrain_site_bim_bcf_seconds"] = time.perf_counter() - gis_start

        ai_start = time.perf_counter()
        ai = window.canvas.app.engine.ai_engine
        ai.register_provider(WorkflowCertificationProvider())
        ai.switch_provider("workflow-certification")
        line = LineEntity(Vector2(0, 0), Vector2(12, 0))
        workspace.command_manager.execute(AddEntityCommand(workspace.entities, line))
        workspace.selection.select(line)
        context_command = CaptureAIContextCommand(ai, workspace, "Batch H AI Context")
        workspace.command_manager.execute(context_command)
        assert context_command.snapshot["context"]["selection"]
        assert context_command.snapshot["context"]["workspace"]["entities_2d"] >= 1
        timings["ai_context_parametric_render_seconds"] = time.perf_counter() - ai_start

        sync_start = time.perf_counter()
        window.property_panel.show_selection([line])
        window._commands_changed(workspace.command_manager)
        window.canvas.update()
        window.viewport3d.update()
        app.processEvents()
        assert window.property_panel.workspace is workspace
        assert workspace.command_manager.undo_available
        workspace.command_manager.undo()
        assert workspace.command_manager.redo_available
        workspace.command_manager.redo()
        workspace.command_manager.execute(CaptureMachineDiagnosticsCommand(workspace))
        timings["synchronization_seconds"] = time.perf_counter() - sync_start

        save_start = time.perf_counter()
        project_path = Path(tmp_path) / "batch_h_cross_workspace.ksproj"
        ProjectSerializer().save(
            workspace,
            project_path,
            settings=window.canvas.app._project_settings(),
        )
        timings["save_seconds"] = time.perf_counter() - save_start

        load_start = time.perf_counter()
        restored = ProjectSerializer().load(project_path)
        restored.simulation_workspace.load_from_settings()
        timings["load_seconds"] = time.perf_counter() - load_start
        assert restored.count >= 2
        assert restored.product_manager.features
        assert restored.product_manager.bodies
        assert restored.simulation_workspace.studies
        assert restored.machine_workspace.state.active is True
        assert restored.manufacturing_engine.toolpaths
        assert restored.gis_manager.active_project is not None
        assert restored.gis_manager.terrain_manager.active_project is not None
        assert restored.gis_manager.terrain_manager.site_engineering_manager.active_project is not None
        assert restored.bim_manager.active_project is not None
        assert restored.bcf_manager.topics()

        global LAST_PERFORMANCE_SUMMARY
        LAST_PERFORMANCE_SUMMARY = timings
        assert all(value < 3.0 for value in timings.values()), timings

    finally:
        window.close()


if __name__ == "__main__":
    output = Path(".tmp_test_output/release_3_batch_h")
    output.mkdir(parents=True, exist_ok=True)
    test_release_3_batch_h_workflow_inventory_is_complete()
    test_release_3_batch_h_cross_workspace_scenarios(output)
    timings = " ".join(
        f"{key}={value:.4f}"
        for key, value in sorted(LAST_PERFORMANCE_SUMMARY.items())
    )
    print(f"release-3-batch-h-cross-workspace-workflows-ok {timings}")
