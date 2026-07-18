import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.import3d import ImportSettings
from engine.workspace.workspace import Workspace
from ui_v2.reference_browser_panel import ReferenceBrowserPanel


qt_app = QApplication.instance() or QApplication([])


def write(path, text):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "browser.obj")
    replacement = os.path.join(folder, "browser.off")
    write(path, "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
    write(replacement, "OFF\n4 1 0\n0 0 0\n2 0 0\n2 2 0\n0 2 0\n4 0 1 2 3\n")

    changed = []
    workspace = Workspace()
    panel = ReferenceBrowserPanel(workspace, lambda: changed.append(True))
    result = panel.import_reference(path, ImportSettings(scale=1.25))

    assert result.reader_type == "OBJ"
    assert panel.tree.topLevelItemCount() == 1
    assert "References: 1" in panel.statistics.text()
    assert workspace.selection.first is workspace.reference_manager.instances[0]

    panel.search.setText("browser")
    assert panel.tree.topLevelItemCount() == 1
    panel.type_filter.setCurrentText("OBJ")
    assert panel.tree.topLevelItemCount() == 1

    panel.replace_reference(replacement, ImportSettings())
    assert workspace.reference_manager.models[0].reader_type == "OFF"

    panel.unload_reference()
    assert workspace.reference_manager.models[0].status == "Unloaded"
    workspace.command_manager.undo()
    assert workspace.reference_manager.models[0].status == "Loaded"

    panel.toggle_visibility()
    assert workspace.reference_manager.models[0].visible is False
    workspace.command_manager.undo()
    assert workspace.reference_manager.models[0].visible is True

    panel.toggle_lock()
    assert workspace.reference_manager.models[0].locked is True

    panel.isolate_reference()
    assert workspace.reference_manager.isolated_model_ids == [workspace.reference_manager.models[0].id]

    panel.remove_reference()
    assert workspace.reference_manager.models == []
    assert changed

print("3d-reference-browser-panel-ok")
