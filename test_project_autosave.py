import tempfile
from pathlib import Path

from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.storage import AutoSaveManager, ProjectSerializer
from engine.workspace import Workspace


workspace = Workspace("Autosave")
workspace.add_entity(LineEntity(Vector2(0, 0), Vector2(10, 0)))

with tempfile.TemporaryDirectory() as tmp:
    recovery = Path(tmp) / "recovery.ksproj"
    manager = AutoSaveManager(
        lambda: workspace,
        serializer=ProjectSerializer(),
        interval_seconds=1,
        recovery_path=recovery,
    )

    saved = manager.autosave_now()
    assert saved == recovery
    assert manager.last_error is None
    assert manager.has_recovery()

    recovered = manager.load_recovery()
    assert recovered.name == "Autosave"
    assert len(recovered.entities) == 1

    manager.clear_recovery()
    assert not manager.has_recovery()

print("project-autosave-ok")
