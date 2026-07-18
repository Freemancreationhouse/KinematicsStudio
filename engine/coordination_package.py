from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from engine.geometry import BoundingBox3D, Vector3


@dataclass
class PackageMetadata:
    """Delivery package descriptive metadata."""

    author: str = ""
    recipient: str = ""
    description: str = ""
    version: str = "1.1"
    status: str = "Draft"

    def to_dict(self):
        """Return JSON-safe metadata."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create metadata from persisted data."""

        data = data or {}

        return PackageMetadata(
            data.get("author", ""),
            data.get("recipient", ""),
            data.get("description", ""),
            data.get("version", "1.1"),
            data.get("status", "Draft"),
        )


@dataclass
class PackageStatistics:
    """Summary counts for one delivery package."""

    references: int = 0
    bcf_topics: int = 0
    clashes: int = 0
    revisions: int = 0
    compare_sessions: int = 0
    reviews: int = 0
    issues: int = 0
    files: int = 0
    validation_warnings: int = 0
    validation_errors: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create statistics from persisted data."""

        data = data or {}

        return PackageStatistics(
            int(data.get("references", 0)),
            int(data.get("bcf_topics", 0)),
            int(data.get("clashes", 0)),
            int(data.get("revisions", 0)),
            int(data.get("compare_sessions", 0)),
            int(data.get("reviews", 0)),
            int(data.get("issues", 0)),
            int(data.get("files", 0)),
            int(data.get("validation_warnings", 0)),
            int(data.get("validation_errors", 0)),
        )


class PackageManifest:
    """Serializable manifest for package contents."""

    def __init__(self):

        self.references = []
        self.bcf_topics = []
        self.clash_reports = []
        self.revisions = []
        self.compare_sessions = []
        self.reviews = []
        self.issues = []
        self.metadata = {}
        self.summary = {}
        self.files = []

    def to_dict(self):
        """Return JSON-safe manifest data."""

        return {
            "references": list(self.references),
            "bcf_topics": list(self.bcf_topics),
            "clash_reports": list(self.clash_reports),
            "revisions": list(self.revisions),
            "compare_sessions": list(self.compare_sessions),
            "reviews": list(self.reviews),
            "issues": list(self.issues),
            "metadata": dict(self.metadata),
            "summary": dict(self.summary),
            "files": list(self.files),
        }

    @staticmethod
    def from_dict(data):
        """Create a manifest from persisted data."""

        data = data or {}
        manifest = PackageManifest()
        manifest.references = list(data.get("references", []))
        manifest.bcf_topics = list(data.get("bcf_topics", []))
        manifest.clash_reports = list(data.get("clash_reports", []))
        manifest.revisions = list(data.get("revisions", []))
        manifest.compare_sessions = list(data.get("compare_sessions", []))
        manifest.reviews = list(data.get("reviews", []))
        manifest.issues = list(data.get("issues", []))
        manifest.metadata = dict(data.get("metadata", {}))
        manifest.summary = dict(data.get("summary", {}))
        manifest.files = list(data.get("files", []))

        return manifest


class PackageValidation:
    """Validation report for delivery package readiness."""

    def __init__(self, valid=True, warnings=None, errors=None, checks=None):

        self.valid = bool(valid)
        self.warnings = list(warnings or [])
        self.errors = list(errors or [])
        self.checks = dict(checks or {})
        self.created_at = _timestamp()

    @property
    def status(self):
        """Return validation status text."""

        return "Valid" if self.valid and not self.errors else "Invalid"

    def to_dict(self):
        """Return JSON-safe validation data."""

        return {
            "valid": self.valid,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "checks": dict(self.checks),
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data):
        """Create validation data from persisted data."""

        data = data or {}
        validation = PackageValidation(
            data.get("valid", True),
            data.get("warnings", []),
            data.get("errors", []),
            data.get("checks", {}),
        )
        validation.created_at = data.get("created_at", validation.created_at)

        return validation


class CoordinationPackage:
    """Selectable coordination delivery package marker."""

    type_name = "CoordinationPackage"
    is_3d = True
    is_coordination_package = True

    def __init__(self, name="Coordination Package", metadata=None, manifest=None, location=None):

        self.id = str(uuid4())
        self.name = name
        self.metadata = metadata or PackageMetadata()
        self.manifest = manifest or PackageManifest()
        self.statistics = PackageStatistics()
        self.validation = PackageValidation()
        self.archive_id = ""
        self.viewpoints = []
        self.review_overlays = []
        self.preferences = {}
        self.visible = True
        self.locked = False
        self.selected = False
        self.hovered = False
        self.layer_name = None
        self.created_at = _timestamp()
        self.updated_at = self.created_at
        self.location = location or Vector3()

    @property
    def display_color(self):
        """Return package marker color."""

        return "#8bc34a" if self.validation.valid else "#ff7043"

    @property
    def bounding_box3d(self):
        """Return compact package marker bounds."""

        box = BoundingBox3D()
        pad = 11.0
        box.add(self.location - Vector3(pad, pad, pad))
        box.add(self.location + Vector3(pad, pad, pad))

        return box

    def points(self):
        """Return representative marker points."""

        return [self.location]

    def segments(self):
        """Return package cube marker segments."""

        pad = 11.0
        a = self.location + Vector3(-pad, -pad, 0.0)
        b = self.location + Vector3(pad, -pad, 0.0)
        c = self.location + Vector3(pad, pad, 0.0)
        d = self.location + Vector3(-pad, pad, 0.0)

        return [(a, b), (b, c), (c, d), (d, a), (a, c), (b, d)]

    def refresh_statistics(self):
        """Refresh statistics from manifest and validation."""

        self.statistics = PackageStatistics(
            len(self.manifest.references),
            len(self.manifest.bcf_topics),
            len(self.manifest.clash_reports),
            len(self.manifest.revisions),
            len(self.manifest.compare_sessions),
            len(self.manifest.reviews),
            len(self.manifest.issues),
            len(self.manifest.files),
            len(self.validation.warnings),
            len(self.validation.errors),
        )
        self.updated_at = _timestamp()

    def to_dict(self):
        """Return JSON-safe package data."""

        return {
            "id": self.id,
            "name": self.name,
            "metadata": self.metadata.to_dict(),
            "manifest": self.manifest.to_dict(),
            "statistics": self.statistics.to_dict(),
            "validation": self.validation.to_dict(),
            "archive_id": self.archive_id,
            "viewpoints": list(self.viewpoints),
            "review_overlays": list(self.review_overlays),
            "preferences": dict(self.preferences),
            "visible": self.visible,
            "locked": self.locked,
            "selected": self.selected,
            "layer_name": self.layer_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "location": _vector_to_data(self.location),
        }

    @staticmethod
    def from_dict(data):
        """Create a package from persisted data."""

        data = data or {}
        package = CoordinationPackage(
            data.get("name", "Coordination Package"),
            PackageMetadata.from_dict(data.get("metadata", {})),
            PackageManifest.from_dict(data.get("manifest", {})),
            _vector_from_data(data.get("location")),
        )
        package.id = data.get("id", package.id)
        package.statistics = PackageStatistics.from_dict(data.get("statistics", {}))
        package.validation = PackageValidation.from_dict(data.get("validation", {}))
        package.archive_id = data.get("archive_id", "")
        package.viewpoints = list(data.get("viewpoints", []))
        package.review_overlays = list(data.get("review_overlays", []))
        package.preferences = dict(data.get("preferences", {}))
        package.visible = bool(data.get("visible", True))
        package.locked = bool(data.get("locked", False))
        package.selected = bool(data.get("selected", False))
        package.layer_name = data.get("layer_name")
        package.created_at = data.get("created_at", package.created_at)
        package.updated_at = data.get("updated_at", package.updated_at)

        return package


class ArchiveManager:
    """Validates and searches coordination package archive metadata."""

    def __init__(self):

        self.archives = []
        self.validation_settings = {
            "require_references": False,
            "require_bcf": False,
            "version": "1.1",
        }
        self.preferences = {}
        self.last_summary = {}

    def create_archive(self, package):
        """Create archive metadata for a package."""

        archive = {
            "id": str(uuid4()),
            "package_id": package.id,
            "package_name": package.name,
            "version": package.metadata.version,
            "created_at": _timestamp(),
            "summary": dict(package.manifest.summary),
            "validation": package.validation.to_dict(),
        }
        self.archives.append(archive)
        package.archive_id = archive["id"]
        self.last_summary = dict(archive["summary"])

        return archive

    def validate_package(self, package, workspace):
        """Run dependency, reference, integrity and version checks."""

        warnings = []
        errors = []
        checks = {
            "dependency_validation": True,
            "missing_reference_detection": True,
            "package_integrity": True,
            "package_version": True,
        }

        if self.validation_settings.get("require_references") and not package.manifest.references:
            warnings.append("Package has no external references.")

        missing = _missing_references(workspace)

        if missing:
            checks["missing_reference_detection"] = False
            errors.extend([f"Missing reference: {item}" for item in missing])

        if not package.manifest.summary:
            checks["package_integrity"] = False
            errors.append("Package summary is empty.")

        expected_version = self.validation_settings.get("version", "1.1")

        if package.metadata.version != expected_version:
            checks["package_version"] = False
            warnings.append(f"Package version {package.metadata.version} differs from expected {expected_version}.")

        validation = PackageValidation(not errors, warnings, errors, checks)
        package.validation = validation
        package.refresh_statistics()

        return validation

    def search(self, query=""):
        """Search archive metadata."""

        query = (query or "").lower().strip()

        if not query:
            return list(self.archives)

        return [
            archive for archive in self.archives
            if query in archive.get("package_name", "").lower() or query in archive.get("version", "").lower()
        ]

    def summary(self):
        """Return archive summary."""

        return {
            "archives": len(self.archives),
            "valid": len([item for item in self.archives if item.get("validation", {}).get("valid", True)]),
            "invalid": len([item for item in self.archives if not item.get("validation", {}).get("valid", True)]),
        }

    def to_dict(self):
        """Return JSON-safe archive data."""

        return {
            "archives": list(self.archives),
            "validation_settings": dict(self.validation_settings),
            "preferences": dict(self.preferences),
            "last_summary": dict(self.last_summary),
        }

    def from_dict(self, data):
        """Restore archive data."""

        data = data or {}
        self.archives = list(data.get("archives", []))
        self.validation_settings = dict(data.get("validation_settings", self.validation_settings))
        self.preferences = dict(data.get("preferences", {}))
        self.last_summary = dict(data.get("last_summary", {}))


class CoordinationPackageManager:
    """Workspace-owned coordination package and delivery manager."""

    def __init__(self):

        self.packages = []
        self.active_package_id = None
        self.archive_manager = ArchiveManager()
        self.preferences = {}
        self.visible = True

    @property
    def active_package(self):
        """Return the active package."""

        if not self.packages:
            return None

        return self.get_package(self.active_package_id) or self.packages[-1]

    def create_delivery_package(self, name, workspace, metadata=None):
        """Create a delivery package from current coordination state."""

        package = CoordinationPackage(
            name,
            metadata or PackageMetadata(),
            self.build_manifest(workspace),
            _package_location(workspace),
        )
        package.viewpoints = self._package_viewpoints(workspace)
        package.review_overlays = self._package_review_overlays(workspace)
        package.validation = self.archive_manager.validate_package(package, workspace)
        package.refresh_statistics()
        self.add_package(package)
        self.archive_manager.create_archive(package)

        return package

    def build_manifest(self, workspace):
        """Build a package manifest by referencing existing managers."""

        manifest = PackageManifest()
        manifest.references = _reference_items(workspace)
        manifest.bcf_topics = _bcf_items(workspace)
        manifest.clash_reports = _clash_items(workspace)
        manifest.revisions = _revision_items(workspace)
        manifest.compare_sessions = _compare_session_items(workspace)
        manifest.reviews = _review_items(workspace)
        manifest.issues = _issue_items(workspace)
        manifest.metadata = {
            "workspace": getattr(workspace, "name", "Workspace"),
            "created_at": _timestamp(),
            "export_framework": "ExportManager",
            "import_framework": "ImportManager",
        }
        manifest.summary = {
            "references": len(manifest.references),
            "bcf_topics": len(manifest.bcf_topics),
            "clashes": len(manifest.clash_reports),
            "revisions": len(manifest.revisions),
            "compare_sessions": len(manifest.compare_sessions),
            "reviews": len(manifest.reviews),
            "issues": len(manifest.issues),
        }
        manifest.files = _package_files(workspace)

        return manifest

    def add_package(self, package):
        """Store a package."""

        if package not in self.packages:
            self.packages.append(package)

        self.active_package_id = package.id

        return package

    def remove_package(self, package):
        """Remove a package."""

        target = self.get_package(package)

        if target is None:
            return False

        self.packages.remove(target)
        if self.active_package_id == target.id:
            self.active_package_id = self.packages[-1].id if self.packages else None

        return True

    def validate_package(self, package, workspace):
        """Validate one package."""

        target = self.get_package(package)

        if target is None:
            return None

        return self.archive_manager.validate_package(target, workspace)

    def archive_summary(self):
        """Return archive summary."""

        return self.archive_manager.summary()

    def search_archives(self, query=""):
        """Search archive metadata."""

        return self.archive_manager.search(query)

    def visible_packages(self):
        """Return visible packages."""

        if not self.visible:
            return []

        return [package for package in self.packages if package.visible]

    def get_package(self, package):
        """Return a package by object, id or name."""

        if isinstance(package, CoordinationPackage):
            return package if package in self.packages else None

        for item in self.packages:
            if item.id == package or item.name == package:
                return item

        return None

    def _package_viewpoints(self, workspace):

        revisions = getattr(getattr(workspace, "revision_manager", None), "revisions", [])

        return [
            {"revision_id": revision.id, "name": revision.name, "viewpoint": dict(revision.viewpoint)}
            for revision in revisions
            if getattr(revision, "viewpoint", None)
        ]

    def _package_review_overlays(self, workspace):

        return [
            {"id": getattr(item, "id", ""), "status": getattr(item, "status", ""), "priority": getattr(item, "priority", "")}
            for item in getattr(getattr(workspace, "review_manager", None), "items", [])
        ]

    def to_dict(self):
        """Return JSON-safe package manager data."""

        return {
            "visible": self.visible,
            "active_package_id": self.active_package_id,
            "preferences": dict(self.preferences),
            "packages": [package.to_dict() for package in self.packages],
            "archive_manager": self.archive_manager.to_dict(),
        }

    def from_dict(self, data):
        """Restore package manager data."""

        data = data or {}
        self.visible = bool(data.get("visible", True))
        self.active_package_id = data.get("active_package_id")
        self.preferences = dict(data.get("preferences", {}))
        self.packages = [CoordinationPackage.from_dict(item) for item in data.get("packages", [])]
        self.archive_manager.from_dict(data.get("archive_manager", {}))


def _reference_items(workspace):

    return [
        {
            "id": getattr(model, "id", ""),
            "name": getattr(model, "name", ""),
            "path": getattr(model, "path", ""),
            "status": getattr(model, "status", ""),
            "category": getattr(model, "category", ""),
        }
        for model in getattr(getattr(workspace, "reference_manager", None), "models", [])
    ]


def _bcf_items(workspace):

    manager = getattr(workspace, "bcf_manager", None)
    topics = manager.topics() if manager is not None and hasattr(manager, "topics") else []

    return [
        {
            "id": getattr(topic, "id", ""),
            "title": getattr(topic, "title", ""),
            "status": getattr(topic, "status", ""),
            "priority": getattr(topic, "priority", ""),
        }
        for topic in topics
    ]


def _clash_items(workspace):

    return [
        {
            "id": getattr(clash, "id", ""),
            "name": getattr(clash, "name", getattr(clash, "clash_type", "Clash")),
            "type": getattr(clash, "clash_type", ""),
            "status": getattr(clash, "status", ""),
            "severity": getattr(clash, "severity", ""),
        }
        for clash in getattr(getattr(workspace, "clash_manager", None), "results", [])
    ]


def _revision_items(workspace):

    return [
        {
            "id": getattr(revision, "id", ""),
            "name": getattr(revision, "name", ""),
            "created_at": getattr(revision, "created_at", ""),
        }
        for revision in getattr(getattr(workspace, "revision_manager", None), "revisions", [])
    ]


def _compare_session_items(workspace):

    return [
        {
            "id": getattr(session, "id", ""),
            "name": getattr(session, "name", ""),
            "changes": getattr(getattr(session, "statistics", None), "total", 0),
        }
        for session in getattr(getattr(workspace, "model_compare_manager", None), "sessions", [])
    ]


def _review_items(workspace):

    return [
        {
            "id": getattr(item, "id", ""),
            "title": getattr(item, "title", getattr(item, "name", "Review")),
            "status": getattr(item, "status", ""),
            "priority": getattr(item, "priority", ""),
        }
        for item in getattr(getattr(workspace, "review_manager", None), "items", [])
    ]


def _issue_items(workspace):

    return [
        {
            "id": getattr(issue, "id", ""),
            "title": getattr(issue, "title", ""),
            "status": getattr(issue, "status", ""),
            "priority": getattr(issue, "priority", ""),
        }
        for issue in getattr(getattr(workspace, "issue_manager", None), "issues", [])
    ]


def _package_files(workspace):

    paths = [
        getattr(model, "path", "")
        for model in getattr(getattr(workspace, "reference_manager", None), "models", [])
        if getattr(model, "path", "")
    ]

    return [{"path": path, "role": "Reference"} for path in paths]


def _missing_references(workspace):

    missing = []

    for model in getattr(getattr(workspace, "reference_manager", None), "models", []):
        if getattr(model, "status", "") == "Missing" or not getattr(model, "path", ""):
            missing.append(getattr(model, "name", getattr(model, "id", "Reference")))

    return missing


def _package_location(workspace):

    candidates = []
    for revision in getattr(getattr(workspace, "revision_manager", None), "revisions", []):
        candidates.append(getattr(revision, "location", Vector3()))
    for result in getattr(getattr(workspace, "model_compare_manager", None), "results", lambda: [])():
        candidates.append(getattr(result, "location", Vector3()))

    if not candidates:
        return Vector3()

    total = Vector3()
    for point in candidates:
        total = total + point

    return total * (1.0 / len(candidates))


def _timestamp():

    return datetime.now(timezone.utc).isoformat()


def _vector_to_data(vector):

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_data(data):

    data = data or {}

    return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))
