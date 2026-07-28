from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS


class OCCMesher:
    """
    Generates triangulation for TopoDS_Shapes.
    This prepares OCC solids for rendering.
    """

    def __init__(
        self,
        linear_deflection=0.5,
        angular_deflection=0.5,
    ):
        self.linear_deflection = linear_deflection
        self.angular_deflection = angular_deflection

    # --------------------------------------------------

    def mesh(self, shape):

        mesher = BRepMesh_IncrementalMesh(
            shape,
            self.linear_deflection,
            False,
            self.angular_deflection,
            True,
        )

        mesher.Perform()

        if not mesher.IsDone():
            raise RuntimeError("Failed to mesh OCC shape.")

        return shape

    # --------------------------------------------------

    def triangulation(self, shape):

        self.mesh(shape)

        vertices = []
        triangles = []

        explorer = TopExp_Explorer(shape, TopAbs_FACE)

        while explorer.More():

            face = TopoDS.Face_s(explorer.Current())

            location = TopLoc_Location()

            poly = BRep_Tool.Triangulation_s(
                face,
                location,
            )

            if poly is not None:

                nodes = poly.Nodes()

                start = len(vertices)

                for i in range(1, poly.NbNodes() + 1):

                    p = nodes.Value(i)

                    vertices.append(
                        (
                            p.X(),
                            p.Y(),
                            p.Z(),
                        )
                    )

                tris = poly.Triangles()

                for i in range(1, poly.NbTriangles() + 1):

                    tri = tris.Value(i)

                    a, b, c = tri.Get()

                    triangles.append(
                        (
                            start + a - 1,
                            start + b - 1,
                            start + c - 1,
                        )
                    )

            explorer.Next()

        return vertices, triangles

    # --------------------------------------------------

    def mesh_manager(self, occ_manager):

        meshes = []

        for shape in occ_manager.shapes:

            meshes.append(
                self.triangulation(shape)
            )

        return meshes