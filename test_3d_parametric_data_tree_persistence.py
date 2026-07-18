import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import DataTreeHistory, ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 2.0, 3.0), name="Persisted Data Tree Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Persisted Data Tree Part", "Persisted Data Tree Mesh"))
engine = manager.parametric_manager.create_engine("Persisted Data Tree Engine")
solver = manager.parametric_manager.create_solver("Persisted Data Tree Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Persisted Data Tree Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("Persisted Data Tree", engine, solver, graph)
branch = manager.parametric_manager.create_data_branch(tree, "Persisted Branch", branch_identifier="{2}")
path = manager.parametric_manager.create_data_path(tree, branch, "Persisted Path", [2])
data_item = manager.parametric_manager.create_data_item(tree, branch, path, "Persisted Item", "Object Reference", {"object_id": part, "mesh_entity_id": mesh})
container = manager.parametric_manager.create_data_container(tree, branch, "Persisted Container", [data_item])
flow = manager.parametric_manager.create_data_flow(tree, data_item, container, "Persisted Flow")
manager.parametric_manager.add_item(DataTreeHistory(tree.id, branch.id, data_item.id, flow.id, "Persisted", "Persisted data tree metadata"))
workspace.selection.select(tree)

with tempfile.TemporaryDirectory() as folder:
    path_name = os.path.join(folder, "data_tree.ksproj")
    app.save_project(path_name)

    opened = CADApplication()
    restored_workspace = opened.open_project(path_name)
    restored = restored_workspace.product_manager

    assert restored.data_trees[0].name == "Persisted Data Tree"
    assert restored.data_trees[0].selected is True
    assert restored.data_trees[0].branch_ids == [branch.id]
    assert restored.data_trees[0].item_ids == [data_item.id]
    assert restored.data_trees[0].flow_ids == [flow.id]
    assert restored.data_branches[0].branch_identifier == "{2}"
    assert restored.data_paths[0].path_segments == [2]
    assert restored.data_items[0].object_id == part.id
    assert restored.data_items[0].mesh_entity_id == mesh.name
    assert restored.data_containers[0].item_ids == [data_item.id]
    assert restored.data_flows[0].name == "Persisted Flow"
    assert restored.data_tree_statistics.trees == 1
    assert restored.data_tree_statistics.branches == 1
    assert restored.data_tree_statistics.items == 1
    assert restored.parts[0].mesh_entity_id == part.mesh_entity_id
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-data-tree-persistence-ok")
