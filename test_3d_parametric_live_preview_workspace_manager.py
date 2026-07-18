from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    PreviewHistory,
    PreviewVersion,
    ProductPart,
    PropertySynchronizationMetadata,
    UpdateCoordinationMetadata,
    ViewportMetadata,
    WorkspaceSyncMetadata,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="Live Preview Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Live Preview Part", "Live Preview Mesh"))
engine = manager.parametric_manager.create_engine("Live Preview Engine")
solver = manager.parametric_manager.create_solver("Live Preview Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Live Preview Graph", engine, solver)
tree = manager.parametric_manager.create_data_tree("Live Preview Data Tree", engine, solver, graph)
cad_library = manager.parametric_manager.create_cad_node_library("Live Preview CAD Bridge", engine, graph, tree)
bim_library = manager.parametric_manager.create_bim_node_library("Live Preview BIM Bridge", engine, graph, tree, cad_library)
manufacturing_library = manager.parametric_manager.create_manufacturing_node_library("Live Preview Manufacturing Bridge", engine, graph, tree, cad_library, bim_library)
ai_library = manager.parametric_manager.create_ai_node_library("Live Preview AI Bridge", engine, graph, tree, cad_library, bim_library, manufacturing_library)
script_library = manager.parametric_manager.create_script_node_library("Live Preview Script Bridge", engine, graph, tree, cad_library, bim_library, manufacturing_library, ai_library)

session = manager.parametric_manager.create_preview_session("Primary Preview Session", engine)
session.context.graph_id = graph.id
session.context.data_tree_id = tree.id
session.context.object_ids.extend([cad_library.id, bim_library.id, manufacturing_library.id, ai_library.id, script_library.id, mesh.name])
request = manager.parametric_manager.create_preview_request(session, "Viewport Refresh Request", "Viewport Refresh")
template = manager.parametric_manager.create_preview_template(session, "Default Preview Template")
history = manager.parametric_manager.add_item(PreviewHistory(session.id, "Created", "Preview metadata created"))
version = manager.parametric_manager.add_item(PreviewVersion(session.id, "1.0", "Initial preview metadata"))
workspace_sync = manager.parametric_manager.create_workspace_synchronization(
    "Workspace Sync",
    engine,
    WorkspaceSyncMetadata(selection_state="Synchronized", property_state="Synchronized", layer_state="Clean", visibility_state="Clean", preview_state="Queued", reference_mappings={"workspace": "Workspace"}),
)
viewport_sync = manager.parametric_manager.create_viewport_synchronization(
    "Viewport Sync",
    engine,
    ViewportMetadata(refresh_requested=True, viewport_dirty=True, view_synchronization="Requested", camera_synchronization="Clean", reference_mappings={"renderer": "Renderer3D"}),
)
property_sync = manager.parametric_manager.create_property_synchronization(
    "Property Sync",
    engine,
    PropertySynchronizationMetadata("Parametric", [session.id, request.id], ["Parameters", "CAD Nodes", "BIM Nodes", "Manufacturing Nodes", "AI Nodes", "Script Nodes"], "Synchronized"),
)
update = manager.parametric_manager.create_update_coordination(
    "Update Coordination",
    engine,
    UpdateCoordinationMetadata("Refresh", request.id, "Dirty", True, {"status": "metadata"}, {"preview_request": request.id}),
)
stats = manager.parametric_manager.statistics()

assert session.id in engine.preview_session_ids
assert workspace_sync.id in engine.workspace_sync_ids
assert viewport_sync.id in engine.viewport_sync_ids
assert property_sync.id in engine.property_sync_ids
assert update.id in engine.update_coordination_ids
assert request.id in session.request_ids
assert template.id in session.template_ids
assert history.id in session.history_ids
assert version.id in session.version_ids
assert session.context.graph_id == graph.id
assert session.context.data_tree_id == tree.id
assert mesh.name in session.context.object_ids
assert workspace_sync.metadata.preview_state == "Queued"
assert viewport_sync.metadata.refresh_requested is True
assert property_sync.metadata.synchronized_groups[-1] == "Script Nodes"
assert update.metadata.refresh_requested is True
assert manager.preview_statistics.sessions == 1
assert manager.preview_statistics.requests == 1
assert manager.preview_statistics.contexts >= 3
assert manager.preview_statistics.workspace_sync_records == 1
assert manager.preview_statistics.viewport_records == 1
assert manager.preview_statistics.property_sync_records == 1
assert manager.preview_statistics.update_records == 1
assert manager.preview_statistics.dirty >= 1
assert stats.engines == 1
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "Live Preview Mesh"

print("3d-parametric-live-preview-workspace-manager-ok")
