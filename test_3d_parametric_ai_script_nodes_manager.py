from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import AINodeHistory, AINodeMetadata, AINodeVersion, ProductPart, ScriptNodeHistory, ScriptNodeMetadata, ScriptNodeVersion
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="AI Script Node Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("AI Script Node Part", "AI Script Node Mesh"))
engine = manager.parametric_manager.create_engine("AI Script Node Engine")
solver = manager.parametric_manager.create_solver("AI Script Node Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("AI Script Node Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("AI Script Node Data Tree", engine, solver, graph)
cad_library = manager.parametric_manager.create_cad_node_library("AI Script CAD Bridge", engine, graph, tree)
bim_library = manager.parametric_manager.create_bim_node_library("AI Script BIM Bridge", engine, graph, tree, cad_library)
manufacturing_library = manager.parametric_manager.create_manufacturing_node_library("AI Script Manufacturing Bridge", engine, graph, tree, cad_library, bim_library)

ai_library = manager.parametric_manager.create_ai_node_library("Core AI Nodes", engine, graph, tree, cad_library, bim_library, manufacturing_library)
script_library = manager.parametric_manager.create_script_node_library("Core Script Nodes", engine, graph, tree, cad_library, bim_library, manufacturing_library, ai_library)

ai_category = manager.parametric_manager.create_ai_node_category(ai_library, "AI Nodes", "AI", "Assistant")
optimization_category = manager.parametric_manager.create_ai_node_category(ai_library, "Optimization Nodes", "Optimization", "Design")
workflow_ai_category = manager.parametric_manager.create_ai_node_category(ai_library, "AI Workflow Nodes", "Workflow", "Planning")
script_category = manager.parametric_manager.create_script_node_category(script_library, "Script Nodes", "Script", "Runtime")
automation_category = manager.parametric_manager.create_script_node_category(script_library, "Automation Nodes", "Automation", "Workflow")
data_category = manager.parametric_manager.create_script_node_category(script_library, "Data Nodes", "Data", "Parsing")

prompt_node = manager.parametric_manager.create_ai_node_definition(
    ai_library,
    ai_category,
    "AI Prompt Node",
    "AI",
    "Prompt",
    AINodeMetadata(model_provider="Placeholder", input_definitions=["prompt"], output_definitions=["response"], default_parameters={"mode": "metadata"}),
)
optimization_node = manager.parametric_manager.create_ai_node_definition(ai_library, optimization_category, "AI Optimization Node", "Optimization", "Optimization")
planning_node = manager.parametric_manager.create_ai_node_definition(ai_library, workflow_ai_category, "AI Planning Node", "Workflow", "Planning")
python_node = manager.parametric_manager.create_script_node_definition(
    script_library,
    script_category,
    "Python Script Node",
    "Script",
    "Python",
    ScriptNodeMetadata(language="Python", input_definitions=["input"], output_definitions=["output"], default_parameters={"runtime": "placeholder"}),
)
trigger_node = manager.parametric_manager.create_script_node_definition(script_library, automation_category, "Trigger Node", "Automation", "Trigger")
json_node = manager.parametric_manager.create_script_node_definition(script_library, data_category, "JSON Node", "Data", "JSON")

prompt_node.data_tree_ids.append(tree.id)
prompt_node.cad_node_ids.append(cad_library.id)
prompt_node.bim_node_ids.append(bim_library.id)
prompt_node.manufacturing_node_ids.append(manufacturing_library.id)
prompt_node.live_solver_id = solver.id
prompt_node.product_manager_reference_id = "ProductManager"
prompt_node.workspace_reference_id = "Workspace"
prompt_node.mesh_entity_id = mesh.name
python_node.ai_node_ids.append(prompt_node.id)
python_node.data_tree_ids.append(tree.id)
python_node.manufacturing_node_ids.append(manufacturing_library.id)
python_node.live_solver_id = solver.id
python_node.mesh_entity_id = mesh.name

ai_template = manager.parametric_manager.create_ai_node_template(ai_library, prompt_node, "Prompt Node Template")
script_template = manager.parametric_manager.create_script_node_template(script_library, python_node, "Python Node Template")
ai_version = manager.parametric_manager.add_item(AINodeVersion(prompt_node.id, "1.0", "Initial AI metadata"))
script_version = manager.parametric_manager.add_item(ScriptNodeVersion(python_node.id, "1.0", "Initial script metadata"))
ai_history = manager.parametric_manager.add_item(AINodeHistory(prompt_node.id, ai_library.id, "Created", "AI node metadata created"))
script_history = manager.parametric_manager.add_item(ScriptNodeHistory(python_node.id, script_library.id, "Created", "Script node metadata created"))
stats = manager.parametric_manager.statistics()

assert ai_library.id in engine.ai_node_library_ids
assert script_library.id in engine.script_node_library_ids
assert ai_library.id in graph.metadata.properties["ai_node_library_ids"]
assert script_library.id in graph.metadata.properties["script_node_library_ids"]
assert ai_library.id in tree.metadata.properties["ai_node_library_ids"]
assert script_library.id in tree.metadata.properties["script_node_library_ids"]
assert ai_library.id in manufacturing_library.metadata.properties["ai_node_library_ids"]
assert script_library.id in manufacturing_library.metadata.properties["script_node_library_ids"]
assert script_library.id in ai_library.metadata.properties["script_node_library_ids"]
assert prompt_node.id in ai_category.definition_ids
assert optimization_node.id in optimization_category.definition_ids
assert planning_node.id in workflow_ai_category.definition_ids
assert python_node.id in script_category.definition_ids
assert trigger_node.id in automation_category.definition_ids
assert json_node.id in data_category.definition_ids
assert ai_template.id in ai_library.template_ids
assert script_template.id in script_library.template_ids
assert ai_version.id in prompt_node.version_ids
assert script_version.id in python_node.version_ids
assert ai_history.id in prompt_node.history_ids
assert script_history.id in python_node.history_ids
assert prompt_node.manufacturing_node_ids == [manufacturing_library.id]
assert python_node.ai_node_ids == [prompt_node.id]
assert prompt_node.mesh_entity_id == mesh.name
assert python_node.mesh_entity_id == mesh.name
assert manager.ai_node_statistics.libraries == 1
assert manager.ai_node_statistics.categories == 3
assert manager.ai_node_statistics.definitions == 3
assert manager.ai_node_statistics.ai_nodes == 1
assert manager.ai_node_statistics.optimization_nodes == 1
assert manager.ai_node_statistics.workflow_nodes == 1
assert manager.script_node_statistics.libraries == 1
assert manager.script_node_statistics.categories == 3
assert manager.script_node_statistics.definitions == 3
assert manager.script_node_statistics.script_nodes == 1
assert manager.script_node_statistics.automation_nodes == 1
assert manager.script_node_statistics.data_nodes == 1
assert stats.engines == 1
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "AI Script Node Mesh"

print("3d-parametric-ai-script-nodes-manager-ok")
