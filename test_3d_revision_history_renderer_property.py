import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.model_compare import RevisionMetadata
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
entity = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name="Rendered Revision Box")
entity.id = "rendered-revision-box"
workspace.add_3d_entity(entity)
revision = workspace.revision_manager.capture_revision(
    "Rendered Revision",
    workspace,
    RevisionMetadata("Reviewer", "Native", "Visible revision marker", ("render",), ()),
)
workspace.selection.select(revision)

renderer = Renderer3D()
renderer.camera = Camera3D()
renderer.camera.resize(640, 480)

image = QImage(640, 480, QImage.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer.render(painter, workspace, 640, 480)
painter.end()

panel = PropertyPanel()
panel.show_selection([revision])

assert "Revision" in panel.type.text()
assert panel.content.text() == "Visible revision marker"
assert "Source: Native" in panel.alignment.text()
assert "Author: Reviewer" in panel.dimension_style.text()
assert "Objects: 1" in panel.line_type.text()

print("3d-revision-history-renderer-property-ok")
