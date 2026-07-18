from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.product import (
    ExtrudeFeature,
    FeatureDefinition,
    FeatureOptions,
    ProductPart,
    Sketch,
    SketchProfile,
    SolidBody,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Existing Body Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Feature Product", "mm", 3)
part = manager.add_part(ProductPart("Feature Part", "Existing Body Mesh", location=Vector3()))
sketch = manager.add_sketch_item(Sketch("Feature Sketch", part.id))
profile = manager.add_sketch_item(SketchProfile("Feature Profile", sketch.id))
body = manager.add_body_item(SolidBody("Main Body", part.id, "Existing Body Mesh"))
feature = manager.add_feature_item(
    ExtrudeFeature(
        "Boss Extrude",
        part.id,
        FeatureDefinition(
            sketch.id,
            profile.id,
            body.id,
            [body.id],
            FeatureOptions("Join", False, "Positive", 25.0, 0.0),
        ),
    )
)

result_entity = manager.feature_manager.apply_feature(feature, workspace)
stats = manager.statistics()
feature_stats = manager.feature_manager.statistics()
body_stats = manager.body_manager.statistics()

assert result_entity is mesh
assert mesh.primitive_type == "extrude"
assert mesh.parameters["operation"] == "Join"
assert mesh.parameters["distance"] == 25.0
assert feature.result.status == "Applied"
assert feature.result.mesh_entity_id == "Existing Body Mesh"
assert body.id in part.body_ids
assert feature.id in body.feature_ids
assert manager.features_for(part) == [feature]
assert manager.bodies_for(part) == [body]
assert manager.feature_tree_for(part).node_ids
assert manager.feature_history_for(part).feature_ids == [feature.id]
assert stats.features == 1
assert stats.bodies == 1
assert feature_stats.features == 1
assert body_stats.bodies == 1

manager.feature_manager.suppress(feature, True)
assert feature.suppressed is True
manager.feature_manager.suppress(feature, False)
assert feature.suppressed is False
manager.feature_manager.rename(feature, "Renamed Extrude")
assert feature.name == "Renamed Extrude"

print("3d-product-feature-foundation-manager-ok")
