import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.geometry import Vector3
from engine.sections import SectionPlane


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "sections3d.ksproj")
    app = CADApplication()
    manager = app.workspace.section_manager
    section = SectionPlane("Saved Cut", Vector3(1.0, 2.0, 3.0), Vector3(0.0, 1.0, 0.0), 321.0)
    section.color = "#00ffff"
    manager.add(section)
    manager.set_active(section)
    manager.clipping.box_enabled = True
    manager.analysis.vertex_display = True
    app.workspace.selection.select(section)
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    restored_manager = restored.workspace.section_manager

    assert len(restored_manager.sections) == 1
    assert restored_manager.active.name == "Saved Cut"
    assert restored_manager.sections[0].origin.x == 1.0
    assert restored_manager.sections[0].size == 321.0
    assert restored_manager.clipping.box_enabled is True
    assert restored_manager.analysis.vertex_display is True
    assert restored.workspace.selection.first is restored_manager.sections[0]

print("3d-section-persistence-ok")
