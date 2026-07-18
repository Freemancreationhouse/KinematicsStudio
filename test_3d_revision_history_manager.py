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
entity = mesh("Revision Box", "revision-box", Vector3())
workspace.add_3d_entity(entity)

revision_a = workspace.revision_manager.capture_revision(
    "Revision A",
    workspace,
    RevisionMetadata("Reviewer", "Native", "Initial coordination revision", ("coordination",), ()),
)

entity.name = "Revision Box Updated"
entity.set_transform_state(position=Vector3(20.0, 0.0, 0.0))
workspace.add_3d_entity(mesh("Added Revision Box", "revision-box-2", Vector3(40.0, 0.0, 0.0)))

revision_b = workspace.revision_manager.capture_revision(
    "Revision B",
    workspace,
    RevisionMetadata("Reviewer", "Native", "Updated coordination revision", ("updated",), ()),
)

session = workspace.revision_manager.compare_revisions(revision_a, revision_b)
types = {result.change_type for result in session.results}

assert "Added" in types
assert "Moved" in types
assert "Renamed" in types
assert revision_b.compare_session_id == session.id
assert revision_b.statistics.change_count == session.statistics.total
assert workspace.revision_manager.jump_to_revision("Revision A") is revision_a
assert workspace.timeline_manager.timeline.entries
assert workspace.revision_manager.search("updated") == [revision_b]
assert "Native" in workspace.revision_manager.grouped_revisions("Source")
assert workspace.revision_manager.summary()["revisions"] == 2

print("3d-revision-history-manager-ok")
