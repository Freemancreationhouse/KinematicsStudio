from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import LaserTool, PlasmaTool, ProductCurve, ProductPart
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(10.0, 6.0, 1.0), name="Laser Plasma Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Laser Plasma Product")
part = manager.add_part(ProductPart("Laser Plasma Part", "Laser Plasma Mesh"))
curve = manager.curve_manager.add_item(ProductCurve("Laser Plasma Curve", part.id))
cam_document = manager.cam_manager.create_document("Laser Plasma CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Laser Plasma CAM Job", [part, curve])
setup = manager.manufacturing_setup_manager.create_setup(cam_job, [part], "Box", name="Laser Plasma Setup")

library = manager.tool_library_manager.create_library("Laser Plasma Tools")
category = manager.tool_library_manager.create_category(library, "Cutting")
laser_tool = manager.tool_library_manager.create_tool(LaserTool, library, category, "CO2 Laser")
plasma_tool = manager.tool_library_manager.create_tool(PlasmaTool, library, category, "Plasma Torch")

wood = manager.laser_plasma_manager.create_material_profile("Birch Plywood", "Plywood", 6.0)
steel = manager.laser_plasma_manager.create_material_profile("Mild Steel", "Steel", 3.0)
laser_cut = manager.laser_plasma_manager.create_cutting_profile(wood, "Plywood Cut", cut_speed=20.0, travel_speed=120.0, pass_count=2, focus_offset=-0.5)
plasma_cut = manager.laser_plasma_manager.create_cutting_profile(steel, "Steel Cut", pierce_height=4.0, cut_height=1.5, kerf_width=1.2, pierce_delay=0.7)
power = manager.laser_plasma_manager.create_power_profile("Plywood Power", 10.0, 80.0, 65.0)
gas = manager.laser_plasma_manager.create_gas_profile("Air", "Compressed Air", 5.5)
cooling = manager.laser_plasma_manager.create_cooling_profile("Water", "Closed Loop")
laser_job = manager.laser_plasma_manager.create_laser_job(cam_job, "Panel Laser Job")
plasma_job = manager.laser_plasma_manager.create_plasma_job(cam_job, "Bracket Plasma Job")

laser_operations = [
    manager.laser_plasma_manager.create_laser_operation(
        laser_job,
        setup,
        operation_type,
        [part, curve],
        f"{operation_type} Definition",
        laser_tool,
        wood,
        laser_cut,
        power,
        laser_power=65.0,
        minimum_power=10.0,
        maximum_power=80.0,
        cut_speed=20.0,
        travel_speed=120.0,
        pass_count=2,
        group="Laser",
        order=index,
    )
    for index, operation_type in enumerate(["Vector Cut", "Vector Engrave", "Raster Engrave", "Raster Fill", "Image Engrave", "Score", "Mark"])
]
plasma_operations = [
    manager.laser_plasma_manager.create_plasma_operation(
        plasma_job,
        setup,
        operation_type,
        [part, curve],
        f"{operation_type} Definition",
        plasma_tool,
        steel,
        plasma_cut,
        gas_profile=gas,
        cooling_profile=cooling,
        pierce_height=4.0,
        cut_height=1.5,
        kerf_width=1.2,
        pierce_delay=0.7,
        lead_radius=2.0,
        lead_angle=45.0,
        group="Plasma",
        order=len(laser_operations) + index,
    )
    for index, operation_type in enumerate(["Plasma Cut", "Pierce", "Lead In", "Lead Out"])
]
manager.operation_manager.set_enabled(plasma_operations[-1], False)

stats = manager.laser_plasma_manager.statistics()
ordered = manager.cam_operations_for_job(cam_job)

assert ordered[0].operation_type == "Vector Cut"
assert ordered[-1].operation_type == "Lead Out"
assert stats.laser_jobs == 1
assert stats.plasma_jobs == 1
assert stats.laser_operations == len(laser_operations)
assert stats.plasma_operations == len(plasma_operations)
assert stats.material_profiles == 2
assert stats.cutting_profiles == 2
assert stats.disabled == 1
assert laser_operations[0].parameters.properties["laser_power"] == 65.0
assert plasma_operations[0].parameters.properties["kerf_width"] == 1.2
assert laser_operations[0].laser_plasma_metadata.material_profile_id == wood.id
assert plasma_operations[0].laser_plasma_metadata.gas_profile_id == gas.id
assert laser_operations[0].segments() == []
assert plasma_operations[0].segments() == []
assert len(workspace.scene3d.entities()) == 1
assert len(manager.dependency_edges) >= 45

print("3d-cam-laser-plasma-manager-ok")
