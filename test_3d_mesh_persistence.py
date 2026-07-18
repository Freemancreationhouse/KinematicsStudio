import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "mesh3d.ksproj")
    app = CADApplication()
    app.workspace.create_layer("Meshes", "#AA55FF")
    layer = app.workspace.layer_manager.get("Meshes")
    entity = MeshEntity(MeshData.box(20, 30, 40), display_mode="shaded")
    entity.show_bounds = True
    app.workspace.add_3d_entity(entity)
    app.workspace.assign_layer(entity, layer)
    app.workspace.selection.select(entity)
    app.workspace.transform_gizmo.set_mode("scale")
    app.workspace.transform_gizmo.highlighted_axis = "Z"
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    entities = restored.workspace.scene3d.entities()

    assert len(entities) == 1
    restored_entity = entities[0]
    assert restored_entity.type_name == "MeshEntity"
    assert restored_entity.display_mode == "shaded"
    assert restored_entity.show_bounds
    assert restored_entity.layer_name == "Meshes"
    assert len(restored_entity.mesh_data.vertices) == 8
    assert restored.workspace.selection.first is restored_entity
    assert restored.workspace.transform_gizmo.mode == "scale"
    assert restored.workspace.transform_gizmo.highlighted_axis == "Z"

print("3d-mesh-persistence-ok")
