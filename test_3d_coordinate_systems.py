from engine.coordinate_systems import CoordinateSystemManager
from engine.geometry import Vector3


manager = CoordinateSystemManager()

assert manager.active.name == "WCS"
assert manager.wcs.system_type == "WCS"

ucs = manager.create_ucs(
    "Shop UCS",
    origin=Vector3(10.0, 0.0, 0.0),
    x_axis=Vector3(0.0, 1.0, 0.0),
    y_axis=Vector3(1.0, 0.0, 0.0),
)
manager.activate("Shop UCS")
world = ucs.to_world(Vector3(5.0, 2.0, 0.0))
local = ucs.from_world(world)

assert manager.active is ucs
assert abs(local.x - 5.0) < 0.0001
assert abs(local.y - 2.0) < 0.0001

assert manager.rename("Shop UCS", "Fixture UCS")
assert manager.get("Fixture UCS") is ucs
assert manager.delete("Fixture UCS")
assert manager.active.name == "WCS"

manager.grid_spacing = 25.0
manager.grid_subdivisions = 4
manager.grid_visible = False
data = manager.to_dict()
restored = CoordinateSystemManager()
restored.from_dict(data)

assert restored.grid_spacing == 25.0
assert restored.grid_subdivisions == 4
assert restored.grid_visible is False

print("3d-coordinate-systems-ok")
