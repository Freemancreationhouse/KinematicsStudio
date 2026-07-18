from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import DataTreeHistory, ProductPart
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="Data Tree Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Data Tree Part", "Data Tree Mesh"))
engine = manager.parametric_manager.create_engine("Data Tree Engine")
solver = manager.parametric_manager.create_solver("Data Tree Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Data Tree Graph", engine, solver)
source_node = manager.parametric_manager.create_node(graph, "Source Node")
target_node = manager.parametric_manager.create_node(graph, "Target Node")
tree = manager.parametric_manager.create_data_tree("Primary Data Tree", engine, solver, graph)
root_branch = manager.parametric_manager.create_data_branch(tree, "Root Branch", branch_identifier="{0}")
child_branch = manager.parametric_manager.create_data_branch(tree, "Child Branch", root_branch, "{0;1}")
path = manager.parametric_manager.create_data_path(tree, child_branch, "Child Path", [0, 1])
data_item = manager.parametric_manager.create_data_item(
    tree,
    child_branch,
    path,
    "Length Item",
    "Length",
    {
        "source_node_id": source_node,
        "destination_node_id": target_node,
        "object_id": part,
        "mesh_entity_id": mesh,
    },
)
container = manager.parametric_manager.create_data_container(tree, child_branch, "Length Container", [data_item])
flow = manager.parametric_manager.create_data_flow(tree, data_item, container, "Length Flow")
history = manager.parametric_manager.add_item(DataTreeHistory(tree.id, child_branch.id, data_item.id, flow.id, "Created", "Data tree metadata created"))
stats = manager.parametric_manager.statistics()

assert tree.id in engine.data_tree_ids
assert tree.id in graph.metadata.properties["data_tree_ids"]
assert root_branch.id in tree.branch_ids
assert child_branch.id in tree.branch_ids
assert child_branch.id in root_branch.child_branch_ids
assert path.id in tree.path_ids
assert path.id in child_branch.path_ids
assert data_item.id in tree.item_ids
assert data_item.id in child_branch.item_ids
assert data_item.id in path.item_ids
assert container.id in tree.container_ids
assert flow.id in tree.flow_ids
assert history.id in tree.history_ids
assert history.id in child_branch.history_ids
assert history.id in data_item.history_ids
assert history.id in flow.history_ids
assert data_item.source_node_id == source_node.id
assert data_item.destination_node_id == target_node.id
assert data_item.object_id == part.id
assert data_item.mesh_entity_id == mesh.name
assert manager.data_tree_statistics.trees == 1
assert manager.data_tree_statistics.branches == 2
assert manager.data_tree_statistics.paths == 1
assert manager.data_tree_statistics.items == 1
assert manager.data_tree_statistics.containers == 1
assert manager.data_tree_statistics.flows == 1
assert stats.engines == 1
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "Data Tree Mesh"

print("3d-parametric-data-tree-manager-ok")
