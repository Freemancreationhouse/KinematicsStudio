import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.entities import Line3D, Point3D, Polyline3D
from engine.geometry import Vector3


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "scene3d.ksproj")
    app = CADApplication()
    app.workspace.create_layer("Scene Layer", "#00AAFF")
    layer = app.workspace.layer_manager.get("Scene Layer")

    point = Point3D(Vector3(1, 2, 3))
    line = Line3D(Vector3(0, 0, 0), Vector3(10, 20, 30))
    polyline = Polyline3D([
        Vector3(0, 0, 0),
        Vector3(5, 5, 5),
        Vector3(10, 0, 10),
    ], closed=True)

    for entity in (point, line, polyline):
        app.workspace.add_3d_entity(entity)
        app.workspace.assign_layer(entity, layer)

    app.workspace.selection.select(line)
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    entities = restored.workspace.scene3d.entities()

    assert len(entities) == 3
    assert entities[0].type_name == "Point3D"
    assert entities[0].layer_name == "Scene Layer"
    assert entities[1].end.z == 30
    assert entities[2].closed
    assert restored.workspace.selection.first is entities[1]
    assert restored.workspace.layer_manager.get("Scene Layer") is not None

print("3d-scene-persistence-ok")
