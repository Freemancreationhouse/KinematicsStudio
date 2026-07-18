import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.view_states import VisualStyle


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "views3d.ksproj")
    app = CADApplication()
    app.camera3d.state.yaw = 33.0
    app.workspace.display_mode_manager.set_mode("x_ray")
    app.workspace.visual_style_manager.add(VisualStyle("Saved Style", background="#112233"))
    app.workspace.visual_style_manager.set_current("Saved Style")
    app.workspace.view_state_manager.save_view(
        "Saved View",
        app.camera3d,
        app.workspace.display_mode_manager.current_mode,
        app.workspace.visual_style_manager.current.name,
    )
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    workspace = restored.workspace

    assert workspace.display_mode_manager.current_mode == "x_ray"
    assert workspace.visual_style_manager.current.name == "Saved Style"
    assert workspace.visual_style_manager.current.background == "#112233"
    assert workspace.view_state_manager.current.name == "Saved View"
    assert workspace.view_state_manager.current.camera.yaw == 33.0

print("3d-view-persistence-ok")
