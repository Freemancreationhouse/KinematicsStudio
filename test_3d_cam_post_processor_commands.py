from engine.commands import AddPostProcessorObjectCommand
from engine.product import GRBL, OutputConfiguration, OutputTemplate, PostProcessor, PostProcessorProfile
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
cam_document = manager.cam_manager.create_document("Command Post CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Command Post CAM Job")

controller = GRBL("Command GRBL")
output = OutputConfiguration("Command Output", "CMD")
template = OutputTemplate("Command Template", "Header")
post = PostProcessor("Command Post", controller.id, output.id)
profile = PostProcessorProfile("Command Profile", post.id, controller.id, cam_job.id)

workspace.command_manager.execute(AddPostProcessorObjectCommand(workspace, controller))
workspace.command_manager.execute(AddPostProcessorObjectCommand(workspace, output))
workspace.command_manager.execute(AddPostProcessorObjectCommand(workspace, template))
workspace.command_manager.execute(AddPostProcessorObjectCommand(workspace, post))
workspace.command_manager.execute(AddPostProcessorObjectCommand(workspace, profile))

assert manager.controller_profiles == [controller]
assert manager.output_configurations == [output]
assert manager.output_templates == [template]
assert manager.post_processors == [post]
assert manager.post_processor_profiles == [profile]
assert post.profile_ids == [profile.id]

manager.post_processor_manager.set_default(post)
manager.post_processor_manager.set_enabled(profile, False)
assert post.default is True
assert profile.enabled is False

workspace.command_manager.undo()
workspace.command_manager.undo()
workspace.command_manager.undo()
workspace.command_manager.undo()
workspace.command_manager.undo()

assert manager.post_processor_profiles == []
assert manager.post_processors == []
assert manager.output_templates == []
assert manager.output_configurations == []
assert manager.controller_profiles == []

print("3d-cam-post-processor-commands-ok")
