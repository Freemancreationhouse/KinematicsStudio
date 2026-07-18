import tempfile
from pathlib import Path

from engine.blocks.block_definition import BlockDefinition
from engine.commands import AddEntityCommand, CreateConstraintCommand
from engine.entities import BlockReference, CircleEntity, LineEntity, RectangleEntity
from engine.export import ExportManager
from engine.geometry import Vector2
from engine.storage.autosave import AutoSaveManager
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace
from engine.snap.snap_manager import SnapManager


workspace = Workspace("Production Stress")

layers = [
    workspace.create_layer(f"Layer {index}", "#FFFFFF", "Continuous", 0.25)
    for index in range(20)
]

for index in range(1200):
    workspace.set_current_layer(layers[index % len(layers)])
    workspace.command_manager.execute(
        AddEntityCommand(
            workspace.entities,
            LineEntity(
                Vector2(index, index % 100),
                Vector2(index + 10, index % 100),
            ),
        )
    )

for index in range(200):
    workspace.add_entity(
        RectangleEntity(
            Vector2(index * 2, 200),
            Vector2(index * 2 + 8, 208),
        )
    )
    workspace.add_entity(CircleEntity(Vector2(index * 2, 260), 4))

definition = BlockDefinition(
    "StressBlock",
    origin=Vector2(0, 0),
    entities=[
        LineEntity(Vector2(0, 0), Vector2(10, 0)),
        CircleEntity(Vector2(5, 5), 3),
    ],
)

for index in range(100):
    workspace.add_entity(BlockReference(definition, Vector2(index * 12, 320)))

workspace.selection.create_set("Large Set", workspace.entities[:500])
workspace.group_manager.create("Stress Group", workspace.entities[10:30])

for index in range(60):
    workspace.command_manager.execute(
        CreateConstraintCommand(
            workspace,
            "Horizontal",
            [workspace.entities[index]],
        )
    )

for _ in range(25):
    workspace.command_manager.undo()

for _ in range(25):
    workspace.command_manager.redo()

assert len(workspace.entities) == 1700
assert workspace.command_manager.undo_count >= 1200
assert workspace.selection.selection_sets["Large Set"].count == 500
assert len(workspace.constraint_manager.constraints) == 60
assert workspace.constraint_manager.validate() in (
    "OK",
    "Under-constrained",
    "Over-constrained",
)

snap = SnapManager()
result = snap.snap(Vector2(25, 25), workspace)
assert result.mode in ("OFF", "END", "MID", "CENTER", "INT", "NEAR", "GRID", "QUAD")

context = ExportManager().context(workspace)
assert len(context.entities) >= len(workspace.entities)
assert all(not getattr(item.entity, "is_constraint", False) for item in context.entities)

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    project_path = root / "stress.ksproj"
    serializer = ProjectSerializer()
    serializer.save(workspace, project_path)
    restored = serializer.load(project_path)

    assert len(restored.entities) == len(workspace.entities)
    assert len(restored.constraint_manager.constraints) == 60
    assert restored.selection.selection_sets["Large Set"].count == 500

    autosave = AutoSaveManager(
        lambda: workspace,
        serializer=serializer,
        recovery_path=root / "recovery.ksproj",
    )
    recovery = autosave.autosave_now()
    assert recovery.exists()
    assert autosave.has_recovery()

print("production-stabilization-ok")
