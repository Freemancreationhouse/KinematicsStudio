import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.model_compare import RevisionMetadata


def mesh(name, entity_id, position):

    entity = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name=name)
    entity.id = entity_id
    entity.set_transform_state(position=position)

    return entity


app = CADApplication()
workspace = app.workspace
entity = mesh("Persisted Revision Box", "persisted-revision-box", Vector3())
workspace.add_3d_entity(entity)

revision_a = workspace.revision_manager.capture_revision(
    "Persisted Revision A",
    workspace,
    RevisionMetadata("Reviewer", "Native", "Saved baseline", ("saved",), ()),
)
entity.name = "Persisted Revision Box Changed"
revision_b = workspace.revision_manager.capture_revision("Persisted Revision B", workspace)
session = workspace.revision_manager.compare_revisions(revision_a, revision_b)
workspace.timeline_manager.add_bookmark("Persisted Bookmark", revision_b.id, "Restore this review point")
workspace.selection.select(revision_b)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "revision_history.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored_revision = restored_workspace.revision_manager.get_revision("Persisted Revision B")
    restored_session = restored_workspace.model_compare_manager.get_session(session.id)

    assert restored_revision is not None
    assert restored_revision.selected is True
    assert restored_session is not None
    assert restored_workspace.timeline_manager.timeline.bookmarks
    assert restored_workspace.revision_manager.summary()["revisions"] == 2

print("3d-revision-history-persistence-ok")
