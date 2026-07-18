import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.references3d import ReferenceModel
from engine.workspace.workspace import Workspace
from ui_v2.reference_layer_panel import ReferenceLayerPanel


qt_app = QApplication.instance() or QApplication([])

changed = []
workspace = Workspace()
model = workspace.reference_manager.add_model(ReferenceModel("Layer Ref", "layer.obj"))
workspace.reference_manager.create_instance(model)
panel = ReferenceLayerPanel(workspace, lambda: changed.append(True))

assert panel.tree.topLevelItemCount() == 1
panel.tree.setCurrentItem(panel.tree.topLevelItem(0))
panel.toggle_visibility()
assert model.layer_mappings["Default"].visible is False
panel.toggle_lock()
assert model.layer_mappings["Default"].locked is True
panel.toggle_isolation()
assert model.layer_mappings["Default"].isolated is True
panel.set_color_override("#123456")
assert model.layer_mappings["Default"].color_override == "#123456"
panel.apply_style(display_color="#abcdef", xray_override=True)
assert model.style_overrides.display_color == "#abcdef"
assert model.style_overrides.xray_override is True
panel.save_preset("Coordination")
assert "Coordination" in model.display_presets
assert changed

print("3d-reference-layer-panel-ok")
