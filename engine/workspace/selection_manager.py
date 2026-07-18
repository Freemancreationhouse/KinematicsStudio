from dataclasses import dataclass

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
)
from engine.geometry import Vector2
from engine.geometry.curves import hit_curve
from engine.geometry.primitives import point_to_segment_distance


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
        self.selection_sets = {}
        self._cycle_point = None
        self._cycle_candidates = []
        self._cycle_index = -1

    # --------------------------------

    def clear(self):
        """Clear the current selection while preserving previous selection."""

        self._remember_previous()
        for entity in self.selected:

            entity.selected = False

        self.selected.clear()

    # --------------------------------

    def select(self, entity, additive=False):
        """Select one entity."""

        if not additive:

            self.clear()

        if entity not in self.selected:

            entity.selected = True

            self.selected.append(entity)

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

            entity.selected = False

            self.selected.remove(entity)

    # --------------------------------

    def unregister_entity(self, entity):
        """Remove a deleted entity from all selection-owned references."""

        self.deselect(entity)

        self.previous = [
            item for item in self.previous
            if item is not entity
        ]

        for selection_set in self.selection_sets.values():
            selection_set.entities = [
                item for item in selection_set.entities
                if item is not entity
            ]

        self._cycle_candidates = [
            item for item in self._cycle_candidates
            if item is not entity
        ]

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
        ]

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
