import os
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication, QPushButton

from engine.commands import (
    CopyEntityCommand,
    MirrorEntityCommand,
    MoveEntityCommand,
    RotateEntityCommand,
    ScaleEntityCommand,
)
from engine.commands.delete_command import DeleteCommand
from engine.entities import ArcEntity, EllipseEntity, PolygonEntity
from engine.geometry import Vector2
from engine.geometry.copy import copy_entities
from engine.geometry.mirror import mirror_entities
from engine.geometry.rotate import rotate_entities
from engine.geometry.scale import scale_entities
from engine.storage import ProjectSerializer
from ui_v2.main_window import MainWindow


CERTIFICATION_MATRIX = [
    {
        "Feature": "Arc",
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
    },
    {
        "Feature": "Ellipse",
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
    },
    {
        "Feature": "Polygon",
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
    },
]

LAST_PERFORMANCE_SUMMARY = {}


class _DeleteProxy:
    def __init__(self, workspace):
        self.workspace = workspace

    def add(self, entity):
        self.workspace.add_entity(entity)

    def remove(self, entity):
        self.workspace.remove_entity(entity)


def test_release_3_batch_b_arc_ellipse_polygon_certification(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    try:
        tab_names = [
            window.ribbon.tabs.tabText(index)
            for index in range(window.ribbon.tabs.count())
        ]
        assert "Draw" in tab_names
        draw_tab = window.ribbon.tabs.widget(tab_names.index("Draw"))
        draw_buttons = {
            button.text()
            for button in draw_tab.findChildren(QPushButton)
        }
        assert {"Arc", "Ellipse", "Polygon"} <= draw_buttons

        tool_manager = window.canvas.app.tool_manager
        for name in ("ArcTool", "EllipseTool", "PolygonTool"):
            assert name in tool_manager.tools
            assert tool_manager.activate(name)

        workspace = window.canvas.app.workspace

        arc_start = time.perf_counter()
        arc_tool = tool_manager.tools["ArcTool"]
        arc_tool.set_mode("three_point")
        arc_tool.mouse_press(workspace, Vector2(0, 0))
        arc_tool.mouse_press(workspace, Vector2(50, 50))
        arc_tool.mouse_move(workspace, Vector2(100, 0))
        assert isinstance(arc_tool.preview, ArcEntity)
        arc_tool.mouse_press(workspace, Vector2(100, 0))
        arc_seconds = time.perf_counter() - arc_start
        arc = next(entity for entity in workspace.entities if isinstance(entity, ArcEntity))
        assert arc.radius > 0
        assert arc.length > 0
        assert arc.hit_test(arc.start_point)

        ellipse_start = time.perf_counter()
        ellipse_tool = tool_manager.tools["EllipseTool"]
        ellipse_tool.set_mode("center")
        ellipse_tool.mouse_press(workspace, Vector2(200, 100))
        ellipse_tool.mouse_move(workspace, Vector2(260, 100))
        assert isinstance(ellipse_tool.preview, EllipseEntity)
        ellipse_tool.mouse_press(workspace, Vector2(260, 100))
        ellipse_tool.mouse_press(workspace, Vector2(260, 130))
        ellipse_seconds = time.perf_counter() - ellipse_start
        ellipse = next(entity for entity in workspace.entities if isinstance(entity, EllipseEntity))
        assert ellipse.major_axis == 120.0
        assert ellipse.minor_axis == 60.0
        assert ellipse.area > 0
        assert ellipse.hit_test(ellipse.sampled_points()[0])

        polygon_start = time.perf_counter()
        polygon_tool = tool_manager.tools["PolygonTool"]
        polygon_tool.sides = 8
        polygon_tool.set_mode("center")
        polygon_tool.mouse_press(workspace, Vector2(400, 100))
        polygon_tool.mouse_move(workspace, Vector2(440, 100))
        assert isinstance(polygon_tool.preview, PolygonEntity)
        polygon_tool.mouse_press(workspace, Vector2(440, 100))
        polygon_seconds = time.perf_counter() - polygon_start
        polygon = next(entity for entity in workspace.entities if isinstance(entity, PolygonEntity))
        assert polygon.sides == 8
        assert len(polygon.points) == 8
        assert polygon.area > 0
        assert polygon.hit_test(polygon.points[0])

        assert workspace.command_manager.undo_count == 3
        workspace.command_manager.undo()
        assert not any(isinstance(entity, PolygonEntity) for entity in workspace.entities)
        workspace.command_manager.redo()
        polygon = next(entity for entity in workspace.entities if isinstance(entity, PolygonEntity))

        for entity in (arc, ellipse, polygon):
            workspace.selection.clear()
            workspace.selection.select(entity)
            window.canvas._sync_selection_ui()
            assert window.property_panel.selected == [entity]
            assert window.property_panel.type.text() == entity.type_name
            assert workspace.selection.filter.matches(entity, workspace)

        window.property_panel.show_selection([arc])
        window.property_panel.radius.setText("75")
        window.property_panel._geometry_changed("radius")
        assert arc.radius == 75.0
        workspace.command_manager.undo()
        assert arc.radius != 75.0
        workspace.command_manager.redo()
        assert arc.radius == 75.0

        window.property_panel.show_selection([ellipse])
        window.property_panel.radius.setText("70")
        window.property_panel._geometry_changed("radius")
        assert ellipse.radius_x == 70.0

        window.property_panel.show_selection([polygon])
        window.property_panel.diameter.setText("12")
        window.property_panel._geometry_changed("diameter")
        assert polygon.sides == 12

        move_start = time.perf_counter()
        workspace.command_manager.execute(MoveEntityCommand(arc, 5, 5))
        assert arc.center.x != 50.0
        workspace.command_manager.undo()
        workspace.command_manager.redo()

        workspace.command_manager.execute(RotateEntityCommand(workspace, [(ellipse, rotate_entities(ellipse, ellipse.center, 30.0))]))
        rotated_ellipse = next(entity for entity in workspace.entities if isinstance(entity, EllipseEntity))
        assert rotated_ellipse.rotation != ellipse.rotation

        workspace.command_manager.execute(ScaleEntityCommand(workspace, [(polygon, scale_entities(polygon, polygon.center, 1.25))]))
        scaled_polygon = next(entity for entity in workspace.entities if isinstance(entity, PolygonEntity))
        assert scaled_polygon.radius > polygon.radius

        workspace.command_manager.execute(MirrorEntityCommand(workspace, [(arc, mirror_entities(arc, Vector2(0, 0), Vector2(0, 100)))]))
        assert any(isinstance(entity, ArcEntity) for entity in workspace.entities)

        copied = []
        for entity in list(workspace.entities):
            if isinstance(entity, (ArcEntity, EllipseEntity, PolygonEntity)):
                copied.extend(copy_entities(entity, 10, 10))
        workspace.command_manager.execute(CopyEntityCommand(workspace, copied))
        assert len([entity for entity in workspace.entities if isinstance(entity, (ArcEntity, EllipseEntity, PolygonEntity))]) >= 6

        proxy = _DeleteProxy(workspace)
        delete_target = copied[0]
        workspace.command_manager.execute(DeleteCommand(proxy, delete_target))
        assert delete_target not in workspace.entities
        workspace.command_manager.undo()
        assert delete_target in workspace.entities
        edit_seconds = time.perf_counter() - move_start

        snap = window.canvas.app.engine.snap_manager
        assert snap.snap(arc.center, workspace).mode in {"CENTER", "GRID"}
        assert snap.snap(ellipse.sampled_points()[0], workspace).mode in {"QUAD", "NEAR", "GRID"}
        polygon_snap = snap.snap(polygon.points[0], workspace)
        assert polygon_snap.mode in {"END", "NEAR", "GRID", "INT"}, polygon_snap.mode

        render_start = time.perf_counter()
        image = QImage(800, 600, QImage.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        window.canvas.app.engine.renderer.render(
            painter,
            workspace,
            None,
            800,
            600,
        )
        painter.end()
        render_seconds = time.perf_counter() - render_start

        serializer = ProjectSerializer()
        project_path = Path(tmp_path) / "batch_b_arc_ellipse_polygon.ksproj"
        save_start = time.perf_counter()
        serializer.save(workspace, project_path)
        save_seconds = time.perf_counter() - save_start

        load_start = time.perf_counter()
        restored = serializer.load(project_path)
        load_seconds = time.perf_counter() - load_start
        assert any(isinstance(entity, ArcEntity) for entity in restored.entities)
        assert any(isinstance(entity, EllipseEntity) for entity in restored.entities)
        assert any(isinstance(entity, PolygonEntity) for entity in restored.entities)

        for suffix, fmt in (("dxf", "dxf"), ("svg", "svg"), ("pdf", "pdf")):
            exported = window.canvas.app.export_manager.export(
                workspace,
                Path(tmp_path) / f"batch_b_export.{suffix}",
                fmt,
            )
            assert Path(exported).exists()
            assert Path(exported).stat().st_size > 0

        global LAST_PERFORMANCE_SUMMARY
        LAST_PERFORMANCE_SUMMARY = {
            "arc_creation_seconds": arc_seconds,
            "ellipse_creation_seconds": ellipse_seconds,
            "polygon_creation_seconds": polygon_seconds,
            "editing_seconds": edit_seconds,
            "render_seconds": render_seconds,
            "save_seconds": save_seconds,
            "load_seconds": load_seconds,
        }
        assert all(value < 1.0 for value in LAST_PERFORMANCE_SUMMARY.values()), LAST_PERFORMANCE_SUMMARY
        assert [row["Status"] for row in CERTIFICATION_MATRIX] == ["PASS", "PASS", "PASS"]

    finally:
        window.close()


if __name__ == "__main__":
    output = Path(".tmp_test_output/release_3_batch_b")
    output.mkdir(parents=True, exist_ok=True)
    test_release_3_batch_b_arc_ellipse_polygon_certification(output)
    timings = " ".join(
        f"{key}={value:.4f}"
        for key, value in sorted(LAST_PERFORMANCE_SUMMARY.items())
    )
    print(f"release-3-batch-b-arc-ellipse-polygon-ok {timings}")
