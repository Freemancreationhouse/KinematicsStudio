import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.commands import CreatePrimitiveCommand, TranslateEntity3DCommand
from engine.geometry import Vector3


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "transform3d.ksproj")
    app = CADApplication()
    app.workspace.command_manager.execute(
        CreatePrimitiveCommand(app.workspace, "cube", {"size": 20.0})
    )
    entity = app.workspace.scene3d.entities()[0]
    app.workspace.command_manager.execute(
        TranslateEntity3DCommand(app.workspace, [entity], Vector3(5.0, 6.0, 7.0))
    )
    app.workspace.transform_gizmo.set_coordinate_mode("local")
    app.workspace.transform_gizmo.set_pivot_mode("bounding_box_center")
    app.workspace.selection.select(entity)
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    restored_entity = restored.workspace.scene3d.entities()[0]

    assert restored_entity.position3d.x == 5.0
    assert restored_entity.position3d.y == 6.0
    assert restored_entity.position3d.z == 7.0
    assert restored.workspace.transform_gizmo.coordinate_mode == "local"
    assert restored.workspace.transform_gizmo.pivot_mode == "bounding_box_center"
    assert restored.workspace.selection.first is restored_entity

print("3d-transform-persistence-ok")
