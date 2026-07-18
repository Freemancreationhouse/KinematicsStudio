import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.workspace import Workspace


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace("Gizmo Workspace")
entity = MeshEntity(MeshData.box(50, 50, 50))
workspace.add_3d_entity(entity)
workspace.selection.select(entity)

gizmo = workspace.transform_gizmo
origin = gizmo.origin_for_selection(workspace.selection.selected)
segments = gizmo.axis_segments(origin)
assert set(segments.keys()) == {"X", "Y", "Z"}

gizmo.set_mode("rotate")
assert gizmo.mode == "rotate"
gizmo.set_mode("scale")
assert gizmo.mode == "scale"
gizmo.set_mode("translate")
assert gizmo.mode == "translate"

ray = workspace.scene3d.entities()[0].bounding_sphere.center
screen_ray = type("Ray", (), {
    "origin": origin,
    "direction": (segments["X"][1] - origin).normalized(),
    "point_at": lambda self, distance: self.origin + self.direction * distance,
})()
axis = gizmo.pick_axis(screen_ray, origin, tolerance=20.0)
assert axis == "X"
assert gizmo.highlighted_axis == "X"

data = gizmo.to_dict()
workspace.transform_gizmo.from_dict(data)
assert workspace.transform_gizmo.mode == "translate"

print("3d-transform-gizmo-ok")
