from copy import deepcopy

from engine.product import ProductDocument
from engine.commands.command import Command


class CreateProductDocumentCommand(Command):
    """Undoable command for creating a Product Design document."""

    def __init__(self, workspace, name="Product Document", units="mm", precision=3, metadata=None):

        self.workspace = workspace
        self.document_name = name
        self.units = units
        self.precision = precision
        self.metadata = metadata
        self.document = None

    def execute(self):
        """Create or restore the product document."""

        manager = self.workspace.product_manager

        if self.document is None:
            self.document = manager.create_document(
                self.document_name,
                self.units,
                self.precision,
                self.metadata,
            )
        else:
            manager.add_document(self.document)

    def undo(self):
        """Remove the created product document."""

        if isinstance(self.document, ProductDocument):
            self.workspace.product_manager.remove_object(self.document)


class AddProductObjectCommand(Command):
    """Undoable command for adding Product Design metadata."""

    def __init__(self, workspace, item):

        self.workspace = workspace
        self.item = item

    def execute(self):
        """Add the product item to the workspace-owned manager."""

        self.workspace.product_manager.add_object(self.item)

    def undo(self):
        """Remove the product item from the workspace-owned manager."""

        self.workspace.product_manager.remove_object(self.item)
        self.workspace.selection.unregister_entity(self.item)


class AddProductPartCommand(AddProductObjectCommand):
    """Undoable command for adding a product part."""


class AddProductComponentCommand(AddProductObjectCommand):
    """Undoable command for adding a product component or component metadata."""


class AddProductParameterCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design parameter metadata."""


class AddParametricParameterCommand(AddProductObjectCommand):
    """Undoable command for adding parametric parameter/expression metadata."""


class AddDependencyGraphCommand(AddProductObjectCommand):
    """Undoable command for adding dependency graph metadata."""


class AddLiveSolverCommand(AddProductObjectCommand):
    """Undoable command for adding live solver metadata."""


class AddVisualNodeGraphCommand(AddProductObjectCommand):
    """Undoable command for adding visual node graph metadata."""


class AddDataTreeCommand(AddProductObjectCommand):
    """Undoable command for adding data tree metadata."""


class AddCADNodeCommand(AddProductObjectCommand):
    """Undoable command for adding CAD node metadata."""


class AddBIMNodeCommand(AddProductObjectCommand):
    """Undoable command for adding BIM node metadata."""


class AddManufacturingNodeCommand(AddProductObjectCommand):
    """Undoable command for adding manufacturing node metadata."""


class AddAINodeCommand(AddProductObjectCommand):
    """Undoable command for adding AI node metadata."""


class AddScriptNodeCommand(AddProductObjectCommand):
    """Undoable command for adding script node metadata."""


class AddLivePreviewCommand(AddProductObjectCommand):
    """Undoable command for adding live preview and workspace synchronization metadata."""


class AddExecutionObjectCommand(AddProductObjectCommand):
    """Undoable command for adding Release 2.0 execution metadata."""


class AddSketchSolverCommand(AddProductObjectCommand):
    """Undoable command for adding Release 2.0 sketch solver metadata."""


class AddFeatureExecutionCommand(AddProductObjectCommand):
    """Undoable command for adding Release 2.0 feature execution metadata."""


class AddGeometryKernelCommand(AddProductObjectCommand):
    """Undoable command for adding Release 2.0 GeometryKernel metadata."""


class AddProductMaterialCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design engineering material metadata."""


class AddProductMechanicalMetadataCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design mechanical metadata."""


class AddProductSketchCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design sketch metadata."""


class AddSketchGeometryCommand(AddProductObjectCommand):
    """Undoable command for adding sketch-owned geometry."""


class AddSketchConstraintCommand(AddProductObjectCommand):
    """Undoable command for adding sketch-owned constraints."""


class AddSketchDimensionCommand(AddProductObjectCommand):
    """Undoable command for adding sketch-owned dimensions."""


class ActivateSketchCommand(Command):
    """Undoable command for activating a Product Design sketch."""

    def __init__(self, workspace, sketch):

        self.workspace = workspace
        self.sketch = sketch
        self.previous_sketch_id = None

    def execute(self):
        """Activate the target sketch through ProductManager."""

        manager = self.workspace.product_manager

        if self.previous_sketch_id is None:
            self.previous_sketch_id = manager.active_sketch_id

        manager.sketch_manager.activate(self.sketch)

    def undo(self):
        """Restore the previously active sketch."""

        manager = self.workspace.product_manager

        if self.previous_sketch_id:
            manager.sketch_manager.activate(self.previous_sketch_id)
        else:
            manager.sketch_manager.deactivate()


class DeactivateSketchCommand(Command):
    """Undoable command for deactivating the current Product Design sketch."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.previous_sketch_id = None

    def execute(self):
        """Deactivate the active sketch."""

        manager = self.workspace.product_manager

        if self.previous_sketch_id is None:
            self.previous_sketch_id = manager.active_sketch_id

        manager.sketch_manager.deactivate()

    def undo(self):
        """Restore the previously active sketch when available."""

        if self.previous_sketch_id:
            self.workspace.product_manager.sketch_manager.activate(self.previous_sketch_id)


class AddProductBodyCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design body metadata."""


class AddProductFeatureCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design feature metadata."""


class AddEdgeModificationCommand(AddProductObjectCommand):
    """Undoable command for adding edge modification metadata."""


class AddPatternMetadataCommand(AddProductObjectCommand):
    """Undoable command for adding pattern metadata."""


class AddSurfaceBodyCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design surface body metadata."""


class AddSurfaceOperationCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design surface operation metadata."""


class AddProductCurveCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design curve metadata."""


class AddReferenceGeometryCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design reference geometry metadata."""


class AddConstructionGeometryCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design construction geometry metadata."""


class AddAssemblyObjectCommand(AddProductObjectCommand):
    """Undoable command for adding assembly document or assembly metadata."""


class AddAssemblyComponentCommand(AddProductObjectCommand):
    """Undoable command for adding assembly component or occurrence metadata."""


class AddAssemblyMateCommand(AddProductObjectCommand):
    """Undoable command for adding assembly mate metadata."""


class AddExplodedViewCommand(AddProductObjectCommand):
    """Undoable command for adding assembly exploded view metadata."""


class AddAssemblyConfigurationCommand(AddProductObjectCommand):
    """Undoable command for adding assembly configuration metadata."""


class AddMechanicalLibraryCommand(AddProductObjectCommand):
    """Undoable command for adding mechanical library metadata."""


class AddSheetMetalCommand(AddProductObjectCommand):
    """Undoable command for adding sheet metal metadata."""


class AddSheetMetalRuleCommand(AddProductObjectCommand):
    """Undoable command for adding sheet metal rule metadata."""


class AddProductValidationCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design validation metadata."""


class AddProductAnalysisCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design analysis metadata."""


class AddManufacturingValidationCommand(AddProductObjectCommand):
    """Undoable command for adding manufacturing readiness metadata."""


class AddProductReportCommand(AddProductObjectCommand):
    """Undoable command for adding Product Design report metadata."""


class AddCAMObjectCommand(AddProductObjectCommand):
    """Undoable command for adding CAM foundation metadata."""


class AddThreeAxisCAMObjectCommand(AddProductObjectCommand):
    """Undoable command for adding 3-axis CAM metadata."""


class AddLaserPlasmaObjectCommand(AddProductObjectCommand):
    """Undoable command for adding laser/plasma manufacturing metadata."""


class AddRouterObjectCommand(AddProductObjectCommand):
    """Undoable command for adding CNC router manufacturing metadata."""


class AddPostProcessorObjectCommand(AddProductObjectCommand):
    """Undoable command for adding post processor metadata."""


class AddMachineLibraryObjectCommand(AddProductObjectCommand):
    """Undoable command for adding machine library metadata."""


class AddSlicerObjectCommand(AddProductObjectCommand):
    """Undoable command for adding additive manufacturing slicer metadata."""


class AddSimulationObjectCommand(AddProductObjectCommand):
    """Undoable command for adding manufacturing simulation metadata."""


class AddNestingObjectCommand(AddProductObjectCommand):
    """Undoable command for adding nesting and fabrication metadata."""


class AddManufacturingJobObjectCommand(AddProductObjectCommand):
    """Undoable command for adding manufacturing job-management metadata."""


class AddParametricObjectCommand(AddProductObjectCommand):
    """Undoable command for adding Parametric Engine metadata."""


class AddToolLibraryCommand(AddProductObjectCommand):
    """Undoable command for adding CAM tool library metadata."""


class UpdateCAMOperationCommand(Command):
    """Undoable command for updating CAM operation metadata only."""

    def __init__(self, workspace, operation, **changes):

        self.workspace = workspace
        self.operation = operation
        self.changes = dict(changes)
        self.previous = None

    def execute(self):
        """Apply operation metadata changes through OperationManager."""

        manager = self.workspace.product_manager
        target = manager.operation_manager.operation_for(self.operation)

        if target is None:
            return

        if self.previous is None:
            self.previous = {
                "name": target.name,
                "enabled": target.metadata.enabled,
                "group": target.metadata.group,
                "order": target.metadata.order,
            }

        if "name" in self.changes:
            manager.operation_manager.rename_operation(target, self.changes["name"])
        if "enabled" in self.changes:
            manager.operation_manager.set_enabled(target, self.changes["enabled"])
        if "group" in self.changes:
            manager.operation_manager.set_group(target, self.changes["group"])
        if "order" in self.changes:
            target.metadata.order = int(self.changes["order"])

    def undo(self):
        """Restore previous CAM operation metadata."""

        target = self.workspace.product_manager.operation_manager.operation_for(self.operation)

        if target is None or self.previous is None:
            return

        target.name = self.previous["name"]
        target.metadata.enabled = self.previous["enabled"]
        target.metadata.group = self.previous["group"]
        target.metadata.order = self.previous["order"]


class ApplyProductFeatureCommand(Command):
    """Undoable command for applying a feature to an existing MeshEntity."""

    def __init__(self, workspace, feature):

        self.workspace = workspace
        self.feature = feature
        self.mesh_entity = None
        self.previous_mesh_data = None
        self.previous_parameters = None
        self.previous_primitive_type = None

    def execute(self):
        """Apply the feature through ProductManager."""

        manager = self.workspace.product_manager
        target = manager.feature_manager.feature_for(self.feature)
        body = manager.body_for(getattr(getattr(target, "definition", None), "body_id", ""))
        mesh_entity = manager.mesh_entity_for_body(body, self.workspace)

        if mesh_entity is not None and self.previous_mesh_data is None:
            self.mesh_entity = mesh_entity
            self.previous_mesh_data = mesh_entity.mesh_data
            self.previous_parameters = dict(getattr(mesh_entity, "parameters", {}))
            self.previous_primitive_type = getattr(mesh_entity, "primitive_type", None)

        manager.feature_manager.apply_feature(self.feature, self.workspace)

    def undo(self):
        """Restore the previous MeshEntity mesh data."""

        if self.mesh_entity is None:
            return

        self.mesh_entity.mesh_data = self.previous_mesh_data
        self.mesh_entity.parameters = dict(self.previous_parameters or {})
        self.mesh_entity.primitive_type = self.previous_primitive_type

        target = self.workspace.product_manager.feature_manager.feature_for(self.feature)
        if target is not None:
            target.result.status = "Undone"
            target.result.updated = False
            target.metadata.status = "Pending"


class ExecuteFeatureGeometryCommand(Command):
    """Undoable command for GeometryKernel feature-to-body generation."""

    def __init__(self, workspace, feature, kernel=None):

        self.workspace = workspace
        self.feature = feature
        self.kernel = kernel
        self.result = None
        self.previous_feature = None
        self.previous_bodies = None
        self.previous_scene_entities = None
        self.previous_mesh_state = {}
        self.created_product_items = []
        self.created_scene_entities = []

    def execute(self):
        """Generate feature geometry through the ParametricEngine GeometryKernel."""

        manager = self.workspace.product_manager
        target = manager.feature_manager.feature_for(self.feature)

        if target is None:
            return

        if self.previous_feature is None:
            self.previous_feature = deepcopy(target)
            self.previous_bodies = list(manager.bodies)
            scene = getattr(self.workspace, "scene3d", None)
            self.previous_scene_entities = list(scene.entities()) if scene is not None else []
            for body in manager.bodies:
                mesh = manager.mesh_entity_for_body(body, self.workspace)
                if mesh is not None:
                    mesh_id = getattr(mesh, "id", "") or getattr(mesh, "name", "")
                    self.previous_mesh_state[mesh_id] = {
                        "mesh_data": deepcopy(mesh.mesh_data),
                        "primitive_type": getattr(mesh, "primitive_type", None),
                        "parameters": deepcopy(getattr(mesh, "parameters", {})),
                    }

        before_ids = {
            getattr(item, "id", None)
            for item in (
                manager.geometry_sessions +
                manager.geometry_histories +
                manager.geometry_caches +
                manager.geometry_results +
                manager.geometry_topologies +
                manager.topology_elements
            )
        }
        self.result = manager.parametric_manager.generate_feature_geometry(target, self.workspace, self.kernel)
        scene = getattr(self.workspace, "scene3d", None)
        current_scene = list(scene.entities()) if scene is not None else []
        current_product_items = (
            manager.geometry_sessions +
            manager.geometry_histories +
            manager.geometry_caches +
            manager.geometry_results +
            manager.geometry_topologies +
            manager.topology_elements
        )
        self.created_product_items = [item for item in current_product_items if getattr(item, "id", None) not in before_ids]
        self.created_scene_entities = [entity for entity in current_scene if entity not in (self.previous_scene_entities or [])]

    def undo(self):
        """Restore feature, body and MeshEntity state before generation."""

        manager = self.workspace.product_manager
        target = manager.feature_manager.feature_for(self.feature)

        for item in list(self.created_product_items):
            manager.remove_object(item)

        previous_body_ids = {body.id for body in self.previous_bodies or []}
        for body in list(manager.bodies):
            if body.id not in previous_body_ids:
                manager.remove_object(body)

        for entity in list(self.created_scene_entities):
            self.workspace.remove_3d_entity(entity)

        for body in manager.bodies:
            mesh = manager.mesh_entity_for_body(body, self.workspace)
            state = self.previous_mesh_state.get(getattr(mesh, "id", "") or getattr(mesh, "name", ""))
            if mesh is not None and state is not None:
                mesh.mesh_data = state["mesh_data"]
                mesh.parameters = dict(state["parameters"])
                mesh.primitive_type = state["primitive_type"]

        if target is not None and self.previous_feature is not None:
            target.definition = deepcopy(self.previous_feature.definition)
            target.result = deepcopy(self.previous_feature.result)
            target.metadata = deepcopy(self.previous_feature.metadata)
            target.execution_state = deepcopy(self.previous_feature.execution_state)
            target.execution_metadata = deepcopy(self.previous_feature.execution_metadata)
            target.diagnostics = deepcopy(self.previous_feature.diagnostics)


class SuppressProductFeatureCommand(Command):
    """Undoable command for suppressing or unsuppressing a feature."""

    def __init__(self, workspace, feature, suppressed=True):

        self.workspace = workspace
        self.feature = feature
        self.suppressed = bool(suppressed)
        self.previous = None

    def execute(self):
        """Set feature suppression state."""

        manager = self.workspace.product_manager
        target = manager.feature_manager.feature_for(self.feature)

        if target is not None and self.previous is None:
            self.previous = target.suppressed

        manager.feature_manager.suppress(self.feature, self.suppressed)

    def undo(self):
        """Restore previous suppression state."""

        self.workspace.product_manager.feature_manager.suppress(
            self.feature,
            bool(self.previous),
        )


class ExecuteProductFeatureMetadataCommand(Command):
    """Undoable command for activating feature execution metadata without geometry."""

    def __init__(self, workspace, feature, session=None):

        self.workspace = workspace
        self.feature = feature
        self.session = session
        self.previous = None

    def execute(self):
        """Activate feature execution metadata through FeatureManager."""

        manager = self.workspace.product_manager
        target = manager.feature_manager.feature_for(self.feature)
        if target is None:
            return
        if self.previous is None:
            self.previous = {
                "metadata": target.metadata.to_dict(),
                "result": target.result.to_dict(),
                "execution_state": target.execution_state.to_dict(),
                "execution_metadata": target.execution_metadata.to_dict(),
                "diagnostics": target.diagnostics.to_dict(),
                "display_color": target.display_color,
            }
        manager.feature_manager.execute_feature_metadata(target, self.session)

    def undo(self):
        """Restore previous feature execution metadata."""

        if self.previous is None:
            return
        target = self.workspace.product_manager.feature_manager.feature_for(self.feature)
        if target is None:
            return
        target.metadata = target.metadata.from_dict(self.previous["metadata"])
        target.result = target.result.from_dict(self.previous["result"])
        target.execution_state = target.execution_state.from_dict(self.previous["execution_state"])
        target.execution_metadata = target.execution_metadata.from_dict(self.previous["execution_metadata"])
        target.diagnostics = target.diagnostics.from_dict(self.previous["diagnostics"])
        target.display_color = self.previous["display_color"]


class RollbackProductFeatureCommand(Command):
    """Undoable command for feature timeline rollback metadata."""

    def __init__(self, workspace, feature):

        self.workspace = workspace
        self.feature = feature
        self.previous = None

    def execute(self):
        """Roll back the feature timeline through FeatureManager metadata."""

        manager = self.workspace.product_manager
        target = manager.feature_manager.feature_for(self.feature)
        if target is None:
            return
        history = manager.feature_history_for(target.part_id)
        self.previous = int(getattr(history, "rollback_index", -1)) if self.previous is None else self.previous
        manager.feature_manager.rollback_to(target)

    def undo(self):
        """Restore previous feature rollback position."""

        manager = self.workspace.product_manager
        target = manager.feature_manager.feature_for(self.feature)
        if target is None:
            return
        if self.previous is None or self.previous < 0:
            manager.feature_manager.roll_forward(target.part_id)
            return
        ordered = manager.feature_manager.features_for_part(target.part_id)
        if self.previous < len(ordered):
            manager.feature_manager.rollback_to(ordered[self.previous])


class RollForwardProductFeaturesCommand(Command):
    """Undoable command for clearing feature rollback metadata."""

    def __init__(self, workspace, part):

        self.workspace = workspace
        self.part = part
        self.previous = None

    def execute(self):
        """Roll the feature timeline forward through FeatureManager metadata."""

        manager = self.workspace.product_manager
        part_id = getattr(self.part, "id", self.part)
        history = manager.feature_history_for(part_id)
        self.previous = int(getattr(history, "rollback_index", -1)) if self.previous is None else self.previous
        manager.feature_manager.roll_forward(part_id)

    def undo(self):
        """Restore previous rollback metadata."""

        if self.previous is None or self.previous < 0:
            return
        manager = self.workspace.product_manager
        ordered = manager.feature_manager.features_for_part(self.part)
        if self.previous < len(ordered):
            manager.feature_manager.rollback_to(ordered[self.previous])


class RenameProductFeatureCommand(Command):
    """Undoable command for renaming a feature."""

    def __init__(self, workspace, feature, name):

        self.workspace = workspace
        self.feature = feature
        self.new_name = name
        self.previous = None

    def execute(self):
        """Rename the feature."""

        target = self.workspace.product_manager.feature_manager.feature_for(self.feature)

        if target is not None and self.previous is None:
            self.previous = target.name

        self.workspace.product_manager.feature_manager.rename(self.feature, self.new_name)

    def undo(self):
        """Restore the previous feature name."""

        if self.previous is not None:
            self.workspace.product_manager.feature_manager.rename(self.feature, self.previous)


class EditProductFeatureCommand(Command):
    """Undoable command for editing feature parameters and marking regeneration state."""

    def __init__(self, workspace, feature, **changes):

        self.workspace = workspace
        self.feature = feature
        self.changes = dict(changes)
        self.previous = None

    def execute(self):
        """Apply editable feature changes."""

        manager = self.workspace.product_manager
        target = manager.feature_manager.feature_for(self.feature)

        if target is not None and self.previous is None:
            self.previous = {
                "name": target.name,
                "visible": target.visible,
                "suppressed": target.suppressed,
                "options": target.definition.options.to_dict(),
                "parameters": dict(target.definition.parameters),
            }

        manager.feature_editor.edit_feature(self.feature, **self.changes)

    def undo(self):
        """Restore previous editable feature state."""

        if self.previous is None:
            return

        manager = self.workspace.product_manager
        target = manager.feature_manager.feature_for(self.feature)

        if target is None:
            return

        target.name = self.previous["name"]
        target.visible = self.previous["visible"]
        target.suppressed = self.previous["suppressed"]
        for key, value in self.previous["options"].items():
            setattr(target.definition.options, key, value)
        target.definition.parameters = dict(self.previous["parameters"])
        manager.regeneration_manager.mark_dirty(target)


class AddFeatureDependencyCommand(Command):
    """Undoable command for storing a feature dependency edge."""

    def __init__(self, workspace, source, target, relationship="DependsOn"):

        self.workspace = workspace
        self.source = source
        self.target = target
        self.relationship = relationship
        self.edge = None

    def execute(self):
        """Store dependency metadata only."""

        if self.edge is None:
            self.edge = self.workspace.product_manager.dependency_manager.add_edge(
                self.source,
                self.target,
                self.relationship,
            )
        elif self.edge not in self.workspace.product_manager.dependency_edges:
            self.workspace.product_manager.dependency_edges.append(self.edge)

    def undo(self):
        """Remove stored dependency edge."""

        edges = self.workspace.product_manager.dependency_edges
        if self.edge in edges:
            edges.remove(self.edge)


class RegenerateProductFeatureCommand(Command):
    """Undoable command for rebuilding a feature against existing MeshEntity geometry."""

    def __init__(self, workspace, feature, downstream=False):

        self.workspace = workspace
        self.feature = feature
        self.downstream = bool(downstream)
        self.previous_mesh = {}

    def execute(self):
        """Regenerate one feature or downstream features."""

        manager = self.workspace.product_manager
        features = [manager.feature_manager.feature_for(self.feature)]

        if self.downstream and features[0] is not None:
            all_features = manager.feature_manager.features_for_part(features[0].part_id)
            start = all_features.index(features[0])
            features = all_features[start:]

        for feature in [item for item in features if item is not None]:
            body = manager.body_for(feature.definition.body_id or feature.result.body_id)
            mesh = manager.mesh_entity_for_body(body, self.workspace)
            if mesh is not None and feature.id not in self.previous_mesh:
                self.previous_mesh[feature.id] = (
                    mesh,
                    mesh.mesh_data,
                    dict(getattr(mesh, "parameters", {})),
                    getattr(mesh, "primitive_type", None),
                )

        if self.downstream:
            manager.regeneration_manager.rebuild_downstream(self.feature, self.workspace)
        else:
            manager.regeneration_manager.rebuild_feature(self.feature, self.workspace)

    def undo(self):
        """Restore MeshEntity data before regeneration."""

        manager = self.workspace.product_manager

        for feature_id, (mesh, mesh_data, parameters, primitive_type) in self.previous_mesh.items():
            mesh.mesh_data = mesh_data
            mesh.parameters = dict(parameters)
            mesh.primitive_type = primitive_type
            feature = manager.feature_manager.feature_for(feature_id)
            if feature is not None:
                manager.regeneration_manager.mark_dirty(feature)


class PropagateProductUpdateCommand(Command):
    """Undoable command for processing queued update metadata."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.previous_states = {}
        self.processed = []

    def execute(self):
        """Process queued updates without solving."""

        manager = self.workspace.product_manager
        self.previous_states = {
            key: state.to_dict()
            for key, state in manager.feature_states.items()
        }
        self.processed = manager.update_manager.propagate(self.workspace)

    def undo(self):
        """Restore previous dirty-state metadata."""

        manager = self.workspace.product_manager
        for key, state_data in self.previous_states.items():
            manager.feature_states[key] = manager.feature_states[key].from_dict(state_data)

        for context in self.processed:
            if context.id not in manager.update_queue.context_ids:
                manager.update_queue.context_ids.append(context.id)


class AssignProductMaterialCommand(Command):
    """Undoable command for assigning an engineering material to a product part."""

    def __init__(self, workspace, part, material):

        self.workspace = workspace
        self.part = part
        self.material = material
        self.before_material_id = None
        self.before_material_name = None

    def execute(self):
        """Assign the engineering material through ProductManager."""

        if self.before_material_id is None:
            self.before_material_id = getattr(self.part, "engineering_material_id", "")
            self.before_material_name = getattr(getattr(self.part, "metadata", None), "material", "")

        self.workspace.product_manager.engineering_material_manager.assign_material(
            self.part,
            self.material,
        )

    def undo(self):
        """Restore the previous material assignment."""

        self.part.engineering_material_id = self.before_material_id or ""

        if getattr(self.part, "metadata", None) is not None:
            self.part.metadata.material = self.before_material_name or ""


class RemoveProductObjectCommand(Command):
    """Undoable command for removing Product Design metadata."""

    def __init__(self, workspace, item):

        self.workspace = workspace
        self.item = item
        self.removed = None

    def execute(self):
        """Remove the product item."""

        self.removed = self.item
        self.workspace.product_manager.remove_object(self.item)
        self.workspace.selection.unregister_entity(self.item)

    def undo(self):
        """Restore the removed product item."""

        if self.removed is not None:
            self.workspace.product_manager.add_object(self.removed)
