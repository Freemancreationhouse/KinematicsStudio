import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import BIMNodeHistory, BIMNodeMetadata, BIMNodeVersion, ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 2.0, 3.0), name="Persisted BIM Node Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Persisted BIM Node Part", "Persisted BIM Node Mesh"))
engine = manager.parametric_manager.create_engine("Persisted BIM Node Engine")
solver = manager.parametric_manager.create_solver("Persisted BIM Node Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Persisted BIM Node Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("Persisted BIM Node Data Tree", engine, solver, graph)
cad_library = manager.parametric_manager.create_cad_node_library("Persisted CAD Bridge", engine, graph, tree)
bim_library = manager.parametric_manager.create_bim_node_library("Persisted BIM Library", engine, graph, tree, cad_library)
category = manager.parametric_manager.create_bim_node_category(bim_library, "Information Nodes", "Information", "Data")
definition = manager.parametric_manager.create_bim_node_definition(bim_library, category, "Persisted Quantity Node", "Information", "Quantity", BIMNodeMetadata(default_parameters={"mode": "metadata"}, reference_mappings={"data_tree": tree.id}, property_sets=["QuantityMetadata"]))
definition.mesh_entity_id = mesh.name
template = manager.parametric_manager.create_bim_node_template(bim_library, definition, "Persisted Quantity Template")
manager.parametric_manager.add_item(BIMNodeVersion(definition.id, "1.0", "Persisted version"))
manager.parametric_manager.add_item(BIMNodeHistory(definition.id, bim_library.id, "Persisted", "Persisted BIM node metadata"))
workspace.selection.select(definition)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "bim_nodes.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.bim_node_libraries[0].name == "Persisted BIM Library"
    assert restored.bim_node_libraries[0].definition_ids == [definition.id]
    assert restored.bim_node_libraries[0].cad_node_library_id == cad_library.id
    assert restored.bim_node_categories[0].category_type == "Information"
    assert restored.bim_node_definitions[0].name == "Persisted Quantity Node"
    assert restored.bim_node_definitions[0].selected is True
    assert restored.bim_node_definitions[0].operation_type == "Quantity"
    assert restored.bim_node_definitions[0].metadata.default_parameters["mode"] == "metadata"
    assert restored.bim_node_definitions[0].metadata.reference_mappings["data_tree"] == tree.id
    assert restored.bim_node_definitions[0].mesh_entity_id == mesh.name
    assert restored.bim_node_templates[0].name == "Persisted Quantity Template"
    assert restored.bim_node_versions[0].definition_id == definition.id
    assert restored.bim_node_histories[0].definition_id == definition.id
    assert restored.bim_node_statistics.libraries == 1
    assert restored.bim_node_statistics.information_nodes == 1
    assert restored.parts[0].mesh_entity_id == part.mesh_entity_id
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-bim-nodes-persistence-ok")
