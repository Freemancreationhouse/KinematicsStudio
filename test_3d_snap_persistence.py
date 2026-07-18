import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "snap3d.ksproj")
    app = CADApplication()
    app.workspace.snap_manager3d.set_enabled(False)
    app.workspace.snap_manager3d.tolerance = 18.0
    app.workspace.snap_manager3d.grid_spacing = 12.5
    app.workspace.snap_manager3d.filters = {"VERTEX", "GRID", "ORIGIN"}
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    snap = restored.workspace.snap_manager3d

    assert not snap.enabled
    assert snap.tolerance == 18.0
    assert snap.grid_spacing == 12.5
    assert snap.filters == {"VERTEX", "GRID", "ORIGIN"}

print("3d-snap-persistence-ok")
