from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ManufacturingNodeHistory, ManufacturingNodeMetadata, ManufacturingNodeVersion, ProductPart
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="Manufacturing Node Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Manufacturing Node Part", "Manufacturing Node Mesh"))
engine = manager.parametric_manager.create_engine("Manufacturing Node Engine")
solver = manager.parametric_manager.create_solver("Manufacturing Node Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Manufacturing Node Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("Manufacturing Node Data Tree", engine, solver, graph)
cad_library = manager.parametric_manager.create_cad_node_library("Manufacturing CAD Bridge", engine, graph, tree)
bim_library = manager.parametric_manager.create_bim_node_library("Manufacturing BIM Bridge", engine, graph, tree, cad_library)
library = manager.parametric_manager.create_manufacturing_node_library("Core Manufacturing Nodes", engine, graph, tree, cad_library, bim_library)

machine_category = manager.parametric_manager.create_manufacturing_node_category(library, "Machine Nodes", "Machine", "Setup")
cam_category = manager.parametric_manager.create_manufacturing_node_category(library, "CAM Operation Nodes", "CAM Operation", "Milling")
fabrication_category = manager.parametric_manager.create_manufacturing_node_category(library, "Digital Fabrication Nodes", "Digital Fabrication", "Fabrication")
information_category = manager.parametric_manager.create_manufacturing_node_category(library, "Manufacturing Information Nodes", "Information", "Data")

machine_node = manager.parametric_manager.create_manufacturing_node_definition(library, machine_category, "Machine Node", "Machine", "Machine")
facing_node = manager.parametric_manager.create_manufacturing_node_definition(
    library,
    cam_category,
    "Facing Node",
    "CAM Operation",
    "Facing",
    ManufacturingNodeMetadata(
        default_parameters={"depth": "metadata"},
        input_definitions=["stock", "tool"],
        output_definitions=["operation"],
        manufacturing_process="Milling",
        machine_type="CNC",
        tool_type="Face Mill",
    ),
)
laser_node = manager.parametric_manager.create_manufacturing_node_definition(library, fabrication_category, "Laser Cutting Node", "Digital Fabrication", "Laser Cutting")
gcode_node = manager.parametric_manager.create_manufacturing_node_definition(library, information_category, "G-Code Node", "Information", "G-Code")

facing_node.data_tree_ids.append(tree.id)
facing_node.cad_node_ids.append(cad_library.id)
facing_node.bim_node_ids.append(bim_library.id)
facing_node.live_solver_id = solver.id
facing_node.product_manager_reference_id = "ProductManager"
facing_node.workspace_reference_id = "Workspace"
facing_node.mesh_entity_id = mesh.name
template = manager.parametric_manager.create_manufacturing_node_template(library, facing_node, "Facing Node Template")
version = manager.parametric_manager.add_item(ManufacturingNodeVersion(facing_node.id, "1.0", "Initial metadata"))
history = manager.parametric_manager.add_item(ManufacturingNodeHistory(facing_node.id, library.id, "Created", "Manufacturing node metadata created"))
stats = manager.parametric_manager.statistics()

assert library.id in engine.manufacturing_node_library_ids
assert library.id in graph.metadata.properties["manufacturing_node_library_ids"]
assert library.id in tree.metadata.properties["manufacturing_node_library_ids"]
assert library.id in cad_library.metadata.properties["manufacturing_node_library_ids"]
assert library.id in bim_library.metadata.properties["manufacturing_node_library_ids"]
assert machine_category.id in library.category_ids
assert cam_category.id in library.category_ids
assert fabrication_category.id in library.category_ids
assert information_category.id in library.category_ids
assert machine_node.id in machine_category.definition_ids
assert facing_node.id in cam_category.definition_ids
assert laser_node.id in fabrication_category.definition_ids
assert gcode_node.id in information_category.definition_ids
assert template.id in library.template_ids
assert version.id in facing_node.version_ids
assert version.id in library.version_ids
assert history.id in facing_node.history_ids
assert history.id in library.history_ids
assert facing_node.data_tree_ids == [tree.id]
assert facing_node.cad_node_ids == [cad_library.id]
assert facing_node.bim_node_ids == [bim_library.id]
assert facing_node.live_solver_id == solver.id
assert facing_node.mesh_entity_id == mesh.name
assert manager.manufacturing_node_statistics.libraries == 1
assert manager.manufacturing_node_statistics.categories == 4
assert manager.manufacturing_node_statistics.definitions == 4
assert manager.manufacturing_node_statistics.machine_nodes == 1
assert manager.manufacturing_node_statistics.cam_operation_nodes == 1
assert manager.manufacturing_node_statistics.fabrication_nodes == 1
assert manager.manufacturing_node_statistics.information_nodes == 1
assert stats.engines == 1
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "Manufacturing Node Mesh"

print("3d-parametric-manufacturing-nodes-manager-ok")
