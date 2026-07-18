import math

from engine.geometry.mesh import Edge, Face, MeshData, Vertex
from engine.geometry.vector3 import Vector3


class MeshBuilder:
    """Shared helper for building indexed MeshData for generated primitives."""

    def __init__(self):

        self.vertices = []
        self.edges = []
        self.faces = []
        self._edge_keys = set()

    # --------------------------------

    def add_vertex(self, position, normal=None, uv=None):
        """Add a vertex and return its index."""

        self.vertices.append(Vertex(position, normal, uv))

        return len(self.vertices) - 1

    # --------------------------------

    def add_edge(self, start, end):
        """Add an edge once, independent of winding order."""

        if start == end:
            return

        key = tuple(sorted((start, end)))

        if key in self._edge_keys:
            return

        self._edge_keys.add(key)
        self.edges.append(Edge(start, end))

    # --------------------------------

    def add_face(self, indices):
        """Add a polygon face and its boundary edges."""

        face_indices = list(indices)

        if len(face_indices) < 3:
            return

        self.faces.append(Face(face_indices))

        for index, start in enumerate(face_indices):
            self.add_edge(start, face_indices[(index + 1) % len(face_indices)])

    # --------------------------------

    def add_quad(self, a, b, c, d):
        """Add a quadrilateral face."""

        self.add_face([a, b, c, d])

    # --------------------------------

    def add_triangle(self, a, b, c):
        """Add a triangular face."""

        self.add_face([a, b, c])

    # --------------------------------

    def build(self):
        """Return normalized MeshData from the accumulated topology."""

        return MeshData(self.vertices, self.edges, self.faces)


class PrimitiveGenerator:
    """Reusable 3D primitive generator that returns MeshData only."""

    DEFAULT_SEGMENTS = 24

    # --------------------------------

    @classmethod
    def generate(cls, primitive_type, **parameters):
        """Generate MeshData for a supported primitive type."""

        method = getattr(cls, str(primitive_type).lower(), None)

        if method is None:
            raise ValueError(f"Unsupported primitive type: {primitive_type}")

        return method(**parameters)

    # --------------------------------

    @staticmethod
    def cube(size=100.0):
        """Generate a cube mesh centered at the origin."""

        return PrimitiveGenerator.box(size, size, size)

    # --------------------------------

    @staticmethod
    def box(width=100.0, depth=100.0, height=100.0):
        """Generate an axis-aligned box mesh centered at the origin."""

        hw = max(float(width), 0.0) * 0.5
        hd = max(float(depth), 0.0) * 0.5
        hh = max(float(height), 0.0) * 0.5
        builder = MeshBuilder()
        vertices = [
            builder.add_vertex(Vector3(-hw, -hd, -hh), uv=(0.0, 0.0)),
            builder.add_vertex(Vector3(hw, -hd, -hh), uv=(1.0, 0.0)),
            builder.add_vertex(Vector3(hw, hd, -hh), uv=(1.0, 1.0)),
            builder.add_vertex(Vector3(-hw, hd, -hh), uv=(0.0, 1.0)),
            builder.add_vertex(Vector3(-hw, -hd, hh), uv=(0.0, 0.0)),
            builder.add_vertex(Vector3(hw, -hd, hh), uv=(1.0, 0.0)),
            builder.add_vertex(Vector3(hw, hd, hh), uv=(1.0, 1.0)),
            builder.add_vertex(Vector3(-hw, hd, hh), uv=(0.0, 1.0)),
        ]
        faces = [
            (0, 3, 2, 1),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (1, 2, 6, 5),
            (2, 3, 7, 6),
            (3, 0, 4, 7),
        ]

        for face in faces:
            builder.add_face([vertices[index] for index in face])

        return builder.build()

    # --------------------------------

    @staticmethod
    def plane(width=100.0, depth=100.0):
        """Generate a rectangular plane on the XY ground plane."""

        hw = max(float(width), 0.0) * 0.5
        hd = max(float(depth), 0.0) * 0.5
        builder = MeshBuilder()
        a = builder.add_vertex(Vector3(-hw, -hd, 0.0), uv=(0.0, 0.0))
        b = builder.add_vertex(Vector3(hw, -hd, 0.0), uv=(1.0, 0.0))
        c = builder.add_vertex(Vector3(hw, hd, 0.0), uv=(1.0, 1.0))
        d = builder.add_vertex(Vector3(-hw, hd, 0.0), uv=(0.0, 1.0))
        builder.add_quad(a, b, c, d)

        return builder.build()

    # --------------------------------

    @staticmethod
    def cylinder(radius=50.0, height=100.0, segments=None):
        """Generate a closed cylinder mesh."""

        return PrimitiveGenerator._radial_prism(
            bottom_radius=radius,
            top_radius=radius,
            height=height,
            sides=segments or PrimitiveGenerator.DEFAULT_SEGMENTS,
            cap_top=True,
            cap_bottom=True,
        )

    # --------------------------------

    @staticmethod
    def cone(radius=50.0, height=100.0, segments=None):
        """Generate a closed cone mesh."""

        return PrimitiveGenerator._radial_prism(
            bottom_radius=radius,
            top_radius=0.0,
            height=height,
            sides=segments or PrimitiveGenerator.DEFAULT_SEGMENTS,
            cap_top=False,
            cap_bottom=True,
        )

    # --------------------------------

    @staticmethod
    def sphere(radius=50.0, segments=None, rings=12):
        """Generate a UV sphere mesh."""

        radius = max(float(radius), 0.0)
        segments = PrimitiveGenerator._safe_segments(segments)
        rings = max(int(rings), 4)
        builder = MeshBuilder()
        grid = []

        for ring in range(rings + 1):
            phi = math.pi * ring / rings
            row = []

            for segment in range(segments):
                theta = 2.0 * math.pi * segment / segments
                normal = Vector3(
                    math.sin(phi) * math.cos(theta),
                    math.sin(phi) * math.sin(theta),
                    math.cos(phi),
                )
                row.append(builder.add_vertex(
                    normal * radius,
                    normal,
                    (segment / segments, ring / rings),
                ))

            grid.append(row)

        PrimitiveGenerator._add_wrapped_grid_faces(builder, grid, segments)

        return builder.build()

    # --------------------------------

    @staticmethod
    def torus(major_radius=60.0, minor_radius=15.0, major_segments=None, minor_segments=12):
        """Generate a torus mesh centered at the origin."""

        major_radius = max(float(major_radius), 0.0)
        minor_radius = max(float(minor_radius), 0.0)
        major_segments = PrimitiveGenerator._safe_segments(major_segments)
        minor_segments = max(int(minor_segments), 6)
        builder = MeshBuilder()
        grid = []

        for major in range(major_segments):
            theta = 2.0 * math.pi * major / major_segments
            row = []

            for minor in range(minor_segments):
                phi = 2.0 * math.pi * minor / minor_segments
                radial = Vector3(math.cos(theta), math.sin(theta), 0.0)
                normal = Vector3(
                    math.cos(theta) * math.cos(phi),
                    math.sin(theta) * math.cos(phi),
                    math.sin(phi),
                )
                center = radial * major_radius
                row.append(builder.add_vertex(
                    center + normal * minor_radius,
                    normal,
                    (major / major_segments, minor / minor_segments),
                ))

            grid.append(row)

        for major in range(major_segments):
            next_major = (major + 1) % major_segments

            for minor in range(minor_segments):
                next_minor = (minor + 1) % minor_segments
                builder.add_quad(
                    grid[major][minor],
                    grid[next_major][minor],
                    grid[next_major][next_minor],
                    grid[major][next_minor],
                )

        return builder.build()

    # --------------------------------

    @staticmethod
    def pyramid(width=100.0, depth=100.0, height=100.0):
        """Generate a rectangular pyramid mesh."""

        hw = max(float(width), 0.0) * 0.5
        hd = max(float(depth), 0.0) * 0.5
        hh = max(float(height), 0.0) * 0.5
        builder = MeshBuilder()
        base = [
            builder.add_vertex(Vector3(-hw, -hd, -hh), uv=(0.0, 0.0)),
            builder.add_vertex(Vector3(hw, -hd, -hh), uv=(1.0, 0.0)),
            builder.add_vertex(Vector3(hw, hd, -hh), uv=(1.0, 1.0)),
            builder.add_vertex(Vector3(-hw, hd, -hh), uv=(0.0, 1.0)),
        ]
        apex = builder.add_vertex(Vector3(0.0, 0.0, hh), uv=(0.5, 1.0))
        builder.add_face([base[3], base[2], base[1], base[0]])

        for index, start in enumerate(base):
            builder.add_triangle(start, base[(index + 1) % 4], apex)

        return builder.build()

    # --------------------------------

    @staticmethod
    def prism(radius=50.0, height=100.0, sides=6):
        """Generate a closed regular prism mesh."""

        return PrimitiveGenerator._radial_prism(
            bottom_radius=radius,
            top_radius=radius,
            height=height,
            sides=sides,
            cap_top=True,
            cap_bottom=True,
        )

    # --------------------------------

    @staticmethod
    def capsule(radius=30.0, height=100.0, segments=None, rings=8):
        """Generate a capsule mesh with a cylindrical middle and hemispherical ends."""

        radius = max(float(radius), 0.0)
        height = max(float(height), radius * 2.0)
        cylinder_half = max((height - radius * 2.0) * 0.5, 0.0)
        segments = PrimitiveGenerator._safe_segments(segments)
        rings = max(int(rings), 4)
        builder = MeshBuilder()
        rows = []

        for ring in range(rings + 1):
            phi = math.pi * ring / rings
            local_z = math.cos(phi) * radius
            row_radius = math.sin(phi) * radius
            center_z = cylinder_half if local_z >= 0.0 else -cylinder_half
            row = []

            for segment in range(segments):
                theta = 2.0 * math.pi * segment / segments
                normal = Vector3(
                    math.sin(phi) * math.cos(theta),
                    math.sin(phi) * math.sin(theta),
                    math.cos(phi),
                )
                row.append(builder.add_vertex(
                    Vector3(
                        row_radius * math.cos(theta),
                        row_radius * math.sin(theta),
                        center_z + local_z,
                    ),
                    normal,
                    (segment / segments, ring / rings),
                ))

            rows.append(row)

        PrimitiveGenerator._add_wrapped_grid_faces(builder, rows, segments)

        return builder.build()

    # --------------------------------

    @staticmethod
    def _radial_prism(bottom_radius, top_radius, height, sides, cap_top, cap_bottom):

        bottom_radius = max(float(bottom_radius), 0.0)
        top_radius = max(float(top_radius), 0.0)
        sides = PrimitiveGenerator._safe_segments(sides)
        half = max(float(height), 0.0) * 0.5
        builder = MeshBuilder()
        bottom = PrimitiveGenerator._ring(builder, bottom_radius, -half, sides, 0.0)
        top = PrimitiveGenerator._ring(builder, top_radius, half, sides, 1.0)

        for index in range(sides):
            builder.add_quad(
                bottom[index],
                bottom[(index + 1) % sides],
                top[(index + 1) % sides],
                top[index],
            )

        if cap_bottom and bottom_radius > 0.0:
            center = builder.add_vertex(Vector3(0.0, 0.0, -half), uv=(0.5, 0.5))

            for index in range(sides):
                builder.add_triangle(center, bottom[index], bottom[(index + 1) % sides])

        if cap_top and top_radius > 0.0:
            center = builder.add_vertex(Vector3(0.0, 0.0, half), uv=(0.5, 0.5))

            for index in range(sides):
                builder.add_triangle(center, top[(index + 1) % sides], top[index])

        return builder.build()

    # --------------------------------

    @staticmethod
    def _ring(builder, radius, z, segments, v):

        vertices = []

        for segment in range(segments):
            theta = 2.0 * math.pi * segment / segments
            vertices.append(builder.add_vertex(
                Vector3(radius * math.cos(theta), radius * math.sin(theta), z),
                uv=(segment / segments, v),
            ))

        return vertices

    # --------------------------------

    @staticmethod
    def _add_wrapped_grid_faces(builder, grid, segments):

        for row in range(len(grid) - 1):
            for segment in range(segments):
                next_segment = (segment + 1) % segments
                builder.add_quad(
                    grid[row][segment],
                    grid[row][next_segment],
                    grid[row + 1][next_segment],
                    grid[row + 1][segment],
                )

    # --------------------------------

    @staticmethod
    def _safe_segments(value):

        return max(int(value or PrimitiveGenerator.DEFAULT_SEGMENTS), 3)
