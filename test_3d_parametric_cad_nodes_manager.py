from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import CADNodeHistory, CADNodeMetadata, CADNodeVersion, ProductPart
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="CAD Node Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("CAD Node Part", "CAD Node Mesh"))
engine = manager.parametric_manager.create_engine("CAD Node Engine")
solver = manager.parametric_manager.create_solver("CAD Node Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("CAD Node Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("CAD Node Data Tree", engine, solver, graph)
library = manager.parametric_manager.create_cad_node_library("Core CAD Nodes", engine, graph, tree)
sketch_category = manager.parametric_manager.create_cad_node_category(library, "Sketch Nodes", "Sketch")
feature_category = manager.parametric_manager.create_cad_node_category(library, "Feature Nodes", "Feature")
point_node = manager.parametric_manager.create_cad_node_definition(library, sketch_category, "Point Node", "Sketch", "Point", CADNodeMetadata(input_definitions=["x", "y", "z"], output_definitions=["point"], parameter_definitions=["position"], category="Sketch", subcategory="Point"))
line_node = manager.parametric_manager.create_cad_node_definition(library, sketch_category, "Line Node", "Sketch", "Line")
extrude_node = manager.parametric_manager.create_cad_node_definition(library, feature_category, "Extrude Node", "Feature", "Extrude")
fillet_node = manager.parametric_manager.create_cad_node_definition(library, feature_category, "Fillet Node", "Feature", "Fillet")
extrude_node.data_tree_ids.append(tree.id)
extrude_node.live_solver_id = solver.id
extrude_node.product_manager_reference_id = "ProductManager"
extrude_node.workspace_reference_id = "Workspace"
extrude_node.mesh_entity_id = mesh.name
template = manager.parametric_manager.create_cad_node_template(library, extrude_node, "Extrude Template")
version = manager.parametric_manager.add_item(CADNodeVersion(extrude_node.id, "1.0", "Initial metadata"))
history = manager.parametric_manager.add_item(CADNodeHistory(extrude_node.id, library.id, "Created", "CAD node metadata created"))
stats = manager.parametric_manager.statistics()

assert library.id in engine.cad_node_library_ids
assert library.id in graph.metadata.properties["cad_node_library_ids"]
assert library.id in tree.metadata.properties["cad_node_library_ids"]
assert sketch_category.id in library.category_ids
assert feature_category.id in library.category_ids
assert point_node.id in library.definition_ids
assert line_node.id in library.definition_ids
assert extrude_node.id in library.definition_ids
assert fillet_node.id in library.definition_ids
assert point_node.id in sketch_category.definition_ids
assert extrude_node.id in feature_category.definition_ids
assert template.id in library.template_ids
assert version.id in extrude_node.version_ids
assert version.id in library.version_ids
assert history.id in extrude_node.history_ids
assert history.id in library.history_ids
assert extrude_node.data_tree_ids == [tree.id]
assert extrude_node.live_solver_id == solver.id
assert extrude_node.mesh_entity_id == mesh.name
assert manager.cad_node_statistics.libraries == 1
assert manager.cad_node_statistics.categories == 2
assert manager.cad_node_statistics.definitions == 4
assert manager.cad_node_statistics.sketch_nodes == 2
assert manager.cad_node_statistics.feature_nodes == 2
assert stats.engines == 1
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "CAD Node Mesh"

print("3d-parametric-cad-nodes-manager-ok")
