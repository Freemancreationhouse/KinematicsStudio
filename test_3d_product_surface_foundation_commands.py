from engine.commands import (
    AddProductPartCommand,
    AddSurfaceBodyCommand,
    AddSurfaceOperationCommand,
    AddProductFeatureCommand,
    ApplyProductFeatureCommand,
    CreateProductDocumentCommand,
    RegenerateProductFeatureCommand,
    SuppressProductFeatureCommand,
)
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    FeatureDefinition,
    FeatureOptions,
    ProductPart,
    SurfaceBody,
    SurfaceOperationMetadata,
    SweepSurfaceFeature,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Command Surface Mesh")
workspace.add_3d_entity(mesh)

workspace.command_manager.execute(CreateProductDocumentCommand(workspace, "Command Surface Product"))
part = ProductPart("Command Surface Part", "Command Surface Mesh")
workspace.command_manager.execute(AddProductPartCommand(workspace, part))

surface_body = SurfaceBody("Command Surface Body", part.id, "Command Surface Mesh")
workspace.command_manager.execute(AddSurfaceBodyCommand(workspace, surface_body))
assert workspace.product_manager.surface_bodies == [surface_body]

surface_feature = SweepSurfaceFeature(
    "Command Sweep Surface",
    part.id,
    FeatureDefinition(
        body_id=surface_body.id,
        target_body_ids=[surface_body.id],
        options=FeatureOptions(distance=4.0),
    ),
)
workspace.command_manager.execute(AddProductFeatureCommand(workspace, surface_feature))
workspace.command_manager.execute(ApplyProductFeatureCommand(workspace, surface_feature))
assert mesh.primitive_type == "sweep surface"
assert surface_feature.surface_result.status == "Applied"

operation = SurfaceOperationMetadata(operation_type="Trim", target_surface_ids=[surface_body.id])
workspace.command_manager.execute(AddSurfaceOperationCommand(workspace, operation))
assert workspace.product_manager.surface_operation_metadata == [operation]

workspace.command_manager.execute(RegenerateProductFeatureCommand(workspace, surface_feature))
assert surface_feature.metadata.status == "Applied"

workspace.command_manager.execute(SuppressProductFeatureCommand(workspace, surface_feature, True))
assert surface_feature.suppressed is True
workspace.command_manager.undo()
assert surface_feature.suppressed is False

print("3d-product-surface-foundation-commands-ok")
