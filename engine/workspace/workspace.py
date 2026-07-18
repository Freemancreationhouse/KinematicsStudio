from engine.commands import CommandManager
from engine.annotations3d import AnnotationManager3D, ReviewManager
from engine.bcf import BCFManager
from engine.bim import BIMManager
from engine.blocks import BlockManager
from engine.collaboration import CollaborationManager, IssueManager
from engine.clashes import ClashManager
from engine.construction_planes import ConstructionPlaneManager
from engine.constraints import ConstraintManager
from engine.coordination_package import CoordinationPackageManager
from engine.coordinate_systems import CoordinateSystemManager
from engine.dimensions import DimensionStyleManager
from engine.groups import GroupManager
from engine.import3d import ImportManager
from engine.layers.layer_manager import LayerManager
from engine.measurements import MeasurementManager
from engine.model_compare import ModelCompareManager
from engine.patterns import PatternManager
from engine.product import ProductManager
from engine.references3d import CoordinationManager, ReferenceManager
from engine.scene3d import Scene3D
from engine.scene_organization import DisplayPresetManager, SceneCollectionManager, ViewFilterManager
from engine.sections import SectionManager
from engine.snap import SnapManager3D
from engine.transform_gizmo import TransformGizmo
from engine.view_states import DisplayModeManager, ViewStateManager, VisualStyleManager
from engine.workspace.selection_manager import SelectionManager


class WorkspaceEntityList(list):
    """List that assigns workspace layer metadata as entities are stored."""

    def __init__(self, workspace):

        super().__init__()
        self.workspace = workspace

    # --------------------------------

    def append(self, entity):

        self.workspace.assign_layer(entity)
        super().append(entity)

    # --------------------------------

    def insert(self, index, entity):

        self.workspace.assign_layer(entity)
        super().insert(index, entity)

    # --------------------------------

    def extend(self, entities):

        for entity in entities:
            self.append(entity)

    # --------------------------------

    def remove(self, entity):

        self.workspace.unregister_layer_entity(entity)
        super().remove(entity)

    # --------------------------------

    def pop(self, index=-1):

        entity = super().pop(index)
        self.workspace.unregister_layer_entity(entity)

        return entity

    # --------------------------------

    def clear(self):

        for entity in list(self):
            self.workspace.unregister_layer_entity(entity)

        super().clear()


class Workspace:
    """Owns model entities, selection state, and command history."""

    def __init__(self, name="Workspace"):

        self.name = name
        self.project_settings = {}

        self.layer_manager = LayerManager()
        self.layers = self.layer_manager
        self.dimension_style_manager = DimensionStyleManager()
        self.dimension_styles = self.dimension_style_manager
        self.pattern_manager = PatternManager()
        self.patterns = self.pattern_manager
        self.block_manager = BlockManager()
        self.blocks = self.block_manager
        self.block_edit_definition = None
        self.block_edit_entities = []
        self.group_manager = GroupManager()
        self.groups = self.group_manager
        self.constraint_manager = ConstraintManager(self)
        self.constraints = self.constraint_manager
        self.scene3d = Scene3D()
        self.construction_plane_manager = ConstructionPlaneManager()
        self.construction_planes = self.construction_plane_manager
        self.coordinate_system_manager = CoordinateSystemManager()
        self.coordinate_systems = self.coordinate_system_manager
        self.measurement_manager = MeasurementManager()
        self.measurements = self.measurement_manager
        self.section_manager = SectionManager()
        self.sections = self.section_manager
        self.view_state_manager = ViewStateManager()
        self.view_states = self.view_state_manager
        self.display_mode_manager = DisplayModeManager()
        self.display_modes = self.display_mode_manager
        self.visual_style_manager = VisualStyleManager()
        self.visual_styles = self.visual_style_manager
        self.scene_collection_manager = SceneCollectionManager()
        self.scene_collections = self.scene_collection_manager
        self.view_filter_manager = ViewFilterManager()
        self.view_filters = self.view_filter_manager
        self.display_preset_manager = DisplayPresetManager()
        self.display_presets = self.display_preset_manager
        self.annotation_manager3d = AnnotationManager3D()
        self.annotations3d = self.annotation_manager3d
        self.review_manager = ReviewManager()
        self.reviews = self.review_manager
        self.collaboration_manager = CollaborationManager()
        self.collaboration = self.collaboration_manager
        self.issue_manager = IssueManager()
        self.issues = self.issue_manager
        self.reference_manager = ReferenceManager()
        self.references = self.reference_manager
        self.import_manager = ImportManager()
        self.imports = self.import_manager
        self.coordination_manager = CoordinationManager()
        self.coordination = self.coordination_manager
        self.clash_manager = ClashManager()
        self.clashes = self.clash_manager
        self.bcf_manager = BCFManager()
        self.bcf = self.bcf_manager
        self.model_compare_manager = ModelCompareManager()
        self.model_compare = self.model_compare_manager
        self.revision_manager = self.model_compare_manager.revision_manager
        self.timeline_manager = self.model_compare_manager.timeline_manager
        self.coordination_package_manager = CoordinationPackageManager()
        self.coordination_packages = self.coordination_package_manager
        self.archive_manager = self.coordination_package_manager.archive_manager
        self.bim_manager = BIMManager()
        self.bim = self.bim_manager
        self.product_manager = ProductManager()
        self.products = self.product_manager
        self.snap_manager3d = SnapManager3D()
        self.transform_gizmo = TransformGizmo()
        self.entities = WorkspaceEntityList(self)

        self.selection = SelectionManager()

        self.command_manager = CommandManager()

    # --------------------------------

    def add_entity(self, entity):
        """Store an entity in this workspace."""

        self.entities.append(entity)

    # --------------------------------

    def remove_entity(self, entity):
        """Remove an entity from this workspace if present."""

        if entity in self.entities:

            self.entities.remove(entity)

    # --------------------------------

    def clear(self):
        """Remove all entities from this workspace."""

        self.entities.clear()
        for entity in list(self.scene3d.entities()):
            self.unregister_layer_entity(entity)
        self.scene3d.clear()
        self.measurement_manager.measurements.clear()
        self.section_manager.sections.clear()
        self.section_manager.active = None
        self.annotation_manager3d.annotations.clear()
        self.review_manager.items.clear()
        self.collaboration_manager.sessions.clear()
        self.collaboration_manager.active = None
        self.issue_manager.issues.clear()
        self.reference_manager.models.clear()
        self.reference_manager.instances.clear()
        self.reference_manager.isolated_model_ids.clear()
        self.import_manager.adapter_settings.clear()
        self.import_manager.last_result = None
        self.import_manager.progress = 0.0
        self.import_manager.validation_manager.last_report = self.import_manager.validation_manager.last_report.__class__()
        self.coordination_manager.rules.clear()
        self.coordination_manager.conflicts.clear()
        self.clash_manager.results.clear()
        self.clash_manager.groups.clear()
        self.bcf_manager.projects.clear()
        self.bcf_manager.active_project_id = None
        self.model_compare_manager.sessions.clear()
        self.model_compare_manager.active_session_id = None
        self.model_compare_manager.revision_manager.revisions.clear()
        self.model_compare_manager.revision_manager.active_revision_id = None
        self.model_compare_manager.timeline_manager.timeline.entries.clear()
        self.model_compare_manager.timeline_manager.timeline.bookmarks.clear()
        self.coordination_package_manager.packages.clear()
        self.coordination_package_manager.active_package_id = None
        self.coordination_package_manager.archive_manager.archives.clear()
        self.bim_manager.clear()
        self.product_manager.clear()

    # --------------------------------

    def visible_entities(self):
        """Return entities currently available for rendering and snapping."""

        return [
            entity for entity in self.entities
            if getattr(entity, "visible", True) and self.entity_layer_visible(entity)
        ]

    # --------------------------------

    def selectable_entities(self):
        """Return visible entities that are not locked."""

        entities = [
            entity for entity in self.visible_entities()
            if (
                not getattr(entity, "locked", False) and
                not self.entity_layer_locked(entity)
            )
        ]

        if hasattr(self, "constraint_manager"):
            entities.extend(self.constraint_manager.selectable_constraints())

        return entities

    # --------------------------------

    def bounds(self):
        """Return the combined bounding box of visible entities."""

        visible = self.visible_entities()

        if not visible:
            return None

        from engine.geometry import BoundingBox

        bounds = BoundingBox()

        for entity in visible:
            box = entity.bounding_box
            bounds.add(box.min)
            bounds.add(box.max)

        return bounds

    # --------------------------------

    def snap_candidates(self):
        """Return visible entities that can participate in snapping."""

        return self.visible_entities()

    # --------------------------------

    def add_3d_entity(self, entity):
        """Store a 3D scene entity in this workspace."""

        self.assign_layer(entity)
        return self.scene3d.add_entity(entity)

    # --------------------------------

    def remove_3d_entity(self, entity):
        """Remove a 3D scene entity from this workspace."""

        self.unregister_layer_entity(entity)
        self.selection.unregister_entity(entity)
        return self.scene3d.remove_entity(entity)

    # --------------------------------

    def visible_3d_entities(self):
        """Return visible 3D scene entities."""

        return [
            entity for entity in self.scene3d.visible_entities()
            if (
                self.entity_layer_visible(entity) and
                self.section_manager.is_entity_visible(entity) and
                self.scene_collection_manager.entity_visible(entity) and
                self.view_filter_manager.matches(entity, self)
            )
        ]

    # --------------------------------

    def selectable_3d_entities(self):
        """Return selectable 3D scene entities."""

        entities = [
            entity for entity in self.visible_3d_entities()
            if (
                not getattr(entity, "locked", False) and
                not self.entity_layer_locked(entity) and
                not self.scene_collection_manager.entity_locked(entity)
            )
        ]

        entities.extend([
            measurement for measurement in self.visible_measurements()
            if (
                not getattr(measurement, "locked", False) and
                self.view_filter_manager.matches(measurement, self)
            )
        ])
        entities.extend([
            section for section in self.visible_sections()
            if (
                not getattr(section, "locked", False) and
                not self.entity_layer_locked(section) and
                self.view_filter_manager.matches(section, self)
            )
        ])
        entities.extend([
            annotation for annotation in self.visible_annotations3d()
            if (
                not getattr(annotation, "locked", False) and
                not self.entity_layer_locked(annotation) and
                not self.scene_collection_manager.entity_locked(annotation)
            )
        ])
        entities.extend([
            issue for issue in self.visible_issues()
            if (
                not getattr(issue, "locked", False) and
                not self.entity_layer_locked(issue) and
                not self.scene_collection_manager.entity_locked(issue)
            )
        ])
        entities.extend([
            reference for reference in self.visible_references()
            if (
                not getattr(reference, "locked", False) and
                not self._reference_model_locked(reference) and
                not self.entity_layer_locked(reference) and
                not self.scene_collection_manager.entity_locked(reference)
            )
        ])
        entities.extend([
            clash for clash in self.visible_clashes()
            if not getattr(clash, "locked", False)
        ])
        entities.extend([
            topic for topic in self.visible_bcf_topics()
            if not getattr(topic, "locked", False)
        ])
        entities.extend([
            result for result in self.visible_compare_results()
            if not getattr(result, "locked", False)
        ])
        entities.extend([
            revision for revision in self.visible_revisions()
            if not getattr(revision, "locked", False)
        ])
        entities.extend([
            package for package in self.visible_coordination_packages()
            if not getattr(package, "locked", False)
        ])
        entities.extend([
            item for item in self.visible_bim_objects()
            if (
                not getattr(item, "locked", False) and
                not self.entity_layer_locked(item) and
                not self.scene_collection_manager.entity_locked(item)
            )
        ])
        entities.extend([
            item for item in self.visible_product_objects()
            if (
                not getattr(item, "locked", False) and
                not self.entity_layer_locked(item) and
                not self.scene_collection_manager.entity_locked(item)
            )
        ])

        return entities

    # --------------------------------

    def visible_product_objects(self):
        """Return visible Product Design parts and component metadata."""

        manager = getattr(self, "product_manager", None)

        if manager is None:
            return []

        return [
            item for item in manager.visible_objects()
            if (
                self.entity_layer_visible(item) and
                self.scene_collection_manager.entity_visible(item) and
                self.view_filter_manager.matches(item, self)
            )
        ]

    # --------------------------------

    def visible_bim_objects(self):
        """Return visible BIM levels, grids and object metadata."""

        manager = getattr(self, "bim_manager", None)

        if manager is None:
            return []

        return [
            item for item in manager.visible_objects()
            if (
                self.entity_layer_visible(item) and
                self.scene_collection_manager.entity_visible(item) and
                self.view_filter_manager.matches(item, self)
            )
        ]

    # --------------------------------

    def visible_coordination_packages(self):
        """Return visible coordination delivery packages."""

        manager = getattr(self, "coordination_package_manager", None)

        if manager is None:
            return []

        return [
            package for package in manager.visible_packages()
            if (
                self.scene_collection_manager.entity_visible(package) and
                self.view_filter_manager.matches(package, self)
            )
        ]

    # --------------------------------

    def visible_revisions(self):
        """Return visible model coordination revisions."""

        manager = getattr(self, "revision_manager", None)

        if manager is None:
            return []

        return [
            revision for revision in manager.visible_revisions()
            if (
                self.scene_collection_manager.entity_visible(revision) and
                self.view_filter_manager.matches(revision, self)
            )
        ]

    # --------------------------------

    def visible_compare_results(self):
        """Return visible model comparison markers."""

        manager = getattr(self, "model_compare_manager", None)

        if manager is None:
            return []

        return [
            result for result in manager.visible_results()
            if (
                self.scene_collection_manager.entity_visible(result) and
                self.view_filter_manager.matches(result, self)
            )
        ]

    # --------------------------------

    def visible_bcf_topics(self):
        """Return visible BCF coordination topics."""

        manager = getattr(self, "bcf_manager", None)

        if manager is None:
            return []

        return [
            topic for topic in manager.visible_topics()
            if (
                self.scene_collection_manager.entity_visible(topic) and
                self.view_filter_manager.matches(topic, self)
            )
        ]

    # --------------------------------

    def visible_clashes(self):
        """Return visible persistent clash markers."""

        manager = getattr(self, "clash_manager", None)

        if manager is None:
            return []

        return [
            clash for clash in manager.visible_results()
            if (
                self.entity_layer_visible(clash) and
                self.scene_collection_manager.entity_visible(clash) and
                self.view_filter_manager.matches(clash, self)
            )
        ]

    # --------------------------------

    def visible_references(self):
        """Return visible external reference instances."""

        manager = getattr(self, "reference_manager", None)

        if manager is None:
            return []

        return [
            reference for reference in manager.visible_instances()
            if (
                self.entity_layer_visible(reference) and
                self.scene_collection_manager.entity_visible(reference) and
                self.view_filter_manager.matches(reference, self)
            )
        ]

    # --------------------------------

    def _reference_model_locked(self, reference):

        manager = getattr(self, "reference_manager", None)

        if manager is None:
            return False

        model = manager.get_model(getattr(reference, "model_id", None))

        return bool(
            model is not None and (
                getattr(model, "locked", False) or
                model.layers_locked()
            )
        )

    # --------------------------------

    def visible_issues(self):
        """Return visible persistent 3D issue markers."""

        manager = getattr(self, "issue_manager", None)

        if manager is None:
            return []

        return [
            issue for issue in manager.visible_issues()
            if (
                self.entity_layer_visible(issue) and
                self.scene_collection_manager.entity_visible(issue) and
                self.view_filter_manager.matches(issue, self)
            )
        ]

    # --------------------------------

    def visible_annotations3d(self):
        """Return visible persistent 3D annotations."""

        manager = getattr(self, "annotation_manager3d", None)

        if manager is None:
            return []

        return [
            annotation for annotation in manager.visible_annotations()
            if (
                self.entity_layer_visible(annotation) and
                self.scene_collection_manager.entity_visible(annotation) and
                self.view_filter_manager.matches(annotation, self)
            )
        ]

    # --------------------------------

    def visible_sections(self):
        """Return visible persistent 3D section planes."""

        manager = getattr(self, "section_manager", None)

        if manager is None:
            return []

        return [
            section for section in manager.visible_sections()
            if (
                self.entity_layer_visible(section) and
                self.scene_collection_manager.entity_visible(section) and
                self.view_filter_manager.matches(section, self)
            )
        ]

    # --------------------------------

    def visible_measurements(self):
        """Return visible persistent 3D measurements."""

        manager = getattr(self, "measurement_manager", None)

        if manager is None or not manager.settings.visible:
            return []

        return [
            measurement for measurement in manager.measurements
            if (
                getattr(measurement, "visible", True) and
                self.scene_collection_manager.entity_visible(measurement) and
                self.view_filter_manager.matches(measurement, self)
            )
        ]

    # --------------------------------

    def begin_block_edit(self, definition):
        """Open a block definition for internal editing."""

        target = self.block_manager._coerce_definition(definition)

        if target is None:
            return []

        self.block_edit_definition = target
        self.block_edit_entities = target.clone_entities()

        return self.block_edit_entities

    # --------------------------------

    def save_block_edit(self):
        """Save the active block edit session through the command system."""

        if self.block_edit_definition is None:
            return False

        from engine.commands import EditBlockCommand

        self.command_manager.execute(
            EditBlockCommand(
                self.block_edit_definition,
                self.block_edit_entities,
                self.block_manager,
            )
        )
        self.exit_block_edit()

        return True

    # --------------------------------

    def exit_block_edit(self):
        """Leave block edit mode without changing workspace entities."""

        self.block_edit_definition = None
        self.block_edit_entities = []

    # --------------------------------

    @property
    def current_layer(self):
        """Return the current layer used for new entities."""

        return self.layer_manager.current

    # --------------------------------

    def set_current_layer(self, layer):
        """Set the current layer by layer name, ID, or object."""

        self.layer_manager.set_current(layer)

    # --------------------------------

    def create_layer(
        self,
        name,
        color="#FFFFFF",
        line_type="Continuous",
        line_weight=1.0,
    ):
        """Create a layer through the workspace-owned manager."""

        return self.layer_manager.create(
            name,
            color,
            line_type,
            line_weight
        )

    # --------------------------------

    def rename_layer(self, layer, new_name):
        """Rename a workspace layer."""

        return self.layer_manager.rename(layer, new_name)

    # --------------------------------

    def update_layer_properties(
        self,
        layer,
        color=None,
        line_type=None,
        line_weight=None,
    ):
        """Update layer display properties."""

        changed = self.layer_manager.set_properties(
            layer,
            color,
            line_type,
            line_weight
        )

        if changed:
            target = self.layer_manager._coerce_layer(layer)

            for entity in list(getattr(target, "entities", [])):
                entity.color = target.color

        return changed

    # --------------------------------

    def delete_layer(self, layer):
        """Delete a non-default layer and move its entities to Layer 0."""

        target = self.layer_manager._coerce_layer(layer)
        default = self.layer_manager.get("0")

        if target is None or target is default:
            return False

        for entity in list(self.entities) + list(self.scene3d.entities()):
            if self._entity_layer(entity) is target:
                self.assign_layer(entity, default)

        self.layer_manager.remove(target)

        return True

    # --------------------------------

    def assign_layer(self, entity, layer=None):
        """Assign an entity to a layer when it has no valid layer."""

        target = layer or self._entity_layer(entity) or self.current_layer

        if target is None:
            return entity

        self.unregister_layer_entity(entity)
        entity.layer = target
        entity.layer_id = target.id
        entity.layer_name = target.name
        entity.color = target.color
        target.add(entity)
        self.assign_dimension_style(entity)
        self.assign_pattern(entity)

        return entity

    # --------------------------------

    @property
    def current_pattern(self):
        """Return the current hatch pattern for new hatch entities."""

        return self.pattern_manager.current

    # --------------------------------

    def set_current_pattern(self, pattern):
        """Set the current hatch pattern by name or object."""

        return self.pattern_manager.set_current(pattern)

    # --------------------------------

    def register_pattern(self, pattern):
        """Register a hatch pattern with the workspace manager."""

        return self.pattern_manager.register(pattern)

    # --------------------------------

    def assign_pattern(self, entity, pattern=None):
        """Assign current pattern metadata to hatch entities."""

        if not getattr(entity, "is_hatch", False):
            return entity

        target = pattern

        if target is None:
            existing = self._entity_pattern(entity)
            target = existing if existing and getattr(entity, "pattern", None) else self.current_pattern

        if target is None:
            return entity

        entity.pattern = target
        entity.pattern_name = target.name

        if not getattr(entity, "pattern_scale", None):
            entity.pattern_scale = target.scale

        if getattr(entity, "pattern_angle", None) is None:
            entity.pattern_angle = target.angle

        return entity

    # --------------------------------

    def entity_pattern(self, entity):
        """Return the pattern assigned to a hatch entity."""

        return self._entity_pattern(entity)

    # --------------------------------

    def _entity_pattern(self, entity):

        pattern = getattr(entity, "pattern", None)

        if pattern is not None and self.pattern_manager.get(pattern.name) is pattern:
            return pattern

        pattern_name = getattr(entity, "pattern_name", None)

        if pattern_name:
            return self.pattern_manager.get(pattern_name)

        return None

    # --------------------------------

    @property
    def current_dimension_style(self):
        """Return the current style used by new dimension entities."""

        return self.dimension_style_manager.current

    # --------------------------------

    def set_current_dimension_style(self, style):
        """Set the current dimension style by style name, ID, or object."""

        return self.dimension_style_manager.set_current(style)

    # --------------------------------

    def create_dimension_style(self, name, **values):
        """Create a dimension style through the workspace-owned manager."""

        return self.dimension_style_manager.create(name, **values)

    # --------------------------------

    def rename_dimension_style(self, style, new_name):
        """Rename a non-default dimension style."""

        return self.dimension_style_manager.rename(style, new_name)

    # --------------------------------

    def delete_dimension_style(self, style):
        """Delete a non-default dimension style."""

        return self.dimension_style_manager.remove(style)

    # --------------------------------

    def assign_dimension_style(self, entity, style=None):
        """Assign current dimension style metadata to dimension entities."""

        if not getattr(entity, "is_dimension", False):
            return entity

        target = style or self._entity_dimension_style(entity) or self.current_dimension_style

        if target is None:
            return entity

        entity.dimension_style = target
        entity.dimension_style_id = target.id
        entity.dimension_style_name = target.name

        return entity

    # --------------------------------

    def entity_dimension_style(self, entity):
        """Return the dimension style assigned to an entity."""

        return self._entity_dimension_style(entity)

    # --------------------------------

    def _entity_dimension_style(self, entity):

        style = getattr(entity, "dimension_style", None)

        if style is not None and self.dimension_style_manager.get_by_id(style.id) is style:
            return style

        style_id = getattr(entity, "dimension_style_id", None)

        if style_id is not None:
            style = self.dimension_style_manager.get_by_id(style_id)

            if style is not None:
                return style

        style_name = getattr(entity, "dimension_style_name", None)

        if style_name:
            return self.dimension_style_manager.get(style_name)

        return None

    # --------------------------------

    def assign_replacement_layer(self, source, replacements):
        """Assign replacement entities to the same layer as their source."""

        layer = self._entity_layer(source) or self.current_layer

        for entity in replacements:
            self.assign_layer(entity, layer)

        return replacements

    # --------------------------------

    def unregister_layer_entity(self, entity):
        """Remove an entity from the layer tracking list if needed."""

        layer = self._entity_layer(entity)

        if layer is not None:
            layer.remove(entity)

        if hasattr(self, "group_manager"):
            self.group_manager.unregister_entity(entity)

        if hasattr(self, "selection"):
            self.selection.unregister_entity(entity)

        if hasattr(self, "constraint_manager"):
            for constraint in list(self.constraint_manager.constraints_for_entity(entity)):
                self.constraint_manager.remove(constraint)

    # --------------------------------

    def selection_entities_for(self, entity):
        """Return entities that should be selected for a picked entity."""

        if hasattr(self, "group_manager"):
            return self.group_manager.expand_selection(entity)

        return [entity]

    # --------------------------------

    def entity_layer(self, entity):
        """Return the layer assigned to an entity."""

        return self._entity_layer(entity)

    # --------------------------------

    def entity_layer_visible(self, entity):
        """Return True when the entity's layer is visible."""

        if getattr(entity, "is_constraint", False):
            return True

        layer = self._entity_layer(entity)

        return True if layer is None else layer.visible

    # --------------------------------

    def entity_layer_locked(self, entity):
        """Return True when the entity's layer is locked."""

        if getattr(entity, "is_constraint", False):
            return False

        layer = self._entity_layer(entity)

        return False if layer is None else layer.locked

    # --------------------------------

    def _entity_layer(self, entity):

        layer = getattr(entity, "layer", None)

        if layer is not None and self.layer_manager.get_by_id(layer.id) is layer:
            return layer

        layer_id = getattr(entity, "layer_id", None)

        if layer_id is not None:
            layer = self.layer_manager.get_by_id(layer_id)

            if layer is not None:
                return layer

        layer_name = getattr(entity, "layer_name", None)

        if layer_name:
            return self.layer_manager.get(layer_name)

        return None

    # --------------------------------

    @property
    def count(self):

        return len(self.entities)
