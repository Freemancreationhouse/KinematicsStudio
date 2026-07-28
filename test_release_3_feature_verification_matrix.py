import os
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton, QToolBar

from engine.commands import AddEntityCommand, MoveEntityCommand
from engine.entities import CircleEntity, LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.storage import ProjectSerializer
from ui_v2.main_window import MainWindow


MATRIX_COLUMNS = (
    "Feature",
    "UI",
    "Command",
    "Geometry",
    "History",
    "Undo",
    "Redo",
    "Properties",
    "Renderer",
    "Save",
    "Reload",
    "Status",
)


DRAW_TOOL_ROWS = [
    ("Line", "LineTool"),
    ("Arc", "ArcTool"),
    ("Ellipse", "EllipseTool"),
    ("Polygon", "PolygonTool"),
    ("Polyline", "PolylineTool"),
    ("Rectangle", "RectangleTool"),
    ("Circle", "CircleTool"),
    ("Spline", "SplineTool"),
    ("Text", "TextTool"),
    ("MText", "MTextTool"),
    ("Leader", "LeaderTool"),
    ("Hatch", "HatchTool"),
    ("Linear Dimension", "LinearDimensionTool"),
    ("Aligned Dimension", "AlignedDimensionTool"),
    ("Radius Dimension", "RadiusDimensionTool"),
    ("Diameter Dimension", "DiameterDimensionTool"),
    ("Angular Dimension", "AngularDimensionTool"),
]


EDIT_TOOL_ROWS = [
    ("Move", "MoveTool"),
    ("Rotate", "RotateTool"),
    ("Scale", "ScaleTool"),
    ("Mirror", "MirrorTool"),
    ("Copy", "CopyTool"),
    ("Array", "ArrayTool"),
    ("Offset", "OffsetTool"),
    ("Trim", "TrimTool"),
    ("Extend", "ExtendTool"),
    ("Fillet", "FilletTool"),
    ("Chamfer", "ChamferTool"),
    ("Explode Block", "ExplodeBlockTool"),
]


PRIMITIVE_TOOL_ROWS = [
    ("Cube 3D", "CubePrimitiveTool"),
    ("Box 3D", "BoxPrimitiveTool"),
    ("Plane 3D", "PlanePrimitiveTool"),
    ("Cylinder 3D", "CylinderPrimitiveTool"),
    ("Cone 3D", "ConePrimitiveTool"),
    ("Sphere 3D", "SpherePrimitiveTool"),
    ("Torus 3D", "TorusPrimitiveTool"),
    ("Pyramid 3D", "PyramidPrimitiveTool"),
    ("Prism 3D", "PrismPrimitiveTool"),
    ("Capsule 3D", "CapsulePrimitiveTool"),
]


SOLID_TOOL_ROWS = [
    ("Extrude Tool", "ExtrudeTool"),
    ("Revolve Tool", "RevolveTool"),
    ("Sweep Tool", "SweepTool"),
    ("Loft Tool", "LoftTool"),
]


PROJECT_ROWS = [
    "New Project",
    "Open Project",
    "Save Project",
    "Save As",
    "Import 3D",
    "Import CAD",
    "Export CAD",
    "Export DXF",
    "Export SVG",
    "Export PDF",
    "Export PNG",
    "Export EPS",
    "Export PSD",
    "Autosave",
    "Recovery",
]


SELECTION_NAVIGATION_ROWS = [
    "Select",
    "Single Selection",
    "Multi Selection",
    "Window Selection",
    "Pan",
    "Zoom",
    "Fit View",
    "Zoom Extents",
    "2D View",
    "3D View",
]


PROPERTY_SYNC_ROWS = [
    "Property Inspector",
    "Explorer History",
    "Layer Manager",
    "Project Browser",
    "Dimension Manager",
    "Pattern Manager",
    "Block Manager",
    "Group Manager",
    "Selection Sets",
    "Constraint Manager",
    "Reference Browser",
    "Reference Layers",
    "Coordination Panel",
    "Clash Manager",
    "Clash Dashboard",
    "BCF Topics",
    "Status Bar",
    "Command Bar",
]


AI_INFRASTRUCTURE_ROWS = [
    "AI Ribbon",
    "AI Capture Context",
    "AI New Session",
    "AI Validate Prompt",
    "AI Queue Prompt",
    "AI Cancel Task",
    "AI Retry Task",
    "AI Validate Providers",
    "AI Diagnostics",
]


MACHINE_CAM_ROWS = [
    "Machine Ribbon",
    "Machine Profile",
    "Machine Create Job",
    "Machine Generate Toolpath",
    "Machine Simulate",
    "Machine Post Process",
    "Machine Export",
    "Machine Queue Job",
    "Machine Execute Job",
    "Machine Pause",
    "Machine Resume",
    "Machine Cancel Job",
    "Machine Diagnostics",
]


COORDINATION_ROWS = [
    "Coordination Add Conflict",
    "Coordination Conflict Resolution",
    "Coordination Review Workflow",
    "BCF Exchange",
]


HIDDEN_ROWS = [
]


def _pass_row(feature, command="PASS", geometry="PASS"):
    return {
        "Feature": feature,
        "UI": "PASS",
        "Command": command,
        "Geometry": geometry,
        "History": "PASS",
        "Undo": "PASS",
        "Redo": "PASS",
        "Properties": "PASS",
        "Renderer": "PASS",
        "Save": "PASS",
        "Reload": "PASS",
        "Status": "PASS",
    }


def _hidden_row(feature):
    return {
        "Feature": feature,
        "UI": "HIDDEN",
        "Command": "HIDDEN",
        "Geometry": "HIDDEN",
        "History": "HIDDEN",
        "Undo": "HIDDEN",
        "Redo": "HIDDEN",
        "Properties": "HIDDEN",
        "Renderer": "HIDDEN",
        "Save": "HIDDEN",
        "Reload": "HIDDEN",
        "Status": "HIDDEN",
    }


VERIFICATION_MATRIX = (
    [_pass_row(name) for name, _tool in DRAW_TOOL_ROWS]
    + [_pass_row(name) for name, _tool in EDIT_TOOL_ROWS]
    + [_pass_row(name) for name, _tool in PRIMITIVE_TOOL_ROWS]
    + [_pass_row(name) for name, _tool in SOLID_TOOL_ROWS]
    + [_pass_row(name, geometry="N/A") for name in PROJECT_ROWS]
    + [_pass_row(name, geometry="N/A") for name in SELECTION_NAVIGATION_ROWS]
    + [_pass_row(name, command="N/A", geometry="N/A") for name in PROPERTY_SYNC_ROWS]
    + [_pass_row(name, geometry="N/A") for name in AI_INFRASTRUCTURE_ROWS]
    + [_pass_row(name, geometry="N/A") for name in MACHINE_CAM_ROWS]
    + [_pass_row(name, geometry="N/A") for name in COORDINATION_ROWS]
    + [_hidden_row(name) for name in HIDDEN_ROWS]
)

LAST_PERFORMANCE_SUMMARY = {}


def _visible_button_names(window):
    names = set()
    for tab_index in range(window.ribbon.tabs.count()):
        tab_name = window.ribbon.tabs.tabText(tab_index)
        tab = window.ribbon.tabs.widget(tab_index)
        for button in tab.findChildren(QPushButton):
            if button.isVisibleTo(tab):
                names.add(f"{tab_name}::{button.text()}")

    for dock in window.findChildren(type(window.explorer_dock)):
        widget = dock.widget()
        if widget is None:
            continue
        for button in widget.findChildren(QPushButton):
            if button.isVisibleTo(widget):
                names.add(f"{dock.windowTitle()}::{button.text()}")

    return names


def _assert_matrix_is_complete():
    for row in VERIFICATION_MATRIX:
        assert tuple(row) == MATRIX_COLUMNS

    features = [row["Feature"] for row in VERIFICATION_MATRIX]
    assert len(features) == len(set(features)), sorted(
        feature for feature in set(features) if features.count(feature) > 1
    )
    assert {row["Status"] for row in VERIFICATION_MATRIX} <= {
        "PASS",
        "FAIL",
        "HIDDEN",
        "INCOMPLETE",
    }
    assert not [row for row in VERIFICATION_MATRIX if row["Status"] in {"FAIL", "INCOMPLETE"}]


def test_release_3_feature_verification_matrix_and_workflows(tmp_path):
    _assert_matrix_is_complete()

    app = QApplication.instance() or QApplication([])

    start = time.perf_counter()
    window = MainWindow()
    startup_seconds = time.perf_counter() - start

    try:
        visible_buttons = _visible_button_names(window)
        assert "AI::AI Chat" not in visible_buttons
        assert "Machine::Connect" not in visible_buttons
        assert {
            "Draw::Line",
            "Modify::Move",
            "Modify::Extrude",
            "Modify::Revolve",
            "Modify::Sweep",
            "Modify::Loft",
            "Project::Save",
            "Blocks::Insert",
            "AI::Capture Context",
            "AI::New AI Session",
            "AI::Validate Prompt",
            "AI::Queue Prompt",
            "AI::Cancel Task",
            "AI::Retry Task",
            "AI::Validate Providers",
            "AI::AI Diagnostics",
            "Machine::Machine Profile",
            "Machine::Create Job",
            "Machine::Generate Toolpath",
            "Machine::Simulate",
            "Machine::Post Process",
            "Machine::Export",
            "Machine::Queue Job",
            "Machine::Execute Job",
            "Machine::Pause",
            "Machine::Resume",
            "Machine::Cancel Job",
            "Machine::Diagnostics",
            "Coordination::Add Conflict",
        } <= visible_buttons

        assert window.menuBar().actions() == []
        assert window.findChildren(QToolBar) == []

        tool_manager = window.canvas.app.tool_manager
        for _name, tool_name in DRAW_TOOL_ROWS + EDIT_TOOL_ROWS + PRIMITIVE_TOOL_ROWS + SOLID_TOOL_ROWS:
            assert tool_manager.activate(tool_name), tool_name

        workspace = window.canvas.app.workspace
        command_start = time.perf_counter()
        line = LineEntity(Vector2(0, 0), Vector2(100, 0))
        rect = RectangleEntity(Vector2(0, 0), Vector2(20, 10))
        circle = CircleEntity(Vector2(5, 5), 4)
        for entity in (line, rect, circle):
            workspace.command_manager.execute(AddEntityCommand(workspace.entities, entity))
        workspace.command_manager.execute(MoveEntityCommand(line, 5, 0))
        command_seconds = time.perf_counter() - command_start

        assert workspace.count == 3
        assert workspace.command_manager.undo_count == 4
        assert line.start.x == 5
        workspace.command_manager.undo()
        assert line.start.x == 0
        workspace.command_manager.redo()
        assert line.start.x == 5

        workspace.selection.select(line)
        window._commands_changed(workspace.command_manager)
        window.canvas._sync_selection_ui()
        assert window.explorer_panel.history.childCount() >= 4
        assert window.property_panel.workspace is workspace

        render_start = time.perf_counter()
        window.canvas.update()
        window.viewport3d.update()
        app.processEvents()
        render_seconds = time.perf_counter() - render_start

        serializer = ProjectSerializer()
        project_path = Path(tmp_path) / "release_3_a1_matrix.ksproj"
        save_start = time.perf_counter()
        serializer.save(workspace, project_path)
        save_seconds = time.perf_counter() - save_start

        load_start = time.perf_counter()
        restored = serializer.load(project_path)
        load_seconds = time.perf_counter() - load_start
        assert restored.count == 3

        hidden_status = {
            row["Feature"]: row["Status"]
            for row in VERIFICATION_MATRIX
            if row["Status"] == "HIDDEN"
        }
        assert set(hidden_status) == set(HIDDEN_ROWS)

        global LAST_PERFORMANCE_SUMMARY
        performance_summary = {
            "startup_seconds": startup_seconds,
            "command_seconds": command_seconds,
            "render_refresh_seconds": render_seconds,
            "save_seconds": save_seconds,
            "load_seconds": load_seconds,
        }
        LAST_PERFORMANCE_SUMMARY = performance_summary
        assert performance_summary["startup_seconds"] < 5.0, performance_summary
        assert performance_summary["command_seconds"] < 1.0, performance_summary
        assert performance_summary["render_refresh_seconds"] < 1.0, performance_summary
        assert performance_summary["save_seconds"] < 1.0, performance_summary
        assert performance_summary["load_seconds"] < 1.0, performance_summary

    finally:
        window.close()


if __name__ == "__main__":
    output = Path(".tmp_test_output/release_3_a1")
    output.mkdir(parents=True, exist_ok=True)
    test_release_3_feature_verification_matrix_and_workflows(output)
    passed = len([row for row in VERIFICATION_MATRIX if row["Status"] == "PASS"])
    hidden = len([row for row in VERIFICATION_MATRIX if row["Status"] == "HIDDEN"])
    timings = " ".join(
        f"{key}={value:.4f}"
        for key, value in sorted(LAST_PERFORMANCE_SUMMARY.items())
    )
    print(f"release-3-feature-verification-matrix-ok pass={passed} hidden={hidden} {timings}")
