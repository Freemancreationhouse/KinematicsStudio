import os
import tempfile

from engine.cad.application import CADApplication
from engine.geometry import Vector3
from engine.product import ProductPart, SketchLine, SketchPlane, SketchProfile


app = CADApplication()
workspace = app.workspace
manager = workspace.product_manager
manager.create_document("Persisted Geometry Kernel", "mm", 3)
part = manager.add_part(ProductPart("Persisted Kernel Part", "persisted-kernel-part", location=Vector3()))
plane = manager.add_sketch_item(SketchPlane("Persisted Kernel Plane"))
sketch = manager.sketch_manager.create_sketch("Persisted Kernel Sketch", part, plane)
line = manager.add_sketch_item(SketchLine("Persisted Kernel Line", sketch.id, Vector3(), Vector3(7.0, 0.0, 0.0)))
profile = manager.add_sketch_item(SketchProfile("Persisted Kernel Profile", sketch.id, [line.id]))
feature = manager.feature_manager.create_feature("Sweep", part, profile, None, name="Persisted Kernel Sweep")
kernel = manager.parametric_manager.create_geometry_kernel("Persisted Kernel")
result = manager.parametric_manager.generate_feature_geometry(feature, workspace, kernel)
workspace.selection.select(kernel)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "geometry_kernel.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager
    restored_kernel = restored.geometry_kernels[0]
    restored_result = restored.geometry_results[-1]
    restored_body = restored.bodies[0]
    restored_mesh = restored.mesh_entity_for_body(restored_body, restored_workspace)
    restored_topology = restored.parametric_manager.brep_topology_for(restored_result.topology_id)

    assert restored_kernel.selected is True
    assert restored_result.id == result.id
    assert restored_result.status == "Completed"
    assert restored_body.mesh_entity_id == (getattr(restored_mesh, "id", "") or restored_mesh.name)
    assert restored_mesh.primitive_type == "sweep"
    assert restored_topology.validation_status == "Valid"
    assert restored.features[0].result.status == "Geometry Generated"
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-geometry-kernel-persistence-ok")
