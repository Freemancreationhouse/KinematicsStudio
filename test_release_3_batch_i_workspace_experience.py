import os
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDockWidget

from engine.commands import AddEntityCommand
from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.storage import ProjectSerializer
from ui_v2.design_system import (
    KINEMATICS_TOKENS,
    design_system_summary,
    ui_component_inventory,
    workspace_layout_matrix,
)
from ui_v2.theme import DARK_THEME, HIGH_CONTRAST_THEME, LIGHT_THEME, THEMES
from ui_v2.main_window import MainWindow


LAST_PERFORMANCE_SUMMARY = {}


def _layout_ratio(window):
    window.resize(1800, 1000)
    window.show()
    QApplication.processEvents()
    window.reset_workspace_layout()
    QApplication.processEvents()
    viewport_width = window.centralWidget().geometry().width()
    total_width = max(1, window.geometry().width())
    viewport_percent = round((viewport_width / total_width) * 100)
    return viewport_percent, 100 - viewport_percent


def test_release_3_batch_i_design_system_and_layout(tmp_path):
    app = QApplication.instance() or QApplication([])
    start = time.perf_counter()
    window = MainWindow()
    startup_seconds = time.perf_counter() - start

    try:
        inventory = ui_component_inventory()
        layouts = workspace_layout_matrix()
        summary = design_system_summary()
        assert summary["components"] == len(inventory)
        assert summary["components_passed"] == len(inventory)
        assert summary["layouts"] == len(layouts)
        assert summary["layouts_passed"] == len(layouts)
        assert all(item.status == "PASS" for item in inventory)
        assert all(item.viewport_target_percent == 80 for item in layouts)
        assert KINEMATICS_TOKENS["accent"]
        assert {"Dark", "Light", "High Contrast"} <= set(THEMES)
        assert DARK_THEME and LIGHT_THEME and HIGH_CONTRAST_THEME

        window.reset_workspace_layout()
        _layout_ratio(window)
        viewport_percent = layouts[0].viewport_actual_percent
        support_percent = layouts[0].supporting_ui_actual_percent
        assert viewport_percent >= 78, (viewport_percent, support_percent)
        assert support_percent <= 22, (viewport_percent, support_percent)

        docks = window.findChildren(QDockWidget)
        assert len(docks) >= 10
        assert all(dock.features() & QDockWidget.DockWidgetMovable for dock in docks)
        assert all(dock.features() & QDockWidget.DockWidgetFloatable for dock in docks)
        assert all(dock.features() & QDockWidget.DockWidgetClosable for dock in docks)

        palette_start = time.perf_counter()
        window.show_command_palette()
        window.command_palette.search.setText("line")
        assert window.command_palette.results.count() >= 1
        first = window.command_palette.results.item(0).text().lower()
        assert "line" in first or "tool" in first
        window.command_palette.search.setText("theme")
        assert window.command_palette.results.count() >= 3
        palette_seconds = time.perf_counter() - palette_start

        window.property_panel.search.setText("radius")
        assert window.property_panel.radius.isVisible()
        assert not window.property_panel.length.isVisible()
        window.property_panel.search.clear()
        assert window.property_panel.length.isVisible()
        assert "Length" in window.property_panel.favorite_fields

        window.enter_focus_mode()
        assert not window.command_bar.isVisible()
        assert all(not dock.isVisible() for dock in docks)
        window.reset_workspace_layout()
        assert window.command_bar.isVisible()
        assert all(dock.isVisible() for dock in docks)
        window.enter_presentation_mode()
        assert not window.ribbon.isVisible()
        window.reset_workspace_layout()
        assert window.ribbon.isVisible()

        workspace = window.canvas.app.workspace
        command_start = time.perf_counter()
        line = LineEntity(Vector2(0, 0), Vector2(10, 0))
        workspace.command_manager.execute(AddEntityCommand(workspace.entities, line))
        workspace.selection.select(line)
        window._commands_changed(workspace.command_manager)
        command_seconds = time.perf_counter() - command_start
        assert workspace.command_manager.undo_available
        workspace.command_manager.undo()
        workspace.command_manager.redo()

        save_start = time.perf_counter()
        project_path = Path(tmp_path) / "batch_i_workspace_experience.ksproj"
        ProjectSerializer().save(workspace, project_path)
        save_seconds = time.perf_counter() - save_start

        load_start = time.perf_counter()
        restored = ProjectSerializer().load(project_path)
        load_seconds = time.perf_counter() - load_start
        assert restored.count == 1

        global LAST_PERFORMANCE_SUMMARY
        LAST_PERFORMANCE_SUMMARY = {
            "startup_seconds": startup_seconds,
            "palette_seconds": palette_seconds,
            "command_seconds": command_seconds,
            "save_seconds": save_seconds,
            "load_seconds": load_seconds,
            "viewport_percent": viewport_percent,
            "support_percent": support_percent,
        }
        assert startup_seconds < 5.0
        assert palette_seconds < 1.0
        assert command_seconds < 1.0
        assert save_seconds < 1.0
        assert load_seconds < 1.0

    finally:
        window.close()


if __name__ == "__main__":
    output = Path(".tmp_test_output/release_3_batch_i")
    output.mkdir(parents=True, exist_ok=True)
    test_release_3_batch_i_design_system_and_layout(output)
    timings = " ".join(
        f"{key}={value:.4f}" if isinstance(value, float) else f"{key}={value}"
        for key, value in sorted(LAST_PERFORMANCE_SUMMARY.items())
    )
    print(f"release-3-batch-i-workspace-experience-ok {timings}")
