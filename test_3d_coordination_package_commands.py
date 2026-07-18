from engine.commands import (
    CreateCoordinationPackageCommand,
    RemoveCoordinationPackageCommand,
    UpdatePackagePreferencesCommand,
    ValidateCoordinationPackageCommand,
)
from engine.coordination_package import PackageMetadata
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData
from engine.workspace.workspace import Workspace


workspace = Workspace()
entity = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name="Command Package Box")
entity.id = "command-package-box"
workspace.add_3d_entity(entity)

workspace.command_manager.execute(
    CreateCoordinationPackageCommand(
        workspace,
        "Command Package",
        PackageMetadata("Author", "Recipient", "Command delivery", "1.1", "Ready").to_dict(),
    )
)
package = workspace.coordination_package_manager.active_package
assert package is not None
assert workspace.coordination_package_manager.archive_manager.archives

workspace.command_manager.execute(ValidateCoordinationPackageCommand(workspace, package))
assert package.validation.status == "Valid"
workspace.command_manager.undo()
assert package.validation.status == "Valid"
workspace.command_manager.redo()
assert package.validation.status == "Valid"

before = dict(workspace.coordination_package_manager.preferences)
after = {"include_reports": True}
workspace.command_manager.execute(UpdatePackagePreferencesCommand(workspace, before, after))
assert workspace.coordination_package_manager.preferences["include_reports"] is True
workspace.command_manager.undo()
assert workspace.coordination_package_manager.preferences == before

workspace.command_manager.execute(RemoveCoordinationPackageCommand(workspace, package))
assert workspace.coordination_package_manager.get_package(package) is None
workspace.command_manager.undo()
assert workspace.coordination_package_manager.get_package(package) is package

workspace.command_manager.undo()
workspace.command_manager.undo()
assert workspace.coordination_package_manager.packages == []

print("3d-coordination-package-commands-ok")
