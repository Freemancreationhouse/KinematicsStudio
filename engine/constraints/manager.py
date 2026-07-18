from engine.constraints.constraint import Constraint
from engine.constraints.solver import ConstraintSolver


class ConstraintManager:
    """Workspace-owned manager for all geometric and dimensional constraints."""

    def __init__(self, workspace=None):

        self.workspace = workspace
        self.constraints = []
        self._by_id = {}
        self._by_name = {}
        self._next_id = 0
        self.current = None
        self.solver = ConstraintSolver()

    # --------------------------------

    def create(self, constraint_type, entities=None, value=None, name=None, driven=False):
        """Create and register a unique constraint."""

        constraint = Constraint(
            constraint_type,
            entities,
            value,
            self.unique_name(name or constraint_type),
            self._next_id,
            driven,
        )
        self._next_id += 1
        self.add(constraint)

        return constraint

    # --------------------------------

    def add(self, constraint):
        """Add an existing constraint instance."""

        if constraint.id is None:
            constraint.id = self._next_id
            self._next_id += 1

        if constraint.id >= self._next_id:
            self._next_id = constraint.id + 1

        if constraint.name in self._by_name and self._by_name[constraint.name] is not constraint:
            constraint.name = self.unique_name(constraint.name)

        if constraint not in self.constraints:
            self.constraints.append(constraint)

        self._by_id[constraint.id] = constraint
        self._by_name[constraint.name] = constraint
        self.current = constraint
        self.validate()

        return constraint

    # --------------------------------

    def remove(self, constraint):
        """Remove a constraint without touching entity geometry."""

        target = self._coerce_constraint(constraint)

        if target is None:
            return False

        if target in self.constraints:
            self.constraints.remove(target)

        self._by_id.pop(target.id, None)
        self._by_name.pop(target.name, None)

        if self.current is target:
            self.current = self.constraints[0] if self.constraints else None

        self.validate()

        return True

    # --------------------------------

    def rename(self, constraint, new_name):
        """Rename a constraint while preserving its ID."""

        target = self._coerce_constraint(constraint)
        clean = str(new_name or "").strip()

        if target is None or not clean:
            return False

        if clean in self._by_name and self._by_name[clean] is not target:
            return False

        self._by_name.pop(target.name, None)
        target.name = clean
        self._by_name[target.name] = target

        return True

    # --------------------------------

    def set_enabled(self, constraint, enabled):
        """Enable or disable a constraint."""

        target = self._coerce_constraint(constraint)

        if target is None:
            return False

        target.enabled = bool(enabled)
        target.suppressed = not target.enabled
        self.validate()

        return True

    # --------------------------------

    def update(self, constraint, **values):
        """Update editable constraint fields."""

        target = self._coerce_constraint(constraint)

        if target is None:
            return False

        for key in ("constraint_type", "value", "driven", "suppressed", "enabled"):
            if key in values:
                setattr(target, key, values[key])

        if "entities" in values:
            target.entities = list(values["entities"])

        self.validate()

        return True

    # --------------------------------

    def validate(self):
        """Validate every constraint and return the graph status."""

        graph = self.solver.validate(self)

        return graph.status

    # --------------------------------

    def solve(self, command_manager=None):
        """Run solver using the workspace and optional command manager."""

        return self.solver.solve(self, command_manager)

    # --------------------------------

    def selectable_constraints(self):
        """Return constraints available for selection."""

        return [
            constraint for constraint in self.constraints
            if constraint.visible
        ]

    # --------------------------------

    def constraints_for_entity(self, entity):
        """Return constraints referencing an entity."""

        return [
            constraint for constraint in self.constraints
            if constraint.references(entity)
        ]

    # --------------------------------

    def unique_name(self, name):
        """Return a unique constraint name."""

        base = str(name or "Constraint").strip() or "Constraint"

        if base not in self._by_name:
            return base

        index = 1

        while f"{base} {index}" in self._by_name:
            index += 1

        return f"{base} {index}"

    # --------------------------------

    def get(self, value):
        """Return a constraint by ID or name."""

        if isinstance(value, int):
            return self._by_id.get(value)

        return self._by_name.get(value)

    # --------------------------------

    def _coerce_constraint(self, constraint):

        if isinstance(constraint, Constraint):
            return constraint

        return self.get(constraint)
