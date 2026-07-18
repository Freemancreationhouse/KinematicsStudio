from engine.commands import (
    AddConstructionGeometryCommand,
    AddProductCurveCommand,
    AddProductPartCommand,
    AddReferenceGeometryCommand,
    CreateProductDocumentCommand,
)
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    ConstructionAxis,
    CurveDefinition,
    ProductPart,
    ReferencePlane,
    SplineCurve,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="Command Curve Mesh")
workspace.add_3d_entity(mesh)

workspace.command_manager.execute(CreateProductDocumentCommand(workspace, "Command Curve Product"))
part = ProductPart("Command Curve Part", "Command Curve Mesh")
workspace.command_manager.execute(AddProductPartCommand(workspace, part))

curve = SplineCurve("Command Spline", part.id, CurveDefinition(part.id, mesh_entity_ids=["Command Curve Mesh"]))
workspace.command_manager.execute(AddProductCurveCommand(workspace, curve))
assert workspace.product_manager.curves == [curve]
assert part.curve_ids == [curve.id]

reference = ReferencePlane("Command Offset Plane", part.id, [curve.id])
workspace.command_manager.execute(AddReferenceGeometryCommand(workspace, reference))
assert workspace.product_manager.reference_geometry == [reference]
assert part.reference_geometry_ids == [reference.id]

construction = ConstructionAxis("Command Construction Axis", part.id, [reference.id])
workspace.command_manager.execute(AddConstructionGeometryCommand(workspace, construction))
assert workspace.product_manager.construction_geometry == [construction]
assert part.construction_ids == [construction.id]

workspace.command_manager.undo()
assert workspace.product_manager.construction_geometry == []
workspace.command_manager.undo()
assert workspace.product_manager.reference_geometry == []
workspace.command_manager.undo()
assert workspace.product_manager.curves == []

print("3d-product-curve-reference-commands-ok")
