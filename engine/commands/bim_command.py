from engine.bim import (
    BIMAnnotation,
    BIMAuthoringSession,
    BIMClashResult,
    BIMCoordinationReference,
    BIMDigitalTwinRecord,
    BIMDocumentationDocument,
    BIMElement,
    BIMGeneratedDrawing,
    BIMIntelligenceIssue,
    BIMRuntimeConfiguration,
    BIMRuntimeSession,
    BIMOptimizationReport,
    BIMParametricDefinition,
    BIMProject,
    BIMCertificationRecord,
    BIMCompatibilityReport,
    BIMPublishingPackage,
    BIMRecommendation,
    BIMRegressionResult,
    BIMReviewSession,
    BIMRuleDefinition,
    IFCExchangeRecord,
)
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


class StartBIMAuthoringSessionCommand(Command):
    """Undoable command for starting a BIM authoring session."""

    def __init__(self, workspace, active_tool="", placement_context=None, metadata=None):

        self.workspace = workspace
        self.active_tool = active_tool
        self.placement_context = placement_context
        self.metadata = metadata
        self.session = None

    def execute(self):
        """Create or restore the authoring session."""

        project = self.workspace.bim_manager.ensure_project()

        if self.session is None:
            self.session = self.workspace.bim_manager.authoring_manager.start_session(
                self.active_tool,
                self.placement_context,
                self.metadata,
            )
        elif self.session not in project.authoring_sessions:
            project.authoring_sessions.append(self.session)
            project.active_authoring_session_id = self.session.id

    def undo(self):
        """Remove the authoring session."""

        if isinstance(self.session, BIMAuthoringSession):
            project = self.workspace.bim_manager.ensure_project()
            if self.session in project.authoring_sessions:
                project.authoring_sessions.remove(self.session)
            if project.active_authoring_session_id == self.session.id:
                project.active_authoring_session_id = project.authoring_sessions[-1].id if project.authoring_sessions else ""


class UpdateBIMAuthoringContextCommand(Command):
    """Undoable command for authoring placement, snapping and preview context."""

    def __init__(self, workspace, updates):

        self.workspace = workspace
        self.updates = dict(updates or {})
        self.before = None
        self.after = None

    def execute(self):
        """Apply authoring context updates."""

        session = self.workspace.bim_manager.authoring_manager.active_session()
        if self.before is None:
            self.before = session.to_dict()
        self.workspace.bim_manager.authoring_manager.update_context(**self.updates)
        self.after = session.to_dict()

    def undo(self):
        """Restore previous authoring context."""

        if self.before is None:
            return
        project = self.workspace.bim_manager.ensure_project()
        restored = BIMAuthoringSession.from_dict(self.before)
        for index, session in enumerate(project.authoring_sessions):
            if session.id == restored.id:
                project.authoring_sessions[index] = restored
                project.active_authoring_session_id = restored.id
                return


class CreateBIMElementCommand(Command):
    """Undoable command for creating a native BIM element through BIM authoring."""

    def __init__(
        self,
        workspace,
        element_type,
        name,
        body_references,
        element_type_id="",
        material_assignment_id="",
        level_id="",
        host_id="",
        parameters=None,
        metadata=None,
        property_set_ids=None,
    ):

        self.workspace = workspace
        self.element_type = element_type
        self.element_name = name
        self.body_references = list(body_references or [])
        self.element_type_id = element_type_id
        self.material_assignment_id = material_assignment_id
        self.level_id = level_id
        self.host_id = host_id
        self.parameters = (
            parameters
            if isinstance(parameters, BIMParametricDefinition)
            else BIMParametricDefinition.from_dict(parameters or {})
        )
        self.metadata = dict(metadata or {})
        self.property_set_ids = list(property_set_ids or [])
        self.element = None

    def execute(self):
        """Create or restore the native BIM element."""

        manager = self.workspace.bim_manager

        if self.element is None:
            self.element = manager.authoring_manager.create_element(
                self.element_type,
                self.element_name,
                self.body_references,
                element_type_id=self.element_type_id,
                material_assignment_id=self.material_assignment_id,
                level_id=self.level_id,
                host_id=self.host_id,
                parameters=self.parameters,
                metadata=self.metadata,
                property_set_ids=self.property_set_ids,
            )
        else:
            manager.add_object(self.element)

    def undo(self):
        """Remove the created native BIM element."""

        if isinstance(self.element, BIMElement):
            self.workspace.bim_manager.remove_object(self.element)
            self.workspace.selection.unregister_entity(self.element)


class CreateWallCommand(CreateBIMElementCommand):
    """Create Wall BIM authoring command."""

    def __init__(self, workspace, name, body_references, **kwargs):
        super().__init__(workspace, "Wall", name, body_references, **kwargs)


class CreateCurtainWallCommand(CreateBIMElementCommand):
    """Create Curtain Wall BIM authoring command."""

    def __init__(self, workspace, name, body_references, **kwargs):
        super().__init__(workspace, "Curtain Wall", name, body_references, **kwargs)


class CreateSlabCommand(CreateBIMElementCommand):
    """Create Slab BIM authoring command."""

    def __init__(self, workspace, name, body_references, **kwargs):
        super().__init__(workspace, "Slab", name, body_references, **kwargs)


class CreateRoofCommand(CreateBIMElementCommand):
    """Create Roof BIM authoring command."""

    def __init__(self, workspace, name, body_references, **kwargs):
        super().__init__(workspace, "Roof", name, body_references, **kwargs)


class CreateCeilingCommand(CreateBIMElementCommand):
    """Create Ceiling BIM authoring command."""

    def __init__(self, workspace, name, body_references, **kwargs):
        super().__init__(workspace, "Ceiling", name, body_references, **kwargs)


class CreateFloorFinishCommand(CreateBIMElementCommand):
    """Create Floor Finish BIM authoring command."""

    def __init__(self, workspace, name, body_references, **kwargs):
        super().__init__(workspace, "Floor Finish", name, body_references, **kwargs)


class CreateColumnCommand(CreateBIMElementCommand):
    """Create Column BIM authoring command."""

    def __init__(self, workspace, name, body_references, **kwargs):
        super().__init__(workspace, "Column", name, body_references, **kwargs)


class CreateBeamCommand(CreateBIMElementCommand):
    """Create Beam BIM authoring command."""

    def __init__(self, workspace, name, body_references, **kwargs):
        super().__init__(workspace, "Beam", name, body_references, **kwargs)


class CreateDoorCommand(CreateBIMElementCommand):
    """Create Door BIM authoring command."""

    def __init__(self, workspace, name, body_references, **kwargs):
        super().__init__(workspace, "Door", name, body_references, **kwargs)


class CreateWindowCommand(CreateBIMElementCommand):
    """Create Window BIM authoring command."""

    def __init__(self, workspace, name, body_references, **kwargs):
        super().__init__(workspace, "Window", name, body_references, **kwargs)


class CreateStairCommand(CreateBIMElementCommand):
    """Create Stair BIM authoring command."""

    def __init__(self, workspace, name, body_references, **kwargs):
        super().__init__(workspace, "Stair", name, body_references, **kwargs)


class CreateRampCommand(CreateBIMElementCommand):
    """Create Ramp BIM authoring command."""

    def __init__(self, workspace, name, body_references, **kwargs):
        super().__init__(workspace, "Ramp", name, body_references, **kwargs)


class CreateRailingCommand(CreateBIMElementCommand):
    """Create Railing BIM authoring command."""

    def __init__(self, workspace, name, body_references, **kwargs):
        super().__init__(workspace, "Railing", name, body_references, **kwargs)


class EditBIMElementCommand(Command):
    """Undoable BIM element metadata edit command."""

    def __init__(self, workspace, element, updates):

        self.workspace = workspace
        self.element = element
        self.updates = dict(updates or {})
        self.before = None
        self.after = None

    def execute(self):
        """Apply metadata edits to the BIM element."""

        if self.before is None:
            self.before = self.element.to_dict()
        self.workspace.bim_manager.authoring_manager.edit_element(self.element, self.updates)
        self.after = self.element.to_dict()

    def undo(self):
        """Restore previous BIM element metadata."""

        if self.before is not None:
            _restore_bim_element_state(self.element, self.before)


class MoveBIMElementCommand(EditBIMElementCommand):
    """Move BIM element metadata command."""


class CopyBIMElementCommand(Command):
    """Undoable BIM element copy command."""

    def __init__(self, workspace, element, name=None, metadata=None):

        self.workspace = workspace
        self.element = element
        self.element_name = name or f"{element.name} Copy"
        self.metadata = dict(metadata or {})
        self.created = None

    def execute(self):
        """Create or restore the copied BIM element metadata."""

        if self.created is None:
            self.created = self.workspace.bim_manager.authoring_manager.create_element(
                self.element.element_type,
                self.element_name,
                [reference.to_dict() for reference in self.element.body_references],
                element_type_id=self.element.element_type_id,
                material_assignment_id=self.element.material_assignment_id,
                level_id=self.element.level_id,
                host_id=self.element.host_id,
                parameters=self.element.parameters,
                metadata=dict(self.element.metadata, **self.metadata),
                property_set_ids=list(self.element.property_set_ids),
            )
        else:
            self.workspace.bim_manager.add_object(self.created)

    def undo(self):
        """Remove the copied element metadata."""

        if self.created is not None:
            self.workspace.bim_manager.remove_object(self.created)


class RotateBIMElementCommand(EditBIMElementCommand):
    """Rotate BIM element metadata command."""


class MirrorBIMElementCommand(EditBIMElementCommand):
    """Mirror BIM element metadata command."""


class ArrayBIMElementCommand(EditBIMElementCommand):
    """Array BIM element metadata command."""


class OffsetBIMElementCommand(EditBIMElementCommand):
    """Offset BIM element metadata command."""


class SplitBIMElementCommand(EditBIMElementCommand):
    """Split BIM element metadata command."""


class JoinBIMElementCommand(EditBIMElementCommand):
    """Join BIM element metadata command."""


class DeleteBIMElementCommand(Command):
    """Undoable native BIM element delete command."""

    def __init__(self, workspace, element):

        self.workspace = workspace
        self.element = element

    def execute(self):
        """Delete the BIM element metadata."""

        self.workspace.bim_manager.remove_object(self.element)

    def undo(self):
        """Restore the BIM element metadata."""

        self.workspace.bim_manager.add_object(self.element)


class ReplaceBIMElementTypeCommand(EditBIMElementCommand):
    """Replace BIM element type metadata."""

    def __init__(self, workspace, element, element_type_id):
        super().__init__(workspace, element, {"element_type_id": element_type_id})


class ChangeBIMElementLevelCommand(EditBIMElementCommand):
    """Change BIM element level assignment metadata."""

    def __init__(self, workspace, element, level_id):
        super().__init__(workspace, element, {"level_id": level_id})


class ChangeBIMElementMaterialCommand(EditBIMElementCommand):
    """Change BIM element material assignment metadata."""

    def __init__(self, workspace, element, material_assignment_id):
        super().__init__(workspace, element, {"material_assignment_id": material_assignment_id})


class CreateBIMElementRelationshipCommand(Command):
    """Undoable BIM element relationship authoring command."""

    def __init__(self, workspace, relationship_type, source_id, target_id, **metadata):

        self.workspace = workspace
        self.relationship_type = relationship_type
        self.source_id = source_id
        self.target_id = target_id
        self.metadata = dict(metadata or {})
        self.relationship = None

    def execute(self):
        """Create or restore the BIM element relationship."""

        project = self.workspace.bim_manager.ensure_project()
        if self.relationship is None:
            self.relationship = self.workspace.bim_manager.authoring_manager.create_relationship(
                self.relationship_type,
                self.source_id,
                self.target_id,
                **self.metadata,
            )
        elif self.relationship not in project.native_relationships:
            project.native_relationships.append(self.relationship)

    def undo(self):
        """Remove the BIM element relationship."""

        project = self.workspace.bim_manager.ensure_project()
        if self.relationship in project.native_relationships:
            project.native_relationships.remove(self.relationship)
        for element in project.native_elements:
            if self.relationship and self.relationship.id in element.host_relationship_ids:
                element.host_relationship_ids.remove(self.relationship.id)


class HostDoorByWallCommand(CreateBIMElementRelationshipCommand):
    """Create Door to Wall host relationship command."""

    def __init__(self, workspace, door_id, wall_id, **metadata):
        super().__init__(workspace, "DoorToWall", door_id, wall_id, **metadata)


class HostWindowByWallCommand(CreateBIMElementRelationshipCommand):
    """Create Window to Wall host relationship command."""

    def __init__(self, workspace, window_id, wall_id, **metadata):
        super().__init__(workspace, "WindowToWall", window_id, wall_id, **metadata)


class ConnectBeamToColumnCommand(CreateBIMElementRelationshipCommand):
    """Create Beam to Column relationship command."""

    def __init__(self, workspace, beam_id, column_id, **metadata):
        super().__init__(workspace, "BeamToColumn", beam_id, column_id, **metadata)


class ConnectColumnToFoundationCommand(CreateBIMElementRelationshipCommand):
    """Create Column to Foundation relationship command."""

    def __init__(self, workspace, column_id, foundation_id, **metadata):
        super().__init__(workspace, "ColumnToFoundation", column_id, foundation_id, **metadata)


class SupportSlabByBeamCommand(CreateBIMElementRelationshipCommand):
    """Create Slab supported by Beam relationship command."""

    def __init__(self, workspace, slab_id, beam_id, **metadata):
        super().__init__(workspace, "SlabToBeam", slab_id, beam_id, **metadata)


def _restore_bim_element_state(element, data):
    restored = BIMElement.from_dict(data)
    element.__dict__.clear()
    element.__dict__.update(restored.__dict__)


class ExportIFC43Command(Command):
    """Undoable command for creating IFC 4.3 export records."""

    def __init__(self, workspace, object_ids=None, owner_history=None, options=None):

        self.workspace = workspace
        self.object_ids = object_ids
        self.owner_history = owner_history
        self.options = options
        self.record = None

    def execute(self):
        """Create or restore the IFC export record."""

        if self.record is None:
            self.record = self.workspace.bim_manager.export_ifc43(self.object_ids, self.owner_history, self.options)
        else:
            self.workspace.bim_manager.add_object(self.record)

    def undo(self):
        """Remove the IFC export record."""

        if isinstance(self.record, IFCExchangeRecord):
            self.workspace.bim_manager.remove_object(self.record)


class ImportIFC43Command(Command):
    """Undoable command for importing IFC 4.3 metadata records."""

    def __init__(self, workspace, content, owner_history=None, options=None):

        self.workspace = workspace
        self.content = content
        self.owner_history = owner_history
        self.options = options
        self.record = None
        self.created_entities = []

    def execute(self):
        """Create or restore IFC import metadata."""

        project = self.workspace.bim_manager.ensure_project()
        if self.record is None:
            before = list(project.core_ifc_entities)
            self.record = self.workspace.bim_manager.import_ifc43(self.content, self.owner_history, self.options)
            self.created_entities = [item for item in project.core_ifc_entities if item not in before]
        else:
            self.workspace.bim_manager.add_object(self.record)
            for entity in self.created_entities:
                self.workspace.bim_manager.add_object(entity)

    def undo(self):
        """Remove imported IFC metadata."""

        if isinstance(self.record, IFCExchangeRecord):
            self.workspace.bim_manager.remove_object(self.record)
        for entity in self.created_entities:
            self.workspace.bim_manager.remove_object(entity)


class UpdateIFC43Command(ExportIFC43Command):
    """Undoable command for incremental IFC 4.3 update records."""

    def __init__(self, workspace, exchange_record, changed_object_ids):

        super().__init__(workspace, changed_object_ids)
        self.exchange_record = exchange_record

    def execute(self):
        """Create or restore the incremental IFC update."""

        if self.record is None:
            self.record = self.workspace.bim_manager.update_ifc43(self.exchange_record, self.object_ids)
        else:
            self.workspace.bim_manager.add_object(self.record)


class CreateBIMDocumentationDocumentCommand(Command):
    """Undoable command for BIM documentation documents."""

    def __init__(self, workspace, name, document_type="Drawing Set", title_block="Default Title Block", **metadata):

        self.workspace = workspace
        self.document_name = name
        self.document_type = document_type
        self.title_block = title_block
        self.metadata = dict(metadata or {})
        self.document = None

    def execute(self):
        """Create or restore the document."""

        if self.document is None:
            self.document = self.workspace.bim_manager.create_documentation_document(
                self.document_name,
                self.document_type,
                self.title_block,
                **self.metadata,
            )
        else:
            self.workspace.bim_manager.add_object(self.document)

    def undo(self):
        """Remove the document."""

        if isinstance(self.document, BIMDocumentationDocument):
            self.workspace.bim_manager.remove_object(self.document)


class GenerateBIMDrawingCommand(Command):
    """Undoable command for generated BIM drawing metadata."""

    def __init__(self, workspace, drawing_type, name, element_ids=None, sheet_id="", view_id="", scale="1:100", **metadata):

        self.workspace = workspace
        self.drawing_type = drawing_type
        self.drawing_name = name
        self.element_ids = list(element_ids or [])
        self.sheet_id = sheet_id
        self.view_id = view_id
        self.scale = scale
        self.metadata = dict(metadata or {})
        self.drawing = None

    def execute(self):
        """Create or restore drawing metadata."""

        if self.drawing is None:
            self.drawing = self.workspace.bim_manager.generate_bim_drawing(
                self.drawing_type,
                self.drawing_name,
                self.element_ids,
                self.sheet_id,
                self.view_id,
                self.scale,
                **self.metadata,
            )
        else:
            self.workspace.bim_manager.add_object(self.drawing)

    def undo(self):
        """Remove drawing metadata."""

        if isinstance(self.drawing, BIMGeneratedDrawing):
            self.workspace.bim_manager.remove_object(self.drawing)


class GenerateBIMScheduleCommand(Command):
    """Undoable command for BIM schedules generated from existing elements."""

    def __init__(self, workspace, schedule_type, name=None, fields=None, export_metadata=None):

        self.workspace = workspace
        self.schedule_type = schedule_type
        self.schedule_name = name
        self.fields = fields
        self.export_metadata = export_metadata
        self.schedule = None

    def execute(self):
        """Create or restore schedule metadata."""

        if self.schedule is None:
            self.schedule = self.workspace.bim_manager.generate_bim_schedule(
                self.schedule_type,
                self.schedule_name,
                self.fields,
                self.export_metadata,
            )
        else:
            self.workspace.bim_manager.add_schedule(self.schedule)

    def undo(self):
        """Remove the generated schedule."""

        if self.schedule is not None:
            self.workspace.bim_manager.remove_object(self.schedule)


class RunBIMDocumentationTakeoffCommand(Command):
    """Undoable command for documentation quantity takeoff."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.before = None
        self.after = None

    def execute(self):
        """Run or restore quantity takeoff results."""

        project = self.workspace.bim_manager.ensure_project()
        if self.before is None:
            self.before = [item.to_dict() for item in project.quantity_items]
        if self.after is None:
            self.workspace.bim_manager.run_documentation_quantity_takeoff()
            self.after = [item.to_dict() for item in project.quantity_items]
        else:
            from engine.bim import QuantityItem
            project.quantity_items = [QuantityItem.from_dict(item) for item in self.after]

    def undo(self):
        """Restore previous quantity takeoff results."""

        from engine.bim import QuantityItem
        project = self.workspace.bim_manager.ensure_project()
        project.quantity_items = [QuantityItem.from_dict(item) for item in self.before or []]


class AddBIMAnnotationCommand(Command):
    """Undoable command for associative BIM annotations."""

    def __init__(self, workspace, annotation_type, target_id, text, view_id="", sheet_id="", **metadata):

        self.workspace = workspace
        self.annotation_type = annotation_type
        self.target_id = target_id
        self.text = text
        self.view_id = view_id
        self.sheet_id = sheet_id
        self.metadata = dict(metadata or {})
        self.annotation = None

    def execute(self):
        """Create or restore annotation metadata."""

        if self.annotation is None:
            self.annotation = self.workspace.bim_manager.create_bim_annotation(
                self.annotation_type,
                self.target_id,
                self.text,
                self.view_id,
                self.sheet_id,
                **self.metadata,
            )
        else:
            self.workspace.bim_manager.add_object(self.annotation)

    def undo(self):
        """Remove annotation metadata."""

        if isinstance(self.annotation, BIMAnnotation):
            self.workspace.bim_manager.remove_object(self.annotation)


class PublishBIMPackageCommand(Command):
    """Undoable command for print/PDF publishing packages."""

    def __init__(self, workspace, name, package_type="PDF", sheet_ids=None, **metadata):

        self.workspace = workspace
        self.package_name = name
        self.package_type = package_type
        self.sheet_ids = list(sheet_ids or [])
        self.metadata = dict(metadata or {})
        self.package = None

    def execute(self):
        """Create or restore publishing package metadata."""

        if self.package is None:
            self.package = self.workspace.bim_manager.publish_bim_package(
                self.package_name,
                self.package_type,
                self.sheet_ids,
                **self.metadata,
            )
        else:
            self.workspace.bim_manager.add_object(self.package)

    def undo(self):
        """Remove publishing package metadata."""

        if isinstance(self.package, BIMPublishingPackage):
            self.workspace.bim_manager.remove_object(self.package)


class AddBIMCoordinationReferenceCommand(Command):
    """Undoable command for BIM coordination references."""

    def __init__(self, workspace, name, reference_type="Linked Model", source="", target_ids=None, **metadata):

        self.workspace = workspace
        self.reference_name = name
        self.reference_type = reference_type
        self.source = source
        self.target_ids = list(target_ids or [])
        self.metadata = dict(metadata or {})
        self.reference = None

    def execute(self):
        """Create or restore coordination reference metadata."""

        if self.reference is None:
            self.reference = self.workspace.bim_manager.add_bim_coordination_reference(
                self.reference_name,
                self.reference_type,
                self.source,
                self.target_ids,
                **self.metadata,
            )
        else:
            self.workspace.bim_manager.add_object(self.reference)

    def undo(self):
        """Remove coordination reference metadata."""

        if isinstance(self.reference, BIMCoordinationReference):
            self.workspace.bim_manager.remove_object(self.reference)


class ValidateBIMDocumentationCommand(Command):
    """Undoable command for refreshing BIM documentation validation."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.before = None
        self.after = None

    def execute(self):
        """Run or restore documentation validation."""

        project = self.workspace.bim_manager.ensure_project()
        if self.before is None:
            self.before = project.documentation_validation_report
        if self.after is None:
            self.after = self.workspace.bim_manager.validate_bim_documentation()
        else:
            project.documentation_validation_report = self.after

    def undo(self):
        """Restore previous documentation validation."""

        self.workspace.bim_manager.ensure_project().documentation_validation_report = self.before


class RunBIMClashDetectionCommand(Command):
    """Undoable command for refreshing BIM Intelligence clash results."""

    def __init__(self, workspace, category_filters=None, clearance=0.0):

        self.workspace = workspace
        self.category_filters = list(category_filters or [])
        self.clearance = float(clearance or 0.0)
        self.before_clashes = None
        self.before_issues = None
        self.after_clashes = None
        self.after_issues = None

    def execute(self):
        """Run or restore clash detection metadata."""

        project = self.workspace.bim_manager.ensure_project()
        if self.before_clashes is None:
            self.before_clashes = [item.to_dict() for item in project.intelligence_clashes]
            self.before_issues = [item.to_dict() for item in project.intelligence_issues]
        if self.after_clashes is None:
            self.workspace.bim_manager.run_bim_clash_detection(self.category_filters, self.clearance)
            self.after_clashes = [item.to_dict() for item in project.intelligence_clashes]
            self.after_issues = [item.to_dict() for item in project.intelligence_issues]
        else:
            project.intelligence_clashes = [BIMClashResult.from_dict(item) for item in self.after_clashes]
            project.intelligence_issues = [BIMIntelligenceIssue.from_dict(item) for item in self.after_issues]
            self.workspace.bim_manager.intelligence_manager.refresh_diagnostics()

    def undo(self):
        """Restore previous clash detection metadata."""

        project = self.workspace.bim_manager.ensure_project()
        project.intelligence_clashes = [BIMClashResult.from_dict(item) for item in self.before_clashes or []]
        project.intelligence_issues = [BIMIntelligenceIssue.from_dict(item) for item in self.before_issues or []]
        self.workspace.bim_manager.intelligence_manager.refresh_diagnostics()


class RunBIMModelValidationCommand(Command):
    """Undoable command for refreshing BIM Intelligence model validation."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.before = None
        self.after = None

    def execute(self):
        """Run or restore BIM Intelligence validation."""

        project = self.workspace.bim_manager.ensure_project()
        if self.before is None:
            self.before = project.intelligence_validation_report
        if self.after is None:
            self.after = self.workspace.bim_manager.run_bim_model_validation()
        else:
            project.intelligence_validation_report = self.after
            self.workspace.bim_manager.intelligence_manager.refresh_diagnostics()

    def undo(self):
        """Restore previous BIM Intelligence validation."""

        project = self.workspace.bim_manager.ensure_project()
        project.intelligence_validation_report = self.before
        self.workspace.bim_manager.intelligence_manager.refresh_diagnostics()


class AddBIMIntelligenceIssueCommand(Command):
    """Undoable command for BIM Intelligence issue management."""

    def __init__(self, workspace, issue_type, title, **metadata):

        self.workspace = workspace
        self.issue_type = issue_type
        self.issue_title = title
        self.metadata = dict(metadata or {})
        self.issue = None

    def execute(self):
        """Create or restore an issue."""

        if self.issue is None:
            self.issue = self.workspace.bim_manager.create_bim_intelligence_issue(
                self.issue_type,
                self.issue_title,
                **self.metadata,
            )
        else:
            self.workspace.bim_manager.add_object(self.issue)

    def undo(self):
        """Remove the issue."""

        if isinstance(self.issue, BIMIntelligenceIssue):
            self.workspace.bim_manager.remove_object(self.issue)


class AddBIMReviewSessionCommand(Command):
    """Undoable command for BIM coordination review sessions."""

    def __init__(self, workspace, name, reviewer="", issue_ids=None, snapshots=None, metadata=None):

        self.workspace = workspace
        self.review_name = name
        self.reviewer = reviewer
        self.issue_ids = list(issue_ids or [])
        self.snapshots = [dict(item) for item in snapshots or []]
        self.metadata = dict(metadata or {})
        self.session = None

    def execute(self):
        """Create or restore a review session."""

        if self.session is None:
            self.session = self.workspace.bim_manager.create_bim_review_session(
                self.review_name,
                self.reviewer,
                self.issue_ids,
                self.snapshots,
                self.metadata,
            )
        else:
            self.workspace.bim_manager.add_object(self.session)

    def undo(self):
        """Remove the review session."""

        if isinstance(self.session, BIMReviewSession):
            self.workspace.bim_manager.remove_object(self.session)


class AddBIMRuleCommand(Command):
    """Undoable command for registering a BIM Intelligence rule."""

    def __init__(self, workspace, name, rule_type, target="All", expression_metadata=None, severity="Medium", enabled=True, metadata=None):

        self.workspace = workspace
        self.rule_name = name
        self.rule_type = rule_type
        self.target = target
        self.expression_metadata = dict(expression_metadata or {})
        self.severity = severity
        self.enabled = bool(enabled)
        self.metadata = dict(metadata or {})
        self.rule = None

    def execute(self):
        """Create or restore a BIM rule."""

        if self.rule is None:
            self.rule = self.workspace.bim_manager.add_bim_intelligence_rule(
                self.rule_name,
                self.rule_type,
                self.target,
                self.expression_metadata,
                self.severity,
                self.enabled,
                self.metadata,
            )
        else:
            self.workspace.bim_manager.add_object(self.rule)

    def undo(self):
        """Remove the BIM rule."""

        if isinstance(self.rule, BIMRuleDefinition):
            self.workspace.bim_manager.remove_object(self.rule)


class RunBIMRuleCheckCommand(Command):
    """Undoable command for BIM Intelligence rule checking."""

    def __init__(self, workspace, rule_ids=None):

        self.workspace = workspace
        self.rule_ids = list(rule_ids or [])
        self.before_results = None
        self.before_issues = None
        self.after_results = None
        self.after_issues = None

    def execute(self):
        """Run or restore BIM rule check results."""

        project = self.workspace.bim_manager.ensure_project()
        if self.before_results is None:
            self.before_results = [item.to_dict() for item in project.intelligence_rule_results]
            self.before_issues = [item.to_dict() for item in project.intelligence_issues]
        if self.after_results is None:
            self.workspace.bim_manager.run_bim_intelligence_rules(self.rule_ids)
            self.after_results = [item.to_dict() for item in project.intelligence_rule_results]
            self.after_issues = [item.to_dict() for item in project.intelligence_issues]
        else:
            from engine.bim import BIMRuleCheckResult
            project.intelligence_rule_results = [BIMRuleCheckResult.from_dict(item) for item in self.after_results]
            project.intelligence_issues = [BIMIntelligenceIssue.from_dict(item) for item in self.after_issues]
            self.workspace.bim_manager.intelligence_manager.refresh_diagnostics()

    def undo(self):
        """Restore previous rule check results."""

        from engine.bim import BIMRuleCheckResult
        project = self.workspace.bim_manager.ensure_project()
        project.intelligence_rule_results = [BIMRuleCheckResult.from_dict(item) for item in self.before_results or []]
        project.intelligence_issues = [BIMIntelligenceIssue.from_dict(item) for item in self.before_issues or []]
        self.workspace.bim_manager.intelligence_manager.refresh_diagnostics()


class AddBIMRecommendationCommand(Command):
    """Undoable command for adding AI BIM Assistant recommendations."""

    def __init__(self, workspace, recommendation_type, title, **metadata):

        self.workspace = workspace
        self.recommendation_type = recommendation_type
        self.recommendation_title = title
        self.metadata = dict(metadata or {})
        self.recommendation = None

    def execute(self):
        """Create or restore an AI BIM recommendation."""

        if self.recommendation is None:
            self.recommendation = self.workspace.bim_manager.create_ai_bim_recommendation(
                self.recommendation_type,
                self.recommendation_title,
                **self.metadata,
            )
        else:
            self.workspace.bim_manager.add_object(self.recommendation)

    def undo(self):
        """Remove the recommendation."""

        if isinstance(self.recommendation, BIMRecommendation):
            self.workspace.bim_manager.remove_object(self.recommendation)


class GenerateAIBIMRecommendationsCommand(Command):
    """Undoable command for generating AI BIM Assistant command-plan recommendations."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.before = None
        self.after = None

    def execute(self):
        """Generate or restore AI BIM recommendations."""

        project = self.workspace.bim_manager.ensure_project()
        if self.before is None:
            self.before = [item.to_dict() for item in project.intelligence_recommendations]
        if self.after is None:
            self.workspace.bim_manager.generate_ai_bim_recommendations()
            self.after = [item.to_dict() for item in project.intelligence_recommendations]
        else:
            project.intelligence_recommendations = [BIMRecommendation.from_dict(item) for item in self.after]
            self.workspace.bim_manager.intelligence_manager.refresh_diagnostics()

    def undo(self):
        """Restore previous AI BIM recommendations."""

        project = self.workspace.bim_manager.ensure_project()
        project.intelligence_recommendations = [BIMRecommendation.from_dict(item) for item in self.before or []]
        self.workspace.bim_manager.intelligence_manager.refresh_diagnostics()


class AddBIMDigitalTwinRecordCommand(Command):
    """Undoable command for digital twin foundation metadata."""

    def __init__(self, workspace, target_id, **metadata):

        self.workspace = workspace
        self.target_id = target_id
        self.metadata = dict(metadata or {})
        self.record = None

    def execute(self):
        """Create or restore a digital twin record."""

        if self.record is None:
            self.record = self.workspace.bim_manager.create_bim_digital_twin_record(
                self.target_id,
                **self.metadata,
            )
        else:
            self.workspace.bim_manager.add_object(self.record)

    def undo(self):
        """Remove the digital twin record."""

        if isinstance(self.record, BIMDigitalTwinRecord):
            self.workspace.bim_manager.remove_object(self.record)


class ValidateBIMIntelligenceCommand(Command):
    """Undoable command for validating BIM Intelligence metadata."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.before = None
        self.after = None

    def execute(self):
        """Run or restore BIM Intelligence validation."""

        project = self.workspace.bim_manager.ensure_project()
        if self.before is None:
            self.before = project.intelligence_validation_report
        if self.after is None:
            self.after = self.workspace.bim_manager.validate_bim_intelligence()
        else:
            project.intelligence_validation_report = self.after
            self.workspace.bim_manager.intelligence_manager.refresh_diagnostics()

    def undo(self):
        """Restore previous BIM Intelligence validation."""

        project = self.workspace.bim_manager.ensure_project()
        project.intelligence_validation_report = self.before
        self.workspace.bim_manager.intelligence_manager.refresh_diagnostics()


class InitializeBIMProductionRuntimeCommand(Command):
    """Undoable command for Production BIM Runtime initialization metadata."""

    def __init__(self, workspace, configuration=None, recovery_metadata=None):

        self.workspace = workspace
        self.configuration = configuration
        self.recovery_metadata = dict(recovery_metadata or {})
        self.session = None

    def execute(self):
        """Initialize or restore production runtime session metadata."""

        if self.session is None:
            self.session = self.workspace.bim_manager.initialize_bim_production_runtime(
                self.configuration,
                self.recovery_metadata,
            )
        else:
            self.workspace.bim_manager.add_object(self.session)

    def undo(self):
        """Remove the runtime session metadata."""

        if isinstance(self.session, BIMRuntimeSession):
            self.workspace.bim_manager.remove_object(self.session)


class OptimizeBIMProjectCommand(Command):
    """Undoable command for production BIM optimization metadata."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.before_cache = None
        self.report = None

    def execute(self):
        """Run or restore project optimization metadata."""

        project = self.workspace.bim_manager.ensure_project()
        if self.before_cache is None:
            self.before_cache = dict(project.production_runtime_cache)
        if self.report is None:
            self.report = self.workspace.bim_manager.optimize_bim_project()
        else:
            self.workspace.bim_manager.add_object(self.report)

    def undo(self):
        """Restore previous optimization cache and report state."""

        project = self.workspace.bim_manager.ensure_project()
        if isinstance(self.report, BIMOptimizationReport):
            self.workspace.bim_manager.remove_object(self.report)
        project.production_runtime_cache = dict(self.before_cache or {})
        self.workspace.bim_manager.production_runtime.refresh_diagnostics("Operational")


class ValidateBIMRuntimeCommand(Command):
    """Undoable command for Production BIM Runtime validation."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.before = None
        self.after = None

    def execute(self):
        """Run or restore production runtime validation."""

        project = self.workspace.bim_manager.ensure_project()
        if self.before is None:
            self.before = project.production_runtime_validation_report
        if self.after is None:
            self.after = self.workspace.bim_manager.validate_bim_runtime(self.workspace)
        else:
            project.production_runtime_validation_report = self.after
            self.workspace.bim_manager.production_runtime.refresh_diagnostics("Operational" if self.after.valid else "Blocked")

    def undo(self):
        """Restore previous runtime validation."""

        project = self.workspace.bim_manager.ensure_project()
        project.production_runtime_validation_report = self.before
        self.workspace.bim_manager.production_runtime.refresh_diagnostics("Operational")


class RunBIMProductionRegressionCommand(Command):
    """Undoable command for Production BIM Runtime regression metadata."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.result = None

    def execute(self):
        """Run or restore production regression results."""

        if self.result is None:
            self.result = self.workspace.bim_manager.run_bim_production_regression()
        else:
            self.workspace.bim_manager.add_object(self.result)

    def undo(self):
        """Remove production regression result metadata."""

        if isinstance(self.result, BIMRegressionResult):
            self.workspace.bim_manager.remove_object(self.result)


class CertifyBIMCompatibilityCommand(Command):
    """Undoable command for BIM compatibility certification metadata."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.report = None

    def execute(self):
        """Generate or restore compatibility certification metadata."""

        if self.report is None:
            self.report = self.workspace.bim_manager.certify_bim_compatibility()
        else:
            self.workspace.bim_manager.add_object(self.report)

    def undo(self):
        """Remove compatibility certification metadata."""

        if isinstance(self.report, BIMCompatibilityReport):
            self.workspace.bim_manager.remove_object(self.report)


class CertifyBIMReleaseCommand(Command):
    """Undoable command for Release 1.9 production BIM certification."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.record = None

    def execute(self):
        """Generate or restore release certification metadata."""

        if self.record is None:
            self.record = self.workspace.bim_manager.certify_bim_release()
        else:
            self.workspace.bim_manager.add_object(self.record)

    def undo(self):
        """Remove release certification metadata."""

        if isinstance(self.record, BIMCertificationRecord):
            self.workspace.bim_manager.remove_object(self.record)
