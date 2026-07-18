import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.clashes import ClashSettings
from engine.commands import RunClashDetectionCommand
from engine.geometry import Vector3
from engine.references3d import ReferenceTransform


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "clashes.ksproj")
    app = CADApplication()
    model_a = app.workspace.reference_manager.create_model("A", "a.obj")
    model_b = app.workspace.reference_manager.create_model("B", "b.obj")
    app.workspace.reference_manager.create_instance(model_a, ReferenceTransform(Vector3()))
    app.workspace.reference_manager.create_instance(model_b, ReferenceTransform(Vector3()))
    app.workspace.command_manager.execute(
        RunClashDetectionCommand(app.workspace, ClashSettings(clearance=1.0))
    )
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)

    assert restored.workspace.clash_manager.results
    assert restored.workspace.clash_manager.settings.clearance == 1.0
    assert restored.workspace.clash_manager.statistics.total == len(restored.workspace.clash_manager.results)
    assert restored.workspace.visible_clashes()

print("3d-clash-persistence-ok")
