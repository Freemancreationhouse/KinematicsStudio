from engine.commands import (
    CreateCompareSessionCommand,
    RemoveCompareSessionCommand,
    RunModelCompareCommand,
    UpdateCompareSettingsCommand,
)
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.model_compare import CompareSettings
from engine.workspace.workspace import Workspace


def mesh(name, entity_id, position):

    entity = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name=name)
    entity.id = entity_id
    entity.set_transform_state(position=position)

    return entity


workspace = Workspace()
entity = mesh("Command Box", "cmd-box", Vector3())
workspace.add_3d_entity(entity)

workspace.command_manager.execute(CreateCompareSessionCommand(workspace, "Command Baseline"))
assert workspace.model_compare_manager.active_session is not None
assert workspace.model_compare_manager.active_session.name == "Command Baseline"

entity.set_transform_state(position=Vector3(15.0, 0.0, 0.0))
workspace.command_manager.execute(RunModelCompareCommand(workspace))
assert workspace.model_compare_manager.active_session.results

workspace.command_manager.undo()
assert workspace.model_compare_manager.active_session.results == []
workspace.command_manager.redo()
assert workspace.model_compare_manager.active_session.results

before = workspace.model_compare_manager.settings
after = CompareSettings(search="box", group_by="Name")
workspace.command_manager.execute(UpdateCompareSettingsCommand(workspace, before, after))
assert workspace.model_compare_manager.settings.search == "box"
workspace.command_manager.undo()
assert workspace.model_compare_manager.settings is before

session = workspace.model_compare_manager.active_session
workspace.command_manager.execute(RemoveCompareSessionCommand(workspace, session))
assert workspace.model_compare_manager.get_session(session) is None
workspace.command_manager.undo()
assert workspace.model_compare_manager.get_session(session) is session

print("3d-model-compare-commands-ok")
