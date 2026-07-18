import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.geometry import Vector3


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "construction3d.ksproj")
    app = CADApplication()
    app.workspace.construction_plane_manager.create_offset("XY Plane", "Machine Table", 12.5)
    app.workspace.construction_plane_manager.set_active("Machine Table")
    app.workspace.coordinate_system_manager.create_ucs(
        "Fixture",
        origin=Vector3(5.0, 6.0, 7.0),
    )
    app.workspace.coordinate_system_manager.activate("Fixture")
    app.workspace.coordinate_system_manager.grid_spacing = 12.5
    app.workspace.coordinate_system_manager.grid_subdivisions = 8
    app.workspace.coordinate_system_manager.grid_visible = False
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)

    assert restored.workspace.construction_plane_manager.active.name == "Machine Table"
    assert restored.workspace.coordinate_system_manager.active.name == "Fixture"
    assert restored.workspace.coordinate_system_manager.grid_spacing == 12.5
    assert restored.workspace.coordinate_system_manager.grid_subdivisions == 8
    assert restored.workspace.coordinate_system_manager.grid_visible is False

print("3d-construction-persistence-ok")
