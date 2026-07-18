from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    DependencyEdge,
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
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Parametric Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Parametric Product", "mm", 3)
part = manager.add_part(ProductPart("Parametric Part", "Parametric Mesh"))
sketch = manager.add_sketch_item(Sketch("Parametric Sketch", part.id))
profile = manager.add_sketch_item(SketchProfile("Parametric Profile", sketch.id))
body = manager.add_body_item(SolidBody("Parametric Body", part.id, "Parametric Mesh"))
feature = manager.add_feature_item(
    ExtrudeFeature(
        "Parametric Extrude",
        part.id,
        FeatureDefinition(sketch.id, profile.id, body.id, [body.id], FeatureOptions("Join", distance=10.0)),
    )
)
manager.feature_manager.apply_feature(feature, workspace)

session = manager.feature_editor.begin_edit(feature)
edited = manager.feature_editor.edit_feature(
    feature,
    distance=18.0,
    angle=5.0,
    direction="Negative",
    operation="Cut",
    merge_result=False,
)
version = manager.feature_editor.snapshot(feature, "Distance edit")
edge = manager.dependency_manager.add_edge(sketch, feature, "SketchToFeature")
edge2 = manager.dependency_manager.add_edge(feature, body, "FeatureToBody")
result = manager.regeneration_manager.rebuild_feature(feature, workspace)

assert session.active is True
assert edited.definition.options.distance == 18.0
assert edited.definition.options.direction == "Negative"
assert edited.definition.options.operation == "Cut"
assert edited.definition.options.merge_result is False
assert version.version == 1
assert isinstance(edge, DependencyEdge)
assert manager.dependency_manager.statistics().edges == 2
assert result.status == "Rebuilt"
assert mesh.parameters["distance"] == 18.0
assert manager.feature_editor.state_for(feature).dirty is False
assert manager.regeneration_manager.statistics().results == 1
assert edge2.relationship == "FeatureToBody"

print("3d-product-parametric-feature-manager-ok")
