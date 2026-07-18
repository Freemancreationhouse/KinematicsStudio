import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.geometry import Vector3
from engine.model_compare import CompareResult, CompareSession
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
result = CompareResult(
    "Modified",
    "object-1",
    "Compared Object",
    {"name": "Before Object", "source": "Reference"},
    {"name": "After Object", "source": "Current"},
    "Object changed between models.",
    Vector3(0.0, 0.0, 0.0),
)
session = CompareSession("Renderer Compare")
session.set_results([result])
workspace.model_compare_manager.add_session(session)
workspace.selection.select(result)

renderer = Renderer3D()
renderer.camera = Camera3D()
renderer.camera.resize(640, 480)

image = QImage(640, 480, QImage.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer.render(painter, workspace, 640, 480)
painter.end()

panel = PropertyPanel()
panel.show_selection([result])

assert "CompareResult" in panel.type.text()
assert panel.content.text() == "Object changed between models."
assert panel.alignment.text() == "Modified"
assert "object-1" in panel.dimension_style.text()
assert "Before Object" in panel.line_type.text()
assert "After Object" in panel.line_type.text()

print("3d-model-compare-renderer-property-ok")
