from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.sections import SectionPlane
from engine.workspace import Workspace


workspace = Workspace("3D Section Workspace")
manager = workspace.section_manager

section = manager.create("Cut A", Vector3(), Vector3(1.0, 0.0, 0.0), 200.0)
assert section.name == "Cut A"
assert manager.active is section
assert section in manager.visible_sections()
assert section in manager.enabled_sections()

duplicate = manager.create("Cut A")
assert duplicate.name == "Cut A 1"

mesh = MeshEntity(MeshData.box(10.0, 10.0, 10.0))
workspace.add_3d_entity(mesh)
assert mesh in workspace.visible_3d_entities()

section.origin = Vector3(20.0, 0.0, 0.0)
assert mesh not in workspace.visible_3d_entities()

manager.clipping.clip_toggle = False
assert mesh in workspace.visible_3d_entities()

manager.clipping.clip_toggle = True
manager.clipping.box_enabled = True
manager.clipping.plane_enabled = False
manager.clipping.box_min = Vector3(50.0, 50.0, 50.0)
manager.clipping.box_max = Vector3(60.0, 60.0, 60.0)
assert mesh not in workspace.visible_3d_entities()

plane = SectionPlane("Manual", Vector3(), Vector3(0.0, 0.0, 1.0))
assert len(plane.segments()) == 4
assert plane.signed_distance(Vector3(0.0, 0.0, 5.0)) > 0.0

print("3d-section-manager-ok")
