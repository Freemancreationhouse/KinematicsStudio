"""Building structural engineering definitions for Simulation Workspace.

This module adds building-oriented study metadata, members, systems, loads,
design-code metadata, summaries and report enrichment. It does not own CAD
geometry and does not introduce a second solver; eligible members are converted
into the existing structural mesh format and solved by StructuralLinearStaticSolver.
"""

from dataclasses import dataclass, field
from uuid import uuid4


BUILDING_MEMBER_TYPES = {
    "Beam",
    "Column",
    "Slab",
    "Wall",
    "Shear Wall",
    "Footing",
    "Combined Footing",
    "Raft Foundation",
    "Pile Cap",
    "Stair Slab",
    "Retaining Wall",
    "Transfer Beam",
    "Transfer Slab",
    "Assembly",
    "Steel Beam",
    "Steel Column",
    "Steel Bracing",
    "Portal Frame",
    "Roof Frame",
    "Space Frame",
    "Steel Truss",
}


BUILDING_SYSTEM_TYPES = {
    "Moment Frame",
    "Braced Frame",
    "Load Bearing Structure",
    "Shear Wall System",
    "Dual System",
    "Space Frame System",
    "Industrial Structure",
    "Composite Structure",
}


BUILDING_LOAD_TYPES = {
    "Dead Load",
    "Live Load",
    "Roof Load",
    "Wall Load",
    "Equipment Load",
    "Facade Load",
    "Wind Load",
    "Seismic Load",
    "Snow Load",
    "Water Tank Load",
    "Custom Load",
}


BUILDING_LOAD_DISTRIBUTIONS = {"Storey", "Area", "Line", "Point"}


DESIGN_CODE_NAMES = {"IS 456", "IS 875", "IS 1893", "IS 800", "ACI", "AISC", "Eurocode", "NBC"}


@dataclass
class BuildingStructuralStudy:
    """Building-specific study metadata linked to an existing structural study."""

    study_id: str
    building_name: str
    storeys: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    status: str = "Defined"
    id: str = field(default_factory=lambda: str(uuid4()))
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe building study metadata."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "building_name": self.building_name,
            "storeys": [dict(item) for item in self.storeys],
            "metadata": dict(self.metadata),
            "status": self.status,
            "diagnostics": dict(self.diagnostics),
        }

    @staticmethod
    def from_dict(data):
        """Create building study metadata from persisted data."""

        data = data or {}
        return BuildingStructuralStudy(
            data.get("study_id", ""),
            data.get("building_name", "Building"),
            [dict(item) for item in data.get("storeys", [])],
            dict(data.get("metadata", {})),
            data.get("status", "Defined"),
            data.get("id", str(uuid4())),
            dict(data.get("diagnostics", {})),
        )


@dataclass
class BuildingStructuralMember:
    """Building structural member definition referencing existing CAD geometry."""

    study_id: str
    name: str
    member_type: str
    storey: str = ""
    geometry_references: list = field(default_factory=list)
    start_node: dict = field(default_factory=dict)
    end_node: dict = field(default_factory=dict)
    section: dict = field(default_factory=dict)
    material_id: str = ""
    system_id: str = ""
    connection_metadata: dict = field(default_factory=dict)
    steel_metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe member data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "member_type": self.member_type,
            "storey": self.storey,
            "geometry_references": [dict(item) for item in self.geometry_references],
            "start_node": dict(self.start_node),
            "end_node": dict(self.end_node),
            "section": dict(self.section),
            "material_id": self.material_id,
            "system_id": self.system_id,
            "connection_metadata": dict(self.connection_metadata),
            "steel_metadata": dict(self.steel_metadata),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a member from persisted data."""

        data = data or {}
        return BuildingStructuralMember(
            data.get("study_id", ""),
            data.get("name", "Member"),
            data.get("member_type", "Beam"),
            data.get("storey", ""),
            [dict(item) for item in data.get("geometry_references", [])],
            dict(data.get("start_node", {})),
            dict(data.get("end_node", {})),
            dict(data.get("section", {})),
            data.get("material_id", ""),
            data.get("system_id", ""),
            dict(data.get("connection_metadata", {})),
            dict(data.get("steel_metadata", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class BuildingStructuralSystem:
    """Building structural system metadata."""

    study_id: str
    name: str
    system_type: str
    member_ids: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe structural system data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "system_type": self.system_type,
            "member_ids": list(self.member_ids),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create structural system metadata from persisted data."""

        data = data or {}
        return BuildingStructuralSystem(
            data.get("study_id", ""),
            data.get("name", "Structural System"),
            data.get("system_type", "Moment Frame"),
            list(data.get("member_ids", [])),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class BuildingLoad:
    """Professional building load metadata converted into structural load cases."""

    study_id: str
    name: str
    load_type: str
    distribution: str
    target_references: list = field(default_factory=list)
    values: dict = field(default_factory=dict)
    storey: str = ""
    load_case_id: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe building load data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "load_type": self.load_type,
            "distribution": self.distribution,
            "target_references": [dict(item) for item in self.target_references],
            "values": dict(self.values),
            "storey": self.storey,
            "load_case_id": self.load_case_id,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create building load metadata from persisted data."""

        data = data or {}
        return BuildingLoad(
            data.get("study_id", ""),
            data.get("name", "Building Load"),
            data.get("load_type", "Custom Load"),
            data.get("distribution", "Point"),
            [dict(item) for item in data.get("target_references", [])],
            dict(data.get("values", {})),
            data.get("storey", ""),
            data.get("load_case_id", ""),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class EngineeringDesignCode:
    """Design-code metadata for future design checks."""

    name: str
    load_factors: dict = field(default_factory=dict)
    partial_safety_factors: dict = field(default_factory=dict)
    material_factors: dict = field(default_factory=dict)
    combination_rules: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe design-code data."""

        return {
            "id": self.id,
            "name": self.name,
            "load_factors": dict(self.load_factors),
            "partial_safety_factors": dict(self.partial_safety_factors),
            "material_factors": dict(self.material_factors),
            "combination_rules": dict(self.combination_rules),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create design-code metadata from persisted data."""

        data = data or {}
        return EngineeringDesignCode(
            data.get("name", "Code"),
            dict(data.get("load_factors", {})),
            dict(data.get("partial_safety_factors", {})),
            dict(data.get("material_factors", {})),
            dict(data.get("combination_rules", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


def member_area(member):
    """Return analysis area for a member section."""

    section = member.section
    if "area" in section:
        return float(section["area"])
    if "width" in section and "depth" in section:
        return float(section["width"]) * float(section["depth"])
    if "diameter" in section:
        return 3.141592653589793 * (float(section["diameter"]) ** 2) / 4.0
    return 1.0
