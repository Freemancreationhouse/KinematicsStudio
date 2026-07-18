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
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Rendered Data Tree Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Rendered Data Tree Part", "Rendered Data Tree Mesh"))
engine = manager.parametric_manager.create_engine("Rendered Data Tree Engine")
solver = manager.parametric_manager.create_solver("Rendered Data Tree Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Rendered Data Tree Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("Rendered Data Tree", engine, solver, graph)
branch = manager.parametric_manager.create_data_branch(tree, "Rendered Branch", branch_identifier="{0}")
path = manager.parametric_manager.create_data_path(tree, branch, "Rendered Path", [0])
data_item = manager.parametric_manager.create_data_item(tree, branch, path, "Rendered Item", "Any", {"object_id": part})
container = manager.parametric_manager.create_data_container(tree, branch, "Rendered Container", [data_item])
flow = manager.parametric_manager.create_data_flow(tree, data_item, container, "Rendered Flow")

renderer = Renderer3D()
for product_item in (tree, branch, path, data_item, container, flow):
    assert renderer._product_color(product_item, manager).isValid()

panel = PropertyPanel()
panel.set_workspace(workspace)
for product_item in (tree, branch, path, data_item, container, flow):
    panel.show_selection([product_item])
    assert panel.radius.text()
    assert panel.line_weight.text()

assert tree in workspace.visible_product_objects()
assert data_item in workspace.visible_product_objects()
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "Rendered Data Tree Mesh"

print("3d-parametric-data-tree-renderer-property-ok")
