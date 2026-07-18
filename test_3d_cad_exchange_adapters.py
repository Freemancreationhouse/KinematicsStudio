import json
import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.export import ExportManager
from engine.geometry import MeshData
from engine.import3d import ImportManager, ImportSettings
from engine.workspace.workspace import Workspace


def write(path, content):

    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


with tempfile.TemporaryDirectory() as folder:
    import_manager = ImportManager()

    paths = {
        "SKP": os.path.join(folder, "model.skp"),
        "3DM": os.path.join(folder, "model.3dm"),
        "SAT": os.path.join(folder, "model.sat"),
        "STEP": os.path.join(folder, "model.step"),
        "IGES": os.path.join(folder, "model.iges"),
        "Alembic": os.path.join(folder, "model.abc"),
        "FBX": os.path.join(folder, "model.fbx"),
    }

    for path in paths.values():
        write(path, "metadata only\n")

    for reader_type, path in paths.items():
        result = import_manager.read(path, ImportSettings(validate=False))
        assert result.reader_type == reader_type
        assert result.metadata["adapter_foundation"] is True
        assert result.metadata["metadata_only"] is True

    workspace = Workspace()
    workspace.scene3d.add_entity(MeshEntity(MeshData.box(2.0, 2.0, 2.0), "Exchange Box"))
    export_manager = ExportManager()

    for extension in ("skp", "3dm", "step", "stp", "iges", "igs", "sat", "fbx", "abc"):
        path = os.path.join(folder, f"exchange.{extension}")
        exported = export_manager.export(workspace, path, extension)
        data = json.loads(open(exported, encoding="utf-8").read())
        assert data["adapter_foundation"] is True
        assert data["scene3d"][0]["name"] == "Exchange Box"

    obj_path = export_manager.export(workspace, os.path.join(folder, "exchange.obj"), "obj")
    obj_text = open(obj_path, encoding="utf-8").read()
    assert "o Exchange Box" in obj_text
    assert "\nv " in obj_text
    assert "\nf " in obj_text

    stl_path = export_manager.export(workspace, os.path.join(folder, "exchange.stl"), "stl")
    stl_text = open(stl_path, encoding="utf-8").read()
    assert stl_text.startswith("solid KinematicsStudio")
    assert "facet normal" in stl_text

    app = CADApplication()
    app.workspace.import_manager.adapter_settings["SKP"] = {
        "fallback_format": "STEP",
        "units": "model",
    }
    project_path = os.path.join(folder, "adapter_settings.ksproj")
    app.save_project(project_path)

    reopened = CADApplication()
    reopened_workspace = reopened.open_project(project_path)
    assert reopened_workspace.import_manager.adapter_settings["SKP"]["fallback_format"] == "STEP"

print("3d-cad-exchange-adapters-ok")
