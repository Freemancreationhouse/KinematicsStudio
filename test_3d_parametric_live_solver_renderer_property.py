import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import GlobalParameter, ProductPart
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])
workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Rendered Solver Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Rendered Solver Part", "Rendered Solver Mesh"))
engine = manager.parametric_manager.create_engine("Rendered Solver Engine")
parametric_session = manager.parametric_manager.create_session("Rendered Parametric Session", engine, references=[part])
parameter = manager.parameter_manager.add_item(GlobalParameter("Rendered Solver Parameter", 7.0))
solver = manager.parametric_manager.create_solver("Rendered Live Solver", engine)
solver_session = manager.parametric_manager.create_solver_session("Rendered Solver Session", solver, engine, parametric_session)
request = manager.parametric_manager.queue_evaluation(parameter, "Parameter Changed", solver, solver_session)
result = manager.parametric_manager.add_evaluation_result(request, "Pending", "Renderer metadata only", [part])

renderer = Renderer3D()
for item in (solver, solver_session, request, result):
    assert renderer._product_color(item, manager).isValid()

panel = PropertyPanel()
panel.set_workspace(workspace)
for item in (solver, solver_session, request, result):
    panel.show_selection([item])
    assert panel.radius.text()
    assert panel.line_weight.text()

assert solver in workspace.visible_product_objects()
assert request in workspace.visible_product_objects()
assert len(workspace.scene3d.entities()) == 1

print("3d-parametric-live-solver-renderer-property-ok")
