from engine.commands import (
    ActivateSketchCommand,
    AddProductPartCommand,
    AddProductSketchCommand,
    AddSketchConstraintCommand,
    AddSketchDimensionCommand,
    AddSketchGeometryCommand,
    CreateProductDocumentCommand,
)
from engine.geometry import Vector3
from engine.product import Constraint, ProductPart, Sketch, SketchDimension, SketchLine
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(CreateProductDocumentCommand(workspace, "Command Sketch Product"))
part = ProductPart("Command Sketch Part", "mesh-command-sketch")
workspace.command_manager.execute(AddProductPartCommand(workspace, part))

sketch = Sketch("Command Sketch", part.id)
line = SketchLine("Command Line", sketch.id, Vector3(), Vector3(5.0, 0.0, 0.0))
constraint = Constraint("Horizontal", sketch.id, [line.id])
dimension = SketchDimension("Linear", 5.0, "mm", sketch.id, [line.id])

workspace.command_manager.execute(AddProductSketchCommand(workspace, sketch))
workspace.command_manager.execute(AddSketchGeometryCommand(workspace, line))
workspace.command_manager.execute(AddSketchConstraintCommand(workspace, constraint))
workspace.command_manager.execute(AddSketchDimensionCommand(workspace, dimension))
workspace.command_manager.execute(ActivateSketchCommand(workspace, sketch))

assert workspace.product_manager.active_sketch_id == sketch.id
assert workspace.product_manager.geometry_for_sketch(sketch) == [line]
assert workspace.product_manager.constraints_for_sketch(sketch) == [constraint]
assert workspace.product_manager.dimensions_for_sketch(sketch) == [dimension]

workspace.command_manager.undo()
assert workspace.product_manager.active_sketch_id is None
workspace.command_manager.undo()
assert workspace.product_manager.sketch_dimensions == []
workspace.command_manager.redo()
assert workspace.product_manager.sketch_dimensions == [dimension]

print("3d-product-sketch-foundation-commands-ok")
