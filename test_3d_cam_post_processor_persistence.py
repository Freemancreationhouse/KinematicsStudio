import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(8.0, 5.0, 1.5), name="Persisted Post Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Post Product")
part = manager.add_part(ProductPart("Persisted Post Part", "Persisted Post Mesh"))
cam_document = manager.cam_manager.create_document("Persisted Post CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Persisted Post CAM Job", [part])

controller = manager.post_processor_manager.create_controller_profile(
    "Fanuc",
    "Persisted Fanuc",
    "31i",
    supported_g_codes=["G0", "G1"],
    supported_m_codes=["M3", "M5", "M8"],
)
output = manager.post_processor_manager.create_output_configuration(
    "Persisted Output",
    "PERSISTED",
    units="inch",
    coordinate_mode="Absolute",
    work_offset="G55",
    file_extension=".tap",
)
template = manager.post_processor_manager.create_output_template("Persisted Footer", "Footer", "M30")
post = manager.post_processor_manager.create_post_processor("Persisted Post", controller, output, default=True)
profile = manager.post_processor_manager.create_profile(
    post,
    cam_job,
    controller,
    output,
    [template],
    "Persisted Profile",
    validation_status="Ready",
    warning_count=1,
)
workspace.selection.select(profile)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "cam_post_processor.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager
    restored_controller = restored.controller_profiles[0]
    restored_output = restored.output_configurations[0]
    restored_post = restored.post_processors[0]
    restored_profile = restored.post_processor_profiles[0]

    assert restored_controller.controller_type == "Fanuc"
    assert restored_controller.metadata.controller_version == "31i"
    assert restored_output.program_name == "PERSISTED"
    assert restored_output.coordinates.work_offset == "G55"
    assert restored_output.metadata.file_extension == ".tap"
    assert restored_post.default is True
    assert restored_post.profile_ids == [restored_profile.id]
    assert restored_profile.settings.output_template_ids == [restored.output_templates[0].id]
    assert restored_profile.settings.validation.warning_count == 1
    assert restored_profile.selected is True
    assert restored.post_processor_statistics.post_processors == 1
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-cam-post-processor-persistence-ok")
