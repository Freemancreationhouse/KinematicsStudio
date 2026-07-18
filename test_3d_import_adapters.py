import json
import os
import struct
import tempfile

from engine.import3d import ImportManager


def write(path, text, mode="w"):
    with open(path, mode, encoding=None if "b" in mode else "utf-8") as handle:
        handle.write(text)


with tempfile.TemporaryDirectory() as folder:
    manager = ImportManager()

    obj = os.path.join(folder, "triangle.obj")
    write(obj, "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
    result = manager.read(obj)
    assert result.reader_type == "OBJ"
    assert result.statistics.vertices == 3
    assert result.statistics.faces == 1

    stl = os.path.join(folder, "triangle.stl")
    write(
        stl,
        "solid s\nfacet normal 0 0 1\nouter loop\n"
        "vertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\n"
        "endloop\nendfacet\nendsolid s\n",
    )
    result = manager.read(stl)
    assert result.reader_type == "STL"
    assert result.statistics.faces == 1

    ply = os.path.join(folder, "triangle.ply")
    write(
        ply,
        "ply\nformat ascii 1.0\nelement vertex 3\n"
        "property float x\nproperty float y\nproperty float z\n"
        "element face 1\nproperty list uchar int vertex_indices\nend_header\n"
        "0 0 0\n1 0 0\n0 1 0\n3 0 1 2\n",
    )
    result = manager.read(ply)
    assert result.reader_type == "PLY"
    assert result.statistics.vertices == 3

    off = os.path.join(folder, "triangle.off")
    write(off, "OFF\n3 1 0\n0 0 0\n1 0 0\n0 1 0\n3 0 1 2\n")
    result = manager.read(off)
    assert result.reader_type == "OFF"
    assert result.statistics.faces == 1

    gltf = os.path.join(folder, "scene.gltf")
    write(gltf, json.dumps({"asset": {"version": "2.0"}, "nodes": [{}], "meshes": [{}]}))
    result = manager.read(gltf)
    assert result.reader_type == "GLTF"
    assert result.metadata["meshes"] == 1

    glb = os.path.join(folder, "scene.glb")
    with open(glb, "wb") as handle:
        handle.write(b"glTF" + struct.pack("<II", 2, 12))
    result = manager.read(glb)
    assert result.reader_type == "GLB"
    assert result.metadata["version"] == 2

    fbx = os.path.join(folder, "scene.fbx")
    write(fbx, "")
    result = manager.read(fbx)
    assert result.reader_type == "FBX"
    assert result.metadata["metadata_only"] is True

print("3d-import-adapters-ok")
