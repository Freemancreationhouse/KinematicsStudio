import json
import os
import tempfile

from engine.bcf import BCFTopic
from engine.cad.application import CADApplication
from engine.export import BCFExchange, ExportManager
from engine.workspace.workspace import Workspace


workspace = Workspace()
topic = BCFTopic("Export Topic", "Export through shared framework")
workspace.bcf_manager.add_topic(topic)

with tempfile.TemporaryDirectory() as folder:
    manager_path = os.path.join(folder, "manager.bcf")
    export_manager = ExportManager()
    exported = export_manager.export(workspace, manager_path, "bcf")
    assert os.path.exists(exported)
    assert json.loads(open(exported, encoding="utf-8").read())["bcf"]["topics"][0]["title"] == "Export Topic"

    exchange_path = os.path.join(folder, "exchange.bcf")
    exchange = BCFExchange()
    exchange.export(workspace, exchange_path)

    imported_workspace = Workspace()
    exchange.import_file(imported_workspace, exchange_path)
    assert imported_workspace.bcf_manager.get_topic("Export Topic") is not None

    app = CADApplication()
    app.workspace.bcf_manager.add_topic(BCFTopic("Application Topic"))
    app_path = os.path.join(folder, "application.bcf")
    app.export_project(app_path, "bcf")
    assert os.path.exists(app_path)

print("3d-bcf-export-framework-ok")
