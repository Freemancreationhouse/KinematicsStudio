import os
import tempfile

from engine.cad.application import CADApplication
from engine.geometry import Vector3
from engine.product import ProductPart, SketchLine, SketchPlane, SketchProfile


app = CADApplication()
workspace = app.workspace
manager = workspace.product_manager
manager.create_document("Persisted Feature Framework", "mm", 3)
part = manager.add_part(ProductPart("Persisted Feature Part", "persisted-feature-mesh", location=Vector3()))
plane = manager.add_sketch_item(SketchPlane("Persisted Feature Plane"))
sketch = manager.sketch_manager.create_sketch("Persisted Feature Sketch", part, plane)
line = manager.add_sketch_item(SketchLine("Persisted Feature Line", sketch.id, Vector3(), Vector3(8.0, 0.0, 0.0)))
profile = manager.add_sketch_item(SketchProfile("Persisted Feature Profile", sketch.id, [line.id]))
feature = manager.feature_manager.create_feature("Revolve", part, profile, None, name="Persisted Revolve")
pattern = manager.feature_manager.create_feature("Pattern", part, profile, None, name="Persisted Pattern")
session = manager.feature_manager.create_execution_session(feature)
manager.feature_manager.execute_timeline_metadata(part, session)
manager.feature_manager.rollback_to(feature)
manager.feature_manager.suppress(pattern, True)
workspace.selection.select(session)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "feature_framework.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    restored_session = restored.feature_execution_sessions[0]
    restored_feature = restored.features[0]
    restored_pattern = restored.features[1]

    assert restored_session.selected is True
    assert restored_session.metadata.execution_session_id == ""
    assert restored_feature.execution_state.execution_status == "Completed"
    assert restored_feature.result.updated is False
    assert restored_pattern.suppressed is True
    assert restored_pattern.execution_state.rolled_back is True
    assert restored.feature_orderings[0].rollback_feature_id == restored_feature.id
    assert restored.feature_execution_caches[0].values["geometry"] == "deferred"
    assert len(restored_workspace.scene3d.entities()) == 0
    assert len(restored.bodies) == 0

print("3d-parametric-feature-framework-persistence-ok")
