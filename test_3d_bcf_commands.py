import os
import tempfile

from engine.bcf import BCFProject, BCFTopic, BCFViewpoint
from engine.commands import (
    AddBCFTopicCommand,
    ImportBCFProjectCommand,
    RemoveBCFTopicCommand,
    RestoreBCFViewpointCommand,
    UpdateBCFTopicCommand,
)
from engine.geometry import Vector3
from engine.workspace.workspace import Workspace


class DummyCamera:
    def __init__(self):

        self.position = Vector3()
        self.target = Vector3()
        self.up = Vector3(0.0, 0.0, 1.0)


workspace = Workspace()
topic = BCFTopic("Command Topic", "Created through command")
workspace.command_manager.execute(AddBCFTopicCommand(workspace, topic))
assert topic in workspace.bcf_manager.topics()
assert topic.selected is True

workspace.command_manager.execute(UpdateBCFTopicCommand(
    topic,
    {"status": topic.status, "priority": topic.priority},
    {"status": "In Review", "priority": "High"},
))
assert topic.status == "In Review"
workspace.command_manager.undo()
assert topic.status == "Open"

camera = DummyCamera()
viewpoint = BCFViewpoint("Restore", Vector3(9.0, 8.0, 7.0), Vector3(1.0, 1.0, 1.0))
workspace.command_manager.execute(RestoreBCFViewpointCommand(workspace, topic, camera, viewpoint))
assert camera.position.x == 9.0
workspace.command_manager.undo()
assert camera.position.x == 0.0

workspace.command_manager.execute(RemoveBCFTopicCommand(workspace, topic))
assert topic not in workspace.bcf_manager.topics()
workspace.command_manager.undo()
assert topic in workspace.bcf_manager.topics()

with tempfile.TemporaryDirectory() as folder:
    import_workspace = Workspace()
    imported_project = BCFProject("Imported")
    imported_project.add_topic(BCFTopic("Imported Topic"))
    import_workspace.bcf_manager.add_project(imported_project)
    path = os.path.join(folder, "imported.bcf")
    import_workspace.bcf_manager.export_bcf(path, imported_project)

    target_workspace = Workspace()
    target_workspace.command_manager.execute(ImportBCFProjectCommand(target_workspace, path))
    assert target_workspace.bcf_manager.get_project("Imported") is not None
    target_workspace.command_manager.undo()
    assert target_workspace.bcf_manager.get_project("Imported") is None

print("3d-bcf-commands-ok")
