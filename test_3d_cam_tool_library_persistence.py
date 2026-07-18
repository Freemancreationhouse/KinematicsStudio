import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import CuttingData, EndMill, EngineeringMaterial, ProductPart, ToolMetadata


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(4.0, 4.0, 1.0), name="Persisted Tool Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Tool Product")
part = manager.add_part(ProductPart("Persisted Tool Part", "Persisted Tool Mesh"))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("Persisted Aluminium", "Aluminium"))
cam_document = manager.cam_manager.create_document("Persisted Tool CAM")
job = manager.cam_manager.create_job(cam_document, "Persisted Tool Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(job, [part], "Box", material, "Persisted Tool Setup")
operation = manager.operation_manager.create_operation(job, setup, "Facing", [part], "Persisted Facing")

library = manager.tool_library_manager.create_library("Persisted Tool Library")
category = manager.tool_library_manager.create_category(library, "Persisted Mills")
tool = manager.tool_library_manager.create_tool(
    EndMill,
    library,
    category,
    "Persisted End Mill",
    diameter=8.0,
    flute_length=22.0,
    overall_length=70.0,
    flutes=4,
    metadata=ToolMetadata(material="Carbide", coating="AlTiN", ansi_id="ANSI-EM-8"),
)
holder = manager.holder_manager.create_holder(library, "Persisted Holder", "HolderDefinition", 90.0, 60.0)
profile = manager.tool_library_manager.create_feed_speed_profile(
    tool,
    material,
    "Persisted Profile",
    CuttingData(spindle_speed=10000.0, feed_rate=800.0, plunge_rate=200.0, step_over=0.45, step_down=1.0, maximum_rpm=16000.0),
)
preset = manager.tool_library_manager.create_preset(tool, holder, profile, "Persisted Preset", 3, 13, 23)
manager.tool_library_manager.assign_preset_to_operation(preset, operation)
workspace.selection.select(tool)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "cam_tool_library.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.tool_libraries[0].name == "Persisted Tool Library"
    assert restored.tool_categories[0].name == "Persisted Mills"
    assert restored.tool_definitions[0].name == "Persisted End Mill"
    assert restored.tool_definitions[0].diameter == 8.0
    assert restored.tool_definitions[0].metadata.coating == "AlTiN"
    assert restored.tool_definitions[0].selected is True
    assert restored.tool_holders[0].name == "Persisted Holder"
    assert restored.feed_speed_profiles[0].cutting_data.feed_rate == 800.0
    assert restored.tool_presets[0].tool_number == 3
    assert restored.cam_operations[0].parameters.tool_id == restored.tool_definitions[0].id
    assert restored.cam_operations[0].metadata.properties["tool_preset_id"] == restored.tool_presets[0].id
    assert restored.tool_statistics.tools == 1
    assert restored.holder_statistics.holder_definitions == 1
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-cam-tool-library-persistence-ok")
