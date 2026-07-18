from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import EngineeringMaterial, ProductPart
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(18.0, 12.0, 3.0), name="Nesting Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Nesting Product")
part = manager.add_part(ProductPart("Nesting Part", "Nesting Mesh"))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("Birch Plywood", "Wood"))
cam_document = manager.cam_manager.create_document("Nesting CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Nesting CAM Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(cam_job, [part], "Box", name="Nesting Setup")
machine_library = manager.machine_library_manager.create_library("Nesting Machines")
machine = manager.machine_library_manager.create_machine("Router", machine_library, "Nesting Router")
machine_profile = manager.machine_library_manager.create_profile(machine, cam_job, setup=setup, name="Nesting Machine Profile")

stock_library = manager.nesting_manager.create_stock_library("Sheet Goods")
stock_profile = manager.nesting_manager.create_stock_profile(
    stock_library,
    "18mm Birch Sheet",
    "Sheet Stock",
    2440.0,
    1220.0,
    18.0,
    material,
    quantity=12,
    grain_direction="Long",
    supplier_placeholder="Local Supplier",
    cost_placeholder=65.0,
)
nesting_profile = manager.nesting_manager.create_profile(
    "Router Nest Profile",
    [stock_profile],
    machine_profile,
    estimated_material_area=2.4,
    estimated_waste_percentage=12.5,
    estimated_yield_percentage=87.5,
    estimated_panels=2,
    estimated_cuts=14,
)
nesting_job = manager.nesting_manager.create_job(cam_job, nesting_profile, "Router Nest Job", enabled=True)
placement = manager.nesting_manager.create_part_placement(part, stock_profile, None, 10.0, 20.0, 0.0, 2)
assignment = manager.nesting_manager.create_stock_assignment(stock_profile, [part], machine_profile, setup, quantity=1)
cut_list = manager.nesting_manager.create_cut_list("Router Cut List", [part], [placement], [assignment])
panel_layout = manager.nesting_manager.create_panel_layout(stock_profile, [placement], "Panel Layout A")
group = manager.nesting_manager.create_fabrication_group("Batch A", [part], [assignment])
plan = manager.nesting_manager.create_fabrication_plan(cam_job, "Fabrication Plan A", [cut_list], [panel_layout], [group], [assignment])
fabrication_job = manager.nesting_manager.create_fabrication_job(plan, cam_job, machine_profile, "Fabrication Job A")
stats = manager.nesting_manager.statistics()

assert stats.jobs == 1
assert stats.profiles == 1
assert stats.enabled_jobs == 1
assert stats.stock_libraries == 1
assert stats.stock_profiles == 1
assert stats.fabrication_plans == 1
assert stats.cut_lists == 1
assert stats.panel_layouts == 1
assert stats.assignments == 1
assert stock_profile.material_reference.engineering_material_id == material.id
assert stock_profile.id in stock_library.profile_ids
assert nesting_profile.stock_profile_ids == [stock_profile.id]
assert nesting_profile.machine_profile_id == machine_profile.id
assert nesting_job.cam_job_id == cam_job.id
assert placement.panel_layout_id == panel_layout.id
assert assignment.setup_id == setup.id
assert cut_list.part_ids == [part.id]
assert plan.cam_job_id == cam_job.id
assert fabrication_job.plan_id == plan.id
assert fabrication_job.machine_profile_id == machine_profile.id
assert len(manager.dependency_edges) >= 10
assert len(workspace.scene3d.entities()) == 1

print("3d-cam-nesting-manager-ok")
