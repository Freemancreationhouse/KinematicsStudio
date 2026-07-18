from engine.geometry import MeshBuilder, PrimitiveGenerator, Vector3


primitive_cases = {
    "cube": {"size": 25.0},
    "box": {"width": 30.0, "depth": 20.0, "height": 10.0},
    "plane": {"width": 30.0, "depth": 20.0},
    "cylinder": {"radius": 10.0, "height": 30.0, "segments": 12},
    "cone": {"radius": 10.0, "height": 30.0, "segments": 12},
    "sphere": {"radius": 10.0, "segments": 12, "rings": 8},
    "torus": {
        "major_radius": 20.0,
        "minor_radius": 5.0,
        "major_segments": 12,
        "minor_segments": 8,
    },
    "pyramid": {"width": 20.0, "depth": 20.0, "height": 30.0},
    "prism": {"radius": 10.0, "height": 30.0, "sides": 6},
    "capsule": {"radius": 8.0, "height": 40.0, "segments": 12, "rings": 8},
}

for primitive_type, parameters in primitive_cases.items():
    mesh = PrimitiveGenerator.generate(primitive_type, **parameters)

    assert mesh.vertices, primitive_type
    assert mesh.edges, primitive_type
    assert mesh.faces, primitive_type
    assert mesh.triangle_indices, primitive_type
    assert mesh.bounding_box3d.valid, primitive_type
    assert mesh.bounding_sphere.radius >= 0.0, primitive_type
    assert all(vertex.normal.length() > 0.0 for vertex in mesh.vertices), primitive_type
    assert all(len(vertex.uv) == 2 for vertex in mesh.vertices), primitive_type

builder = MeshBuilder()
a = builder.add_vertex(Vector3(0.0, 0.0, 0.0), uv=(0.0, 0.0))
b = builder.add_vertex(Vector3(1.0, 0.0, 0.0), uv=(1.0, 0.0))
c = builder.add_vertex(Vector3(1.0, 1.0, 0.0), uv=(1.0, 1.0))
builder.add_triangle(a, b, c)
custom = builder.build()
assert len(custom.vertices) == 3
assert len(custom.edges) == 3
assert len(custom.faces) == 1

print("3d-primitive-generator-ok")
