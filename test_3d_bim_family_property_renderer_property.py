import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.bim import BIMCategory, BIMFamily, BIMInstance, BIMType, PropertyDefinition, PropertySet, PropertyValue
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.bim_manager.create_project("Rendered Family BIM")
category = workspace.bim_manager.add_category(BIMCategory("Columns", color="#ab47bc"))
family = workspace.bim_manager.add_family(BIMFamily("Concrete Column Family", category.id))
bim_type = BIMType("400x400 Column", category.id)
bim_type.family_id = family.id
bim_type.type_defaults.values["Height"] = 3.0
workspace.bim_manager.add_type(bim_type)
mesh = MeshEntity(MeshData.box(0.4, 0.4, 3.0), name="Family Render Column Mesh")
mesh.id = "family-render-column-mesh"
workspace.add_3d_entity(mesh)
instance = BIMInstance("Family Render Column", category.id, bim_type.id, mesh)
instance.family_id = family.id
workspace.bim_manager.add_instance(instance)
property_set = PropertySet("Pset_ColumnCommon", instance.id, "Pset_ColumnCommon")
definition = PropertyDefinition("Reference", "Text")
property_set.add_property(definition, PropertyValue(definition.id, "C-001", "IFC"))
workspace.bim_manager.add_property_set(property_set)
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
assert panel.content.text() == "Family Render Column"
assert "Category: Columns" in panel.alignment.text()
assert "Family: Concrete Column Family" in panel.dimension_style.text()
assert "Type: 400x400 Column" in panel.dimension_style.text()
assert "Properties: 2" in panel.radius.text()

print("3d-bim-family-property-renderer-property-ok")
