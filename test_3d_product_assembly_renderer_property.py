import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.product import ProductPart
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(3.0, 3.0, 3.0), name="Rendered Assembly Mesh")
workspace.add_3d_entity(mesh)
manager = workspace.product_manager
manager.create_document("Rendered Assembly Product")
part = manager.add_part(ProductPart("Rendered Assembly Part", "Rendered Assembly Mesh"))

document = manager.assembly_manager.create_document("Rendered Assembly Document")
assembly = manager.assembly_manager.create_assembly(document, "Rendered Assembly")
component = manager.assembly_manager.insert_part(assembly, part, "Rendered Component")
instance = manager.assembly_manager.create_instance(assembly, component, "Rendered Instance", Vector3(1.0, 1.0, 0.0))
mate = manager.mate_manager.create_mate(assembly, "Coincident", component, instance)
exploded = manager.exploded_view_manager.create_view(assembly, "Rendered Exploded")
manager.exploded_view_manager.add_step(exploded, instance, Vector3(4.0, 0.0, 0.0))
configuration = manager.configuration_manager.create_configuration(assembly, "Rendered Configuration")
manager.configuration_manager.set_active(configuration)
workspace.selection.select(assembly)

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

panel.show_selection([assembly])
assert panel.type.text() == "Assembly"
assert "Components: 1" in panel.radius.text()
assert "Instances: 1" in panel.radius.text()
assert "Exploded Views: 1" in panel.width.text()

panel.show_selection([component])
assert panel.type.text() == "AssemblyComponent"
assert "Reference:" in panel.radius.text()
assert "Instances: 1" in panel.width.text()

panel.show_selection([instance])
assert panel.type.text() == "AssemblyInstance"
assert "Component:" in panel.radius.text()
assert "Position:" in panel.width.text()

panel.show_selection([mate])
assert panel.type.text() == "Mate"
assert "Mate: Coincident" in panel.radius.text()

panel.show_selection([exploded])
assert panel.type.text() == "ExplodedView"
assert "Steps: 1" in panel.radius.text()

panel.show_selection([configuration])
assert panel.type.text() == "AssemblyConfiguration"
assert "Suppression:" in panel.radius.text()

print("3d-product-assembly-renderer-property-ok")
