import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import Expression, GlobalParameter, ProductPart
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])
workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Rendered Execution Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Rendered Execution Part", "Rendered Execution Mesh"))
parametric_engine = manager.parametric_manager.create_engine("Rendered Execution Parametric Engine")
execution_engine = manager.parametric_manager.create_execution_engine("Rendered Execution Engine", parametric_engine)
execution_session = manager.parametric_manager.create_execution_session("Rendered Execution Session", execution_engine, parametric_engine)
manager.parameter_manager.add_item(GlobalParameter("rendered_width", 4.0))
manager.parameter_manager.add_item(GlobalParameter("rendered_height", 6.0))
expression = manager.parameter_manager.add_item(Expression("Rendered Execution Expression", "rendered_width * rendered_height"))
request = manager.parametric_manager.queue_execution(expression, "Expression Evaluation", execution_engine, execution_session)
result = manager.parametric_manager.execute_request(request)
pipeline = manager.execution_pipelines[0]
history = manager.execution_histories[0]

renderer = Renderer3D()
for item in (execution_engine, execution_session, request, result, pipeline, history):
    assert renderer._product_color(item, manager).isValid()

panel = PropertyPanel()
panel.set_workspace(workspace)
for item in (execution_engine, execution_session, request, result, pipeline):
    panel.show_selection([item])
    assert panel.radius.text()
    assert panel.line_weight.text()

assert execution_engine in workspace.visible_product_objects()
assert execution_session in workspace.visible_product_objects()
assert result in workspace.visible_product_objects()
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "Rendered Execution Mesh"

print("3d-parametric-execution-engine-renderer-property-ok")
