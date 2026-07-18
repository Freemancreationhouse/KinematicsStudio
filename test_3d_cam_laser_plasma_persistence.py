import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import LaserTool, PlasmaTool, ProductCurve, ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(8.0, 4.0, 1.0), name="Persisted Laser Plasma Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Laser Plasma Product")
part = manager.add_part(ProductPart("Persisted Laser Plasma Part", "Persisted Laser Plasma Mesh"))
curve = manager.curve_manager.add_item(ProductCurve("Persisted Laser Plasma Curve", part.id))
cam_document = manager.cam_manager.create_document("Persisted Laser Plasma CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Persisted Laser Plasma CAM Job", [part, curve])
setup = manager.manufacturing_setup_manager.create_setup(cam_job, [part], "Box", name="Persisted Setup")
library = manager.tool_library_manager.create_library("Persisted Laser Plasma Tools")
category = manager.tool_library_manager.create_category(library, "Persisted Cutting")
laser_tool = manager.tool_library_manager.create_tool(LaserTool, library, category, "Persisted Laser")
plasma_tool = manager.tool_library_manager.create_tool(PlasmaTool, library, category, "Persisted Plasma")
material = manager.laser_plasma_manager.create_material_profile("Persisted Acrylic", "Acrylic", 4.0)
cutting = manager.laser_plasma_manager.create_cutting_profile(material, "Persisted Acrylic Cut", cut_speed=18.0, travel_speed=100.0, pass_count=1)
power = manager.laser_plasma_manager.create_power_profile("Persisted Power", 5.0, 70.0, 55.0)
gas = manager.laser_plasma_manager.create_gas_profile("Persisted Gas", "Air", 4.0)
laser_job = manager.laser_plasma_manager.create_laser_job(cam_job, "Persisted Laser Job")
plasma_job = manager.laser_plasma_manager.create_plasma_job(cam_job, "Persisted Plasma Job")
laser_operation = manager.laser_plasma_manager.create_laser_operation(
    laser_job,
    setup,
    "Vector Cut",
    [part, curve],
    "Persisted Vector Cut",
    laser_tool,
    material,
    cutting,
    power,
    laser_power=55.0,
    cut_speed=18.0,
)
plasma_operation = manager.laser_plasma_manager.create_plasma_operation(
    plasma_job,
    setup,
    "Plasma Cut",
    [part, curve],
    "Persisted Plasma Cut",
    plasma_tool,
    material,
    cutting,
    gas_profile=gas,
    pierce_height=3.5,
    cut_height=1.2,
    kerf_width=1.1,
)
manager.operation_manager.set_enabled(plasma_operation, False)
workspace.selection.select(laser_operation)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "cam_laser_plasma.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager
    restored_laser = restored.cam_operations[0]
    restored_plasma = restored.cam_operations[1]

    assert restored_laser.name == "Persisted Vector Cut"
    assert restored_laser.operation_type == "Vector Cut"
    assert restored_laser.parameters.properties["laser_power"] == 55.0
    assert restored_laser.laser_plasma_metadata.material_profile_id == restored.material_profiles[0].id
    assert restored_laser.laser_plasma_metadata.power_profile_id == restored.power_profiles[0].id
    assert restored_laser.selected is True
    assert restored_plasma.operation_type == "Plasma Cut"
    assert restored_plasma.parameters.properties["kerf_width"] == 1.1
    assert restored_plasma.laser_plasma_metadata.gas_profile_id == restored.gas_profiles[0].id
    assert restored_plasma.metadata.enabled is False
    assert restored.laser_plasma_statistics.laser_operations == 1
    assert restored.laser_plasma_statistics.plasma_operations == 1
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-cam-laser-plasma-persistence-ok")
