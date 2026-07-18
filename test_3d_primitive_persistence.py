import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.commands import CreatePrimitiveCommand
from engine.geometry import Vector3


qt_app = QApplication.instance() or QApplication([])

primitive_cases = [
    ("cube", {"size": 10.0}),
    ("box", {"width": 10.0, "depth": 20.0, "height": 30.0}),
    ("plane", {"width": 10.0, "depth": 20.0}),
    ("cylinder", {"radius": 10.0, "height": 20.0, "segments": 12}),
    ("cone", {"radius": 10.0, "height": 20.0, "segments": 12}),
    ("sphere", {"radius": 10.0, "segments": 12, "rings": 8}),
    ("torus", {"major_radius": 20.0, "minor_radius": 5.0, "major_segments": 12, "minor_segments": 8}),
    ("pyramid", {"width": 10.0, "depth": 20.0, "height": 30.0}),
    ("prism", {"radius": 10.0, "height": 20.0, "sides": 6}),
    ("capsule", {"radius": 5.0, "height": 30.0, "segments": 12, "rings": 8}),
]

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "primitive3d.ksproj")
    app = CADApplication()

    for index, (primitive_type, parameters) in enumerate(primitive_cases):
        app.workspace.command_manager.execute(
            CreatePrimitiveCommand(
                app.workspace,
                primitive_type,
                parameters,
                position=Vector3(index * 10.0, 0.0, 0.0),
                display_mode="shaded",
            )
        )

    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    entities = restored.workspace.scene3d.entities()

    assert len(entities) == len(primitive_cases)

    for entity, (primitive_type, parameters) in zip(entities, primitive_cases):
        assert entity.primitive_type == primitive_type
        assert entity.parameters == parameters
        assert entity.display_mode == "shaded"
        assert entity.mesh_data.vertices
        assert all(len(vertex.uv) == 2 for vertex in entity.mesh_data.vertices)

print("3d-primitive-persistence-ok")
