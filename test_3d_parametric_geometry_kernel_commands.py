from engine.commands import AddGeometryKernelCommand, ExecuteFeatureGeometryCommand
from engine.geometry import Vector3
from engine.product import ProductPart, SketchLine, SketchPlane, SketchProfile
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
manager.create_document("Geometry Kernel Commands", "mm", 3)
part = manager.add_part(ProductPart("Command Kernel Part", "command-kernel-part", location=Vector3()))
plane = manager.add_sketch_item(SketchPlane("Command Kernel Plane"))
sketch = manager.sketch_manager.create_sketch("Command Kernel Sketch", part, plane)
line = manager.add_sketch_item(SketchLine("Command Kernel Line", sketch.id, Vector3(), Vector3(5.0, 0.0, 0.0)))
profile = manager.add_sketch_item(SketchProfile("Command Kernel Profile", sketch.id, [line.id]))
feature = manager.feature_manager.create_feature("Revolve", part, profile, None, name="Command Kernel Revolve")
kernel = manager.parametric_manager.create_geometry_kernel("Command Kernel")
manager.remove_object(kernel)

workspace.command_manager.execute(AddGeometryKernelCommand(workspace, kernel))
assert kernel in manager.geometry_kernels

workspace.command_manager.undo()
assert kernel not in manager.geometry_kernels

workspace.command_manager.redo()
assert kernel in manager.geometry_kernels

command = ExecuteFeatureGeometryCommand(workspace, feature, kernel)
workspace.command_manager.execute(command)
assert feature.result.status == "Geometry Generated"
assert len(manager.bodies) == 1
assert len(workspace.scene3d.entities()) == 1
assert manager.geometry_results[-1].mesh_synchronized is True

workspace.command_manager.undo()
assert len(manager.bodies) == 0
assert len(workspace.scene3d.entities()) == 0
assert feature.result.status == "Pending"

workspace.command_manager.redo()
assert len(manager.bodies) == 1
assert len(workspace.scene3d.entities()) == 1
assert feature.result.status == "Geometry Generated"

print("3d-parametric-geometry-kernel-commands-ok")
