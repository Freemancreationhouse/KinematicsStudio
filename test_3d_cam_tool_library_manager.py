from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    BallNose,
    BoringBar,
    BullNose,
    CenterDrill,
    ChamferMill,
    CuttingData,
    Drill,
    EndMill,
    EngravingTool,
    EngineeringMaterial,
    FaceMill,
    FlyCutter,
    LaserTool,
    PlasmaTool,
    PrinterNozzle,
    ProductPart,
    Reamer,
    RouterBit,
    SlotMill,
    SpotDrill,
    Tap,
    ThreadMill,
    ToolMetadata,
    VBit,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(4.0, 4.0, 1.0), name="Tool Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Tool Product")
part = manager.add_part(ProductPart("Tool Part", "Tool Mesh"))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("6061 Aluminium", "Aluminium"))
cam_document = manager.cam_manager.create_document("Tool CAM Document")
job = manager.cam_manager.create_job(cam_document, "Tool CAM Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(job, [part], "Box", material, "Tool Setup")
operation = manager.operation_manager.create_operation(job, setup, "Pocket", [part], "Pocket Definition")

library = manager.tool_library_manager.create_library("Shop Tool Library")
category = manager.tool_library_manager.create_category(library, "Milling")

tool_classes = [
    EndMill,
    BallNose,
    BullNose,
    FaceMill,
    SlotMill,
    ChamferMill,
    VBit,
    EngravingTool,
    Drill,
    CenterDrill,
    SpotDrill,
    Reamer,
    Tap,
    ThreadMill,
    FlyCutter,
    BoringBar,
    RouterBit,
    LaserTool,
    PlasmaTool,
    PrinterNozzle,
]
tools = [
    manager.tool_library_manager.create_tool(
        tool_class,
        library,
        category,
        name=f"{tool_class.__name__} Tool",
        diameter=index + 1,
        flute_length=10.0,
        overall_length=50.0,
        flutes=2,
        corner_radius=0.5,
        tip_angle=90.0,
        metadata=ToolMetadata(material="Carbide", coating="TiN", iso_id=f"ISO-{index}", favorite=index == 0),
    )
    for index, tool_class in enumerate(tool_classes)
]
holder = manager.holder_manager.create_holder(library, "ER32 Collet", "Collet", 60.0, 45.0)
profile = manager.tool_library_manager.create_feed_speed_profile(
    tools[0],
    material,
    "Aluminium Roughing",
    CuttingData(spindle_speed=12000.0, feed_rate=900.0, plunge_rate=250.0, step_over=0.4, step_down=1.5, maximum_rpm=18000.0),
)
preset = manager.tool_library_manager.create_preset(tools[0], holder, profile, "T1 Roughing", 1, 1, 1)
manager.tool_library_manager.assign_preset_to_operation(preset, operation)

stats = manager.tool_library_manager.statistics()
holder_stats = manager.holder_manager.statistics()

assert library.category_ids == [category.id]
assert len(library.tool_ids) == len(tool_classes)
assert holder.id in library.holder_ids
assert preset.id in library.preset_ids
assert len(category.tool_ids) == len(tool_classes)
assert tools[0].preset_ids == [preset.id]
assert manager.tool_library_manager.search_tools("router")[0].tool_type == "RouterBit"
assert manager.tool_library_manager.search_tools("ISO-0") == [tools[0]]
assert stats.libraries == 1
assert stats.categories == 1
assert stats.tools == len(tool_classes)
assert stats.holders == 1
assert stats.profiles == 1
assert stats.presets == 1
assert stats.favorites == 1
assert holder_stats.collets == 1
assert operation.parameters.tool_id == tools[0].id
assert operation.metadata.properties["tool_preset_id"] == preset.id
assert len(workspace.scene3d.entities()) == 1
assert len(manager.dependency_edges) >= 7

print("3d-cam-tool-library-manager-ok")
