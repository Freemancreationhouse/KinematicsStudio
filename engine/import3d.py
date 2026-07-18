import json
import os
import struct
from dataclasses import dataclass, field
from uuid import uuid4

from engine.geometry import Edge, Face, MeshData, Vector3, Vertex


@dataclass
class ImportSettings:
    """Reusable import settings shared by all 3D reference adapters."""

    units: str = "model"
    scale: float = 1.0
    up_axis: str = "Z"
    forward_axis: str = "Y"
    center_model: bool = False
    merge_meshes: bool = True
    keep_hierarchy: bool = True
    generate_normals: bool = True
    generate_bounds: bool = True
    import_hidden_objects: bool = False
    validate: bool = True
    remember_settings: bool = True

    def to_dict(self):
        """Return JSON-safe settings."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create settings from persisted data."""

        data = data or {}

        return ImportSettings(
            data.get("units", "model"),
            float(data.get("scale", 1.0)),
            data.get("up_axis", "Z"),
            data.get("forward_axis", "Y"),
            bool(data.get("center_model", False)),
            bool(data.get("merge_meshes", True)),
            bool(data.get("keep_hierarchy", True)),
            bool(data.get("generate_normals", True)),
            bool(data.get("generate_bounds", True)),
            bool(data.get("import_hidden_objects", False)),
            bool(data.get("validate", True)),
            bool(data.get("remember_settings", True)),
        )


@dataclass
class ImportStatistics:
    """Import summary statistics."""

    vertices: int = 0
    edges: int = 0
    faces: int = 0
    meshes: int = 0
    warnings: int = 0
    errors: int = 0

    @staticmethod
    def from_meshes(meshes, warning_count=0, error_count=0):
        """Build statistics from imported meshes."""

        return ImportStatistics(
            sum(len(mesh.vertices) for mesh in meshes),
            sum(len(mesh.edges) for mesh in meshes),
            sum(len(mesh.faces) for mesh in meshes),
            len(meshes),
            warning_count,
            error_count,
        )

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create statistics from persisted data."""

        data = data or {}

        return ImportStatistics(
            int(data.get("vertices", 0)),
            int(data.get("edges", 0)),
            int(data.get("faces", 0)),
            int(data.get("meshes", 0)),
            int(data.get("warnings", 0)),
            int(data.get("errors", 0)),
        )


@dataclass
class ImportContext:
    """Context supplied to an import adapter."""

    path: str
    settings: ImportSettings = field(default_factory=ImportSettings)
    reference_id: str = ""


@dataclass
class ImportResult:
    """Common internal result returned by every import adapter."""

    reader_type: str
    path: str
    meshes: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @property
    def ok(self):
        """Return True when no blocking import errors occurred."""

        return not self.errors

    @property
    def statistics(self):
        """Return import statistics."""

        return ImportStatistics.from_meshes(
            self.meshes,
            len(self.warnings),
            len(self.errors),
        )

    @property
    def mesh_data(self):
        """Return the common MeshData representation."""

        if not self.meshes:
            return MeshData()

        if len(self.meshes) == 1:
            return self.meshes[0]

        vertices = []
        edges = []
        faces = []

        for mesh in self.meshes:
            offset = len(vertices)
            vertices.extend(mesh.vertices)
            edges.extend([Edge(edge.start + offset, edge.end + offset) for edge in mesh.edges])
            faces.extend([Face([index + offset for index in face.indices]) for face in mesh.faces])

        return MeshData(vertices, edges, faces)


@dataclass
class ExchangeValidationIssue:
    """One import/export validation issue."""

    category: str
    message: str
    severity: str = "Warning"
    entity_id: str = ""

    def to_dict(self):
        """Return JSON-safe issue data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create an issue from persisted data."""

        data = data or {}

        return ExchangeValidationIssue(
            data.get("category", "Metadata Validation"),
            data.get("message", ""),
            data.get("severity", "Warning"),
            data.get("entity_id", ""),
        )


class ExchangeValidationReport:
    """Persistent exchange validation report."""

    def __init__(self, name="Validation Report", issues=None, summary=None):

        self.name = name
        self.issues = list(issues or [])
        self.summary = dict(summary or {})

    @property
    def warnings(self):
        """Return warning issues."""

        return [issue for issue in self.issues if issue.severity != "Error"]

    @property
    def errors(self):
        """Return error issues."""

        return [issue for issue in self.issues if issue.severity == "Error"]

    @property
    def ok(self):
        """Return True when no errors are present."""

        return not self.errors

    def to_dict(self):
        """Return JSON-safe report data."""

        return {
            "name": self.name,
            "issues": [issue.to_dict() for issue in self.issues],
            "summary": dict(self.summary),
        }

    @staticmethod
    def from_dict(data):
        """Create a report from persisted data."""

        data = data or {}

        return ExchangeValidationReport(
            data.get("name", "Validation Report"),
            [ExchangeValidationIssue.from_dict(item) for item in data.get("issues", [])],
            data.get("summary", {}),
        )


class ExchangeValidationManager:
    """Validation manager for import/export exchange workflows."""

    DEFAULT_SETTINGS = {
        "expected_units": "model",
        "expected_up_axis": "Z",
        "expected_forward_axis": "Y",
        "highlight_issues": True,
    }

    def __init__(self):

        self.settings = dict(self.DEFAULT_SETTINGS)
        self.profiles = {
            "Default": {
                "units": "model",
                "up_axis": "Z",
                "forward_axis": "Y",
                "scale": 1.0,
            }
        }
        self.previous_report = None
        self.last_report = ExchangeValidationReport()

    def validate_import_result(self, result, settings=None):
        """Validate one import result."""

        settings = settings or ImportSettings()
        issues = []

        if result.errors:
            issues.extend(
                ExchangeValidationIssue("Import Warnings", error, "Error")
                for error in result.errors
            )

        issues.extend(
            ExchangeValidationIssue("Import Warnings", warning, "Warning")
            for warning in result.warnings
        )

        if result.statistics.vertices == 0:
            issues.append(ExchangeValidationIssue("Missing Geometry", "No decoded geometry was found."))

        metadata = result.metadata or {}

        if not metadata.get("reader_type"):
            issues.append(ExchangeValidationIssue("Metadata Validation", "Reader metadata is missing."))

        self._validate_settings(settings, issues)

        return self._store_report("Import Validation", issues)

    def validate_workspace(self, workspace, export_format=""):
        """Validate workspace state before export."""

        issues = []
        scene = getattr(workspace, "scene3d", None)
        references = getattr(workspace, "reference_manager", None)

        if scene is not None:
            mesh_entities = [
                entity for entity in scene.entities()
                if hasattr(entity, "mesh_data")
            ]

            if not mesh_entities and export_format.lower() in {"obj", "stl", "step", "stp", "iges", "igs", "sat", "skp", "3dm"}:
                issues.append(ExchangeValidationIssue("Missing Geometry", "No MeshEntity data is available for CAD exchange."))

            for entity in mesh_entities:
                if len(entity.mesh_data.vertices) == 0:
                    issues.append(ExchangeValidationIssue(
                        "Missing Geometry",
                        f"{entity.name} has no vertices.",
                        "Warning",
                        getattr(entity, "id", getattr(entity, "name", "")),
                    ))

        if references is not None:
            for model in references.models:
                if getattr(model, "status", "") == "Missing":
                    issues.append(ExchangeValidationIssue("Missing References", f"{model.name} is missing."))
                if not getattr(model, "reader_type", ""):
                    issues.append(ExchangeValidationIssue("Metadata Validation", f"{model.name} has no reader type."))

        if export_format.lower() in {"skp", "3dm", "fbx", "abc"}:
            issues.append(ExchangeValidationIssue(
                "Unsupported Entities",
                f"{export_format.upper()} export uses the professional exchange foundation manifest in this batch.",
            ))

        return self._store_report("Export Validation", issues)

    def save_profile(self, name, settings):
        """Store an exchange profile."""

        self.profiles[name] = dict(settings)

    def highlight_entities(self, workspace):
        """Return workspace objects referenced by validation issues."""

        ids = {
            issue.entity_id
            for issue in self.last_report.issues
            if issue.entity_id
        }

        if not ids:
            return []

        entities = []
        scene = getattr(workspace, "scene3d", None)

        if scene is not None:
            entities.extend([
                entity for entity in scene.entities()
                if getattr(entity, "id", getattr(entity, "name", "")) in ids
            ])

        return entities

    def to_dict(self):
        """Return JSON-safe validation settings."""

        return {
            "settings": dict(self.settings),
            "profiles": dict(self.profiles),
            "last_report": self.last_report.to_dict(),
        }

    def from_dict(self, data):
        """Restore validation settings."""

        data = data or {}
        self.settings.update(data.get("settings", {}))
        self.profiles = dict(data.get("profiles", self.profiles))
        self.last_report = ExchangeValidationReport.from_dict(data.get("last_report", {}))
        self.previous_report = None

    def _validate_settings(self, settings, issues):

        if settings.units != self.settings.get("expected_units", "model"):
            issues.append(ExchangeValidationIssue("Unit Mismatch", f"Units are {settings.units}."))

        if settings.up_axis != self.settings.get("expected_up_axis", "Z"):
            issues.append(ExchangeValidationIssue("Axis Mismatch", f"Up axis is {settings.up_axis}."))

        if settings.forward_axis != self.settings.get("expected_forward_axis", "Y"):
            issues.append(ExchangeValidationIssue("Axis Mismatch", f"Forward axis is {settings.forward_axis}."))

    def _store_report(self, name, issues):

        summary = {
            "issues": len(issues),
            "warnings": len([issue for issue in issues if issue.severity != "Error"]),
            "errors": len([issue for issue in issues if issue.severity == "Error"]),
        }
        self.previous_report = self.last_report
        self.last_report = ExchangeValidationReport(name, issues, summary)

        return self.last_report


class ImportAdapter:
    """Base class for 3D reference import adapters."""

    name = "Base"
    extensions = ()
    metadata_only = False

    def can_read(self, path):
        """Return True when this adapter can read the path."""

        return _extension(path) in self.extensions

    def read(self, context):
        """Read a reference file into a common ImportResult."""

        raise NotImplementedError

    def _metadata_result(self, context, warning):
        return ImportResult(
            self.name,
            context.path,
            [MeshData()],
            self._file_metadata(context.path),
            [warning],
            [],
        )

    def _file_metadata(self, path):
        return {
            "path": path,
            "file_name": os.path.basename(path),
            "extension": _extension(path),
            "reader_type": self.name,
            "metadata_only": self.metadata_only,
        }


class ObjImportAdapter(ImportAdapter):
    """OBJ reference reader foundation."""

    name = "OBJ"
    extensions = (".obj",)

    def read(self, context):
        """Read a Wavefront OBJ file."""

        vertices = []
        faces = []

        for line in _read_text_lines(context.path):
            parts = line.strip().split()

            if not parts:
                continue

            if parts[0] == "v" and len(parts) >= 4:
                vertices.append(Vertex(_scaled_vector(parts[1:4], context.settings.scale)))
            elif parts[0] == "f" and len(parts) >= 4:
                face = []

                for token in parts[1:]:
                    index = token.split("/")[0]

                    if index:
                        face.append(int(index) - 1)

                if len(face) >= 3:
                    faces.append(Face(face))

        mesh = MeshData(vertices, _edges_from_faces(faces), faces)

        return ImportResult(self.name, context.path, [mesh], self._file_metadata(context.path))


class StlImportAdapter(ImportAdapter):
    """STL reference reader foundation."""

    name = "STL"
    extensions = (".stl",)

    def read(self, context):
        """Read ASCII or binary STL data."""

        with open(context.path, "rb") as handle:
            data = handle.read()

        if data[:5].lower() == b"solid" and b"facet" in data[:512].lower():
            return self._read_ascii(context, data.decode("utf-8", errors="ignore"))

        return self._read_binary(context, data)

    def _read_ascii(self, context, text):
        vertices = []
        faces = []
        current = []

        for line in text.splitlines():
            parts = line.strip().split()

            if len(parts) == 4 and parts[0] == "vertex":
                vertices.append(Vertex(_scaled_vector(parts[1:4], context.settings.scale)))
                current.append(len(vertices) - 1)

            if len(current) == 3:
                faces.append(Face(list(current)))
                current = []

        return ImportResult(
            self.name,
            context.path,
            [MeshData(vertices, _edges_from_faces(faces), faces)],
            self._file_metadata(context.path),
        )

    def _read_binary(self, context, data):
        vertices = []
        faces = []

        if len(data) < 84:
            return ImportResult(self.name, context.path, [], self._file_metadata(context.path), [], ["Invalid STL"])

        triangle_count = struct.unpack("<I", data[80:84])[0]
        offset = 84

        for _ in range(triangle_count):
            if offset + 50 > len(data):
                break

            offset += 12
            face = []

            for _ in range(3):
                x, y, z = struct.unpack("<fff", data[offset:offset + 12])
                vertices.append(Vertex(Vector3(x, y, z) * context.settings.scale))
                face.append(len(vertices) - 1)
                offset += 12

            faces.append(Face(face))
            offset += 2

        return ImportResult(
            self.name,
            context.path,
            [MeshData(vertices, _edges_from_faces(faces), faces)],
            self._file_metadata(context.path),
        )


class PlyImportAdapter(ImportAdapter):
    """ASCII PLY reference reader foundation."""

    name = "PLY"
    extensions = (".ply",)

    def read(self, context):
        """Read an ASCII PLY file."""

        lines = _read_text_lines(context.path)

        if not lines or lines[0].strip() != "ply":
            return ImportResult(self.name, context.path, [], self._file_metadata(context.path), [], ["Invalid PLY"])

        vertex_count = 0
        face_count = 0
        header_end = 0

        for index, line in enumerate(lines):
            parts = line.strip().split()

            if len(parts) == 3 and parts[:2] == ["element", "vertex"]:
                vertex_count = int(parts[2])
            elif len(parts) == 3 and parts[:2] == ["element", "face"]:
                face_count = int(parts[2])
            elif parts == ["end_header"]:
                header_end = index + 1
                break

        vertices = [
            Vertex(_scaled_vector(lines[header_end + index].split()[:3], context.settings.scale))
            for index in range(vertex_count)
        ]
        faces = []
        start = header_end + vertex_count

        for index in range(face_count):
            parts = lines[start + index].split()

            if not parts:
                continue

            count = int(parts[0])
            face = [int(value) for value in parts[1:1 + count]]

            if len(face) >= 3:
                faces.append(Face(face))

        return ImportResult(
            self.name,
            context.path,
            [MeshData(vertices, _edges_from_faces(faces), faces)],
            self._file_metadata(context.path),
        )


class OffImportAdapter(ImportAdapter):
    """OFF reference reader foundation."""

    name = "OFF"
    extensions = (".off",)

    def read(self, context):
        """Read an OFF file."""

        lines = [line.strip() for line in _read_text_lines(context.path) if line.strip() and not line.strip().startswith("#")]

        if not lines or lines[0] != "OFF":
            return ImportResult(self.name, context.path, [], self._file_metadata(context.path), [], ["Invalid OFF"])

        counts = lines[1].split()
        vertex_count = int(counts[0])
        face_count = int(counts[1])
        vertices = [
            Vertex(_scaled_vector(lines[2 + index].split()[:3], context.settings.scale))
            for index in range(vertex_count)
        ]
        faces = []
        start = 2 + vertex_count

        for index in range(face_count):
            parts = lines[start + index].split()
            count = int(parts[0])
            face = [int(value) for value in parts[1:1 + count]]

            if len(face) >= 3:
                faces.append(Face(face))

        return ImportResult(
            self.name,
            context.path,
            [MeshData(vertices, _edges_from_faces(faces), faces)],
            self._file_metadata(context.path),
        )


class GltfImportAdapter(ImportAdapter):
    """GLTF reference reader foundation."""

    name = "GLTF"
    extensions = (".gltf",)

    def read(self, context):
        """Read GLTF metadata and preserve common result structure."""

        with open(context.path, "r", encoding="utf-8", errors="ignore") as handle:
            data = json.load(handle)

        metadata = self._file_metadata(context.path)
        metadata["asset"] = data.get("asset", {})
        metadata["nodes"] = len(data.get("nodes", []))
        metadata["meshes"] = len(data.get("meshes", []))

        return ImportResult(
            self.name,
            context.path,
            [MeshData()],
            metadata,
            ["GLTF geometry decoding is foundation-only in this batch."],
        )


class GlbImportAdapter(ImportAdapter):
    """GLB reference reader foundation."""

    name = "GLB"
    extensions = (".glb",)

    def read(self, context):
        """Read GLB header metadata and preserve common result structure."""

        with open(context.path, "rb") as handle:
            header = handle.read(12)

        if len(header) != 12 or header[:4] != b"glTF":
            return ImportResult(self.name, context.path, [], self._file_metadata(context.path), [], ["Invalid GLB"])

        version, length = struct.unpack("<II", header[4:12])
        metadata = self._file_metadata(context.path)
        metadata["version"] = version
        metadata["length"] = length

        return ImportResult(
            self.name,
            context.path,
            [MeshData()],
            metadata,
            ["GLB geometry decoding is foundation-only in this batch."],
        )


class MetadataOnlyImportAdapter(ImportAdapter):
    """Metadata-only placeholder for future professional readers."""

    metadata_only = True

    def __init__(self, name, extensions):

        self.name = name
        self.extensions = tuple(extensions)

    def read(self, context):
        """Return metadata-only result for future reader implementation."""

        return self._metadata_result(
            context,
            f"{self.name} geometry decoding is metadata-only in this batch.",
        )


class ProfessionalCADImportAdapter(MetadataOnlyImportAdapter):
    """Professional CAD exchange adapter foundation using the common import result."""

    def __init__(self, name, extensions, compatibility=None, fallback_formats=None):

        super().__init__(name, extensions)
        self.compatibility = compatibility or name
        self.fallback_formats = list(fallback_formats or [])

    def read(self, context):
        """Return metadata-only CAD exchange data through the shared pipeline."""

        result = super().read(context)
        result.metadata["compatibility"] = self.compatibility
        result.metadata["fallback_formats"] = list(self.fallback_formats)
        result.metadata["adapter_foundation"] = True

        return result


class ImportRegistry:
    """Registry for built-in and future plugin import adapters."""

    def __init__(self):

        self.adapters = []

    def register(self, adapter):
        """Register an adapter."""

        if adapter not in self.adapters:
            self.adapters.append(adapter)

        return adapter

    def adapter_for_path(self, path):
        """Return the adapter that can read the path."""

        for adapter in self.adapters:
            if adapter.can_read(path):
                return adapter

        return None

    def to_dict(self):
        """Return registered adapter names."""

        return {"adapters": [adapter.name for adapter in self.adapters]}


class ImportManager:
    """Reusable 3D import manager for external reference files."""

    def __init__(self, registry=None):

        self.registry = registry or default_import_registry()
        self.last_result = None
        self.progress = 0.0
        self.adapter_settings = {}
        self.validation_manager = ExchangeValidationManager()

    def read(self, path, settings=None):
        """Read a path through the registered adapter pipeline."""

        adapter = self.registry.adapter_for_path(path)
        settings = settings or ImportSettings()

        if adapter is None:
            result = ImportResult("Unknown", path, [], {"path": path}, [], [f"No adapter for {_extension(path)}"])
        else:
            result = adapter.read(ImportContext(path, settings, str(uuid4())))

        if settings.validate:
            self._validate(result)
            self.validation_manager.validate_import_result(result, settings)

        self.last_result = result
        self.progress = 1.0

        return result

    def create_reference(self, workspace, path, name=None, settings=None, transform=None):
        """Create an undoable imported reference in a workspace."""

        from engine.commands import ImportReferenceCommand

        command = ImportReferenceCommand(workspace, self, path, name, settings, transform)
        workspace.command_manager.execute(command)

        return command.result

    def reload_reference(self, workspace, model, settings=None):
        """Reload reference import data through the command system."""

        from engine.commands import ReloadImportedReferenceCommand

        command = ReloadImportedReferenceCommand(workspace, self, model, settings)
        workspace.command_manager.execute(command)

        return command.result

    def replace_reference(self, workspace, model, path, settings=None):
        """Replace reference import data through the command system."""

        from engine.commands import ReplaceReferenceCommand

        command = ReplaceReferenceCommand(workspace, self, model, path, settings)
        workspace.command_manager.execute(command)

        return command.result

    def _validate(self, result):
        if result.meshes and result.statistics.vertices == 0:
            result.warnings.append("No decoded vertices in import result.")

    def to_dict(self):
        """Return persisted import manager settings."""

        return {
            "adapter_settings": dict(self.adapter_settings),
            "validation": self.validation_manager.to_dict(),
            "registry": self.registry.to_dict(),
        }

    def from_dict(self, data):
        """Restore persisted import manager settings."""

        data = data or {}
        self.adapter_settings = dict(data.get("adapter_settings", {}))
        self.validation_manager.from_dict(data.get("validation", {}))


def default_import_registry():
    """Create the default import adapter registry."""

    registry = ImportRegistry()
    registry.register(ObjImportAdapter())
    registry.register(StlImportAdapter())
    registry.register(PlyImportAdapter())
    registry.register(OffImportAdapter())
    registry.register(GltfImportAdapter())
    registry.register(GlbImportAdapter())
    registry.register(ProfessionalCADImportAdapter("SKP", (".skp",), "SketchUp", ["STEP", "OBJ"]))
    registry.register(ProfessionalCADImportAdapter("3DM", (".3dm",), "Rhino", ["STEP", "IGES", "OBJ"]))
    registry.register(ProfessionalCADImportAdapter("SAT", (".sat",), "Fusion 360 / ACIS SAT", ["STEP", "IGES"]))
    registry.register(ProfessionalCADImportAdapter("FBX", (".fbx",), "FBX", ["OBJ", "GLTF"]))
    registry.register(ProfessionalCADImportAdapter("Alembic", (".abc",), "Alembic", ["OBJ", "GLTF"]))
    registry.register(MetadataOnlyImportAdapter("3DS", (".3ds",)))
    registry.register(ProfessionalCADImportAdapter("STEP", (".step", ".stp"), "Fusion 360 / STEP", ["OBJ", "STL"]))
    registry.register(ProfessionalCADImportAdapter("IGES", (".iges", ".igs"), "Fusion 360 / IGES", ["OBJ", "STL"]))

    return registry


def _extension(path):
    return os.path.splitext(str(path or ""))[1].lower()


def _read_text_lines(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        return handle.readlines()


def _scaled_vector(values, scale):
    return Vector3(float(values[0]), float(values[1]), float(values[2])) * scale


def _edges_from_faces(faces):
    seen = set()
    edges = []

    for face in faces:
        indices = list(face.indices)

        for index, start in enumerate(indices):
            end = indices[(index + 1) % len(indices)]
            key = tuple(sorted((start, end)))

            if key not in seen:
                seen.add(key)
                edges.append(Edge(start, end))

    return edges
