from engine.commands import AddParametricObjectCommand
from engine.product import (
    ParametricContext,
    ParametricDocument,
    ParametricEngine,
    ParametricSession,
    ParametricWorkspace,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager

engine = ParametricEngine("Command Parametric Engine")
document = ParametricDocument("Command Parametric Document", engine.id)
workspace_record = ParametricWorkspace("Command Parametric Workspace", engine.id, document.id)
session = ParametricSession("Command Parametric Session", engine.id, document.id)
context = ParametricContext(reference_ids=[document.id, session.id])

for item in (engine, document, workspace_record, session, context):
    workspace.command_manager.execute(AddParametricObjectCommand(workspace, item))

assert manager.parametric_engines == [engine]
assert manager.parametric_documents == [document]
assert manager.parametric_workspaces == [workspace_record]
assert manager.parametric_sessions == [session]
assert manager.parametric_contexts == [context]
assert document.id in engine.document_ids
assert workspace_record.id in engine.workspace_ids
assert session.id in engine.session_ids

workspace.command_manager.undo()
assert manager.parametric_contexts == []
workspace.command_manager.redo()
assert manager.parametric_contexts == [context]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.parametric_contexts == []
assert manager.parametric_sessions == []
assert manager.parametric_workspaces == [workspace_record]
workspace.command_manager.undo()
assert manager.parametric_workspaces == []
workspace.command_manager.redo()
workspace.command_manager.redo()
assert manager.parametric_workspaces == [workspace_record]
assert manager.parametric_sessions == [session]
workspace.command_manager.redo()
assert manager.parametric_contexts == [context]

print("3d-parametric-engine-commands-ok")
