from engine.bim import BIMProject
from engine.commands.command import Command


class CreateBIMProjectCommand(Command):
    """Undoable command for creating a BIM project container."""

    def __init__(self, workspace, name="BIM Project", metadata=None, settings=None):

        self.workspace = workspace
        self.project_name = name
        self.metadata = metadata
        self.settings = settings
        self.project = None

    def execute(self):
        """Create or restore the BIM project."""

        manager = self.workspace.bim_manager

        if self.project is None:
            self.project = manager.create_project(self.project_name, self.metadata, self.settings)
        else:
            manager.add_project(self.project)

    def undo(self):
        """Remove the created BIM project."""

        if isinstance(self.project, BIMProject):
            self.workspace.bim_manager.remove_project(self.project)


class AddBIMObjectCommand(Command):
    """Undoable command for adding BIM hierarchy or object metadata."""

    def __init__(self, workspace, item):

        self.workspace = workspace
        self.item = item

    def execute(self):
        """Add the BIM item to the active project."""

        self.workspace.bim_manager.add_object(self.item)

    def undo(self):
        """Remove the BIM item from the active project."""

        self.workspace.bim_manager.remove_object(self.item)
        self.workspace.selection.unregister_entity(self.item)


class AddBIMFamilyCommand(AddBIMObjectCommand):
    """Undoable command for adding a BIM family."""


class AddBIMTypeCommand(AddBIMObjectCommand):
    """Undoable command for adding a BIM type."""


class AddBIMPropertySetCommand(AddBIMObjectCommand):
    """Undoable command for adding a BIM property set."""


class AddBIMElementDefinitionCommand(AddBIMObjectCommand):
    """Undoable command for adding a BIM element definition."""


class AddBIMMaterialCommand(AddBIMObjectCommand):
    """Undoable command for adding a BIM material or material category."""


class AssignBIMMaterialCommand(AddBIMObjectCommand):
    """Undoable command for assigning a material to a BIM item."""


class AddBIMAssemblyCommand(AddBIMObjectCommand):
    """Undoable command for adding a BIM assembly."""


class AddBIMViewCommand(AddBIMObjectCommand):
    """Undoable command for adding a BIM view."""


class AddBIMSheetCommand(AddBIMObjectCommand):
    """Undoable command for adding a BIM drawing sheet."""


class AddBIMScheduleCommand(AddBIMObjectCommand):
    """Undoable command for adding a BIM schedule definition."""


class AddBIMClassificationCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM classification metadata."""


class AddBIMIFCObjectCommand(AddBIMObjectCommand):
    """Undoable command for adding IFC foundation metadata."""


class AddBIMRelationshipCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM relationship graph metadata."""


class AddBIMHostOpeningCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM host/opening metadata."""


class AddBIMConnectionCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM connectivity metadata."""


class AddBIMDesignOptionCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM design option metadata."""


class AddBIMPhaseCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM phase metadata."""


class AddBIMLifecycleCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM lifecycle metadata."""


class AddBIMRoomCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM room metadata."""


class AddBIMSpaceCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM space metadata."""


class AddBIMZoneCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM zone metadata."""


class AddBIMAreaAnalysisCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM area analysis metadata."""


class AddBIMMEPCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM MEP foundation metadata."""


class AddBIMConnectorCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM connector topology metadata."""


class AddBIMValidationCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM validation metadata."""


class AddBIMModelCheckCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM model checking metadata."""


class AddBIMInteroperabilityCommand(AddBIMObjectCommand):
    """Undoable command for adding BIM interoperability metadata."""


class RemoveBIMObjectCommand(Command):
    """Undoable command for removing BIM hierarchy or object metadata."""

    def __init__(self, workspace, item):

        self.workspace = workspace
        self.item = item
        self.removed = None

    def execute(self):
        """Remove the BIM item from the active project."""

        self.removed = self.item
        self.workspace.bim_manager.remove_object(self.item)
        self.workspace.selection.unregister_entity(self.item)

    def undo(self):
        """Restore the BIM item to the active project."""

        if self.removed is not None:
            self.workspace.bim_manager.add_object(self.removed)


class UpdateBIMSettingsCommand(Command):
    """Undoable command for BIM project settings."""

    def __init__(self, workspace, before, after):

        self.workspace = workspace
        self.before = before
        self.after = after

    def execute(self):
        """Apply BIM settings to the active project."""

        project = self.workspace.bim_manager.ensure_project()
        project.settings = self.after

    def undo(self):
        """Restore previous BIM settings."""

        project = self.workspace.bim_manager.ensure_project()
        project.settings = self.before


class UpdateBIMPropertySetCommand(Command):
    """Undoable command for replacing property-set values."""

    def __init__(self, workspace, property_set, before, after):

        self.workspace = workspace
        self.property_set = property_set
        self.before = before
        self.after = after

    def execute(self):
        """Apply updated property set data."""

        self._apply(self.after)

    def undo(self):
        """Restore previous property set data."""

        self._apply(self.before)

    def _apply(self, data):

        restored = self.property_set.__class__.from_dict(data)
        self.property_set.name = restored.name
        self.property_set.owner_id = restored.owner_id
        self.property_set.ifc_name = restored.ifc_name
        self.property_set.classification = restored.classification
        self.property_set.definitions = restored.definitions
        self.property_set.values = restored.values
        self.property_set.groups = restored.groups


class UpdateBIMElementParametersCommand(Command):
    """Undoable command for BIM element parameters and relationships."""

    def __init__(self, workspace, instance, before_parameters, after_parameters, before_relationships=None, after_relationships=None):

        self.workspace = workspace
        self.instance = instance
        self.before_parameters = before_parameters
        self.after_parameters = after_parameters
        self.before_relationships = before_relationships
        self.after_relationships = after_relationships

    def execute(self):
        """Apply element parameter and relationship updates."""

        self._apply(self.after_parameters, self.after_relationships)

    def undo(self):
        """Restore previous element parameter and relationship state."""

        self._apply(self.before_parameters, self.before_relationships)

    def _apply(self, parameters, relationships):

        if parameters is not None:
            self.instance.element_parameters = self.instance.element_parameters.__class__.from_dict(parameters)

        if relationships is not None:
            self.instance.element_relationships = self.instance.element_relationships.__class__.from_dict(relationships)


class RunBIMQuantityTakeoffCommand(Command):
    """Undoable command for refreshing BIM quantity takeoff results."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.before_items = None
        self.before_summary = None
        self.before_statistics = None
        self.after_items = None
        self.after_summary = None
        self.after_statistics = None

    def execute(self):
        """Run quantity takeoff using existing BIM data."""

        project = self.workspace.bim_manager.ensure_project()

        if self.before_items is None:
            self.before_items = list(project.quantity_items)
            self.before_summary = project.quantity_summary
            self.before_statistics = project.quantity_statistics

        if self.after_items is None:
            self.workspace.bim_manager.run_quantity_takeoff()
            self.after_items = list(project.quantity_items)
            self.after_summary = project.quantity_summary
            self.after_statistics = project.quantity_statistics
        else:
            project.quantity_items = list(self.after_items)
            project.quantity_summary = self.after_summary
            project.quantity_statistics = self.after_statistics

    def undo(self):
        """Restore previous quantity takeoff results."""

        project = self.workspace.bim_manager.ensure_project()
        project.quantity_items = list(self.before_items or [])
        project.quantity_summary = self.before_summary
        project.quantity_statistics = self.before_statistics


class RunBIMValidationCommand(Command):
    """Undoable command for refreshing BIM validation results."""

    def __init__(self, workspace, profile=None):

        self.workspace = workspace
        self.profile = profile
        self.before_results = None
        self.before_statistics = None
        self.after_results = None
        self.after_statistics = None

    def execute(self):
        """Run or restore validation results."""

        project = self.workspace.bim_manager.ensure_project()

        if self.before_results is None:
            self.before_results = list(project.validation_results)
            self.before_statistics = project.validation_statistics

        if self.after_results is None:
            self.workspace.bim_manager.validation_manager.run(self.profile)
            self.after_results = list(project.validation_results)
            self.after_statistics = project.validation_statistics
        else:
            project.validation_results = list(self.after_results)
            project.validation_statistics = self.after_statistics

    def undo(self):
        """Restore previous validation results."""

        project = self.workspace.bim_manager.ensure_project()
        project.validation_results = list(self.before_results or [])
        project.validation_statistics = self.before_statistics


class RunBIMModelCheckCommand(Command):
    """Undoable command for refreshing BIM model check results."""

    def __init__(self, workspace, profile=None):

        self.workspace = workspace
        self.profile = profile
        self.before_results = None
        self.before_statistics = None
        self.after_results = None
        self.after_statistics = None

    def execute(self):
        """Run or restore model check results."""

        project = self.workspace.bim_manager.ensure_project()

        if self.before_results is None:
            self.before_results = list(project.model_check_results)
            self.before_statistics = project.model_check_statistics

        if self.after_results is None:
            self.workspace.bim_manager.model_check_manager.run(self.profile)
            self.after_results = list(project.model_check_results)
            self.after_statistics = project.model_check_statistics
        else:
            project.model_check_results = list(self.after_results)
            project.model_check_statistics = self.after_statistics

    def undo(self):
        """Restore previous model check results."""

        project = self.workspace.bim_manager.ensure_project()
        project.model_check_results = list(self.before_results or [])
        project.model_check_statistics = self.before_statistics


class RefreshBIMInteroperabilityCommand(Command):
    """Undoable command for refreshing BIM interoperability statistics."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.before_statistics = None
        self.after_statistics = None

    def execute(self):
        """Refresh or restore interoperability readiness statistics."""

        project = self.workspace.bim_manager.ensure_project()

        if self.before_statistics is None:
            self.before_statistics = project.exchange_statistics

        if self.after_statistics is None:
            self.workspace.bim_manager.interoperability_manager.statistics()
            self.after_statistics = project.exchange_statistics
        else:
            project.exchange_statistics = self.after_statistics

    def undo(self):
        """Restore previous interoperability statistics."""

        project = self.workspace.bim_manager.ensure_project()
        project.exchange_statistics = self.before_statistics


class BuildBIMScheduleCommand(Command):
    """Undoable command for rebuilding a BIM schedule from existing BIM data."""

    def __init__(self, workspace, schedule):

        self.workspace = workspace
        self.schedule = schedule
        self.before_rows = None
        self.after_rows = None
        self.before_statistics = None
        self.after_statistics = None

    def execute(self):
        """Build or restore schedule rows."""

        project = self.workspace.bim_manager.ensure_project()

        if self.before_rows is None:
            self.before_rows = list(self.schedule.rows)
            self.before_statistics = project.schedule_statistics

        if self.after_rows is None:
            self.workspace.bim_manager.build_schedule(self.schedule)
            self.after_rows = list(self.schedule.rows)
            self.after_statistics = project.schedule_statistics
        else:
            self.schedule.rows = list(self.after_rows)
            project.schedule_statistics = self.after_statistics

    def undo(self):
        """Restore previous schedule rows."""

        project = self.workspace.bim_manager.ensure_project()
        self.schedule.rows = list(self.before_rows or [])
        project.schedule_statistics = self.before_statistics


class UpdateBIMDocumentationSettingsCommand(Command):
    """Undoable command for BIM documentation settings."""

    def __init__(self, workspace, before, after):

        self.workspace = workspace
        self.before = before
        self.after = after

    def execute(self):
        """Apply documentation settings."""

        self.workspace.bim_manager.ensure_project().documentation_settings = self.after

    def undo(self):
        """Restore documentation settings."""

        self.workspace.bim_manager.ensure_project().documentation_settings = self.before
