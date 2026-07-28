from engine.commands.command import Command


class ImportOCCShapeCommand(Command):
    """Undoable STEP/BREP import using the existing CADEngine OCC backend."""

    def __init__(self, cad_engine, workspace, path):

        self.cad_engine = cad_engine
        self.workspace = workspace
        self.path = path
        self.shape = None
        self.previous_selection = None
        self.previous_shapes = None

    # --------------------------------

    def execute(self):

        self.previous_selection = list(self.workspace.selection.selected)
        self.previous_shapes = list(self.cad_engine.occ.shapes)

        if self.shape is None:
            self.shape = self.cad_engine.import_model(self.path)
        elif self.shape not in self.cad_engine.occ.shapes:
            self.cad_engine.occ.add(self.shape)

        self.workspace.selection.clear()
        self.workspace.selection.select(self.shape)

    # --------------------------------

    def undo(self):

        if self.shape in self.cad_engine.occ.shapes:
            self.cad_engine.occ.remove(self.shape)

        self.workspace.selection.unregister_entity(self.shape)
        self.workspace.selection.clear()

        for item in self.previous_selection or []:
            if item is self.shape:
                continue

            if item not in (self.previous_shapes or []) or item in self.cad_engine.occ.shapes:
                self.workspace.selection.select(item, True)
