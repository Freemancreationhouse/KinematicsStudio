from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ManufacturingMetrics, ProductPart, ValidationError, ValidationWarning
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(16.0, 10.0, 4.0), name="Manufacturing Job Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Manufacturing Job Product")
part = manager.add_part(ProductPart("Manufacturing Job Part", "Manufacturing Job Mesh"))
cam_document = manager.cam_manager.create_document("Manufacturing Job CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Manufacturing Job CAM Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(cam_job, [part], "Box", name="Manufacturing Job Setup")
tool_library = manager.tool_library_manager.create_library("Manufacturing Job Tools")
machine_library = manager.machine_library_manager.create_library("Manufacturing Job Machines")
machine = manager.machine_library_manager.create_machine("Router", machine_library, "Manufacturing Router")
machine_profile = manager.machine_library_manager.create_profile(machine, cam_job, tool_library=tool_library, setup=setup, name="Manufacturing Machine Profile")
slice_profile = manager.slicer_manager.create_profile("Manufacturing Slice Profile", machine_profile, layer_count=24)
slice_job = manager.slicer_manager.create_job(cam_job, slice_profile, "Manufacturing Slice Job")
simulation_profile = manager.simulation_manager.create_profile("Generic", "Manufacturing Simulation Profile", machine_profile=machine_profile, setup=setup, ready=True)
simulation_job = manager.simulation_manager.create_job(cam_job, slice_job, simulation_profile, "Manufacturing Simulation Job")
stock_library = manager.nesting_manager.create_stock_library("Manufacturing Stock")
stock_profile = manager.nesting_manager.create_stock_profile(stock_library, "Manufacturing Sheet", "Sheet Stock", 1200.0, 800.0, 12.0)
nesting_profile = manager.nesting_manager.create_profile("Manufacturing Nest Profile", [stock_profile], machine_profile)
nesting_job = manager.nesting_manager.create_job(cam_job, nesting_profile, "Manufacturing Nesting Job")

profile = manager.manufacturing_job_manager.create_profile("Production Profile", [cam_job, slice_job, simulation_job, nesting_job])
job = manager.manufacturing_job_manager.create_job(
    "Production Job",
    cam_job,
    slice_job,
    simulation_job,
    nesting_job,
    profile,
    group="Batch L",
    priority="High",
    status="Ready",
)
collection = manager.manufacturing_job_manager.create_collection("Production Collection", [job])
validation_profile = manager.manufacturing_validation_manager.create_profile("Production Validation Profile", [machine_profile, tool_library, stock_profile])
validation_result = manager.manufacturing_validation_manager.create_result(
    validation_profile,
    job,
    "Ready",
    [ValidationWarning("Stock assignment review", [stock_profile.id]), ValidationError("Post processor assignment pending", [cam_job.id])],
)
setup_sheet = manager.manufacturing_job_manager.create_setup_sheet(
    job,
    setup,
    machine_profile,
    tools=[],
    materials=[],
    fixtures=[],
    operations=[],
    name="Production Setup Sheet",
    operator_notes="Verify clamps before run",
    estimated_time=45.0,
)
dashboard = manager.manufacturing_job_manager.create_dashboard(
    "Production Dashboard",
    [job],
    ManufacturingMetrics(completed_jobs=0, pending_jobs=0, ready_jobs=1, warning_jobs=0, estimated_time=45.0),
)
browser = manager.manufacturing_job_manager.create_browser("Manufacturing Browser")
queue = manager.manufacturing_job_manager.create_queue("Production Queue")
history = manager.manufacturing_job_manager.create_history("Job History")
report = manager.manufacturing_job_manager.create_report("Production", job, [setup_sheet, validation_result], "Production Report")
readiness = manager.manufacturing_job_manager.create_report("Readiness", job, [validation_result], "Readiness Report")
shop_doc = manager.manufacturing_job_manager.create_report("Shop Floor", job, [setup_sheet], "Shop Floor Packet")
stats = manager.manufacturing_job_manager.statistics()

assert stats.jobs == 1
assert stats.collections == 1
assert stats.profiles == 1
assert stats.enabled_jobs == 1
assert stats.ready_jobs == 1
assert job.cam_job_id == cam_job.id
assert job.slice_job_id == slice_job.id
assert job.simulation_job_id == simulation_job.id
assert job.nesting_job_id == nesting_job.id
assert job.id in profile.reference_ids
assert collection.job_ids == [job.id]
assert validation_result.profile_id == validation_profile.id
assert validation_result.job_id == job.id
assert len(validation_result.issues) == 2
assert setup_sheet.manufacturing_job_id == job.id
assert setup_sheet.machine_setup.machine_profile_id == machine_profile.id
assert setup_sheet.operation_summary.estimated_time == 45.0
assert dashboard.metrics.ready_jobs == 1
assert browser in manager.manufacturing_browsers
assert queue in manager.production_queues
assert history in manager.job_histories
assert report in manager.product_reports
assert readiness in manager.product_reports
assert shop_doc in manager.product_reports
assert len(manager.dependency_edges) >= 15
assert len(workspace.scene3d.entities()) == 1

print("3d-cam-manufacturing-job-manager-ok")
