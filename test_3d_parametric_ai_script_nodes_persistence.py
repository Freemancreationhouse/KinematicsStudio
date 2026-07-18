import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import AINodeHistory, AINodeMetadata, AINodeVersion, ProductPart, ScriptNodeHistory, ScriptNodeMetadata, ScriptNodeVersion


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 2.0, 3.0), name="Persisted AI Script Node Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Persisted AI Script Node Part", "Persisted AI Script Node Mesh"))
engine = manager.parametric_manager.create_engine("Persisted AI Script Node Engine")
solver = manager.parametric_manager.create_solver("Persisted AI Script Node Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Persisted AI Script Node Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("Persisted AI Script Node Data Tree", engine, solver, graph)
cad_library = manager.parametric_manager.create_cad_node_library("Persisted AI Script CAD Bridge", engine, graph, tree)
bim_library = manager.parametric_manager.create_bim_node_library("Persisted AI Script BIM Bridge", engine, graph, tree, cad_library)
manufacturing_library = manager.parametric_manager.create_manufacturing_node_library("Persisted AI Script Manufacturing Bridge", engine, graph, tree, cad_library, bim_library)
ai_library = manager.parametric_manager.create_ai_node_library("Persisted AI Library", engine, graph, tree, cad_library, bim_library, manufacturing_library)
script_library = manager.parametric_manager.create_script_node_library("Persisted Script Library", engine, graph, tree, cad_library, bim_library, manufacturing_library, ai_library)
ai_category = manager.parametric_manager.create_ai_node_category(ai_library, "AI Nodes", "AI", "Prompt")
script_category = manager.parametric_manager.create_script_node_category(script_library, "Script Nodes", "Script", "Python")
ai_definition = manager.parametric_manager.create_ai_node_definition(ai_library, ai_category, "Persisted AI Prompt Node", "AI", "Prompt", AINodeMetadata(default_parameters={"mode": "metadata"}, reference_mappings={"data_tree": tree.id}, model_provider="Placeholder"))
script_definition = manager.parametric_manager.create_script_node_definition(script_library, script_category, "Persisted Python Script Node", "Script", "Python", ScriptNodeMetadata(default_parameters={"runtime": "metadata"}, reference_mappings={"ai_node": ai_definition.id}, language="Python"))
ai_definition.mesh_entity_id = mesh.name
script_definition.mesh_entity_id = mesh.name
ai_template = manager.parametric_manager.create_ai_node_template(ai_library, ai_definition, "Persisted AI Prompt Template")
script_template = manager.parametric_manager.create_script_node_template(script_library, script_definition, "Persisted Python Template")
manager.parametric_manager.add_item(AINodeVersion(ai_definition.id, "1.0", "Persisted AI version"))
manager.parametric_manager.add_item(ScriptNodeVersion(script_definition.id, "1.0", "Persisted script version"))
manager.parametric_manager.add_item(AINodeHistory(ai_definition.id, ai_library.id, "Persisted", "Persisted AI node metadata"))
manager.parametric_manager.add_item(ScriptNodeHistory(script_definition.id, script_library.id, "Persisted", "Persisted script node metadata"))
workspace.selection.select(ai_definition)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "ai_script_nodes.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.ai_node_libraries[0].name == "Persisted AI Library"
    assert restored.script_node_libraries[0].name == "Persisted Script Library"
    assert restored.ai_node_libraries[0].manufacturing_node_library_id == manufacturing_library.id
    assert restored.script_node_libraries[0].ai_node_library_id == ai_library.id
    assert restored.ai_node_definitions[0].name == "Persisted AI Prompt Node"
    assert restored.ai_node_definitions[0].selected is True
    assert restored.ai_node_definitions[0].metadata.default_parameters["mode"] == "metadata"
    assert restored.ai_node_definitions[0].metadata.reference_mappings["data_tree"] == tree.id
    assert restored.ai_node_definitions[0].mesh_entity_id == mesh.name
    assert restored.script_node_definitions[0].name == "Persisted Python Script Node"
    assert restored.script_node_definitions[0].metadata.default_parameters["runtime"] == "metadata"
    assert restored.script_node_definitions[0].metadata.reference_mappings["ai_node"] == ai_definition.id
    assert restored.script_node_definitions[0].metadata.language == "Python"
    assert restored.script_node_templates[0].name == script_template.name
    assert restored.ai_node_templates[0].name == ai_template.name
    assert restored.ai_node_versions[0].definition_id == ai_definition.id
    assert restored.script_node_versions[0].definition_id == script_definition.id
    assert restored.ai_node_histories[0].definition_id == ai_definition.id
    assert restored.script_node_histories[0].definition_id == script_definition.id
    assert restored.ai_node_statistics.libraries == 1
    assert restored.script_node_statistics.libraries == 1
    assert restored.parts[0].mesh_entity_id == part.mesh_entity_id
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-ai-script-nodes-persistence-ok")
