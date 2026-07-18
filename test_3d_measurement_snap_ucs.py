from engine.geometry import Vector3
from engine.workspace import Workspace


workspace = Workspace("3D Measurement Snap UCS Workspace")
workspace.coordinate_system_manager.create_ucs("Shifted", origin=Vector3(10.0, 0.0, 0.0))
workspace.coordinate_system_manager.activate("Shifted")

readout = workspace.measurement_manager.coordinate_readout(
    Vector3(15.0, 5.0, 0.0),
    workspace.coordinate_system_manager.active,
)
assert readout.result.value == {"x": 5.0, "y": 5.0, "z": 0.0}

workspace.snap_manager3d.active_snap = type("Snap", (), {"point": Vector3(15.0, 5.0, 0.0)})()
snap_readout = workspace.measurement_manager.coordinate_readout(
    workspace.snap_manager3d.active_snap.point,
    workspace.coordinate_system_manager.active,
)
assert snap_readout.result.value["x"] == 5.0

print("3d-measurement-snap-ucs-ok")
