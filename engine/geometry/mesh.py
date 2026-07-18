from dataclasses import dataclass

from engine.geometry.bounding_box3d import BoundingBox3D
from engine.geometry.bounding_sphere import BoundingSphere
from engine.geometry.vector3 import Vector3


@dataclass
class Vertex:
    """Mesh vertex with position, normal, and optional UV coordinates."""

    position: Vector3
    normal: Vector3 = None
    uv: tuple = None

    def __post_init__(self):

        if self.normal is None:
            self.normal = Vector3(0.0, 0.0, 1.0)

        if self.uv is None:
            self.uv = (0.0, 0.0)


@dataclass
class Edge:
    """Mesh edge by vertex indices."""

    start: int
    end: int


@dataclass
class Face:
    """Mesh face by vertex indices."""

    indices: list
    normal: Vector3 = None


class MeshData:
    """Reusable indexed mesh data with normals and bounds."""

    def __init__(self, vertices=None, edges=None, faces=None):

        self.vertices = list(vertices or [])
        self.edges = list(edges or [])
        self.faces = list(faces or [])
        self.triangle_indices = []
        self.rebuild()

    # --------------------------------

    def rebuild(self):
        """Recalculate triangles, normals and bounding data."""

        self.triangle_indices = self._build_triangle_indices()
        self._calculate_normals()

    # --------------------------------

    @property
    def bounding_box3d(self):
        """Return the mesh bounds."""

        box = BoundingBox3D()

        for vertex in self.vertices:
            box.add(vertex.position)

        return box

    # --------------------------------

    @property
    def bounding_sphere(self):
        """Return a coarse mesh bounding sphere."""

        return BoundingSphere.from_box(self.bounding_box3d)

    # --------------------------------

    def positions(self):
        """Return vertex positions."""

        return [vertex.position for vertex in self.vertices]

    # --------------------------------

    def edge_segments(self):
        """Return edge point pairs."""

        segments = []

        for edge in self.edges:
            if self._valid_index(edge.start) and self._valid_index(edge.end):
                segments.append((
                    self.vertices[edge.start].position,
                    self.vertices[edge.end].position,
                ))

        return segments

    # --------------------------------

    def face_triangles(self):
        """Return triangle point triples."""

        triangles = []

        for a, b, c in self.triangle_indices:
            if self._valid_index(a) and self._valid_index(b) and self._valid_index(c):
                triangles.append((
                    self.vertices[a].position,
                    self.vertices[b].position,
                    self.vertices[c].position,
                ))

        return triangles

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe mesh data."""

        return {
            "vertices": [
                {
                    "position": _vector_to_data(vertex.position),
                    "normal": _vector_to_data(vertex.normal),
                    "uv": _uv_to_data(vertex.uv),
                }
                for vertex in self.vertices
            ],
            "edges": [
                {"start": edge.start, "end": edge.end}
                for edge in self.edges
            ],
            "faces": [
                {
                    "indices": list(face.indices),
                    "normal": _vector_to_data(face.normal) if face.normal else None,
                }
                for face in self.faces
            ],
        }

    # --------------------------------

    @staticmethod
    def from_dict(data):
        """Create mesh data from persisted data."""

        data = data or {}
        vertices = [
            Vertex(
                _vector_from_data(item.get("position")),
                _vector_from_data(item.get("normal")),
                _uv_from_data(item.get("uv")),
            )
            for item in data.get("vertices", [])
        ]
        edges = [
            Edge(item.get("start", 0), item.get("end", 0))
            for item in data.get("edges", [])
        ]
        faces = [
            Face(
                list(item.get("indices", [])),
                _vector_from_data(item.get("normal")) if item.get("normal") else None,
            )
            for item in data.get("faces", [])
        ]

        return MeshData(vertices, edges, faces)

    # --------------------------------

    @staticmethod
    def box(width=100.0, depth=100.0, height=100.0):
        """Create a simple box mesh for tests and future primitives."""

        hw = width * 0.5
        hd = depth * 0.5
        hh = height * 0.5
        points = [
            Vector3(-hw, -hd, -hh),
            Vector3(hw, -hd, -hh),
            Vector3(hw, hd, -hh),
            Vector3(-hw, hd, -hh),
            Vector3(-hw, -hd, hh),
            Vector3(hw, -hd, hh),
            Vector3(hw, hd, hh),
            Vector3(-hw, hd, hh),
        ]
        edges = [
            Edge(0, 1), Edge(1, 2), Edge(2, 3), Edge(3, 0),
            Edge(4, 5), Edge(5, 6), Edge(6, 7), Edge(7, 4),
            Edge(0, 4), Edge(1, 5), Edge(2, 6), Edge(3, 7),
        ]
        faces = [
            Face([0, 1, 2, 3]),
            Face([4, 5, 6, 7]),
            Face([0, 1, 5, 4]),
            Face([1, 2, 6, 5]),
            Face([2, 3, 7, 6]),
            Face([3, 0, 4, 7]),
        ]

        return MeshData([Vertex(point) for point in points], edges, faces)

    # --------------------------------

    def _build_triangle_indices(self):

        triangles = []

        for face in self.faces:
            indices = list(face.indices)

            if len(indices) < 3:
                continue

            for index in range(1, len(indices) - 1):
                triangles.append((indices[0], indices[index], indices[index + 1]))

        return triangles

    # --------------------------------

    def _calculate_normals(self):

        normals = [Vector3() for _ in self.vertices]

        for face in self.faces:
            normal = self._face_normal(face.indices)
            face.normal = normal

            for index in face.indices:
                if self._valid_index(index):
                    normals[index] = normals[index] + normal

        for index, normal in enumerate(normals):
            if normal.length_squared() > 0.0:
                self.vertices[index].normal = normal.normalized()

    # --------------------------------

    def _face_normal(self, indices):

        if len(indices) < 3:
            return Vector3(0.0, 0.0, 1.0)

        a = self.vertices[indices[0]].position
        b = self.vertices[indices[1]].position
        c = self.vertices[indices[2]].position

        return (b - a).cross(c - a).normalized()

    # --------------------------------

    def _valid_index(self, index):

        return 0 <= index < len(self.vertices)


def _vector_to_data(vector):

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_data(data):

    data = data or {}

    return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))


def _uv_to_data(uv):

    u, v = uv or (0.0, 0.0)

    return {"u": u, "v": v}


def _uv_from_data(data):

    data = data or {}

    return (float(data.get("u", 0.0)), float(data.get("v", 0.0)))
