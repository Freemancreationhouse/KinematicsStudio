import json

from .base import Exporter


class CADExchangeExporter(Exporter):
    """Professional CAD exchange adapter foundation using ExportManager context."""

    extension = ""
    format_name = "CAD Exchange"

    def __init__(self, extension, format_name, compatibility="", fallback_format="STEP"):

        self.extension = extension.lower().lstrip(".")
        self.format_name = format_name
        self.compatibility = compatibility or format_name
        self.fallback_format = fallback_format

    def serialize(self, context):
        """Return a JSON exchange manifest from the canonical workspace context."""

        return json.dumps(self._manifest(context), indent=2) + "\n"

    def _manifest(self, context):

        return {
            "format": self.format_name,
            "extension": self.extension,
            "compatibility": self.compatibility,
            "fallback_format": self.fallback_format,
            "adapter_foundation": True,
            "workspace": getattr(context.workspace, "name", "Workspace"),
            "entities": [
                self._entity_record(item)
                for item in context.entities
            ],
            "scene3d": self._scene_records(context.workspace),
            "references": self._reference_records(context.workspace),
            "layers": [
                {
                    "name": getattr(layer, "name", ""),
                    "visible": getattr(layer, "visible", True),
                    "locked": getattr(layer, "locked", False),
                    "color": getattr(layer, "color", ""),
                }
                for layer in context.layers
            ],
        }

    def _entity_record(self, item):

        entity = item.entity

        return {
            "type": entity.__class__.__name__,
            "name": getattr(entity, "name", getattr(entity, "type_name", "")),
            "layer": getattr(item.layer, "name", None),
            "block_path": list(item.block_path),
        }

    def _scene_records(self, workspace):

        scene = getattr(workspace, "scene3d", None)

        if scene is None:
            return []

        return [
            {
                "type": entity.__class__.__name__,
                "name": getattr(entity, "name", getattr(entity, "type_name", "")),
                "display_mode": getattr(entity, "display_mode", ""),
                "vertices": len(getattr(getattr(entity, "mesh_data", None), "vertices", [])),
                "faces": len(getattr(getattr(entity, "mesh_data", None), "faces", [])),
            }
            for entity in scene.entities()
        ]

    def _reference_records(self, workspace):

        manager = getattr(workspace, "reference_manager", None)

        if manager is None:
            return []

        return [
            {
                "name": getattr(model, "name", ""),
                "path": getattr(model, "path", ""),
                "reader_type": getattr(model, "reader_type", ""),
                "vertices": getattr(getattr(model, "import_statistics", None), "vertices", 0),
                "faces": getattr(getattr(model, "import_statistics", None), "faces", 0),
            }
            for model in getattr(manager, "models", [])
        ]


class OBJExchangeExporter(CADExchangeExporter):
    """Wavefront OBJ exporter foundation for 3D mesh exchange."""

    def __init__(self):

        super().__init__("obj", "OBJ", "Fusion 360 / Wavefront OBJ", "OBJ")

    def serialize(self, context):
        """Return OBJ geometry from workspace MeshEntity data."""

        lines = [
            "# Kinematics Studio OBJ exchange",
            f"# workspace: {getattr(context.workspace, 'name', 'Workspace')}",
        ]
        offset = 1

        for entity in self._mesh_entities(context.workspace):
            lines.append(f"o {getattr(entity, 'name', 'MeshEntity')}")

            for vertex in entity.mesh_data.vertices:
                point = vertex.position
                lines.append(f"v {point.x:.6f} {point.y:.6f} {point.z:.6f}")

            for face in entity.mesh_data.faces:
                indices = [str(index + offset) for index in face.indices]
                if len(indices) >= 3:
                    lines.append("f " + " ".join(indices))

            offset += len(entity.mesh_data.vertices)

        return "\n".join(lines) + "\n"

    def _mesh_entities(self, workspace):

        scene = getattr(workspace, "scene3d", None)

        if scene is None:
            return []

        return [
            entity for entity in scene.entities()
            if hasattr(entity, "mesh_data")
        ]


class STLExchangeExporter(CADExchangeExporter):
    """ASCII STL exporter foundation for 3D mesh exchange."""

    def __init__(self):

        super().__init__("stl", "STL", "Fusion 360 / STL", "STL")

    def serialize(self, context):
        """Return ASCII STL geometry from workspace MeshEntity data."""

        lines = ["solid KinematicsStudio"]

        for entity in self._mesh_entities(context.workspace):
            for triangle in entity.triangles():
                lines.extend(self._facet(triangle))

        lines.append("endsolid KinematicsStudio")

        return "\n".join(lines) + "\n"

    def _mesh_entities(self, workspace):

        scene = getattr(workspace, "scene3d", None)

        if scene is None:
            return []

        return [
            entity for entity in scene.entities()
            if hasattr(entity, "triangles")
        ]

    def _facet(self, triangle):

        a, b, c = triangle

        return [
            "  facet normal 0 0 1",
            "    outer loop",
            f"      vertex {a.x:.6f} {a.y:.6f} {a.z:.6f}",
            f"      vertex {b.x:.6f} {b.y:.6f} {b.z:.6f}",
            f"      vertex {c.x:.6f} {c.y:.6f} {c.z:.6f}",
            "    endloop",
            "  endfacet",
        ]


def professional_cad_exporters():
    """Return built-in professional CAD exchange exporters."""

    return [
        CADExchangeExporter("skp", "SKP", "SketchUp", "STEP"),
        CADExchangeExporter("3dm", "3DM", "Rhino", "STEP"),
        CADExchangeExporter("step", "STEP", "Fusion 360 / STEP", "STEP"),
        CADExchangeExporter("stp", "STEP", "Fusion 360 / STEP", "STEP"),
        CADExchangeExporter("iges", "IGES", "Fusion 360 / IGES", "IGES"),
        CADExchangeExporter("igs", "IGES", "Fusion 360 / IGES", "IGES"),
        CADExchangeExporter("sat", "SAT", "Fusion 360 / ACIS SAT", "STEP"),
        CADExchangeExporter("fbx", "FBX", "FBX", "OBJ"),
        CADExchangeExporter("abc", "Alembic", "Alembic", "OBJ"),
        OBJExchangeExporter(),
        STLExchangeExporter(),
    ]
