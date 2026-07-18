from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import EngineeringMaterial, OperationParameters, ProductPart, SolidBody
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(6.0, 4.0, 2.0), name="CAM Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("CAM Product")
part = manager.add_part(ProductPart("CAM Part", "CAM Mesh"))
body = manager.add_body_item(SolidBody("CAM Body", part.id, mesh.name))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("CAM Aluminium", "Aluminium"))

cam_document = manager.cam_manager.create_document("CAM Document")
job = manager.cam_manager.create_job(cam_document, "Roughing Job", [part, body])
setup = manager.manufacturing_setup_manager.create_setup(job, [part, body], "Box", material, "Setup 1")

operation_types = [
    "Facing",
    "Pocket",
    "Contour",
    "Drill",
    "Adaptive",
    "Parallel",
    "Waterline",
    "Laser",
    "Plasma",
    "Router",
    "3D Printing",
]
operations = [
    manager.operation_manager.create_operation(
        job,
        setup,
        operation_type,
        [part],
        parameters=OperationParameters(
            tool_id=f"T{index + 1}",
            feed_rate=100.0 + index,
            stepover=float(index + 1),
            properties={"coolant": False},
        ),
    )
    for index, operation_type in enumerate(operation_types)
]

cam_stats = manager.cam_manager.statistics()
setup_stats = manager.manufacturing_setup_manager.statistics()
operation_stats = manager.operation_manager.statistics()

assert cam_document.job_ids == [job.id]
assert job.active is True
assert manager.active_cam_job_id == job.id
assert setup.id in job.setup_ids
assert [operation.id for operation in operations] == job.operation_ids
assert manager.cam_jobs_for_document(cam_document) == [job]
assert manager.cam_setups_for_job(job) == [setup]
assert manager.cam_operations_for_job(job) == operations
assert manager.cam_operations_for_setup(setup) == operations
assert cam_stats.documents == 1
assert cam_stats.jobs == 1
assert cam_stats.active_jobs == 1
assert setup_stats.setups == 1
assert setup_stats.stock_box == 1
assert operation_stats.operations == len(operation_types)
assert operation_stats.definition_only == len(operation_types)
assert operation_stats.laser == 1
assert operation_stats.plasma == 1
assert operation_stats.router == 1
assert operation_stats.printing == 1
assert all(operation.segments() == [] for operation in operations)
assert len(workspace.scene3d.entities()) == 1
assert len(manager.dependency_edges) >= 14

print("3d-cam-foundation-manager-ok")
