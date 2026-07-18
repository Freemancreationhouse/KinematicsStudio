import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    FeatureDefinition,
    FeatureOptions,
    ProductPart,
    RevolveFeature,
    Sketch,
    SketchProfile,
    SolidBody,
)


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Persisted Body Mesh")
workspace.add_3d_entity(mesh)
manager = workspace.product_manager
manager.create_document("Persisted Feature Product", "mm", 4)
part = manager.add_part(ProductPart("Persisted Feature Part", "Persisted Body Mesh"))
sketch = manager.add_sketch_item(Sketch("Persisted Feature Sketch", part.id))
profile = manager.add_sketch_item(SketchProfile("Persisted Feature Profile", sketch.id))
body = manager.add_body_item(SolidBody("Persisted Body", part.id, "Persisted Body Mesh"))
feature = manager.add_feature_item(
    RevolveFeature(
        "Persisted Revolve",
        part.id,
        FeatureDefinition(
            sketch.id,
            profile.id,
            body.id,
            [body.id],
            FeatureOptions("New Body", angle=180.0, distance=8.0),
        ),
    )
)
manager.feature_manager.apply_feature(feature, workspace)
workspace.selection.select(feature)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "product_feature.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager
    restored_feature = restored.features[0]
    restored_body = restored.bodies[0]
    restored_mesh = restored.mesh_entity_for_body(restored_body, restored_workspace)

    assert restored_feature.type_name == "RevolveFeature"
    assert restored_feature.definition.options.operation == "New Body"
    assert restored_feature.definition.options.angle == 180.0
    assert restored_feature.result.status == "Applied"
    assert restored_body.feature_ids == [restored_feature.id]
    assert restored_mesh is not None
    assert restored_mesh.primitive_type == "revolve"
    assert restored_feature.selected is True

print("3d-product-feature-foundation-persistence-ok")
