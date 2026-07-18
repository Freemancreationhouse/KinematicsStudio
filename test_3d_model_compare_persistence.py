import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData, Vector3


def mesh(name, entity_id, position):

    entity = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name=name)
    entity.id = entity_id
    entity.set_transform_state(position=position)

    return entity


app = CADApplication()
workspace = app.workspace
entity = mesh("Persisted Box", "persist-box", Vector3())
workspace.add_3d_entity(entity)
session = workspace.model_compare_manager.create_session("Persisted Compare", workspace)
entity.name = "Persisted Box Changed"
entity.set_transform_state(position=Vector3(30.0, 0.0, 0.0))
workspace.model_compare_manager.rerun(workspace, session)
workspace.selection.select(session.results[0])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "model_compare.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.model_compare_manager.get_session("Persisted Compare")

    assert restored is not None
    assert restored.results
    assert restored.statistics.total == len(restored.results)
    assert any(result.selected for result in restored.results)

print("3d-model-compare-persistence-ok")
