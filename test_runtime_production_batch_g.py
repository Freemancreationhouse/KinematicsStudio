from pathlib import Path

from engine.cad import CADApplication
from engine.commands.command import Command
from engine.entities import MeshEntity
from engine.geometry import MeshData


class RuntimeNoopCommand(Command):
    """Minimal command used to verify existing undo/redo cleanup."""

    def __init__(self):
        self.executed = False

    def execute(self):
        self.executed = True

    def undo(self):
        self.executed = False


app = CADApplication()
diagnostics = app.runtime_diagnostics()

assert diagnostics["runtime_validation"]["production_ready"] is True
assert diagnostics["workspaces"] == 1
assert diagnostics["runtime_validation"]["renderer3d_cad_engine_bound"] is True

mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Runtime Mesh")
app.workspace.add_3d_entity(mesh)
app.workspace.selection.select(mesh)
app.workspace.command_manager.execute(RuntimeNoopCommand())
app.engine.add_shape("runtime-shape")
app.engine.save_history()

dirty = app.runtime_diagnostics()
assert dirty["entities_3d"] == 1
assert dirty["selection_count"] == 1
assert dirty["undo_count"] == 1
assert dirty["occ_shapes"] == 1
assert dirty["occ_undo"] == 1

path = Path("runtime_batch_g_validation.ksproj")
app.save_project(path)
assert app.workspace.project_settings["runtime"]["configuration"] == "production"
assert app.workspace.project_settings["runtime"]["diagnostics"]["runtime_validation"]["production_ready"] is True

app.close_project()
closed = app.runtime_diagnostics()
assert closed["runtime_validation"]["production_ready"] is True
assert closed["workspaces"] == 1
assert closed["entities_3d"] == 0
assert closed["selection_count"] == 0
assert closed["undo_count"] == 0
assert closed["redo_count"] == 0
assert closed["occ_shapes"] == 0
assert closed["occ_undo"] == 0

app.open_project(path)
opened = app.runtime_diagnostics()
assert opened["runtime_validation"]["production_ready"] is True
assert opened["workspaces"] == 1
assert opened["entities_3d"] == 1
assert app.workspace.project_settings["runtime"]["configuration"] == "production"

path.unlink(missing_ok=True)

print("runtime-production-batch-g-ok")
