from engine.entities import Line3D, MeshEntity
from engine.geometry import MeshData, Vector3
from engine.workspace import Workspace


workspace = Workspace("3D Collection Workspace")
mesh = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name="Box A")
line = Line3D(Vector3(), Vector3(10.0, 0.0, 0.0), name="Line A")
workspace.add_3d_entity(mesh)
workspace.add_3d_entity(line)

manager = workspace.scene_collection_manager
parent = manager.create("Parent")
child = manager.create("Child", parent=parent)

assert child.parent_id == parent.id
assert manager.children(parent) == [child]

manager.move_entity(mesh, parent)
manager.move_entity(line, child)
assert manager.entity_collection(mesh) is parent
assert manager.entity_collection(line) is child

parent.visible = False
assert mesh not in workspace.visible_3d_entities()
assert line not in workspace.visible_3d_entities()

parent.visible = True
child.locked = True
assert manager.entity_locked(line) is True

parent.isolated = True
assert mesh in workspace.visible_3d_entities()
assert line not in workspace.visible_3d_entities()

data = manager.to_dict()
restored = Workspace("Restored Collection Workspace").scene_collection_manager
restored.from_dict(data)
assert restored.get("Parent") is not None
assert restored.get("Child").parent_id == restored.get("Parent").id

print("3d-scene-collections-ok")
