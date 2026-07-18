import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.geometry import Vector3
from engine.references3d import ReferenceTransform


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "references3d.ksproj")
    app = CADApplication()
    model = app.workspace.reference_manager.create_model(
        "MEP Reference",
        "C:/refs/mep.ifc",
        category="MEP",
        group="Coordination",
        source_format="IFC",
    )
    instance = app.workspace.reference_manager.create_instance(
        model,
        ReferenceTransform(
            Vector3(10.0, 20.0, 30.0),
            rotation=Vector3(0.0, 0.0, 45.0),
            scale=Vector3(1.5, 1.5, 1.5),
        ),
    )
    app.workspace.assign_layer(instance)
    instance.selected = True
    app.workspace.selection.select(instance)
    app.workspace.coordination_manager.reference_offset(model.id, Vector3(1.0, 2.0, 3.0))
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    restored_model = restored.workspace.reference_manager.models[0]
    restored_instance = restored.workspace.reference_manager.instances[0]

    assert restored_model.name == "MEP Reference"
    assert restored_model.category == "MEP"
    assert restored_instance.transform.position.z == 30.0
    assert restored_instance.transform.rotation.z == 45.0
    assert restored.workspace.coordination_manager.rules[0].settings["offset"]["y"] == 2.0
    assert restored.workspace.selection.first is restored_instance

print("3d-reference-persistence-ok")
