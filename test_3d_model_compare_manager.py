from engine.entities.entity3d import MeshEntity
from engine.geometry import Matrix4, MeshData, Vector3
from engine.workspace.workspace import Workspace


def mesh(name, entity_id, position=None, size=10.0):

    entity = MeshEntity(MeshData.box(size, size, size), name=name)
    entity.id = entity_id

    if position is not None:
        entity.set_transform_state(position=position)

    return entity


workspace = Workspace()
original = mesh("Original Box", "box-1", Vector3(0.0, 0.0, 0.0))
workspace.add_3d_entity(original)

session = workspace.model_compare_manager.create_session("Baseline", workspace)
original.name = "Renamed Box"
original.layer_name = "Changed Layer"
original.set_transform_state(position=Vector3(25.0, 0.0, 0.0))
original.mesh_data = MeshData.box(12.0, 10.0, 10.0)
workspace.add_3d_entity(mesh("Added Box", "box-2", Vector3(50.0, 0.0, 0.0)))

workspace.model_compare_manager.rerun(workspace, session)
types = {result.change_type for result in session.results}

assert "Added" in types
assert "Renamed" in types
assert "Moved" in types
assert "Layer Changed" in types
assert "Modified" in types
assert "Geometry Placeholder" in types
assert session.statistics.added == 1
assert session.statistics.renamed == 1

workspace.model_compare_manager.settings.search = "renamed"
filtered = workspace.model_compare_manager.filtered_results(session.results)
assert filtered
assert all("renamed" in result.name.lower() or "renamed" in result.description.lower() for result in filtered)

groups = workspace.model_compare_manager.grouped_results("Change Type")
assert "Added" in groups

print("3d-model-compare-manager-ok")
