import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import Expression, GlobalParameter, ProductPart
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


app = QApplication.instance() or QApplication([])
workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Render Dependency Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Render Dependency Part", "Render Dependency Mesh"))
parameter = manager.parameter_manager.add_item(GlobalParameter("Render Parameter", 3.0))
expression = manager.parameter_manager.add_item(Expression("Render Expression", "Render Parameter"))
graph = manager.dependency_manager.create_graph("Render Dependency Graph")
edge = manager.dependency_manager.add_edge(part, parameter, "PartToParameter", graph=graph)
manager.dependency_manager.add_edge(parameter, expression, "ParameterToExpression", graph=graph)
manager.dependency_manager.mark_metadata_dirty(parameter, graph, [expression], "renderer dirty metadata")
node = manager.dependency_nodes[1]
topology = manager.dependency_topologies[0]

renderer = Renderer3D()
assert renderer._product_color(graph, manager).isValid()
assert renderer._product_color(node, manager).isValid()
assert renderer._product_color(edge, manager).isValid()
assert renderer._product_color(topology, manager).isValid()

panel = PropertyPanel()
panel.set_workspace(workspace)
for item in (graph, node, edge, topology):
    panel.show_selection([item])
    assert panel.radius.text()
    assert panel.line_weight.text()

assert len(workspace.scene3d.entities()) == 1

print("3d-parametric-dependency-graph-renderer-property-ok")
