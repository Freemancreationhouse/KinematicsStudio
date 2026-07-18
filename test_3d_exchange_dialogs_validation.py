import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.commands import SaveExchangeProfileCommand, StoreExchangeValidationReportCommand, UpdateExchangeSettingsCommand
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.import3d import ImportSettings
from engine.workspace.workspace import Workspace
from ui_v2.exchange_dialogs import ExchangeExportDialog, ExchangeImportDialog, ExchangeValidationReportPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.scene3d.add_entity(MeshEntity(MeshData.box(2.0, 2.0, 2.0), "Validation Box"))

workspace.command_manager.execute(SaveExchangeProfileCommand(
    workspace,
    "Rhino",
    {"units": "millimeter", "up_axis": "Z", "forward_axis": "Y", "scale": 1.0},
))
assert "Rhino" in workspace.import_manager.validation_manager.profiles

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "model.skp")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("sketchup placeholder")

    import_dialog = ExchangeImportDialog(
        None,
        workspace,
        path,
        ImportSettings("millimeter", 2.0, "Y", "X"),
    )
    assert import_dialog.path.text() == path
    assert import_dialog.settings().units == "millimeter"
    assert import_dialog.profile_name() in {"Default", "Rhino"}

    result = workspace.import_manager.read(path, import_dialog.settings())
    assert result.reader_type == "SKP"
    assert workspace.import_manager.validation_manager.last_report.summary["issues"] >= 1

    export_dialog = ExchangeExportDialog(None, workspace)
    export_dialog.format.setCurrentText("STEP")
    assert export_dialog.format_name() == "step"
    profile = export_dialog.profile_settings()
    assert profile["format"] == "STEP"

    report = workspace.import_manager.validation_manager.validate_workspace(workspace, "step")
    workspace.command_manager.execute(StoreExchangeValidationReportCommand(workspace, report))
    report_panel = ExchangeValidationReportPanel(None, report)
    assert "Issues:" in report_panel.summary.text()

    before = dict(workspace.import_manager.adapter_settings.get("cad_export", {}))
    workspace.command_manager.execute(UpdateExchangeSettingsCommand(
        workspace,
        "cad_export",
        before,
        profile,
    ))
    assert workspace.import_manager.adapter_settings["cad_export"]["format"] == "STEP"
    workspace.command_manager.undo()
    assert "cad_export" not in workspace.import_manager.adapter_settings

workspace.command_manager.undo()
assert workspace.import_manager.validation_manager.last_report is not report

workspace.command_manager.undo()
assert "Rhino" not in workspace.import_manager.validation_manager.profiles

print("3d-exchange-dialogs-validation-ok")
