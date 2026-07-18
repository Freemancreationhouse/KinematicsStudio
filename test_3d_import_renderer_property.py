import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.render import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])


def write(path, text):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


with tempfile.TemporaryDirectory() as folder:
    obj = os.path.join(folder, "display.obj")
    write(obj, "v 0 0 0\nv 10 0 0\nv 0 10 0\nf 1 2 3\n")

    workspace = Workspace()
    workspace.import_manager.create_reference(workspace, obj, "Display Import")
    instance = workspace.reference_manager.instances[0]

    renderer = Renderer3D()
    renderer.camera = Camera3D()
    image = QImage(320, 240, QImage.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter, workspace, 320, 240)
    painter.end()

    panel = PropertyPanel()
    panel.set_workspace(workspace)
    panel.show_selection([instance])

    assert panel.type.text() == "ReferenceInstance"
    assert panel.alignment.text() == "Reader: OBJ"
    assert "3 V" in panel.line_type.text()

print("3d-import-renderer-property-ok")
