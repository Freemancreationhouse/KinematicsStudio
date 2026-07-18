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
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Rendered AI Script Node Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Rendered AI Script Node Part", "Rendered AI Script Node Mesh"))
engine = manager.parametric_manager.create_engine("Rendered AI Script Node Engine")
solver = manager.parametric_manager.create_solver("Rendered AI Script Node Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Rendered AI Script Node Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("Rendered AI Script Node Data Tree", engine, solver, graph)
cad_library = manager.parametric_manager.create_cad_node_library("Rendered AI Script CAD Bridge", engine, graph, tree)
bim_library = manager.parametric_manager.create_bim_node_library("Rendered AI Script BIM Bridge", engine, graph, tree, cad_library)
manufacturing_library = manager.parametric_manager.create_manufacturing_node_library("Rendered AI Script Manufacturing Bridge", engine, graph, tree, cad_library, bim_library)
ai_library = manager.parametric_manager.create_ai_node_library("Rendered AI Library", engine, graph, tree, cad_library, bim_library, manufacturing_library)
script_library = manager.parametric_manager.create_script_node_library("Rendered Script Library", engine, graph, tree, cad_library, bim_library, manufacturing_library, ai_library)
ai_category = manager.parametric_manager.create_ai_node_category(ai_library, "AI Nodes", "AI", "Prompt")
script_category = manager.parametric_manager.create_script_node_category(script_library, "Script Nodes", "Script", "Python")
ai_definition = manager.parametric_manager.create_ai_node_definition(ai_library, ai_category, "Rendered AI Prompt Node", "AI", "Prompt")
script_definition = manager.parametric_manager.create_script_node_definition(script_library, script_category, "Rendered Python Script Node", "Script", "Python")
ai_template = manager.parametric_manager.create_ai_node_template(ai_library, ai_definition, "Rendered AI Template")
script_template = manager.parametric_manager.create_script_node_template(script_library, script_definition, "Rendered Script Template")

renderer = Renderer3D()
for item in (ai_library, ai_category, ai_definition, ai_template, script_library, script_category, script_definition, script_template):
    assert renderer._product_color(item, manager).isValid()

panel = PropertyPanel()
panel.set_workspace(workspace)
for item in (ai_library, ai_category, ai_definition, ai_template, script_library, script_category, script_definition, script_template):
    panel.show_selection([item])
    assert panel.radius.text()
    assert panel.line_weight.text()

assert ai_library in workspace.visible_product_objects()
assert script_library in workspace.visible_product_objects()
assert ai_definition in workspace.visible_product_objects()
assert script_definition in workspace.visible_product_objects()
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "Rendered AI Script Node Mesh"

print("3d-parametric-ai-script-nodes-renderer-property-ok")
