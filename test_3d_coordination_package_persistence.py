import os
import tempfile

from engine.cad.application import CADApplication
from engine.coordination_package import PackageMetadata
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData


app = CADApplication()
workspace = app.workspace
entity = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name="Persisted Package Box")
entity.id = "persisted-package-box"
workspace.add_3d_entity(entity)
workspace.reference_manager.create_model("Persisted Reference", "persisted.obj")
package = workspace.coordination_package_manager.create_delivery_package(
    "Persisted Package",
    workspace,
    PackageMetadata("Author", "Recipient", "Persisted delivery", "1.1", "Ready"),
)
workspace.selection.select(package)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "coordination_package.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.coordination_package_manager.get_package("Persisted Package")

    assert restored is not None
    assert restored.selected is True
    assert restored.statistics.references == 1
    assert restored.metadata.description == "Persisted delivery"
    assert restored_workspace.archive_manager.archives
    assert restored_workspace.coordination_package_manager.archive_summary()["archives"] == 1

print("3d-coordination-package-persistence-ok")
