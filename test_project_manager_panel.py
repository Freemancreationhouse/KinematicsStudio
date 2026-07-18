import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.entities import LineEntity
from engine.geometry import Vector2
from ui_v2.project_manager_panel import ProjectManagerPanel


qt_app = QApplication.instance() or QApplication([])
cad_app = CADApplication()
cad_app.workspace.add_entity(LineEntity(Vector2(0, 0), Vector2(1, 1)))

panel = ProjectManagerPanel(cad_app)
panel.refresh()

assert panel.value("current_project") == cad_app.workspace.name
assert panel.value("file_path") == "Unsaved"
assert panel.value("entity_count") == "1"
assert panel.value("layer_count") == "1"
assert panel.value("autosave_status") in ("On", "Off")

print("project-manager-panel-ok")
