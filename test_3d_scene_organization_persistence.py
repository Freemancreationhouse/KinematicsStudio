import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.scene_organization import ViewFilter


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "scene_organization.ksproj")
    app = CADApplication()
    mesh = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name="Persist Mesh")
    app.workspace.add_3d_entity(mesh)
    parent = app.workspace.scene_collection_manager.create("Persist Parent")
    child = app.workspace.scene_collection_manager.create("Persist Child", parent=parent)
    child.color_tag = "#ff00ff"
    app.workspace.scene_collection_manager.move_entity(mesh, child)
    app.workspace.view_filter_manager.add(ViewFilter("Persist Filter", collection_names=["Persist Child"]))
    app.workspace.display_mode_manager.set_mode("bounding_box")
    app.workspace.display_preset_manager.save("Persist Preset", app.workspace)
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    manager = restored.workspace.scene_collection_manager

    assert manager.get("Persist Parent") is not None
    assert manager.get("Persist Child").parent_id == manager.get("Persist Parent").id
    assert manager.get("Persist Child").color_tag == "#ff00ff"
    assert restored.workspace.view_filter_manager.get("Persist Filter") is not None
    assert restored.workspace.display_preset_manager.get("Persist Preset") is not None

print("3d-scene-organization-persistence-ok")
