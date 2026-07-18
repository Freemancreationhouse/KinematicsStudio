from engine.commands import AddLivePreviewCommand
from engine.product import PreviewRequest, PreviewSession, PreviewTemplate, PropertySynchronization, UpdateCoordination, ViewportSynchronization, WorkspaceSynchronization
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
engine = manager.parametric_manager.create_engine("Command Preview Engine")
session = PreviewSession("Command Preview Session", engine.id)
request = PreviewRequest("Command Preview Request", session.id)
template = PreviewTemplate("Command Preview Template", session.id)
workspace_sync = WorkspaceSynchronization("Command Workspace Sync", engine.id)
viewport_sync = ViewportSynchronization("Command Viewport Sync", engine.id)
property_sync = PropertySynchronization("Command Property Sync", engine.id)
update = UpdateCoordination("Command Update Coordination", engine.id)

for item in (session, request, template, workspace_sync, viewport_sync, property_sync, update):
    workspace.command_manager.execute(AddLivePreviewCommand(workspace, item))

assert manager.preview_sessions == [session]
assert manager.preview_requests == [request]
assert manager.preview_templates == [template]
assert manager.workspace_synchronizations == [workspace_sync]
assert manager.viewport_synchronizations == [viewport_sync]
assert manager.property_synchronizations == [property_sync]
assert manager.update_coordinations == [update]

workspace.command_manager.undo()
assert manager.update_coordinations == []
workspace.command_manager.redo()
assert manager.update_coordinations == [update]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.update_coordinations == []
assert manager.property_synchronizations == []
workspace.command_manager.redo()
workspace.command_manager.redo()
assert manager.property_synchronizations == [property_sync]
assert manager.update_coordinations == [update]

print("3d-parametric-live-preview-workspace-commands-ok")
