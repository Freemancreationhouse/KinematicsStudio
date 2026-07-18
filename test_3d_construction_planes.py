from engine.construction_planes import ConstructionPlaneManager
from engine.geometry import Vector3


manager = ConstructionPlaneManager()

assert manager.active.name == "XY Plane"
assert set(manager.names()) == {"XY Plane", "YZ Plane", "ZX Plane"}

custom = manager.create(
    "Custom Plane",
    origin=Vector3(10.0, 20.0, 30.0),
    normal=Vector3(0.0, 0.0, 1.0),
)
assert custom.name == "Custom Plane"

offset = manager.create_offset("XY Plane", "Offset Plane", 25.0)
assert offset.origin.z == 25.0

manager.set_active("Offset Plane")
assert manager.active is offset

offset.visible = False
offset.locked = True
data = manager.to_dict()
restored = ConstructionPlaneManager()
restored.from_dict(data)

assert restored.active.name == "Offset Plane"
assert restored.get("Offset Plane").visible is False
assert restored.get("Offset Plane").locked is True

print("3d-construction-planes-ok")
