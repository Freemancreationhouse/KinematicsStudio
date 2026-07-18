import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.import3d import ImportSettings
from ui_v2.reference_browser_panel import ReferenceBrowserPanel


qt_app = QApplication.instance() or QApplication([])


def write(path, text):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


with tempfile.TemporaryDirectory() as folder:
    obj = os.path.join(folder, "ui.obj")
    project = os.path.join(folder, "reference_ui.ksproj")
    write(obj, "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")

    app = CADApplication()
    panel = ReferenceBrowserPanel(app.workspace)
    panel.import_reference(obj, ImportSettings(units="meter", scale=3.0))
    panel.search.setText("ui")
    panel.status_filter.setCurrentText("Loaded")
    panel.refresh()
    app.save_project(project)

    restored = CADApplication()
    restored.open_project(project)

    assert restored.workspace.project_settings["import_options"]["units"] == "meter"
    assert restored.workspace.project_settings["import_options"]["scale"] == 3.0
    assert restored.workspace.project_settings["reference_browser"]["search"] == "ui"
    assert restored.workspace.project_settings["reference_browser"]["status"] == "Loaded"

print("3d-reference-ui-persistence-ok")
