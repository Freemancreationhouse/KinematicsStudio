import os
import tempfile

from engine.bcf import BCFProject, BCFTopic
from engine.cad.application import CADApplication


app = CADApplication()
workspace = app.workspace

project = BCFProject("Persisted Coordination")
project.add_topic(BCFTopic("Persisted Topic"))
workspace.bcf_manager.add_project(project)
workspace.bcf_manager.settings["browser_state"] = {
    "search": "Persisted",
    "status": "Open",
    "priority": "All",
    "grouping": "Project",
}
workspace.import_manager.adapter_settings["cad_import"] = {
    "units": "millimeter",
    "scale": 1.0,
    "up_axis": "Z",
    "forward_axis": "Y",
}
workspace.import_manager.validation_manager.settings["expected_units"] = "millimeter"
workspace.import_manager.validation_manager.save_profile(
    "Mechanical Exchange",
    {"units": "millimeter", "scale": 1.0, "up_axis": "Z", "forward_axis": "Y"},
)
workspace.import_manager.validation_manager.validate_workspace(workspace, "step")

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "exchange_ui.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored = opened.open_project(path)

    assert restored.bcf_manager.settings["browser_state"]["search"] == "Persisted"
    assert restored.bcf_manager.get_topic("Persisted Topic") is not None
    assert restored.import_manager.adapter_settings["cad_import"]["units"] == "millimeter"
    assert restored.import_manager.validation_manager.settings["expected_units"] == "millimeter"
    assert "Mechanical Exchange" in restored.import_manager.validation_manager.profiles
    assert restored.import_manager.validation_manager.last_report.summary["issues"] >= 1

print("3d-exchange-ui-persistence-ok")
