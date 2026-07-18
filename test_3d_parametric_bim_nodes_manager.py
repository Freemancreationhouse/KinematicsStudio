from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import BIMNodeHistory, BIMNodeMetadata, BIMNodeVersion, ProductPart
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="BIM Node Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("BIM Node Part", "BIM Node Mesh"))
engine = manager.parametric_manager.create_engine("BIM Node Engine")
solver = manager.parametric_manager.create_solver("BIM Node Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("BIM Node Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("BIM Node Data Tree", engine, solver, graph)
cad_library = manager.parametric_manager.create_cad_node_library("BIM-CAD Node Library", engine, graph, tree)
bim_library = manager.parametric_manager.create_bim_node_library("Core BIM Nodes", engine, graph, tree, cad_library)
building_category = manager.parametric_manager.create_bim_node_category(bim_library, "Building Nodes", "Building", "Architecture")
architectural_category = manager.parametric_manager.create_bim_node_category(bim_library, "Architectural Nodes", "Architectural", "Architecture")
information_category = manager.parametric_manager.create_bim_node_category(bim_library, "Information Nodes", "Information", "Data")
project_node = manager.parametric_manager.create_bim_node_definition(bim_library, building_category, "Project Node", "Building", "Project")
level_node = manager.parametric_manager.create_bim_node_definition(bim_library, building_category, "Level Node", "Building", "Level")
wall_node = manager.parametric_manager.create_bim_node_definition(bim_library, architectural_category, "Wall Node", "Architectural", "Wall", BIMNodeMetadata(default_parameters={"height": "3000mm"}, property_sets=["Pset_WallCommon"], input_definitions=["level", "path"], output_definitions=["wall"], category="Architectural", discipline="Architecture"))
schedule_node = manager.parametric_manager.create_bim_node_definition(bim_library, information_category, "Schedule Node", "Information", "Schedule")
wall_node.data_tree_ids.append(tree.id)
wall_node.cad_node_ids.append(cad_library.id)
wall_node.live_solver_id = solver.id
wall_node.product_manager_reference_id = "ProductManager"
wall_node.workspace_reference_id = "Workspace"
wall_node.mesh_entity_id = mesh.name
template = manager.parametric_manager.create_bim_node_template(bim_library, wall_node, "Wall Node Template")
version = manager.parametric_manager.add_item(BIMNodeVersion(wall_node.id, "1.0", "Initial metadata"))
history = manager.parametric_manager.add_item(BIMNodeHistory(wall_node.id, bim_library.id, "Created", "BIM node metadata created"))
stats = manager.parametric_manager.statistics()

assert bim_library.id in engine.bim_node_library_ids
assert bim_library.id in graph.metadata.properties["bim_node_library_ids"]
assert bim_library.id in tree.metadata.properties["bim_node_library_ids"]
assert bim_library.id in cad_library.metadata.properties["bim_node_library_ids"]
assert building_category.id in bim_library.category_ids
assert architectural_category.id in bim_library.category_ids
assert information_category.id in bim_library.category_ids
assert project_node.id in building_category.definition_ids
assert wall_node.id in architectural_category.definition_ids
assert schedule_node.id in information_category.definition_ids
assert template.id in bim_library.template_ids
assert version.id in wall_node.version_ids
assert version.id in bim_library.version_ids
assert history.id in wall_node.history_ids
assert history.id in bim_library.history_ids
assert wall_node.data_tree_ids == [tree.id]
assert wall_node.cad_node_ids == [cad_library.id]
assert wall_node.live_solver_id == solver.id
assert wall_node.mesh_entity_id == mesh.name
assert manager.bim_node_statistics.libraries == 1
assert manager.bim_node_statistics.categories == 3
assert manager.bim_node_statistics.definitions == 4
assert manager.bim_node_statistics.building_nodes == 2
assert manager.bim_node_statistics.architectural_nodes == 1
assert manager.bim_node_statistics.information_nodes == 1
assert stats.engines == 1
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "BIM Node Mesh"

print("3d-parametric-bim-nodes-manager-ok")
