from engine.commands.command import Command


class OCCBooleanCommand(Command):
    """Undoable OCC boolean operation using the existing CADEngine backend."""

    def __init__(self, cad_engine, workspace, operation, shape_a, shape_b):

        self.cad_engine = cad_engine
        self.workspace = workspace
        self.operation = operation
        self.shape_a = shape_a
        self.shape_b = shape_b
        self.previous_shapes = None
        self.previous_selection = None
        self.result = None

    # --------------------------------

    def execute(self):

        occ = self.cad_engine.occ

        self.previous_shapes = list(occ.shapes)
        self.previous_selection = list(self.workspace.selection.selected)

        if self.operation == "union":
            result = self.cad_engine.boolean_union(self.shape_a, self.shape_b)
        elif self.operation == "subtract":
            result = self.cad_engine.boolean_subtract(self.shape_a, self.shape_b)
        elif self.operation == "intersect":
            result = self.cad_engine.boolean_intersect(self.shape_a, self.shape_b)
        else:
            raise ValueError(f"Unknown OCC boolean operation: {self.operation}")

        remaining = [
            shape for shape in self.previous_shapes
            if shape is not self.shape_a and shape is not self.shape_b
        ]
        occ.clear()

        for shape in remaining:
            occ.add(shape)

        occ.add(result)
        self.result = result
        self.workspace.selection.clear()
        self.workspace.selection.select(result)

    # --------------------------------

    def undo(self):

        if self.previous_shapes is None:
            return

        occ = self.cad_engine.occ
        occ.clear()

        for shape in self.previous_shapes:
            occ.add(shape)

        self.workspace.selection.clear()

        for shape in self.previous_selection or []:
            if shape not in (self.previous_shapes or []) or shape in occ.shapes:
                self.workspace.selection.select(shape, True)
