from engine.commands import (
    AddTimelineBookmarkCommand,
    CaptureRevisionCommand,
    CompareRevisionsCommand,
    UpdateRevisionFiltersCommand,
)
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.model_compare import RevisionMetadata
from engine.workspace.workspace import Workspace


def mesh(name, entity_id, position):

    entity = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name=name)
    entity.id = entity_id
    entity.set_transform_state(position=position)

    return entity


workspace = Workspace()
entity = mesh("Command Revision Box", "command-revision-box", Vector3())
workspace.add_3d_entity(entity)

workspace.command_manager.execute(
    CaptureRevisionCommand(
        workspace,
        "Command Revision A",
        RevisionMetadata("Reviewer", "Native", "Before", ("before",), ()).to_dict(),
    )
)
revision_a = workspace.revision_manager.active_revision
assert revision_a is not None

entity.set_transform_state(position=Vector3(30.0, 0.0, 0.0))
workspace.command_manager.execute(CaptureRevisionCommand(workspace, "Command Revision B"))
revision_b = workspace.revision_manager.active_revision
assert revision_b is not revision_a

workspace.command_manager.execute(CompareRevisionsCommand(workspace, revision_a, revision_b))
assert workspace.model_compare_manager.active_session.results
workspace.command_manager.undo()
assert revision_b.compare_session_id is None
workspace.command_manager.redo()
assert revision_b.compare_session_id == workspace.model_compare_manager.active_session.id

workspace.command_manager.execute(AddTimelineBookmarkCommand(workspace, "Review Point", revision_b.id, "Check this revision"))
assert workspace.timeline_manager.timeline.bookmarks
workspace.command_manager.undo()
assert workspace.timeline_manager.timeline.bookmarks == []

before = dict(workspace.revision_manager.filters)
after = {"search": "Command"}
workspace.command_manager.execute(UpdateRevisionFiltersCommand(workspace, before, after))
assert workspace.revision_manager.filters["search"] == "Command"
workspace.command_manager.undo()
assert workspace.revision_manager.filters == before

workspace.command_manager.undo()
workspace.command_manager.undo()
workspace.command_manager.undo()
assert workspace.revision_manager.revisions == []

print("3d-revision-history-commands-ok")
