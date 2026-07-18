import os
import tempfile

from engine.geometry import Vector3
from engine.import3d import ImportManager, ImportSettings
from engine.workspace.workspace import Workspace


def write(path, text):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


with tempfile.TemporaryDirectory() as folder:
    obj = os.path.join(folder, "one.obj")
    replacement = os.path.join(folder, "two.off")
    write(obj, "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
    write(replacement, "OFF\n4 1 0\n0 0 0\n2 0 0\n2 2 0\n0 2 0\n4 0 1 2 3\n")

    workspace = Workspace()
    manager = ImportManager()
    result = manager.create_reference(
        workspace,
        obj,
        "Imported OBJ",
        ImportSettings(scale=2.0),
    )

    model = workspace.reference_manager.models[0]
    instance = workspace.reference_manager.instances[0]

    assert result.reader_type == "OBJ"
    assert model.reader_type == "OBJ"
    assert model.import_statistics.vertices == 3
    assert instance in workspace.selectable_3d_entities()
    assert workspace.selection.first is instance

    workspace.command_manager.undo()
    assert workspace.reference_manager.models == []
    assert workspace.reference_manager.instances == []

    workspace.command_manager.redo()
    model = workspace.reference_manager.models[0]
    manager.reload_reference(workspace, model)
    assert model.reader_type == "OBJ"

    manager.replace_reference(workspace, model, replacement)
    assert model.reader_type == "OFF"
    assert model.import_statistics.faces == 1

    workspace.coordination_manager.reference_offset(model.id, Vector3(1.0, 0.0, 0.0))
    assert workspace.coordination_manager.rules[-1].settings["reference_id"] == model.id

print("3d-import-workflow-ok")
