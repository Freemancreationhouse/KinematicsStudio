import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import EngineeringMaterial, OperationParameters, ProductPart, SolidBody


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(5.0, 5.0, 2.0), name="Persisted CAM Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted CAM Product")
part = manager.add_part(ProductPart("Persisted CAM Part", "Persisted CAM Mesh"))
body = manager.add_body_item(SolidBody("Persisted CAM Body", part.id, mesh.name))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("Persisted Steel", "Steel"))
cam_document = manager.cam_manager.create_document("Persisted CAM Document")
job = manager.cam_manager.create_job(cam_document, "Persisted CAM Job", [part, body])
setup = manager.manufacturing_setup_manager.create_setup(job, [part, body], "Box", material, "Persisted Setup")
operation = manager.operation_manager.create_operation(
    job,
    setup,
    "Facing",
    [part],
    "Persisted Facing",
    OperationParameters(tool_id="T1", depth=2.5, properties={"strategy": "roughing"}),
)
workspace.selection.select(operation)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "cam_foundation.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.cam_documents[0].name == "Persisted CAM Document"
    assert restored.cam_jobs[0].name == "Persisted CAM Job"
    assert restored.cam_jobs[0].target_ids == [restored.parts[0].id, restored.bodies[0].id]
    assert restored.cam_jobs[0].active is True
    assert restored.cam_setups[0].name == "Persisted Setup"
    assert restored.cam_setups[0].stock.stock_type == "Box"
    assert restored.cam_setups[0].stock.material_id == restored.engineering_materials[0].id
    assert restored.cam_operations[0].name == "Persisted Facing"
    assert restored.cam_operations[0].operation_type == "Facing"
    assert restored.cam_operations[0].parameters.depth == 2.5
    assert restored.cam_operations[0].parameters.tool_id == "T1"
    assert restored.cam_operations[0].parameters.properties["strategy"] == "roughing"
    assert restored.cam_operations[0].selected is True
    assert restored.cam_statistics.jobs == 1
    assert restored.setup_statistics.stock_box == 1
    assert restored.operation_statistics.definition_only == 1
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-cam-foundation-persistence-ok")
