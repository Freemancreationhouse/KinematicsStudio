import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.view_states import VisualStyle
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

app = CADApplication()
style = app.workspace.visual_style_manager.add(
    VisualStyle("Panel Style", background="#010203", grid_visible=False, axis_visible=False)
)
app.workspace.visual_style_manager.set_current(style)
app.workspace.display_mode_manager.set_mode("shaded")
mesh = MeshEntity(MeshData.box(10.0, 10.0, 10.0))
app.workspace.add_3d_entity(mesh)
app.workspace.selection.select(mesh)

panel = PropertyPanel()
panel.set_workspace(app.workspace)
panel.show_selection([mesh])

assert "Style: Panel Style" in panel.color.text()
assert "Display: shaded" in panel.line_weight.text()

print("3d-visual-style-property-ok")
