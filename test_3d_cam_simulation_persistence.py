import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart, WarningMetadata


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(9.0, 7.0, 3.0), name="Persisted Simulation Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Simulation Product")
part = manager.add_part(ProductPart("Persisted Simulation Part", "Persisted Simulation Mesh"))
cam_document = manager.cam_manager.create_document("Persisted Simulation CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Persisted Simulation CAM Job", [part])
slice_profile = manager.slicer_manager.create_profile("Persisted Simulation Slice Profile", layer_count=50)
slice_job = manager.slicer_manager.create_job(cam_job, slice_profile, "Persisted Simulation Slice Job")
warning = WarningMetadata("Info", "Metadata-only warning", [part.id])
profile = manager.simulation_manager.create_profile("Generic", "Persisted Simulation Profile", warnings=[warning], ready=True, estimated_runtime=1800.0)
job = manager.simulation_manager.create_job(cam_job, slice_job, profile, "Persisted Simulation Job", result_status="Ready")
workspace.selection.select(profile)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "cam_simulation.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager
    restored_profile = restored.simulation_profiles[0]
    restored_job = restored.simulation_jobs[0]

    assert restored_profile.name == "Persisted Simulation Profile"
    assert restored_profile.validation.warnings[0].message == "Metadata-only warning"
    assert restored_profile.validation.readiness.ready is True
    assert restored_profile.estimate.estimated_runtime == 1800.0
    assert restored_profile.selected is True
    assert restored_job.cam_job_id == restored.cam_jobs[0].id
    assert restored_job.slice_job_id == restored.slice_jobs[0].id
    assert restored_job.result.status == "Ready"
    assert restored.simulation_statistics.jobs == 1
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-cam-simulation-persistence-ok")
