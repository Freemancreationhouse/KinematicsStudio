import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ManufacturingNodeHistory, ManufacturingNodeMetadata, ManufacturingNodeVersion, ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 2.0, 3.0), name="Persisted Manufacturing Node Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Persisted Manufacturing Node Part", "Persisted Manufacturing Node Mesh"))
engine = manager.parametric_manager.create_engine("Persisted Manufacturing Node Engine")
solver = manager.parametric_manager.create_solver("Persisted Manufacturing Node Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Persisted Manufacturing Node Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("Persisted Manufacturing Node Data Tree", engine, solver, graph)
cad_library = manager.parametric_manager.create_cad_node_library("Persisted Manufacturing CAD Bridge", engine, graph, tree)
bim_library = manager.parametric_manager.create_bim_node_library("Persisted Manufacturing BIM Bridge", engine, graph, tree, cad_library)
library = manager.parametric_manager.create_manufacturing_node_library("Persisted Manufacturing Library", engine, graph, tree, cad_library, bim_library)
category = manager.parametric_manager.create_manufacturing_node_category(library, "Information Nodes", "Information", "Data")
definition = manager.parametric_manager.create_manufacturing_node_definition(
    library,
    category,
    "Persisted Toolpath Node",
    "Information",
    "Toolpath",
    ManufacturingNodeMetadata(
        default_parameters={"mode": "metadata"},
        reference_mappings={"data_tree": tree.id},
        manufacturing_process="Documentation",
    ),
)
definition.mesh_entity_id = mesh.name
template = manager.parametric_manager.create_manufacturing_node_template(library, definition, "Persisted Toolpath Template")
manager.parametric_manager.add_item(ManufacturingNodeVersion(definition.id, "1.0", "Persisted version"))
manager.parametric_manager.add_item(ManufacturingNodeHistory(definition.id, library.id, "Persisted", "Persisted manufacturing node metadata"))
workspace.selection.select(definition)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "manufacturing_nodes.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.manufacturing_node_libraries[0].name == "Persisted Manufacturing Library"
    assert restored.manufacturing_node_libraries[0].definition_ids == [definition.id]
    assert restored.manufacturing_node_libraries[0].cad_node_library_id == cad_library.id
    assert restored.manufacturing_node_libraries[0].bim_node_library_id == bim_library.id
    assert restored.manufacturing_node_categories[0].category_type == "Information"
    assert restored.manufacturing_node_definitions[0].name == "Persisted Toolpath Node"
    assert restored.manufacturing_node_definitions[0].selected is True
    assert restored.manufacturing_node_definitions[0].operation_type == "Toolpath"
    assert restored.manufacturing_node_definitions[0].metadata.default_parameters["mode"] == "metadata"
    assert restored.manufacturing_node_definitions[0].metadata.reference_mappings["data_tree"] == tree.id
    assert restored.manufacturing_node_definitions[0].mesh_entity_id == mesh.name
    assert restored.manufacturing_node_templates[0].name == "Persisted Toolpath Template"
    assert restored.manufacturing_node_versions[0].definition_id == definition.id
    assert restored.manufacturing_node_histories[0].definition_id == definition.id
    assert restored.manufacturing_node_statistics.libraries == 1
    assert restored.manufacturing_node_statistics.information_nodes == 1
    assert restored.parts[0].mesh_entity_id == part.mesh_entity_id
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-manufacturing-nodes-persistence-ok")
