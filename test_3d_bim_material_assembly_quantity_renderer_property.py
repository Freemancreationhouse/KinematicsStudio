import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.bim import Assembly, AssemblyMember, BIMInstance, BIMMaterial, MaterialAssignment
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
workspace.bim_manager.create_project("Rendered Material BIM")
material = workspace.bim_manager.add_material(BIMMaterial("Rendered Concrete", color="#8d6e63"))
mesh = MeshEntity(MeshData.box(1.0, 1.0, 3.0), name="Rendered Material Mesh")
mesh.id = "rendered-material-mesh"
workspace.add_3d_entity(mesh)
instance = BIMInstance("Rendered Material Instance", entity=mesh)
workspace.bim_manager.add_instance(instance)
workspace.bim_manager.add_material_assignment(MaterialAssignment(instance.id, material.id, 3.0, "m3"))
assembly = Assembly("Rendered Assembly")
assembly.add_member(AssemblyMember(instance.id, "Core"))
workspace.bim_manager.add_assembly(assembly)
workspace.bim_manager.run_quantity_takeoff()
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
assert panel.content.text() == "Rendered Material Instance"
assert panel.length.text() == "Material: Rendered Concrete"
assert "Assemblies: 1" in panel.radius.text()
assert "QTO Items:" in panel.diameter.text()

print("3d-bim-material-assembly-quantity-renderer-property-ok")
