import tempfile
from pathlib import Path

from engine.entities import PolylineEntity, SplineEntity
from engine.geometry import Vector2
from engine.storage import ProjectSerializer
from engine.workspace import Workspace


workspace = Workspace("Curves")
layer = workspace.create_layer("Curves", "#22AAFF")
workspace.set_current_layer(layer)

polyline = PolylineEntity([
    Vector2(0, 0),
    Vector2(100, 0),
    Vector2(100, 50),
], closed=True)
spline = SplineEntity([
    Vector2(0, 100),
    Vector2(50, 160),
    Vector2(100, 100),
], samples_per_segment=8)

workspace.add_entity(polyline)
workspace.add_entity(spline)

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "curves.ksproj"
    serializer = ProjectSerializer()
    serializer.save(workspace, path)
    loaded = serializer.load(path)

loaded_polyline = next(entity for entity in loaded.entities if isinstance(entity, PolylineEntity))
loaded_spline = next(entity for entity in loaded.entities if isinstance(entity, SplineEntity))

assert loaded_polyline.closed
assert loaded_polyline.count == 3
assert loaded_polyline.layer_name == "Curves"
assert loaded_spline.count == 3
assert loaded_spline.samples_per_segment == 8
assert loaded_spline.layer_name == "Curves"

print("curve-persistence-ok")
