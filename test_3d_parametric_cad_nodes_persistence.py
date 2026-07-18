import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import CADNodeHistory, CADNodeMetadata, CADNodeVersion, ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 2.0, 3.0), name="Persisted CAD Node Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Persisted CAD Node Part", "Persisted CAD Node Mesh"))
engine = manager.parametric_manager.create_engine("Persisted CAD Node Engine")
solver = manager.parametric_manager.create_solver("Persisted CAD Node Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Persisted CAD Node Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("Persisted CAD Node Data Tree", engine, solver, graph)
library = manager.parametric_manager.create_cad_node_library("Persisted CAD Library", engine, graph, tree)
category = manager.parametric_manager.create_cad_node_category(library, "Feature Nodes", "Feature")
definition = manager.parametric_manager.create_cad_node_definition(library, category, "Persisted Sweep Node", "Feature", "Sweep", CADNodeMetadata(default_values={"operation": "Join"}, reference_mappings={"data_tree": tree.id}))
definition.mesh_entity_id = mesh.name
template = manager.parametric_manager.create_cad_node_template(library, definition, "Persisted Sweep Template")
manager.parametric_manager.add_item(CADNodeVersion(definition.id, "1.0", "Persisted version"))
manager.parametric_manager.add_item(CADNodeHistory(definition.id, library.id, "Persisted", "Persisted CAD node metadata"))
workspace.selection.select(definition)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "cad_nodes.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.cad_node_libraries[0].name == "Persisted CAD Library"
    assert restored.cad_node_libraries[0].definition_ids == [definition.id]
    assert restored.cad_node_categories[0].category_type == "Feature"
    assert restored.cad_node_definitions[0].name == "Persisted Sweep Node"
    assert restored.cad_node_definitions[0].selected is True
    assert restored.cad_node_definitions[0].operation_type == "Sweep"
    assert restored.cad_node_definitions[0].metadata.default_values["operation"] == "Join"
    assert restored.cad_node_definitions[0].metadata.reference_mappings["data_tree"] == tree.id
    assert restored.cad_node_definitions[0].mesh_entity_id == mesh.name
    assert restored.cad_node_templates[0].name == "Persisted Sweep Template"
    assert restored.cad_node_versions[0].definition_id == definition.id
    assert restored.cad_node_histories[0].definition_id == definition.id
    assert restored.cad_node_statistics.libraries == 1
    assert restored.cad_node_statistics.feature_nodes == 1
    assert restored.parts[0].mesh_entity_id == part.mesh_entity_id
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-cad-nodes-persistence-ok")
