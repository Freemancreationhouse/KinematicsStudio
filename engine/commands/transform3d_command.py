from copy import deepcopy

from engine.commands.command import Command
from engine.geometry import Matrix4, Vector3


class TransformEntity3DCommand(Command):
    """Base undoable transform command for one or more 3D entities."""

    def __init__(self, workspace, entities, pivot=None):

        self.workspace = workspace
        self.entities = [
            entity for entity in entities
            if getattr(entity, "is_3d", False)
        ]
        self.pivot = pivot or self._default_pivot()
        self.before = [self._state(entity) for entity in self.entities]
        self.after = []

    # --------------------------------

    def execute(self):
        """Apply the transform and record one command-history entry."""

        if not self.after:
            self.after = [
                self._transformed_state(entity)
                for entity in self.entities
            ]

        self._apply_states(self.after)
        self.workspace.selection.select_many(self.entities)

    # --------------------------------

    def undo(self):
        """Restore the previous transform states."""

        self._apply_states(self.before)
        self.workspace.selection.select_many(self.entities)

    # --------------------------------

    def preview_states(self):
        """Return detached preview states without editing the workspace."""

        return [
            self._transformed_state(entity)
            for entity in self.entities
        ]

    # --------------------------------

    def _transformed_state(self, entity):

        return self._state(entity)

    # --------------------------------

    def _apply_states(self, states):

        for state in states:
            entity = state["entity"]
            entity.position3d = state["position3d"].copy()
            entity.rotation3d = state["rotation3d"].copy()
            entity.scale3d = state["scale3d"].copy()
            entity.transform = state["transform"].copy()

    # --------------------------------

    def _state(self, entity):

        return {
            "entity": entity,
            "position3d": deepcopy(getattr(entity, "position3d", Vector3())),
            "rotation3d": deepcopy(getattr(entity, "rotation3d", Vector3())),
            "scale3d": deepcopy(getattr(entity, "scale3d", Vector3(1.0, 1.0, 1.0))),
            "transform": getattr(entity, "transform", Matrix4.identity()).copy(),
        }

    # --------------------------------

    def _default_pivot(self):

        gizmo = getattr(self.workspace, "transform_gizmo", None)

        if gizmo is not None:
            return gizmo.pivot_for_selection(self.entities)

        return Vector3()


class TranslateEntity3DCommand(TransformEntity3DCommand):
    """Translate one or more 3D entities."""

    def __init__(self, workspace, entities, delta, pivot=None, axis=None, plane=None):

        self.delta = _snap_delta(workspace, entities, _constrain_delta(delta, axis, plane))
        self.axis = axis
        self.plane = plane
        super().__init__(workspace, entities, pivot)

    # --------------------------------

    def _transformed_state(self, entity):

        state = self._state(entity)
        state["position3d"] = state["position3d"] + self.delta
        state["transform"] = Matrix4.translation(self.delta) @ state["transform"]

        return state


class RotateEntity3DCommand(TransformEntity3DCommand):
    """Rotate one or more 3D entities around a pivot."""

    def __init__(self, workspace, entities, rotation, pivot=None, axis=None):

        self.rotation = _constrain_rotation(rotation, axis)
        self.axis = axis
        super().__init__(workspace, entities, pivot)

    # --------------------------------

    def _transformed_state(self, entity):

        state = self._state(entity)
        rotation = self.rotation
        state["rotation3d"] = state["rotation3d"] + rotation
        matrix = Matrix4.around_pivot(Matrix4.rotation_euler(rotation), self.pivot)
        state["transform"] = matrix @ state["transform"]

        return state


class ScaleEntity3DCommand(TransformEntity3DCommand):
    """Scale one or more 3D entities around a pivot."""

    def __init__(self, workspace, entities, scale, pivot=None, axis=None):

        self.scale = _constrain_scale(scale, axis)
        self.axis = axis
        super().__init__(workspace, entities, pivot)

    # --------------------------------

    def _transformed_state(self, entity):

        state = self._state(entity)
        scale = self.scale
        state["scale3d"] = Vector3(
            state["scale3d"].x * scale.x,
            state["scale3d"].y * scale.y,
            state["scale3d"].z * scale.z,
        )
        matrix = Matrix4.around_pivot(Matrix4.scaling(scale), self.pivot)
        state["transform"] = matrix @ state["transform"]

        return state


def _constrain_delta(delta, axis=None, plane=None):

    x = delta.x
    y = delta.y
    z = delta.z

    if axis == "X":
        return Vector3(x, 0.0, 0.0)
    if axis == "Y":
        return Vector3(0.0, y, 0.0)
    if axis == "Z":
        return Vector3(0.0, 0.0, z)

    if plane == "XY":
        return Vector3(x, y, 0.0)
    if plane == "XZ":
        return Vector3(x, 0.0, z)
    if plane == "YZ":
        return Vector3(0.0, y, z)

    return delta


def _constrain_rotation(rotation, axis=None):

    if axis == "X":
        return Vector3(rotation.x, 0.0, 0.0)
    if axis == "Y":
        return Vector3(0.0, rotation.y, 0.0)
    if axis == "Z":
        return Vector3(0.0, 0.0, rotation.z)

    return rotation


def _constrain_scale(scale, axis=None):

    if axis == "X":
        return Vector3(scale.x, 1.0, 1.0)
    if axis == "Y":
        return Vector3(1.0, scale.y, 1.0)
    if axis == "Z":
        return Vector3(1.0, 1.0, scale.z)

    return scale


def _snap_delta(workspace, entities, delta):

    snap_manager = getattr(workspace, "snap_manager3d", None)

    if snap_manager is None or not snap_manager.enabled:
        return delta

    if snap_manager.active_snap is not None and entities:
        source = getattr(entities[0], "position3d", Vector3())
        target = snap_manager.active_snap.point
        return target - source

    return delta
