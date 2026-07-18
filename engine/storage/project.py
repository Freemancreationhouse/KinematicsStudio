import json
import os
from pathlib import Path

from engine.blocks.block_definition import BlockDefinition
from engine.entities import (
    AlignedDimensionEntity,
    AngularDimensionEntity,
    ArcEntity,
    BlockReference,
    CircleEntity,
    DiameterDimensionEntity,
    HatchEntity,
    LeaderEntity,
    LineEntity,
    LinearDimensionEntity,
    MTextEntity,
    PolylineEntity,
    RadiusDimensionEntity,
    RectangleEntity,
    SplineEntity,
    TextEntity,
    entity3d_from_dict,
)
from engine.geometry import Vector2
from engine.groups.group import Group
from engine.layers.layer import Layer
from engine.patterns import Pattern
from engine.workspace import Workspace


PROJECT_FORMAT_VERSION = 1


class ProjectFormatError(ValueError):
    """Raised when a project file cannot be loaded safely."""


class ProjectSerializer:
    """Versioned JSON persistence for V2 workspaces and managers."""

    VERSION = PROJECT_FORMAT_VERSION

    # --------------------------------

    def save(self, workspace, path, settings=None):
        """Save a workspace to a versioned project file."""

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict(workspace, settings=settings)
        temporary = target.with_suffix(target.suffix + ".tmp")

        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)

        os.replace(temporary, target)

        return target

    # --------------------------------

    def load(self, path):
        """Load a workspace from a versioned project file."""

        source = Path(path)

        with source.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        return self.from_dict(payload)

    # --------------------------------

    def to_dict(self, workspace, settings=None):
        """Return a JSON-safe project dictionary."""

        project_settings = (
            settings
            if settings is not None
            else getattr(workspace, "project_settings", {})
        )
        entity_ids = {
            entity: index
            for index, entity in enumerate(workspace.entities)
        }

        return {
            "format": "KinematicsStudioProject",
            "version": self.VERSION,
            "workspace": {
                "name": workspace.name,
                "entities": [
                    self._entity_to_data(entity, entity_ids)
                    for entity in workspace.entities
                ],
                "layers": self._layers_to_data(workspace),
                "blocks": self._blocks_to_data(workspace, entity_ids),
                "groups": self._groups_to_data(workspace, entity_ids),
                "selection_sets": self._selection_sets_to_data(workspace, entity_ids),
                "constraints": self._constraints_to_data(workspace, entity_ids),
                "patterns": self._patterns_to_data(workspace),
                "dimension_styles": self._dimension_styles_to_data(workspace),
                "settings": dict(project_settings or {}),
                "scene3d": self._scene3d_to_data(workspace),
            },
        }

    # --------------------------------

    def from_dict(self, payload):
        """Reconstruct a workspace from project data."""

        self._validate_payload(payload)
        workspace_data = payload.get("workspace", {})
        workspace = Workspace(workspace_data.get("name", "Model"))
        workspace.project_settings = dict(workspace_data.get("settings", {}))
        context = {
            "workspace": workspace,
            "entity_by_id": {},
            "definition_by_id": {},
        }

        self._restore_layers(workspace, workspace_data.get("layers", {}))
        self._restore_patterns(workspace, workspace_data.get("patterns", {}))
        self._restore_dimension_styles(
            workspace,
            workspace_data.get("dimension_styles", {})
        )
        self._restore_blocks(
            workspace,
            workspace_data.get("blocks", {}),
            context,
        )
        self._restore_entities(
            workspace,
            workspace_data.get("entities", []),
            context,
        )
        self._restore_groups(
            workspace,
            workspace_data.get("groups", {}),
            context,
        )
        self._restore_selection_sets(
            workspace,
            workspace_data.get("selection_sets", {}),
            context,
        )
        self._restore_constraints(
            workspace,
            workspace_data.get("constraints", {}),
            context,
        )
        self._restore_scene3d(
            workspace,
            workspace_data.get("scene3d", {}),
        )

        return workspace

    # --------------------------------

    def _validate_payload(self, payload):

        if payload.get("format") != "KinematicsStudioProject":
            raise ProjectFormatError("Unsupported project format")

        version = int(payload.get("version", 0))

        if version > self.VERSION:
            raise ProjectFormatError(
                f"Project version {version} is newer than supported {self.VERSION}"
            )

    # --------------------------------

    def _layers_to_data(self, workspace):

        manager = workspace.layer_manager

        return {
            "current": getattr(manager.current, "name", "0"),
            "items": [
                {
                    "id": layer.id,
                    "name": layer.name,
                    "visible": layer.visible,
                    "locked": layer.locked,
                    "color": layer.color,
                    "line_type": layer.line_type,
                    "line_weight": layer.line_weight,
                }
                for layer in manager.layers
            ],
        }

    # --------------------------------

    def _patterns_to_data(self, workspace):

        manager = workspace.pattern_manager

        return {
            "current": getattr(manager.current, "name", "SOLID"),
            "items": [
                {
                    "name": pattern.name,
                    "pattern_type": pattern.pattern_type,
                    "scale": pattern.scale,
                    "angle": pattern.angle,
                }
                for pattern in manager.patterns
            ],
        }

    # --------------------------------

    def _dimension_styles_to_data(self, workspace):

        manager = workspace.dimension_style_manager

        return {
            "current": getattr(manager.current, "name", "Standard"),
            "items": [
                {
                    "id": style.id,
                    "name": style.name,
                    "text_height": style.text_height,
                    "arrow_size": style.arrow_size,
                    "extension_offset": style.extension_offset,
                    "extension_overshoot": style.extension_overshoot,
                    "precision": style.precision,
                    "units": style.units,
                    "text_gap": style.text_gap,
                }
                for style in manager.styles
            ],
        }

    # --------------------------------

    def _blocks_to_data(self, workspace, entity_ids):

        manager = workspace.block_manager

        return {
            "current": getattr(manager.current, "id", None),
            "items": [
                {
                    "id": definition.id,
                    "name": definition.name,
                    "origin": self._point_to_data(definition.origin),
                    "entities": [
                        self._entity_to_data(entity, entity_ids)
                        for entity in definition.entities
                    ],
                }
                for definition in manager.definitions
            ],
        }

    # --------------------------------

    def _groups_to_data(self, workspace, entity_ids):

        manager = workspace.group_manager

        return {
            "current": getattr(manager.current, "id", None),
            "selection_enabled": manager.selection_enabled,
            "items": [
                {
                    "id": group.id,
                    "name": group.name,
                    "entity_ids": [
                        entity_ids[entity]
                        for entity in group.entities
                        if entity in entity_ids
                    ],
                }
                for group in manager.groups
            ],
        }

    # --------------------------------

    def _selection_sets_to_data(self, workspace, entity_ids):

        manager = workspace.selection

        return {
            "items": [
                {
                    "name": selection_set.name,
                    "entity_ids": [
                        entity_ids[entity]
                        for entity in selection_set.entities
                        if entity in entity_ids
                    ],
                }
                for selection_set in manager.selection_sets.values()
            ],
        }

    # --------------------------------

    def _constraints_to_data(self, workspace, entity_ids):

        manager = workspace.constraint_manager

        return {
            "items": [
                {
                    "id": constraint.id,
                    "type": constraint.constraint_type,
                    "name": constraint.name,
                    "value": constraint.value,
                    "driven": constraint.driven,
                    "enabled": constraint.enabled,
                    "suppressed": constraint.suppressed,
                    "entity_ids": [
                        entity_ids[entity]
                        for entity in constraint.entities
                        if entity in entity_ids
                    ],
                }
                for constraint in manager.constraints
            ],
        }

    # --------------------------------

    def _scene3d_to_data(self, workspace):

        scene = getattr(workspace, "scene3d", None)

        if scene is None:
            return {"entities": []}

        data = scene.to_dict()
        gizmo = getattr(workspace, "transform_gizmo", None)

        if gizmo is not None:
            data["gizmo"] = gizmo.to_dict()

        snap_manager = getattr(workspace, "snap_manager3d", None)

        if snap_manager is not None:
            data["snap"] = snap_manager.to_dict()

        construction_planes = getattr(workspace, "construction_plane_manager", None)

        if construction_planes is not None:
            data["construction_planes"] = construction_planes.to_dict()

        coordinate_systems = getattr(workspace, "coordinate_system_manager", None)

        if coordinate_systems is not None:
            data["coordinate_systems"] = coordinate_systems.to_dict()

        measurements = getattr(workspace, "measurement_manager", None)

        if measurements is not None:
            data["measurements"] = measurements.to_dict()

        sections = getattr(workspace, "section_manager", None)

        if sections is not None:
            data["sections"] = sections.to_dict()

        view_states = getattr(workspace, "view_state_manager", None)

        if view_states is not None:
            data["view_states"] = view_states.to_dict()

        display_modes = getattr(workspace, "display_mode_manager", None)

        if display_modes is not None:
            data["display_modes"] = display_modes.to_dict()

        visual_styles = getattr(workspace, "visual_style_manager", None)

        if visual_styles is not None:
            data["visual_styles"] = visual_styles.to_dict()

        scene_collections = getattr(workspace, "scene_collection_manager", None)

        if scene_collections is not None:
            data["scene_collections"] = scene_collections.to_dict()

        view_filters = getattr(workspace, "view_filter_manager", None)

        if view_filters is not None:
            data["view_filters"] = view_filters.to_dict()

        display_presets = getattr(workspace, "display_preset_manager", None)

        if display_presets is not None:
            data["display_presets"] = display_presets.to_dict()

        annotations = getattr(workspace, "annotation_manager3d", None)

        if annotations is not None:
            data["annotations3d"] = annotations.to_dict()

        reviews = getattr(workspace, "review_manager", None)

        if reviews is not None:
            data["reviews"] = reviews.to_dict()

        collaboration = getattr(workspace, "collaboration_manager", None)

        if collaboration is not None:
            data["collaboration"] = collaboration.to_dict()

        issues = getattr(workspace, "issue_manager", None)

        if issues is not None:
            data["issues"] = issues.to_dict()

        references = getattr(workspace, "reference_manager", None)

        if references is not None:
            data["references"] = references.to_dict()

        imports = getattr(workspace, "import_manager", None)

        if imports is not None:
            data["imports"] = imports.to_dict()

        coordination = getattr(workspace, "coordination_manager", None)

        if coordination is not None:
            data["coordination"] = coordination.to_dict()

        clashes = getattr(workspace, "clash_manager", None)

        if clashes is not None:
            data["clashes"] = clashes.to_dict()

        bcf = getattr(workspace, "bcf_manager", None)

        if bcf is not None:
            data["bcf"] = bcf.to_dict()

        model_compare = getattr(workspace, "model_compare_manager", None)

        if model_compare is not None:
            data["model_compare"] = model_compare.to_dict()

        packages = getattr(workspace, "coordination_package_manager", None)

        if packages is not None:
            data["coordination_packages"] = packages.to_dict()

        bim = getattr(workspace, "bim_manager", None)

        if bim is not None:
            data["bim"] = bim.to_dict()

        product = getattr(workspace, "product_manager", None)

        if product is not None:
            data["product"] = product.to_dict()

        return data

    # --------------------------------

    def _entity_to_data(self, entity, entity_ids):

        data = {
            "type": entity.__class__.__name__,
            "meta": self._entity_meta_to_data(entity),
        }

        if entity in entity_ids:
            data["id"] = entity_ids[entity]

        data.update(self._entity_fields_to_data(entity, entity_ids))

        return data

    # --------------------------------

    def _entity_meta_to_data(self, entity):

        return {
            "visible": getattr(entity, "visible", True),
            "locked": getattr(entity, "locked", False),
            "layer_name": getattr(entity, "layer_name", None),
            "color": getattr(entity, "color", None),
        }

    # --------------------------------

    def _entity_fields_to_data(self, entity, entity_ids):

        if isinstance(entity, LineEntity):
            return {
                "start": self._point_to_data(entity.start),
                "end": self._point_to_data(entity.end),
            }

        if isinstance(entity, RectangleEntity):
            return {
                "p1": self._point_to_data(entity.p1),
                "p2": self._point_to_data(entity.p2),
            }

        if isinstance(entity, CircleEntity):
            return {
                "center": self._point_to_data(entity.center),
                "radius": entity.radius,
            }

        if isinstance(entity, ArcEntity):
            return {
                "center": self._point_to_data(entity.center),
                "radius": entity.radius,
                "start_angle": entity.start_angle,
                "end_angle": entity.end_angle,
            }

        if isinstance(entity, PolylineEntity):
            return {
                "points": [self._point_to_data(point) for point in entity.points],
                "closed": entity.closed,
            }

        if isinstance(entity, SplineEntity):
            return {
                "control_points": [
                    self._point_to_data(point)
                    for point in entity.control_points
                ],
                "samples_per_segment": entity.samples_per_segment,
            }

        if isinstance(entity, TextEntity):
            return {
                "position": self._point_to_data(entity.position),
                "text": entity.text,
                "height": entity.height,
                "rotation": entity.rotation,
                "alignment": getattr(entity, "alignment", "Left"),
            }

        if isinstance(entity, MTextEntity):
            return {
                "position": self._point_to_data(entity.position),
                "text": entity.text,
                "box_width": entity.box_width,
                "box_height": entity.box_height,
                "height": entity.height,
                "rotation": entity.rotation,
                "alignment": entity.alignment,
            }

        if isinstance(entity, LeaderEntity):
            return {
                "arrow_point": self._point_to_data(entity.arrow_point),
                "landing_start": self._point_to_data(entity.landing_start),
                "landing_end": self._point_to_data(entity.landing_end),
                "text_entity": self._entity_to_data(entity.text_entity, entity_ids),
            }

        if isinstance(entity, HatchEntity):
            return {
                "boundary_points": [
                    self._point_to_data(point)
                    for point in entity.boundary_points
                ],
                "boundary_entity_ids": [
                    entity_ids[boundary]
                    for boundary in entity.boundary_entities
                    if boundary in entity_ids
                ],
                "pattern_name": entity.pattern_name,
                "pattern_scale": entity.pattern_scale,
                "pattern_angle": entity.pattern_angle,
                "associative": entity.associative,
            }

        if isinstance(entity, BlockReference):
            return {
                "definition_id": getattr(entity.definition, "id", entity.definition_id),
                "definition_name": getattr(entity.definition, "name", entity.definition_name),
                "insertion_point": self._point_to_data(entity.insertion_point),
                "rotation": entity.rotation,
                "scale_x": entity.scale_x,
                "scale_y": entity.scale_y,
            }

        if getattr(entity, "is_dimension", False):
            return self._dimension_to_data(entity)

        return {}

    # --------------------------------

    def _dimension_to_data(self, entity):

        data = {
            "text_override": getattr(entity, "text_override", ""),
            "dimension_style_name": getattr(entity, "dimension_style_name", None),
        }

        if isinstance(entity, (LinearDimensionEntity, AlignedDimensionEntity)):
            data.update({
                "point1": self._point_to_data(entity.point1),
                "point2": self._point_to_data(entity.point2),
                "dimension_point": self._point_to_data(entity.dimension_point),
            })
        elif isinstance(entity, (RadiusDimensionEntity, DiameterDimensionEntity)):
            data.update({
                "center": self._point_to_data(entity.center),
                "radius_point": self._point_to_data(entity.radius_point),
                "text_point": self._point_to_data(entity.text_point),
            })
        elif isinstance(entity, AngularDimensionEntity):
            data.update({
                "vertex": self._point_to_data(entity.vertex),
                "point1": self._point_to_data(entity.point1),
                "point2": self._point_to_data(entity.point2),
                "arc_point": self._point_to_data(entity.arc_point),
            })

        return data

    # --------------------------------

    def _restore_layers(self, workspace, data):

        manager = workspace.layer_manager
        items = data.get("items", [])

        for item in items:
            if item.get("name") == "0":
                layer = manager.get("0")
            else:
                layer = manager.create(item.get("name", "Layer"))

            layer.visible = bool(item.get("visible", True))
            layer.locked = bool(item.get("locked", False))
            layer.color = item.get("color", layer.color)
            layer.line_type = item.get("line_type", layer.line_type)
            layer.line_weight = float(item.get("line_weight", layer.line_weight))

        manager.set_current(data.get("current", "0"))

    # --------------------------------

    def _restore_patterns(self, workspace, data):

        manager = workspace.pattern_manager

        for item in data.get("items", []):
            pattern = manager.get(item.get("name"))

            if pattern is None:
                pattern = manager.create(
                    item.get("name", "Pattern"),
                    item.get("pattern_type", "lines"),
                    item.get("scale", 10.0),
                    item.get("angle", 45.0),
                )

            pattern.pattern_type = item.get("pattern_type", pattern.pattern_type)
            pattern.scale = float(item.get("scale", pattern.scale))
            pattern.angle = float(item.get("angle", pattern.angle))

        manager.set_current(data.get("current", "SOLID"))

    # --------------------------------

    def _restore_dimension_styles(self, workspace, data):

        manager = workspace.dimension_style_manager

        for item in data.get("items", []):
            style = manager.get(item.get("name"))

            if style is None:
                style = manager.create(item.get("name", "Dimension Style"))

            style.text_height = float(item.get("text_height", style.text_height))
            style.arrow_size = float(item.get("arrow_size", style.arrow_size))
            style.extension_offset = float(item.get("extension_offset", style.extension_offset))
            style.extension_overshoot = float(item.get("extension_overshoot", style.extension_overshoot))
            style.precision = int(item.get("precision", style.precision))
            style.units = item.get("units", style.units)
            style.text_gap = float(item.get("text_gap", style.text_gap))

        manager.set_current(data.get("current", "Standard"))

    # --------------------------------

    def _restore_blocks(self, workspace, data, context):

        manager = workspace.block_manager

        for item in data.get("items", []):
            definition = manager.create_definition(
                item.get("name", "Block"),
                origin=self._point_from_data(item.get("origin")),
                entities=[],
            )
            context["definition_by_id"][item.get("id")] = definition

        for item in data.get("items", []):
            definition = context["definition_by_id"].get(item.get("id"))

            if definition is None:
                continue

            definition.entities = [
                self._entity_from_data(entity_data, context)
                for entity_data in item.get("entities", [])
            ]

        current = context["definition_by_id"].get(data.get("current"))

        if current is not None:
            manager.set_current(current)

    # --------------------------------

    def _restore_entities(self, workspace, items, context):

        for item in items:
            entity = self._entity_from_data(item, context)
            workspace.add_entity(entity)

            if "id" in item:
                context["entity_by_id"][item["id"]] = entity

        for item in items:
            if item.get("type") == "HatchEntity" and "id" in item:
                entity = context["entity_by_id"].get(item["id"])
                self._restore_hatch_references(entity, item, context)

    # --------------------------------

    def _restore_groups(self, workspace, data, context):

        manager = workspace.group_manager
        manager.selection_enabled = bool(data.get("selection_enabled", True))

        for item in data.get("items", []):
            entities = [
                context["entity_by_id"][entity_id]
                for entity_id in item.get("entity_ids", [])
                if entity_id in context["entity_by_id"]
            ]
            group = manager.create(item.get("name", "Group"), entities)

            if item.get("id") == data.get("current"):
                manager.set_current(group)

    # --------------------------------

    def _restore_selection_sets(self, workspace, data, context):

        for item in data.get("items", []):
            entities = [
                context["entity_by_id"][entity_id]
                for entity_id in item.get("entity_ids", [])
                if entity_id in context["entity_by_id"]
            ]
            workspace.selection.create_set(item.get("name", "Selection Set"), entities)

    # --------------------------------

    def _restore_constraints(self, workspace, data, context):

        for item in data.get("items", []):
            entities = [
                context["entity_by_id"][entity_id]
                for entity_id in item.get("entity_ids", [])
                if entity_id in context["entity_by_id"]
            ]
            constraint = workspace.constraint_manager.create(
                item.get("type", "Coincident"),
                entities,
                item.get("value"),
                item.get("name"),
                item.get("driven", False),
            )
            old_id = constraint.id
            constraint.id = item.get("id", constraint.id)
            constraint.enabled = bool(item.get("enabled", True))
            constraint.suppressed = bool(item.get("suppressed", False))
            workspace.constraint_manager._by_id.pop(old_id, None)
            workspace.constraint_manager.add(constraint)

        workspace.constraint_manager.validate()

    # --------------------------------

    def _restore_scene3d(self, workspace, data):

        gizmo_data = data.get("gizmo")

        if gizmo_data is not None and hasattr(workspace, "transform_gizmo"):
            workspace.transform_gizmo.from_dict(gizmo_data)

        snap_data = data.get("snap")

        if snap_data is not None and hasattr(workspace, "snap_manager3d"):
            workspace.snap_manager3d.from_dict(snap_data)

        plane_data = data.get("construction_planes")

        if plane_data is not None and hasattr(workspace, "construction_plane_manager"):
            workspace.construction_plane_manager.from_dict(plane_data)

        coordinate_data = data.get("coordinate_systems")

        if coordinate_data is not None and hasattr(workspace, "coordinate_system_manager"):
            workspace.coordinate_system_manager.from_dict(coordinate_data)

        measurement_data = data.get("measurements")

        if measurement_data is not None and hasattr(workspace, "measurement_manager"):
            workspace.measurement_manager.from_dict(measurement_data)
            for measurement in workspace.measurement_manager.measurements:
                layer = workspace.layer_manager.get(getattr(measurement, "layer_name", None))
                if layer is not None:
                    workspace.assign_layer(measurement, layer)
                if getattr(measurement, "selected", False):
                    workspace.selection.select(measurement, True)

        section_data = data.get("sections")

        if section_data is not None and hasattr(workspace, "section_manager"):
            workspace.section_manager.from_dict(section_data)
            for section in workspace.section_manager.sections:
                layer = workspace.layer_manager.get(getattr(section, "layer_name", None))
                if layer is not None:
                    workspace.assign_layer(section, layer)
                else:
                    workspace.assign_layer(section)
                if getattr(section, "selected", False):
                    workspace.selection.select(section, True)

        view_state_data = data.get("view_states")

        if view_state_data is not None and hasattr(workspace, "view_state_manager"):
            workspace.view_state_manager.from_dict(view_state_data)

        display_mode_data = data.get("display_modes")

        if display_mode_data is not None and hasattr(workspace, "display_mode_manager"):
            workspace.display_mode_manager.from_dict(display_mode_data)

        visual_style_data = data.get("visual_styles")

        if visual_style_data is not None and hasattr(workspace, "visual_style_manager"):
            workspace.visual_style_manager.from_dict(visual_style_data)

        collection_data = data.get("scene_collections")

        if collection_data is not None and hasattr(workspace, "scene_collection_manager"):
            workspace.scene_collection_manager.from_dict(collection_data)

        filter_data = data.get("view_filters")

        if filter_data is not None and hasattr(workspace, "view_filter_manager"):
            workspace.view_filter_manager.from_dict(filter_data)

        preset_data = data.get("display_presets")

        if preset_data is not None and hasattr(workspace, "display_preset_manager"):
            workspace.display_preset_manager.from_dict(preset_data)

        annotation_data = data.get("annotations3d")

        if annotation_data is not None and hasattr(workspace, "annotation_manager3d"):
            workspace.annotation_manager3d.from_dict(annotation_data)
            for annotation in workspace.annotation_manager3d.annotations:
                layer = workspace.layer_manager.get(getattr(annotation, "layer_name", None))
                if layer is not None:
                    workspace.assign_layer(annotation, layer)
                else:
                    workspace.assign_layer(annotation)
                if getattr(annotation, "selected", False):
                    workspace.selection.select(annotation, True)

        review_data = data.get("reviews")

        if review_data is not None and hasattr(workspace, "review_manager"):
            workspace.review_manager.from_dict(review_data)

        collaboration_data = data.get("collaboration")

        if collaboration_data is not None and hasattr(workspace, "collaboration_manager"):
            workspace.collaboration_manager.from_dict(collaboration_data)

        issue_data = data.get("issues")

        if issue_data is not None and hasattr(workspace, "issue_manager"):
            workspace.issue_manager.from_dict(issue_data)
            for issue in workspace.issue_manager.issues:
                layer = workspace.layer_manager.get(getattr(issue, "layer_name", None))
                if layer is not None:
                    workspace.assign_layer(issue, layer)
                else:
                    workspace.assign_layer(issue)
                if getattr(issue, "selected", False):
                    workspace.selection.select(issue, True)

        reference_data = data.get("references")

        if reference_data is not None and hasattr(workspace, "reference_manager"):
            workspace.reference_manager.from_dict(reference_data)
            for reference in workspace.reference_manager.instances:
                layer = workspace.layer_manager.get(getattr(reference, "layer_name", None))
                if layer is not None:
                    workspace.assign_layer(reference, layer)
                else:
                    workspace.assign_layer(reference)
                if getattr(reference, "selected", False):
                    workspace.selection.select(reference, True)

        import_data = data.get("imports")

        if import_data is not None and hasattr(workspace, "import_manager"):
            workspace.import_manager.from_dict(import_data)

        coordination_data = data.get("coordination")

        if coordination_data is not None and hasattr(workspace, "coordination_manager"):
            workspace.coordination_manager.from_dict(coordination_data)

        clash_data = data.get("clashes")

        if clash_data is not None and hasattr(workspace, "clash_manager"):
            workspace.clash_manager.from_dict(clash_data)
            for clash in workspace.clash_manager.results:
                layer = workspace.layer_manager.get(getattr(clash, "layer_name", None))
                if layer is not None:
                    workspace.assign_layer(clash, layer)
                else:
                    workspace.assign_layer(clash)
                if getattr(clash, "selected", False):
                    workspace.selection.select(clash, True)

        bcf_data = data.get("bcf")

        if bcf_data is not None and hasattr(workspace, "bcf_manager"):
            workspace.bcf_manager.from_dict(bcf_data)
            for topic in workspace.bcf_manager.topics():
                if getattr(topic, "selected", False):
                    workspace.selection.select(topic, True)

        compare_data = data.get("model_compare")

        if compare_data is not None and hasattr(workspace, "model_compare_manager"):
            workspace.model_compare_manager.from_dict(compare_data)
            workspace.revision_manager = workspace.model_compare_manager.revision_manager
            workspace.timeline_manager = workspace.model_compare_manager.timeline_manager
            for result in workspace.model_compare_manager.results():
                if getattr(result, "selected", False):
                    workspace.selection.select(result, True)
            for revision in workspace.revision_manager.visible_revisions():
                if getattr(revision, "selected", False):
                    workspace.selection.select(revision, True)

        package_data = data.get("coordination_packages")

        if package_data is not None and hasattr(workspace, "coordination_package_manager"):
            workspace.coordination_package_manager.from_dict(package_data)
            workspace.archive_manager = workspace.coordination_package_manager.archive_manager
            for package in workspace.coordination_package_manager.visible_packages():
                if getattr(package, "selected", False):
                    workspace.selection.select(package, True)

        bim_data = data.get("bim")

        if bim_data is not None and hasattr(workspace, "bim_manager"):
            workspace.bim_manager.from_dict(bim_data)
            for item in workspace.bim_manager.visible_objects():
                layer = workspace.layer_manager.get(getattr(item, "layer_name", None))
                if layer is not None:
                    workspace.assign_layer(item, layer)
                else:
                    workspace.assign_layer(item)
                if getattr(item, "selected", False):
                    workspace.selection.select(item, True)

        for item in data.get("entities", []):
            entity = entity3d_from_dict(item)
            layer = workspace.layer_manager.get(getattr(entity, "layer_name", None))

            if layer is not None:
                workspace.assign_layer(entity, layer)
            else:
                workspace.assign_layer(entity)

            workspace.scene3d.add_entity(entity)

            if getattr(entity, "selected", False):
                workspace.selection.select(entity, True)

        if hasattr(workspace, "bim_manager"):
            workspace.bim_manager.relink_scene_entities(workspace.scene3d.entities())

        product_data = data.get("product")

        if product_data is not None and hasattr(workspace, "product_manager"):
            workspace.product_manager.from_dict(product_data)
            for item in workspace.product_manager.visible_objects():
                layer = workspace.layer_manager.get(getattr(item, "layer_name", None))
                if layer is not None:
                    workspace.assign_layer(item, layer)
                else:
                    workspace.assign_layer(item)
                if getattr(item, "selected", False):
                    workspace.selection.select(item, True)
            workspace.product_manager.relink_scene_entities(workspace.scene3d.entities())

    # --------------------------------

    def _entity_from_data(self, data, context):

        entity_type = data.get("type")

        if entity_type == "LineEntity":
            entity = LineEntity(
                self._point_from_data(data.get("start")),
                self._point_from_data(data.get("end")),
            )
        elif entity_type == "RectangleEntity":
            entity = RectangleEntity(
                self._point_from_data(data.get("p1")),
                self._point_from_data(data.get("p2")),
            )
        elif entity_type == "CircleEntity":
            entity = CircleEntity(
                self._point_from_data(data.get("center")),
                data.get("radius", 0.0),
            )
        elif entity_type == "ArcEntity":
            entity = ArcEntity(
                self._point_from_data(data.get("center")),
                data.get("radius", 0.0),
                data.get("start_angle", 0.0),
                data.get("end_angle", 90.0),
            )
        elif entity_type == "PolylineEntity":
            entity = PolylineEntity([
                self._point_from_data(point)
                for point in data.get("points", [])
            ], data.get("closed", False))
        elif entity_type == "SplineEntity":
            entity = SplineEntity(
                [
                    self._point_from_data(point)
                    for point in data.get("control_points", [])
                ],
                data.get("samples_per_segment", 16),
            )
        elif entity_type == "TextEntity":
            entity = TextEntity(
                self._point_from_data(data.get("position")),
                data.get("text", ""),
                data.get("height", 20.0),
                data.get("rotation", 0.0),
            )
            entity.alignment = data.get("alignment", "Left")
        elif entity_type == "MTextEntity":
            entity = MTextEntity(
                self._point_from_data(data.get("position")),
                data.get("text", ""),
                data.get("box_width", 180.0),
                data.get("box_height", 80.0),
                data.get("height", 20.0),
                data.get("rotation", 0.0),
                data.get("alignment", "Left"),
            )
        elif entity_type == "LeaderEntity":
            entity = LeaderEntity(
                self._point_from_data(data.get("arrow_point")),
                self._point_from_data(data.get("landing_start")),
                self._point_from_data(data.get("landing_end")),
                self._entity_from_data(data.get("text_entity", {"type": "TextEntity"}), context),
            )
        elif entity_type == "HatchEntity":
            entity = HatchEntity(
                [self._point_from_data(point) for point in data.get("boundary_points", [])],
                [],
                data.get("pattern_name", "SOLID"),
                data.get("pattern_scale", 10.0),
                data.get("pattern_angle", 45.0),
            )
            entity.associative = bool(data.get("associative", False))
            entity.pattern = context["workspace"].pattern_manager.get(entity.pattern_name)
        elif entity_type == "BlockReference":
            definition = (
                context["definition_by_id"].get(data.get("definition_id")) or
                context["workspace"].block_manager.get(data.get("definition_name"))
            )
            entity = BlockReference(
                definition,
                self._point_from_data(data.get("insertion_point")),
                data.get("rotation", 0.0),
                data.get("scale_x", 1.0),
                data.get("scale_y", 1.0),
            )
        else:
            entity = self._dimension_from_data(entity_type, data, context)

        self._restore_entity_meta(entity, data.get("meta", {}), context["workspace"])
        self._restore_dimension_style(entity, data, context["workspace"])

        return entity

    # --------------------------------

    def _dimension_from_data(self, entity_type, data, context):

        if entity_type == "LinearDimensionEntity":
            entity = LinearDimensionEntity(
                self._point_from_data(data.get("point1")),
                self._point_from_data(data.get("point2")),
                self._point_from_data(data.get("dimension_point")),
            )
        elif entity_type == "AlignedDimensionEntity":
            entity = AlignedDimensionEntity(
                self._point_from_data(data.get("point1")),
                self._point_from_data(data.get("point2")),
                self._point_from_data(data.get("dimension_point")),
            )
        elif entity_type == "RadiusDimensionEntity":
            entity = RadiusDimensionEntity(
                self._point_from_data(data.get("center")),
                self._point_from_data(data.get("radius_point")),
                self._point_from_data(data.get("text_point")),
            )
        elif entity_type == "DiameterDimensionEntity":
            entity = DiameterDimensionEntity(
                self._point_from_data(data.get("center")),
                self._point_from_data(data.get("radius_point")),
                self._point_from_data(data.get("text_point")),
            )
        elif entity_type == "AngularDimensionEntity":
            entity = AngularDimensionEntity(
                self._point_from_data(data.get("vertex")),
                self._point_from_data(data.get("point1")),
                self._point_from_data(data.get("point2")),
                self._point_from_data(data.get("arc_point")),
            )
        else:
            raise ProjectFormatError(f"Unsupported entity type: {entity_type}")

        entity.text_override = data.get("text_override", "")

        return entity

    # --------------------------------

    def _restore_entity_meta(self, entity, meta, workspace):

        entity.visible = bool(meta.get("visible", True))
        entity.locked = bool(meta.get("locked", False))
        entity.color = meta.get("color")

        layer = workspace.layer_manager.get(meta.get("layer_name"))

        if layer is not None:
            workspace.assign_layer(entity, layer)

    # --------------------------------

    def _restore_dimension_style(self, entity, data, workspace):

        if not getattr(entity, "is_dimension", False):
            return

        style = workspace.dimension_style_manager.get(data.get("dimension_style_name"))

        if style is not None:
            entity.dimension_style = style
            entity.dimension_style_id = style.id
            entity.dimension_style_name = style.name

    # --------------------------------

    def _restore_hatch_references(self, entity, data, context):

        if entity is None:
            return

        entity.boundary_entities = [
            context["entity_by_id"][entity_id]
            for entity_id in data.get("boundary_entity_ids", [])
            if entity_id in context["entity_by_id"]
        ]
        entity.boundary_entity_ids = data.get("boundary_entity_ids", [])
        entity.associative = bool(entity.boundary_entities)

    # --------------------------------

    def _point_to_data(self, point):

        return {"x": point.x, "y": point.y}

    # --------------------------------

    def _point_from_data(self, data):

        data = data or {}

        return Vector2(data.get("x", 0.0), data.get("y", 0.0))


class Project:
    """Backward-compatible storage project container."""

    def __init__(self):

        self.entities = []

    def add_entity(self, entity):

        self.entities.append(entity)

    def clear(self):

        self.entities.clear()
