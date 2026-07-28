from engine.commands.command import Command


class DeleteCommand(Command):

    def __init__(self, project, entity):

        self.project = project
        self.entity = entity
        self._deleted_occ_shape = False
        self._previous_selection = None
        self._previous_occ_shapes = None

    def execute(self):

        occ = getattr(self.project, "occ", None)

        if occ is not None and self.entity in getattr(occ, "shapes", []):
            workspace = getattr(self.project, "workspace", None)
            self._previous_selection = list(workspace.selection.selected) if workspace is not None else []
            self._previous_occ_shapes = list(occ.shapes)
            self._deleted_occ_shape = occ.remove(self.entity)
            occ_selection = getattr(self.project, "occ_selection", None)

            if occ_selection is not None:
                occ_selection.deselect(self.entity)

            if workspace is not None:
                workspace.selection.unregister_entity(self.entity)

            return

        self.project.remove(self.entity)

    def undo(self):

        if self._deleted_occ_shape:
            if self.entity not in self.project.occ.shapes:
                self.project.occ.add(self.entity)

            workspace = getattr(self.project, "workspace", None)

            if workspace is not None:
                workspace.selection.clear()

                for item in self._previous_selection or [self.entity]:
                    if item not in (self._previous_occ_shapes or []) or item in self.project.occ.shapes:
                        workspace.selection.select(item, True)

            return

        self.project.add(self.entity)
