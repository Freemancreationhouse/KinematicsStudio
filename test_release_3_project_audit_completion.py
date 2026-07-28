import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from engine.commands import (
    AddEntityCommand,
    BootstrapIntegratedPlatformRuntimeCommand,
    CertifyIntegratedPlatformRuntimeCommand,
    StartupIntegratedPlatformRuntimeCommand,
    ValidateIntegratedPlatformRuntimeCommand,
)
from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.storage import ProjectSerializer
from ui_v2.main_window import MainWindow


VISIBLE_TOOL_COMMANDS = {
    "SelectTool",
    "LineTool",
    "RectangleTool",
    "CircleTool",
    "ArcTool",
    "EllipseTool",
    "PolygonTool",
    "PolylineTool",
    "ClosedPolylineTool",
    "SplineTool",
    "TextTool",
    "MTextTool",
    "LeaderTool",
    "HatchTool",
    "LinearDimensionTool",
    "AlignedDimensionTool",
    "RadiusDimensionTool",
    "DiameterDimensionTool",
    "AngularDimensionTool",
    "MoveTool",
    "SmartSketchTool",
    "TrimTool",
    "ExtendTool",
    "OffsetTool",
    "RotateTool",
    "MirrorTool",
    "ScaleTool",
    "CopyTool",
    "ArrayTool",
    "FilletTool",
    "ChamferTool",
    "InsertBlockTool",
    "ExplodeBlockTool",
    "CubePrimitiveTool",
    "BoxPrimitiveTool",
    "PlanePrimitiveTool",
    "CylinderPrimitiveTool",
    "ConePrimitiveTool",
    "SpherePrimitiveTool",
    "TorusPrimitiveTool",
    "PyramidPrimitiveTool",
    "PrismPrimitiveTool",
    "CapsulePrimitiveTool",
    "ExtrudeTool",
    "RevolveTool",
    "SweepTool",
    "LoftTool",
}


def test_release_3_visible_product_surface_is_command_connected(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    try:
        tab_names = [
            window.ribbon.tabs.tabText(index)
            for index in range(window.ribbon.tabs.count())
        ]
        assert tab_names == ["Project", "Draw", "Modify", "Blocks", "AI", "Machine"]
        assert window.ribbon.hidden_tabs == {}

        visible_buttons = []
        for tab_index in range(window.ribbon.tabs.count()):
            tab = window.ribbon.tabs.widget(tab_index)
            for button in tab.findChildren(QPushButton):
                visible_buttons.append(
                    f"{window.ribbon.tabs.tabText(tab_index)}::{button.text()}"
                )
        assert "AI::AI Chat" not in visible_buttons
        assert "Machine::Connect" not in visible_buttons
        assert {
            "Draw::Line",
            "Modify::Move",
            "Blocks::Insert",
            "AI::Capture Context",
            "Machine::Create Job",
            "Machine::Generate Toolpath",
            "Machine::Diagnostics",
        } <= set(visible_buttons)

        dock_buttons = []
        for dock in window.findChildren(type(window.explorer_dock)):
            widget = dock.widget()
            if widget is None:
                continue
            for button in widget.findChildren(QPushButton):
                if button.isVisibleTo(widget):
                    dock_buttons.append(f"{dock.windowTitle()}::{button.text()}")
        assert "Coordination::Add Conflict" in set(dock_buttons)

        tool_manager = window.canvas.app.tool_manager
        missing = sorted(VISIBLE_TOOL_COMMANDS - set(tool_manager.tools))
        assert not missing

        for tool_name in sorted(VISIBLE_TOOL_COMMANDS):
            assert tool_manager.activate(tool_name), tool_name

        workspace = window.canvas.app.workspace
        command = AddEntityCommand(
            workspace.entities,
            LineEntity(Vector2(0, 0), Vector2(100, 0)),
        )
        workspace.command_manager.execute(command)
        assert workspace.count == 1
        assert workspace.command_manager.undo_count == 1

        window._commands_changed(workspace.command_manager)
        assert window.explorer_panel.history.childCount() >= 1

        workspace.selection.select(workspace.entities[0])
        window.canvas._sync_selection_ui()
        assert window.property_panel.workspace is workspace

        workspace.command_manager.undo()
        assert workspace.count == 0
        workspace.command_manager.redo()
        assert workspace.count == 1

        project_path = Path(tmp_path) / "release_3_product_surface.ksproj"
        serializer = ProjectSerializer()
        serializer.save(workspace, project_path)
        restored = serializer.load(project_path)
        assert restored.count == 1
        assert restored.command_manager.undo_count == 0

        workspace.command_manager.execute(
            BootstrapIntegratedPlatformRuntimeCommand(workspace)
        )
        workspace.command_manager.execute(
            StartupIntegratedPlatformRuntimeCommand(workspace)
        )
        validation = ValidateIntegratedPlatformRuntimeCommand(workspace)
        workspace.command_manager.execute(validation)
        assert validation.report["valid"] is True, validation.report

        certification = CertifyIntegratedPlatformRuntimeCommand(workspace)
        workspace.command_manager.execute(certification)
        assert certification.certification["status"] == "Certified"
        assert (
            workspace.integrated_design_manager
            .integrated_platform_runtime
            .runtime_state["geometry_owned_by_runtime"]
            is False
        )

    finally:
        window.close()


if __name__ == "__main__":
    output = Path(".tmp_test_output/release_3")
    output.mkdir(parents=True, exist_ok=True)
    test_release_3_visible_product_surface_is_command_connected(output)
    print("release-3-project-audit-completion-ok")
