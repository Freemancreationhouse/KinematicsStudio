import math
from copy import deepcopy

from engine.geometry import Vector2
from engine.geometry.primitives import are_parallel_segments, is_degenerate_segment
from engine.geometry.tolerance import GEOMETRY_EPSILON, nearly_equal


class ConstraintGraph:
    """Dependency graph and validation result for the constraint manager."""

    def __init__(self):

        self.nodes = set()
        self.edges = {}
        self.conflicts = []
        self.under_constrained = []
        self.status = "OK"

    # --------------------------------

    def add_constraint(self, constraint):
        """Track a constraint and its referenced entities."""

        self.nodes.add(constraint)

        for entity in constraint.entities:
            self.nodes.add(entity)
            self.edges.setdefault(entity, []).append(constraint)

    # --------------------------------

    def mark_conflict(self, constraint, message):
        """Register a solver conflict."""

        self.conflicts.append((constraint, message))
        self.status = "Over-constrained"

    # --------------------------------

    def mark_under_constrained(self, entity):
        """Register an entity with no active constraints."""

        self.under_constrained.append(entity)

        if self.status == "OK":
            self.status = "Under-constrained"


class ConstraintSolver:
    """Incremental validator and lightweight geometry solver."""

    def validate(self, manager):
        """Validate active constraints and annotate their status."""

        graph = self.build_graph(manager)

        for constraint in manager.constraints:
            self._validate_constraint(constraint, graph)

        if manager.workspace is not None:
            constrained = {
                entity
                for constraint in manager.constraints
                if constraint.enabled and not constraint.suppressed
                for entity in constraint.entities
            }

            for entity in manager.workspace.entities:
                if entity not in constrained:
                    graph.mark_under_constrained(entity)

        self._detect_conflicts(manager, graph)

        return graph

    # --------------------------------

    def build_graph(self, manager):
        """Build dependency graph from active constraints."""

        graph = ConstraintGraph()

        for constraint in manager.constraints:
            if constraint.enabled and not constraint.suppressed:
                graph.add_constraint(constraint)

        return graph

    # --------------------------------

    def solve(self, manager, command_manager=None):
        """Apply simple driving constraints through UpdateEntityCommand."""

        graph = self.validate(manager)

        if graph.conflicts or command_manager is None:
            return graph

        for constraint in manager.constraints:
            state = self._solved_state(constraint)

            if state:
                self._execute_update(command_manager, constraint.entities[0], state)

        self.validate(manager)

        return graph

    # --------------------------------

    def _validate_constraint(self, constraint, graph):

        if not constraint.enabled or constraint.suppressed:
            constraint.status = "Suppressed"
            constraint.message = ""
            return

        if not constraint.entities:
            constraint.status = "Invalid"
            constraint.message = "No referenced entities"
            graph.mark_conflict(constraint, constraint.message)
            return

        ok, message = self._check_geometry(constraint)
        constraint.status = "Satisfied" if ok else "Unsatisfied"
        constraint.message = message

    # --------------------------------

    def _check_geometry(self, constraint):

        kind = constraint.constraint_type
        entities = constraint.entities
        first = entities[0]
        second = entities[1] if len(entities) > 1 else None

        if kind == "Horizontal" and hasattr(first, "start"):
            return nearly_equal(first.start.y, first.end.y), "Line is not horizontal"

        if kind == "Vertical" and hasattr(first, "start"):
            return nearly_equal(first.start.x, first.end.x), "Line is not vertical"

        if kind == "Parallel" and second is not None:
            return self._parallel(first, second), "Entities are not parallel"

        if kind == "Perpendicular" and second is not None:
            return self._perpendicular(first, second), "Entities are not perpendicular"

        if kind == "Equal" and second is not None:
            return nearly_equal(self._length(first), self._length(second)), "Lengths are not equal"

        if kind == "Concentric" and second is not None:
            return self._same_center(first, second), "Centers are not coincident"

        if kind == "Tangent" and second is not None:
            return True, ""

        if kind in ("Coincident", "Symmetry", "Midpoint"):
            return True, ""

        if kind in ("Distance", "Horizontal Distance", "Vertical Distance"):
            return self._distance_satisfied(constraint), "Distance value is not satisfied"

        if kind == "Radius" and hasattr(first, "radius"):
            return nearly_equal(first.radius, float(constraint.value or 0.0)), "Radius value is not satisfied"

        if kind == "Diameter" and hasattr(first, "radius"):
            return nearly_equal(first.radius * 2.0, float(constraint.value or 0.0)), "Diameter value is not satisfied"

        if kind == "Angle":
            return True, ""

        return True, ""

    # --------------------------------

    def _detect_conflicts(self, manager, graph):

        by_entity_kind = {}

        for constraint in manager.constraints:
            if not constraint.enabled or constraint.suppressed:
                continue

            if constraint.constraint_type not in ("Distance", "Horizontal Distance", "Vertical Distance", "Radius", "Diameter"):
                continue

            key = (constraint.constraint_type, tuple(id(entity) for entity in constraint.entities))
            previous = by_entity_kind.get(key)

            if previous is not None and not nearly_equal(float(previous.value or 0.0), float(constraint.value or 0.0)):
                graph.mark_conflict(constraint, "Conflicting driven values")
                constraint.status = "Conflict"

            by_entity_kind[key] = constraint

    # --------------------------------

    def _solved_state(self, constraint):

        if constraint.driven or not constraint.enabled or constraint.suppressed:
            return None

        entity = constraint.entities[0]
        kind = constraint.constraint_type

        if kind == "Horizontal" and hasattr(entity, "start"):
            return {"end": Vector2(entity.end.x, entity.start.y)}

        if kind == "Vertical" and hasattr(entity, "start"):
            return {"end": Vector2(entity.start.x, entity.end.y)}

        if kind == "Parallel" and len(constraint.entities) > 1:
            return self._parallel_state(entity, constraint.entities[1])

        if kind == "Perpendicular" and len(constraint.entities) > 1:
            return self._perpendicular_state(entity, constraint.entities[1])

        if kind == "Equal" and len(constraint.entities) > 1:
            return self._line_distance_state(entity, self._length(constraint.entities[1]))

        if kind == "Concentric" and len(constraint.entities) > 1 and hasattr(entity, "center"):
            other = constraint.entities[1]

            if hasattr(other, "center"):
                return {"center": other.center.copy()}

        if kind == "Distance" and hasattr(entity, "start"):
            return self._line_distance_state(entity, float(constraint.value or 0.0))

        if kind == "Horizontal Distance" and hasattr(entity, "start"):
            return {"end": Vector2(entity.start.x + float(constraint.value or 0.0), entity.end.y)}

        if kind == "Vertical Distance" and hasattr(entity, "start"):
            return {"end": Vector2(entity.end.x, entity.start.y + float(constraint.value or 0.0))}

        if kind == "Radius" and hasattr(entity, "radius"):
            return {"radius": max(0.0, float(constraint.value or 0.0))}

        if kind == "Diameter" and hasattr(entity, "radius"):
            return {"radius": max(0.0, float(constraint.value or 0.0) * 0.5)}

        return None

    # --------------------------------

    def _parallel_state(self, entity, other):

        if not all(hasattr(item, "start") and hasattr(item, "end") for item in (entity, other)):
            return None

        length = self._length(entity)
        dx = other.end.x - other.start.x
        dy = other.end.y - other.start.y
        other_length = math.hypot(dx, dy)

        if other_length <= GEOMETRY_EPSILON:
            return None

        return {
            "end": Vector2(
                entity.start.x + dx / other_length * length,
                entity.start.y + dy / other_length * length,
            )
        }

    # --------------------------------

    def _perpendicular_state(self, entity, other):

        if not all(hasattr(item, "start") and hasattr(item, "end") for item in (entity, other)):
            return None

        length = self._length(entity)
        dx = other.end.x - other.start.x
        dy = other.end.y - other.start.y
        other_length = math.hypot(dx, dy)

        if other_length <= GEOMETRY_EPSILON:
            return None

        return {
            "end": Vector2(
                entity.start.x - dy / other_length * length,
                entity.start.y + dx / other_length * length,
            )
        }

    # --------------------------------

    def _execute_update(self, command_manager, entity, state):

        from engine.commands import UpdateEntityCommand

        before = deepcopy(entity.__dict__)
        after = deepcopy(entity.__dict__)
        after.update(state)

        if after != before:
            command_manager.execute(UpdateEntityCommand(entity, before=before, after=after))

    # --------------------------------

    def _line_distance_state(self, entity, distance):

        dx = entity.end.x - entity.start.x
        dy = entity.end.y - entity.start.y
        length = math.hypot(dx, dy)

        if length <= GEOMETRY_EPSILON:
            return {"end": Vector2(entity.start.x + distance, entity.start.y)}

        return {
            "end": Vector2(
                entity.start.x + dx / length * distance,
                entity.start.y + dy / length * distance,
            )
        }

    # --------------------------------

    def _distance_satisfied(self, constraint):

        entity = constraint.entities[0]
        value = float(constraint.value or 0.0)

        if not hasattr(entity, "start"):
            return True

        if constraint.constraint_type == "Horizontal Distance":
            return nearly_equal(abs(entity.end.x - entity.start.x), abs(value))

        if constraint.constraint_type == "Vertical Distance":
            return nearly_equal(abs(entity.end.y - entity.start.y), abs(value))

        return nearly_equal(entity.start.distance_to(entity.end), abs(value))

    # --------------------------------

    def _length(self, entity):

        if hasattr(entity, "length"):
            return float(entity.length)

        if hasattr(entity, "start") and hasattr(entity, "end"):
            return entity.start.distance_to(entity.end)

        return 0.0

    # --------------------------------

    def _parallel(self, first, second):

        if not all(hasattr(entity, "start") and hasattr(entity, "end") for entity in (first, second)):
            return True

        return are_parallel_segments(first.start, first.end, second.start, second.end)

    # --------------------------------

    def _perpendicular(self, first, second):

        if not all(hasattr(entity, "start") and hasattr(entity, "end") for entity in (first, second)):
            return True

        if is_degenerate_segment(first.start, first.end) or is_degenerate_segment(second.start, second.end):
            return False

        ax = first.end.x - first.start.x
        ay = first.end.y - first.start.y
        bx = second.end.x - second.start.x
        by = second.end.y - second.start.y

        return nearly_equal(ax * bx + ay * by, 0.0)

    # --------------------------------

    def _same_center(self, first, second):

        if not all(hasattr(entity, "center") for entity in (first, second)):
            return True

        return first.center.distance_to(second.center) <= GEOMETRY_EPSILON
