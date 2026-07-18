from engine.commands import AddMeasurementCommand, RemoveMeasurementCommand
from engine.geometry import Vector3
from engine.workspace import Workspace


workspace = Workspace("3D Measurement Command Workspace")
measurement = workspace.measurement_manager.point_to_point(Vector3(), Vector3(1.0, 0.0, 0.0))

workspace.command_manager.execute(AddMeasurementCommand(workspace, measurement))
assert measurement in workspace.measurement_manager.measurements
assert workspace.selection.first is measurement

workspace.command_manager.undo()
assert measurement not in workspace.measurement_manager.measurements

workspace.command_manager.redo()
assert measurement in workspace.measurement_manager.measurements

workspace.command_manager.execute(RemoveMeasurementCommand(workspace, measurement))
assert measurement not in workspace.measurement_manager.measurements
workspace.command_manager.undo()
assert measurement in workspace.measurement_manager.measurements

print("3d-measurement-command-ok")
