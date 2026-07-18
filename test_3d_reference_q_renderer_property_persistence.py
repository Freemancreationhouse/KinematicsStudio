import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.commands import UpdateReferenceLayerMappingCommand, UpdateReferenceStyleCommand
from engine.render import Camera3D
from engine.render.renderer3d import Renderer3D
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    obj = os.path.join(folder, "styled.obj")
    project = os.path.join(folder, "styled.ksproj")
    with open(obj, "w", encoding="utf-8") as handle:
        handle.write("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")

    app = CADApplication()
    app.workspace.import_manager.create_reference(app.workspace, obj, "Styled Ref")
    model = app.workspace.reference_manager.models[0]
    instance = app.workspace.reference_manager.instances[0]
    mapping = model.layer_mappings["Default"]
    app.workspace.command_manager.execute(
        UpdateReferenceLayerMappingCommand(
            app.workspace,
            model,
            "Default",
            mapping.to_dict(),
            {**mapping.to_dict(), "color_override": "#336699"},
        )
    )
    before = model.style_overrides.to_dict()
    app.workspace.command_manager.execute(
        UpdateReferenceStyleCommand(
            app.workspace,
            model,
            before,
            {**before, "display_color": "#abcdef", "transparency": 0.25},
        )
    )
    model.coordination_ui_settings["validation_status"] = "Valid"

    renderer = Renderer3D()
    renderer.camera = Camera3D()
    image = QImage(320, 240, QImage.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter, app.workspace, 320, 240)
    painter.end()

    panel = PropertyPanel()
    panel.set_workspace(app.workspace)
    panel.show_selection([instance])
    assert "Ref Layers" in panel.dimension_style.text()
    assert "T:0.25" in panel.color.text()
    assert panel.diameter.text() == "Valid"

    app.save_project(project)
    restored = CADApplication()
    restored.open_project(project)
    restored_model = restored.workspace.reference_manager.models[0]
    assert restored_model.layer_mappings["Default"].color_override == "#336699"
    assert restored_model.style_overrides.transparency == 0.25
    assert restored_model.coordination_ui_settings["validation_status"] == "Valid"

print("3d-reference-q-renderer-property-persistence-ok")
