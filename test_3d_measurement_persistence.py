import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.geometry import Vector3


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "measurements3d.ksproj")
    app = CADApplication()
    manager = app.workspace.measurement_manager
    manager.settings.precision = 4
    manager.settings.show_labels = False
    manager.inspection_settings["show_normals"] = False
    measurement = manager.point_to_point(Vector3(), Vector3(6.0, 8.0, 0.0))
    manager.add(measurement)
    app.workspace.selection.select(measurement)
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    restored_manager = restored.workspace.measurement_manager

    assert restored_manager.settings.precision == 4
    assert restored_manager.settings.show_labels is False
    assert restored_manager.inspection_settings["show_normals"] is False
    assert len(restored_manager.measurements) == 1
    assert restored_manager.measurements[0].result.value == 10.0
    assert restored.workspace.selection.first is restored_manager.measurements[0]

print("3d-measurement-persistence-ok")
