from engine.commands import (
    AddFeatureDependencyCommand,
    EditProductFeatureCommand,
    PropagateProductUpdateCommand,
    RegenerateProductFeatureCommand,
)
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ExtrudeFeature, FeatureDefinition, FeatureOptions, ProductPart, Sketch, SolidBody
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Command Parametric Mesh")
workspace.add_3d_entity(mesh)
manager = workspace.product_manager
manager.create_document("Command Parametric Product")
part = manager.add_part(ProductPart("Command Parametric Part", "Command Parametric Mesh"))
sketch = manager.add_sketch_item(Sketch("Command Parametric Sketch", part.id))
body = manager.add_body_item(SolidBody("Command Parametric Body", part.id, "Command Parametric Mesh"))
feature = manager.add_feature_item(
    ExtrudeFeature(
        "Command Parametric Extrude",
        part.id,
        FeatureDefinition(sketch.id, "", body.id, [body.id], FeatureOptions("Join", distance=4.0)),
    )
)
manager.feature_manager.apply_feature(feature, workspace)

workspace.command_manager.execute(EditProductFeatureCommand(workspace, feature, distance=9.0, operation="Intersect"))
assert feature.definition.options.distance == 9.0
assert feature.definition.options.operation == "Intersect"
assert manager.feature_editor.state_for(feature).dirty is True

workspace.command_manager.execute(AddFeatureDependencyCommand(workspace, sketch, feature, "SketchToFeature"))
assert manager.dependency_statistics.edges == 1 or len(manager.dependency_edges) == 1

workspace.command_manager.execute(PropagateProductUpdateCommand(workspace))
workspace.command_manager.execute(RegenerateProductFeatureCommand(workspace, feature))
assert mesh.parameters["distance"] == 9.0
assert manager.feature_editor.state_for(feature).dirty is False

workspace.command_manager.undo()
assert manager.feature_editor.state_for(feature).dirty is True

print("3d-product-parametric-feature-commands-ok")
