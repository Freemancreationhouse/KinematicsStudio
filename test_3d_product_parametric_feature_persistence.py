import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ExtrudeFeature, FeatureDefinition, FeatureOptions, ProductPart, Sketch, SolidBody


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Persisted Parametric Mesh")
workspace.add_3d_entity(mesh)
manager = workspace.product_manager
manager.create_document("Persisted Parametric Product")
part = manager.add_part(ProductPart("Persisted Parametric Part", "Persisted Parametric Mesh"))
sketch = manager.add_sketch_item(Sketch("Persisted Parametric Sketch", part.id))
body = manager.add_body_item(SolidBody("Persisted Parametric Body", part.id, "Persisted Parametric Mesh"))
feature = manager.add_feature_item(
    ExtrudeFeature(
        "Persisted Parametric Extrude",
        part.id,
        FeatureDefinition(sketch.id, "", body.id, [body.id], FeatureOptions("Join", distance=3.0)),
    )
)
manager.feature_editor.edit_feature(feature, distance=11.0, operation="Cut")
manager.dependency_manager.add_edge(sketch, feature, "SketchToFeature")
manager.regeneration_manager.rebuild_feature(feature, workspace)
manager.update_manager.queue_update("Parameter change", feature.id, "Parameter edited")
workspace.selection.select(feature)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "parametric_feature.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager
    restored_feature = restored.features[0]

    assert restored.feature_parameter_sets[0].parameters["distance"] == 11.0
    assert restored.dependency_edges[0].relationship == "SketchToFeature"
    assert restored.regeneration_results[0].status == "Rebuilt"
    assert any(context.event_type == "Parameter change" for context in restored.update_contexts)
    assert restored_feature.selected is True
    assert restored.feature_editor.state_for(restored_feature).dirty is False

print("3d-product-parametric-feature-persistence-ok")
