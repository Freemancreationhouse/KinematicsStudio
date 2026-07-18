import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.bim import (
    BIMCategory,
    BIMElementDefinition,
    BIMInstance,
    BIMType,
    ElementCategoryMetadata,
    ElementParameters,
    ElementRelationships,
)
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.bim_manager.create_project("Rendered Element BIM")
category = workspace.bim_manager.add_category(BIMCategory("Columns"))
element_category = workspace.bim_manager.add_element_category(
    ElementCategoryMetadata("Column", "Column elements", "#ce93d8")
)
definition = workspace.bim_manager.add_element_definition(
    BIMElementDefinition(
        "Column",
        "Column Element",
        element_category.id,
        parameters=ElementParameters("Column", "Structural column", "Column", "400x400", "Concrete", "2h"),
    )
)
bim_type = BIMType("400x400 Column", category.id)
bim_type.element_definition_id = definition.id
workspace.bim_manager.add_type(bim_type)
mesh = MeshEntity(MeshData.box(0.4, 0.4, 3.0), name="Rendered Element Column Mesh")
mesh.id = "rendered-element-column-mesh"
workspace.add_3d_entity(mesh)
instance = BIMInstance("Rendered Element Column", category.id, bim_type.id, mesh)
instance.element_definition_id = definition.id
instance.element_parameters.material = "Concrete"
instance.element_parameters.fire_rating = "2h"
instance.element_relationships = ElementRelationships(hosts=["level-01"], adjacent=["grid-a"])
workspace.bim_manager.add_instance(instance)
workspace.selection.select(instance)

renderer = Renderer3D()
renderer.camera = Camera3D()
renderer.camera.resize(640, 480)

image = QImage(640, 480, QImage.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer.render(painter, workspace, 640, 480)
painter.end()

panel = PropertyPanel()
panel.set_workspace(workspace)
panel.show_selection([instance])

assert panel.type.text() == "BIMInstance"
assert panel.content.text() == "Rendered Element Column"
assert "Element: Column" in panel.line_type.text()
assert "Properties:" in panel.radius.text()
assert "Relations: 2" in panel.radius.text()
assert panel.length.text() == "Material: Concrete"
assert panel.angle.text() == "Fire: 2h"

print("3d-bim-element-library-renderer-property-ok")
