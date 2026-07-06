from copy import deepcopy

from engine.commands.command import Command


class UpdateEntityCommand(Command):
    """Undoable entity state update.

    The legacy constructor accepts ``(entity, new_entity)`` and copies the
    replacement entity dictionary.  Property editing can also pass explicit
    before/after dictionaries plus a workspace so layer assignment remains
    synchronized with the LayerManager.
    """

    def __init__(self, entity, new_entity=None, workspace=None, before=None, after=None):

        self.entity = entity
        self.workspace = workspace

        if before is None or after is None:
            self.before = deepcopy(entity.__dict__)
            self.after = deepcopy(new_entity.__dict__)
        else:
            self.before = deepcopy(before)
            self.after = deepcopy(after)

    # --------------------------------

    def _apply(self, state):

        layer_id = state.get("layer_id")

        if self.workspace is not None and layer_id is not None:
            layer = self.workspace.layer_manager.get_by_id(layer_id)

            if layer is not None:
                self.workspace.assign_layer(self.entity, layer)

        for key, value in state.items():
            if (
                self.workspace is not None and
                key in ("layer", "layer_id", "layer_name")
            ):
                continue

            setattr(self.entity, key, deepcopy(value))

    # --------------------------------

    def execute(self):

        self._apply(self.after)

    # --------------------------------

    def undo(self):

        self._apply(self.before)


class UpdateLayerCommand(Command):
    """Undoable layer property update through the workspace LayerManager."""

    def __init__(self, workspace, layer, before, after):

        self.workspace = workspace
        self.layer_id = layer.id
        self.before = deepcopy(before)
        self.after = deepcopy(after)

    # --------------------------------

    def _apply(self, state):

        layer = self.workspace.layer_manager.get_by_id(self.layer_id)

        if layer is None:
            return

        if "visible" in state:
            layer.visible = bool(state["visible"])

        if "locked" in state:
            layer.locked = bool(state["locked"])

        self.workspace.update_layer_properties(
            layer,
            color=state.get("color"),
            line_type=state.get("line_type"),
            line_weight=state.get("line_weight"),
        )

    # --------------------------------

    def execute(self):

        self._apply(self.after)

    # --------------------------------

    def undo(self):

        self._apply(self.before)
