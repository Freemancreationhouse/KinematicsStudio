from engine.commands import (
    AddFeatureExecutionCommand,
    ExecuteProductFeatureMetadataCommand,
    RollbackProductFeatureCommand,
    RollForwardProductFeaturesCommand,
)
from engine.geometry import Vector3
from engine.product import ProductPart, SketchLine, SketchPlane, SketchProfile
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
manager.create_document("Feature Framework Commands", "mm", 3)
part = manager.add_part(ProductPart("Command Feature Part", "command-feature-mesh", location=Vector3()))
plane = manager.add_sketch_item(SketchPlane("Command Feature Plane"))
sketch = manager.sketch_manager.create_sketch("Command Feature Sketch", part, plane)
line = manager.add_sketch_item(SketchLine("Command Feature Line", sketch.id, Vector3(), Vector3(4.0, 0.0, 0.0)))
profile = manager.add_sketch_item(SketchProfile("Command Feature Profile", sketch.id, [line.id]))
feature = manager.feature_manager.create_feature("Extrude", part, profile, None, name="Command Extrude")
second = manager.feature_manager.create_feature("Draft", part, profile, None, name="Command Draft")
session = manager.feature_manager.create_execution_session(feature)
manager.remove_object(session)

add_command = AddFeatureExecutionCommand(workspace, session)
workspace.command_manager.execute(add_command)
assert session in manager.feature_execution_sessions

workspace.command_manager.undo()
assert session not in manager.feature_execution_sessions

workspace.command_manager.redo()
assert session in manager.feature_execution_sessions

execute_command = ExecuteProductFeatureMetadataCommand(workspace, feature, session)
workspace.command_manager.execute(execute_command)
assert feature.execution_state.execution_status == "Completed"
assert feature.result.updated is False

workspace.command_manager.undo()
assert feature.execution_state.execution_status == "Not Executed"

rollback_command = RollbackProductFeatureCommand(workspace, feature)
workspace.command_manager.execute(rollback_command)
assert second.execution_state.rolled_back is True

roll_forward_command = RollForwardProductFeaturesCommand(workspace, part)
workspace.command_manager.execute(roll_forward_command)
assert second.execution_state.rolled_back is False

workspace.command_manager.undo()
assert second.execution_state.rolled_back is True
assert len(workspace.scene3d.entities()) == 0
assert len(manager.bodies) == 0

print("3d-parametric-feature-framework-commands-ok")
