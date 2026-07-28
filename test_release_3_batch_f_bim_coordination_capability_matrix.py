import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from engine.bcf import BCFProject, BCFTopic
from engine.capability_matrix import (
    capability_summary,
    release_3_master_capability_matrix,
)
from engine.commands import (
    AddBCFTopicCommand,
    ImportBCFProjectCommand,
    RemoveBCFTopicCommand,
)
from engine.references3d import ReferenceModel
from engine.storage import ProjectSerializer
from engine.workspace.workspace import Workspace
from ui_v2.coordination_panel import CoordinationPanel
from ui_v2.main_window import MainWindow


def test_release_3_batch_f_coordination_workflow_and_capability_matrix(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    try:
        dock_buttons = set()
        for dock in window.findChildren(type(window.explorer_dock)):
            widget = dock.widget()
            if widget is None:
                continue
            for button in widget.findChildren(QPushButton):
                if button.isVisibleTo(widget):
                    dock_buttons.add(f"{dock.windowTitle()}::{button.text()}")
        assert "Coordination::Add Conflict" in dock_buttons

        workspace = Workspace()
        model = workspace.reference_manager.add_model(ReferenceModel("Batch F Reference", "batch_f.ifc"))
        workspace.reference_manager.create_instance(model)
        panel = CoordinationPanel(workspace)
        panel.reference.setCurrentText("Batch F Reference")
        panel.alignment.setCurrentText("Shared Coordinates")
        panel.origin_mapping.setCurrentText("Shared Origin")
        panel.coordinate_display.setCurrentText("Local Reference")
        panel.offset_x.setValue(2.5)
        panel.rotation_z.setValue(12.0)
        panel.apply_coordination()
        assert model.coordination_ui_settings["alignment"] == "Shared Coordinates"
        assert workspace.coordination_manager.rules[-1].rule_type == "Reference Coordination"

        panel.validate_reference()
        assert model.coordination_ui_settings["validation_status"] == "Valid"

        conflict = panel.add_conflict(
            "Batch F model federation conflict",
            severity="High",
            priority="High",
        )
        assert conflict["status"] == "Open"
        assert conflict["severity"] == "High"
        assert conflict["priority"] == "High"
        assert conflict["reference_id"] == model.id
        assert model.coordination_ui_settings["conflict_description"] == conflict["description"]
        assert workspace.coordination_manager.conflicts[-1]["id"] == conflict["id"]

        undo_count = workspace.command_manager.undo_count
        workspace.command_manager.undo()
        assert workspace.command_manager.undo_count == undo_count - 1
        assert workspace.coordination_manager.conflicts == []
        workspace.command_manager.redo()
        assert workspace.coordination_manager.conflicts[-1]["id"] == conflict["id"]

        serializer = ProjectSerializer()
        project_path = Path(tmp_path) / "batch_f_coordination.ksproj"
        serializer.save(workspace, project_path)
        restored = serializer.load(project_path)
        assert restored.coordination_manager.conflicts[-1]["description"] == conflict["description"]
        assert restored.reference_manager.models[0].coordination_ui_settings["conflict_status"] == "Open"

        topic = BCFTopic("Batch F Coordination Topic", "Coordination exchange validation")
        workspace.command_manager.execute(AddBCFTopicCommand(workspace, topic))
        assert topic in workspace.bcf_manager.topics()
        workspace.command_manager.execute(RemoveBCFTopicCommand(workspace, topic))
        assert topic not in workspace.bcf_manager.topics()
        workspace.command_manager.undo()
        assert topic in workspace.bcf_manager.topics()

        imported_project = BCFProject("Batch F BCF Project")
        imported_project.add_topic(BCFTopic("Imported Batch F Topic"))
        bcf_path = Path(tmp_path) / "batch_f.bcf"
        workspace.bcf_manager.add_project(imported_project)
        workspace.bcf_manager.export_bcf(str(bcf_path), imported_project)
        import_workspace = Workspace()
        import_workspace.command_manager.execute(ImportBCFProjectCommand(import_workspace, str(bcf_path)))
        assert import_workspace.bcf_manager.get_project("Batch F BCF Project") is not None

        records = release_3_master_capability_matrix()
        names = {record.name for record in records}
        assert {
            "BIM Coordination Conflicts",
            "Clash Detection",
            "Issue Management",
            "Review & Approval Workflow",
            "BCF Coordination Exchange",
            "Machine/CAM Workspace",
            "GIS Foundation",
            "AI Platform Infrastructure",
        } <= names
        assert all(record.result == "PASS" for record in records)
        summary = capability_summary()
        assert summary["total"] == len(records)
        assert summary["failed"] == 0
        assert summary["statuses"]["PASS"] >= 40
        assert summary["statuses"]["LEGACY"] == 2

    finally:
        window.close()


if __name__ == "__main__":
    output = Path(".tmp_test_output/release_3_batch_f")
    output.mkdir(parents=True, exist_ok=True)
    test_release_3_batch_f_coordination_workflow_and_capability_matrix(output)
    summary = capability_summary()
    print(
        "release-3-batch-f-bim-coordination-capability-matrix-ok "
        f"total={summary['total']} failed={summary['failed']}"
    )
