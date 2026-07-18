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
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Rendered BIM Node Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Rendered BIM Node Part", "Rendered BIM Node Mesh"))
engine = manager.parametric_manager.create_engine("Rendered BIM Node Engine")
solver = manager.parametric_manager.create_solver("Rendered BIM Node Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Rendered BIM Node Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("Rendered BIM Node Data Tree", engine, solver, graph)
cad_library = manager.parametric_manager.create_cad_node_library("Rendered CAD Bridge", engine, graph, tree)
bim_library = manager.parametric_manager.create_bim_node_library("Rendered BIM Library", engine, graph, tree, cad_library)
category = manager.parametric_manager.create_bim_node_category(bim_library, "Architectural Nodes", "Architectural", "Architecture")
definition = manager.parametric_manager.create_bim_node_definition(bim_library, category, "Rendered Door Node", "Architectural", "Door")
template = manager.parametric_manager.create_bim_node_template(bim_library, definition, "Rendered Door Template")

renderer = Renderer3D()
for item in (bim_library, category, definition, template):
    assert renderer._product_color(item, manager).isValid()

panel = PropertyPanel()
panel.set_workspace(workspace)
for item in (bim_library, category, definition, template):
    panel.show_selection([item])
    assert panel.radius.text()
    assert panel.line_weight.text()

assert bim_library in workspace.visible_product_objects()
assert definition in workspace.visible_product_objects()
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "Rendered BIM Node Mesh"

print("3d-parametric-bim-nodes-renderer-property-ok")
