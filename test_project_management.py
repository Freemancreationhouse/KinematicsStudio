import tempfile
from pathlib import Path

from engine.cad.application import CADApplication
from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.storage import ProjectTemplateManager


with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "managed.ksproj"
    app = CADApplication()
    app.recent_files.storage_path = Path(tmp) / "recent.json"

    workspace = app.new_project(ProjectTemplateManager.ARCHITECTURAL)
    assert workspace.current_layer.name == "Walls"

    workspace.add_entity(LineEntity(Vector2(0, 0), Vector2(10, 0)))
    app.save_project(path)
    assert app.project_path == str(path)
    assert app.last_save_time is not None
    assert str(path.resolve()) in app.recent_files.paths()

    loaded = app.open_project(path)
    assert loaded.current_layer.name == "Walls"
    assert loaded.project_settings["template"] == ProjectTemplateManager.ARCHITECTURAL
    assert len(loaded.entities) == 1

    info = app.project_info()
    assert info["current_project"] == "Model"
    assert info["file_path"] == str(path)
    assert info["entity_count"] == 1
    assert info["layer_count"] >= 2

print("project-management-ok")
