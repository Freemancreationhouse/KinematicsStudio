from engine.commands import (
    AddEdgeModificationCommand,
    AddPatternMetadataCommand,
    AddProductBodyCommand,
    AddProductFeatureCommand,
    AddProductPartCommand,
    ApplyProductFeatureCommand,
    CreateProductDocumentCommand,
    RegenerateProductFeatureCommand,
    SuppressProductFeatureCommand,
)
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import EdgeSelection, FilletFeature, FeatureDefinition, FeatureOptions, PatternDefinition, PatternInstance, PatternFeature, ProductPart, SolidBody
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Command Edge Pattern Mesh")
workspace.add_3d_entity(mesh)
workspace.command_manager.execute(CreateProductDocumentCommand(workspace, "Command Edge Pattern Product"))
part = ProductPart("Command Edge Pattern Part", "Command Edge Pattern Mesh")
workspace.command_manager.execute(AddProductPartCommand(workspace, part))
body = SolidBody("Command Edge Body", part.id, "Command Edge Pattern Mesh")
workspace.command_manager.execute(AddProductBodyCommand(workspace, body))

fillet = FilletFeature("Command Fillet", part.id, FeatureDefinition(body_id=body.id, target_body_ids=[body.id], options=FeatureOptions(distance=2.0), parameters={"radius": 2.0}))
workspace.command_manager.execute(AddProductFeatureCommand(workspace, fillet))
selection = EdgeSelection(body.id, "Command Edge Pattern Mesh", 0, fillet.id)
workspace.command_manager.execute(AddEdgeModificationCommand(workspace, selection))
workspace.command_manager.execute(ApplyProductFeatureCommand(workspace, fillet))
assert mesh.primitive_type == "fillet"
assert len(workspace.product_manager.edge_selections) == 1

pattern_definition = PatternDefinition("Circular Pattern", [fillet.id], [], 3.0, 4)
pattern = PatternFeature("Command Pattern", part.id, FeatureDefinition(body_id=body.id, target_body_ids=[body.id], options=FeatureOptions(distance=3.0)), pattern_definition=pattern_definition)
workspace.command_manager.execute(AddProductFeatureCommand(workspace, pattern))
instance = PatternInstance(pattern.id, fillet.id, "Feature", 0)
workspace.command_manager.execute(AddPatternMetadataCommand(workspace, instance))
workspace.command_manager.execute(RegenerateProductFeatureCommand(workspace, pattern))
assert workspace.product_manager.pattern_instances == [instance]

workspace.command_manager.execute(SuppressProductFeatureCommand(workspace, fillet, True))
assert fillet.suppressed is True
workspace.command_manager.undo()
assert fillet.suppressed is False

print("3d-product-edge-pattern-commands-ok")
