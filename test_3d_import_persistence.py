import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication


qt_app = QApplication.instance() or QApplication([])


def write(path, text):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


with tempfile.TemporaryDirectory() as folder:
    obj = os.path.join(folder, "persist.obj")
    project = os.path.join(folder, "imported_reference.ksproj")
    write(obj, "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")

    app = CADApplication()
    app.workspace.import_manager.create_reference(app.workspace, obj, "Persisted Import")
    model = app.workspace.reference_manager.models[0]
    app.workspace.coordination_manager.model_alignment(model.id, "Shared Coordinates")
    app.save_project(project)

    restored = CADApplication()
    restored.open_project(project)
    restored_model = restored.workspace.reference_manager.models[0]
    restored_instance = restored.workspace.reference_manager.instances[0]

    assert restored_model.name == "Persisted Import"
    assert restored_model.reader_type == "OBJ"
    assert restored_model.import_statistics.vertices == 3
    assert len(restored_model.mesh_data.vertices) == 3
    assert restored_instance.model_id == restored_model.id
    assert restored.workspace.coordination_manager.rules[0].settings["target"] == "Shared Coordinates"

print("3d-import-persistence-ok")
