"""Manufacturing Engine production orchestration foundation.

The Manufacturing Engine is a Workspace-owned manufacturing orchestration
facade. It manages jobs, ordered operations, stock, fixtures, coordinate
systems, work offsets, execution plans, validation and diagnostics using
existing Workspace, Machine Workspace and ProductManager storage.

It owns manufacturing planning data, CAM/toolpath data and additive slicing
data. It does not communicate with machines, run manufacturing simulation,
mutate MeshEntity, or own geometry.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import pi
from uuid import uuid4

from engine.geometry import Vector3
from engine.product import (
    CAMMetadata,
    FixtureDefinition,
    OperationMetadata,
    OperationParameters,
    SetupMetadata,
    StockDefinition,
    WorkCoordinateSystem,
)


MANUFACTURING_ENGINE_SETTINGS_KEY = "manufacturing_engine"


MANUFACTURING_STATES = {
    "Pending",
    "Ready",
    "Validated",
    "Blocked",
    "Running",
    "Completed",
    "Cancelled",
    "Archived",
}


VALID_STATE_TRANSITIONS = {
    "Pending": {"Ready", "Blocked", "Cancelled", "Archived"},
    "Ready": {"Validated", "Blocked", "Cancelled", "Archived"},
    "Validated": {"Running", "Blocked", "Completed", "Cancelled", "Archived"},
    "Blocked": {"Pending", "Ready", "Cancelled", "Archived"},
    "Running": {"Completed", "Cancelled", "Blocked"},
    "Completed": {"Archived"},
    "Cancelled": {"Archived", "Pending"},
    "Archived": set(),
}


@dataclass
class ManufacturingEngineState:
    """Persistent state for the Workspace-owned Manufacturing Engine."""

    initialized: bool = False
    active_job_id: str = ""
    version: str = "1.7"
    status: str = "Pending"
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe state data."""

        return {
            "initialized": self.initialized,
            "active_job_id": self.active_job_id,
            "version": self.version,
            "status": self.status,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create state from persisted data."""

        data = data or {}
        return ManufacturingEngineState(
            bool(data.get("initialized", False)),
            data.get("active_job_id", ""),
            data.get("version", "1.7"),
            data.get("status", "Pending"),
            dict(data.get("metadata", {})),
        )


@dataclass
class ManufacturingWorkOffset:
    """Work offset metadata; no controller communication is performed."""

    name: str = "G54"
    translation: dict = field(default_factory=dict)
    rotation: dict = field(default_factory=dict)
    reference_system_id: str = ""
    valid: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe work offset data."""

        return {
            "id": self.id,
            "name": self.name,
            "translation": dict(self.translation),
            "rotation": dict(self.rotation),
            "reference_system_id": self.reference_system_id,
            "valid": self.valid,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create work offset metadata from persisted data."""

        data = data or {}
        return ManufacturingWorkOffset(
            data.get("name", "G54"),
            dict(data.get("translation", {})),
            dict(data.get("rotation", {})),
            data.get("reference_system_id", ""),
            bool(data.get("valid", True)),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class ManufacturingExecutionPlan:
    """Execution plan metadata for a manufacturing job."""

    job_id: str = ""
    operation_ids: list = field(default_factory=list)
    stock_id: str = ""
    fixture_ids: list = field(default_factory=list)
    coordinate_system_ids: list = field(default_factory=list)
    work_offset_ids: list = field(default_factory=list)
    status: str = "Pending"
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the execution plan is complete enough to run later."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe execution plan data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "operation_ids": list(self.operation_ids),
            "stock_id": self.stock_id,
            "fixture_ids": list(self.fixture_ids),
            "coordinate_system_ids": list(self.coordinate_system_ids),
            "work_offset_ids": list(self.work_offset_ids),
            "status": self.status,
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create execution plan metadata from persisted data."""

        data = data or {}
        return ManufacturingExecutionPlan(
            data.get("job_id", ""),
            list(data.get("operation_ids", [])),
            data.get("stock_id", ""),
            list(data.get("fixture_ids", [])),
            list(data.get("coordinate_system_ids", [])),
            list(data.get("work_offset_ids", [])),
            data.get("status", "Pending"),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class ManufacturingValidationReport:
    """Validation report for Manufacturing Engine planning metadata."""

    valid: bool = True
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def add_error(self, message):
        """Record a validation error."""

        self.valid = False
        self.errors.append(str(message))

    def add_warning(self, message):
        """Record a validation warning."""

        self.warnings.append(str(message))

    def to_dict(self):
        """Return JSON-safe validation report data."""

        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }

    @staticmethod
    def from_dict(data):
        """Create validation report from persisted data."""

        data = data or {}
        return ManufacturingValidationReport(
            bool(data.get("valid", True)),
            list(data.get("errors", [])),
            list(data.get("warnings", [])),
        )


@dataclass
class ManufacturingEngineDiagnostics:
    """Diagnostics summary for manufacturing orchestration metadata."""

    jobs: int = 0
    operations: int = 0
    planning_statistics: dict = field(default_factory=dict)
    validation_statistics: dict = field(default_factory=dict)
    dependency_statistics: dict = field(default_factory=dict)
    stock_statistics: dict = field(default_factory=dict)
    fixture_statistics: dict = field(default_factory=dict)
    coordinate_system_statistics: dict = field(default_factory=dict)
    work_offset_statistics: dict = field(default_factory=dict)
    execution_plan_statistics: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe diagnostics data."""

        return {
            "jobs": self.jobs,
            "operations": self.operations,
            "planning_statistics": dict(self.planning_statistics),
            "validation_statistics": dict(self.validation_statistics),
            "dependency_statistics": dict(self.dependency_statistics),
            "stock_statistics": dict(self.stock_statistics),
            "fixture_statistics": dict(self.fixture_statistics),
            "coordinate_system_statistics": dict(self.coordinate_system_statistics),
            "work_offset_statistics": dict(self.work_offset_statistics),
            "execution_plan_statistics": dict(self.execution_plan_statistics),
        }

    @staticmethod
    def from_dict(data):
        """Create diagnostics from persisted data."""

        data = data or {}
        return ManufacturingEngineDiagnostics(
            int(data.get("jobs", 0)),
            int(data.get("operations", 0)),
            dict(data.get("planning_statistics", {})),
            dict(data.get("validation_statistics", {})),
            dict(data.get("dependency_statistics", {})),
            dict(data.get("stock_statistics", {})),
            dict(data.get("fixture_statistics", {})),
            dict(data.get("coordinate_system_statistics", {})),
            dict(data.get("work_offset_statistics", {})),
            dict(data.get("execution_plan_statistics", {})),
        )


@dataclass
class CNCToolpathMove:
    """Native CNC toolpath move metadata."""

    move_type: str = "Rapid"
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    feed: float = 0.0
    i: float = 0.0
    j: float = 0.0
    k: float = 0.0
    comment: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe move data."""

        return {
            "move_type": self.move_type,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "feed": self.feed,
            "i": self.i,
            "j": self.j,
            "k": self.k,
            "comment": self.comment,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a toolpath move from persisted data."""

        data = data or {}
        return CNCToolpathMove(
            data.get("move_type", "Rapid"),
            float(data.get("x", 0.0)),
            float(data.get("y", 0.0)),
            float(data.get("z", 0.0)),
            float(data.get("feed", 0.0)),
            float(data.get("i", 0.0)),
            float(data.get("j", 0.0)),
            float(data.get("k", 0.0)),
            data.get("comment", ""),
            dict(data.get("metadata", {})),
        )


@dataclass
class CNCCuttingParameters:
    """Calculated CNC cutting parameters."""

    rpm: float = 0.0
    feed_rate: float = 0.0
    plunge_rate: float = 0.0
    stepover: float = 0.0
    stepdown: float = 0.0
    surface_speed: float = 0.0
    chip_load: float = 0.0
    material_removal_estimate: float = 0.0
    cycle_estimate: float = 0.0
    tool_engagement: float = 0.0
    overrides: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe cutting parameter data."""

        return {
            "rpm": self.rpm,
            "feed_rate": self.feed_rate,
            "plunge_rate": self.plunge_rate,
            "stepover": self.stepover,
            "stepdown": self.stepdown,
            "surface_speed": self.surface_speed,
            "chip_load": self.chip_load,
            "material_removal_estimate": self.material_removal_estimate,
            "cycle_estimate": self.cycle_estimate,
            "tool_engagement": self.tool_engagement,
            "overrides": dict(self.overrides),
        }

    @staticmethod
    def from_dict(data):
        """Create cutting parameters from persisted data."""

        data = data or {}
        return CNCCuttingParameters(
            float(data.get("rpm", 0.0)),
            float(data.get("feed_rate", 0.0)),
            float(data.get("plunge_rate", 0.0)),
            float(data.get("stepover", 0.0)),
            float(data.get("stepdown", 0.0)),
            float(data.get("surface_speed", 0.0)),
            float(data.get("chip_load", 0.0)),
            float(data.get("material_removal_estimate", 0.0)),
            float(data.get("cycle_estimate", 0.0)),
            float(data.get("tool_engagement", 0.0)),
            dict(data.get("overrides", {})),
        )


@dataclass
class CNCToolpath:
    """Persisted native CNC toolpath for one CAM operation."""

    operation_id: str = ""
    job_id: str = ""
    strategy: str = ""
    tool_id: str = ""
    moves: list = field(default_factory=list)
    cutting_parameters: CNCCuttingParameters = field(default_factory=CNCCuttingParameters)
    status: str = "Generated"
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the toolpath has no blocking validation errors."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe toolpath data."""

        return {
            "id": self.id,
            "operation_id": self.operation_id,
            "job_id": self.job_id,
            "strategy": self.strategy,
            "tool_id": self.tool_id,
            "moves": [move.to_dict() for move in self.moves],
            "cutting_parameters": self.cutting_parameters.to_dict(),
            "status": self.status,
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create toolpath data from persisted project data."""

        data = data or {}
        return CNCToolpath(
            data.get("operation_id", ""),
            data.get("job_id", ""),
            data.get("strategy", ""),
            data.get("tool_id", ""),
            [CNCToolpathMove.from_dict(item) for item in data.get("moves", [])],
            CNCCuttingParameters.from_dict(data.get("cutting_parameters", {})),
            data.get("status", "Generated"),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class CAMPlan:
    """Persistent CAM plan metadata for a manufacturing job."""

    job_id: str = ""
    operation_ids: list = field(default_factory=list)
    strategy_metadata: dict = field(default_factory=dict)
    tool_ids: list = field(default_factory=list)
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the CAM plan has no blocking errors."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe CAM plan data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "operation_ids": list(self.operation_ids),
            "strategy_metadata": dict(self.strategy_metadata),
            "tool_ids": list(self.tool_ids),
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a CAM plan from persisted data."""

        data = data or {}
        return CAMPlan(
            data.get("job_id", ""),
            list(data.get("operation_ids", [])),
            dict(data.get("strategy_metadata", {})),
            list(data.get("tool_ids", [])),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class CNCProgram:
    """Generated native controller-specific G-code program."""

    job_id: str = ""
    controller: str = "Generic ISO G-code"
    program_name: str = "PROGRAM"
    gcode: str = ""
    toolpath_ids: list = field(default_factory=list)
    statistics: dict = field(default_factory=dict)
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the generated program has no blocking errors."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe program data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "controller": self.controller,
            "program_name": self.program_name,
            "gcode": self.gcode,
            "toolpath_ids": list(self.toolpath_ids),
            "statistics": dict(self.statistics),
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a CNC program from persisted data."""

        data = data or {}
        return CNCProgram(
            data.get("job_id", ""),
            data.get("controller", "Generic ISO G-code"),
            data.get("program_name", "PROGRAM"),
            data.get("gcode", ""),
            list(data.get("toolpath_ids", [])),
            dict(data.get("statistics", {})),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class AdditivePrintParameters:
    """Native additive manufacturing print parameters."""

    technology: str = "FDM"
    layer_height: float = 0.2
    nozzle_diameter: float = 0.4
    extrusion_width: float = 0.45
    line_count: int = 2
    wall_thickness: float = 0.8
    top_thickness: float = 0.8
    bottom_thickness: float = 0.8
    infill_percentage: float = 20.0
    infill_pattern: str = "Grid"
    print_speed: float = 60.0
    travel_speed: float = 120.0
    acceleration: float = 1000.0
    jerk: float = 8.0
    temperature: dict = field(default_factory=dict)
    cooling: dict = field(default_factory=dict)
    resin: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe print parameter data."""

        return {
            "technology": self.technology,
            "layer_height": self.layer_height,
            "nozzle_diameter": self.nozzle_diameter,
            "extrusion_width": self.extrusion_width,
            "line_count": self.line_count,
            "wall_thickness": self.wall_thickness,
            "top_thickness": self.top_thickness,
            "bottom_thickness": self.bottom_thickness,
            "infill_percentage": self.infill_percentage,
            "infill_pattern": self.infill_pattern,
            "print_speed": self.print_speed,
            "travel_speed": self.travel_speed,
            "acceleration": self.acceleration,
            "jerk": self.jerk,
            "temperature": dict(self.temperature),
            "cooling": dict(self.cooling),
            "resin": dict(self.resin),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create print parameters from persisted data."""

        data = data or {}
        return AdditivePrintParameters(
            data.get("technology", "FDM"),
            float(data.get("layer_height", 0.2)),
            float(data.get("nozzle_diameter", 0.4)),
            float(data.get("extrusion_width", 0.45)),
            int(data.get("line_count", 2)),
            float(data.get("wall_thickness", 0.8)),
            float(data.get("top_thickness", 0.8)),
            float(data.get("bottom_thickness", 0.8)),
            float(data.get("infill_percentage", 20.0)),
            data.get("infill_pattern", "Grid"),
            float(data.get("print_speed", 60.0)),
            float(data.get("travel_speed", 120.0)),
            float(data.get("acceleration", 1000.0)),
            float(data.get("jerk", 8.0)),
            dict(data.get("temperature", {})),
            dict(data.get("cooling", {})),
            dict(data.get("resin", {})),
            dict(data.get("metadata", {})),
        )


@dataclass
class AdditiveSupportPlan:
    """Generated support metadata for additive manufacturing."""

    enabled: bool = False
    support_type: str = "Automatic"
    density: float = 15.0
    pattern: str = "Grid"
    angle: float = 45.0
    interface_layers: int = 2
    blockers: list = field(default_factory=list)
    enforcers: list = field(default_factory=list)
    support_regions: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe support data."""

        return {
            "enabled": self.enabled,
            "support_type": self.support_type,
            "density": self.density,
            "pattern": self.pattern,
            "angle": self.angle,
            "interface_layers": self.interface_layers,
            "blockers": list(self.blockers),
            "enforcers": list(self.enforcers),
            "support_regions": [dict(item) for item in self.support_regions],
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create support plan from persisted data."""

        data = data or {}
        return AdditiveSupportPlan(
            bool(data.get("enabled", False)),
            data.get("support_type", "Automatic"),
            float(data.get("density", 15.0)),
            data.get("pattern", "Grid"),
            float(data.get("angle", 45.0)),
            int(data.get("interface_layers", 2)),
            list(data.get("blockers", [])),
            list(data.get("enforcers", [])),
            [dict(item) for item in data.get("support_regions", [])],
            dict(data.get("metadata", {})),
        )


@dataclass
class BuildPlateLayout:
    """Build plate placement and adhesion metadata."""

    job_id: str = ""
    placements: list = field(default_factory=list)
    build_volume: dict = field(default_factory=dict)
    brim: bool = False
    skirt: bool = True
    raft: bool = False
    prime_tower: dict = field(default_factory=dict)
    collisions: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the build layout has no placement collisions."""

        return not self.collisions

    def to_dict(self):
        """Return JSON-safe build plate layout data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "placements": [dict(item) for item in self.placements],
            "build_volume": dict(self.build_volume),
            "brim": self.brim,
            "skirt": self.skirt,
            "raft": self.raft,
            "prime_tower": dict(self.prime_tower),
            "collisions": [dict(item) for item in self.collisions],
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create build plate layout from persisted data."""

        data = data or {}
        return BuildPlateLayout(
            data.get("job_id", ""),
            [dict(item) for item in data.get("placements", [])],
            dict(data.get("build_volume", {})),
            bool(data.get("brim", False)),
            bool(data.get("skirt", True)),
            bool(data.get("raft", False)),
            dict(data.get("prime_tower", {})),
            [dict(item) for item in data.get("collisions", [])],
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class AdditiveLayer:
    """Generated native additive layer data."""

    index: int = 0
    z: float = 0.0
    height: float = 0.2
    perimeters: list = field(default_factory=list)
    walls: list = field(default_factory=list)
    top: list = field(default_factory=list)
    bottom: list = field(default_factory=list)
    infill: list = field(default_factory=list)
    supports: list = field(default_factory=list)
    travel: list = field(default_factory=list)
    exposure: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe layer data."""

        return {
            "index": self.index,
            "z": self.z,
            "height": self.height,
            "perimeters": [list(path) for path in self.perimeters],
            "walls": [list(path) for path in self.walls],
            "top": [list(path) for path in self.top],
            "bottom": [list(path) for path in self.bottom],
            "infill": [list(path) for path in self.infill],
            "supports": [list(path) for path in self.supports],
            "travel": [list(path) for path in self.travel],
            "exposure": dict(self.exposure),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create layer data from persisted project data."""

        data = data or {}
        return AdditiveLayer(
            int(data.get("index", 0)),
            float(data.get("z", 0.0)),
            float(data.get("height", 0.2)),
            [list(path) for path in data.get("perimeters", [])],
            [list(path) for path in data.get("walls", [])],
            [list(path) for path in data.get("top", [])],
            [list(path) for path in data.get("bottom", [])],
            [list(path) for path in data.get("infill", [])],
            [list(path) for path in data.get("supports", [])],
            [list(path) for path in data.get("travel", [])],
            dict(data.get("exposure", {})),
            dict(data.get("metadata", {})),
        )


@dataclass
class AdditiveSliceResult:
    """Generated additive slicing result for FDM or SLA."""

    job_id: str = ""
    slice_job_id: str = ""
    technology: str = "FDM"
    layers: list = field(default_factory=list)
    support_plan: AdditiveSupportPlan = field(default_factory=AdditiveSupportPlan)
    build_layout_id: str = ""
    material_usage: dict = field(default_factory=dict)
    estimated_print_time: float = 0.0
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the slice result has no blocking errors."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe slice result data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "slice_job_id": self.slice_job_id,
            "technology": self.technology,
            "layers": [layer.to_dict() for layer in self.layers],
            "support_plan": self.support_plan.to_dict(),
            "build_layout_id": self.build_layout_id,
            "material_usage": dict(self.material_usage),
            "estimated_print_time": self.estimated_print_time,
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create additive slice result from persisted data."""

        data = data or {}
        return AdditiveSliceResult(
            data.get("job_id", ""),
            data.get("slice_job_id", ""),
            data.get("technology", "FDM"),
            [AdditiveLayer.from_dict(item) for item in data.get("layers", [])],
            AdditiveSupportPlan.from_dict(data.get("support_plan", {})),
            data.get("build_layout_id", ""),
            dict(data.get("material_usage", {})),
            float(data.get("estimated_print_time", 0.0)),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class AdditivePrintFile:
    """Generated native additive manufacturing print file."""

    job_id: str = ""
    slice_result_id: str = ""
    format: str = "Generic G-code"
    file_name: str = "print.gcode"
    content: str = ""
    statistics: dict = field(default_factory=dict)
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the print file has no blocking errors."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe print file data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "slice_result_id": self.slice_result_id,
            "format": self.format,
            "file_name": self.file_name,
            "content": self.content,
            "statistics": dict(self.statistics),
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create additive print file from persisted data."""

        data = data or {}
        return AdditivePrintFile(
            data.get("job_id", ""),
            data.get("slice_result_id", ""),
            data.get("format", "Generic G-code"),
            data.get("file_name", "print.gcode"),
            data.get("content", ""),
            dict(data.get("statistics", {})),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SheetCutParameters:
    """Production sheet cutting parameters for laser, plasma and waterjet jobs."""

    process: str = "Laser"
    operation_type: str = "Vector Cut"
    kerf_width: float = 0.1
    compensation: str = "Outside"
    power: float = 0.0
    speed: float = 1200.0
    pass_count: int = 1
    pierce: dict = field(default_factory=dict)
    lead_in: dict = field(default_factory=dict)
    lead_out: dict = field(default_factory=dict)
    gas: dict = field(default_factory=dict)
    height_control: dict = field(default_factory=dict)
    consumable: dict = field(default_factory=dict)
    waterjet: dict = field(default_factory=dict)
    raster: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe sheet cutting parameters."""

        return {
            "process": self.process,
            "operation_type": self.operation_type,
            "kerf_width": self.kerf_width,
            "compensation": self.compensation,
            "power": self.power,
            "speed": self.speed,
            "pass_count": self.pass_count,
            "pierce": dict(self.pierce),
            "lead_in": dict(self.lead_in),
            "lead_out": dict(self.lead_out),
            "gas": dict(self.gas),
            "height_control": dict(self.height_control),
            "consumable": dict(self.consumable),
            "waterjet": dict(self.waterjet),
            "raster": dict(self.raster),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create sheet cutting parameters from persisted data."""

        data = data or {}
        return SheetCutParameters(
            data.get("process", "Laser"),
            data.get("operation_type", "Vector Cut"),
            float(data.get("kerf_width", 0.1)),
            data.get("compensation", "Outside"),
            float(data.get("power", 0.0)),
            float(data.get("speed", 1200.0)),
            int(data.get("pass_count", 1)),
            dict(data.get("pierce", {})),
            dict(data.get("lead_in", {})),
            dict(data.get("lead_out", {})),
            dict(data.get("gas", {})),
            dict(data.get("height_control", {})),
            dict(data.get("consumable", {})),
            dict(data.get("waterjet", {})),
            dict(data.get("raster", {})),
            dict(data.get("metadata", {})),
        )


@dataclass
class SheetMaterialProfile:
    """Sheet material process profile reused by sheet manufacturing jobs."""

    job_id: str = ""
    material_id: str = ""
    thickness: float = 0.0
    sheet_size: dict = field(default_factory=dict)
    compatibility: dict = field(default_factory=dict)
    recommendations: dict = field(default_factory=dict)
    quality: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe sheet material profile data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "material_id": self.material_id,
            "thickness": self.thickness,
            "sheet_size": dict(self.sheet_size),
            "compatibility": dict(self.compatibility),
            "recommendations": dict(self.recommendations),
            "quality": dict(self.quality),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a sheet material profile from persisted data."""

        data = data or {}
        return SheetMaterialProfile(
            data.get("job_id", ""),
            data.get("material_id", ""),
            float(data.get("thickness", 0.0)),
            dict(data.get("sheet_size", {})),
            dict(data.get("compatibility", {})),
            dict(data.get("recommendations", {})),
            dict(data.get("quality", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SheetNestLayout:
    """Nested 2D sheet layout for laser, plasma and waterjet fabrication."""

    job_id: str = ""
    sheet_size: dict = field(default_factory=dict)
    placements: list = field(default_factory=list)
    spacing: float = 2.0
    utilization: float = 0.0
    collisions: list = field(default_factory=list)
    remnants: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the nest has no blocking placement collisions."""

        return not self.collisions

    def to_dict(self):
        """Return JSON-safe nest layout data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "sheet_size": dict(self.sheet_size),
            "placements": [dict(item) for item in self.placements],
            "spacing": self.spacing,
            "utilization": self.utilization,
            "collisions": [dict(item) for item in self.collisions],
            "remnants": [dict(item) for item in self.remnants],
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a nest layout from persisted data."""

        data = data or {}
        return SheetNestLayout(
            data.get("job_id", ""),
            dict(data.get("sheet_size", {})),
            [dict(item) for item in data.get("placements", [])],
            float(data.get("spacing", 2.0)),
            float(data.get("utilization", 0.0)),
            [dict(item) for item in data.get("collisions", [])],
            [dict(item) for item in data.get("remnants", [])],
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SheetCutPath:
    """Generated native 2D sheet cutting path."""

    job_id: str = ""
    operation_id: str = ""
    process: str = "Laser"
    path_type: str = "Cut"
    points: list = field(default_factory=list)
    compensated_points: list = field(default_factory=list)
    lead_in: list = field(default_factory=list)
    lead_out: list = field(default_factory=list)
    pierce_points: list = field(default_factory=list)
    travel_moves: list = field(default_factory=list)
    kerf_width: float = 0.0
    estimated_time: float = 0.0
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the cut path has no validation errors."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe cut path data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "operation_id": self.operation_id,
            "process": self.process,
            "path_type": self.path_type,
            "points": [list(point) for point in self.points],
            "compensated_points": [list(point) for point in self.compensated_points],
            "lead_in": [list(point) for point in self.lead_in],
            "lead_out": [list(point) for point in self.lead_out],
            "pierce_points": [list(point) for point in self.pierce_points],
            "travel_moves": [list(point) for point in self.travel_moves],
            "kerf_width": self.kerf_width,
            "estimated_time": self.estimated_time,
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a cut path from persisted data."""

        data = data or {}
        return SheetCutPath(
            data.get("job_id", ""),
            data.get("operation_id", ""),
            data.get("process", "Laser"),
            data.get("path_type", "Cut"),
            [list(point) for point in data.get("points", [])],
            [list(point) for point in data.get("compensated_points", [])],
            [list(point) for point in data.get("lead_in", [])],
            [list(point) for point in data.get("lead_out", [])],
            [list(point) for point in data.get("pierce_points", [])],
            [list(point) for point in data.get("travel_moves", [])],
            float(data.get("kerf_width", 0.0)),
            float(data.get("estimated_time", 0.0)),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SheetProgram:
    """Controller-ready sheet manufacturing program."""

    job_id: str = ""
    controller: str = "Generic G-code"
    program_name: str = "SHEET_PROGRAM"
    content: str = ""
    cut_path_ids: list = field(default_factory=list)
    statistics: dict = field(default_factory=dict)
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the sheet program has no blocking errors."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe sheet program data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "controller": self.controller,
            "program_name": self.program_name,
            "content": self.content,
            "cut_path_ids": list(self.cut_path_ids),
            "statistics": dict(self.statistics),
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a sheet program from persisted data."""

        data = data or {}
        return SheetProgram(
            data.get("job_id", ""),
            data.get("controller", "Generic G-code"),
            data.get("program_name", "SHEET_PROGRAM"),
            data.get("content", ""),
            list(data.get("cut_path_ids", [])),
            dict(data.get("statistics", {})),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class RobotProfile:
    """Reusable robot profile metadata for Robotics & Motion planning."""

    name: str = "Robot Profile"
    robot_type: str = "6-axis"
    machine_profile_id: str = ""
    payload: float = 0.0
    reach: float = 0.0
    joint_limits: list = field(default_factory=list)
    tcp: dict = field(default_factory=dict)
    base_frame: dict = field(default_factory=dict)
    tool_frame: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe robot profile data."""

        return {
            "id": self.id,
            "name": self.name,
            "robot_type": self.robot_type,
            "machine_profile_id": self.machine_profile_id,
            "payload": self.payload,
            "reach": self.reach,
            "joint_limits": [dict(item) for item in self.joint_limits],
            "tcp": dict(self.tcp),
            "base_frame": dict(self.base_frame),
            "tool_frame": dict(self.tool_frame),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a robot profile from persisted data."""

        data = data or {}
        return RobotProfile(
            data.get("name", "Robot Profile"),
            data.get("robot_type", "6-axis"),
            data.get("machine_profile_id", ""),
            float(data.get("payload", 0.0)),
            float(data.get("reach", 0.0)),
            [dict(item) for item in data.get("joint_limits", [])],
            dict(data.get("tcp", {})),
            dict(data.get("base_frame", {})),
            dict(data.get("tool_frame", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class RobotFrame:
    """Persistent robot, machine, user or tool coordinate frame."""

    job_id: str = ""
    name: str = "Frame"
    frame_type: str = "User Frame"
    origin: dict = field(default_factory=dict)
    rotation: dict = field(default_factory=dict)
    parent_frame_id: str = ""
    transform: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe frame data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "name": self.name,
            "frame_type": self.frame_type,
            "origin": dict(self.origin),
            "rotation": dict(self.rotation),
            "parent_frame_id": self.parent_frame_id,
            "transform": dict(self.transform),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a robot frame from persisted data."""

        data = data or {}
        return RobotFrame(
            data.get("job_id", ""),
            data.get("name", "Frame"),
            data.get("frame_type", "User Frame"),
            dict(data.get("origin", {})),
            dict(data.get("rotation", {})),
            data.get("parent_frame_id", ""),
            dict(data.get("transform", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class RobotMotionCommand:
    """Planned robot motion command metadata."""

    job_id: str = ""
    motion_type: str = "Joint"
    target: dict = field(default_factory=dict)
    joints: list = field(default_factory=list)
    frame_id: str = ""
    velocity: float = 100.0
    acceleration: float = 100.0
    jerk: float = 0.0
    blend_radius: float = 0.0
    process: dict = field(default_factory=dict)
    order: int = 0
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe motion command data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "motion_type": self.motion_type,
            "target": dict(self.target),
            "joints": list(self.joints),
            "frame_id": self.frame_id,
            "velocity": self.velocity,
            "acceleration": self.acceleration,
            "jerk": self.jerk,
            "blend_radius": self.blend_radius,
            "process": dict(self.process),
            "order": self.order,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a motion command from persisted data."""

        data = data or {}
        return RobotMotionCommand(
            data.get("job_id", ""),
            data.get("motion_type", "Joint"),
            dict(data.get("target", {})),
            list(data.get("joints", [])),
            data.get("frame_id", ""),
            float(data.get("velocity", 100.0)),
            float(data.get("acceleration", 100.0)),
            float(data.get("jerk", 0.0)),
            float(data.get("blend_radius", 0.0)),
            dict(data.get("process", {})),
            int(data.get("order", 0)),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class RobotTrajectory:
    """Generated native robot trajectory."""

    job_id: str = ""
    motion_ids: list = field(default_factory=list)
    waypoints: list = field(default_factory=list)
    joint_path: list = field(default_factory=list)
    linear_path: list = field(default_factory=list)
    circular_path: list = field(default_factory=list)
    estimated_cycle_time: float = 0.0
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the trajectory has no validation errors."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe trajectory data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "motion_ids": list(self.motion_ids),
            "waypoints": [dict(item) for item in self.waypoints],
            "joint_path": [list(item) for item in self.joint_path],
            "linear_path": [dict(item) for item in self.linear_path],
            "circular_path": [dict(item) for item in self.circular_path],
            "estimated_cycle_time": self.estimated_cycle_time,
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a trajectory from persisted data."""

        data = data or {}
        return RobotTrajectory(
            data.get("job_id", ""),
            list(data.get("motion_ids", [])),
            [dict(item) for item in data.get("waypoints", [])],
            [list(item) for item in data.get("joint_path", [])],
            [dict(item) for item in data.get("linear_path", [])],
            [dict(item) for item in data.get("circular_path", [])],
            float(data.get("estimated_cycle_time", 0.0)),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class RobotProgram:
    """Generated production robot program text."""

    job_id: str = ""
    controller: str = "Generic Robot Program"
    program_name: str = "ROBOT_PROGRAM"
    content: str = ""
    trajectory_id: str = ""
    statistics: dict = field(default_factory=dict)
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the robot program has no validation errors."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe robot program data."""

        return {
            "id": self.id,
            "job_id": self.job_id,
            "controller": self.controller,
            "program_name": self.program_name,
            "content": self.content,
            "trajectory_id": self.trajectory_id,
            "statistics": dict(self.statistics),
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a robot program from persisted data."""

        data = data or {}
        return RobotProgram(
            data.get("job_id", ""),
            data.get("controller", "Generic Robot Program"),
            data.get("program_name", "ROBOT_PROGRAM"),
            data.get("content", ""),
            data.get("trajectory_id", ""),
            dict(data.get("statistics", {})),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationJob:
    """Manufacturing simulation job metadata stored by the Manufacturing Engine."""

    manufacturing_job_id: str = ""
    process_type: str = "CNC"
    name: str = "Simulation"
    settings: dict = field(default_factory=dict)
    status: str = "Planned"
    version: str = "1.7"
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the simulation job has no blocking validation errors."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe simulation job data."""

        return {
            "id": self.id,
            "manufacturing_job_id": self.manufacturing_job_id,
            "process_type": self.process_type,
            "name": self.name,
            "settings": dict(self.settings),
            "status": self.status,
            "version": self.version,
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create simulation job metadata from persisted data."""

        data = data or {}
        return SimulationJob(
            data.get("manufacturing_job_id", ""),
            data.get("process_type", "CNC"),
            data.get("name", "Simulation"),
            dict(data.get("settings", {})),
            data.get("status", "Planned"),
            data.get("version", "1.7"),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationSession:
    """Virtual manufacturing replay session metadata."""

    simulation_job_id: str = ""
    manufacturing_job_id: str = ""
    process_type: str = "CNC"
    replay_steps: list = field(default_factory=list)
    progress: float = 0.0
    estimated_time: float = 0.0
    material_usage: dict = field(default_factory=dict)
    tool_usage: dict = field(default_factory=dict)
    status: str = "Completed"
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the simulation session replay is valid."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe session data."""

        return {
            "id": self.id,
            "simulation_job_id": self.simulation_job_id,
            "manufacturing_job_id": self.manufacturing_job_id,
            "process_type": self.process_type,
            "replay_steps": [dict(item) for item in self.replay_steps],
            "progress": self.progress,
            "estimated_time": self.estimated_time,
            "material_usage": dict(self.material_usage),
            "tool_usage": dict(self.tool_usage),
            "status": self.status,
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a simulation session from persisted data."""

        data = data or {}
        return SimulationSession(
            data.get("simulation_job_id", ""),
            data.get("manufacturing_job_id", ""),
            data.get("process_type", "CNC"),
            [dict(item) for item in data.get("replay_steps", [])],
            float(data.get("progress", 0.0)),
            float(data.get("estimated_time", 0.0)),
            dict(data.get("material_usage", {})),
            dict(data.get("tool_usage", {})),
            data.get("status", "Completed"),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationCollisionReport:
    """Collision checking result for virtual manufacturing replay."""

    simulation_job_id: str = ""
    manufacturing_job_id: str = ""
    collisions: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    checked_categories: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the collision report contains no collisions."""

        return not self.collisions

    def to_dict(self):
        """Return JSON-safe collision report data."""

        return {
            "id": self.id,
            "simulation_job_id": self.simulation_job_id,
            "manufacturing_job_id": self.manufacturing_job_id,
            "collisions": [dict(item) for item in self.collisions],
            "warnings": list(self.warnings),
            "checked_categories": list(self.checked_categories),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create collision report from persisted data."""

        data = data or {}
        return SimulationCollisionReport(
            data.get("simulation_job_id", ""),
            data.get("manufacturing_job_id", ""),
            [dict(item) for item in data.get("collisions", [])],
            list(data.get("warnings", [])),
            list(data.get("checked_categories", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationVerificationReport:
    """Manufacturing readiness verification metadata."""

    simulation_job_id: str = ""
    manufacturing_job_id: str = ""
    checks: dict = field(default_factory=dict)
    ready: bool = True
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether verification has no blocking errors."""

        return self.ready and not self.validation_errors

    def to_dict(self):
        """Return JSON-safe verification report data."""

        return {
            "id": self.id,
            "simulation_job_id": self.simulation_job_id,
            "manufacturing_job_id": self.manufacturing_job_id,
            "checks": dict(self.checks),
            "ready": self.ready,
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create verification report from persisted data."""

        data = data or {}
        return SimulationVerificationReport(
            data.get("simulation_job_id", ""),
            data.get("manufacturing_job_id", ""),
            dict(data.get("checks", {})),
            bool(data.get("ready", True)),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationReport:
    """Persistent manufacturing simulation summary report."""

    simulation_job_id: str = ""
    manufacturing_job_id: str = ""
    process_type: str = "CNC"
    summary: str = ""
    estimated_cycle_time: float = 0.0
    estimated_print_time: float = 0.0
    estimated_cutting_time: float = 0.0
    material_usage: dict = field(default_factory=dict)
    tool_usage: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    collisions: list = field(default_factory=list)
    verification_status: str = "Ready"
    validation_results: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the simulation report is manufacturing-ready."""

        return not self.collisions and self.verification_status == "Ready"

    def to_dict(self):
        """Return JSON-safe simulation report data."""

        return {
            "id": self.id,
            "simulation_job_id": self.simulation_job_id,
            "manufacturing_job_id": self.manufacturing_job_id,
            "process_type": self.process_type,
            "summary": self.summary,
            "estimated_cycle_time": self.estimated_cycle_time,
            "estimated_print_time": self.estimated_print_time,
            "estimated_cutting_time": self.estimated_cutting_time,
            "material_usage": dict(self.material_usage),
            "tool_usage": dict(self.tool_usage),
            "warnings": list(self.warnings),
            "collisions": [dict(item) for item in self.collisions],
            "verification_status": self.verification_status,
            "validation_results": dict(self.validation_results),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create simulation report from persisted data."""

        data = data or {}
        return SimulationReport(
            data.get("simulation_job_id", ""),
            data.get("manufacturing_job_id", ""),
            data.get("process_type", "CNC"),
            data.get("summary", ""),
            float(data.get("estimated_cycle_time", 0.0)),
            float(data.get("estimated_print_time", 0.0)),
            float(data.get("estimated_cutting_time", 0.0)),
            dict(data.get("material_usage", {})),
            dict(data.get("tool_usage", {})),
            list(data.get("warnings", [])),
            [dict(item) for item in data.get("collisions", [])],
            data.get("verification_status", "Ready"),
            dict(data.get("validation_results", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class MachineConnection:
    """Persistent machine connection metadata for native communication."""

    machine_profile_id: str = ""
    protocol: str = "GRBL"
    connection_type: str = "Serial"
    parameters: dict = field(default_factory=dict)
    capabilities: dict = field(default_factory=dict)
    state: str = "Disconnected"
    last_heartbeat: str = ""
    timeout_seconds: float = 30.0
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the connection metadata can be used for dispatch."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe connection data."""

        return {
            "id": self.id,
            "machine_profile_id": self.machine_profile_id,
            "protocol": self.protocol,
            "connection_type": self.connection_type,
            "parameters": dict(self.parameters),
            "capabilities": dict(self.capabilities),
            "state": self.state,
            "last_heartbeat": self.last_heartbeat,
            "timeout_seconds": self.timeout_seconds,
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create connection metadata from persisted data."""

        data = data or {}
        return MachineConnection(
            data.get("machine_profile_id", ""),
            data.get("protocol", "GRBL"),
            data.get("connection_type", "Serial"),
            dict(data.get("parameters", {})),
            dict(data.get("capabilities", {})),
            data.get("state", "Disconnected"),
            data.get("last_heartbeat", ""),
            float(data.get("timeout_seconds", 30.0)),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class CommunicationSession:
    """Execution session for a machine connection and queued manufacturing job."""

    connection_id: str = ""
    manufacturing_job_id: str = ""
    protocol: str = "GRBL"
    state: str = "Created"
    uploaded_program_id: str = ""
    progress: float = 0.0
    elapsed_time: float = 0.0
    remaining_time: float = 0.0
    started_at: str = ""
    completed_at: str = ""
    validation_errors: list = field(default_factory=list)
    validation_warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the communication session has no validation errors."""

        return not self.validation_errors

    def to_dict(self):
        """Return JSON-safe communication session data."""

        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "manufacturing_job_id": self.manufacturing_job_id,
            "protocol": self.protocol,
            "state": self.state,
            "uploaded_program_id": self.uploaded_program_id,
            "progress": self.progress,
            "elapsed_time": self.elapsed_time,
            "remaining_time": self.remaining_time,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a communication session from persisted data."""

        data = data or {}
        return CommunicationSession(
            data.get("connection_id", ""),
            data.get("manufacturing_job_id", ""),
            data.get("protocol", "GRBL"),
            data.get("state", "Created"),
            data.get("uploaded_program_id", ""),
            float(data.get("progress", 0.0)),
            float(data.get("elapsed_time", 0.0)),
            float(data.get("remaining_time", 0.0)),
            data.get("started_at", ""),
            data.get("completed_at", ""),
            list(data.get("validation_errors", [])),
            list(data.get("validation_warnings", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class CommunicationJobQueueItem:
    """Queued manufacturing job dispatch metadata."""

    manufacturing_job_id: str = ""
    connection_id: str = ""
    priority: int = 0
    status: str = "Queued"
    retry_count: int = 0
    max_retries: int = 1
    uploaded_program_id: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe queue item data."""

        return {
            "id": self.id,
            "manufacturing_job_id": self.manufacturing_job_id,
            "connection_id": self.connection_id,
            "priority": self.priority,
            "status": self.status,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "uploaded_program_id": self.uploaded_program_id,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create queue item from persisted data."""

        data = data or {}
        return CommunicationJobQueueItem(
            data.get("manufacturing_job_id", ""),
            data.get("connection_id", ""),
            int(data.get("priority", 0)),
            data.get("status", "Queued"),
            int(data.get("retry_count", 0)),
            int(data.get("max_retries", 1)),
            data.get("uploaded_program_id", ""),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class MachineMonitoringState:
    """Live machine monitoring metadata captured by the Communication Engine."""

    connection_id: str = ""
    machine_state: str = "Unknown"
    current_job_id: str = ""
    progress: float = 0.0
    elapsed_time: float = 0.0
    remaining_time: float = 0.0
    tool_status: dict = field(default_factory=dict)
    temperature: dict = field(default_factory=dict)
    spindle: dict = field(default_factory=dict)
    position: dict = field(default_factory=dict)
    feed_override: dict = field(default_factory=dict)
    status_events: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe monitoring data."""

        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "machine_state": self.machine_state,
            "current_job_id": self.current_job_id,
            "progress": self.progress,
            "elapsed_time": self.elapsed_time,
            "remaining_time": self.remaining_time,
            "tool_status": dict(self.tool_status),
            "temperature": dict(self.temperature),
            "spindle": dict(self.spindle),
            "position": dict(self.position),
            "feed_override": dict(self.feed_override),
            "status_events": list(self.status_events),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create monitoring state from persisted data."""

        data = data or {}
        return MachineMonitoringState(
            data.get("connection_id", ""),
            data.get("machine_state", "Unknown"),
            data.get("current_job_id", ""),
            float(data.get("progress", 0.0)),
            float(data.get("elapsed_time", 0.0)),
            float(data.get("remaining_time", 0.0)),
            dict(data.get("tool_status", {})),
            dict(data.get("temperature", {})),
            dict(data.get("spindle", {})),
            dict(data.get("position", {})),
            dict(data.get("feed_override", {})),
            list(data.get("status_events", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class CommunicationEvent:
    """Persistent machine communication event log entry."""

    connection_id: str = ""
    event_type: str = "Info"
    message: str = ""
    severity: str = "Info"
    manufacturing_job_id: str = ""
    session_id: str = ""
    timestamp: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe event data."""

        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "event_type": self.event_type,
            "message": self.message,
            "severity": self.severity,
            "manufacturing_job_id": self.manufacturing_job_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create event from persisted data."""

        data = data or {}
        return CommunicationEvent(
            data.get("connection_id", ""),
            data.get("event_type", "Info"),
            data.get("message", ""),
            data.get("severity", "Info"),
            data.get("manufacturing_job_id", ""),
            data.get("session_id", ""),
            data.get("timestamp", ""),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class ProductionRuntimeState:
    """Production manufacturing runtime lifecycle metadata."""

    initialized: bool = False
    status: str = "Pending"
    active_pipeline_id: str = ""
    heartbeat: str = ""
    version: str = "1.7"
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe runtime state data."""

        return {
            "initialized": self.initialized,
            "status": self.status,
            "active_pipeline_id": self.active_pipeline_id,
            "heartbeat": self.heartbeat,
            "version": self.version,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create runtime state from persisted data."""

        data = data or {}
        return ProductionRuntimeState(
            bool(data.get("initialized", False)),
            data.get("status", "Pending"),
            data.get("active_pipeline_id", ""),
            data.get("heartbeat", ""),
            data.get("version", "1.7"),
            dict(data.get("metadata", {})),
        )


@dataclass
class ProductionRuntimeEvent:
    """Runtime event metadata for lifecycle, health, validation and recovery."""

    event_type: str = "Runtime"
    message: str = ""
    severity: str = "Info"
    job_id: str = ""
    session_id: str = ""
    timestamp: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe runtime event data."""

        return {
            "id": self.id,
            "event_type": self.event_type,
            "message": self.message,
            "severity": self.severity,
            "job_id": self.job_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create runtime event from persisted data."""

        data = data or {}
        return ProductionRuntimeEvent(
            data.get("event_type", "Runtime"),
            data.get("message", ""),
            data.get("severity", "Info"),
            data.get("job_id", ""),
            data.get("session_id", ""),
            data.get("timestamp", ""),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class ProductionRuntimeHealth:
    """Production runtime health summary over existing manufacturing subsystems."""

    status: str = "Unknown"
    subsystem_status: dict = field(default_factory=dict)
    dependencies: dict = field(default_factory=dict)
    resources: dict = field(default_factory=dict)
    failures: list = field(default_factory=list)
    recovery_plan: list = field(default_factory=list)
    heartbeat: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether runtime health is production ready."""

        return self.status == "Healthy" and not self.failures

    def to_dict(self):
        """Return JSON-safe runtime health data."""

        return {
            "id": self.id,
            "status": self.status,
            "subsystem_status": dict(self.subsystem_status),
            "dependencies": dict(self.dependencies),
            "resources": dict(self.resources),
            "failures": list(self.failures),
            "recovery_plan": list(self.recovery_plan),
            "heartbeat": self.heartbeat,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create runtime health data from persisted data."""

        data = data or {}
        return ProductionRuntimeHealth(
            data.get("status", "Unknown"),
            dict(data.get("subsystem_status", {})),
            dict(data.get("dependencies", {})),
            dict(data.get("resources", {})),
            list(data.get("failures", [])),
            list(data.get("recovery_plan", [])),
            data.get("heartbeat", ""),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class ProductionExecutionPipeline:
    """Production execution pipeline metadata using existing subsystem APIs."""

    manufacturing_job_id: str = ""
    intent: str = ""
    stages: list = field(default_factory=list)
    status: str = "Pending"
    validation: dict = field(default_factory=dict)
    simulation_report_id: str = ""
    approval_status: str = "Pending"
    communication_session_id: str = ""
    monitoring_state_id: str = ""
    report_id: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the pipeline has no blocking validation errors."""

        return not self.validation.get("errors", [])

    def to_dict(self):
        """Return JSON-safe pipeline data."""

        return {
            "id": self.id,
            "manufacturing_job_id": self.manufacturing_job_id,
            "intent": self.intent,
            "stages": [dict(stage) for stage in self.stages],
            "status": self.status,
            "validation": dict(self.validation),
            "simulation_report_id": self.simulation_report_id,
            "approval_status": self.approval_status,
            "communication_session_id": self.communication_session_id,
            "monitoring_state_id": self.monitoring_state_id,
            "report_id": self.report_id,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create execution pipeline metadata from persisted data."""

        data = data or {}
        return ProductionExecutionPipeline(
            data.get("manufacturing_job_id", ""),
            data.get("intent", ""),
            [dict(item) for item in data.get("stages", [])],
            data.get("status", "Pending"),
            dict(data.get("validation", {})),
            data.get("simulation_report_id", ""),
            data.get("approval_status", "Pending"),
            data.get("communication_session_id", ""),
            data.get("monitoring_state_id", ""),
            data.get("report_id", ""),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class ProductionRuntimeReport:
    """Persistent production manufacturing runtime report."""

    pipeline_id: str = ""
    manufacturing_job_id: str = ""
    summary: str = ""
    execution_summary: dict = field(default_factory=dict)
    simulation_summary: dict = field(default_factory=dict)
    performance_metrics: dict = field(default_factory=dict)
    machine_utilization: dict = field(default_factory=dict)
    material_utilization: dict = field(default_factory=dict)
    cycle_statistics: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    @property
    def valid(self):
        """Return whether the report has no blocking production errors."""

        return not self.errors

    def to_dict(self):
        """Return JSON-safe report data."""

        return {
            "id": self.id,
            "pipeline_id": self.pipeline_id,
            "manufacturing_job_id": self.manufacturing_job_id,
            "summary": self.summary,
            "execution_summary": dict(self.execution_summary),
            "simulation_summary": dict(self.simulation_summary),
            "performance_metrics": dict(self.performance_metrics),
            "machine_utilization": dict(self.machine_utilization),
            "material_utilization": dict(self.material_utilization),
            "cycle_statistics": dict(self.cycle_statistics),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "recommendations": list(self.recommendations),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create runtime report from persisted data."""

        data = data or {}
        return ProductionRuntimeReport(
            data.get("pipeline_id", ""),
            data.get("manufacturing_job_id", ""),
            data.get("summary", ""),
            dict(data.get("execution_summary", {})),
            dict(data.get("simulation_summary", {})),
            dict(data.get("performance_metrics", {})),
            dict(data.get("machine_utilization", {})),
            dict(data.get("material_utilization", {})),
            dict(data.get("cycle_statistics", {})),
            list(data.get("warnings", [])),
            list(data.get("errors", [])),
            list(data.get("recommendations", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


class ManufacturingEngine:
    """Workspace-owned manufacturing planning and orchestration facade."""

    OPERATION_TYPES = {
        "Setup",
        "Facing",
        "Profiling",
        "Pocketing",
        "2D Profile",
        "2D Pocket",
        "Adaptive Clearing",
        "Slot Milling",
        "Contour",
        "Chamfer",
        "Drilling",
        "Peck Drilling",
        "Counterbore",
        "Countersink",
        "Boring",
        "Reaming",
        "Rigid Tapping",
        "Thread Milling",
        "Engraving",
        "Vector Cut",
        "Vector Engrave",
        "Raster Engrave",
        "Laser Cut",
        "Plasma Cut",
        "Waterjet Cut",
        "Inspection",
        "Assembly",
        "Cleaning",
        "Packaging",
    }

    COORDINATE_SYSTEM_TYPES = {
        "Machine Coordinate System",
        "Work Coordinate System",
        "Part Coordinate System",
        "Fixture Coordinate System",
    }

    DEFAULT_WORK_OFFSETS = ("G54", "G55", "G56", "G57")

    CONTROLLERS = {
        "Generic ISO G-code",
        "GenericGCode",
        "Fanuc",
        "Haas",
        "LinuxCNC",
        "Mach3",
        "Mach4",
        "GRBL",
        "Marlin",
        "Klipper",
        "FluidNC",
        "GRBL Laser",
        "Plasma controller metadata",
        "Waterjet controller metadata",
    }

    SHEET_PROCESSES = {"Laser", "Plasma", "Waterjet"}

    SHEET_PROGRAM_CONTROLLERS = {
        "Generic G-code",
        "GRBL Laser",
        "LinuxCNC",
        "Mach3",
        "Mach4",
        "Plasma controller metadata",
        "Waterjet controller metadata",
    }

    ROBOT_TYPES = {"6-axis", "SCARA", "Delta", "Cartesian", "Custom"}

    ROBOT_FRAME_TYPES = {
        "World",
        "Machine Coordinate System",
        "Robot Base",
        "User Frame",
        "Tool Frame",
        "Work Offset",
    }

    ROBOT_MOTION_TYPES = {"Joint", "Linear", "Circular", "Spline", "Approach", "Retract", "Safe"}

    ROBOT_PROGRAM_CONTROLLERS = {
        "Generic Robot Program",
        "ABB RAPID foundation",
        "KUKA KRL foundation",
        "Fanuc TP metadata",
        "URScript foundation",
        "Yaskawa INFORM metadata",
    }

    SIMULATION_PROCESS_TYPES = {"CNC", "Additive", "Sheet", "Robotics"}

    COMMUNICATION_PROTOCOLS = {
        "Klipper",
        "Marlin",
        "GRBL",
        "LinuxCNC",
        "Mach3",
        "Mach4",
        "Fanuc foundation",
        "Haas foundation",
        "Siemens foundation",
    }

    CONNECTION_TYPES = {"USB", "Serial", "TCP/IP", "Network"}

    COMMUNICATION_COMMANDS = {
        "connect",
        "disconnect",
        "status",
        "upload",
        "start",
        "pause",
        "resume",
        "stop",
        "emergency_stop",
    }

    def __init__(self, workspace):

        self.workspace = workspace
        self.state = ManufacturingEngineState()
        self.execution_plans = []
        self.cam_plans = []
        self.toolpaths = []
        self.generated_programs = []
        self.additive_parameters = []
        self.build_plate_layouts = []
        self.additive_slices = []
        self.additive_print_files = []
        self.sheet_parameters = []
        self.sheet_material_profiles = []
        self.sheet_nest_layouts = []
        self.sheet_cut_paths = []
        self.sheet_programs = []
        self.robot_profiles = []
        self.robot_frames = []
        self.robot_motions = []
        self.robot_trajectories = []
        self.robot_programs = []
        self.simulation_jobs = []
        self.simulation_sessions = []
        self.simulation_collision_reports = []
        self.simulation_verification_reports = []
        self.simulation_reports = []
        self.machine_connections = []
        self.communication_sessions = []
        self.communication_queue = []
        self.machine_monitoring = []
        self.communication_events = []
        self.recent_machines = []
        self.production_runtime_state = ProductionRuntimeState()
        self.production_runtime_events = []
        self.production_runtime_health_history = []
        self.production_execution_pipelines = []
        self.production_runtime_reports = []
        self.production_recovery_checkpoints = []
        self.production_performance_cache = {}
        self.coordinate_systems = []
        self.work_offsets = []
        self.last_validation = ManufacturingValidationReport()
        self.last_diagnostics = ManufacturingEngineDiagnostics()
        self.validation_count = 0
        self.planning_count = 0
        self.load_from_settings()

    @property
    def product_manager(self):
        """Return the existing ProductManager owned by Workspace."""

        return self.workspace.product_manager

    @property
    def machine_workspace(self):
        """Return the existing Machine Workspace owned by Workspace."""

        return getattr(self.workspace, "machine_workspace", None)

    def initialize(self):
        """Initialize manufacturing orchestration metadata."""

        self.state.initialized = True
        self._ensure_default_offsets()
        self._save()
        return self

    def initialize_production_runtime(self):
        """Initialize the production runtime inside the existing Manufacturing Engine."""

        self.initialize()
        self.production_runtime_state.initialized = True
        self.production_runtime_state.status = "Ready"
        self.production_runtime_state.heartbeat = self._timestamp()
        self.production_runtime_state.metadata.update({
            "runtime_owner": "ManufacturingEngine",
            "orchestration_metadata_only": True,
            "subsystems": list(self._production_subsystem_status().keys()),
        })
        self._record_production_event("Runtime Initialized", "Production Manufacturing Runtime initialized.")
        self.production_runtime_health()
        self._save()
        return self.production_runtime_state

    def production_runtime_health(self):
        """Return health metadata for existing manufacturing subsystems."""

        self.production_runtime_state.heartbeat = self._timestamp()
        subsystem_status = self._production_subsystem_status()
        dependencies = {
            "workspace": self.workspace is not None,
            "machine_workspace": self.machine_workspace is not None,
            "manufacturing_engine": self.state.initialized,
            "command_system": hasattr(self.workspace, "command_manager"),
            "ai_manufacturing_assistant": self._ai_manufacturing_assistant_ready(),
        }
        failures = []
        for name, ready in dependencies.items():
            if not ready:
                failures.append(f"Missing dependency: {name}.")
        if not any(subsystem_status.values()):
            failures.append("No manufacturing subsystem output is available yet.")
        recovery_plan = []
        if not self.state.initialized:
            recovery_plan.append("Initialize Manufacturing Engine.")
        if not self.machine_connections and (self.generated_programs or self.additive_print_files or self.sheet_programs or self.robot_programs):
            recovery_plan.append("Create a machine connection before production dispatch.")
        if not self.simulation_reports and (self.generated_programs or self.additive_print_files or self.sheet_programs or self.robot_programs):
            recovery_plan.append("Run manufacturing simulation before production dispatch.")
        resources = {
            "jobs": len(self.product_manager.cam_jobs),
            "execution_plans": len(self.execution_plans),
            "generated_programs": len(self.generated_programs) + len(self.additive_print_files) + len(self.sheet_programs) + len(self.robot_programs),
            "simulation_reports": len(self.simulation_reports),
            "machine_connections": len(self.machine_connections),
            "communication_sessions": len(self.communication_sessions),
            "queue_items": len(self.communication_queue),
        }
        status = "Healthy" if not failures else "Degraded"
        health = ProductionRuntimeHealth(
            status,
            subsystem_status,
            dependencies,
            resources,
            failures,
            recovery_plan,
            self.production_runtime_state.heartbeat,
            metadata={"checked_at": self.production_runtime_state.heartbeat},
        )
        self.production_runtime_health_history.append(health)
        self._record_production_event("Health", f"Production runtime health is {status}.", "Info" if health.valid else "Warning")
        self._save()
        return health

    def optimize_production_runtime(self):
        """Return deterministic runtime optimization metadata without replacing subsystems."""

        queue = sorted(self.communication_queue, key=lambda item: (-item.priority, item.metadata.get("queued_at", "")))
        metrics = {
            "job_scheduling": {
                "queued_jobs": len(queue),
                "highest_priority": queue[0].priority if queue else 0,
                "ordered_job_ids": [item.manufacturing_job_id for item in queue],
            },
            "queue_optimization": {
                "running_sessions": len([item for item in self.communication_sessions if item.state == "Running"]),
                "recoverable_queue_items": len([item for item in self.communication_queue if item.status in {"Queued", "Uploaded", "Paused"}]),
            },
            "execution_prioritization": {
                "simulation_ready_jobs": len({report.manufacturing_job_id for report in self.simulation_reports if report.valid}),
                "program_ready_jobs": len(self._program_ready_job_ids()),
            },
            "lazy_initialization": {
                "runtime_initialized": self.production_runtime_state.initialized,
                "manufacturing_engine_initialized": self.state.initialized,
            },
            "resource_reuse": {
                "machine_connections": len(self.machine_connections),
                "cached_performance_metrics": bool(self.production_performance_cache),
            },
        }
        self.production_performance_cache = {
            **metrics,
            "updated_at": self._timestamp(),
            "orchestration_metadata_only": True,
        }
        self._record_production_event("Performance", "Production runtime optimization metadata refreshed.")
        self._save()
        return dict(self.production_performance_cache)

    def validate_production_runtime(self, job=None, require_execution=False):
        """Validate production readiness using existing Manufacturing Engine data."""

        health = self.production_runtime_health()
        manufacturing_validation = self.validate()
        target_job = self.job_for(job) if job is not None else None
        errors = list(health.failures) + list(manufacturing_validation.errors)
        warnings = list(manufacturing_validation.warnings)
        if target_job is not None:
            program = self._communication_program_for_job(target_job)
            simulation = next((report for report in self.simulation_reports if report.manufacturing_job_id == target_job.id and report.valid), None)
            if program is None:
                errors.append("Production execution requires an existing generated manufacturing program.")
            if simulation is None:
                errors.append("Production execution requires an existing valid simulation report.")
            if require_execution and not self._connection_for_job(target_job):
                errors.append("Production execution requires an existing machine connection.")
        elif require_execution:
            errors.append("Production execution requires an existing manufacturing job.")
        report = {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "health": health.to_dict(),
            "manufacturing_engine": manufacturing_validation.to_dict(),
            "job_id": getattr(target_job, "id", ""),
        }
        self._record_production_event("Validation", "Production runtime validation completed.", "Info" if report["valid"] else "Warning", getattr(target_job, "id", ""))
        self._save()
        return report

    def execute_production_pipeline(self, job, connection=None, intent="Manufacturing Production", approved=False, approved_by=""):
        """Execute the production pipeline by coordinating existing subsystem APIs."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Production pipeline requires an existing manufacturing job.")
        self.initialize_production_runtime()
        validation = self.validate_production_runtime(target_job, require_execution=True)
        simulation = next((report for report in self.simulation_reports if report.manufacturing_job_id == target_job.id and report.valid), None)
        target_connection = self._connection_for(connection) if connection is not None else self._connection_for_job(target_job)
        stages = self._production_pipeline_stages(validation, simulation, approved, target_connection)
        pipeline = ProductionExecutionPipeline(
            manufacturing_job_id=target_job.id,
            intent=intent,
            stages=stages,
            status="Blocked" if not validation["valid"] else ("Awaiting Approval" if not approved else "Ready"),
            validation=validation,
            simulation_report_id=getattr(simulation, "id", ""),
            approval_status="Approved" if approved else "Pending",
            metadata={
                "approved_by": approved_by,
                "created_at": self._timestamp(),
                "existing_subsystems_only": True,
            },
        )
        self.production_execution_pipelines.append(pipeline)
        self.production_runtime_state.active_pipeline_id = pipeline.id
        if validation["valid"] and approved:
            if target_connection.state != "Connected":
                self.connect_machine(target_connection)
            queue_item = self.queue_machine_job(target_job, target_connection, priority=10, production_runtime=True)
            session = self.upload_machine_job(queue_item)
            self.start_machine_job(session)
            monitoring = self._monitoring_for(target_connection)
            pipeline.communication_session_id = session.id
            pipeline.monitoring_state_id = getattr(monitoring, "id", "")
            pipeline.status = "Running"
            self.production_runtime_state.status = "Running"
            self._record_production_event("Execution", "Production pipeline started existing Communication Engine session.", "Info", target_job.id, session.id)
        else:
            self._record_production_event("Execution", f"Production pipeline status: {pipeline.status}.", "Warning" if not validation["valid"] else "Info", target_job.id)
        report = self.generate_production_report(pipeline)
        pipeline.report_id = report.id
        self._save()
        return pipeline

    def recover_production_runtime(self):
        """Create recovery metadata and restore safe runtime lifecycle state."""

        checkpoint = {
            "id": str(uuid4()),
            "timestamp": self._timestamp(),
            "runtime_state": self.production_runtime_state.to_dict(),
            "queue_items": len(self.communication_queue),
            "communication_sessions": len(self.communication_sessions),
            "connections": len(self.machine_connections),
        }
        for connection in self.machine_connections:
            if connection.state in {"Running", "Paused"} and not any(session.connection_id == connection.id and session.state in {"Running", "Paused"} for session in self.communication_sessions):
                connection.state = "Disconnected"
        self.production_recovery_checkpoints.append(checkpoint)
        self.production_runtime_state.status = "Recovered"
        self.production_runtime_state.heartbeat = self._timestamp()
        self._record_production_event("Recovery", "Production runtime recovery metadata recorded.")
        self.production_runtime_health()
        self._save()
        return checkpoint

    def shutdown_production_runtime(self, graceful=True):
        """Gracefully stop runtime lifecycle metadata without deleting manufacturing data."""

        if graceful:
            for connection in self.machine_connections:
                if connection.state in {"Connected", "Idle"}:
                    self.disconnect_machine(connection)
        self.production_runtime_state.status = "Shutdown"
        self.production_runtime_state.heartbeat = self._timestamp()
        self._record_production_event("Shutdown", "Production runtime shutdown completed.")
        self._save()
        return self.production_runtime_state

    def generate_production_report(self, pipeline=None):
        """Generate a persistent production runtime report."""

        target_pipeline = pipeline if isinstance(pipeline, ProductionExecutionPipeline) else next((item for item in self.production_execution_pipelines if item.id == pipeline), None)
        job_id = getattr(target_pipeline, "manufacturing_job_id", "")
        simulation = next((report for report in self.simulation_reports if report.manufacturing_job_id == job_id), None)
        session = next((item for item in self.communication_sessions if item.id == getattr(target_pipeline, "communication_session_id", "")), None)
        health = self.production_runtime_health()
        performance = self.optimize_production_runtime()
        errors = list(getattr(target_pipeline, "validation", {}).get("errors", [])) if target_pipeline else []
        warnings = list(getattr(target_pipeline, "validation", {}).get("warnings", [])) if target_pipeline else []
        report = ProductionRuntimeReport(
            pipeline_id=getattr(target_pipeline, "id", ""),
            manufacturing_job_id=job_id,
            summary=f"Production runtime report for job {job_id or 'workspace'}.",
            execution_summary={
                "pipeline_status": getattr(target_pipeline, "status", self.production_runtime_state.status),
                "communication_session_id": getattr(session, "id", ""),
                "session_state": getattr(session, "state", ""),
                "approval_status": getattr(target_pipeline, "approval_status", ""),
            },
            simulation_summary=simulation.to_dict() if simulation is not None else {},
            performance_metrics=performance,
            machine_utilization={
                "connections": len(self.machine_connections),
                "running_sessions": len([item for item in self.communication_sessions if item.state == "Running"]),
                "monitoring_states": len(self.machine_monitoring),
            },
            material_utilization=dict(getattr(simulation, "material_usage", {})) if simulation is not None else {},
            cycle_statistics={
                "estimated_cycle_time": getattr(simulation, "estimated_cycle_time", 0.0) if simulation else 0.0,
                "estimated_print_time": getattr(simulation, "estimated_print_time", 0.0) if simulation else 0.0,
                "estimated_cutting_time": getattr(simulation, "estimated_cutting_time", 0.0) if simulation else 0.0,
            },
            warnings=warnings + list(getattr(simulation, "warnings", [])) if simulation else warnings,
            errors=errors,
            recommendations=list(health.recovery_plan),
            metadata={
                "generated_at": self._timestamp(),
                "runtime_health": health.status,
                "release": "1.7",
            },
        )
        self.production_runtime_reports.append(report)
        self._record_production_event("Report", "Production runtime report generated.", "Info" if report.valid else "Warning", job_id)
        self._save()
        return report

    def create_job(
        self,
        name,
        description="",
        machine_profile=None,
        material=None,
        revision="A",
        version="1.0",
        status="Pending",
        targets=None,
    ):
        """Create a manufacturing job backed by existing CAM/Product records."""

        if not name:
            raise ValueError("Manufacturing job name is required.")
        if self._name_exists(self.product_manager.cam_jobs, name):
            raise ValueError(f"Duplicate manufacturing job name: {name}")
        if status not in MANUFACTURING_STATES:
            raise ValueError(f"Unsupported manufacturing state: {status}")

        machine_profile_id = getattr(machine_profile, "id", machine_profile) or ""
        material_id = getattr(material, "id", material) or ""
        metadata = CAMMetadata(
            description=description,
            status=status,
            properties={
                "manufacturing_engine": True,
                "machine_profile_id": machine_profile_id,
                "material_id": material_id,
                "revision": revision,
                "created_at": self._timestamp(),
                "version": version,
            },
        )
        document = self.product_manager.cam_manager.active_document()
        if document is None:
            document = self.product_manager.cam_manager.create_document("Manufacturing Engine")
        job = self.product_manager.cam_manager.create_job(
            document=document,
            name=name,
            targets=targets or [],
            metadata=metadata,
        )
        self.product_manager.manufacturing_job_manager.create_job(
            name=f"{name} Manufacturing Record",
            cam_job=job,
            profile=None,
            status=status,
        )
        self.activate_job(job)
        self._save()
        return job

    def edit_job(self, job, **changes):
        """Edit manufacturing job metadata without changing geometry."""

        target = self.job_for(job)
        if target is None:
            raise ValueError("Manufacturing job was not found.")
        if "name" in changes:
            new_name = changes["name"]
            if new_name != target.name and self._name_exists(self.product_manager.cam_jobs, new_name):
                raise ValueError(f"Duplicate manufacturing job name: {new_name}")
            target.name = new_name
        if "description" in changes:
            target.metadata.description = changes["description"]
        if "status" in changes:
            self.transition_job(target, changes["status"])
        properties = target.metadata.properties
        for key in ("machine_profile", "material"):
            if key in changes:
                properties[f"{key}_id"] = getattr(changes[key], "id", changes[key]) or ""
        for key in ("revision", "version"):
            if key in changes:
                properties[key] = changes[key]
        for key, value in changes.get("metadata", {}).items():
            properties[key] = value
        self._save()
        return target

    def duplicate_job(self, job, name):
        """Duplicate a manufacturing job and its planning metadata."""

        source = self.job_for(job)
        if source is None:
            raise ValueError("Manufacturing job was not found.")
        if self._name_exists(self.product_manager.cam_jobs, name):
            raise ValueError(f"Duplicate manufacturing job name: {name}")
        clone = self.create_job(
            name,
            description=source.metadata.description,
            machine_profile=source.metadata.properties.get("machine_profile_id", ""),
            material=source.metadata.properties.get("material_id", ""),
            revision=source.metadata.properties.get("revision", "A"),
            version=source.metadata.properties.get("version", "1.0"),
            status=source.metadata.status,
            targets=list(source.target_ids),
        )
        for setup in self.product_manager.manufacturing_setup_manager.setups_for_job(source):
            copied_setup = self.create_stock(
                clone,
                stock_type=setup.stock.stock_type,
                dimensions=self._vector_to_dict(setup.stock.dimensions),
                material=setup.stock.material_id,
                allowance=setup.metadata.properties.get("stock_metadata", {}).get("allowance", 0.0),
                notes=setup.metadata.properties.get("stock_metadata", {}).get("notes", ""),
            )
            copied_setup.fixture = FixtureDefinition.from_dict(setup.fixture.to_dict())
            copied_setup.fixture.id = str(uuid4())
        for operation in self.operations_for_job(source):
            self.create_operation(
                clone,
                operation.operation_type,
                name=operation.name,
                dependencies=list(operation.metadata.properties.get("dependencies", [])),
                estimated_duration=operation.metadata.properties.get("estimated_duration", 0.0),
                required_machine=operation.metadata.properties.get("required_machine_id", ""),
                required_tool=operation.parameters.tool_id,
                required_material=operation.metadata.properties.get("required_material_id", ""),
                status=operation.metadata.status,
                metadata=dict(operation.metadata.properties.get("manufacturing_metadata", {})),
            )
        self._save()
        return clone

    def delete_job(self, job):
        """Delete a manufacturing job through existing ProductManager unlinking."""

        target = self.job_for(job)
        if target is None:
            return False
        job_id = target.id
        for plan in list(self.execution_plans):
            if plan.job_id == job_id:
                self.execution_plans.remove(plan)
        if self.state.active_job_id == job_id:
            self.state.active_job_id = ""
        result = self.product_manager.cam_manager.delete_job(target)
        self._save()
        return result

    def activate_job(self, job):
        """Activate one manufacturing job."""

        target = self.job_for(job)
        if target is None:
            raise ValueError("Manufacturing job was not found.")
        self.product_manager.cam_manager.activate_job(target)
        self.state.active_job_id = target.id
        self._save()
        return target

    def suspend_job(self, job):
        """Move a job to Blocked state."""

        return self.transition_job(job, "Blocked")

    def resume_job(self, job):
        """Resume a blocked job into Pending state for replanning."""

        return self.transition_job(job, "Pending")

    def archive_job(self, job):
        """Archive a manufacturing job."""

        return self.transition_job(job, "Archived")

    def transition_job(self, job, status):
        """Apply deterministic manufacturing state transitions."""

        target = self.job_for(job)
        if target is None:
            raise ValueError("Manufacturing job was not found.")
        if status not in MANUFACTURING_STATES:
            raise ValueError(f"Unsupported manufacturing state: {status}")
        current = target.metadata.status
        if current != status and status not in VALID_STATE_TRANSITIONS.get(current, set()):
            raise ValueError(f"Invalid manufacturing state transition: {current} -> {status}")
        target.metadata.status = status
        target.metadata.properties["updated_at"] = self._timestamp()
        self._save()
        return target

    def create_operation(
        self,
        job,
        operation_type,
        name=None,
        dependencies=None,
        estimated_duration=0.0,
        required_machine=None,
        required_tool=None,
        required_material=None,
        status="Pending",
        feeds=None,
        speeds=None,
        coolant=None,
        depth=0.0,
        allowance=0.0,
        stepover=0.0,
        stepdown=0.0,
        tolerance=0.01,
        cut_geometry=None,
        machine_overrides=None,
        metadata=None,
    ):
        """Create an ordered manufacturing operation; no toolpath is generated."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Operation requires an existing manufacturing job.")
        normalized = self._operation_type(operation_type)
        if any(operation.name == (name or f"{normalized} Operation") and operation.job_id == target_job.id for operation in self.product_manager.cam_operations):
            raise ValueError(f"Duplicate operation name in job: {name or f'{normalized} Operation'}")
        required_tool_id = getattr(required_tool, "id", required_tool) or ""
        required_machine_id = getattr(required_machine, "id", required_machine) or target_job.metadata.properties.get("machine_profile_id", "")
        required_material_id = getattr(required_material, "id", required_material) or target_job.metadata.properties.get("material_id", "")
        parameters = OperationParameters(tool_id=required_tool_id)
        setup = self._first_setup(target_job)
        operation = self.product_manager.operation_manager.create_operation(
            target_job,
            setup=setup,
            operation_type=self._product_operation_type(normalized),
            name=name or f"{normalized} Operation",
            parameters=parameters,
            tool=required_tool,
            order=len(self.operations_for_job(target_job)),
        )
        operation.operation_type = normalized
        operation.metadata.status = status
        operation.metadata.properties.update({
            "manufacturing_engine": True,
            "dependencies": [getattr(item, "id", item) for item in dependencies or []],
            "estimated_duration": float(estimated_duration),
            "required_machine_id": required_machine_id,
            "required_tool_id": required_tool_id,
            "required_material_id": required_material_id,
            "feeds": dict(feeds or {}),
            "speeds": dict(speeds or {}),
            "coolant": dict(coolant or {}),
            "depth": float(depth),
            "allowance": float(allowance),
            "stepover": float(stepover),
            "stepdown": float(stepdown),
            "tolerance": float(tolerance),
            "cut_geometry": dict(cut_geometry or {}),
            "machine_overrides": dict(machine_overrides or {}),
            "manufacturing_metadata": dict(metadata or {}),
        })
        self._save()
        return operation

    def plan_cam_job(self, job):
        """Build a CAM plan for a manufacturing job."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("CAM plan requires an existing manufacturing job.")
        operations = self.operations_for_job(target_job)
        plan = CAMPlan(
            job_id=target_job.id,
            operation_ids=[operation.id for operation in operations],
            strategy_metadata={
                operation.id: self._strategy_for_operation(operation)
                for operation in operations
            },
            tool_ids=[
                operation.metadata.properties.get("required_tool_id", "") or operation.parameters.tool_id
                for operation in operations
                if operation.metadata.properties.get("required_tool_id", "") or operation.parameters.tool_id
            ],
            metadata={
                "created_at": self._timestamp(),
                "operation_count": len(operations),
            },
        )
        self._validate_cam_plan(target_job, plan)
        self.cam_plans = [item for item in self.cam_plans if item.job_id != target_job.id]
        self.cam_plans.append(plan)
        self._save()
        return plan

    def calculate_cutting_parameters(self, operation, tool=None, material=None, overrides=None):
        """Calculate production CNC cutting parameters from operation/tool metadata."""

        target = self._operation_for(operation)
        if target is None:
            raise ValueError("Cutting parameters require an existing operation.")
        properties = target.metadata.properties
        target_tool = self._tool_for(tool or properties.get("required_tool_id") or target.parameters.tool_id)
        diameter = max(float(getattr(target_tool, "diameter", 0.0) or 0.0), 0.1)
        flutes = max(int(getattr(target_tool, "flutes", 0) or 2), 1)
        feed_overrides = dict(properties.get("feeds", {}))
        speed_overrides = dict(properties.get("speeds", {}))
        explicit = dict(overrides or {})
        explicit.update(properties.get("machine_overrides", {}))

        surface_speed = float(speed_overrides.get("surface_speed", explicit.get("surface_speed", 120.0)))
        chip_load = float(feed_overrides.get("chip_load", explicit.get("chip_load", max(diameter * 0.01, 0.02))))
        rpm = float(speed_overrides.get("rpm", explicit.get("rpm", (1000.0 * surface_speed) / (pi * diameter))))
        feed_rate = float(feed_overrides.get("feed_rate", explicit.get("feed_rate", rpm * flutes * chip_load)))
        plunge_rate = float(feed_overrides.get("plunge_rate", explicit.get("plunge_rate", feed_rate * 0.35)))
        stepover = float(properties.get("stepover", 0.0) or explicit.get("stepover", diameter * 0.4))
        stepdown = float(properties.get("stepdown", 0.0) or explicit.get("stepdown", diameter * 0.5))
        depth = abs(float(properties.get("depth", 0.0) or stepdown))
        tool_engagement = min(max(stepover / diameter, 0.0), 1.0)
        path_length = float(properties.get("cut_geometry", {}).get("estimated_path_length", 0.0) or self._estimated_operation_path_length(target))
        cycle_estimate = path_length / max(feed_rate, 1.0)
        material_removal = path_length * stepover * max(depth, stepdown)
        params = CNCCuttingParameters(
            rpm=rpm,
            feed_rate=feed_rate,
            plunge_rate=plunge_rate,
            stepover=stepover,
            stepdown=stepdown,
            surface_speed=surface_speed,
            chip_load=chip_load,
            material_removal_estimate=material_removal,
            cycle_estimate=cycle_estimate,
            tool_engagement=tool_engagement,
            overrides=explicit,
        )
        target.parameters.feed_rate = feed_rate
        target.parameters.spindle_speed = rpm
        target.parameters.stepover = stepover
        target.parameters.step_down = stepdown
        target.parameters.depth = depth
        return params

    def generate_toolpath(self, operation):
        """Generate and persist a native CNC toolpath for one operation."""

        target = self._operation_for(operation)
        if target is None:
            raise ValueError("Toolpath generation requires an existing operation.")
        tool = self._tool_for(target.metadata.properties.get("required_tool_id") or target.parameters.tool_id)
        params = self.calculate_cutting_parameters(target, tool=tool)
        moves = self._generate_operation_moves(target, params)
        toolpath = CNCToolpath(
            operation_id=target.id,
            job_id=target.job_id,
            strategy=self._strategy_for_operation(target),
            tool_id=getattr(tool, "id", "") or target.parameters.tool_id,
            moves=moves,
            cutting_parameters=params,
            metadata={
                "operation_type": target.operation_type,
                "generated_at": self._timestamp(),
            },
        )
        self._validate_toolpath(target, toolpath)
        toolpath.status = "Generated" if toolpath.valid else "Blocked"
        self.toolpaths = [item for item in self.toolpaths if item.operation_id != target.id]
        self.toolpaths.append(toolpath)
        self._save()
        return toolpath

    def generate_toolpaths(self, job):
        """Generate native CNC toolpaths for every operation in a job."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Toolpath generation requires an existing job.")
        self.plan_cam_job(target_job)
        generated = [self.generate_toolpath(operation) for operation in self.operations_for_job(target_job)]
        self._save()
        return generated

    def generate_gcode(self, job, controller="Generic ISO G-code", program_name=None):
        """Generate controller-specific native G-code for a manufacturing job."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("G-code generation requires an existing manufacturing job.")
        controller_name = self._normalize_controller(controller)
        if not any(path.job_id == target_job.id for path in self.toolpaths):
            self.generate_toolpaths(target_job)
        toolpaths = [
            path for path in self.toolpaths
            if path.job_id == target_job.id
        ]
        if not toolpaths:
            raise ValueError("G-code generation requires at least one generated toolpath.")
        gcode_lines = self._post_lines(target_job, toolpaths, controller_name, program_name or self._program_name(target_job.name))
        program = CNCProgram(
            job_id=target_job.id,
            controller=controller_name,
            program_name=program_name or self._program_name(target_job.name),
            gcode="\n".join(gcode_lines),
            toolpath_ids=[path.id for path in toolpaths],
            statistics={
                "lines": len(gcode_lines),
                "toolpaths": len(toolpaths),
                "moves": sum(len(path.moves) for path in toolpaths),
                "tool_changes": len({path.tool_id for path in toolpaths if path.tool_id}),
                "estimated_cycle_time": sum(path.cutting_parameters.cycle_estimate for path in toolpaths),
                "estimated_material_removal": sum(path.cutting_parameters.material_removal_estimate for path in toolpaths),
            },
            metadata={
                "generated_at": self._timestamp(),
                "post_processor": controller_name,
            },
        )
        self._validate_program(program)
        self.generated_programs = [item for item in self.generated_programs if item.job_id != target_job.id or item.controller != controller_name]
        self.generated_programs.append(program)
        self._save()
        return program

    def create_additive_job(
        self,
        name,
        technology="FDM",
        machine_profile=None,
        material=None,
        model_dimensions=None,
        quantity=1,
        description="",
    ):
        """Create an additive manufacturing job using existing ProductManager records."""

        if technology not in {"FDM", "SLA"}:
            raise ValueError(f"Unsupported additive technology: {technology}")
        job = self.create_job(
            name,
            description=description,
            machine_profile=machine_profile,
            material=material,
            status="Pending",
        )
        job.metadata.properties.update({
            "additive_manufacturing": True,
            "technology": technology,
            "model_dimensions": dict(model_dimensions or {"x": 20.0, "y": 20.0, "z": 10.0}),
            "quantity": int(quantity),
        })
        profile = self._create_slice_profile(job, technology, machine_profile, material)
        slice_job = self.product_manager.slicer_manager.create_job(
            job,
            profile=profile,
            name=f"{name} Slice Job",
            metadata=None,
            enabled=True,
        )
        slice_job.metadata.technology = technology
        slice_job.metadata.status = "Planned"
        self.product_manager.slicer_manager.create_operation(
            slice_job,
            targets=[],
            profile=profile,
            name=f"{technology} Slice Operation",
        )
        self._save()
        return job

    def configure_print_parameters(self, job, **kwargs):
        """Create or update additive print parameters for a job."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Print parameters require an existing additive job.")
        technology = kwargs.get("technology") or target_job.metadata.properties.get("technology", "FDM")
        params = AdditivePrintParameters(
            technology=technology,
            layer_height=float(kwargs.get("layer_height", 0.2 if technology == "FDM" else 0.05)),
            nozzle_diameter=float(kwargs.get("nozzle_diameter", 0.4)),
            extrusion_width=float(kwargs.get("extrusion_width", kwargs.get("nozzle_diameter", 0.4) * 1.125)),
            line_count=int(kwargs.get("line_count", 2)),
            wall_thickness=float(kwargs.get("wall_thickness", 0.8)),
            top_thickness=float(kwargs.get("top_thickness", 0.8)),
            bottom_thickness=float(kwargs.get("bottom_thickness", 0.8)),
            infill_percentage=float(kwargs.get("infill_percentage", 20.0)),
            infill_pattern=kwargs.get("infill_pattern", "Grid"),
            print_speed=float(kwargs.get("print_speed", 60.0)),
            travel_speed=float(kwargs.get("travel_speed", 120.0)),
            acceleration=float(kwargs.get("acceleration", 1000.0)),
            jerk=float(kwargs.get("jerk", 8.0)),
            temperature=dict(kwargs.get("temperature", {})),
            cooling=dict(kwargs.get("cooling", {})),
            resin=dict(kwargs.get("resin", {})),
            metadata={
                "job_id": target_job.id,
                "adaptive_layers": bool(kwargs.get("adaptive_layers", False)),
                "retraction": dict(kwargs.get("retraction", {"enabled": technology == "FDM", "distance": 1.0, "speed": 35.0})),
                "z_hop": dict(kwargs.get("z_hop", {"enabled": technology == "FDM", "height": 0.2})),
                "sequential_printing": bool(kwargs.get("sequential_printing", False)),
                "hollowing": dict(kwargs.get("hollowing", {})),
                "drain_holes": list(kwargs.get("drain_holes", [])),
                "orientation": dict(kwargs.get("orientation", {})),
                "exposure": dict(kwargs.get("exposure", {})),
                "lift": dict(kwargs.get("lift", {})),
                "resin_profile": dict(kwargs.get("resin_profile", {})),
                "material_metadata": dict(kwargs.get("material_metadata", {})),
            },
        )
        self.additive_parameters = [item for item in self.additive_parameters if item.metadata.get("job_id") != target_job.id]
        self.additive_parameters.append(params)
        self._sync_slice_profile(target_job, params)
        self._save()
        return params

    def plan_build_plate(self, job, placements=None, build_volume=None, auto_arrange=True, brim=False, skirt=True, raft=False, prime_tower=None):
        """Create additive build plate layout metadata."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Build plate planning requires an existing additive job.")
        dimensions = target_job.metadata.properties.get("model_dimensions", {"x": 20.0, "y": 20.0, "z": 10.0})
        quantity = int(target_job.metadata.properties.get("quantity", 1))
        volume = dict(build_volume or self._machine_build_volume(target_job) or {"x": 220.0, "y": 220.0, "z": 220.0})
        items = [dict(item) for item in placements or []]
        if auto_arrange or not items:
            items = self._auto_arrange(quantity, dimensions, volume)
        layout = BuildPlateLayout(
            job_id=target_job.id,
            placements=items,
            build_volume=volume,
            brim=bool(brim),
            skirt=bool(skirt),
            raft=bool(raft),
            prime_tower=dict(prime_tower or {}),
            metadata={
                "auto_arrange": bool(auto_arrange),
                "rotation_supported": True,
                "scaling_validation": True,
                "multiple_model_job": quantity > 1,
            },
        )
        self._validate_build_layout(layout, dimensions)
        self.build_plate_layouts = [item for item in self.build_plate_layouts if item.job_id != target_job.id]
        self.build_plate_layouts.append(layout)
        self._save()
        return layout

    def generate_supports(self, job, support_type="Automatic", density=15.0, pattern="Grid", angle=45.0, interface_layers=2, blockers=None, enforcers=None):
        """Generate support metadata for additive slicing."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Support generation requires an existing additive job.")
        dimensions = target_job.metadata.properties.get("model_dimensions", {"x": 20.0, "y": 20.0, "z": 10.0})
        regions = []
        if support_type != "None" and density > 0.0:
            regions.append({
                "type": support_type,
                "x": dimensions.get("x", 20.0) * 0.5,
                "y": dimensions.get("y", 20.0) * 0.5,
                "height": dimensions.get("z", 10.0) * 0.75,
                "angle": float(angle),
                "density": float(density),
            })
        return AdditiveSupportPlan(
            enabled=bool(regions),
            support_type=support_type,
            density=float(density),
            pattern=pattern,
            angle=float(angle),
            interface_layers=int(interface_layers),
            blockers=list(blockers or []),
            enforcers=list(enforcers or []),
            support_regions=regions,
            metadata={
                "job_id": target_job.id,
                "tree_supports": support_type == "Tree",
                "organic_supports": support_type == "Organic",
                "custom_supports": support_type == "Custom",
            },
        )

    def slice_fdm(self, job, parameters=None, support_plan=None):
        """Generate native FDM slice layers and extrusion paths."""

        return self._slice_additive(job, "FDM", parameters, support_plan)

    def slice_sla(self, job, parameters=None, support_plan=None):
        """Generate native SLA slice layers, exposure metadata and resin estimates."""

        return self._slice_additive(job, "SLA", parameters, support_plan)

    def generate_print_file(self, job, format="Generic G-code", file_name=None):
        """Generate and persist a native additive print file."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Print file generation requires an existing additive job.")
        slice_result = self._slice_for_job(target_job)
        if slice_result is None:
            technology = target_job.metadata.properties.get("technology", "FDM")
            slice_result = self.slice_fdm(target_job) if technology == "FDM" else self.slice_sla(target_job)
        normalized = self._normalize_print_format(format)
        content = self._generate_print_content(target_job, slice_result, normalized)
        print_file = AdditivePrintFile(
            job_id=target_job.id,
            slice_result_id=slice_result.id,
            format=normalized,
            file_name=file_name or self._print_file_name(target_job.name, normalized),
            content=content,
            statistics={
                "layers": len(slice_result.layers),
                "estimated_print_time": slice_result.estimated_print_time,
                "material_usage": dict(slice_result.material_usage),
                "bytes": len(content.encode("utf-8")),
            },
            metadata={
                "generated_at": self._timestamp(),
                "technology": slice_result.technology,
            },
        )
        self._validate_print_file(print_file)
        self.additive_print_files = [
            item for item in self.additive_print_files
            if item.job_id != target_job.id or item.format != normalized
        ]
        self.additive_print_files.append(print_file)
        self._save()
        return print_file

    def create_sheet_job(
        self,
        name,
        process="Laser",
        machine_profile=None,
        material=None,
        sheet_size=None,
        thickness=0.0,
        parts=None,
        description="",
    ):
        """Create a sheet manufacturing job through the existing Manufacturing Engine."""

        if process not in self.SHEET_PROCESSES:
            raise ValueError(f"Unsupported sheet manufacturing process: {process}")
        job = self.create_job(
            name,
            description=description,
            machine_profile=machine_profile,
            material=material,
            status="Pending",
        )
        sheet = dict(sheet_size or {"x": 600.0, "y": 400.0})
        part_records = [self._normalize_sheet_part(part, index) for index, part in enumerate(parts or [])]
        if not part_records:
            part_records = [self._normalize_sheet_part({"name": f"{name} Part", "width": 100.0, "height": 60.0, "quantity": 1}, 0)]
        job.metadata.properties.update({
            "sheet_manufacturing": True,
            "sheet_process": process,
            "sheet_size": sheet,
            "sheet_thickness": float(thickness),
            "sheet_parts": part_records,
        })
        self.configure_sheet_material_profile(
            job,
            thickness=thickness,
            sheet_size=sheet,
            compatibility={
                "laser": process == "Laser",
                "plasma": process == "Plasma",
                "waterjet": process == "Waterjet",
            },
        )
        self._create_sheet_product_records(job, process, material, thickness)
        self._save()
        return job

    def configure_sheet_material_profile(self, job, thickness=0.0, sheet_size=None, compatibility=None, recommendations=None, quality=None, **metadata):
        """Create or update a sheet material profile using the existing material reference."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Sheet material profile requires an existing manufacturing job.")
        profile = SheetMaterialProfile(
            job_id=target_job.id,
            material_id=target_job.metadata.properties.get("material_id", ""),
            thickness=float(thickness),
            sheet_size=dict(sheet_size or target_job.metadata.properties.get("sheet_size", {"x": 600.0, "y": 400.0})),
            compatibility=dict(compatibility or {}),
            recommendations=dict(recommendations or {}),
            quality=dict(quality or {}),
            metadata=dict(metadata or {}),
        )
        self.sheet_material_profiles = [item for item in self.sheet_material_profiles if item.job_id != target_job.id]
        self.sheet_material_profiles.append(profile)
        self._save()
        return profile

    def configure_sheet_parameters(self, job, operation_type=None, **kwargs):
        """Configure cutting, kerf, pierce, power, speed and process metadata."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Sheet cutting parameters require an existing manufacturing job.")
        process = kwargs.get("process") or target_job.metadata.properties.get("sheet_process", "Laser")
        if process not in self.SHEET_PROCESSES:
            raise ValueError(f"Unsupported sheet manufacturing process: {process}")
        params = SheetCutParameters(
            process=process,
            operation_type=operation_type or kwargs.get("operation_type") or ("Vector Cut" if process == "Laser" else f"{process} Cut"),
            kerf_width=float(kwargs.get("kerf_width", 0.12 if process == "Laser" else 1.0 if process == "Plasma" else 0.8)),
            compensation=kwargs.get("compensation", "Outside"),
            power=float(kwargs.get("power", 60.0 if process == "Laser" else 45.0 if process == "Plasma" else 55.0)),
            speed=float(kwargs.get("speed", 1200.0 if process == "Laser" else 900.0 if process == "Plasma" else 700.0)),
            pass_count=int(kwargs.get("pass_count", 1)),
            pierce=dict(kwargs.get("pierce", {"delay": 0.2 if process == "Laser" else 0.8, "height": 3.0})),
            lead_in=dict(kwargs.get("lead_in", {"length": 3.0, "angle": 45.0})),
            lead_out=dict(kwargs.get("lead_out", {"length": 2.0, "angle": 45.0})),
            gas=dict(kwargs.get("gas", {"air_assist": process == "Laser"})),
            height_control=dict(kwargs.get("height_control", {"enabled": process == "Plasma", "cut_height": 1.5})),
            consumable=dict(kwargs.get("consumable", {})),
            waterjet=dict(kwargs.get("waterjet", {"quality": 3, "low_pressure_pierce": process == "Waterjet", "high_pressure_cutting": process == "Waterjet"})),
            raster=dict(kwargs.get("raster", {"enabled": operation_type == "Raster Engrave"})),
            metadata={
                "job_id": target_job.id,
                "corner_optimization": bool(kwargs.get("corner_optimization", True)),
                "corner_slowdown": bool(kwargs.get("corner_slowdown", process == "Plasma")),
                "travel_optimization": bool(kwargs.get("travel_optimization", True)),
                "quality_level": kwargs.get("quality_level", kwargs.get("quality", "Production")),
                "taper_metadata": dict(kwargs.get("taper", {})),
                "kerf_table": dict(kwargs.get("kerf_table", {})),
                "tool_diameter": float(kwargs.get("tool_diameter", kwargs.get("kerf_width", 0.0) or 0.0)),
            },
        )
        self.sheet_parameters = [item for item in self.sheet_parameters if item.metadata.get("job_id") != target_job.id or item.process != process]
        self.sheet_parameters.append(params)
        self._sync_sheet_product_operations(target_job, params)
        self._save()
        return params

    def nest_sheet(self, job, parts=None, sheet_size=None, spacing=2.0, manual_placements=None, rotation_optimization=True, priority_ordering=True):
        """Generate a production sheet nesting layout with collision detection."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Sheet nesting requires an existing manufacturing job.")
        sheet = dict(sheet_size or target_job.metadata.properties.get("sheet_size", {"x": 600.0, "y": 400.0}))
        part_records = [self._normalize_sheet_part(part, index) for index, part in enumerate(parts or target_job.metadata.properties.get("sheet_parts", []))]
        placements = [dict(item) for item in manual_placements or []]
        if not placements:
            placements = self._auto_nest_sheet_parts(part_records, sheet, float(spacing), bool(rotation_optimization))
        layout = SheetNestLayout(
            job_id=target_job.id,
            sheet_size=sheet,
            placements=placements,
            spacing=float(spacing),
            metadata={
                "automatic_nesting": not bool(manual_placements),
                "manual_nesting": bool(manual_placements),
                "rotation_optimization": bool(rotation_optimization),
                "spacing_rules": {"spacing": float(spacing)},
                "part_grouping": self._part_groups(part_records),
                "priority_ordering": bool(priority_ordering),
            },
        )
        self._validate_sheet_nest(layout)
        layout.utilization = self._sheet_utilization(layout)
        layout.remnants = self._sheet_remnants(layout)
        self._sync_nesting_product_records(target_job, layout)
        self.sheet_nest_layouts = [item for item in self.sheet_nest_layouts if item.job_id != target_job.id]
        self.sheet_nest_layouts.append(layout)
        self._save()
        return layout

    def generate_sheet_toolpaths(self, job, parameters=None, layout=None):
        """Generate native 2D cutting paths for sheet manufacturing."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Sheet toolpath generation requires an existing manufacturing job.")
        params = parameters or self._sheet_parameters_for_job(target_job) or self.configure_sheet_parameters(target_job)
        nest = layout or self._sheet_layout_for_job(target_job) or self.nest_sheet(target_job)
        paths = []
        for order, placement in enumerate(sorted(nest.placements, key=lambda item: (item.get("priority", 0), item.get("y", 0.0), item.get("x", 0.0)))):
            outline = self._placement_outline(placement)
            compensated = self._apply_kerf_compensation(outline, params)
            lead_in = self._lead_path(compensated, params.lead_in, incoming=True)
            lead_out = self._lead_path(compensated, params.lead_out, incoming=False)
            pierce = [compensated[0]] if compensated else []
            travel = [compensated[0]] if compensated else []
            estimated_time = self._estimate_sheet_cut_time(compensated, params)
            operation = self._sheet_operation_for(target_job, params)
            cut_path = SheetCutPath(
                job_id=target_job.id,
                operation_id=getattr(operation, "id", ""),
                process=params.process,
                path_type=params.operation_type,
                points=outline,
                compensated_points=compensated,
                lead_in=lead_in,
                lead_out=lead_out,
                pierce_points=pierce,
                travel_moves=travel,
                kerf_width=params.kerf_width,
                estimated_time=estimated_time,
                metadata={
                    "placement_id": placement.get("id", ""),
                    "part_id": placement.get("part_id", ""),
                    "cut_sequence": order,
                    "corner_optimization": bool(params.metadata.get("corner_optimization", True)),
                    "corner_slowdown": bool(params.metadata.get("corner_slowdown", False)),
                    "travel_optimization": bool(params.metadata.get("travel_optimization", True)),
                    "compensation": params.compensation,
                },
            )
            self._validate_sheet_cut_path(cut_path)
            paths.append(cut_path)
        self.sheet_cut_paths = [item for item in self.sheet_cut_paths if item.job_id != target_job.id]
        self.sheet_cut_paths.extend(paths)
        self._save()
        return paths

    def generate_sheet_program(self, job, controller="Generic G-code", program_name=None):
        """Generate and persist a controller-ready sheet manufacturing program."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Sheet program generation requires an existing manufacturing job.")
        normalized = self._normalize_sheet_controller(controller)
        cut_paths = [path for path in self.sheet_cut_paths if path.job_id == target_job.id]
        if not cut_paths:
            cut_paths = self.generate_sheet_toolpaths(target_job)
        content = self._sheet_program_content(target_job, cut_paths, normalized, program_name or self._program_name(target_job.name))
        program = SheetProgram(
            job_id=target_job.id,
            controller=normalized,
            program_name=program_name or self._program_name(target_job.name),
            content=content,
            cut_path_ids=[path.id for path in cut_paths],
            statistics={
                "lines": len(content.splitlines()),
                "cut_paths": len(cut_paths),
                "pierces": sum(len(path.pierce_points) for path in cut_paths),
                "estimated_cutting_time": sum(path.estimated_time for path in cut_paths),
                "material_utilization": (self._sheet_layout_for_job(target_job) or SheetNestLayout()).utilization,
                "kerf_width": max([path.kerf_width for path in cut_paths] or [0.0]),
            },
            metadata={
                "generated_at": self._timestamp(),
                "sheet_process": target_job.metadata.properties.get("sheet_process", ""),
            },
        )
        self._validate_sheet_program(program)
        self.sheet_programs = [item for item in self.sheet_programs if item.job_id != target_job.id or item.controller != normalized]
        self.sheet_programs.append(program)
        self._save()
        return program

    def create_robot_profile(
        self,
        name,
        robot_type="6-axis",
        machine_profile=None,
        payload=0.0,
        reach=0.0,
        joint_limits=None,
        tcp=None,
        base_frame=None,
        tool_frame=None,
        **metadata,
    ):
        """Create a reusable robot profile using existing machine profile references."""

        if robot_type not in self.ROBOT_TYPES:
            raise ValueError(f"Unsupported robot type: {robot_type}")
        if any(profile.name == name for profile in self.robot_profiles):
            raise ValueError(f"Duplicate robot profile name: {name}")
        profile = RobotProfile(
            name=name,
            robot_type=robot_type,
            machine_profile_id=getattr(machine_profile, "id", machine_profile) or "",
            payload=float(payload),
            reach=float(reach),
            joint_limits=[dict(item) for item in joint_limits or self._default_joint_limits(robot_type)],
            tcp=dict(tcp or {"x": 0.0, "y": 0.0, "z": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}),
            base_frame=dict(base_frame or {"x": 0.0, "y": 0.0, "z": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}),
            tool_frame=dict(tool_frame or {"x": 0.0, "y": 0.0, "z": 100.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}),
            metadata={
                "robot_library": True,
                "payload_metadata": float(payload),
                "reach_metadata": float(reach),
                **dict(metadata or {}),
            },
        )
        self.robot_profiles.append(profile)
        self._save()
        return profile

    def create_robot_job(self, name, robot_profile, process="Pick & Place", machine_profile=None, material=None, description=""):
        """Create a robot job backed by the existing Manufacturing Engine job record."""

        profile = self._robot_profile_for(robot_profile)
        if profile is None:
            raise ValueError("Robot job requires an existing robot profile.")
        job = self.create_job(
            name,
            description=description,
            machine_profile=machine_profile or profile.machine_profile_id,
            material=material,
            status="Pending",
        )
        job.metadata.properties.update({
            "robotics_motion": True,
            "robot_profile_id": profile.id,
            "robot_process": process,
            "process_metadata": {
                "pick_place": process == "Pick & Place",
                "machine_tending": process == "Machine Tending",
                "welding": process == "Welding foundation",
                "painting": process == "Painting foundation",
                "dispensing": process == "Dispensing foundation",
                "inspection": process == "Inspection foundation",
                "additive_deposition": process == "Additive deposition foundation",
            },
        })
        self.define_robot_frame(job, "World", "World")
        self.define_robot_frame(job, "Robot Base", "Robot Base", origin=profile.base_frame)
        self.define_robot_frame(job, "Tool Frame", "Tool Frame", origin=profile.tool_frame)
        self._save()
        return job

    def define_robot_frame(self, job, name, frame_type="User Frame", origin=None, rotation=None, parent_frame=None, **metadata):
        """Define a persistent robot coordinate frame."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Robot frame requires an existing robot job.")
        if frame_type not in self.ROBOT_FRAME_TYPES:
            raise ValueError(f"Unsupported robot frame type: {frame_type}")
        existing = next((item for item in self.robot_frames if item.job_id == target_job.id and item.name == name), None)
        frame = existing or RobotFrame()
        frame.job_id = target_job.id
        frame.name = name
        frame.frame_type = frame_type
        frame.origin = dict(origin or {"x": 0.0, "y": 0.0, "z": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0})
        frame.rotation = dict(rotation or {"rx": frame.origin.get("rx", 0.0), "ry": frame.origin.get("ry", 0.0), "rz": frame.origin.get("rz", 0.0)})
        frame.parent_frame_id = getattr(parent_frame, "id", parent_frame) or ""
        frame.transform = self._frame_transform(frame.origin, frame.rotation)
        frame.metadata = {
            "persistent_coordinate_definition": True,
            "frame_transformations": True,
            **dict(metadata or {}),
        }
        if existing is None:
            self.robot_frames.append(frame)
        self._save()
        return frame

    def plan_robot_motion(
        self,
        job,
        motion_type="Joint",
        target=None,
        joints=None,
        frame=None,
        velocity=100.0,
        acceleration=100.0,
        jerk=0.0,
        blend_radius=0.0,
        process=None,
        metadata=None,
    ):
        """Plan a robot or machine motion command without communicating with hardware."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Robot motion requires an existing robot job.")
        if motion_type not in self.ROBOT_MOTION_TYPES:
            raise ValueError(f"Unsupported robot motion type: {motion_type}")
        profile = self._robot_profile_for_job(target_job)
        motion = RobotMotionCommand(
            job_id=target_job.id,
            motion_type=motion_type,
            target=dict(target or {}),
            joints=list(joints or []),
            frame_id=getattr(frame, "id", frame) or self._default_frame_id(target_job),
            velocity=float(velocity),
            acceleration=float(acceleration),
            jerk=float(jerk),
            blend_radius=float(blend_radius),
            process=dict(process or target_job.metadata.properties.get("process_metadata", {})),
            order=len([item for item in self.robot_motions if item.job_id == target_job.id]),
            metadata={
                "waypoint_planning": True,
                "motion_optimization": True,
                "forward_kinematics": self.forward_kinematics(profile, joints or []),
                "inverse_kinematics_foundation": self.inverse_kinematics(profile, target or {}),
                **dict(metadata or {}),
            },
        )
        self._validate_robot_motion(motion, profile)
        self.robot_motions.append(motion)
        self._save()
        return motion

    def generate_robot_trajectory(self, job, motions=None):
        """Generate a persistent native robot trajectory from planned motions."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Robot trajectory generation requires an existing robot job.")
        motion_items = sorted(
            [self._robot_motion_for(item) for item in motions] if motions is not None else [item for item in self.robot_motions if item.job_id == target_job.id],
            key=lambda item: item.order,
        )
        motion_items = [item for item in motion_items if item is not None]
        waypoints = []
        joint_path = []
        linear_path = []
        circular_path = []
        previous = None
        for motion in motion_items:
            waypoint = self._motion_waypoint(motion)
            waypoints.append(waypoint)
            joint_path.append(list(motion.joints))
            if motion.motion_type in {"Linear", "Approach", "Retract", "Safe", "Spline"}:
                linear_path.extend(self._interpolate_linear(previous, waypoint))
            if motion.motion_type == "Circular":
                circular_path.extend(self._interpolate_circular(previous, waypoint, motion))
            previous = waypoint
        trajectory = RobotTrajectory(
            job_id=target_job.id,
            motion_ids=[motion.id for motion in motion_items],
            waypoints=waypoints,
            joint_path=joint_path,
            linear_path=linear_path,
            circular_path=circular_path,
            estimated_cycle_time=sum(self._motion_time(motion) for motion in motion_items),
            metadata={
                "trajectory_ordering": True,
                "joint_interpolation": True,
                "linear_interpolation": True,
                "circular_interpolation": bool(circular_path),
                "motion_optimization": True,
            },
        )
        self._validate_robot_trajectory(trajectory)
        self.robot_trajectories = [item for item in self.robot_trajectories if item.job_id != target_job.id]
        self.robot_trajectories.append(trajectory)
        self._save()
        return trajectory

    def forward_kinematics(self, robot_profile, joints):
        """Return deterministic forward kinematics foundation metadata."""

        profile = self._robot_profile_for(robot_profile)
        values = [float(value) for value in joints or []]
        reach = float(getattr(profile, "reach", 0.0) or 0.0)
        x = sum(values[:2]) * 0.5 if values else 0.0
        y = sum(values[2:4]) * 0.5 if len(values) > 2 else 0.0
        z = min(max(reach - sum(abs(value) for value in values) * 0.01, 0.0), reach) if reach else 0.0
        return {
            "pose": {"x": x, "y": y, "z": z, "rx": values[3] if len(values) > 3 else 0.0, "ry": values[4] if len(values) > 4 else 0.0, "rz": values[5] if len(values) > 5 else 0.0},
            "joint_count": len(values),
            "within_limits": self._joints_within_limits(profile, values),
        }

    def inverse_kinematics(self, robot_profile, target):
        """Return inverse kinematics foundation metadata without robot execution."""

        profile = self._robot_profile_for(robot_profile)
        pose = dict(target or {})
        distance = self._pose_distance(pose)
        reachable = distance <= float(getattr(profile, "reach", 0.0) or 0.0)
        joint_count = len(getattr(profile, "joint_limits", []) or [])
        seed = distance / max(joint_count, 1)
        solution = [seed for _ in range(joint_count)]
        return {
            "reachable": reachable,
            "distance": distance,
            "solution": solution,
            "singularity_metadata": {"near_singularity": distance < 1.0 or distance > float(getattr(profile, "reach", 0.0) or 0.0) * 0.98},
            "joint_limit_metadata": {"within_limits": self._joints_within_limits(profile, solution)},
        }

    def generate_robot_program(self, job, controller="Generic Robot Program", program_name=None):
        """Generate and persist a production robot program."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Robot program generation requires an existing robot job.")
        normalized = self._normalize_robot_controller(controller)
        trajectory = self._robot_trajectory_for_job(target_job) or self.generate_robot_trajectory(target_job)
        content = self._robot_program_content(target_job, trajectory, normalized, program_name or self._program_name(target_job.name))
        program = RobotProgram(
            job_id=target_job.id,
            controller=normalized,
            program_name=program_name or self._program_name(target_job.name),
            content=content,
            trajectory_id=trajectory.id,
            statistics={
                "lines": len(content.splitlines()),
                "motions": len(trajectory.motion_ids),
                "waypoints": len(trajectory.waypoints),
                "estimated_cycle_time": trajectory.estimated_cycle_time,
                "robot_utilization": min(trajectory.estimated_cycle_time / 3600.0, 1.0),
            },
            metadata={
                "generated_at": self._timestamp(),
                "robot_controller": normalized,
            },
        )
        self._validate_robot_program(program)
        self.robot_programs = [item for item in self.robot_programs if item.job_id != target_job.id or item.controller != normalized]
        self.robot_programs.append(program)
        self._save()
        return program

    def create_simulation_job(self, job, process_type=None, settings=None, name=None, **metadata):
        """Create a manufacturing simulation job for an existing manufacturing job."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Simulation requires an existing manufacturing job.")
        resolved_process = process_type or self._simulation_process_for_job(target_job)
        if resolved_process not in self.SIMULATION_PROCESS_TYPES:
            raise ValueError(f"Unsupported simulation process type: {resolved_process}")
        simulation = SimulationJob(
            manufacturing_job_id=target_job.id,
            process_type=resolved_process,
            name=name or f"{target_job.name} Simulation",
            settings={
                "replay": True,
                "collision_checking": True,
                "verification": True,
                **dict(settings or {}),
            },
            metadata={
                "created_at": self._timestamp(),
                "simulation_engine": True,
                "virtual_execution_only": True,
                "no_machine_communication": True,
                **dict(metadata or {}),
            },
        )
        self._validate_simulation_job(simulation)
        self.simulation_jobs = [
            item for item in self.simulation_jobs
            if item.manufacturing_job_id != target_job.id or item.process_type != resolved_process
        ]
        self.simulation_jobs.append(simulation)
        self._save()
        return simulation

    def run_simulation(self, simulation_job):
        """Run virtual manufacturing replay without modifying geometry or machines."""

        simulation = self._simulation_job_for(simulation_job)
        if simulation is None:
            raise ValueError("Simulation job was not found.")
        job = self.job_for(simulation.manufacturing_job_id)
        if job is None:
            raise ValueError("Simulation references a missing manufacturing job.")
        replay = self._simulation_replay_steps(job, simulation.process_type)
        material_usage = self._simulation_material_usage(job, simulation.process_type, replay)
        tool_usage = self._simulation_tool_usage(job, simulation.process_type, replay)
        estimated_time = self._simulation_estimated_time(simulation.process_type, replay)
        session = SimulationSession(
            simulation_job_id=simulation.id,
            manufacturing_job_id=job.id,
            process_type=simulation.process_type,
            replay_steps=replay,
            progress=1.0 if replay else 0.0,
            estimated_time=estimated_time,
            material_usage=material_usage,
            tool_usage=tool_usage,
            status="Completed" if replay else "Blocked",
            metadata={
                "started_at": self._timestamp(),
                "completed_at": self._timestamp(),
                "virtual_execution_only": True,
                "replay_statistics": {
                    "steps": len(replay),
                    "rapid_steps": len([step for step in replay if step.get("replay_type") == "Rapid"]),
                    "cut_steps": len([step for step in replay if step.get("replay_type") in {"Cut", "Extrusion", "Laser", "Plasma", "Waterjet"}]),
                    "layer_steps": len([step for step in replay if step.get("replay_type") == "Layer"]),
                    "waypoint_steps": len([step for step in replay if step.get("replay_type") == "Waypoint"]),
                },
            },
        )
        self._validate_simulation_session(session)
        self.simulation_sessions = [item for item in self.simulation_sessions if item.simulation_job_id != simulation.id]
        self.simulation_sessions.append(session)
        self._save()
        return session

    def check_simulation_collisions(self, simulation_job):
        """Check virtual manufacturing replay for planning-level collisions."""

        simulation = self._simulation_job_for(simulation_job)
        if simulation is None:
            raise ValueError("Simulation job was not found.")
        job = self.job_for(simulation.manufacturing_job_id)
        session = self._simulation_session_for(simulation) or self.run_simulation(simulation)
        collisions, warnings, categories = self._simulation_collision_data(job, simulation, session)
        report = SimulationCollisionReport(
            simulation_job_id=simulation.id,
            manufacturing_job_id=simulation.manufacturing_job_id,
            collisions=collisions,
            warnings=warnings,
            checked_categories=categories,
            metadata={
                "checked_at": self._timestamp(),
                "collision_engine": True,
            },
        )
        self.simulation_collision_reports = [item for item in self.simulation_collision_reports if item.simulation_job_id != simulation.id]
        self.simulation_collision_reports.append(report)
        self._save()
        return report

    def verify_simulation(self, simulation_job):
        """Verify manufacturing readiness for a virtual simulation."""

        simulation = self._simulation_job_for(simulation_job)
        if simulation is None:
            raise ValueError("Simulation job was not found.")
        session = self._simulation_session_for(simulation) or self.run_simulation(simulation)
        collision = self._simulation_collision_report_for(simulation) or self.check_simulation_collisions(simulation)
        checks = self._simulation_verification_checks(simulation, session, collision)
        errors = [name for name, passed in checks.items() if not passed]
        verification = SimulationVerificationReport(
            simulation_job_id=simulation.id,
            manufacturing_job_id=simulation.manufacturing_job_id,
            checks=checks,
            ready=not errors,
            validation_errors=[f"Simulation verification failed: {name}" for name in errors],
            validation_warnings=list(collision.warnings),
            metadata={
                "verified_at": self._timestamp(),
                "verification_engine": True,
            },
        )
        self.simulation_verification_reports = [item for item in self.simulation_verification_reports if item.simulation_job_id != simulation.id]
        self.simulation_verification_reports.append(verification)
        self._save()
        return verification

    def generate_simulation_report(self, simulation_job):
        """Generate and persist a manufacturing simulation report."""

        simulation = self._simulation_job_for(simulation_job)
        if simulation is None:
            raise ValueError("Simulation job was not found.")
        session = self._simulation_session_for(simulation) or self.run_simulation(simulation)
        collision = self._simulation_collision_report_for(simulation) or self.check_simulation_collisions(simulation)
        verification = self._simulation_verification_report_for(simulation) or self.verify_simulation(simulation)
        report = SimulationReport(
            simulation_job_id=simulation.id,
            manufacturing_job_id=simulation.manufacturing_job_id,
            process_type=simulation.process_type,
            summary=f"{simulation.process_type} simulation completed with {len(session.replay_steps)} replay steps.",
            estimated_cycle_time=session.estimated_time if simulation.process_type in {"CNC", "Robotics"} else 0.0,
            estimated_print_time=session.estimated_time if simulation.process_type == "Additive" else 0.0,
            estimated_cutting_time=session.estimated_time if simulation.process_type == "Sheet" else 0.0,
            material_usage=dict(session.material_usage),
            tool_usage=dict(session.tool_usage),
            warnings=list(session.validation_warnings) + list(collision.warnings) + list(verification.validation_warnings),
            collisions=[dict(item) for item in collision.collisions],
            verification_status="Ready" if verification.valid else "Blocked",
            validation_results={
                "simulation_job_valid": simulation.valid,
                "session_valid": session.valid,
                "collision_free": collision.valid,
                "verification_ready": verification.valid,
            },
            metadata={
                "generated_at": self._timestamp(),
                "simulation_reporting": True,
                "history": {
                    "simulation_job_id": simulation.id,
                    "session_id": session.id,
                    "collision_report_id": collision.id,
                    "verification_report_id": verification.id,
                },
            },
        )
        self.simulation_reports = [item for item in self.simulation_reports if item.simulation_job_id != simulation.id]
        self.simulation_reports.append(report)
        self._save()
        return report

    def create_machine_connection(
        self,
        machine_profile,
        protocol=None,
        connection_type="Serial",
        parameters=None,
        timeout_seconds=30.0,
        **metadata,
    ):
        """Create persistent machine connection metadata for an existing profile."""

        profile = self.product_manager.machine_library_manager.profile_for(getattr(machine_profile, "id", machine_profile) or "")
        if profile is None:
            raise ValueError("Machine connection requires an existing machine profile.")
        resolved_protocol = protocol or self._protocol_for_profile(profile)
        if resolved_protocol not in self.COMMUNICATION_PROTOCOLS:
            raise ValueError(f"Unsupported communication protocol: {resolved_protocol}")
        if connection_type not in self.CONNECTION_TYPES:
            raise ValueError(f"Unsupported connection type: {connection_type}")
        connection = MachineConnection(
            machine_profile_id=profile.id,
            protocol=resolved_protocol,
            connection_type=connection_type,
            parameters=dict(parameters or {}),
            capabilities=self._communication_capabilities(profile, resolved_protocol),
            timeout_seconds=float(timeout_seconds),
            metadata={
                "communication_engine": True,
                "profile_name": getattr(profile, "name", ""),
                "connection_parameters": dict(parameters or {}),
                **dict(metadata or {}),
            },
        )
        self._validate_machine_connection(connection)
        self.machine_connections = [
            item for item in self.machine_connections
            if item.machine_profile_id != profile.id or item.protocol != resolved_protocol
        ]
        self.machine_connections.append(connection)
        self._log_communication_event(connection, "Connection Created", f"{resolved_protocol} connection registered.")
        self._save()
        return connection

    def connect_machine(self, connection):
        """Open a validated machine connection lifecycle record."""

        target = self._connection_for(connection)
        if target is None:
            raise ValueError("Machine connection was not found.")
        self._validate_machine_connection(target)
        if not target.valid:
            raise ValueError("; ".join(target.validation_errors))
        target.state = "Connected"
        target.last_heartbeat = self._timestamp()
        target.metadata["adapter_status"] = self._protocol_adapter_status(target, "connect")
        self._update_monitoring(target, machine_state="Idle", progress=0.0)
        self._remember_machine(target)
        self._log_communication_event(target, "Connected", f"Connected using {target.protocol}.")
        self._save()
        return target

    def disconnect_machine(self, connection, safe=True):
        """Disconnect a machine connection after safe idle verification."""

        target = self._connection_for(connection)
        if target is None:
            raise ValueError("Machine connection was not found.")
        if safe and not self._machine_idle(target):
            raise ValueError("Safe disconnect requires the machine to be idle, stopped or disconnected.")
        target.state = "Disconnected"
        target.metadata["adapter_status"] = self._protocol_adapter_status(target, "disconnect")
        self._update_monitoring(target, machine_state="Disconnected")
        self._log_communication_event(target, "Disconnected", "Machine connection closed.")
        self._save()
        return target

    def heartbeat_machine(self, connection):
        """Record connection heartbeat and timeout metadata."""

        target = self._connection_for(connection)
        if target is None:
            raise ValueError("Machine connection was not found.")
        target.last_heartbeat = self._timestamp()
        target.metadata["heartbeat"] = {"received": True, "timestamp": target.last_heartbeat}
        self._log_communication_event(target, "Heartbeat", "Machine heartbeat received.")
        self._save()
        return target

    def queue_machine_job(self, job, connection, priority=0, max_retries=1, **metadata):
        """Queue a validated manufacturing job for machine dispatch."""

        target_job = self.job_for(job)
        target_connection = self._connection_for(connection)
        if target_job is None:
            raise ValueError("Queued machine job requires an existing manufacturing job.")
        if target_connection is None:
            raise ValueError("Queued machine job requires an existing machine connection.")
        self._validate_dispatch_job(target_job, target_connection)
        item = CommunicationJobQueueItem(
            manufacturing_job_id=target_job.id,
            connection_id=target_connection.id,
            priority=int(priority),
            max_retries=int(max_retries),
            metadata={
                "queued_at": self._timestamp(),
                "retry_metadata": {"max_retries": int(max_retries)},
                **dict(metadata or {}),
            },
        )
        self.communication_queue.append(item)
        self.communication_queue.sort(key=lambda queue_item: (-queue_item.priority, queue_item.metadata.get("queued_at", "")))
        self._log_communication_event(target_connection, "Job Queued", f"Queued job {target_job.name}.", manufacturing_job_id=target_job.id)
        self._save()
        return item

    def upload_machine_job(self, queue_item):
        """Upload an existing generated manufacturing program to a connected machine."""

        item = self._queue_item_for(queue_item)
        if item is None:
            raise ValueError("Communication queue item was not found.")
        connection = self._connection_for(item.connection_id)
        job = self.job_for(item.manufacturing_job_id)
        if connection is None or job is None:
            raise ValueError("Queued communication job is incomplete.")
        if connection.state != "Connected":
            raise ValueError("Machine must be connected before upload.")
        program = self._communication_program_for_job(job)
        if program is None:
            raise ValueError("Machine communication requires an existing generated manufacturing program.")
        item.uploaded_program_id = program.get("id", "")
        item.status = "Uploaded"
        connection.metadata["last_upload"] = self._protocol_payload(connection, "upload", program)
        session = CommunicationSession(
            connection_id=connection.id,
            manufacturing_job_id=job.id,
            protocol=connection.protocol,
            state="Uploaded",
            uploaded_program_id=item.uploaded_program_id,
            remaining_time=self._communication_estimated_time(job),
            metadata={
                "created_at": self._timestamp(),
                "program_type": program.get("type", ""),
                "program_name": program.get("name", ""),
                "job_dispatcher": True,
            },
        )
        self._validate_communication_session(session)
        self.communication_sessions = [
            existing for existing in self.communication_sessions
            if existing.connection_id != connection.id or existing.manufacturing_job_id != job.id
        ]
        self.communication_sessions.append(session)
        self._update_monitoring(connection, machine_state="Program Uploaded", current_job_id=job.id, remaining_time=session.remaining_time)
        self._log_communication_event(connection, "Job Uploaded", f"Uploaded program {program.get('name', '')}.", manufacturing_job_id=job.id, session_id=session.id)
        self._save()
        return session

    def start_machine_job(self, session):
        """Start an uploaded machine communication session."""

        target = self._communication_session_for(session)
        if target is None:
            raise ValueError("Communication session was not found.")
        connection = self._connection_for(target.connection_id)
        if connection is None or connection.state != "Connected":
            raise ValueError("Machine must be connected before job start.")
        self._validate_communication_session(target)
        if not target.valid:
            raise ValueError("; ".join(target.validation_errors))
        target.state = "Running"
        target.started_at = target.started_at or self._timestamp()
        target.progress = max(target.progress, 0.01)
        connection.state = "Running"
        connection.metadata["last_start"] = self._protocol_payload(connection, "start", {"session_id": target.id})
        self._set_queue_status(target.manufacturing_job_id, connection.id, "Running")
        self._update_monitoring(connection, machine_state="Running", current_job_id=target.manufacturing_job_id, progress=target.progress, remaining_time=target.remaining_time)
        self._log_communication_event(connection, "Job Started", "Machine job started.", manufacturing_job_id=target.manufacturing_job_id, session_id=target.id)
        self._save()
        return target

    def pause_machine_job(self, session):
        """Pause a running communication session."""

        target = self._communication_session_for(session)
        if target is None:
            raise ValueError("Communication session was not found.")
        connection = self._connection_for(target.connection_id)
        target.state = "Paused"
        if connection is not None:
            connection.state = "Paused"
            connection.metadata["last_pause"] = self._protocol_payload(connection, "pause", {"session_id": target.id})
            self._update_monitoring(connection, machine_state="Paused", current_job_id=target.manufacturing_job_id, progress=target.progress)
            self._log_communication_event(connection, "Job Paused", "Machine job paused.", manufacturing_job_id=target.manufacturing_job_id, session_id=target.id)
        self._set_queue_status(target.manufacturing_job_id, target.connection_id, "Paused")
        self._save()
        return target

    def resume_machine_job(self, session):
        """Resume a paused communication session."""

        target = self._communication_session_for(session)
        if target is None:
            raise ValueError("Communication session was not found.")
        connection = self._connection_for(target.connection_id)
        target.state = "Running"
        if connection is not None:
            connection.state = "Running"
            connection.metadata["last_resume"] = self._protocol_payload(connection, "resume", {"session_id": target.id})
            self._update_monitoring(connection, machine_state="Running", current_job_id=target.manufacturing_job_id, progress=target.progress)
            self._log_communication_event(connection, "Job Resumed", "Machine job resumed.", manufacturing_job_id=target.manufacturing_job_id, session_id=target.id)
        self._set_queue_status(target.manufacturing_job_id, target.connection_id, "Running")
        self._save()
        return target

    def stop_machine_job(self, session):
        """Stop a communication session without emergency-stop state."""

        target = self._communication_session_for(session)
        if target is None:
            raise ValueError("Communication session was not found.")
        connection = self._connection_for(target.connection_id)
        target.state = "Stopped"
        target.completed_at = self._timestamp()
        target.remaining_time = 0.0
        if connection is not None:
            connection.state = "Idle"
            connection.metadata["last_stop"] = self._protocol_payload(connection, "stop", {"session_id": target.id})
            self._update_monitoring(connection, machine_state="Stopped", current_job_id=target.manufacturing_job_id, progress=target.progress, remaining_time=0.0)
            self._log_communication_event(connection, "Job Stopped", "Machine job stopped.", manufacturing_job_id=target.manufacturing_job_id, session_id=target.id)
        self._set_queue_status(target.manufacturing_job_id, target.connection_id, "Stopped")
        self._save()
        return target

    def emergency_stop_machine(self, connection, reason="Operator emergency stop"):
        """Record emergency stop metadata for a machine connection."""

        target = self._connection_for(connection)
        if target is None:
            raise ValueError("Machine connection was not found.")
        target.state = "Emergency Stop"
        target.metadata["emergency_stop"] = {
            "reason": reason,
            "timestamp": self._timestamp(),
            "interface": "Communication Engine",
        }
        for session in self.communication_sessions:
            if session.connection_id == target.id and session.state in {"Running", "Paused", "Uploaded"}:
                session.state = "Emergency Stop"
                session.validation_warnings.append(reason)
        self._update_monitoring(target, machine_state="Emergency Stop")
        self._log_communication_event(target, "Emergency Stop", reason, severity="Critical")
        self._save()
        return target

    def machine_status(self, connection):
        """Return live monitoring metadata for a connection."""

        target = self._connection_for(connection)
        if target is None:
            raise ValueError("Machine connection was not found.")
        status = self._monitoring_for(target) or self._update_monitoring(target, machine_state=target.state)
        target.metadata["last_status"] = self._protocol_adapter_status(target, "status")
        self._save()
        return status

    def create_stock(self, job, stock_type="Box", dimensions=None, material=None, weight=0.0, origin=None, allowance=0.0, notes=""):
        """Create or update manufacturing stock metadata through an existing setup."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Stock requires an existing manufacturing job.")
        setup = self._first_setup(target_job)
        if setup is None:
            setup = self.product_manager.manufacturing_setup_manager.create_setup(
                target_job,
                stock_type=stock_type,
                material=material,
                name=f"{target_job.name} Setup",
            )
        setup.stock = StockDefinition(
            stock_type,
            list(target_job.target_ids),
            self._vector_from_dict(origin or {}),
            self._vector_from_dict(dimensions or {}),
            getattr(material, "id", material) or "",
        )
        setup.metadata.properties["stock_metadata"] = {
            "identifier": setup.stock.material_id or setup.id,
            "weight": float(weight),
            "allowance": float(allowance),
            "notes": notes,
            "validation": "Not Checked",
        }
        self._save()
        return setup

    def create_fixture(self, job, fixture_type, clamping_method="", reference_surfaces=None, alignment_method="", offsets=None, notes="", compatible_machines=None):
        """Create fixture metadata on the job setup."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Fixture requires an existing manufacturing job.")
        setup = self._ensure_setup(target_job)
        setup.fixture = FixtureDefinition(
            f"{fixture_type} Fixture",
            fixture_type,
            [getattr(item, "id", item) for item in reference_surfaces or []],
        )
        setup.metadata.properties["fixture_metadata"] = {
            "fixture_id": setup.fixture.id,
            "clamping_method": clamping_method,
            "alignment_method": alignment_method,
            "offsets": dict(offsets or {}),
            "notes": notes,
            "compatible_machines": [getattr(item, "id", item) for item in compatible_machines or []],
        }
        self._save()
        return setup.fixture

    def create_coordinate_system(self, job, name, system_type="Work Coordinate System", origin=None, x_axis=None, y_axis=None, z_axis=None, activate=False):
        """Create coordinate-system metadata for a manufacturing job."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Coordinate system requires an existing manufacturing job.")
        if system_type not in self.COORDINATE_SYSTEM_TYPES:
            raise ValueError(f"Unsupported coordinate system type: {system_type}")
        if any(item.get("job_id") == target_job.id and item.get("name") == name for item in self.coordinate_systems):
            raise ValueError(f"Duplicate coordinate system name: {name}")
        coordinate = WorkCoordinateSystem(
            name,
            self._vector_from_dict(origin or {}),
            self._vector_from_dict(x_axis or {"x": 1.0}),
            self._vector_from_dict(y_axis or {"y": 1.0}),
            self._vector_from_dict(z_axis or {"z": 1.0}),
        )
        record = {
            "id": coordinate.id,
            "job_id": target_job.id,
            "name": name,
            "system_type": system_type,
            "coordinate": coordinate.to_dict(),
            "active": bool(activate),
            "valid": True,
        }
        if activate:
            for item in self.coordinate_systems:
                if item.get("job_id") == target_job.id:
                    item["active"] = False
            self._ensure_setup(target_job).work_coordinate_system = coordinate
        self.coordinate_systems.append(record)
        self._save()
        return record

    def activate_coordinate_system(self, coordinate_system):
        """Activate a coordinate system and copy it onto the job setup."""

        record = self._coordinate_for(coordinate_system)
        if record is None:
            raise ValueError("Coordinate system was not found.")
        job = self.job_for(record["job_id"])
        if job is None:
            raise ValueError("Coordinate system references a missing job.")
        for item in self.coordinate_systems:
            if item.get("job_id") == job.id:
                item["active"] = False
        record["active"] = True
        self._ensure_setup(job).work_coordinate_system = WorkCoordinateSystem.from_dict(record["coordinate"])
        self._save()
        return record

    def create_work_offset(self, job, name="G54", translation=None, rotation=None, reference_system=None, metadata=None):
        """Create work-offset metadata; no controller communication occurs."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Work offset requires an existing manufacturing job.")
        if any(offset.name == name and offset.metadata.get("job_id") == target_job.id for offset in self.work_offsets):
            raise ValueError(f"Duplicate work offset name: {name}")
        reference_id = getattr(reference_system, "id", reference_system) or ""
        offset = ManufacturingWorkOffset(
            name,
            dict(translation or {}),
            dict(rotation or {}),
            reference_id,
            True,
            metadata={
                "job_id": target_job.id,
                **dict(metadata or {}),
            },
        )
        self.work_offsets.append(offset)
        self._save()
        return offset

    def build_execution_plan(self, job):
        """Build and validate a deterministic execution plan."""

        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Execution plan requires an existing manufacturing job.")
        operations = sorted(self.operations_for_job(target_job), key=lambda item: item.metadata.order)
        setups = self.product_manager.manufacturing_setup_manager.setups_for_job(target_job)
        coordinate_ids = [item["id"] for item in self.coordinate_systems if item.get("job_id") == target_job.id]
        offset_ids = [item.id for item in self.work_offsets if item.metadata.get("job_id") == target_job.id]
        plan = ManufacturingExecutionPlan(
            job_id=target_job.id,
            operation_ids=[operation.id for operation in operations],
            stock_id=getattr(setups[0].stock, "material_id", "") if setups else "",
            fixture_ids=[setup.fixture.id for setup in setups if getattr(setup, "fixture", None)],
            coordinate_system_ids=coordinate_ids,
            work_offset_ids=offset_ids,
            status="Ready",
            metadata={
                "operation_count": len(operations),
                "created_at": self._timestamp(),
            },
        )
        self._validate_plan(target_job, plan)
        plan.status = "Validated" if plan.valid else "Blocked"
        self.execution_plans = [item for item in self.execution_plans if item.job_id != target_job.id]
        self.execution_plans.append(plan)
        self.planning_count += 1
        self._save()
        return plan

    def validate(self):
        """Validate manufacturing metadata without executing manufacturing."""

        report = ManufacturingValidationReport()
        self._validate_duplicate_names(report, "manufacturing job", self.product_manager.cam_jobs)
        for job in self.product_manager.cam_jobs:
            self._validate_job(report, job)
            self._validate_sheet_job(report, job)
            self._validate_robot_job(report, job)
        for job in self.product_manager.cam_jobs:
            operations = self.operations_for_job(job)
            self._validate_operations(report, job, operations)
        for plan in self.execution_plans:
            job = self.job_for(plan.job_id)
            if job is None:
                report.add_error("Execution plan references a missing job.")
            else:
                self._validate_plan(job, plan)
        for plan in self.cam_plans:
            job = self.job_for(plan.job_id)
            if job is None:
                report.add_error("CAM plan references a missing job.")
            else:
                self._validate_cam_plan(job, plan)
        for toolpath in self.toolpaths:
            operation = self._operation_for(toolpath.operation_id)
            if operation is None:
                report.add_error("Toolpath references a missing operation.")
            elif not toolpath.valid:
                for error in toolpath.validation_errors:
                    report.add_error(error)
        for program in self.generated_programs:
            if not program.valid:
                for error in program.validation_errors:
                    report.add_error(error)
        for layout in self.build_plate_layouts:
            if not layout.valid:
                report.add_error(f"Build plate layout for job '{layout.job_id}' has collisions.")
        for result in self.additive_slices:
            if not result.valid:
                for error in result.validation_errors:
                    report.add_error(error)
        for print_file in self.additive_print_files:
            if not print_file.valid:
                for error in print_file.validation_errors:
                    report.add_error(error)
        for layout in self.sheet_nest_layouts:
            if not layout.valid:
                report.add_error(f"Sheet nest layout for job '{layout.job_id}' has collisions.")
        for cut_path in self.sheet_cut_paths:
            if not cut_path.valid:
                for error in cut_path.validation_errors:
                    report.add_error(error)
        for program in self.sheet_programs:
            if not program.valid:
                for error in program.validation_errors:
                    report.add_error(error)
        for profile in self.robot_profiles:
            self._validate_robot_profile(report, profile)
        for frame in self.robot_frames:
            self._validate_robot_frame(report, frame)
        for trajectory in self.robot_trajectories:
            if not trajectory.valid:
                for error in trajectory.validation_errors:
                    report.add_error(error)
        for program in self.robot_programs:
            if not program.valid:
                for error in program.validation_errors:
                    report.add_error(error)
        for simulation in self.simulation_jobs:
            self._validate_simulation_job(simulation)
            if not simulation.valid:
                for error in simulation.validation_errors:
                    report.add_error(error)
        for session in self.simulation_sessions:
            if not session.valid:
                for error in session.validation_errors:
                    report.add_error(error)
        for collision in self.simulation_collision_reports:
            if not collision.valid:
                for item in collision.collisions:
                    report.add_error(f"Simulation collision detected: {item.get('type', 'collision')}")
        for verification in self.simulation_verification_reports:
            if not verification.valid:
                for error in verification.validation_errors:
                    report.add_error(error)
        for simulation_report in self.simulation_reports:
            if not simulation_report.valid:
                report.add_error(f"Simulation report '{simulation_report.id}' is not manufacturing-ready.")
        for connection in self.machine_connections:
            self._validate_machine_connection(connection)
            if not connection.valid:
                for error in connection.validation_errors:
                    report.add_error(error)
        for session in self.communication_sessions:
            self._validate_communication_session(session)
            if not session.valid:
                for error in session.validation_errors:
                    report.add_error(error)
        for queue_item in self.communication_queue:
            if self.job_for(queue_item.manufacturing_job_id) is None:
                report.add_error("Communication queue item references a missing manufacturing job.")
            if self._connection_for(queue_item.connection_id) is None:
                report.add_error("Communication queue item references a missing connection.")
        self.validation_count += 1
        self.last_validation = report
        self._save()
        return report

    def diagnostics(self):
        """Return Manufacturing Engine diagnostics."""

        operations = self.product_manager.cam_operations
        setups = self.product_manager.cam_setups
        coordinate_count = len(self.coordinate_systems)
        offset_count = len(self.work_offsets)
        diagnostics = ManufacturingEngineDiagnostics(
            jobs=len(self.product_manager.cam_jobs),
            operations=len(operations),
            planning_statistics={
                "plans": len(self.execution_plans),
                "cam_plans": len(self.cam_plans),
                "planning_count": self.planning_count,
                "validated_plans": len([plan for plan in self.execution_plans if plan.status == "Validated"]),
                "blocked_plans": len([plan for plan in self.execution_plans if plan.status == "Blocked"]),
            },
            validation_statistics={
                "validation_count": self.validation_count,
                "last_valid": self.last_validation.valid,
                "errors": len(self.last_validation.errors),
                "warnings": len(self.last_validation.warnings),
            },
            dependency_statistics={
                "dependency_edges": len(getattr(self.product_manager, "dependency_edges", [])),
                "operation_dependencies": sum(len(operation.metadata.properties.get("dependencies", [])) for operation in operations),
            },
            stock_statistics={
                "setups": len(setups),
                "stocks": len([setup for setup in setups if getattr(setup, "stock", None)]),
            },
            fixture_statistics={
                "fixtures": len([setup for setup in setups if getattr(getattr(setup, "fixture", None), "fixture_type", "")]),
            },
            coordinate_system_statistics={
                "coordinate_systems": coordinate_count,
                "active": len([item for item in self.coordinate_systems if item.get("active")]),
            },
            work_offset_statistics={
                "work_offsets": offset_count,
                "defaults": len([offset for offset in self.work_offsets if offset.name in self.DEFAULT_WORK_OFFSETS]),
            },
            execution_plan_statistics={
                "plans": len(self.execution_plans),
                "operations_planned": sum(len(plan.operation_ids) for plan in self.execution_plans),
                "toolpaths": len(self.toolpaths),
                "generated_programs": len(self.generated_programs),
                "additive_slices": len(self.additive_slices),
                "additive_print_files": len(self.additive_print_files),
                "gcode_lines": sum(program.statistics.get("lines", 0) for program in self.generated_programs),
                "estimated_cycle_time": sum(program.statistics.get("estimated_cycle_time", 0.0) for program in self.generated_programs),
                "estimated_material_removal": sum(program.statistics.get("estimated_material_removal", 0.0) for program in self.generated_programs),
                "additive_layers": sum(len(result.layers) for result in self.additive_slices),
                "estimated_print_time": sum(result.estimated_print_time for result in self.additive_slices),
                "estimated_filament_length": sum(result.material_usage.get("filament_length", 0.0) for result in self.additive_slices),
                "estimated_resin_volume": sum(result.material_usage.get("resin_volume", 0.0) for result in self.additive_slices),
                "sheet_nest_layouts": len(self.sheet_nest_layouts),
                "sheet_cut_paths": len(self.sheet_cut_paths),
                "sheet_programs": len(self.sheet_programs),
                "sheet_program_lines": sum(program.statistics.get("lines", 0) for program in self.sheet_programs),
                "sheet_pierces": sum(program.statistics.get("pierces", 0) for program in self.sheet_programs),
                "sheet_estimated_cutting_time": sum(program.statistics.get("estimated_cutting_time", 0.0) for program in self.sheet_programs),
                "sheet_material_utilization": max([layout.utilization for layout in self.sheet_nest_layouts] or [0.0]),
                "sheet_kerf_paths": len([path for path in self.sheet_cut_paths if path.kerf_width > 0.0]),
                "robot_profiles": len(self.robot_profiles),
                "robot_frames": len(self.robot_frames),
                "robot_motions": len(self.robot_motions),
                "robot_trajectories": len(self.robot_trajectories),
                "robot_programs": len(self.robot_programs),
                "robot_waypoints": sum(len(trajectory.waypoints) for trajectory in self.robot_trajectories),
                "robot_estimated_cycle_time": sum(trajectory.estimated_cycle_time for trajectory in self.robot_trajectories),
                "robot_program_lines": sum(program.statistics.get("lines", 0) for program in self.robot_programs),
                "robot_utilization": max([program.statistics.get("robot_utilization", 0.0) for program in self.robot_programs] or [0.0]),
                "simulation_jobs": len(self.simulation_jobs),
                "simulation_sessions": len(self.simulation_sessions),
                "simulation_replay_steps": sum(len(session.replay_steps) for session in self.simulation_sessions),
                "simulation_collision_reports": len(self.simulation_collision_reports),
                "simulation_collisions": sum(len(report.collisions) for report in self.simulation_collision_reports),
                "simulation_verification_reports": len(self.simulation_verification_reports),
                "simulation_reports": len(self.simulation_reports),
                "simulation_estimated_cycle_time": sum(report.estimated_cycle_time for report in self.simulation_reports),
                "simulation_estimated_print_time": sum(report.estimated_print_time for report in self.simulation_reports),
                "simulation_estimated_cutting_time": sum(report.estimated_cutting_time for report in self.simulation_reports),
                "simulation_material_usage": sum(sum(float(value) for value in report.material_usage.values() if isinstance(value, (int, float))) for report in self.simulation_reports),
                "simulation_history": len(self.simulation_reports),
                "machine_connections": len(self.machine_connections),
                "connected_machines": len([connection for connection in self.machine_connections if connection.state in {"Connected", "Idle", "Running", "Paused"}]),
                "communication_sessions": len(self.communication_sessions),
                "communication_queue": len(self.communication_queue),
                "communication_events": len(self.communication_events),
                "monitoring_states": len(self.machine_monitoring),
                "recent_machines": len(self.recent_machines),
                "running_sessions": len([session for session in self.communication_sessions if session.state == "Running"]),
                "uploaded_sessions": len([session for session in self.communication_sessions if session.state == "Uploaded"]),
                "emergency_stop_events": len([event for event in self.communication_events if event.event_type == "Emergency Stop"]),
                "protocols": len({connection.protocol for connection in self.machine_connections}),
            },
        )
        self.last_diagnostics = diagnostics
        self._save()
        return diagnostics

    def job_for(self, job):
        """Return a manufacturing job by object, id or name."""

        return self.product_manager.cam_manager.job_for(job)

    def operations_for_job(self, job):
        """Return ordered operations for a manufacturing job."""

        return sorted(
            self.product_manager.operation_manager.operations_for_job(job),
            key=lambda item: item.metadata.order,
        )

    def to_dict(self):
        """Return JSON-safe Manufacturing Engine settings."""

        return {
            "state": self.state.to_dict(),
            "execution_plans": [plan.to_dict() for plan in self.execution_plans],
            "cam_plans": [plan.to_dict() for plan in self.cam_plans],
            "toolpaths": [toolpath.to_dict() for toolpath in self.toolpaths],
            "generated_programs": [program.to_dict() for program in self.generated_programs],
            "additive_parameters": [params.to_dict() for params in self.additive_parameters],
            "build_plate_layouts": [layout.to_dict() for layout in self.build_plate_layouts],
            "additive_slices": [result.to_dict() for result in self.additive_slices],
            "additive_print_files": [print_file.to_dict() for print_file in self.additive_print_files],
            "sheet_parameters": [params.to_dict() for params in self.sheet_parameters],
            "sheet_material_profiles": [profile.to_dict() for profile in self.sheet_material_profiles],
            "sheet_nest_layouts": [layout.to_dict() for layout in self.sheet_nest_layouts],
            "sheet_cut_paths": [path.to_dict() for path in self.sheet_cut_paths],
            "sheet_programs": [program.to_dict() for program in self.sheet_programs],
            "robot_profiles": [profile.to_dict() for profile in self.robot_profiles],
            "robot_frames": [frame.to_dict() for frame in self.robot_frames],
            "robot_motions": [motion.to_dict() for motion in self.robot_motions],
            "robot_trajectories": [trajectory.to_dict() for trajectory in self.robot_trajectories],
            "robot_programs": [program.to_dict() for program in self.robot_programs],
            "simulation_jobs": [simulation.to_dict() for simulation in self.simulation_jobs],
            "simulation_sessions": [session.to_dict() for session in self.simulation_sessions],
            "simulation_collision_reports": [report.to_dict() for report in self.simulation_collision_reports],
            "simulation_verification_reports": [report.to_dict() for report in self.simulation_verification_reports],
            "simulation_reports": [report.to_dict() for report in self.simulation_reports],
            "machine_connections": [connection.to_dict() for connection in self.machine_connections],
            "communication_sessions": [session.to_dict() for session in self.communication_sessions],
            "communication_queue": [item.to_dict() for item in self.communication_queue],
            "machine_monitoring": [state.to_dict() for state in self.machine_monitoring],
            "communication_events": [event.to_dict() for event in self.communication_events],
            "recent_machines": [dict(item) for item in self.recent_machines],
            "production_runtime_state": self.production_runtime_state.to_dict(),
            "production_runtime_events": [event.to_dict() for event in self.production_runtime_events],
            "production_runtime_health_history": [health.to_dict() for health in self.production_runtime_health_history],
            "production_execution_pipelines": [pipeline.to_dict() for pipeline in self.production_execution_pipelines],
            "production_runtime_reports": [report.to_dict() for report in self.production_runtime_reports],
            "production_recovery_checkpoints": [dict(item) for item in self.production_recovery_checkpoints],
            "production_performance_cache": dict(self.production_performance_cache),
            "coordinate_systems": [dict(item) for item in self.coordinate_systems],
            "work_offsets": [offset.to_dict() for offset in self.work_offsets],
            "last_validation": self.last_validation.to_dict(),
            "last_diagnostics": self.last_diagnostics.to_dict(),
            "validation_count": self.validation_count,
            "planning_count": self.planning_count,
        }

    def load_from_settings(self):
        """Restore Manufacturing Engine state from Workspace project settings."""

        data = self.workspace.project_settings.get(MANUFACTURING_ENGINE_SETTINGS_KEY, {})
        self.state = ManufacturingEngineState.from_dict(data.get("state", {}))
        self.execution_plans = [
            ManufacturingExecutionPlan.from_dict(item)
            for item in data.get("execution_plans", [])
        ]
        self.cam_plans = [
            CAMPlan.from_dict(item)
            for item in data.get("cam_plans", [])
        ]
        self.toolpaths = [
            CNCToolpath.from_dict(item)
            for item in data.get("toolpaths", [])
        ]
        self.generated_programs = [
            CNCProgram.from_dict(item)
            for item in data.get("generated_programs", [])
        ]
        self.additive_parameters = [
            AdditivePrintParameters.from_dict(item)
            for item in data.get("additive_parameters", [])
        ]
        self.build_plate_layouts = [
            BuildPlateLayout.from_dict(item)
            for item in data.get("build_plate_layouts", [])
        ]
        self.additive_slices = [
            AdditiveSliceResult.from_dict(item)
            for item in data.get("additive_slices", [])
        ]
        self.additive_print_files = [
            AdditivePrintFile.from_dict(item)
            for item in data.get("additive_print_files", [])
        ]
        self.sheet_parameters = [
            SheetCutParameters.from_dict(item)
            for item in data.get("sheet_parameters", [])
        ]
        self.sheet_material_profiles = [
            SheetMaterialProfile.from_dict(item)
            for item in data.get("sheet_material_profiles", [])
        ]
        self.sheet_nest_layouts = [
            SheetNestLayout.from_dict(item)
            for item in data.get("sheet_nest_layouts", [])
        ]
        self.sheet_cut_paths = [
            SheetCutPath.from_dict(item)
            for item in data.get("sheet_cut_paths", [])
        ]
        self.sheet_programs = [
            SheetProgram.from_dict(item)
            for item in data.get("sheet_programs", [])
        ]
        self.robot_profiles = [
            RobotProfile.from_dict(item)
            for item in data.get("robot_profiles", [])
        ]
        self.robot_frames = [
            RobotFrame.from_dict(item)
            for item in data.get("robot_frames", [])
        ]
        self.robot_motions = [
            RobotMotionCommand.from_dict(item)
            for item in data.get("robot_motions", [])
        ]
        self.robot_trajectories = [
            RobotTrajectory.from_dict(item)
            for item in data.get("robot_trajectories", [])
        ]
        self.robot_programs = [
            RobotProgram.from_dict(item)
            for item in data.get("robot_programs", [])
        ]
        self.simulation_jobs = [
            SimulationJob.from_dict(item)
            for item in data.get("simulation_jobs", [])
        ]
        self.simulation_sessions = [
            SimulationSession.from_dict(item)
            for item in data.get("simulation_sessions", [])
        ]
        self.simulation_collision_reports = [
            SimulationCollisionReport.from_dict(item)
            for item in data.get("simulation_collision_reports", [])
        ]
        self.simulation_verification_reports = [
            SimulationVerificationReport.from_dict(item)
            for item in data.get("simulation_verification_reports", [])
        ]
        self.simulation_reports = [
            SimulationReport.from_dict(item)
            for item in data.get("simulation_reports", [])
        ]
        self.machine_connections = [
            MachineConnection.from_dict(item)
            for item in data.get("machine_connections", [])
        ]
        self.communication_sessions = [
            CommunicationSession.from_dict(item)
            for item in data.get("communication_sessions", [])
        ]
        self.communication_queue = [
            CommunicationJobQueueItem.from_dict(item)
            for item in data.get("communication_queue", [])
        ]
        self.machine_monitoring = [
            MachineMonitoringState.from_dict(item)
            for item in data.get("machine_monitoring", [])
        ]
        self.communication_events = [
            CommunicationEvent.from_dict(item)
            for item in data.get("communication_events", [])
        ]
        self.recent_machines = [dict(item) for item in data.get("recent_machines", [])]
        self.production_runtime_state = ProductionRuntimeState.from_dict(data.get("production_runtime_state", {}))
        self.production_runtime_events = [
            ProductionRuntimeEvent.from_dict(item)
            for item in data.get("production_runtime_events", [])
        ]
        self.production_runtime_health_history = [
            ProductionRuntimeHealth.from_dict(item)
            for item in data.get("production_runtime_health_history", [])
        ]
        self.production_execution_pipelines = [
            ProductionExecutionPipeline.from_dict(item)
            for item in data.get("production_execution_pipelines", [])
        ]
        self.production_runtime_reports = [
            ProductionRuntimeReport.from_dict(item)
            for item in data.get("production_runtime_reports", [])
        ]
        self.production_recovery_checkpoints = [dict(item) for item in data.get("production_recovery_checkpoints", [])]
        self.production_performance_cache = dict(data.get("production_performance_cache", {}))
        self.coordinate_systems = [dict(item) for item in data.get("coordinate_systems", [])]
        self.work_offsets = [
            ManufacturingWorkOffset.from_dict(item)
            for item in data.get("work_offsets", [])
        ]
        self.last_validation = ManufacturingValidationReport.from_dict(data.get("last_validation", {}))
        self.last_diagnostics = ManufacturingEngineDiagnostics.from_dict(data.get("last_diagnostics", {}))
        self.validation_count = int(data.get("validation_count", 0))
        self.planning_count = int(data.get("planning_count", 0))
        return self

    def clear(self):
        """Clear engine settings while ProductManager clears manufacturing records."""

        self.state = ManufacturingEngineState()
        self.execution_plans = []
        self.cam_plans = []
        self.toolpaths = []
        self.generated_programs = []
        self.additive_parameters = []
        self.build_plate_layouts = []
        self.additive_slices = []
        self.additive_print_files = []
        self.sheet_parameters = []
        self.sheet_material_profiles = []
        self.sheet_nest_layouts = []
        self.sheet_cut_paths = []
        self.sheet_programs = []
        self.robot_profiles = []
        self.robot_frames = []
        self.robot_motions = []
        self.robot_trajectories = []
        self.robot_programs = []
        self.simulation_jobs = []
        self.simulation_sessions = []
        self.simulation_collision_reports = []
        self.simulation_verification_reports = []
        self.simulation_reports = []
        self.machine_connections = []
        self.communication_sessions = []
        self.communication_queue = []
        self.machine_monitoring = []
        self.communication_events = []
        self.recent_machines = []
        self.production_runtime_state = ProductionRuntimeState()
        self.production_runtime_events = []
        self.production_runtime_health_history = []
        self.production_execution_pipelines = []
        self.production_runtime_reports = []
        self.production_recovery_checkpoints = []
        self.production_performance_cache = {}
        self.coordinate_systems = []
        self.work_offsets = []
        self.last_validation = ManufacturingValidationReport()
        self.last_diagnostics = ManufacturingEngineDiagnostics()
        self.validation_count = 0
        self.planning_count = 0
        self.workspace.project_settings.pop(MANUFACTURING_ENGINE_SETTINGS_KEY, None)

    def _save(self):
        self.workspace.project_settings[MANUFACTURING_ENGINE_SETTINGS_KEY] = self.to_dict()

    def _ensure_default_offsets(self):
        existing = {offset.name for offset in self.work_offsets if not offset.metadata.get("job_id")}
        for name in self.DEFAULT_WORK_OFFSETS:
            if name not in existing:
                self.work_offsets.append(ManufacturingWorkOffset(name, metadata={"default": True}))

    def _ensure_setup(self, job):
        setup = self._first_setup(job)
        if setup is None:
            setup = self.product_manager.manufacturing_setup_manager.create_setup(
                job,
                stock_type="Box",
                name=f"{job.name} Setup",
            )
        return setup

    def _first_setup(self, job):
        setups = self.product_manager.manufacturing_setup_manager.setups_for_job(job)
        return setups[0] if setups else None

    def _validate_job(self, report, job):
        properties = job.metadata.properties
        if not properties.get("machine_profile_id"):
            report.add_error(f"Manufacturing job '{job.name}' is missing a machine profile.")
        if not properties.get("material_id"):
            report.add_error(f"Manufacturing job '{job.name}' is missing a material.")
        if job.metadata.status not in MANUFACTURING_STATES:
            report.add_error(f"Manufacturing job '{job.name}' has invalid status '{job.metadata.status}'.")

    def _validate_sheet_job(self, report, job):
        properties = job.metadata.properties
        if not properties.get("sheet_manufacturing"):
            return
        process = properties.get("sheet_process", "")
        if process not in self.SHEET_PROCESSES:
            report.add_error(f"Sheet job '{job.name}' has unsupported process '{process}'.")
        sheet = properties.get("sheet_size", {})
        if float(sheet.get("x", sheet.get("width", 0.0))) <= 0.0 or float(sheet.get("y", sheet.get("height", 0.0))) <= 0.0:
            report.add_error(f"Sheet job '{job.name}' has invalid sheet size.")
        profile = self.product_manager.machine_library_manager.profile_for(properties.get("machine_profile_id", ""))
        machine = self.product_manager.machine_library_manager.machine_for(getattr(profile, "machine_id", ""))
        material = self.product_manager.engineering_material_manager.material_for(properties.get("material_id", ""))
        if machine is not None:
            category = getattr(getattr(machine, "metadata", None), "machine_category", "")
            expected = {"Laser": "Laser Cutter", "Plasma": "Plasma Cutter", "Waterjet": "Waterjet"}.get(process)
            if expected and category != expected:
                report.add_error(f"Sheet job '{job.name}' uses incompatible machine category '{category}'.")
            supported = getattr(getattr(machine, "metadata", None), "properties", {}).get("supported_materials", [])
            if material is not None and supported and material.name not in supported:
                report.add_error(f"Sheet job '{job.name}' uses material not listed by the machine profile.")
        params = self._sheet_parameters_for_job(job)
        if params is not None:
            if params.kerf_width < 0.0:
                report.add_error(f"Sheet job '{job.name}' has invalid kerf width.")
            if params.speed <= 0.0:
                report.add_error(f"Sheet job '{job.name}' has invalid cutting speed.")
            if params.pass_count <= 0:
                report.add_error(f"Sheet job '{job.name}' has invalid pass count.")

    def _validate_robot_job(self, report, job):
        properties = job.metadata.properties
        if not properties.get("robotics_motion"):
            return
        profile = self._robot_profile_for(properties.get("robot_profile_id", ""))
        if profile is None:
            report.add_error(f"Robot job '{job.name}' references a missing robot profile.")
            return
        machine_profile = self.product_manager.machine_library_manager.profile_for(properties.get("machine_profile_id", ""))
        machine = self.product_manager.machine_library_manager.machine_for(getattr(machine_profile, "machine_id", ""))
        if machine is not None:
            category = getattr(getattr(machine, "metadata", None), "machine_category", "")
            if category not in {"Robot", "Custom Machine"}:
                report.add_error(f"Robot job '{job.name}' uses incompatible machine category '{category}'.")
        job_frames = [frame for frame in self.robot_frames if frame.job_id == job.id]
        if not any(frame.frame_type == "World" for frame in job_frames):
            report.add_error(f"Robot job '{job.name}' is missing a world coordinate frame.")
        if not any(frame.frame_type == "Robot Base" for frame in job_frames):
            report.add_error(f"Robot job '{job.name}' is missing a robot base frame.")
        if not any(frame.frame_type == "Tool Frame" for frame in job_frames):
            report.add_error(f"Robot job '{job.name}' is missing a tool frame.")
        if not any(motion.job_id == job.id for motion in self.robot_motions):
            report.add_error(f"Robot job '{job.name}' requires at least one planned motion.")

    def _validate_operations(self, report, job, operations):
        operation_ids = {operation.id for operation in operations}
        orders = []
        for operation in operations:
            orders.append(operation.metadata.order)
            properties = operation.metadata.properties
            if properties.get("required_tool_id") and not self._id_exists(self.product_manager.tool_definitions, properties["required_tool_id"]):
                report.add_error(f"Operation '{operation.name}' references a missing tool.")
            if properties.get("required_material_id") and not self._id_exists(self.product_manager.engineering_materials, properties["required_material_id"]):
                report.add_error(f"Operation '{operation.name}' references a missing material.")
            for dependency_id in properties.get("dependencies", []):
                if dependency_id not in operation_ids:
                    report.add_error(f"Operation '{operation.name}' references a missing operation dependency.")
        if len(orders) != len(set(orders)):
            report.add_error(f"Manufacturing job '{job.name}' has duplicate operation order values.")
        if self._has_cycle(operations):
            report.add_error(f"Manufacturing job '{job.name}' has circular operation dependencies.")

    def _validate_plan(self, job, plan):
        plan.validation_errors.clear()
        plan.validation_warnings.clear()
        operations = self.operations_for_job(job)
        setups = self.product_manager.manufacturing_setup_manager.setups_for_job(job)
        if not operations:
            plan.validation_errors.append("Execution plan requires at least one operation.")
        if not setups:
            plan.validation_errors.append("Execution plan requires stock/setup metadata.")
        if setups and not getattr(setups[0], "stock", None):
            plan.validation_errors.append("Execution plan requires stock metadata.")
        if setups and not getattr(setups[0], "fixture", None):
            plan.validation_errors.append("Execution plan requires fixture metadata.")
        if not plan.coordinate_system_ids:
            plan.validation_errors.append("Execution plan requires a coordinate system.")
        if not plan.work_offset_ids:
            plan.validation_errors.append("Execution plan requires a work offset.")
        properties = job.metadata.properties
        if not properties.get("machine_profile_id"):
            plan.validation_errors.append("Execution plan requires a machine profile.")
        if not properties.get("material_id"):
            plan.validation_errors.append("Execution plan requires material metadata.")
        for operation in operations:
            operation_properties = operation.metadata.properties
            if operation_properties.get("required_tool_id") and not self._id_exists(self.product_manager.tool_definitions, operation_properties["required_tool_id"]):
                plan.validation_errors.append(f"Operation '{operation.name}' requires a missing tool.")
            if operation_properties.get("dependencies"):
                missing = [
                    dependency_id for dependency_id in operation_properties["dependencies"]
                    if dependency_id not in {item.id for item in operations}
                ]
                if missing:
                    plan.validation_errors.append(f"Operation '{operation.name}' has missing dependencies.")
        if self._has_cycle(operations):
            plan.validation_errors.append("Operation dependencies contain a cycle.")

    def _validate_cam_plan(self, job, plan):
        plan.validation_errors.clear()
        plan.validation_warnings.clear()
        operations = self.operations_for_job(job)
        if not operations:
            plan.validation_errors.append("CAM plan requires at least one machining operation.")
        for operation in operations:
            properties = operation.metadata.properties
            tool_id = properties.get("required_tool_id") or operation.parameters.tool_id
            if not tool_id:
                plan.validation_errors.append(f"Operation '{operation.name}' is missing a tool.")
            elif not self._id_exists(self.product_manager.tool_definitions, tool_id):
                plan.validation_errors.append(f"Operation '{operation.name}' references a missing tool.")
            if float(operation.parameters.feed_rate or properties.get("feeds", {}).get("feed_rate", 1.0)) <= 0.0 and not properties.get("feeds"):
                plan.validation_warnings.append(f"Operation '{operation.name}' has no explicit feed metadata; calculated feeds will be used.")
            if float(operation.parameters.spindle_speed or properties.get("speeds", {}).get("rpm", 1.0)) <= 0.0 and not properties.get("speeds"):
                plan.validation_warnings.append(f"Operation '{operation.name}' has no explicit speed metadata; calculated speeds will be used.")
        if self._has_cycle(operations):
            plan.validation_errors.append("CAM plan has circular operation dependencies.")

    def _validate_toolpath(self, operation, toolpath):
        toolpath.validation_errors.clear()
        toolpath.validation_warnings.clear()
        if not toolpath.moves:
            toolpath.validation_errors.append(f"Operation '{operation.name}' generated no toolpath moves.")
        if not toolpath.tool_id:
            toolpath.validation_errors.append(f"Operation '{operation.name}' generated a toolpath without a tool.")
        if toolpath.cutting_parameters.feed_rate <= 0.0:
            toolpath.validation_errors.append(f"Operation '{operation.name}' has invalid feed rate.")
        if toolpath.cutting_parameters.rpm <= 0.0:
            toolpath.validation_errors.append(f"Operation '{operation.name}' has invalid spindle speed.")
        if operation.metadata.properties.get("required_machine_id") and not self._id_exists(self.product_manager.machine_profiles, operation.metadata.properties["required_machine_id"]):
            toolpath.validation_errors.append(f"Operation '{operation.name}' references a missing machine profile.")

    @staticmethod
    def _validate_program(program):
        program.validation_errors.clear()
        program.validation_warnings.clear()
        required = ("G21", "G90", "M30")
        for token in required:
            if token not in program.gcode:
                program.validation_errors.append(f"G-code program is missing required block {token}.")
        if not program.toolpath_ids:
            program.validation_errors.append("G-code program references no toolpaths.")

    def _operation_for(self, operation):
        identifier = getattr(operation, "id", operation)
        for item in self.product_manager.cam_operations:
            if item is operation or item.id == identifier or item.name == identifier:
                return item
        return None

    def _tool_for(self, tool):
        identifier = getattr(tool, "id", tool)
        for item in self.product_manager.tool_definitions:
            if item is tool or item.id == identifier or item.name == identifier:
                return item
        return None

    @staticmethod
    def _strategy_for_operation(operation):
        operation_type = getattr(operation, "operation_type", "Facing")
        return {
            "Facing": "Planar Facing",
            "2D Profile": "2D Contour Profile",
            "Profiling": "2D Contour Profile",
            "2D Pocket": "Offset Pocket Clearing",
            "Pocketing": "Offset Pocket Clearing",
            "Adaptive Clearing": "Constant Engagement Clearing",
            "Slot Milling": "Centerline Slot Milling",
            "Contour": "Contour Finishing",
            "Chamfer": "Chamfer Edge Break",
            "Drilling": "Standard Drill Cycle",
            "Peck Drilling": "Peck Drill Cycle",
            "Counterbore": "Counterbore Cycle",
            "Countersink": "Countersink Cycle",
            "Boring": "Boring Cycle",
            "Reaming": "Reaming Cycle",
            "Rigid Tapping": "Rigid Tapping Cycle",
            "Thread Milling": "Thread Milling Helix",
            "Engraving": "Shallow Engraving",
        }.get(operation_type, operation_type)

    def _estimated_operation_path_length(self, operation):
        geometry = operation.metadata.properties.get("cut_geometry", {})
        if geometry.get("points"):
            points = geometry["points"]
            length = 0.0
            previous = None
            for point in points:
                if previous is not None:
                    length += ((float(point.get("x", 0.0)) - float(previous.get("x", 0.0))) ** 2 + (float(point.get("y", 0.0)) - float(previous.get("y", 0.0))) ** 2) ** 0.5
                previous = point
            return max(length, 1.0)
        setup = self._first_setup(self.job_for(operation.job_id))
        dimensions = getattr(getattr(setup, "stock", None), "dimensions", Vector3(100.0, 60.0, 10.0))
        return max((dimensions.x * 2.0) + (dimensions.y * 2.0), 1.0)

    def _generate_operation_moves(self, operation, params):
        geometry = operation.metadata.properties.get("cut_geometry", {})
        points = list(geometry.get("points", []))
        if not points:
            points = self._default_points_for_operation(operation)
        clearance = float(geometry.get("clearance", 5.0))
        approach = float(geometry.get("approach", 1.0))
        depth = -abs(float(operation.metadata.properties.get("depth", 0.0) or params.stepdown))
        first = points[0]
        moves = [
            CNCToolpathMove("Rapid", float(first.get("x", 0.0)), float(first.get("y", 0.0)), clearance, comment="Clearance rapid"),
            CNCToolpathMove("Rapid", float(first.get("x", 0.0)), float(first.get("y", 0.0)), approach, comment="Approach plane"),
            CNCToolpathMove("Lead-in", float(first.get("x", 0.0)), float(first.get("y", 0.0)), depth, params.plunge_rate, comment="Entry"),
        ]
        for point in points[1:]:
            moves.append(CNCToolpathMove("Cut", float(point.get("x", 0.0)), float(point.get("y", 0.0)), depth, params.feed_rate))
        if operation.operation_type in {"Drilling", "Peck Drilling", "Counterbore", "Countersink", "Boring", "Reaming", "Rigid Tapping"}:
            moves = []
            for point in points:
                moves.extend([
                    CNCToolpathMove("Rapid", float(point.get("x", 0.0)), float(point.get("y", 0.0)), clearance, comment="Hole rapid"),
                    CNCToolpathMove("Drill", float(point.get("x", 0.0)), float(point.get("y", 0.0)), depth, params.plunge_rate, comment=operation.operation_type),
                    CNCToolpathMove("Retract", float(point.get("x", 0.0)), float(point.get("y", 0.0)), clearance, comment="Safe retract"),
                ])
            return moves
        if operation.operation_type in {"Thread Milling"}:
            center = points[0]
            radius = float(geometry.get("radius", max(params.stepover, 1.0)))
            moves.append(CNCToolpathMove("Helix", float(center.get("x", 0.0)) + radius, float(center.get("y", 0.0)), depth, params.feed_rate, i=-radius, j=0.0, comment="Thread helix"))
        if operation.operation_type in {"Adaptive Clearing", "2D Pocket", "Pocketing"}:
            center = points[0]
            moves.append(CNCToolpathMove("Ramp", float(center.get("x", 0.0)), float(center.get("y", 0.0)), depth, params.plunge_rate, comment="Ramp entry"))
        last = points[-1]
        moves.extend([
            CNCToolpathMove("Lead-out", float(last.get("x", 0.0)), float(last.get("y", 0.0)), approach, params.feed_rate, comment="Exit"),
            CNCToolpathMove("Retract", float(last.get("x", 0.0)), float(last.get("y", 0.0)), clearance, comment="Safe retract"),
        ])
        return moves

    def _default_points_for_operation(self, operation):
        setup = self._first_setup(self.job_for(operation.job_id))
        dimensions = getattr(getattr(setup, "stock", None), "dimensions", Vector3(100.0, 60.0, 10.0))
        width = max(float(getattr(dimensions, "x", 100.0)), 1.0)
        height = max(float(getattr(dimensions, "y", 60.0)), 1.0)
        margin = float(operation.metadata.properties.get("allowance", 0.0))
        if operation.operation_type in {"Drilling", "Peck Drilling", "Counterbore", "Countersink", "Boring", "Reaming", "Rigid Tapping"}:
            return [
                {"x": width * 0.25, "y": height * 0.25},
                {"x": width * 0.75, "y": height * 0.25},
                {"x": width * 0.75, "y": height * 0.75},
                {"x": width * 0.25, "y": height * 0.75},
            ]
        return [
            {"x": margin, "y": margin},
            {"x": width - margin, "y": margin},
            {"x": width - margin, "y": height - margin},
            {"x": margin, "y": height - margin},
            {"x": margin, "y": margin},
        ]

    def _post_lines(self, job, toolpaths, controller, program_name):
        lines = [f"({program_name})", f"(POST: {controller})", "G21", "G90", "G17"]
        offset = self._active_work_offset(job)
        lines.append(offset.name if offset else "G54")
        current_tool = None
        for toolpath in toolpaths:
            if toolpath.tool_id and toolpath.tool_id != current_tool:
                tool_number = self._tool_number(toolpath.tool_id)
                lines.extend(self._tool_change_lines(controller, tool_number, toolpath.cutting_parameters.rpm))
                current_tool = toolpath.tool_id
            lines.append(f"(OPERATION {toolpath.metadata.get('operation_type', '')})")
            for move in toolpath.moves:
                lines.extend(self._move_to_gcode(move, controller))
        lines.extend(["M9", "M5", "G0 Z5.000", "G0 X0.000 Y0.000", "M30"])
        return lines

    def _move_to_gcode(self, move, controller):
        xyz = f"X{move.x:.3f} Y{move.y:.3f} Z{move.z:.3f}"
        feed = f" F{move.feed:.1f}" if move.feed > 0.0 else ""
        if move.move_type in {"Rapid", "Retract"}:
            return [f"G0 {xyz}"]
        if move.move_type == "Drill":
            cycle = "G83" if "Peck" in move.comment else "G81"
            if controller == "GRBL":
                return [f"G1 {xyz}{feed}", "G0 Z5.000"]
            return [f"{cycle} {xyz} R2.000{feed}", "G80"]
        if move.move_type == "Helix":
            return [f"G3 X{move.x:.3f} Y{move.y:.3f} Z{move.z:.3f} I{move.i:.3f} J{move.j:.3f}{feed}"]
        return [f"G1 {xyz}{feed}"]

    @staticmethod
    def _tool_number(tool_id):
        return max((sum(ord(ch) for ch in str(tool_id)) % 90) + 1, 1)

    @staticmethod
    def _tool_change_lines(controller, tool_number, rpm):
        spindle = f"S{rpm:.0f} M3"
        if controller == "GRBL":
            return [f"(TOOL {tool_number})", spindle]
        return [f"T{tool_number} M6", spindle, "M8"]

    def _active_work_offset(self, job):
        job_id = getattr(job, "id", job)
        job_offsets = [offset for offset in self.work_offsets if offset.metadata.get("job_id") == job_id]
        return job_offsets[0] if job_offsets else next((offset for offset in self.work_offsets if offset.name == "G54"), None)

    @classmethod
    def _normalize_controller(cls, controller):
        names = {
            "Generic ISO G-code": "Generic ISO G-code",
            "GenericGCode": "Generic ISO G-code",
            "Generic": "Generic ISO G-code",
            "Fanuc": "Fanuc",
            "Haas": "Haas",
            "LinuxCNC": "LinuxCNC",
            "Mach3": "Mach3",
            "Mach4": "Mach4",
            "GRBL": "GRBL",
            "Marlin": "Marlin",
            "Klipper": "Klipper",
            "FluidNC": "FluidNC",
        }
        normalized = names.get(str(controller), str(controller))
        if normalized not in cls.CONTROLLERS:
            raise ValueError(f"Unsupported controller: {controller}")
        return normalized

    @staticmethod
    def _program_name(name):
        return "".join(ch for ch in str(name).upper().replace(" ", "_") if ch.isalnum() or ch == "_")[:32] or "PROGRAM"

    def _create_slice_profile(self, job, technology, machine_profile, material):
        existing = self.product_manager.slicer_manager.profile_for(f"{job.name} {technology} Profile")
        if existing is not None:
            return existing
        return self.product_manager.slicer_manager.create_profile(
            name=f"{job.name} {technology} Profile",
            machine_profile=machine_profile,
            engineering_material=material,
            technology=technology,
            status="Planned",
            metadata_properties={
                "additive_engine": True,
                "job_id": job.id,
            },
        )

    def _sync_slice_profile(self, job, params):
        profiles = [
            profile for profile in self.product_manager.slice_profiles
            if profile.metadata.properties.get("job_id") == job.id
        ]
        if not profiles:
            return None
        profile = profiles[0]
        profile.print_profile.layer.layer_height = params.layer_height
        profile.print_profile.layer.first_layer_height = params.layer_height
        profile.print_profile.layer.adaptive_layers_placeholder = bool(params.metadata.get("adaptive_layers", False))
        profile.print_profile.infill.percentage = params.infill_percentage
        profile.print_profile.infill.pattern_placeholder = params.infill_pattern
        profile.print_profile.shell.perimeters = params.line_count
        profile.print_profile.shell.top_layers = max(int(params.top_thickness / max(params.layer_height, 0.001)), 1)
        profile.print_profile.shell.bottom_layers = max(int(params.bottom_thickness / max(params.layer_height, 0.001)), 1)
        profile.print_profile.print_speed = params.print_speed
        profile.print_profile.travel_speed = params.travel_speed
        profile.print_profile.acceleration_placeholder = params.acceleration
        profile.print_profile.jerk_placeholder = params.jerk
        profile.metadata.status = "Configured"
        return profile

    def _slice_additive(self, job, technology, parameters=None, support_plan=None):
        target_job = self.job_for(job)
        if target_job is None:
            raise ValueError("Additive slicing requires an existing additive job.")
        if technology not in {"FDM", "SLA"}:
            raise ValueError(f"Unsupported additive technology: {technology}")
        params = parameters or self._parameters_for_job(target_job) or self.configure_print_parameters(target_job, technology=technology)
        if params.technology != technology:
            params.technology = technology
        layout = self._layout_for_job(target_job) or self.plan_build_plate(target_job)
        support = support_plan or self.generate_supports(
            target_job,
            support_type="Automatic" if technology == "FDM" else "Tree",
            density=15.0 if technology == "FDM" else 25.0,
        )
        dimensions = target_job.metadata.properties.get("model_dimensions", {"x": 20.0, "y": 20.0, "z": 10.0})
        layer_count = max(int((float(dimensions.get("z", 10.0)) / max(params.layer_height, 0.001)) + 0.999), 1)
        layers = [
            self._generate_fdm_layer(index, layer_count, dimensions, params, support)
            if technology == "FDM"
            else self._generate_sla_layer(index, layer_count, dimensions, params, support)
            for index in range(layer_count)
        ]
        usage = self._estimate_additive_usage(layers, dimensions, params, technology, target_job.id)
        estimated_time = self._estimate_print_time(layers, params, technology)
        slice_job = self._slice_job_for_cam_job(target_job)
        if slice_job is not None:
            slice_job.metadata.status = "Sliced"
            slice_job.metadata.technology = technology
            slice_job.metadata.properties.update({
                "layers": layer_count,
                "estimated_print_time": estimated_time,
                "material_usage": dict(usage),
            })
        result = AdditiveSliceResult(
            job_id=target_job.id,
            slice_job_id=getattr(slice_job, "id", ""),
            technology=technology,
            layers=layers,
            support_plan=support,
            build_layout_id=layout.id,
            material_usage=usage,
            estimated_print_time=estimated_time,
            metadata={
                "native_slicer": True,
                "generated_at": self._timestamp(),
                "adaptive_layers": bool(params.metadata.get("adaptive_layers", False)),
                "hollowing": dict(params.metadata.get("hollowing", {})),
                "drain_holes": list(params.metadata.get("drain_holes", [])),
                "orientation": dict(params.metadata.get("orientation", {})),
                "island_detection": technology == "SLA",
            },
        )
        self._validate_slice_result(target_job, result, params, layout)
        self.additive_slices = [item for item in self.additive_slices if item.job_id != target_job.id or item.technology != technology]
        self.additive_slices.append(result)
        self._save()
        return result

    def _generate_fdm_layer(self, index, layer_count, dimensions, params, support):
        z = (index + 1) * params.layer_height
        width = float(dimensions.get("x", 20.0))
        depth = float(dimensions.get("y", 20.0))
        perimeter = self._rectangle_path(width, depth, offset=0.0)
        walls = [
            self._rectangle_path(width, depth, offset=params.extrusion_width * wall)
            for wall in range(params.line_count)
        ]
        is_bottom = index < max(int(params.bottom_thickness / max(params.layer_height, 0.001)), 1)
        is_top = index >= layer_count - max(int(params.top_thickness / max(params.layer_height, 0.001)), 1)
        infill = [] if is_top or is_bottom else self._infill_paths(width, depth, params)
        supports = [
            self._support_path(region)
            for region in support.support_regions
            if support.enabled and z <= float(region.get("height", 0.0))
        ]
        travel = [list(reversed(perimeter))]
        return AdditiveLayer(
            index=index,
            z=z,
            height=params.layer_height,
            perimeters=[perimeter],
            walls=walls,
            top=[perimeter] if is_top else [],
            bottom=[perimeter] if is_bottom else [],
            infill=infill,
            supports=supports,
            travel=travel,
            metadata={
                "adaptive": bool(params.metadata.get("adaptive_layers", False)),
                "retraction": dict(params.metadata.get("retraction", {})),
                "z_hop": dict(params.metadata.get("z_hop", {})),
                "print_order": index,
            },
        )

    def _generate_sla_layer(self, index, layer_count, dimensions, params, support):
        z = (index + 1) * params.layer_height
        width = float(dimensions.get("x", 20.0))
        depth = float(dimensions.get("y", 20.0))
        perimeter = self._rectangle_path(width, depth, offset=0.0)
        supports = [
            self._support_path(region)
            for region in support.support_regions
            if support.enabled and z <= float(region.get("height", 0.0))
        ]
        hollowing = params.metadata.get("hollowing", {})
        inner = []
        if hollowing.get("enabled", False):
            wall = float(hollowing.get("wall_thickness", 2.0))
            inner = [self._rectangle_path(width, depth, offset=wall)]
        return AdditiveLayer(
            index=index,
            z=z,
            height=params.layer_height,
            perimeters=[perimeter] + inner,
            supports=supports,
            exposure={
                "normal": params.metadata.get("exposure", {}).get("normal", 2.5),
                "bottom": params.metadata.get("exposure", {}).get("bottom", 25.0),
                "lift": dict(params.metadata.get("lift", {"distance": 6.0, "speed": 60.0})),
            },
            metadata={
                "island_detection": True,
                "islands": [] if index < layer_count else [],
                "drain_holes": list(params.metadata.get("drain_holes", [])),
                "orientation": dict(params.metadata.get("orientation", {})),
                "resin_profile": dict(params.metadata.get("resin_profile", {})),
            },
        )

    @staticmethod
    def _rectangle_path(width, depth, offset=0.0):
        x0 = min(max(float(offset), 0.0), max(width * 0.5, 0.0))
        y0 = min(max(float(offset), 0.0), max(depth * 0.5, 0.0))
        x1 = max(width - x0, x0)
        y1 = max(depth - y0, y0)
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]

    @staticmethod
    def _infill_paths(width, depth, params):
        spacing = max(params.extrusion_width * (100.0 / max(params.infill_percentage, 1.0)), params.extrusion_width)
        paths = []
        y = spacing
        while y < depth:
            paths.append([(0.0, y), (width, y)])
            y += spacing
        if params.infill_pattern.lower() in {"grid", "gyroid"}:
            x = spacing
            while x < width:
                paths.append([(x, 0.0), (x, depth)])
                x += spacing
        return paths

    @staticmethod
    def _support_path(region):
        x = float(region.get("x", 0.0))
        y = float(region.get("y", 0.0))
        size = max(float(region.get("density", 15.0)) * 0.05, 0.5)
        return [(x - size, y - size), (x + size, y - size), (x + size, y + size), (x - size, y + size), (x - size, y - size)]

    def _estimate_additive_usage(self, layers, dimensions, params, technology, job_id=""):
        path_length = sum(self._path_length(path) for layer in layers for path in (layer.perimeters + layer.walls + layer.infill + layer.supports))
        volume = path_length * params.extrusion_width * params.layer_height
        density = self._material_density_for_job_id(job_id)
        if technology == "SLA":
            resin_volume = float(dimensions.get("x", 20.0)) * float(dimensions.get("y", 20.0)) * float(dimensions.get("z", 10.0)) * 0.35
            return {
                "resin_volume": resin_volume,
                "resin_weight": resin_volume * density / 1000.0,
                "filament_length": 0.0,
                "filament_weight": 0.0,
            }
        filament_area = pi * (1.75 / 2.0) ** 2
        filament_length = volume / max(filament_area, 0.001)
        return {
            "filament_length": filament_length,
            "filament_weight": volume * density / 1000.0,
            "resin_volume": 0.0,
            "resin_weight": 0.0,
        }

    @staticmethod
    def _path_length(path):
        total = 0.0
        previous = None
        for point in path:
            if previous is not None:
                total += ((float(point[0]) - float(previous[0])) ** 2 + (float(point[1]) - float(previous[1])) ** 2) ** 0.5
            previous = point
        return total

    @staticmethod
    def _estimate_print_time(layers, params, technology):
        if technology == "SLA":
            exposure = float(params.metadata.get("exposure", {}).get("normal", 2.5))
            lift = float(params.metadata.get("lift", {}).get("time", 5.0))
            return len(layers) * (exposure + lift)
        path_length = sum(ManufacturingEngine._path_length(path) for layer in layers for path in (layer.perimeters + layer.walls + layer.infill + layer.supports + layer.travel))
        return (path_length / max(params.print_speed, 1.0)) * 60.0

    def _generate_print_content(self, job, slice_result, format_name):
        params = self._parameters_for_job(job) or AdditivePrintParameters(slice_result.technology)
        header = [
            f"; {self._program_name(job.name)}",
            f"; FORMAT: {format_name}",
            f"; TECHNOLOGY: {slice_result.technology}",
            f"; LAYERS: {len(slice_result.layers)}",
            f"; ESTIMATED_TIME: {slice_result.estimated_print_time:.2f}",
            f"; MATERIAL: {job.metadata.properties.get('material_id', '')}",
            f"; MACHINE: {job.metadata.properties.get('machine_profile_id', '')}",
        ]
        if format_name in {"CTB foundation", "Photon foundation"}:
            return "\n".join(header + [
                "; SLA_PRINT_FILE_METADATA",
                f"; RESIN_VOLUME: {slice_result.material_usage.get('resin_volume', 0.0):.3f}",
                "BEGIN_LAYERS",
                *[f"LAYER {layer.index} Z{layer.z:.3f} EXPOSURE {layer.exposure.get('normal', 2.5)}" for layer in slice_result.layers],
                "END_LAYERS",
            ])
        lines = header + ["G21", "G90", f"M104 S{params.temperature.get('nozzle', 200)}", f"M140 S{params.temperature.get('bed', 60)}"]
        if format_name == "Klipper G-code":
            lines.append("SET_VELOCITY_LIMIT ACCEL={:.0f}".format(params.acceleration))
        if format_name == "Bambu-compatible metadata foundation":
            lines.append("; BAMBU_METADATA_BEGIN")
            lines.append(f"; filament_length={slice_result.material_usage.get('filament_length', 0.0):.3f}")
            lines.append("; BAMBU_METADATA_END")
        extrusion = 0.0
        for layer in slice_result.layers:
            lines.append(f";LAYER:{layer.index}")
            lines.append(f"G0 Z{layer.z:.3f}")
            for group in (layer.perimeters, layer.walls, layer.infill, layer.supports):
                for path in group:
                    if not path:
                        continue
                    start = path[0]
                    lines.append(f"G0 X{start[0]:.3f} Y{start[1]:.3f} F{params.travel_speed * 60:.0f}")
                    for point in path[1:]:
                        extrusion += max(params.extrusion_width * params.layer_height, 0.001)
                        lines.append(f"G1 X{point[0]:.3f} Y{point[1]:.3f} E{extrusion:.5f} F{params.print_speed * 60:.0f}")
            if params.metadata.get("retraction", {}).get("enabled", False):
                extrusion = max(extrusion - float(params.metadata["retraction"].get("distance", 1.0)), 0.0)
                lines.append(f"G1 E{extrusion:.5f} F{params.metadata['retraction'].get('speed', 35.0) * 60:.0f}")
        lines.extend(["M104 S0", "M140 S0", "M107", "M84", "M30"])
        return "\n".join(lines)

    def _validate_slice_result(self, job, result, params, layout):
        result.validation_errors.clear()
        result.validation_warnings.clear()
        dimensions = job.metadata.properties.get("model_dimensions", {})
        volume = layout.build_volume
        if float(dimensions.get("x", 0.0)) > float(volume.get("x", 0.0)) or float(dimensions.get("y", 0.0)) > float(volume.get("y", 0.0)) or float(dimensions.get("z", 0.0)) > float(volume.get("z", 0.0)):
            result.validation_errors.append("Model exceeds build volume.")
        if result.technology == "FDM" and params.layer_height > params.nozzle_diameter * 0.8:
            result.validation_errors.append("Layer height exceeds nozzle compatibility limit.")
        if params.wall_thickness < params.extrusion_width:
            result.validation_errors.append("Wall thickness is smaller than extrusion width.")
        if not layout.valid:
            result.validation_errors.append("Build layout has placement collisions.")
        material_id = job.metadata.properties.get("material_id", "")
        if material_id and not self._id_exists(self.product_manager.engineering_materials, material_id):
            result.validation_errors.append("Additive job references a missing material.")
        machine_profile_id = job.metadata.properties.get("machine_profile_id", "")
        if machine_profile_id and not self._id_exists(self.product_manager.machine_profiles, machine_profile_id):
            result.validation_errors.append("Additive job references a missing machine profile.")
        if not result.layers:
            result.validation_errors.append("Native slicer generated no layers.")

    @staticmethod
    def _validate_print_file(print_file):
        print_file.validation_errors.clear()
        print_file.validation_warnings.clear()
        if not print_file.content:
            print_file.validation_errors.append("Print file is empty.")
        if print_file.format in {"Generic G-code", "Klipper G-code", "Marlin G-code"} and "G21" not in print_file.content:
            print_file.validation_errors.append("G-code print file is missing units setup.")
        if print_file.format in {"CTB foundation", "Photon foundation"} and "BEGIN_LAYERS" not in print_file.content:
            print_file.validation_errors.append("SLA print file metadata is missing layer data.")

    @staticmethod
    def _normalize_print_format(format_name):
        formats = {
            "Generic G-code",
            "Klipper G-code",
            "Marlin G-code",
            "Bambu-compatible metadata foundation",
            "CTB foundation",
            "Photon foundation",
        }
        if format_name not in formats:
            raise ValueError(f"Unsupported print file format: {format_name}")
        return format_name

    @staticmethod
    def _print_file_name(name, format_name):
        extension = {
            "Generic G-code": ".gcode",
            "Klipper G-code": ".gcode",
            "Marlin G-code": ".gcode",
            "Bambu-compatible metadata foundation": ".3mf.meta",
            "CTB foundation": ".ctb.meta",
            "Photon foundation": ".photon.meta",
        }[format_name]
        return f"{ManufacturingEngine._program_name(name).lower()}{extension}"

    def _parameters_for_job(self, job):
        job_id = getattr(job, "id", job)
        return next((item for item in self.additive_parameters if item.metadata.get("job_id") == job_id), None)

    def _layout_for_job(self, job):
        job_id = getattr(job, "id", job)
        return next((item for item in self.build_plate_layouts if item.job_id == job_id), None)

    def _slice_for_job(self, job):
        job_id = getattr(job, "id", job)
        return next((item for item in self.additive_slices if item.job_id == job_id), None)

    def _slice_job_for_cam_job(self, cam_job):
        job_id = getattr(cam_job, "id", cam_job)
        return next((item for item in self.product_manager.slice_jobs if item.cam_job_id == job_id), None)

    def _machine_build_volume(self, job):
        profile = self.product_manager.machine_library_manager.profile_for(job.metadata.properties.get("machine_profile_id", ""))
        machine = self.product_manager.machine_library_manager.machine_for(getattr(profile, "machine_id", ""))
        properties = getattr(getattr(machine, "metadata", None), "properties", {}) if machine is not None else {}
        return dict(properties.get("work_envelope", {}))

    @staticmethod
    def _auto_arrange(quantity, dimensions, volume):
        placements = []
        width = float(dimensions.get("x", 20.0))
        depth = float(dimensions.get("y", 20.0))
        spacing = max(width, depth) * 0.15
        columns = max(int(float(volume.get("x", 220.0)) // max(width + spacing, 1.0)), 1)
        for index in range(max(int(quantity), 1)):
            row = index // columns
            column = index % columns
            placements.append({
                "model_id": f"model_{index + 1}",
                "x": column * (width + spacing),
                "y": row * (depth + spacing),
                "rotation": 0.0,
                "scale": 1.0,
                "dimensions": dict(dimensions),
            })
        return placements

    @staticmethod
    def _validate_build_layout(layout, dimensions):
        layout.collisions.clear()
        volume = layout.build_volume
        for placement in layout.placements:
            if float(placement.get("scale", 1.0)) <= 0.0:
                layout.collisions.append({"type": "invalid_scale", "model_id": placement.get("model_id", "")})
            x_extent = float(placement.get("x", 0.0)) + float(dimensions.get("x", 20.0)) * float(placement.get("scale", 1.0))
            y_extent = float(placement.get("y", 0.0)) + float(dimensions.get("y", 20.0)) * float(placement.get("scale", 1.0))
            if x_extent > float(volume.get("x", 0.0)) or y_extent > float(volume.get("y", 0.0)):
                layout.collisions.append({"type": "build_volume", "model_id": placement.get("model_id", "")})
        for left_index, left in enumerate(layout.placements):
            for right in layout.placements[left_index + 1:]:
                if ManufacturingEngine._placements_overlap(left, right):
                    layout.collisions.append({"type": "placement_overlap", "a": left.get("model_id", ""), "b": right.get("model_id", "")})

    @staticmethod
    def _placements_overlap(left, right):
        left_dims = left.get("dimensions", {})
        right_dims = right.get("dimensions", {})
        lx0 = float(left.get("x", 0.0))
        ly0 = float(left.get("y", 0.0))
        lx1 = lx0 + float(left_dims.get("x", 20.0)) * float(left.get("scale", 1.0))
        ly1 = ly0 + float(left_dims.get("y", 20.0)) * float(left.get("scale", 1.0))
        rx0 = float(right.get("x", 0.0))
        ry0 = float(right.get("y", 0.0))
        rx1 = rx0 + float(right_dims.get("x", 20.0)) * float(right.get("scale", 1.0))
        ry1 = ry0 + float(right_dims.get("y", 20.0)) * float(right.get("scale", 1.0))
        return lx0 < rx1 and lx1 > rx0 and ly0 < ry1 and ly1 > ry0

    def _material_density_for_job_id(self, job_id):
        job = self.job_for(job_id)
        material_id = getattr(getattr(job, "metadata", None), "properties", {}).get("material_id", "") if job is not None else ""
        material = self.product_manager.engineering_material_manager.material_for(material_id)
        return float(getattr(material, "density", 1240.0) or 1240.0) / 1000.0

    def _create_sheet_product_records(self, job, process, material, thickness):
        manager = self.product_manager.laser_plasma_manager
        if process == "Laser" and not any(item.cam_job_id == job.id for item in self.product_manager.laser_jobs):
            manager.create_laser_job(job, f"{job.name} Laser Job")
        if process == "Plasma" and not any(item.cam_job_id == job.id for item in self.product_manager.plasma_jobs):
            manager.create_plasma_job(job, f"{job.name} Plasma Job")
        if process in {"Laser", "Plasma"}:
            profile_name = f"{job.name} {process} Material"
            if not any(item.name == profile_name for item in self.product_manager.material_profiles):
                material_type = self._sheet_material_type(material)
                material_profile = manager.create_material_profile(
                    profile_name,
                    material_type,
                    float(thickness),
                    properties={
                        "sheet_manufacturing": True,
                        "material_id": getattr(material, "id", material) or "",
                    },
                )
                manager.create_cutting_profile(
                    material_profile,
                    f"{job.name} {process} Cutting",
                    cut_speed=1200.0 if process == "Laser" else 900.0,
                    travel_speed=3000.0,
                    pass_count=1,
                    kerf_width=0.12 if process == "Laser" else 1.0,
                    pierce_delay=0.2 if process == "Laser" else 0.8,
                    properties={"sheet_manufacturing": True, "process": process},
                )
        nesting = self.product_manager.nesting_manager
        sheet = job.metadata.properties.get("sheet_size", {"x": 600.0, "y": 400.0})
        library_name = "Sheet Manufacturing Stock"
        library = next((item for item in self.product_manager.stock_libraries if item.name == library_name), None)
        if library is None:
            library = nesting.create_stock_library(library_name)
        stock_name = f"{job.name} Sheet Stock"
        if not any(item.name == stock_name for item in self.product_manager.stock_profiles):
            nesting.create_stock_profile(
                library,
                stock_name,
                length=float(sheet.get("x", 600.0)),
                width=float(sheet.get("y", 400.0)),
                thickness=float(thickness),
                material=material,
                properties={"sheet_manufacturing": True, "process": process},
            )

    def _sync_sheet_product_operations(self, job, params):
        existing = self._sheet_operation_for(job, params)
        if existing is not None:
            existing.metadata.properties["sheet_cut_parameters"] = params.to_dict()
            return existing
        setup = self._first_setup(job)
        manager = self.product_manager.laser_plasma_manager
        if params.process == "Laser":
            laser_job = next((item for item in self.product_manager.laser_jobs if item.cam_job_id == job.id), None)
            if laser_job is None:
                laser_job = manager.create_laser_job(job, f"{job.name} Laser Job")
            operation = manager.create_laser_operation(
                laser_job,
                setup=setup,
                operation_type=params.operation_type,
                name=f"{job.name} {params.operation_type}",
                laser_power=params.power,
                cut_speed=params.speed,
                travel_speed=params.metadata.get("travel_speed", 3000.0),
                pass_count=params.pass_count,
            )
        elif params.process == "Plasma":
            plasma_job = next((item for item in self.product_manager.plasma_jobs if item.cam_job_id == job.id), None)
            if plasma_job is None:
                plasma_job = manager.create_plasma_job(job, f"{job.name} Plasma Job")
            operation = manager.create_plasma_operation(
                plasma_job,
                setup=setup,
                operation_type="Plasma Cut",
                name=f"{job.name} Plasma Cut",
                kerf_width=params.kerf_width,
                pierce_delay=params.pierce.get("delay", 0.8),
                pierce_height=params.pierce.get("height", 3.0),
                cut_height=params.height_control.get("cut_height", 1.5),
            )
        else:
            operation = self.create_operation(
                job,
                "Waterjet Cut",
                name=f"{job.name} Waterjet Cut",
                feeds={"feed_rate": params.speed},
                metadata={"sheet_manufacturing": True, "process": params.process},
            )
        operation.metadata.properties.update({
            "sheet_manufacturing": True,
            "sheet_job_id": job.id,
            "sheet_process": params.process,
            "sheet_cut_parameters": params.to_dict(),
        })
        return operation

    def _sync_nesting_product_records(self, job, layout):
        nesting = self.product_manager.nesting_manager
        stock_profile = next(
            (
                item for item in self.product_manager.stock_profiles
                if item.name == f"{job.name} Sheet Stock"
            ),
            None,
        )
        profile = next(
            (
                item for item in self.product_manager.nesting_profiles
                if item.name == f"{job.name} Nest Profile"
            ),
            None,
        )
        if profile is None:
            profile = nesting.create_profile(
                f"{job.name} Nest Profile",
                stock_profiles=[stock_profile] if stock_profile is not None else [],
                machine_profile=job.metadata.properties.get("machine_profile_id", ""),
                properties={"sheet_manufacturing": True},
            )
        if not any(item.cam_job_id == job.id for item in self.product_manager.nesting_jobs):
            nesting.create_job(
                job,
                profile,
                f"{job.name} Nest Job",
                enabled=True,
                properties={
                    "sheet_manufacturing": True,
                    "utilization": layout.utilization,
                },
            )

    @staticmethod
    def _normalize_sheet_part(part, index):
        data = dict(part or {})
        width = float(data.get("width", data.get("x", 100.0)))
        height = float(data.get("height", data.get("y", 60.0)))
        outline = data.get("outline") or [(0.0, 0.0), (width, 0.0), (width, height), (0.0, height), (0.0, 0.0)]
        return {
            "id": data.get("id", f"sheet_part_{index + 1}"),
            "name": data.get("name", f"Sheet Part {index + 1}"),
            "width": width,
            "height": height,
            "quantity": int(data.get("quantity", 1)),
            "priority": int(data.get("priority", index)),
            "group": data.get("group", ""),
            "outline": [list(point) for point in outline],
        }

    @staticmethod
    def _auto_nest_sheet_parts(parts, sheet, spacing, rotation_optimization=True):
        placements = []
        sheet_width = float(sheet.get("x", sheet.get("width", 600.0)))
        cursor_x = spacing
        cursor_y = spacing
        row_height = 0.0
        for part in sorted(parts, key=lambda item: item.get("priority", 0)):
            for quantity_index in range(max(int(part.get("quantity", 1)), 1)):
                width = float(part.get("width", 100.0))
                height = float(part.get("height", 60.0))
                rotation = 0.0
                if rotation_optimization and width > height and cursor_x + width > sheet_width and cursor_x + height <= sheet_width:
                    width, height = height, width
                    rotation = 90.0
                if cursor_x + width > sheet_width:
                    cursor_x = spacing
                    cursor_y += row_height + spacing
                    row_height = 0.0
                placements.append({
                    "id": str(uuid4()),
                    "part_id": part.get("id", ""),
                    "part_name": part.get("name", ""),
                    "x": cursor_x,
                    "y": cursor_y,
                    "width": width,
                    "height": height,
                    "rotation": rotation,
                    "priority": part.get("priority", 0),
                    "group": part.get("group", ""),
                    "quantity_index": quantity_index,
                    "outline": [list(point) for point in part.get("outline", [])],
                })
                cursor_x += width + spacing
                row_height = max(row_height, height)
        return placements

    @staticmethod
    def _part_groups(parts):
        groups = {}
        for part in parts:
            group = part.get("group", "") or "Default"
            groups.setdefault(group, 0)
            groups[group] += int(part.get("quantity", 1))
        return groups

    @staticmethod
    def _validate_sheet_nest(layout):
        layout.collisions.clear()
        sheet_width = float(layout.sheet_size.get("x", layout.sheet_size.get("width", 0.0)))
        sheet_height = float(layout.sheet_size.get("y", layout.sheet_size.get("height", 0.0)))
        for placement in layout.placements:
            if float(placement.get("x", 0.0)) < 0.0 or float(placement.get("y", 0.0)) < 0.0:
                layout.collisions.append({"type": "negative_position", "part_id": placement.get("part_id", "")})
            if float(placement.get("x", 0.0)) + float(placement.get("width", 0.0)) > sheet_width:
                layout.collisions.append({"type": "sheet_width", "part_id": placement.get("part_id", "")})
            if float(placement.get("y", 0.0)) + float(placement.get("height", 0.0)) > sheet_height:
                layout.collisions.append({"type": "sheet_height", "part_id": placement.get("part_id", "")})
        for left_index, left in enumerate(layout.placements):
            for right in layout.placements[left_index + 1:]:
                if ManufacturingEngine._sheet_placements_overlap(left, right, layout.spacing):
                    layout.collisions.append({"type": "part_collision", "a": left.get("part_id", ""), "b": right.get("part_id", "")})

    @staticmethod
    def _sheet_placements_overlap(left, right, spacing=0.0):
        lx0 = float(left.get("x", 0.0)) - spacing
        ly0 = float(left.get("y", 0.0)) - spacing
        lx1 = float(left.get("x", 0.0)) + float(left.get("width", 0.0)) + spacing
        ly1 = float(left.get("y", 0.0)) + float(left.get("height", 0.0)) + spacing
        rx0 = float(right.get("x", 0.0))
        ry0 = float(right.get("y", 0.0))
        rx1 = float(right.get("x", 0.0)) + float(right.get("width", 0.0))
        ry1 = float(right.get("y", 0.0)) + float(right.get("height", 0.0))
        return lx0 < rx1 and lx1 > rx0 and ly0 < ry1 and ly1 > ry0

    @staticmethod
    def _sheet_utilization(layout):
        sheet_area = float(layout.sheet_size.get("x", layout.sheet_size.get("width", 0.0))) * float(layout.sheet_size.get("y", layout.sheet_size.get("height", 0.0)))
        part_area = sum(float(item.get("width", 0.0)) * float(item.get("height", 0.0)) for item in layout.placements)
        return (part_area / sheet_area) if sheet_area > 0.0 else 0.0

    @staticmethod
    def _sheet_remnants(layout):
        if not layout.placements:
            return []
        used_height = max(float(item.get("y", 0.0)) + float(item.get("height", 0.0)) for item in layout.placements)
        sheet_height = float(layout.sheet_size.get("y", layout.sheet_size.get("height", 0.0)))
        sheet_width = float(layout.sheet_size.get("x", layout.sheet_size.get("width", 0.0)))
        remaining = max(sheet_height - used_height, 0.0)
        return [{"x": 0.0, "y": used_height, "width": sheet_width, "height": remaining}] if remaining > 0.0 else []

    @staticmethod
    def _placement_outline(placement):
        x = float(placement.get("x", 0.0))
        y = float(placement.get("y", 0.0))
        width = float(placement.get("width", 0.0))
        height = float(placement.get("height", 0.0))
        return [(x, y), (x + width, y), (x + width, y + height), (x, y + height), (x, y)]

    @staticmethod
    def _apply_kerf_compensation(points, params):
        if params.compensation == "Centerline" or not points:
            return [tuple(point) for point in points]
        offset = params.kerf_width * 0.5
        if params.compensation == "Inside":
            offset *= -1.0
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        cx = (min(xs) + max(xs)) * 0.5
        cy = (min(ys) + max(ys)) * 0.5
        compensated = []
        for x, y in points:
            dx = 1.0 if float(x) >= cx else -1.0
            dy = 1.0 if float(y) >= cy else -1.0
            compensated.append((float(x) + dx * offset, float(y) + dy * offset))
        return compensated

    @staticmethod
    def _lead_path(points, metadata, incoming=True):
        if not points:
            return []
        length = float(metadata.get("length", 0.0))
        start = points[0] if incoming else points[-1]
        if incoming:
            return [(float(start[0]) - length, float(start[1])), tuple(start)]
        return [tuple(start), (float(start[0]) + length, float(start[1]))]

    @staticmethod
    def _estimate_sheet_cut_time(points, params):
        length = ManufacturingEngine._path_length(points)
        pierce_delay = float(params.pierce.get("delay", 0.0))
        passes = max(int(params.pass_count), 1)
        return ((length / max(params.speed, 1.0)) * 60.0 + pierce_delay) * passes

    def _sheet_operation_for(self, job, params):
        job_id = getattr(job, "id", job)
        process = getattr(params, "process", None)
        return next(
            (
                item for item in self.product_manager.cam_operations
                if item.metadata.properties.get("sheet_job_id") == job_id
                and (process is None or item.metadata.properties.get("sheet_process") == process)
            ),
            None,
        )

    def _sheet_parameters_for_job(self, job):
        job_id = getattr(job, "id", job)
        process = getattr(getattr(job, "metadata", None), "properties", {}).get("sheet_process", "")
        return next(
            (
                item for item in self.sheet_parameters
                if item.metadata.get("job_id") == job_id and (not process or item.process == process)
            ),
            None,
        )

    def _sheet_layout_for_job(self, job):
        job_id = getattr(job, "id", job)
        return next((item for item in self.sheet_nest_layouts if item.job_id == job_id), None)

    @staticmethod
    def _validate_sheet_cut_path(cut_path):
        cut_path.validation_errors.clear()
        cut_path.validation_warnings.clear()
        if len(cut_path.compensated_points) < 2:
            cut_path.validation_errors.append("Sheet cut path requires at least two points.")
        if cut_path.kerf_width < 0.0:
            cut_path.validation_errors.append("Sheet cut path has invalid kerf width.")
        if cut_path.estimated_time <= 0.0:
            cut_path.validation_warnings.append("Sheet cut path has zero estimated cutting time.")

    def _sheet_program_content(self, job, cut_paths, controller, program_name):
        params = self._sheet_parameters_for_job(job) or SheetCutParameters(job.metadata.properties.get("sheet_process", "Laser"))
        lines = [
            f"; {program_name}",
            f"; CONTROLLER: {controller}",
            f"; PROCESS: {job.metadata.properties.get('sheet_process', '')}",
            f"; MATERIAL: {job.metadata.properties.get('material_id', '')}",
            f"; MACHINE: {job.metadata.properties.get('machine_profile_id', '')}",
            "G21",
            "G90",
        ]
        if controller == "GRBL Laser" or params.process == "Laser":
            lines.append(f"M4 S{params.power:.0f}")
        if params.process == "Plasma":
            lines.append(f"; PLASMA_CONTROLLER_METADATA pierce={params.pierce} height_control={params.height_control} consumable={params.consumable}")
        if params.process == "Waterjet":
            lines.append(f"; WATERJET_CONTROLLER_METADATA {params.waterjet}")
        for path in cut_paths:
            points = path.compensated_points
            if not points:
                continue
            lines.append(f"; PATH {path.metadata.get('cut_sequence', 0)} {path.path_type}")
            if path.pierce_points:
                pierce = path.pierce_points[0]
                lines.append(f"G0 X{float(pierce[0]):.3f} Y{float(pierce[1]):.3f}")
                lines.append(f"; PIERCE delay={params.pierce.get('delay', 0.0)}")
            for point in path.lead_in:
                lines.append(f"G1 X{float(point[0]):.3f} Y{float(point[1]):.3f} F{params.speed:.0f}")
            for point in points[1:]:
                lines.append(f"G1 X{float(point[0]):.3f} Y{float(point[1]):.3f} F{params.speed:.0f}")
            for point in path.lead_out:
                lines.append(f"G1 X{float(point[0]):.3f} Y{float(point[1]):.3f} F{params.speed:.0f}")
            lines.append("G0 Z5.000")
        if params.process == "Laser":
            lines.append("M5")
        lines.extend(["M30", "%"])
        return "\n".join(lines)

    def _validate_sheet_program(self, program):
        program.validation_errors.clear()
        program.validation_warnings.clear()
        if not program.content:
            program.validation_errors.append("Sheet program is empty.")
        if "G21" not in program.content:
            program.validation_errors.append("Sheet program is missing units setup.")
        if not program.cut_path_ids:
            program.validation_errors.append("Sheet program requires at least one cut path.")

    def _normalize_sheet_controller(self, controller):
        if controller not in self.SHEET_PROGRAM_CONTROLLERS:
            raise ValueError(f"Unsupported sheet program controller: {controller}")
        return controller

    @staticmethod
    def _sheet_material_type(material):
        name = getattr(material, "name", material) or ""
        lowered = str(name).lower()
        if "acrylic" in lowered:
            return "Acrylic"
        if "mdf" in lowered:
            return "MDF"
        if "plywood" in lowered or "wood" in lowered:
            return "Plywood"
        if "steel" in lowered:
            return "Steel"
        if "aluminum" in lowered or "aluminium" in lowered:
            return "Aluminium"
        return "Wood"

    @staticmethod
    def _default_joint_limits(robot_type):
        count = {"6-axis": 6, "SCARA": 4, "Delta": 3, "Cartesian": 3, "Custom": 6}.get(robot_type, 6)
        return [
            {"axis": f"J{index + 1}", "minimum": -180.0, "maximum": 180.0, "velocity": 180.0}
            for index in range(count)
        ]

    def _robot_profile_for(self, profile):
        if isinstance(profile, RobotProfile):
            return profile if profile in self.robot_profiles else None
        return next((item for item in self.robot_profiles if item.id == profile or item.name == profile), None)

    def _robot_profile_for_job(self, job):
        job = self.job_for(job)
        profile_id = getattr(getattr(job, "metadata", None), "properties", {}).get("robot_profile_id", "") if job is not None else ""
        return self._robot_profile_for(profile_id)

    def _robot_motion_for(self, motion):
        if isinstance(motion, RobotMotionCommand):
            return motion if motion in self.robot_motions else None
        return next((item for item in self.robot_motions if item.id == motion), None)

    def _robot_trajectory_for_job(self, job):
        job_id = getattr(job, "id", job)
        return next((item for item in self.robot_trajectories if item.job_id == job_id), None)

    def _default_frame_id(self, job):
        job_id = getattr(job, "id", job)
        frame = next((item for item in self.robot_frames if item.job_id == job_id and item.frame_type == "User Frame"), None)
        if frame is None:
            frame = next((item for item in self.robot_frames if item.job_id == job_id and item.frame_type == "World"), None)
        return getattr(frame, "id", "")

    @staticmethod
    def _frame_transform(origin, rotation):
        return {
            "translation": {
                "x": float(origin.get("x", 0.0)),
                "y": float(origin.get("y", 0.0)),
                "z": float(origin.get("z", 0.0)),
            },
            "rotation": {
                "rx": float(rotation.get("rx", origin.get("rx", 0.0))),
                "ry": float(rotation.get("ry", origin.get("ry", 0.0))),
                "rz": float(rotation.get("rz", origin.get("rz", 0.0))),
            },
        }

    @staticmethod
    def _pose_distance(pose):
        return (
            float(pose.get("x", 0.0)) ** 2
            + float(pose.get("y", 0.0)) ** 2
            + float(pose.get("z", 0.0)) ** 2
        ) ** 0.5

    @staticmethod
    def _joints_within_limits(profile, joints):
        if profile is None:
            return False
        limits = getattr(profile, "joint_limits", []) or []
        if len(joints) > len(limits):
            return False
        for index, value in enumerate(joints):
            limit = limits[index]
            if float(value) < float(limit.get("minimum", -180.0)) or float(value) > float(limit.get("maximum", 180.0)):
                return False
        return True

    def _validate_robot_profile(self, report, profile):
        if profile.robot_type not in self.ROBOT_TYPES:
            report.add_error(f"Robot profile '{profile.name}' has unsupported robot type.")
        if profile.machine_profile_id and not self._id_exists(self.product_manager.machine_profiles, profile.machine_profile_id):
            report.add_error(f"Robot profile '{profile.name}' references a missing machine profile.")
        if profile.payload < 0.0:
            report.add_error(f"Robot profile '{profile.name}' has invalid payload.")
        if profile.reach <= 0.0:
            report.add_error(f"Robot profile '{profile.name}' has invalid reach.")
        for limit in profile.joint_limits:
            if float(limit.get("minimum", 0.0)) >= float(limit.get("maximum", 0.0)):
                report.add_error(f"Robot profile '{profile.name}' has invalid joint limits.")

    def _validate_robot_frame(self, report, frame):
        if frame.job_id and self.job_for(frame.job_id) is None:
            report.add_error(f"Robot frame '{frame.name}' references a missing job.")
        if frame.frame_type not in self.ROBOT_FRAME_TYPES:
            report.add_error(f"Robot frame '{frame.name}' has unsupported frame type.")

    def _validate_robot_motion(self, motion, profile):
        motion.metadata.setdefault("validation_errors", [])
        errors = motion.metadata["validation_errors"]
        errors.clear()
        if profile is None:
            errors.append("Robot motion requires a robot profile.")
        if motion.motion_type not in self.ROBOT_MOTION_TYPES:
            errors.append("Robot motion type is unsupported.")
        if motion.joints and not self._joints_within_limits(profile, motion.joints):
            errors.append("Robot motion violates joint limits.")
        if motion.target and profile is not None and self._pose_distance(motion.target) > profile.reach:
            errors.append("Robot motion target exceeds robot reach.")
        if motion.velocity <= 0.0:
            errors.append("Robot motion requires positive velocity.")
        if motion.acceleration <= 0.0:
            errors.append("Robot motion requires positive acceleration.")

    def _validate_robot_trajectory(self, trajectory):
        trajectory.validation_errors.clear()
        trajectory.validation_warnings.clear()
        if not trajectory.motion_ids:
            trajectory.validation_errors.append("Robot trajectory requires at least one motion.")
        if not trajectory.waypoints:
            trajectory.validation_errors.append("Robot trajectory requires waypoints.")
        for motion_id in trajectory.motion_ids:
            motion = self._robot_motion_for(motion_id)
            if motion is None:
                trajectory.validation_errors.append("Robot trajectory references a missing motion.")
            elif motion.metadata.get("validation_errors"):
                trajectory.validation_errors.extend(motion.metadata.get("validation_errors", []))

    def _validate_robot_program(self, program):
        program.validation_errors.clear()
        program.validation_warnings.clear()
        if not program.content:
            program.validation_errors.append("Robot program is empty.")
        if not program.trajectory_id:
            program.validation_errors.append("Robot program requires a trajectory.")
        if "PROGRAM" not in program.content and "PROC" not in program.content and "DEF" not in program.content:
            program.validation_warnings.append("Robot program has minimal controller header metadata.")

    def _motion_waypoint(self, motion):
        return {
            "motion_id": motion.id,
            "motion_type": motion.motion_type,
            "target": dict(motion.target),
            "joints": list(motion.joints),
            "frame_id": motion.frame_id,
            "velocity": motion.velocity,
            "acceleration": motion.acceleration,
            "blend_radius": motion.blend_radius,
            "order": motion.order,
        }

    @staticmethod
    def _interpolate_linear(previous, waypoint):
        if previous is None:
            return [waypoint]
        start = previous.get("target", {})
        end = waypoint.get("target", {})
        steps = 3
        path = []
        for index in range(1, steps + 1):
            ratio = index / steps
            path.append({
                "x": float(start.get("x", 0.0)) + (float(end.get("x", 0.0)) - float(start.get("x", 0.0))) * ratio,
                "y": float(start.get("y", 0.0)) + (float(end.get("y", 0.0)) - float(start.get("y", 0.0))) * ratio,
                "z": float(start.get("z", 0.0)) + (float(end.get("z", 0.0)) - float(start.get("z", 0.0))) * ratio,
                "motion_id": waypoint.get("motion_id", ""),
            })
        return path

    @staticmethod
    def _interpolate_circular(previous, waypoint, motion):
        if previous is None:
            return [waypoint]
        center = motion.metadata.get("center", {"x": 0.0, "y": 0.0, "z": waypoint.get("target", {}).get("z", 0.0)})
        return [
            {
                "center": dict(center),
                "target": dict(waypoint.get("target", {})),
                "motion_id": waypoint.get("motion_id", ""),
                "segment": index,
            }
            for index in range(3)
        ]

    @staticmethod
    def _motion_time(motion):
        distance = ManufacturingEngine._pose_distance(motion.target)
        joint_distance = sum(abs(float(value)) for value in motion.joints)
        travel = max(distance, joint_distance)
        return travel / max(motion.velocity, 1.0)

    def _robot_program_content(self, job, trajectory, controller, program_name):
        frames = [frame for frame in self.robot_frames if frame.job_id == job.id]
        motions = [self._robot_motion_for(item) for item in trajectory.motion_ids]
        motions = [motion for motion in motions if motion is not None]
        header = [
            f"; PROGRAM {program_name}",
            f"; CONTROLLER: {controller}",
            f"; PROCESS: {job.metadata.properties.get('robot_process', '')}",
            f"; ROBOT_PROFILE: {job.metadata.properties.get('robot_profile_id', '')}",
        ]
        if controller == "ABB RAPID foundation":
            lines = [f"MODULE {program_name}", "PROC main()"]
            lines.extend([f"! FRAME {frame.name} {frame.origin}" for frame in frames])
            lines.extend(self._robot_motion_line(motion, "ABB") for motion in motions)
            lines.extend(["ENDPROC", "ENDMODULE"])
            return "\n".join(lines)
        if controller == "KUKA KRL foundation":
            lines = [f"DEF {program_name}()"]
            lines.extend([f"; FRAME {frame.name} {frame.origin}" for frame in frames])
            lines.extend(self._robot_motion_line(motion, "KUKA") for motion in motions)
            lines.append("END")
            return "\n".join(lines)
        if controller == "URScript foundation":
            lines = [f"def {program_name.lower()}():"]
            lines.extend([f"  # FRAME {frame.name} {frame.origin}" for frame in frames])
            lines.extend(f"  {self._robot_motion_line(motion, 'UR')}" for motion in motions)
            lines.append("end")
            return "\n".join(lines)
        if controller == "Fanuc TP metadata":
            return "\n".join(header + ["/PROG " + program_name, *[self._robot_motion_line(motion, "FANUC") for motion in motions], "/END"])
        if controller == "Yaskawa INFORM metadata":
            return "\n".join(header + ["/JOB", f"//NAME {program_name}", *[self._robot_motion_line(motion, "YASKAWA") for motion in motions], "END"])
        return "\n".join(header + ["PROGRAM " + program_name, *[self._robot_motion_line(motion, "GENERIC") for motion in motions], "END PROGRAM"])

    @staticmethod
    def _robot_motion_line(motion, dialect):
        target = motion.target
        joints = ",".join(f"{float(value):.3f}" for value in motion.joints)
        pose = "X{:.3f} Y{:.3f} Z{:.3f} RX{:.3f} RY{:.3f} RZ{:.3f}".format(
            float(target.get("x", 0.0)),
            float(target.get("y", 0.0)),
            float(target.get("z", 0.0)),
            float(target.get("rx", 0.0)),
            float(target.get("ry", 0.0)),
            float(target.get("rz", 0.0)),
        )
        if dialect == "ABB":
            return f"Move{motion.motion_type[0]} [{pose}], v{motion.velocity:.0f}, z{motion.blend_radius:.0f};"
        if dialect == "KUKA":
            return f"{'PTP' if motion.motion_type == 'Joint' else 'LIN'} {{{pose}}} ; joints {joints}"
        if dialect == "UR":
            return f"{'movej' if motion.motion_type == 'Joint' else 'movel'}([{joints}], a={motion.acceleration:.3f}, v={motion.velocity:.3f})"
        if dialect == "FANUC":
            return f"J {joints} {motion.velocity:.0f}% CNT{motion.blend_radius:.0f} ; {pose}"
        if dialect == "YASKAWA":
            return f"MOVJ VJ={motion.velocity:.2f} ; {pose} J={joints}"
        return f"{motion.motion_type.upper()} {pose} J[{joints}] V{motion.velocity:.3f} A{motion.acceleration:.3f} B{motion.blend_radius:.3f}"

    def _normalize_robot_controller(self, controller):
        if controller not in self.ROBOT_PROGRAM_CONTROLLERS:
            raise ValueError(f"Unsupported robot program controller: {controller}")
        return controller

    def _simulation_process_for_job(self, job):
        properties = getattr(getattr(job, "metadata", None), "properties", {})
        if properties.get("additive_manufacturing"):
            return "Additive"
        if properties.get("sheet_manufacturing"):
            return "Sheet"
        if properties.get("robotics_motion"):
            return "Robotics"
        return "CNC"

    def _simulation_job_for(self, simulation):
        if isinstance(simulation, SimulationJob):
            return simulation if simulation in self.simulation_jobs else None
        return next((item for item in self.simulation_jobs if item.id == simulation or item.name == simulation), None)

    def _simulation_session_for(self, simulation):
        simulation_id = getattr(simulation, "id", simulation)
        return next((item for item in self.simulation_sessions if item.simulation_job_id == simulation_id), None)

    def _simulation_collision_report_for(self, simulation):
        simulation_id = getattr(simulation, "id", simulation)
        return next((item for item in self.simulation_collision_reports if item.simulation_job_id == simulation_id), None)

    def _simulation_verification_report_for(self, simulation):
        simulation_id = getattr(simulation, "id", simulation)
        return next((item for item in self.simulation_verification_reports if item.simulation_job_id == simulation_id), None)

    def _simulation_replay_steps(self, job, process_type):
        if process_type == "CNC":
            return self._cnc_simulation_replay(job)
        if process_type == "Additive":
            return self._additive_simulation_replay(job)
        if process_type == "Sheet":
            return self._sheet_simulation_replay(job)
        if process_type == "Robotics":
            return self._robotics_simulation_replay(job)
        return []

    def _cnc_simulation_replay(self, job):
        steps = []
        for toolpath in [item for item in self.toolpaths if item.job_id == job.id]:
            for index, move in enumerate(toolpath.moves):
                steps.append({
                    "process": "CNC",
                    "replay_type": "Rapid" if move.move_type == "Rapid" else "Cut",
                    "toolpath_id": toolpath.id,
                    "operation_id": toolpath.operation_id,
                    "step": index,
                    "position": {"x": move.x, "y": move.y, "z": move.z},
                    "feed": move.feed,
                    "spindle": toolpath.cutting_parameters.rpm,
                    "tool_engagement": toolpath.cutting_parameters.tool_engagement,
                    "material_removal": toolpath.cutting_parameters.material_removal_estimate / max(len(toolpath.moves), 1),
                    "visualization_metadata": {
                        "rapid": move.move_type == "Rapid",
                        "cut": move.move_type != "Rapid",
                        "feed_progression": move.feed,
                    },
                })
        return steps

    def _additive_simulation_replay(self, job):
        steps = []
        for result in [item for item in self.additive_slices if item.job_id == job.id]:
            for layer in result.layers:
                steps.append({
                    "process": "Additive",
                    "technology": result.technology,
                    "replay_type": "Layer",
                    "slice_id": result.id,
                    "layer_index": layer.index,
                    "z": layer.z,
                    "height": layer.height,
                    "perimeters": len(layer.perimeters),
                    "walls": len(layer.walls),
                    "infill": len(layer.infill),
                    "supports": len(layer.supports),
                    "travel": len(layer.travel),
                    "extrusion_replay_metadata": {
                        "extrusion": bool(layer.perimeters or layer.walls or layer.infill),
                        "support_replay": bool(layer.supports),
                        "travel_replay": bool(layer.travel),
                    },
                    "material_usage": dict(result.material_usage),
                })
        return steps

    def _sheet_simulation_replay(self, job):
        steps = []
        process = getattr(getattr(job, "metadata", None), "properties", {}).get("sheet_process", "Laser")
        for path in [item for item in self.sheet_cut_paths if item.job_id == job.id]:
            points = path.compensated_points or path.points
            if path.pierce_points:
                for pierce in path.pierce_points:
                    steps.append({
                        "process": "Sheet",
                        "sheet_process": process,
                        "replay_type": "Pierce",
                        "cut_path_id": path.id,
                        "position": {"x": float(pierce[0]), "y": float(pierce[1])},
                        "kerf": path.kerf_width,
                    })
            for index, point in enumerate(points):
                steps.append({
                    "process": "Sheet",
                    "sheet_process": process,
                    "replay_type": process,
                    "cut_path_id": path.id,
                    "step": index,
                    "position": {"x": float(point[0]), "y": float(point[1])},
                    "kerf_visualization_metadata": {
                        "kerf_width": path.kerf_width,
                        "path_type": path.path_type,
                    },
                    "estimated_cutting_time": path.estimated_time / max(len(points), 1),
                })
        return steps

    def _robotics_simulation_replay(self, job):
        trajectory = self._robot_trajectory_for_job(job)
        if trajectory is None:
            return []
        steps = []
        for index, waypoint in enumerate(trajectory.waypoints):
            motion = self._robot_motion_for(waypoint.get("motion_id", ""))
            steps.append({
                "process": "Robotics",
                "replay_type": "Waypoint",
                "trajectory_id": trajectory.id,
                "motion_id": waypoint.get("motion_id", ""),
                "motion_type": waypoint.get("motion_type", ""),
                "step": index,
                "tcp": dict(waypoint.get("target", {})),
                "joints": list(waypoint.get("joints", [])),
                "velocity": waypoint.get("velocity", 0.0),
                "cycle_estimate": self._motion_time(motion) if motion is not None else 0.0,
                "reach_verification": self.inverse_kinematics(self._robot_profile_for_job(job), waypoint.get("target", {})).get("reachable", False),
                "joint_limit_verification": self._joints_within_limits(self._robot_profile_for_job(job), waypoint.get("joints", [])),
            })
        return steps

    def _simulation_estimated_time(self, process_type, replay):
        if process_type == "CNC":
            return sum(float(step.get("material_removal", 0.0)) for step in replay) + len(replay) * 0.05
        if process_type == "Additive":
            return len(replay) * 0.75
        if process_type == "Sheet":
            return sum(float(step.get("estimated_cutting_time", 0.0)) for step in replay) + len([step for step in replay if step.get("replay_type") == "Pierce"]) * 0.5
        if process_type == "Robotics":
            return sum(float(step.get("cycle_estimate", 0.0)) for step in replay)
        return float(len(replay))

    def _simulation_material_usage(self, job, process_type, replay):
        if process_type == "CNC":
            return {"material_removed": sum(float(step.get("material_removal", 0.0)) for step in replay)}
        if process_type == "Additive":
            result = self._slice_for_job(job)
            return dict(getattr(result, "material_usage", {}) or {})
        if process_type == "Sheet":
            layout = self._sheet_layout_for_job(job)
            return {"sheet_utilization": getattr(layout, "utilization", 0.0), "cut_length": len([step for step in replay if step.get("replay_type") != "Pierce"])}
        if process_type == "Robotics":
            profile = self._robot_profile_for_job(job)
            return {"payload_capacity": getattr(profile, "payload", 0.0)}
        return {}

    def _simulation_tool_usage(self, job, process_type, replay):
        if process_type == "CNC":
            return {
                toolpath.tool_id: len(toolpath.moves)
                for toolpath in self.toolpaths
                if toolpath.job_id == job.id
            }
        if process_type == "Additive":
            return {"layers": len(replay), "support_layers": len([step for step in replay if step.get("supports", 0) > 0])}
        if process_type == "Sheet":
            return {"cut_paths": len({step.get("cut_path_id") for step in replay if step.get("cut_path_id")})}
        if process_type == "Robotics":
            return {"waypoints": len(replay), "joint_replay": len([step for step in replay if step.get("joints")])}
        return {}

    def _simulation_collision_data(self, job, simulation, session):
        collisions = []
        warnings = []
        categories = [
            "tool_vs_stock",
            "tool_vs_fixture",
            "machine_envelope",
            "robot_self_collision_foundation",
            "robot_workspace_collision_foundation",
            "build_plate_collision",
            "sheet_collision",
            "travel_collision",
        ]
        if simulation.process_type == "CNC":
            for step in session.replay_steps:
                position = step.get("position", {})
                if float(position.get("z", 0.0)) < -1000.0:
                    collisions.append({"type": "tool_vs_stock", "step": step.get("step", 0)})
        if simulation.process_type == "Additive":
            layout = self._layout_for_job(job)
            if layout is not None and not layout.valid:
                collisions.extend(dict(item) for item in layout.collisions)
        if simulation.process_type == "Sheet":
            layout = self._sheet_layout_for_job(job)
            if layout is not None and not layout.valid:
                collisions.extend(dict(item) for item in layout.collisions)
        if simulation.process_type == "Robotics":
            for step in session.replay_steps:
                if not step.get("reach_verification", True):
                    collisions.append({"type": "robot_workspace_collision_foundation", "step": step.get("step", 0)})
                if not step.get("joint_limit_verification", True):
                    collisions.append({"type": "robot_self_collision_foundation", "step": step.get("step", 0)})
        if not session.replay_steps:
            warnings.append("Simulation contains no replay steps.")
        return collisions, warnings, categories

    def _simulation_verification_checks(self, simulation, session, collision):
        process = simulation.process_type
        checks = {
            "simulation_compatibility": process in self.SIMULATION_PROCESS_TYPES,
            "machine_compatibility": bool(self.job_for(simulation.manufacturing_job_id)),
            "collision_validity": collision.valid,
            "replay_validity": session.valid and bool(session.replay_steps),
            "program_validity": True,
            "operation_ordering": True,
            "manufacturing_readiness": collision.valid and session.valid and bool(session.replay_steps),
        }
        job = self.job_for(simulation.manufacturing_job_id)
        if process == "CNC":
            checks.update({
                "toolpath_verification": bool([item for item in self.toolpaths if item.job_id == simulation.manufacturing_job_id]),
                "program_verification": bool([item for item in self.generated_programs if item.job_id == simulation.manufacturing_job_id]),
            })
        if process == "Additive":
            checks.update({
                "build_verification": bool(self._slice_for_job(job)),
                "program_verification": bool([item for item in self.additive_print_files if item.job_id == simulation.manufacturing_job_id]),
            })
        if process == "Sheet":
            checks.update({
                "toolpath_verification": bool([item for item in self.sheet_cut_paths if item.job_id == simulation.manufacturing_job_id]),
                "program_verification": bool([item for item in self.sheet_programs if item.job_id == simulation.manufacturing_job_id]),
                "nesting_verification": bool(self._sheet_layout_for_job(job)),
            })
        if process == "Robotics":
            checks.update({
                "trajectory_verification": bool(self._robot_trajectory_for_job(job)),
                "program_verification": bool([item for item in self.robot_programs if item.job_id == simulation.manufacturing_job_id]),
            })
        return checks

    def _validate_simulation_job(self, simulation):
        simulation.validation_errors.clear()
        simulation.validation_warnings.clear()
        if self.job_for(simulation.manufacturing_job_id) is None:
            simulation.validation_errors.append("Simulation references a missing manufacturing job.")
        if simulation.process_type not in self.SIMULATION_PROCESS_TYPES:
            simulation.validation_errors.append("Simulation process type is unsupported.")
        if not simulation.settings:
            simulation.validation_warnings.append("Simulation uses default settings.")

    @staticmethod
    def _validate_simulation_session(session):
        session.validation_errors.clear()
        session.validation_warnings.clear()
        if not session.replay_steps:
            session.validation_errors.append("Simulation session requires replay steps.")
        if session.progress < 1.0:
            session.validation_warnings.append("Simulation session is not complete.")

    def _protocol_for_profile(self, profile):
        machine = self.product_manager.machine_library_manager.machine_for(getattr(profile, "machine_id", ""))
        firmware = str(getattr(getattr(machine, "metadata", None), "firmware", "") or "").lower()
        category = str(getattr(getattr(machine, "metadata", None), "machine_category", "") or "").lower()
        if "klipper" in firmware:
            return "Klipper"
        if "marlin" in firmware:
            return "Marlin"
        if "grbl" in firmware:
            return "GRBL"
        if "linuxcnc" in firmware:
            return "LinuxCNC"
        if "mach3" in firmware:
            return "Mach3"
        if "mach4" in firmware:
            return "Mach4"
        if "fanuc" in firmware:
            return "Fanuc foundation"
        if "haas" in firmware:
            return "Haas foundation"
        if "siemens" in firmware:
            return "Siemens foundation"
        if "printer" in category:
            return "Klipper"
        if "laser" in category:
            return "GRBL"
        return "GRBL"

    def _communication_capabilities(self, profile, protocol):
        machine = self.product_manager.machine_library_manager.machine_for(getattr(profile, "machine_id", ""))
        metadata = getattr(machine, "metadata", None)
        return {
            "protocol": protocol,
            "connect": True,
            "disconnect": True,
            "status": True,
            "job_upload": True,
            "job_start": True,
            "job_pause": True,
            "job_resume": True,
            "job_stop": True,
            "emergency_stop": True,
            "axes": dict(getattr(metadata, "work_envelope", {}) or {}),
            "tools": list(getattr(metadata, "supported_tool_systems", []) or []),
            "materials": list(getattr(metadata, "supported_materials", []) or []),
            "file_formats": list(getattr(metadata, "supported_file_formats", []) or []),
            "firmware": getattr(metadata, "firmware", ""),
        }

    def _connection_for(self, connection):
        if isinstance(connection, MachineConnection):
            return connection if connection in self.machine_connections else None
        return next((item for item in self.machine_connections if item.id == connection), None)

    def _communication_session_for(self, session):
        if isinstance(session, CommunicationSession):
            return session if session in self.communication_sessions else None
        return next((item for item in self.communication_sessions if item.id == session), None)

    def _queue_item_for(self, queue_item):
        if isinstance(queue_item, CommunicationJobQueueItem):
            return queue_item if queue_item in self.communication_queue else None
        return next((item for item in self.communication_queue if item.id == queue_item), None)

    def _monitoring_for(self, connection):
        connection_id = getattr(connection, "id", connection)
        return next((item for item in self.machine_monitoring if item.connection_id == connection_id), None)

    def _validate_machine_connection(self, connection):
        connection.validation_errors.clear()
        connection.validation_warnings.clear()
        if connection.protocol not in self.COMMUNICATION_PROTOCOLS:
            connection.validation_errors.append("Machine connection uses an unsupported protocol.")
        if connection.connection_type not in self.CONNECTION_TYPES:
            connection.validation_errors.append("Machine connection uses an unsupported connection type.")
        if not self.product_manager.machine_library_manager.profile_for(connection.machine_profile_id):
            connection.validation_errors.append("Machine connection references a missing machine profile.")
        if connection.connection_type in {"USB", "Serial"} and not connection.parameters.get("port"):
            connection.validation_errors.append("USB/Serial connections require a port.")
        if connection.connection_type in {"TCP/IP", "Network"} and not connection.parameters.get("host"):
            connection.validation_errors.append("TCP/IP connections require a host.")
        if connection.timeout_seconds <= 0.0:
            connection.validation_errors.append("Machine connection timeout must be positive.")

    def _validate_dispatch_job(self, job, connection):
        if self._communication_program_for_job(job) is None:
            raise ValueError("Machine dispatch requires an existing generated program.")
        profile_id = getattr(getattr(job, "metadata", None), "properties", {}).get("machine_profile_id", "")
        if profile_id and profile_id != connection.machine_profile_id:
            raise ValueError("Machine dispatch connection does not match the job machine profile.")
        simulation = next((report for report in self.simulation_reports if report.manufacturing_job_id == job.id), None)
        if simulation is not None and not simulation.valid:
            raise ValueError("Machine dispatch requires a valid simulation report when one exists.")

    def _validate_communication_session(self, session):
        session.validation_errors.clear()
        session.validation_warnings.clear()
        if self._connection_for(session.connection_id) is None:
            session.validation_errors.append("Communication session references a missing connection.")
        if self.job_for(session.manufacturing_job_id) is None:
            session.validation_errors.append("Communication session references a missing manufacturing job.")
        if session.state not in {"Created", "Uploaded", "Running", "Paused", "Stopped", "Completed", "Emergency Stop"}:
            session.validation_errors.append("Communication session has an invalid state.")
        if session.state in {"Uploaded", "Running", "Paused"} and not session.uploaded_program_id:
            session.validation_errors.append("Communication session requires an uploaded program.")

    def _production_subsystem_status(self):
        return {
            "Machine Workspace": self.machine_workspace is not None and getattr(self.machine_workspace.state, "initialized", False),
            "Manufacturing Engine": self.state.initialized,
            "CAM": bool(self.cam_plans or self.toolpaths or self.generated_programs),
            "Additive Manufacturing": bool(self.additive_parameters or self.additive_slices or self.additive_print_files),
            "Sheet Manufacturing": bool(self.sheet_parameters or self.sheet_nest_layouts or self.sheet_cut_paths or self.sheet_programs),
            "Robotics & Motion": bool(self.robot_profiles or self.robot_trajectories or self.robot_programs),
            "Simulation": bool(self.simulation_reports),
            "Machine Communication": bool(self.machine_connections or self.communication_sessions or self.communication_queue),
            "AI Manufacturing Assistant": self._ai_manufacturing_assistant_ready(),
        }

    def _ai_manufacturing_assistant_ready(self):
        data = getattr(self.workspace, "project_settings", {}).get("ai_manufacturing_assistant", {})
        return bool(data.get("initialized", False) or data.get("intents") or data.get("workflow_plans"))

    def _program_ready_job_ids(self):
        job_ids = {program.job_id for program in self.generated_programs if program.valid}
        job_ids.update(print_file.job_id for print_file in self.additive_print_files if print_file.valid)
        job_ids.update(program.job_id for program in self.sheet_programs if program.valid)
        job_ids.update(program.job_id for program in self.robot_programs if program.valid)
        return job_ids

    def _connection_for_job(self, job):
        profile_id = getattr(getattr(job, "metadata", None), "properties", {}).get("machine_profile_id", "")
        return next((connection for connection in self.machine_connections if connection.machine_profile_id == profile_id), None)

    def _production_pipeline_stages(self, validation, simulation, approved, connection):
        stage_names = [
            "Manufacturing Intent",
            "Validation",
            "Planning",
            "Simulation",
            "Approval",
            "Communication",
            "Execution",
            "Monitoring",
            "Completion",
            "Reporting",
        ]
        stages = []
        for index, name in enumerate(stage_names, start=1):
            status = "Ready"
            if name == "Validation" and not validation.get("valid", False):
                status = "Blocked"
            elif name == "Simulation" and simulation is None:
                status = "Blocked"
            elif name == "Approval" and not approved:
                status = "Pending"
            elif name == "Communication" and connection is None:
                status = "Blocked"
            elif name in {"Execution", "Monitoring", "Completion"} and (not approved or not validation.get("valid", False) or connection is None):
                status = "Pending"
            stages.append({
                "order": index,
                "name": name,
                "status": status,
                "existing_api": True,
            })
        return stages

    def _record_production_event(self, event_type, message, severity="Info", job_id="", session_id="", **metadata):
        event = ProductionRuntimeEvent(
            event_type=event_type,
            message=message,
            severity=severity,
            job_id=job_id,
            session_id=session_id,
            timestamp=self._timestamp(),
            metadata=dict(metadata or {}),
        )
        self.production_runtime_events.append(event)
        return event

    def _communication_program_for_job(self, job):
        job_id = getattr(job, "id", job)
        program = next((item for item in self.generated_programs if item.job_id == job_id), None)
        if program is not None:
            return {"id": program.id, "type": "CNC", "name": program.program_name, "content": program.gcode}
        print_file = next((item for item in self.additive_print_files if item.job_id == job_id), None)
        if print_file is not None:
            return {"id": print_file.id, "type": "Additive", "name": print_file.file_name, "content": print_file.content}
        sheet_program = next((item for item in self.sheet_programs if item.job_id == job_id), None)
        if sheet_program is not None:
            return {"id": sheet_program.id, "type": "Sheet", "name": sheet_program.program_name, "content": sheet_program.content}
        robot_program = next((item for item in self.robot_programs if item.job_id == job_id), None)
        if robot_program is not None:
            return {"id": robot_program.id, "type": "Robotics", "name": robot_program.program_name, "content": robot_program.content}
        return None

    def _communication_estimated_time(self, job):
        job_id = getattr(job, "id", job)
        simulation = next((report for report in self.simulation_reports if report.manufacturing_job_id == job_id), None)
        if simulation is not None:
            return simulation.estimated_cycle_time + simulation.estimated_print_time + simulation.estimated_cutting_time
        cnc = next((program for program in self.generated_programs if program.job_id == job_id), None)
        if cnc is not None:
            return float(cnc.statistics.get("estimated_cycle_time", 0.0))
        additive = next((result for result in self.additive_slices if result.job_id == job_id), None)
        if additive is not None:
            return additive.estimated_print_time
        sheet = [path for path in self.sheet_cut_paths if path.job_id == job_id]
        if sheet:
            return sum(path.estimated_time for path in sheet)
        robot = self._robot_trajectory_for_job(job_id)
        if robot is not None:
            return robot.estimated_cycle_time
        return 0.0

    def _protocol_adapter_status(self, connection, command):
        return {
            "protocol": connection.protocol,
            "command": command,
            "supported": command in self.COMMUNICATION_COMMANDS,
            "connection_state": connection.state,
            "timestamp": self._timestamp(),
        }

    def _protocol_payload(self, connection, command, payload):
        return {
            "protocol": connection.protocol,
            "command": command,
            "payload": dict(payload or {}),
            "sent_at": self._timestamp(),
            "emergency_stop_supported": True,
        }

    def _update_monitoring(self, connection, **updates):
        state = self._monitoring_for(connection)
        if state is None:
            state = MachineMonitoringState(connection_id=connection.id)
            self.machine_monitoring.append(state)
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)
        state.status_events.append({"timestamp": self._timestamp(), "state": state.machine_state})
        state.metadata.update({
            "connection_state": connection.state,
            "protocol": connection.protocol,
            "live_monitoring": True,
        })
        return state

    def _log_communication_event(self, connection, event_type, message, severity="Info", manufacturing_job_id="", session_id="", **metadata):
        event = CommunicationEvent(
            connection_id=getattr(connection, "id", connection),
            event_type=event_type,
            message=message,
            severity=severity,
            manufacturing_job_id=manufacturing_job_id,
            session_id=session_id,
            timestamp=self._timestamp(),
            metadata=dict(metadata or {}),
        )
        self.communication_events.append(event)
        return event

    def _remember_machine(self, connection):
        profile = self.product_manager.machine_library_manager.profile_for(connection.machine_profile_id)
        record = {
            "connection_id": connection.id,
            "machine_profile_id": connection.machine_profile_id,
            "profile_name": getattr(profile, "name", ""),
            "protocol": connection.protocol,
            "last_connected": self._timestamp(),
        }
        self.recent_machines = [item for item in self.recent_machines if item.get("connection_id") != connection.id]
        self.recent_machines.insert(0, record)
        self.recent_machines = self.recent_machines[:10]

    def _machine_idle(self, connection):
        state = self._monitoring_for(connection)
        machine_state = getattr(state, "machine_state", connection.state)
        return machine_state in {"Idle", "Stopped", "Disconnected", "Unknown", "Program Uploaded"}

    def _set_queue_status(self, job_id, connection_id, status):
        for item in self.communication_queue:
            if item.manufacturing_job_id == job_id and item.connection_id == connection_id:
                item.status = status

    @staticmethod
    def _validate_duplicate_names(report, label, collection):
        seen = set()
        for item in collection:
            name = getattr(item, "name", "")
            if name in seen:
                report.add_error(f"Duplicate {label} name: {name}")
            seen.add(name)

    def _coordinate_for(self, coordinate_system):
        identifier = getattr(coordinate_system, "id", coordinate_system)
        for item in self.coordinate_systems:
            if item.get("id") == identifier or item.get("name") == identifier:
                return item
        return None

    @staticmethod
    def _has_cycle(operations):
        graph = {
            operation.id: list(operation.metadata.properties.get("dependencies", []))
            for operation in operations
        }
        visiting = set()
        visited = set()

        def visit(node):
            if node in visited:
                return False
            if node in visiting:
                return True
            visiting.add(node)
            for dependency in graph.get(node, []):
                if dependency in graph and visit(dependency):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        return any(visit(node) for node in graph)

    @staticmethod
    def _product_operation_type(operation_type):
        return {
            "Profiling": "Contour",
            "2D Profile": "Contour",
            "Pocketing": "Pocket",
            "2D Pocket": "Pocket",
            "Drilling": "Drill",
            "Peck Drilling": "Peck Drill",
            "Counterbore": "CounterBore",
            "Countersink": "CounterSink",
            "Boring": "Bore",
            "Reaming": "Bore",
            "Rigid Tapping": "Tap",
            "Thread Milling": "Thread Mill",
            "Slot Milling": "Slot",
            "Chamfer": "Chamfer Router",
            "Engraving": "Engrave Router",
            "Setup": "Facing",
            "Inspection": "Facing",
            "Assembly": "Facing",
            "Cleaning": "Facing",
            "Packaging": "Facing",
        }.get(operation_type, operation_type)

    @classmethod
    def _operation_type(cls, operation_type):
        if operation_type not in cls.OPERATION_TYPES:
            raise ValueError(f"Unsupported operation type: {operation_type}")
        return operation_type

    @staticmethod
    def _timestamp():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _name_exists(collection, name):
        return any(getattr(item, "name", None) == name for item in collection)

    @staticmethod
    def _id_exists(collection, identifier):
        return any(getattr(item, "id", None) == identifier for item in collection)

    @staticmethod
    def _vector_from_dict(data):
        data = data or {}
        return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))

    @staticmethod
    def _vector_to_dict(vector):
        return {
            "x": getattr(vector, "x", 0.0),
            "y": getattr(vector, "y", 0.0),
            "z": getattr(vector, "z", 0.0),
        }
