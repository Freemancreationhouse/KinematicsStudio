from engine.commands.command import Command
from engine.coordination_package import CoordinationPackage, PackageMetadata


class CreateCoordinationPackageCommand(Command):
    """Undoable command for creating a coordination delivery package."""

    def __init__(self, workspace, name, metadata=None):

        self.workspace = workspace
        self.package_name = name
        self.metadata = metadata
        self.package = None
        self.archive = None

    def execute(self):
        """Create or restore the delivery package."""

        manager = self.workspace.coordination_package_manager

        if self.package is None:
            metadata = (
                self.metadata
                if isinstance(self.metadata, PackageMetadata)
                else PackageMetadata.from_dict(self.metadata or {})
            )
            self.package = manager.create_delivery_package(
                self.package_name,
                self.workspace,
                metadata,
            )
            self.archive = manager.archive_manager.archives[-1] if manager.archive_manager.archives else None
        else:
            manager.add_package(self.package)
            if self.archive is not None and self.archive not in manager.archive_manager.archives:
                manager.archive_manager.archives.append(self.archive)

    def undo(self):
        """Remove the package and generated archive metadata."""

        manager = self.workspace.coordination_package_manager

        if self.package is not None:
            manager.remove_package(self.package)
            self.workspace.selection.unregister_entity(self.package)

        if self.archive is not None and self.archive in manager.archive_manager.archives:
            manager.archive_manager.archives.remove(self.archive)


class ValidateCoordinationPackageCommand(Command):
    """Undoable command for refreshing package validation."""

    def __init__(self, workspace, package):

        self.workspace = workspace
        self.package = package
        self.before_validation = None
        self.before_statistics = None
        self.after_validation = None
        self.after_statistics = None

    def execute(self):
        """Validate the package."""

        manager = self.workspace.coordination_package_manager
        target = manager.get_package(self.package)

        if target is None:
            return

        if self.before_validation is None:
            self.before_validation = target.validation
            self.before_statistics = target.statistics

        if self.after_validation is None:
            self.after_validation = manager.validate_package(target, self.workspace)
            self.after_statistics = target.statistics
        else:
            target.validation = self.after_validation
            target.statistics = self.after_statistics

    def undo(self):
        """Restore previous validation state."""

        target = self.workspace.coordination_package_manager.get_package(self.package)

        if target is None:
            return

        target.validation = self.before_validation
        target.statistics = self.before_statistics


class RemoveCoordinationPackageCommand(Command):
    """Undoable command for removing a coordination package."""

    def __init__(self, workspace, package):

        self.workspace = workspace
        self.package = package
        self.removed = None

    def execute(self):
        """Remove the package."""

        manager = self.workspace.coordination_package_manager
        self.removed = manager.get_package(self.package)

        if self.removed is not None:
            manager.remove_package(self.removed)
            self.workspace.selection.unregister_entity(self.removed)

    def undo(self):
        """Restore the removed package."""

        if isinstance(self.removed, CoordinationPackage):
            self.workspace.coordination_package_manager.add_package(self.removed)


class UpdatePackagePreferencesCommand(Command):
    """Undoable command for package preferences and validation settings."""

    def __init__(self, workspace, before, after):

        self.workspace = workspace
        self.before = dict(before or {})
        self.after = dict(after or {})

    def execute(self):
        """Apply package preferences."""

        manager = self.workspace.coordination_package_manager
        manager.preferences = dict(self.after)
        manager.archive_manager.preferences = dict(self.after)

    def undo(self):
        """Restore package preferences."""

        manager = self.workspace.coordination_package_manager
        manager.preferences = dict(self.before)
        manager.archive_manager.preferences = dict(self.before)
