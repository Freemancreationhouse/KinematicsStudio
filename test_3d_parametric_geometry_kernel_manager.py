from engine.geometry import Vector3
from engine.product import ProductPart, SketchLine, SketchPlane, SketchProfile
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
manager.create_document("Geometry Kernel Product", "mm", 3)
part = manager.add_part(ProductPart("Geometry Kernel Part", "geometry-kernel-part", location=Vector3()))
plane = manager.add_sketch_item(SketchPlane("Geometry Kernel Plane"))
sketch = manager.sketch_manager.create_sketch("Geometry Kernel Sketch", part, plane)
line = manager.add_sketch_item(SketchLine("Geometry Kernel Line", sketch.id, Vector3(), Vector3(10.0, 0.0, 0.0)))
profile = manager.add_sketch_item(SketchProfile("Geometry Kernel Profile", sketch.id, [line.id]))
feature = manager.feature_manager.create_feature("Extrude", part, profile, None, name="Kernel Extrude")

engine = manager.parametric_manager.create_engine("Kernel Parametric Engine")
execution = manager.parametric_manager.create_execution_engine("Kernel Execution Engine", engine)
kernel = manager.parametric_manager.create_geometry_kernel("Kernel Subsystem", engine, execution)
result = manager.parametric_manager.generate_feature_geometry(feature, workspace, kernel)

body = manager.body_for(result.body_id)
mesh = manager.mesh_entity_for_body(body, workspace)
topology = manager.parametric_manager.brep_topology_for(result.topology_id)

assert kernel in manager.geometry_kernels
assert kernel.id in engine.geometry_kernel_ids
assert result.status == "Completed"
assert feature.result.status == "Geometry Generated"
assert feature.result.updated is True
assert body is not None
assert mesh is not None
mesh_id = getattr(mesh, "id", "") or mesh.name
assert body.mesh_entity_id == mesh_id
assert mesh.primitive_type == "extrude"
assert topology.validation_status == "Valid"
assert len(topology.vertex_ids) == len(mesh.mesh_data.vertices)
assert len(topology.edge_ids) == len(mesh.mesh_data.edges)
assert len(topology.face_ids) == len(mesh.mesh_data.faces)
assert len(topology.solid_ids) == 1
assert len(topology.body_ids) == 1
assert result.mesh_synchronized is True
assert manager.geometry_statistics.kernels == 1
assert manager.geometry_statistics.meshes_synchronized == 1
assert len(workspace.scene3d.entities()) == 1
assert not hasattr(manager, "geometry_manager")
assert not hasattr(manager, "kernel_manager")

print("3d-parametric-geometry-kernel-manager-ok")
