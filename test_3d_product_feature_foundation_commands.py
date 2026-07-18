from engine.commands import (
    AddProductBodyCommand,
    AddProductFeatureCommand,
    AddProductPartCommand,
    ApplyProductFeatureCommand,
    CreateProductDocumentCommand,
    RenameProductFeatureCommand,
    SuppressProductFeatureCommand,
)
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    ExtrudeFeature,
    FeatureDefinition,
    FeatureOptions,
    ProductPart,
    SolidBody,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Command Body Mesh")
workspace.add_3d_entity(mesh)
workspace.command_manager.execute(CreateProductDocumentCommand(workspace, "Command Feature Product"))
part = ProductPart("Command Feature Part", "Command Body Mesh")
workspace.command_manager.execute(AddProductPartCommand(workspace, part))

body = SolidBody("Command Body", part.id, "Command Body Mesh")
feature = ExtrudeFeature(
    "Command Extrude",
    part.id,
    FeatureDefinition(body_id=body.id, target_body_ids=[body.id], options=FeatureOptions("Join", distance=12.0)),
)

workspace.command_manager.execute(AddProductBodyCommand(workspace, body))
workspace.command_manager.execute(AddProductFeatureCommand(workspace, feature))
workspace.command_manager.execute(ApplyProductFeatureCommand(workspace, feature))

assert mesh.parameters["distance"] == 12.0
assert feature.result.status == "Applied"

workspace.command_manager.execute(SuppressProductFeatureCommand(workspace, feature, True))
assert feature.suppressed is True
workspace.command_manager.undo()
assert feature.suppressed is False

workspace.command_manager.execute(RenameProductFeatureCommand(workspace, feature, "Command Extrude Renamed"))
assert feature.name == "Command Extrude Renamed"
workspace.command_manager.undo()
assert feature.name == "Command Extrude"

workspace.command_manager.undo()
workspace.command_manager.undo()
assert feature.suppressed is False

print("3d-product-feature-foundation-commands-ok")
