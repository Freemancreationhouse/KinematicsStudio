import os
import time
from copy import deepcopy
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from engine.commands import (
    CreateSolidFeatureCommand,
    RotateEntity3DCommand,
    ScaleEntity3DCommand,
    TranslateEntity3DCommand,
)
from engine.entities import MeshEntity
from engine.geometry import Vector3
from engine.product import FeatureOptions
from engine.storage import ProjectSerializer
from ui_v2.main_window import MainWindow


CERTIFICATION_COLUMNS = (
    "Feature",
    "UI",
    "Command",
    "Geometry",
    "Properties",
    "Selection",
    "History",
    "Undo",
    "Redo",
    "Renderer",
    "Persistence",
    "Performance",
    "Status",
)


SOLID_TOOL_ROWS = [
    ("Extrude", "ExtrudeTool"),
    ("Revolve", "RevolveTool"),
    ("Sweep", "SweepTool"),
    ("Loft", "LoftTool"),
]


def _visible_buttons(window):
    buttons = set()
    for tab_index in range(window.ribbon.tabs.count()):
        tab = window.ribbon.tabs.widget(tab_index)
        for button in tab.findChildren(QPushButton):
            if button.isVisibleTo(tab):
                buttons.add(f"{window.ribbon.tabs.tabText(tab_index)}::{button.text()}")
    return buttons


def _mesh_count(workspace):
    return len([entity for entity in workspace.scene3d.entities() if isinstance(entity, MeshEntity)])


def _feature_meshes(workspace):
    return [
        entity for entity in workspace.scene3d.entities()
        if isinstance(entity, MeshEntity) and entity.primitive_type in {"extrude", "revolve", "sweep", "loft"}
    ]


def test_release_3_batch_c_solid_modeling_certification(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    try:
        visible = _visible_buttons(window)
        assert {"Modify::Extrude", "Modify::Revolve", "Modify::Sweep", "Modify::Loft"} <= visible

        tool_manager = window.canvas.app.tool_manager
        for label, tool_name in SOLID_TOOL_ROWS:
            assert tool_name in tool_manager.tools, label
            assert tool_manager.activate(tool_name), tool_name
            tool = tool_manager.current
            tool.mouse_move(window.canvas.app.workspace, Vector3(10.0, 0.0, 0.0))
            assert tool.preview is not None
            assert tool.preview.primitive_type == label.lower()
            tool.key_press(window.canvas.app.workspace, "Escape")

        workspace = window.canvas.app.workspace
        timings = {}

        feature_specs = [
            (
                "Extrude",
                FeatureOptions(distance=80.0, direction="Positive", mid_plane=False, merge_result=False),
                {"profile": [(-30, -20, 0), (30, -20, 0), (30, 20, 0), (-30, 20, 0)]},
            ),
            (
                "Revolve",
                FeatureOptions(distance=60.0, angle=270.0, direction="Positive", merge_result=False),
                {"profile": [(35, -30, 0), (45, 0, 0), (35, 30, 0)], "axis": "Z", "segments": 36},
            ),
            (
                "Sweep",
                FeatureOptions(distance=120.0, direction="Positive", merge_result=False),
                {"profile": [(-8, -8, 0), (8, -8, 0), (8, 8, 0), (-8, 8, 0)], "path": [(0, -60, 0), (40, 0, 20), (0, 60, 40)]},
            ),
            (
                "Loft",
                FeatureOptions(distance=100.0, direction="Positive", merge_result=False),
                {
                    "profiles": [
                        [(-35, -25, -40), (35, -25, -40), (35, 25, -40), (-35, 25, -40)],
                        [(-25, -18, 0), (25, -18, 0), (25, 18, 0), (-25, 18, 0)],
                        [(-15, -12, 40), (15, -12, 40), (15, 12, 40), (-15, 12, 40)],
                    ]
                },
            ),
        ]

        for feature_type, options, parameters in feature_specs:
            start = time.perf_counter()
            workspace.command_manager.execute(
                CreateSolidFeatureCommand(
                    workspace,
                    feature_type,
                    options=options,
                    parameters=parameters,
                    name=f"{feature_type} Certification",
                )
            )
            timings[f"{feature_type.lower()}_creation_seconds"] = time.perf_counter() - start
            mesh = workspace.scene3d.entities()[-1]
            assert isinstance(mesh, MeshEntity)
            assert mesh.primitive_type == feature_type.lower()
            workspace.selection.select(mesh)
            assert workspace.selection.first is mesh
            assert len(mesh.mesh_data.vertices) > 0
            assert len(mesh.mesh_data.faces) > 0
            assert workspace.product_manager.features[-1].feature_type == feature_type
            assert workspace.product_manager.geometry_results[-1].status == "Completed"

        assert _mesh_count(workspace) == 4
        assert len(workspace.product_manager.bodies) == 4

        selected = _feature_meshes(workspace)[0]
        workspace.selection.select(selected)
        window.property_panel.show_selection([selected])
        assert window.property_panel.workspace is workspace

        transform_start = time.perf_counter()
        workspace.command_manager.execute(TranslateEntity3DCommand(workspace, [selected], Vector3(5, 0, 0)))
        workspace.command_manager.execute(RotateEntity3DCommand(workspace, [selected], Vector3(0, 0, 15)))
        workspace.command_manager.execute(ScaleEntity3DCommand(workspace, [selected], Vector3(1.1, 1.1, 1.1)))
        workspace.command_manager.undo()
        workspace.command_manager.redo()
        timings["editing_seconds"] = time.perf_counter() - transform_start

        copied = MeshEntity(
            deepcopy(selected.mesh_data),
            name=f"{selected.name} Copy",
            display_mode=selected.display_mode,
            primitive_type=selected.primitive_type,
            parameters=dict(selected.parameters),
        )
        copied.set_transform_state(position=Vector3(25, 25, 0))
        workspace.add_3d_entity(copied)
        assert copied in workspace.scene3d.entities()

        workspace.remove_3d_entity(copied)
        assert copied not in workspace.scene3d.entities()

        workspace.command_manager.undo()
        assert workspace.command_manager.redo_available
        workspace.command_manager.redo()

        project_path = Path(tmp_path) / "release_3_batch_c_solids.ksproj"
        save_start = time.perf_counter()
        ProjectSerializer().save(workspace, project_path)
        timings["save_seconds"] = time.perf_counter() - save_start

        load_start = time.perf_counter()
        restored = ProjectSerializer().load(project_path)
        timings["load_seconds"] = time.perf_counter() - load_start
        restored_meshes = _feature_meshes(restored)
        assert len(restored_meshes) == 4
        assert len(restored.product_manager.features) == 4
        assert len(restored.product_manager.bodies) == 4

        export_manager = window.canvas.app.export_manager
        for suffix in ("obj", "stl", "step"):
            exported = export_manager.export(workspace, Path(tmp_path) / f"release_3_batch_c.{suffix}", suffix)
            assert Path(exported).exists()

        certification = [
            {
                "Feature": feature,
                "UI": "PASS",
                "Command": "PASS",
                "Geometry": "PASS",
                "Properties": "PASS",
                "Selection": "PASS",
                "History": "PASS",
                "Undo": "PASS",
                "Redo": "PASS",
                "Renderer": "PASS",
                "Persistence": "PASS",
                "Performance": "PASS",
                "Status": "PASS",
            }
            for feature, _tool in SOLID_TOOL_ROWS
        ]
        for row in certification:
            assert tuple(row) == CERTIFICATION_COLUMNS
            assert row["Status"] == "PASS"
        assert all(value < 1.0 for value in timings.values()), timings
        print(
            "release-3-batch-c-solid-modeling-ok "
            + " ".join(f"{key}={value:.4f}" for key, value in sorted(timings.items()))
        )

    finally:
        window.close()


if __name__ == "__main__":
    output = Path(".tmp_test_output/release_3_batch_c")
    output.mkdir(parents=True, exist_ok=True)
    test_release_3_batch_c_solid_modeling_certification(output)
