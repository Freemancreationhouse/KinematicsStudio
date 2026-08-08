from dataclasses import dataclass

from engine.entities import (
    AlignedDimensionEntity,
    AngularDimensionEntity,
    ArcEntity,
    BlockReference,
    CircleEntity,
    DiameterDimensionEntity,
    EllipseEntity,
    HatchEntity,
    LeaderEntity,
    LineEntity,
    LinearDimensionEntity,
    MTextEntity,
    PolylineEntity,
    PolygonEntity,
    RadiusDimensionEntity,
    RectangleEntity,
    SplineEntity,
    TextEntity,
)
from engine.geometry import Vector2
from engine.geometry.curves import hit_curve
from engine.geometry.primitives import point_to_segment_distance
from engine.selection import (
    SelectionContext,
    SelectionMode,
    SelectionPolicy,
    SelectionTarget,
)


@dataclass
class SelectionSet:
    """Named collection of entity references stored by the SelectionManager."""

    name: str
    entities: list

    @property
    def count(self):
        """Return the number of stored entity references."""

        return len(self.entities)


class SelectionFilter:
    """Reusable selection filter shared by tools, panels and tests."""

    TYPE_MAP = {
        "Lines": (LineEntity,),
        "Polylines": (PolylineEntity,),
        "Splines": (SplineEntity,),
        "Rectangles": (RectangleEntity,),
        "Circles": (CircleEntity,),
        "Arcs": (ArcEntity,),
        "Ellipses": (EllipseEntity,),
        "Polygons": (PolygonEntity,),
        "Blocks": (BlockReference,),
        "Text": (TextEntity,),
        "MText": (MTextEntity,),
        "Leaders": (LeaderEntity,),
        "Dimensions": (
            LinearDimensionEntity,
            AlignedDimensionEntity,
            RadiusDimensionEntity,
            DiameterDimensionEntity,
            AngularDimensionEntity,
        ),
        "Hatches": (HatchEntity,),
    }

    def __init__(self):

        self.type_filter = "All"
        self.layer_names = set()
        self.lock_state = "Any"
        self.visibility = "Any"

    # --------------------------------

    def reset(self):
        """Reset filters to the all-selectable state."""

        self.type_filter = "All"
        self.layer_names.clear()
        self.lock_state = "Any"
        self.visibility = "Any"

    # --------------------------------

    def matches(self, entity, workspace=None):
        """Return True when an entity passes the active filters."""

        return (
            self._matches_type(entity, workspace) and
            self._matches_layer(entity, workspace) and
            self._matches_lock(entity, workspace) and
            self._matches_visibility(entity, workspace)
        )

    # --------------------------------

    def _matches_type(self, entity, workspace):

        if self.type_filter == "All":
            return True

        if self.type_filter == "Groups":
            manager = getattr(workspace, "group_manager", None)
            return bool(manager and manager.groups_for_entity(entity))

        expected = self.TYPE_MAP.get(self.type_filter)

        return isinstance(entity, expected) if expected else True

    # --------------------------------

    def _matches_layer(self, entity, workspace):

        if not self.layer_names:
            return True

        layer = workspace.entity_layer(entity) if workspace else getattr(entity, "layer", None)
        name = getattr(layer, "name", None) or getattr(entity, "layer_name", None)

        return name in self.layer_names

    # --------------------------------

    def _matches_lock(self, entity, workspace):

        if self.lock_state == "Any":
            return True

        locked = bool(getattr(entity, "locked", False))

        if workspace is not None:
            locked = locked or workspace.entity_layer_locked(entity)

        return locked if self.lock_state == "Locked" else not locked

    # --------------------------------

    def _matches_visibility(self, entity, workspace):

        if self.visibility == "Any":
            return True

        visible = bool(getattr(entity, "visible", True))

        if workspace is not None:
            visible = visible and workspace.entity_layer_visible(entity)

        return visible if self.visibility == "Visible" else not visible


class SelectionManager:
    """Owns selected entities, filters, previous selection and named sets."""

    def __init__(self):

        self.selected = []
        self.previous = []
        self.filter = SelectionFilter()
        self.policy = SelectionPolicy()
        self.selection_context = SelectionContext()
        self.selection_sets = {}
        self.persistent_targets = {}
        self.hovered = None
        self.preselected = None
        self._cycle_point = None
        self._cycle_candidates = []
        self._cycle_index = -1
        self.occ_manager = None
        self.occ_selection = None
        self.on_change = None

    # --------------------------------

    def bind_occ_selection(self, occ_manager, occ_selection):
        """Bind existing OpenCascade selection without creating another selection manager."""

        self.occ_manager = occ_manager
        self.occ_selection = occ_selection
        self._sync_occ_selection()

    # --------------------------------

    def clear(self):
        """Clear the current selection while preserving previous selection."""

        had_selection = bool(self.selected)
        self._remember_previous()
        for entity in self.selected:

            self._set_selected_flag(entity, False)

        self.selected.clear()
        self._sync_occ_selection()
        if had_selection:
            self._changed()
        else:
            self._update_context()

    # --------------------------------

    def select(self, entity, additive=False):
        """Select one entity."""

        if entity is None:
            return

        if not additive:

            self.clear()

        if entity not in self.selected:

            self._set_selected_flag(entity, True)

            self.selected.append(entity)
            self._remember_persistent_target(entity)
            self._sync_occ_selection()
            self._changed()

    # --------------------------------

    def select_many(self, entities, additive=False):
        """Select multiple entities using existing selection state."""

        if not additive:
            self.clear()

        for entity in entities:
            self.select(entity, True)

    # --------------------------------

    def deselect(self, entity):
        """Deselect one entity."""

        if entity in self.selected:

            self._set_selected_flag(entity, False)

            self.selected.remove(entity)
            self._sync_occ_selection()
            self._changed()

    # --------------------------------

    def unregister_entity(self, entity):
        """Remove a deleted entity from all selection-owned references."""

        self.deselect(entity)

        self.previous = [
            item for item in self.previous
            if item is not entity
        ]

        persistent_id = self._persistent_id_for(entity)
        if persistent_id:
            self.persistent_targets.pop(persistent_id, None)

        for selection_set in self.selection_sets.values():
            selection_set.entities = [
                item for item in selection_set.entities
                if item is not entity
            ]

        self._cycle_candidates = [
            item for item in self._cycle_candidates
            if item is not entity
        ]
        self._sync_occ_selection()

    # --------------------------------

    def _set_selected_flag(self, entity, value):
        """Set an object's selected flag when the object supports one."""

        try:
            entity.selected = bool(value)
        except Exception:
            pass

    # --------------------------------

    def _sync_occ_selection(self):
        """Mirror selected OCC shapes into the existing OCCSelection helper."""

        if self.occ_manager is None or self.occ_selection is None:
            return

        shapes = getattr(self.occ_manager, "shapes", [])

        if callable(shapes):
            shapes = shapes()

        self.occ_selection.clear()

        for entity in self.selected:
            if entity in shapes:
                self.occ_selection.select(entity, True)

    # --------------------------------

    def _changed(self):
        """Notify observers that the selection state changed."""

        self._update_context()

        if callable(self.on_change):
            self.on_change(self)

    # --------------------------------

    def toggle(self, entity):
        """Toggle one entity in the current selection."""

        if entity in self.selected:

            self.deselect(entity)

        else:

            self.select(entity, True)

    # --------------------------------

    def filtered_entities(self, workspace, include_unselectable=False):
        """Return workspace entities that pass active selection filters."""

        if include_unselectable:
            candidates = list(workspace.entities)
        else:
            candidates = (
                workspace.selectable_entities()
                if hasattr(workspace, "selectable_entities")
                else list(workspace.entities)
            )

        return [
            entity for entity in candidates
            if self.filter.matches(entity, workspace)
            and self.policy.accepts(entity, workspace)
        ]

    # --------------------------------

    def set_mode(self, mode):
        """Set the active professional selection mode."""

        normalized = self.policy.set_mode(mode)
        self._changed()
        return normalized

    # --------------------------------

    def selection_mode(self):
        """Return the active professional selection mode."""

        return self.policy.mode

    # --------------------------------

    def enable_filter(self, filter_type):
        """Enable a professional selection filter."""

        self.policy.enable_filter(filter_type)
        self._changed()

    # --------------------------------

    def disable_filter(self, filter_type):
        """Disable a professional selection filter."""

        self.policy.disable_filter(filter_type)
        self._changed()

    # --------------------------------

    def clear_filters(self):
        """Clear professional and legacy selection filters."""

        self.policy.clear_filters()
        self.filter.reset()
        self._changed()

    # --------------------------------

    def enabled_filters(self):
        """Return enabled professional selection filters."""

        return tuple(self.policy.enabled_filters)

    # --------------------------------

    def set_priority(self, priority):
        """Set configurable selection priority."""

        self.policy.set_priority(priority)
        self._changed()

    # --------------------------------

    def selection_priority(self):
        """Return current selection priority."""

        return tuple(self.policy.priority)

    # --------------------------------

    def context(self):
        """Return the current selection context."""

        return self.selection_context

    # --------------------------------

    def targets(self):
        """Return persistent selection target records."""

        return tuple(
            self.persistent_targets.get(self._persistent_id_for(entity))
            or SelectionTarget.from_entity(entity, self.policy.mode)
            for entity in self.selected
        )

    # --------------------------------

    def persistent_selection_ids(self):
        """Return persistent identifiers for the active selection."""

        return tuple(
            persistent_id for persistent_id in (
                self._persistent_id_for(entity)
                for entity in self.selected
            )
            if persistent_id
        )

    # --------------------------------

    def restore_persistent_selection(self, workspace, additive=False):
        """Restore current persistent selection IDs against workspace entities."""

        ids = set(self.persistent_selection_ids())
        if not ids:
            return []
        matched = [
            entity for entity in self._workspace_entities(workspace)
            if self._persistent_id_for(entity) in ids
        ]
        self.select_many(matched, additive)
        return matched

    # --------------------------------

    def set_hovered(self, entity):
        """Set hover highlight state without modifying selection."""

        if self.hovered is entity:
            return
        self._set_highlight_flag(self.hovered, "hovered", False)
        self.hovered = entity
        self._set_highlight_flag(self.hovered, "hovered", True)
        self._changed()

    # --------------------------------

    def set_preselected(self, entity):
        """Set preselection highlight state without modifying selection."""

        if self.preselected is entity:
            return
        self._set_highlight_flag(self.preselected, "preselected", False)
        self.preselected = entity
        self._set_highlight_flag(self.preselected, "preselected", True)
        self._changed()

    # --------------------------------

    def clear_highlights(self):
        """Clear hover and preselection highlight state."""

        self._set_highlight_flag(self.hovered, "hovered", False)
        self._set_highlight_flag(self.preselected, "preselected", False)
        self.hovered = None
        self.preselected = None
        self._changed()

    # --------------------------------

    def select_window(self, workspace, start, end, crossing=False, additive=False):
        """Select entities inside or crossing a rectangular window."""

        left = min(start.x, end.x)
        right = max(start.x, end.x)
        top = min(start.y, end.y)
        bottom = max(start.y, end.y)
        matched = []

        for entity in self.filtered_entities(workspace):
            box = entity.bounding_box

            if crossing:
                ok = (
                    box.max.x >= left and
                    box.min.x <= right and
                    box.max.y >= top and
                    box.min.y <= bottom
                )
            else:
                ok = (
                    box.min.x >= left and
                    box.max.x <= right and
                    box.min.y >= top and
                    box.max.y <= bottom
                )

            if ok:
                matched.extend(self._expanded(workspace, entity))

        self.select_many(matched, additive)
        return matched

    # --------------------------------

    def select_fence(self, workspace, points, additive=False, tolerance=5.0):
        """Select entities touched by a fence polyline."""

        matched = []

        for entity in self.filtered_entities(workspace):
            if self._entity_touches_fence(entity, points, tolerance):
                matched.extend(self._expanded(workspace, entity))

        self.select_many(matched, additive)
        return matched

    # --------------------------------

    def select_lasso(self, workspace, points, crossing=True, additive=False):
        """Select entities inside or crossing a lasso polygon."""

        points = list(points)
        matched = []

        for entity in self.filtered_entities(workspace):
            box = entity.bounding_box
            corners = [
                box.min,
                Vector2(box.max.x, box.min.y),
                box.max,
                Vector2(box.min.x, box.max.y),
            ]
            center = box.center
            inside = all(_point_in_polygon(corner, points) for corner in corners)
            touches = crossing and (
                any(_point_in_polygon(corner, points) for corner in corners) or
                _point_in_polygon(center, points) or
                self._entity_touches_fence(entity, points + points[:1], 5.0)
            )

            if inside or touches:
                matched.extend(self._expanded(workspace, entity))

        self.select_many(matched, additive)
        return matched

    # --------------------------------

    def cycle_at_point(self, workspace, point, additive=False):
        """Cycle through overlapping entities at a pick point."""

        candidates = [
            entity for entity in reversed(self.filtered_entities(workspace))
            if entity.hit_test(point)
        ]

        same_point = (
            self._cycle_point is not None and
            self._cycle_point.distance_to(point) <= 1.0
        )

        if candidates != self._cycle_candidates or not same_point:
            self._cycle_candidates = candidates
            self._cycle_index = -1
            self._cycle_point = point.copy()

        if not candidates:
            if not additive:
                self.clear()
            return None

        self._cycle_index = (self._cycle_index + 1) % len(candidates)
        entity = candidates[self._cycle_index]
        self.select_many(self._expanded(workspace, entity), additive)

        return entity

    # --------------------------------

    def recall_previous(self, workspace=None):
        """Restore the previous selection."""

        candidates = self.previous

        if workspace is not None:
            candidates = [
                entity for entity in candidates
                if entity in workspace.entities
            ]

        self.select_many(candidates, False)
        return list(self.selected)

    # --------------------------------

    def invert(self, workspace):
        """Invert the current selection over filtered selectable entities."""

        current = set(self.selected)
        targets = [
            entity for entity in self.filtered_entities(workspace)
            if entity not in current
        ]
        self.select_many(targets, False)

        return list(self.selected)

    # --------------------------------

    def select_similar(self, workspace, source=None, additive=False):
        """Select entities similar by type and layer."""

        seed = source or self.first

        if seed is None:
            return []

        layer_name = getattr(seed, "layer_name", None)
        entity_type = seed.__class__
        matched = [
            entity for entity in self.filtered_entities(workspace)
            if isinstance(entity, entity_type) and
            getattr(entity, "layer_name", None) == layer_name
        ]
        self.select_many(matched, additive)

        return matched

    # --------------------------------

    def select_loop(self, workspace, source=None, additive=False):
        """Select a loop-related set using available topology metadata."""

        seed = source or self.first
        matched = self._related_by_metadata(workspace, seed, ("loop_id", "loop_ids"))
        self.select_many(matched or ([seed] if seed is not None else []), additive)
        return list(self.selected)

    # --------------------------------

    def select_ring(self, workspace, source=None, additive=False):
        """Select a ring-related set using available topology metadata."""

        seed = source or self.first
        matched = self._related_by_metadata(workspace, seed, ("ring_id", "ring_ids"))
        self.select_many(matched or ([seed] if seed is not None else []), additive)
        return list(self.selected)

    # --------------------------------

    def select_connected_faces(self, workspace, source=None, additive=False):
        """Select faces connected by shared body or shell metadata."""

        return self._select_connected(
            workspace,
            source,
            additive,
            ("body_id", "shell_id", "face_ids"),
            SelectionMode.FACE,
        )

    # --------------------------------

    def select_connected_edges(self, workspace, source=None, additive=False):
        """Select edges connected by shared loop or vertex metadata."""

        return self._select_connected(
            workspace,
            source,
            additive,
            ("loop_id", "vertex_ids", "edge_ids"),
            SelectionMode.EDGE,
        )

    # --------------------------------

    def select_connected_bodies(self, workspace, source=None, additive=False):
        """Select bodies connected by component or assembly metadata."""

        return self._select_connected(
            workspace,
            source,
            additive,
            ("component_id", "assembly_id", "body_ids"),
            SelectionMode.BODY,
        )

    # --------------------------------

    def grow_selection(self, workspace):
        """Grow selection to directly related metadata neighbors."""

        seeds = list(self.selected)
        grown = list(seeds)
        for seed in seeds:
            for entity in self._workspace_entities(workspace):
                if entity in grown:
                    continue
                if self._shares_metadata(seed, entity):
                    grown.append(entity)
        self.select_many(grown, False)
        return list(self.selected)

    # --------------------------------

    def shrink_selection(self):
        """Shrink selection by removing the most recently selected item."""

        if self.selected:
            self.deselect(self.selected[-1])
        return list(self.selected)

    # --------------------------------

    def select_by_layer(self, workspace, layer_name, additive=False):
        """Select all selectable entities on one layer."""

        matched = [
            entity for entity in self.filtered_entities(workspace)
            if self._layer_name_for(entity, workspace) == layer_name
        ]
        self.select_many(matched, additive)
        return matched

    # --------------------------------

    def select_by_material(self, workspace, material_id, additive=False):
        """Select all selectable entities with one material identifier."""

        material = str(material_id or "")
        matched = [
            entity for entity in self.filtered_entities(workspace)
            if str(
                getattr(
                    entity,
                    "material_id",
                    getattr(entity, "material", ""),
                )
            ) == material
        ]
        self.select_many(matched, additive)
        return matched

    # --------------------------------

    def select_by_ai_request(self, workspace, request, additive=False):
        """Resolve an AI selection request through SelectionManager."""

        text = str(request or "").strip().lower()
        if "vertex" in text:
            self.set_mode(SelectionMode.VERTEX)
        elif "edge" in text:
            self.set_mode(SelectionMode.EDGE)
        elif "face" in text:
            self.set_mode(SelectionMode.FACE)
        elif "body" in text:
            self.set_mode(SelectionMode.BODY)
        elif "feature" in text:
            self.set_mode(SelectionMode.OBJECT)
        return self.filtered_entities(workspace)

    # --------------------------------

    def create_set(self, name, entities=None):
        """Create or replace a named selection set."""

        clean = self._clean_name(name)
        selection = list(entities if entities is not None else self.selected)
        selection_set = SelectionSet(clean, selection)
        self.selection_sets[clean] = selection_set

        return selection_set

    # --------------------------------

    def rename_set(self, old_name, new_name):
        """Rename a selection set."""

        old = self._clean_name(old_name)
        new = self._clean_name(new_name)

        if old not in self.selection_sets or not new:
            return False

        selection_set = self.selection_sets.pop(old)
        selection_set.name = new
        self.selection_sets[new] = selection_set

        return True

    # --------------------------------

    def delete_set(self, name):
        """Delete a named selection set."""

        return self.selection_sets.pop(self._clean_name(name), None) is not None

    # --------------------------------

    def recall_set(self, name, workspace=None):
        """Recall a named selection set into the active selection."""

        selection_set = self.selection_sets.get(self._clean_name(name))

        if selection_set is None:
            return []

        entities = list(selection_set.entities)

        if workspace is not None:
            entities = [
                entity for entity in entities
                if entity in workspace.entities
            ]

        self.select_many(entities, False)
        return list(self.selected)

    # --------------------------------

    def update_set(self, name, entities=None):
        """Update an existing selection set with current or provided entities."""

        selection_set = self.selection_sets.get(self._clean_name(name))

        if selection_set is None:
            return None

        selection_set.entities = list(entities if entities is not None else self.selected)

        return selection_set

    # --------------------------------

    def set_names(self):
        """Return selection set names."""

        return list(self.selection_sets.keys())

    # --------------------------------

    def _expanded(self, workspace, entity):

        return (
            workspace.selection_entities_for(entity)
            if hasattr(workspace, "selection_entities_for")
            else [entity]
        )

    # --------------------------------

    def _remember_previous(self):

        if self.selected:
            self.previous = list(self.selected)

    # --------------------------------

    def _update_context(self):

        self.selection_context.update(
            mode=self.policy.mode,
            targets=self.targets(),
        )

    # --------------------------------

    def _remember_persistent_target(self, entity):

        target = SelectionTarget.from_entity(entity, self.policy.mode)
        if target.persistent_id:
            self.persistent_targets[target.persistent_id] = target

    # --------------------------------

    def _persistent_id_for(self, entity):

        if entity is None:
            return ""

        for name in (
            "persistent_topology_id",
            "topology_id",
            "persistent_id",
            "id",
            "name",
        ):
            value = getattr(entity, name, "")
            if callable(value):
                try:
                    value = value()
                except TypeError:
                    continue
            if value:
                return str(value)
        return ""

    # --------------------------------

    def _set_highlight_flag(self, entity, name, value):

        if entity is None:
            return

        try:
            setattr(entity, name, bool(value))
        except Exception:
            pass

    # --------------------------------

    def _workspace_entities(self, workspace):

        if workspace is None:
            return []

        entities = getattr(workspace, "entities", None)
        if callable(entities):
            return list(entities())
        return list(entities or [])

    # --------------------------------

    def _related_by_metadata(self, workspace, seed, names):

        if seed is None:
            return []

        seed_values = self._metadata_values(seed, names)
        if not seed_values:
            return []

        return [
            entity for entity in self.filtered_entities(workspace)
            if self._metadata_values(entity, names).intersection(seed_values)
        ]

    # --------------------------------

    def _select_connected(self, workspace, source, additive, names, mode):

        seed = source or self.first
        previous_mode = self.policy.mode
        try:
            self.policy.set_mode(mode)
            matched = self._related_by_metadata(workspace, seed, names)
            self.select_many(matched or ([seed] if seed is not None else []), additive)
            return list(self.selected)
        finally:
            self.policy.set_mode(previous_mode)
            self._update_context()

    # --------------------------------

    def _shares_metadata(self, first, second):

        names = (
            "body_id",
            "shell_id",
            "face_id",
            "loop_id",
            "edge_id",
            "vertex_id",
            "component_id",
            "assembly_id",
            "layer_name",
            "material_id",
        )
        return bool(self._metadata_values(first, names).intersection(
            self._metadata_values(second, names)
        ))

    # --------------------------------

    def _metadata_values(self, entity, names):

        values = set()
        if entity is None:
            return values

        metadata = getattr(entity, "metadata", None)
        for name in names:
            candidates = [getattr(entity, name, None)]
            if isinstance(metadata, dict):
                candidates.append(metadata.get(name))
            for candidate in candidates:
                if candidate is None:
                    continue
                if isinstance(candidate, (list, tuple, set)):
                    values.update(str(item) for item in candidate if item)
                elif candidate:
                    values.add(str(candidate))
        return values

    # --------------------------------

    def _layer_name_for(self, entity, workspace):

        layer = None
        if workspace is not None and hasattr(workspace, "entity_layer"):
            layer = workspace.entity_layer(entity)
        return (
            getattr(layer, "name", None)
            or getattr(entity, "layer_name", None)
            or getattr(entity, "layer", "")
        )

    # --------------------------------

    def _entity_touches_fence(self, entity, points, tolerance):

        if len(points) < 2:
            return False

        for start, end in zip(points, points[1:]):
            if entity.hit_test(start) or entity.hit_test(end):
                return True

            if self._entity_touches_segment(entity, start, end, tolerance):
                return True

            box = entity.bounding_box
            center = box.center

            if point_to_segment_distance(center, start, end) <= tolerance:
                return True

            if hit_curve(center, [start, end], False, tolerance):
                return True

        return False

    # --------------------------------

    def _entity_touches_segment(self, entity, start, end, tolerance):

        distance = start.distance_to(end)

        if distance <= tolerance:
            return entity.hit_test(start)

        steps = max(2, int(distance / max(tolerance, 1.0)))

        for index in range(steps + 1):
            t = index / steps
            sample = Vector2(
                start.x + (end.x - start.x) * t,
                start.y + (end.y - start.y) * t,
            )

            if entity.hit_test(sample):
                return True

        return False

    # --------------------------------

    def _clean_name(self, name):

        return str(name or "").strip()

    # --------------------------------

    @property
    def count(self):

        return len(self.selected)

    # --------------------------------

    @property
    def first(self):

        if self.selected:

            return self.selected[0]

        return None


def _point_in_polygon(point, polygon):
    """Return True when point lies inside a polygon."""

    if len(polygon) < 3:
        return False

    inside = False
    previous = polygon[-1]

    for current in polygon:
        if (
            (current.y > point.y) != (previous.y > point.y) and
            point.x < (
                (previous.x - current.x) *
                (point.y - current.y) /
                ((previous.y - current.y) or 1e-9) +
                current.x
            )
        ):
            inside = not inside

        previous = current

    return inside
