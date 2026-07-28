from OCP.BRepAlgoAPI import (
    BRepAlgoAPI_Common,
    BRepAlgoAPI_Cut,
    BRepAlgoAPI_Fuse,
)


class OCCBoolean:
    """Boolean operations for OpenCascade solids."""

    # -----------------------------------------------------

    def union(
        self,
        shape_a,
        shape_b,
    ):

        operation = BRepAlgoAPI_Fuse(
            shape_a,
            shape_b,
        )

        operation.Build()

        if not operation.IsDone():
            raise RuntimeError("Boolean Union failed.")

        return operation.Shape()

    # -----------------------------------------------------

    def subtract(
        self,
        shape_a,
        shape_b,
    ):

        operation = BRepAlgoAPI_Cut(
            shape_a,
            shape_b,
        )

        operation.Build()

        if not operation.IsDone():
            raise RuntimeError("Boolean Subtract failed.")

        return operation.Shape()

    # -----------------------------------------------------

    def intersect(
        self,
        shape_a,
        shape_b,
    ):

        operation = BRepAlgoAPI_Common(
            shape_a,
            shape_b,
        )

        operation.Build()

        if not operation.IsDone():
            raise RuntimeError("Boolean Intersect failed.")

        return operation.Shape()

    # -----------------------------------------------------

    def replace(
        self,
        occ_manager,
        shape_a,
        shape_b,
        operation,
    ):

        if operation == "union":
            result = self.union(
                shape_a,
                shape_b,
            )

        elif operation == "subtract":
            result = self.subtract(
                shape_a,
                shape_b,
            )

        elif operation == "intersect":
            result = self.intersect(
                shape_a,
                shape_b,
            )

        else:
            raise ValueError(
                f"Unknown Boolean operation: {operation}"
            )

        occ_manager.clear()

        occ_manager.add(result)

        return result