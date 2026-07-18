import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart, PropertySynchronizationMetadata, UpdateCoordinationMetadata, ViewportMetadata, WorkspaceSyncMetadata


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 2.0, 3.0), name="Persisted Live Preview Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Persisted Live Preview Part", "Persisted Live Preview Mesh"))
engine = manager.parametric_manager.create_engine("Persisted Preview Engine")
session = manager.parametric_manager.create_preview_session("Persisted Preview Session", engine)
request = manager.parametric_manager.create_preview_request(session, "Persisted Preview Request", "Property Refresh")
template = manager.parametric_manager.create_preview_template(session, "Persisted Preview Template")
workspace_sync = manager.parametric_manager.create_workspace_synchronization("Persisted Workspace Sync", engine, WorkspaceSyncMetadata(selection_state="Synchronized", preview_state="Queued"))
viewport_sync = manager.parametric_manager.create_viewport_synchronization("Persisted Viewport Sync", engine, ViewportMetadata(refresh_requested=True, viewport_dirty=True))
property_sync = manager.parametric_manager.create_property_synchronization("Persisted Property Sync", engine, PropertySynchronizationMetadata("Workspace", [session.id], ["Parameters", "Script Nodes"], "Synchronized"))
update = manager.parametric_manager.create_update_coordination("Persisted Update Coordination", engine, UpdateCoordinationMetadata("Refresh", request.id, "Dirty", True))
workspace.selection.select(session)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "live_preview_workspace.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.preview_sessions[0].name == session.name
    assert restored.preview_sessions[0].selected is True
    assert restored.preview_requests[0].request_type == "Property Refresh"
    assert restored.preview_templates[0].name == template.name
    assert restored.workspace_synchronizations[0].metadata.preview_state == "Queued"
    assert restored.viewport_synchronizations[0].metadata.refresh_requested is True
    assert restored.property_synchronizations[0].metadata.synchronized_groups == ["Parameters", "Script Nodes"]
    assert restored.update_coordinations[0].metadata.target_id == update.metadata.target_id
    assert restored.preview_statistics.sessions == 1
    assert restored.preview_statistics.workspace_sync_records == 1
    assert restored.parts[0].mesh_entity_id == part.mesh_entity_id
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-live-preview-workspace-persistence-ok")
