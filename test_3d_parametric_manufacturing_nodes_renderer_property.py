import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])
workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Rendered Manufacturing Node Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Rendered Manufacturing Node Part", "Rendered Manufacturing Node Mesh"))
engine = manager.parametric_manager.create_engine("Rendered Manufacturing Node Engine")
solver = manager.parametric_manager.create_solver("Rendered Manufacturing Node Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Rendered Manufacturing Node Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("Rendered Manufacturing Node Data Tree", engine, solver, graph)
cad_library = manager.parametric_manager.create_cad_node_library("Rendered Manufacturing CAD Bridge", engine, graph, tree)
bim_library = manager.parametric_manager.create_bim_node_library("Rendered Manufacturing BIM Bridge", engine, graph, tree, cad_library)
library = manager.parametric_manager.create_manufacturing_node_library("Rendered Manufacturing Library", engine, graph, tree, cad_library, bim_library)
category = manager.parametric_manager.create_manufacturing_node_category(library, "CAM Operation Nodes", "CAM Operation", "Milling")
definition = manager.parametric_manager.create_manufacturing_node_definition(library, category, "Rendered Pocket Node", "CAM Operation", "Pocket")
template = manager.parametric_manager.create_manufacturing_node_template(library, definition, "Rendered Pocket Template")

renderer = Renderer3D()
for item in (library, category, definition, template):
    assert renderer._product_color(item, manager).isValid()

panel = PropertyPanel()
panel.set_workspace(workspace)
for item in (library, category, definition, template):
    panel.show_selection([item])
    assert panel.radius.text()
    assert panel.line_weight.text()

assert library in workspace.visible_product_objects()
assert definition in workspace.visible_product_objects()
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "Rendered Manufacturing Node Mesh"

print("3d-parametric-manufacturing-nodes-renderer-property-ok")
