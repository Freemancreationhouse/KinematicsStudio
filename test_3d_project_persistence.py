import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "camera3d.ksproj")

    app = CADApplication()
    app.camera3d.state.yaw = 75.0
    app.camera3d.state.pitch = 22.0
    app.camera3d.state.distance = 1234.0
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)

    assert restored.camera3d.state.yaw == 75.0
    assert restored.camera3d.state.pitch == 22.0
    assert restored.camera3d.state.distance == 1234.0
    assert restored.workspace.project_settings["view3d"]["camera"]["yaw"] == 75.0

print("3d-project-persistence-ok")
