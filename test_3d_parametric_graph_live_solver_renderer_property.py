import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import DataBranch, DataTree, Expression, GlobalParameter
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])
workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Rendered Reactive Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
parametric_engine = manager.parametric_manager.create_engine("Rendered Reactive Engine")
execution_engine = manager.parametric_manager.create_execution_engine("Rendered Reactive Execution", parametric_engine)
solver = manager.parametric_manager.create_solver("Rendered Reactive Solver", parametric_engine)
solver_session = manager.parametric_manager.create_solver_session("Rendered Reactive Session", solver, parametric_engine)
parameter = manager.parameter_manager.add_item(GlobalParameter("rendered_value", 5.0))
expression = manager.parameter_manager.add_item(Expression("Rendered Reactive Expression", "rendered_value + 7"))
dependency_graph = manager.dependency_manager.create_graph("Rendered Reactive Graph")
manager.dependency_manager.add_edge(parameter, expression, "ParameterToExpression", graph=dependency_graph)
tree = manager.parametric_manager.add_item(DataTree("Rendered Reactive Tree", parametric_engine.id, solver.id, dependency_graph.id))
branch = manager.parametric_manager.add_item(DataBranch("Rendered Reactive Branch", tree.id))
manager.parametric_manager.run_live_solver(solver, solver_session, dependency_graph, [parameter], execution_engine)

renderer = Renderer3D()
for item in (solver, solver_session, dependency_graph, parameter, expression, tree, branch):
    assert renderer._product_color(item, manager).isValid()

panel = PropertyPanel()
panel.set_workspace(workspace)
for item in (solver, solver_session, dependency_graph, tree, branch):
    panel.show_selection([item])
    assert panel.radius.text()
    assert panel.line_weight.text()

assert len(workspace.scene3d.entities()) == 1

print("3d-parametric-graph-live-solver-renderer-property-ok")
