import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ManufacturingMetrics, ProductPart, ValidationWarning


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(9.0, 7.0, 3.0), name="Persisted Manufacturing Job Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Manufacturing Job Product")
part = manager.add_part(ProductPart("Persisted Manufacturing Job Part", "Persisted Manufacturing Job Mesh"))
cam_document = manager.cam_manager.create_document("Persisted Manufacturing Job CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Persisted Manufacturing Job CAM Job", [part])
profile = manager.manufacturing_job_manager.create_profile("Persisted Job Profile", [cam_job])
job = manager.manufacturing_job_manager.create_job("Persisted Job", cam_job=cam_job, profile=profile, status="Ready")
validation_profile = manager.manufacturing_validation_manager.create_profile("Persisted Validation Profile", [cam_job])
validation_result = manager.manufacturing_validation_manager.create_result(validation_profile, job, "Ready", [ValidationWarning("Metadata warning", [cam_job.id])])
sheet = manager.manufacturing_job_manager.create_setup_sheet(job, name="Persisted Setup Sheet", operator_notes="Persisted notes")
dashboard = manager.manufacturing_job_manager.create_dashboard("Persisted Dashboard", [job], ManufacturingMetrics(ready_jobs=1))
report = manager.manufacturing_job_manager.create_report("Production", job, [sheet, validation_result], "Persisted Production Report")
workspace.selection.select(job)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "manufacturing_job.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.manufacturing_jobs[0].name == "Persisted Job"
    assert restored.manufacturing_jobs[0].cam_job_id == restored.cam_jobs[0].id
    assert restored.manufacturing_jobs[0].selected is True
    assert restored.manufacturing_job_profiles[0].reference_ids[-1] == restored.manufacturing_jobs[0].id
    assert restored.manufacturing_validation_profiles[0].name == "Persisted Validation Profile"
    assert restored.manufacturing_validation_results[0].issues[0].message == "Metadata warning"
    assert restored.setup_sheets[0].operator_notes == "Persisted notes"
    assert restored.manufacturing_dashboards[0].metrics.ready_jobs == 1
    assert restored.product_reports[0].type_name == "ProductionReport"
    assert restored.manufacturing_job_statistics.jobs == 1
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-cam-manufacturing-job-persistence-ok")
