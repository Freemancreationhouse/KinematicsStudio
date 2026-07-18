import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import EngineeringMaterial, ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(10.0, 8.0, 2.0), name="Persisted Nesting Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Nesting Product")
part = manager.add_part(ProductPart("Persisted Nesting Part", "Persisted Nesting Mesh"))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("Aluminium Sheet", "Metal"))
cam_document = manager.cam_manager.create_document("Persisted Nesting CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Persisted Nesting CAM Job", [part])
stock_library = manager.nesting_manager.create_stock_library("Persisted Stock Library")
stock_profile = manager.nesting_manager.create_stock_profile(stock_library, "Persisted Plate", "Plate Stock", 500.0, 400.0, 6.0, material, quantity=3)
nesting_profile = manager.nesting_manager.create_profile("Persisted Nest Profile", [stock_profile], estimated_yield_percentage=80.0)
nesting_job = manager.nesting_manager.create_job(cam_job, nesting_profile, "Persisted Nest Job", result_status="Stored")
placement = manager.nesting_manager.create_part_placement(part, stock_profile, quantity=4)
assignment = manager.nesting_manager.create_stock_assignment(stock_profile, [part], quantity=2)
cut_list = manager.nesting_manager.create_cut_list("Persisted Cut List", [part], [placement], [assignment])
panel = manager.nesting_manager.create_panel_layout(stock_profile, [placement], "Persisted Panel")
plan = manager.nesting_manager.create_fabrication_plan(cam_job, "Persisted Fabrication Plan", [cut_list], [panel], assignments=[assignment])
manager.nesting_manager.create_fabrication_job(plan, cam_job, name="Persisted Fabrication Job")
workspace.selection.select(nesting_job)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "cam_nesting.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.stock_libraries[0].name == "Persisted Stock Library"
    assert restored.stock_profiles[0].material_reference.engineering_material_id == restored.engineering_materials[0].id
    assert restored.nesting_profiles[0].stock_profile_ids == [restored.stock_profiles[0].id]
    assert restored.nesting_jobs[0].cam_job_id == restored.cam_jobs[0].id
    assert restored.nesting_jobs[0].selected is True
    assert restored.part_placements[0].part_id == restored.parts[0].id
    assert restored.cut_lists[0].part_ids == [restored.parts[0].id]
    assert restored.panel_layouts[0].placement_ids == [restored.part_placements[0].id]
    assert restored.fabrication_plans[0].cut_list_ids == [restored.cut_lists[0].id]
    assert restored.fabrication_jobs[0].plan_id == restored.fabrication_plans[0].id
    assert restored.nesting_statistics.jobs == 1
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-cam-nesting-persistence-ok")
