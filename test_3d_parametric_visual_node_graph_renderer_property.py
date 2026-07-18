import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart, VisualNodeGraphItem
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])
workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Rendered Node Graph Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Rendered Node Graph Part", "Rendered Node Graph Mesh"))
engine = manager.parametric_manager.create_engine("Rendered Node Graph Engine")
solver = manager.parametric_manager.create_solver("Rendered Node Graph Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Rendered Visual Graph", engine, solver)
node = manager.parametric_manager.create_node(graph, "Rendered Node")
output_port = manager.parametric_manager.add_port(node, "Out", "Output", "Any")
input_port = manager.parametric_manager.add_port(node, "In", "Input", "Any")
connection = manager.parametric_manager.connect_nodes(graph, node, node, output_port, input_port, "Rendered Connection")
item = manager.parametric_manager.add_item(VisualNodeGraphItem("Rendered Frame", graph.id, "Frame"))

renderer = Renderer3D()
for product_item in (graph, node, output_port, input_port, connection, item):
    assert renderer._product_color(product_item, manager).isValid()

panel = PropertyPanel()
panel.set_workspace(workspace)
for product_item in (graph, node, output_port, input_port, connection, item):
    panel.show_selection([product_item])
    assert panel.radius.text()
    assert panel.line_weight.text()

assert graph in workspace.visible_product_objects()
assert node in workspace.visible_product_objects()
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "Rendered Node Graph Mesh"

print("3d-parametric-visual-node-graph-renderer-property-ok")
