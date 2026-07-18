from engine.geometry import Vector3
from engine.references3d import ReferenceManager, ReferenceTransform


manager = ReferenceManager()
model = manager.create_model(
    "Architectural Model",
    "C:/refs/architectural.ifc",
    author="Coordinator",
    source_format="IFC",
    category="Architecture",
    group="Campus",
)
instance = manager.create_instance(
    model,
    ReferenceTransform(Vector3(1.0, 2.0, 3.0), scale=Vector3(2.0, 2.0, 2.0)),
)

assert model.name == "Architectural Model"
assert instance.model_id == model.id
assert manager.statistics()["models"] == 1
assert manager.search("campus") == [model]
assert manager.filter(status="Loaded", category="Architecture") == [model]
assert manager.visible_instances() == [instance]

manager.unload(model)
assert manager.visible_instances() == []
assert manager.statistics()["unloaded"] == 1

manager.reload(model)
manager.isolate(model)
assert manager.visible_instances() == [instance]
manager.clear_isolation()

round_tripped = ReferenceManager()
round_tripped.from_dict(manager.to_dict())

assert round_tripped.models[0].id == model.id
assert round_tripped.instances[0].transform.position.z == 3.0

print("3d-reference-manager-ok")
