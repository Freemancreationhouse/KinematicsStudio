"""Engineering and environmental simulation foundation.

This module stores simulation data inside the existing Workspace. It does not
create CAD geometry, own meshes, or mutate renderers. Structural analysis
execution is routed through the solver interface and writes results back to the
workspace-owned simulation result database.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from .building import (
    BUILDING_LOAD_DISTRIBUTIONS,
    BUILDING_LOAD_TYPES,
    BUILDING_MEMBER_TYPES,
    BUILDING_SYSTEM_TYPES,
    DESIGN_CODE_NAMES,
    BuildingLoad,
    BuildingStructuralMember,
    BuildingStructuralStudy,
    BuildingStructuralSystem,
    EngineeringDesignCode,
    member_area,
)
from .cfd import (
    CFD_BOUNDARY_TYPES,
    CFD_DOMAIN_TYPES,
    CFD_FLOW_SOURCE_TYPES,
    CFD_STUDY_TYPES,
    CFDBoundaryCondition,
    CFDDomain,
    CFDExecutionRecord,
    CFDFlowSolver,
    CFDFlowSource,
)
from .daylight import (
    DAYLIGHT_STUDY_TYPES,
    OPENING_TYPES,
    SKY_MODEL_TYPES,
    DaylightExecutionRecord,
    DaylightLocation,
    DaylightOpening,
    DaylightStaticSolver,
    DaylightZone,
    SkyModel,
    solar_position,
)
from .energy import (
    ENERGY_ENVELOPE_TYPES,
    ENERGY_SCHEDULE_TYPES,
    ENERGY_STUDY_TYPES,
    HVAC_SYSTEM_TYPES,
    EnergyBalanceSolver,
    EnergyClimateProfile,
    EnergyEnvelopeElement,
    EnergyExecutionRecord,
    EnergySchedule,
    HVACSystem,
)
from .motion import (
    MOTION_DRIVER_TYPES,
    MOTION_JOINT_TYPES,
    MOTION_MECHANISM_TYPES,
    MOTION_STUDY_TYPES,
    MechanismKinematicsSolver,
    MotionAnimationSettings,
    MotionDriver,
    MotionExecutionRecord,
    MotionJoint,
    MotionMechanism,
    MotionRigidBody,
)
from .optimization import (
    DESIGN_VARIABLE_TYPES,
    OPTIMIZATION_CONSTRAINT_TYPES,
    OPTIMIZATION_OBJECTIVE_TYPES,
    OPTIMIZATION_STRATEGIES,
    OPTIMIZATION_STUDY_TYPES,
    OptimizationAIHint,
    OptimizationConstraint,
    OptimizationDesignVariable,
    OptimizationExecutionRecord,
    OptimizationObjective,
    OptimizationSimulationSolver,
)
from .runtime import ProductionSimulationRuntime
from .structural import (
    STRUCTURAL_BOUNDARY_CONDITION_TYPES,
    STRUCTURAL_LOAD_TYPES,
    StructuralExecutionRecord,
    StructuralLinearStaticSolver,
    StructuralMaterialAssignment,
)
from .thermal import (
    HEAT_SOURCE_TYPES,
    THERMAL_ASSEMBLY_TYPES,
    THERMAL_BOUNDARY_TYPES,
    THERMAL_STUDY_TYPES,
    HeatSource,
    ThermalAssembly,
    ThermalExecutionRecord,
    ThermalMaterialProperties,
    ThermalSteadyStateSolver,
)


SIMULATION_WORKSPACE_SETTINGS_KEY = "simulation_workspace"


STUDY_TYPES = {
    "Static Structural",
    "Thermal",
    "Daylight",
    "Energy",
    "CFD",
    "Motion",
    "Optimization",
    "Custom Study",
} | THERMAL_STUDY_TYPES | {"Daylight"}


BOUNDARY_CONDITION_TYPES = {
    "Fixed",
    "Pinned",
    "Roller",
    "Symmetry",
    "Pressure",
    "Force",
    "Gravity",
    "Temperature",
    "Heat Flux",
    "Convection",
    "Radiation",
    "Wind",
    "Solar",
    "Fluid",
} | STRUCTURAL_BOUNDARY_CONDITION_TYPES | THERMAL_BOUNDARY_TYPES


LOAD_CASE_TYPES = {
    "Dead Load",
    "Live Load",
    "Wind Load",
    "Snow Load",
    "Seismic Load",
    "Thermal Load",
    "Solar Gain",
    "Mechanical Load",
    "Dynamic Load",
    "Custom Load Case",
} | STRUCTURAL_LOAD_TYPES | BUILDING_LOAD_TYPES


@dataclass
class SimulationWorkspaceState:
    """Workspace-owned simulation foundation state."""

    initialized: bool = False
    active_project_id: str = ""
    active_study_id: str = ""
    version: str = "1.8"
    status: str = "Pending"
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe workspace state."""

        return {
            "initialized": self.initialized,
            "active_project_id": self.active_project_id,
            "active_study_id": self.active_study_id,
            "version": self.version,
            "status": self.status,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create workspace state from persisted metadata."""

        data = data or {}
        return SimulationWorkspaceState(
            bool(data.get("initialized", False)),
            data.get("active_project_id", ""),
            data.get("active_study_id", ""),
            data.get("version", "1.8"),
            data.get("status", "Pending"),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationProject:
    """Simulation project metadata owned by the existing Workspace."""

    name: str
    description: str = ""
    study_ids: list = field(default_factory=list)
    version: str = "1.8"
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe project data."""

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "study_ids": list(self.study_ids),
            "version": self.version,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a simulation project from persisted metadata."""

        data = data or {}
        return SimulationProject(
            data.get("name", "Simulation Project"),
            data.get("description", ""),
            list(data.get("study_ids", [])),
            data.get("version", "1.8"),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationStudy:
    """Reusable simulation study definition without numerical execution."""

    name: str
    study_type: str
    project_id: str = ""
    description: str = ""
    target_geometry: list = field(default_factory=list)
    material_references: list = field(default_factory=list)
    boundary_condition_ids: list = field(default_factory=list)
    load_case_ids: list = field(default_factory=list)
    mesh_definition_id: str = ""
    solver_id: str = ""
    solver_settings: dict = field(default_factory=dict)
    visualization_settings: dict = field(default_factory=dict)
    status: str = "Defined"
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe study data."""

        return {
            "id": self.id,
            "name": self.name,
            "study_type": self.study_type,
            "project_id": self.project_id,
            "description": self.description,
            "target_geometry": [dict(item) for item in self.target_geometry],
            "material_references": [dict(item) for item in self.material_references],
            "boundary_condition_ids": list(self.boundary_condition_ids),
            "load_case_ids": list(self.load_case_ids),
            "mesh_definition_id": self.mesh_definition_id,
            "solver_id": self.solver_id,
            "solver_settings": dict(self.solver_settings),
            "visualization_settings": dict(self.visualization_settings),
            "status": self.status,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a simulation study from persisted metadata."""

        data = data or {}
        return SimulationStudy(
            data.get("name", "Simulation Study"),
            data.get("study_type", "Custom Study"),
            data.get("project_id", ""),
            data.get("description", ""),
            [dict(item) for item in data.get("target_geometry", [])],
            [dict(item) for item in data.get("material_references", [])],
            list(data.get("boundary_condition_ids", [])),
            list(data.get("load_case_ids", [])),
            data.get("mesh_definition_id", ""),
            data.get("solver_id", ""),
            dict(data.get("solver_settings", {})),
            dict(data.get("visualization_settings", {})),
            data.get("status", "Defined"),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class EngineeringMaterialProperties:
    """Engineering and environmental properties linked to existing materials."""

    material_id: str
    density: float = 0.0
    elastic_modulus: float = 0.0
    poisson_ratio: float = 0.0
    yield_strength: float = 0.0
    ultimate_strength: float = 0.0
    thermal_conductivity: float = 0.0
    specific_heat: float = 0.0
    thermal_expansion: float = 0.0
    solar_absorptance: float = 0.0
    reflectance: float = 0.0
    transmittance: float = 0.0
    emissivity: float = 0.0
    air_permeability: dict = field(default_factory=dict)
    mechanical: dict = field(default_factory=dict)
    environmental: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe material property data."""

        return {
            "id": self.id,
            "material_id": self.material_id,
            "density": self.density,
            "elastic_modulus": self.elastic_modulus,
            "poisson_ratio": self.poisson_ratio,
            "yield_strength": self.yield_strength,
            "ultimate_strength": self.ultimate_strength,
            "thermal_conductivity": self.thermal_conductivity,
            "specific_heat": self.specific_heat,
            "thermal_expansion": self.thermal_expansion,
            "solar_absorptance": self.solar_absorptance,
            "reflectance": self.reflectance,
            "transmittance": self.transmittance,
            "emissivity": self.emissivity,
            "air_permeability": dict(self.air_permeability),
            "mechanical": dict(self.mechanical),
            "environmental": dict(self.environmental),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create material properties from persisted metadata."""

        data = data or {}
        return EngineeringMaterialProperties(
            data.get("material_id", ""),
            float(data.get("density", 0.0)),
            float(data.get("elastic_modulus", 0.0)),
            float(data.get("poisson_ratio", 0.0)),
            float(data.get("yield_strength", 0.0)),
            float(data.get("ultimate_strength", 0.0)),
            float(data.get("thermal_conductivity", 0.0)),
            float(data.get("specific_heat", 0.0)),
            float(data.get("thermal_expansion", 0.0)),
            float(data.get("solar_absorptance", 0.0)),
            float(data.get("reflectance", 0.0)),
            float(data.get("transmittance", 0.0)),
            float(data.get("emissivity", 0.0)),
            dict(data.get("air_permeability", {})),
            dict(data.get("mechanical", {})),
            dict(data.get("environmental", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationBoundaryCondition:
    """Reusable boundary condition metadata."""

    name: str
    condition_type: str
    target_references: list = field(default_factory=list)
    values: dict = field(default_factory=dict)
    coordinate_system: str = ""
    enabled: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe boundary condition data."""

        return {
            "id": self.id,
            "name": self.name,
            "condition_type": self.condition_type,
            "target_references": [dict(item) for item in self.target_references],
            "values": dict(self.values),
            "coordinate_system": self.coordinate_system,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a boundary condition from persisted metadata."""

        data = data or {}
        return SimulationBoundaryCondition(
            data.get("name", "Boundary Condition"),
            data.get("condition_type", "Fixed"),
            [dict(item) for item in data.get("target_references", [])],
            dict(data.get("values", {})),
            data.get("coordinate_system", ""),
            bool(data.get("enabled", True)),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationLoadCase:
    """Reusable simulation load case metadata."""

    name: str
    load_type: str
    target_references: list = field(default_factory=list)
    values: dict = field(default_factory=dict)
    factors: dict = field(default_factory=dict)
    enabled: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe load case data."""

        return {
            "id": self.id,
            "name": self.name,
            "load_type": self.load_type,
            "target_references": [dict(item) for item in self.target_references],
            "values": dict(self.values),
            "factors": dict(self.factors),
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a load case from persisted metadata."""

        data = data or {}
        return SimulationLoadCase(
            data.get("name", "Load Case"),
            data.get("load_type", "Custom Load Case"),
            [dict(item) for item in data.get("target_references", [])],
            dict(data.get("values", {})),
            dict(data.get("factors", {})),
            bool(data.get("enabled", True)),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationLoadCombination:
    """Load combination metadata for future solvers."""

    name: str
    load_case_factors: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe load combination data."""

        return {
            "id": self.id,
            "name": self.name,
            "load_case_factors": dict(self.load_case_factors),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a load combination from persisted metadata."""

        data = data or {}
        return SimulationLoadCombination(
            data.get("name", "Load Combination"),
            dict(data.get("load_case_factors", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationMeshDefinition:
    """Mesh definition metadata; does not create or own solver meshes."""

    name: str
    study_id: str = ""
    element_size: float = 1.0
    element_type: str = "Tetrahedral"
    quality: dict = field(default_factory=dict)
    settings: dict = field(default_factory=dict)
    adaptive_refinement: dict = field(default_factory=dict)
    status: str = "Defined"
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe mesh definition data."""

        return {
            "id": self.id,
            "name": self.name,
            "study_id": self.study_id,
            "element_size": self.element_size,
            "element_type": self.element_type,
            "quality": dict(self.quality),
            "settings": dict(self.settings),
            "adaptive_refinement": dict(self.adaptive_refinement),
            "status": self.status,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a mesh definition from persisted metadata."""

        data = data or {}
        return SimulationMeshDefinition(
            data.get("name", "Simulation Mesh"),
            data.get("study_id", ""),
            float(data.get("element_size", 1.0)),
            data.get("element_type", "Tetrahedral"),
            dict(data.get("quality", {})),
            dict(data.get("settings", {})),
            dict(data.get("adaptive_refinement", {})),
            data.get("status", "Defined"),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationSolverDefinition:
    """Abstract solver interface registration metadata."""

    name: str
    solver_type: str
    compatible_study_types: list = field(default_factory=list)
    version: str = "1.0"
    diagnostics: dict = field(default_factory=dict)
    enabled: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe solver definition data."""

        return {
            "id": self.id,
            "name": self.name,
            "solver_type": self.solver_type,
            "compatible_study_types": list(self.compatible_study_types),
            "version": self.version,
            "diagnostics": dict(self.diagnostics),
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create solver definition metadata from persisted data."""

        data = data or {}
        return SimulationSolverDefinition(
            data.get("name", "Solver Interface"),
            data.get("solver_type", "Abstract"),
            list(data.get("compatible_study_types", [])),
            data.get("version", "1.0"),
            dict(data.get("diagnostics", {})),
            bool(data.get("enabled", True)),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationResult:
    """Reusable result storage metadata for future numerical solvers."""

    study_id: str
    result_type: str
    scalars: dict = field(default_factory=dict)
    vectors: dict = field(default_factory=dict)
    statistics: dict = field(default_factory=dict)
    reports: list = field(default_factory=list)
    history: list = field(default_factory=list)
    visualization_metadata: dict = field(default_factory=dict)
    status: str = "Stored"
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe result data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "result_type": self.result_type,
            "scalars": dict(self.scalars),
            "vectors": dict(self.vectors),
            "statistics": dict(self.statistics),
            "reports": [dict(item) for item in self.reports],
            "history": [dict(item) for item in self.history],
            "visualization_metadata": dict(self.visualization_metadata),
            "status": self.status,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a simulation result from persisted metadata."""

        data = data or {}
        return SimulationResult(
            data.get("study_id", ""),
            data.get("result_type", "Result"),
            dict(data.get("scalars", {})),
            dict(data.get("vectors", {})),
            dict(data.get("statistics", {})),
            [dict(item) for item in data.get("reports", [])],
            [dict(item) for item in data.get("history", [])],
            dict(data.get("visualization_metadata", {})),
            data.get("status", "Stored"),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationVisualization:
    """Visualization metadata consumed by renderers without computation."""

    study_id: str
    result_id: str = ""
    color_legend: dict = field(default_factory=dict)
    result_overlays: list = field(default_factory=list)
    vector_overlays: list = field(default_factory=list)
    section_views: list = field(default_factory=list)
    animation: dict = field(default_factory=dict)
    probes: list = field(default_factory=list)
    measurements: list = field(default_factory=list)
    display_settings: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe visualization metadata."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "result_id": self.result_id,
            "color_legend": dict(self.color_legend),
            "result_overlays": [dict(item) for item in self.result_overlays],
            "vector_overlays": [dict(item) for item in self.vector_overlays],
            "section_views": [dict(item) for item in self.section_views],
            "animation": dict(self.animation),
            "probes": [dict(item) for item in self.probes],
            "measurements": [dict(item) for item in self.measurements],
            "display_settings": dict(self.display_settings),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create visualization metadata from persisted data."""

        data = data or {}
        return SimulationVisualization(
            data.get("study_id", ""),
            data.get("result_id", ""),
            dict(data.get("color_legend", {})),
            [dict(item) for item in data.get("result_overlays", [])],
            [dict(item) for item in data.get("vector_overlays", [])],
            [dict(item) for item in data.get("section_views", [])],
            dict(data.get("animation", {})),
            [dict(item) for item in data.get("probes", [])],
            [dict(item) for item in data.get("measurements", [])],
            dict(data.get("display_settings", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SimulationDiagnostics:
    """Diagnostics summary for the simulation foundation."""

    projects: int = 0
    studies: int = 0
    material_properties: int = 0
    boundary_conditions: int = 0
    load_cases: int = 0
    meshes: int = 0
    solvers: int = 0
    results: int = 0
    visualizations: int = 0
    validation: dict = field(default_factory=dict)
    statistics: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe diagnostics."""

        return {
            "projects": self.projects,
            "studies": self.studies,
            "material_properties": self.material_properties,
            "boundary_conditions": self.boundary_conditions,
            "load_cases": self.load_cases,
            "meshes": self.meshes,
            "solvers": self.solvers,
            "results": self.results,
            "visualizations": self.visualizations,
            "validation": dict(self.validation),
            "statistics": dict(self.statistics),
        }

    @staticmethod
    def from_dict(data):
        """Create diagnostics from persisted metadata."""

        data = data or {}
        return SimulationDiagnostics(
            int(data.get("projects", 0)),
            int(data.get("studies", 0)),
            int(data.get("material_properties", 0)),
            int(data.get("boundary_conditions", 0)),
            int(data.get("load_cases", 0)),
            int(data.get("meshes", 0)),
            int(data.get("solvers", 0)),
            int(data.get("results", 0)),
            int(data.get("visualizations", 0)),
            dict(data.get("validation", {})),
            dict(data.get("statistics", {})),
        )


class EngineeringSimulationManager:
    """Workspace-owned simulation metadata coordinator."""

    def __init__(self, simulation_workspace):

        self.simulation_workspace = simulation_workspace

    def register_study(self, study):
        """Register an existing study definition."""

        if study.study_type not in STUDY_TYPES:
            raise ValueError(f"Unsupported simulation study type: {study.study_type}")
        existing = self.study_for(study.id)
        if existing is None:
            self.simulation_workspace.studies.append(study)
        self.simulation_workspace._link_study(study)
        self.simulation_workspace._save()
        return study

    def study_for(self, study):
        """Return a study by object, id, or name."""

        if isinstance(study, SimulationStudy):
            return study if study in self.simulation_workspace.studies else None
        return next((item for item in self.simulation_workspace.studies if item.id == study or item.name == study), None)

    def validate_study(self, study):
        """Validate a study definition without running a solver."""

        target = self.study_for(study)
        errors = []
        warnings = []
        if target is None:
            errors.append("Simulation study was not found.")
        else:
            if target.study_type not in STUDY_TYPES:
                errors.append("Simulation study type is unsupported.")
            if not target.target_geometry:
                warnings.append("Simulation study has no target geometry references.")
            if not target.material_references:
                warnings.append("Simulation study has no material references.")
            if target.solver_id and self.simulation_workspace.solver_for(target.solver_id) is None:
                errors.append("Simulation study references a missing solver interface.")
            if target.mesh_definition_id and self.simulation_workspace.mesh_for(target.mesh_definition_id) is None:
                errors.append("Simulation study references a missing mesh definition.")
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def schedule_execution(self, study):
        """Record execution scheduling metadata; no numerical solving is performed."""

        target = self.study_for(study)
        validation = self.validate_study(target)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))
        target.status = "Scheduled"
        target.metadata["execution_schedule"] = {
            "scheduled_at": self.simulation_workspace._timestamp(),
            "numerical_solver_executed": False,
            "metadata_only": True,
        }
        self.simulation_workspace._save()
        return target.metadata["execution_schedule"]


class SimulationWorkspace:
    """Simulation subsystem owned by the existing Workspace."""

    def __init__(self, workspace):

        self.workspace = workspace
        self.state = SimulationWorkspaceState()
        self.projects = []
        self.studies = []
        self.material_properties = []
        self.boundary_conditions = []
        self.load_cases = []
        self.load_combinations = []
        self.mesh_definitions = []
        self.solvers = []
        self.results = []
        self.visualizations = []
        self.structural_material_assignments = []
        self.structural_execution_history = []
        self.building_structural_studies = []
        self.building_members = []
        self.building_systems = []
        self.building_loads = []
        self.engineering_design_codes = []
        self.thermal_material_properties = []
        self.heat_sources = []
        self.thermal_assemblies = []
        self.thermal_execution_history = []
        self.daylight_locations = []
        self.sky_models = []
        self.daylight_openings = []
        self.daylight_zones = []
        self.daylight_execution_history = []
        self.energy_climate_profiles = []
        self.energy_envelope_elements = []
        self.energy_schedules = []
        self.hvac_systems = []
        self.energy_execution_history = []
        self.cfd_domains = []
        self.cfd_boundary_conditions = []
        self.cfd_flow_sources = []
        self.cfd_execution_history = []
        self.motion_rigid_bodies = []
        self.motion_joints = []
        self.motion_drivers = []
        self.motion_mechanisms = []
        self.motion_animation_settings = []
        self.motion_execution_history = []
        self.optimization_design_variables = []
        self.optimization_constraints = []
        self.optimization_objectives = []
        self.optimization_ai_hints = []
        self.optimization_execution_history = []
        self.diagnostics_state = SimulationDiagnostics()
        self.manager = EngineeringSimulationManager(self)
        self.structural_solver = StructuralLinearStaticSolver()
        self.thermal_solver = ThermalSteadyStateSolver()
        self.daylight_solver = DaylightStaticSolver()
        self.energy_solver = EnergyBalanceSolver()
        self.cfd_solver = CFDFlowSolver()
        self.motion_solver = MechanismKinematicsSolver()
        self.optimization_solver = OptimizationSimulationSolver()
        self.production_runtime = ProductionSimulationRuntime(self)
        self.load_from_settings()

    def initialize(self):
        """Initialize the simulation workspace metadata."""

        self.state.initialized = True
        self.state.status = "Ready"
        self.state.metadata.update({
            "workspace_owner": "Workspace",
            "metadata_owner": True,
            "structural_solver_interface": True,
            "energy_solver_interface": True,
            "cfd_solver_interface": True,
            "motion_solver_interface": True,
            "optimization_solver_interface": True,
            "production_simulation_runtime": True,
        })
        self.production_runtime.initialize()
        self._save()
        return self

    def create_project(self, name, description="", metadata=None):
        """Create a simulation project inside the existing Workspace."""

        if not name:
            raise ValueError("Simulation project requires a name.")
        project = SimulationProject(name, description, metadata=dict(metadata or {}))
        self.projects.append(project)
        self.state.active_project_id = project.id
        self._save()
        return project

    def create_study(self, project, name, study_type, description="", target_geometry=None, material_references=None, solver_settings=None, visualization_settings=None, metadata=None):
        """Create a reusable study definition."""

        target_project = self.project_for(project)
        if target_project is None:
            raise ValueError("Simulation study requires an existing simulation project.")
        study = SimulationStudy(
            name,
            study_type,
            target_project.id,
            description,
            [dict(item) for item in target_geometry or []],
            [dict(item) for item in material_references or []],
            solver_settings=dict(solver_settings or {}),
            visualization_settings=dict(visualization_settings or {}),
            metadata=dict(metadata or {}),
        )
        self.manager.register_study(study)
        self.state.active_study_id = study.id
        return study

    def create_structural_study(self, project, name, description="", target_geometry=None, solver_settings=None, visualization_settings=None, metadata=None):
        """Create a static structural study using the existing study registry."""

        study = self.create_study(
            project,
            name,
            "Static Structural",
            description,
            target_geometry,
            solver_settings=solver_settings,
            visualization_settings=visualization_settings,
            metadata=dict(metadata or {}),
        )
        solver = self.register_structural_solver()
        self.select_solver(study, solver)
        return study

    def create_building_structural_study(self, project, name, building_name, storeys=None, description="", target_geometry=None, solver_settings=None, visualization_settings=None, metadata=None):
        """Create a storey-aware building structural study using the existing structural study type."""

        study_metadata = dict(metadata or {})
        study_metadata.update({"building_structural": True, "building_name": building_name})
        study = self.create_structural_study(
            project,
            name,
            description,
            target_geometry,
            solver_settings,
            visualization_settings,
            study_metadata,
        )
        building = BuildingStructuralStudy(
            study.id,
            building_name,
            [dict(item) for item in storeys or []],
            metadata=study_metadata,
        )
        self.building_structural_studies.append(building)
        self._save()
        return study

    def register_building_member(self, study, name, member_type, storey="", geometry_references=None, start_node=None, end_node=None, section=None, material=None, system=None, connection_metadata=None, steel_metadata=None, metadata=None):
        """Register a building structural member that references existing CAD geometry."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Building member registration requires an existing study.")
        if member_type not in BUILDING_MEMBER_TYPES:
            raise ValueError(f"Unsupported building structural member type: {member_type}")
        material_id = getattr(material, "id", material or "")
        system_id = getattr(system, "id", system or "")
        member = BuildingStructuralMember(
            target.id,
            name,
            member_type,
            storey,
            [dict(item) for item in geometry_references or []],
            dict(start_node or {}),
            dict(end_node or {}),
            dict(section or {}),
            material_id,
            system_id,
            dict(connection_metadata or {}),
            dict(steel_metadata or {}),
            metadata=dict(metadata or {}),
        )
        self.building_members.append(member)
        if material_id and not any(item.get("material_id") == material_id for item in target.material_references):
            target.material_references.append({"material_id": material_id, "source": "building_structural_member"})
        self._save()
        return member

    def register_steel_member(self, study, name, member_type, section, storey="", geometry_references=None, start_node=None, end_node=None, material=None, connection_metadata=None, steel_metadata=None, metadata=None):
        """Register a steel building member with section and connection metadata."""

        if member_type not in {"Steel Beam", "Steel Column", "Steel Bracing", "Portal Frame", "Roof Frame", "Space Frame", "Steel Truss"}:
            raise ValueError(f"Unsupported steel member type: {member_type}")
        steel_data = dict(steel_metadata or {})
        steel_data["steel_member"] = True
        return self.register_building_member(
            study,
            name,
            member_type,
            storey,
            geometry_references,
            start_node,
            end_node,
            section,
            material,
            connection_metadata=connection_metadata,
            steel_metadata=steel_data,
            metadata=metadata,
        )

    def create_building_structural_system(self, study, name, system_type, member_ids=None, metadata=None):
        """Create building structural system metadata."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Building structural system requires an existing study.")
        if system_type not in BUILDING_SYSTEM_TYPES:
            raise ValueError(f"Unsupported building structural system type: {system_type}")
        system = BuildingStructuralSystem(target.id, name, system_type, list(member_ids or []), dict(metadata or {}))
        self.building_systems.append(system)
        for member in self.building_members:
            if member.id in system.member_ids:
                member.system_id = system.id
        self._save()
        return system

    def create_building_load(self, study, name, load_type, distribution, target_references=None, values=None, storey="", metadata=None):
        """Create a professional building load and matching structural load case."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Building load requires an existing study.")
        if load_type not in BUILDING_LOAD_TYPES:
            raise ValueError(f"Unsupported building load type: {load_type}")
        if distribution not in BUILDING_LOAD_DISTRIBUTIONS:
            raise ValueError(f"Unsupported building load distribution: {distribution}")
        structural_type = self._building_structural_load_type(load_type, distribution)
        load_case = self.create_load_case(
            name,
            structural_type,
            [dict(item) for item in target_references or []],
            dict(values or {}),
            metadata={"building_load_type": load_type, "distribution": distribution, "storey": storey, **dict(metadata or {})},
        )
        if load_case.id not in target.load_case_ids:
            target.load_case_ids.append(load_case.id)
        load = BuildingLoad(
            target.id,
            name,
            load_type,
            distribution,
            [dict(item) for item in target_references or []],
            dict(values or {}),
            storey,
            load_case.id,
            metadata=dict(metadata or {}),
        )
        self.building_loads.append(load)
        self._save()
        return load

    def register_design_code(self, name, load_factors=None, partial_safety_factors=None, material_factors=None, combination_rules=None, metadata=None):
        """Register engineering design-code metadata for building studies."""

        if name not in DESIGN_CODE_NAMES:
            raise ValueError(f"Unsupported engineering design code: {name}")
        existing = next((item for item in self.engineering_design_codes if item.name == name), None)
        if existing is not None:
            return existing
        code = EngineeringDesignCode(
            name,
            dict(load_factors or {}),
            dict(partial_safety_factors or {}),
            dict(material_factors or {}),
            dict(combination_rules or {}),
            metadata=dict(metadata or {}),
        )
        self.engineering_design_codes.append(code)
        self._save()
        return code

    def create_thermal_study(self, project, name, thermal_type="Steady-State Thermal", description="", target_geometry=None, solver_settings=None, visualization_settings=None, metadata=None):
        """Create a thermal study using the existing simulation study registry."""

        if thermal_type not in THERMAL_STUDY_TYPES:
            raise ValueError(f"Unsupported thermal study type: {thermal_type}")
        study_metadata = dict(metadata or {})
        study_metadata.update({"thermal_type": thermal_type})
        study = self.create_study(
            project,
            name,
            "Thermal",
            description,
            target_geometry,
            solver_settings=solver_settings,
            visualization_settings=visualization_settings,
            metadata=study_metadata,
        )
        solver = self.register_thermal_solver()
        self.select_solver(study, solver)
        return study

    def register_thermal_material_properties(self, material, **properties):
        """Attach thermal simulation properties to an existing material."""

        material_id = getattr(material, "id", material)
        if not material_id:
            raise ValueError("Thermal material properties require an existing material reference.")
        item = ThermalMaterialProperties(material_id, **properties)
        self.thermal_material_properties = [existing for existing in self.thermal_material_properties if existing.material_id != material_id]
        self.thermal_material_properties.append(item)
        if not any(existing.material_id == material_id for existing in self.material_properties):
            self.register_material_properties(
                material_id,
                density=item.density,
                thermal_conductivity=item.thermal_conductivity,
                specific_heat=item.specific_heat,
                thermal_expansion=item.thermal_expansion,
                solar_absorptance=item.solar_absorptance,
                reflectance=item.solar_reflectance,
                emissivity=item.emissivity,
                environmental=item.environmental,
            )
        self._save()
        return item

    def assign_thermal_material(self, study, material, target_references=None, properties=None, metadata=None):
        """Assign an existing material to a thermal study by reference."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Thermal material assignment requires an existing study.")
        material_id = getattr(material, "id", material)
        properties_id = getattr(properties, "id", properties or "")
        if not properties_id:
            thermal_properties = next((item for item in self.thermal_material_properties if item.material_id == material_id), None)
            properties_id = getattr(thermal_properties, "id", "")
        reference = {
            "material_id": material_id,
            "thermal_properties_id": properties_id,
            "target_references": [dict(item) for item in target_references or []],
            "metadata": dict(metadata or {}),
        }
        target.material_references.append(reference)
        self._save()
        return reference

    def create_heat_source(self, study, name, source_type, target_references=None, values=None, metadata=None):
        """Create reusable heat source metadata for a thermal study."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Heat source requires an existing thermal study.")
        if source_type not in HEAT_SOURCE_TYPES:
            raise ValueError(f"Unsupported heat source type: {source_type}")
        source = HeatSource(target.id, name, source_type, [dict(item) for item in target_references or []], dict(values or {}), metadata=dict(metadata or {}))
        self.heat_sources.append(source)
        target.metadata.setdefault("heat_source_ids", []).append(source.id)
        self._save()
        return source

    def create_thermal_assembly(self, study, name, assembly_type, layer_references=None, target_references=None, thermal_bridge_metadata=None, room_metadata=None, metadata=None):
        """Create building-oriented thermal assembly metadata."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Thermal assembly requires an existing thermal study.")
        if assembly_type not in THERMAL_ASSEMBLY_TYPES:
            raise ValueError(f"Unsupported thermal assembly type: {assembly_type}")
        assembly = ThermalAssembly(
            target.id,
            name,
            assembly_type,
            [dict(item) for item in layer_references or []],
            [dict(item) for item in target_references or []],
            dict(thermal_bridge_metadata or {}),
            dict(room_metadata or {}),
            metadata=dict(metadata or {}),
        )
        self.thermal_assemblies.append(assembly)
        self._save()
        return assembly

    def generate_thermal_mesh(self, study, nodes, elements, name="Thermal Mesh", element_size=1.0, element_type="Thermal Line", quality=None, settings=None, adaptive_refinement=None, metadata=None):
        """Create thermal mesh data using the existing mesh definition path."""

        if len(nodes or []) < 2:
            raise ValueError("Thermal mesh requires at least two nodes.")
        if not elements:
            raise ValueError("Thermal mesh requires at least one element.")
        mesh_settings = dict(settings or {})
        mesh_settings["nodes"] = [dict(item) for item in nodes]
        mesh_settings["elements"] = [dict(item) for item in elements]
        mesh_quality = dict(quality or {})
        mesh_quality.update({"thermal_region_count": len({item.get("region", "") for item in elements}), "quality_evaluated": True})
        return self.create_mesh_definition(study, name, element_size, element_type, mesh_quality, mesh_settings, adaptive_refinement, metadata)

    def register_thermal_solver(self):
        """Register or return the production thermal solver interface."""

        existing = next((item for item in self.solvers if item.solver_type == self.thermal_solver.solver_type), None)
        if existing is not None:
            return existing
        return self.register_solver(
            "Steady-State Thermal Solver",
            self.thermal_solver.solver_type,
            self.thermal_solver.compatible_study_types,
            version="1.8-thermal",
            diagnostics={"steady_state_heat_transfer": True, "numerical_solver": True},
            metadata={"solver_interface": "SimulationWorkspace", "heat_transfer": "conduction_convection_radiation_framework"},
        )

    def execute_thermal_study(self, study):
        """Execute a thermal study through the existing solver interface."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Thermal execution requires an existing study.")
        solver = self.solver_for(target.solver_id) or self.register_thermal_solver()
        self.select_solver(target, solver)
        execution = ThermalExecutionRecord(target.id, status="Running", started_at=self._timestamp())
        self.thermal_execution_history.append(execution)
        try:
            solved = self.thermal_solver.solve(self, target)
            summary = self._thermal_building_summary(target, solved)
            solved["statistics"].update(summary["statistics"])
            solved["metadata"]["thermal_building"] = summary
            solved["visualization_metadata"].update(summary["visualization"])
            solved["reports"].append(summary["report"])
            result = self.create_result(
                target,
                solved["result_type"],
                solved["scalars"],
                solved["vectors"],
                solved["statistics"],
                solved["reports"],
                solved["history"],
                solved["visualization_metadata"],
                solved["metadata"],
            )
            visualization = self.create_visualization(
                target,
                result,
                color_legend=solved["visualization_metadata"]["color_legends"],
                result_overlays=[
                    {"type": "temperature_contours", "source": "temperature_distribution"},
                    {"type": "gradient_visualization", "source": "thermal_gradients"},
                    {"type": "thermal_overlays", "source": "thermal_boundaries"},
                    {"type": "section_visualization", "source": "thermal_sections"},
                    {"type": "assembly_visualization", "source": "thermal_assemblies"},
                ],
                vector_overlays=[{"type": "heat_flow_vectors", "source": "heat_flux"}],
                animation={"type": "thermal_transient_metadata", "enabled": target.metadata.get("thermal_type") == "Transient Thermal"},
                probes=[{"type": "temperature_probe", "enabled": True}],
                display_settings=target.visualization_settings,
                metadata={"study_id": target.id, "result_id": result.id},
            )
            target.status = "Solved"
            target.metadata["last_thermal_execution"] = solved["diagnostics"]
            execution.result_id = result.id
            execution.report_id = solved["report"]["id"]
            execution.status = "Completed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = solved["diagnostics"]
            self._save()
            return {"result": result, "visualization": visualization, "report": solved["report"], "execution": execution}
        except Exception as exc:
            execution.status = "Failed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = {"error": str(exc)}
            target.status = "Failed"
            self._save()
            raise

    def create_daylight_study(self, project, name, daylight_type="Static Daylight", description="", target_geometry=None, solver_settings=None, visualization_settings=None, metadata=None):
        """Create a daylight study using the existing simulation study registry."""

        if daylight_type not in DAYLIGHT_STUDY_TYPES:
            raise ValueError(f"Unsupported daylight study type: {daylight_type}")
        study_metadata = dict(metadata or {})
        study_metadata.update({"daylight_type": daylight_type})
        study = self.create_study(
            project,
            name,
            "Daylight",
            description,
            target_geometry,
            solver_settings=solver_settings,
            visualization_settings=visualization_settings,
            metadata=study_metadata,
        )
        solver = self.register_daylight_solver()
        self.select_solver(study, solver)
        return study

    def set_daylight_location(self, study, latitude, longitude, elevation=0.0, time_zone=0.0, north_orientation=0.0, site_metadata=None, weather_metadata=None, sky_condition_metadata=None, season_metadata=None, date="", time="", metadata=None):
        """Set geographic and climate metadata for a daylight study."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Daylight location requires an existing study.")
        location = DaylightLocation(
            target.id,
            float(latitude),
            float(longitude),
            float(elevation),
            float(time_zone),
            float(north_orientation),
            dict(site_metadata or {}),
            dict(weather_metadata or {}),
            dict(sky_condition_metadata or {}),
            dict(season_metadata or {}),
            date,
            time,
            metadata=dict(metadata or {}),
        )
        self.daylight_locations = [item for item in self.daylight_locations if item.study_id != target.id]
        self.daylight_locations.append(location)
        target.metadata["solar_position"] = solar_position(location.latitude, location.longitude, location.time_zone, location.date, location.time)
        self._save()
        return location

    def create_sky_model(self, study, name, model_type, luminance=10000.0, diffuse_illuminance=10000.0, direct_normal_illuminance=50000.0, metadata=None):
        """Create sky model metadata for a daylight study."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Sky model requires an existing daylight study.")
        if model_type not in SKY_MODEL_TYPES:
            raise ValueError(f"Unsupported sky model type: {model_type}")
        sky = SkyModel(target.id, name, model_type, float(luminance), float(diffuse_illuminance), float(direct_normal_illuminance), dict(metadata or {}))
        self.sky_models = [item for item in self.sky_models if item.study_id != target.id]
        self.sky_models.append(sky)
        self._save()
        return sky

    def create_daylight_opening(self, study, name, opening_type, target_references=None, area=1.0, transmittance=0.6, orientation=None, room_id="", facade_id="", metadata=None):
        """Register a daylight opening that references existing CAD geometry."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Daylight opening requires an existing daylight study.")
        if opening_type not in OPENING_TYPES:
            raise ValueError(f"Unsupported daylight opening type: {opening_type}")
        opening = DaylightOpening(
            target.id,
            name,
            opening_type,
            [dict(item) for item in target_references or []],
            float(area),
            float(transmittance),
            dict(orientation or {}),
            room_id,
            facade_id,
            metadata=dict(metadata or {}),
        )
        self.daylight_openings.append(opening)
        self._save()
        return opening

    def create_daylight_zone(self, study, name, zone_type="Room", area=1.0, target_references=None, opening_ids=None, metadata=None):
        """Create room, facade, atrium or daylight zone metadata."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Daylight zone requires an existing daylight study.")
        zone = DaylightZone(
            target.id,
            name,
            zone_type,
            float(area),
            [dict(item) for item in target_references or []],
            list(opening_ids or []),
            metadata=dict(metadata or {}),
        )
        self.daylight_zones.append(zone)
        self._save()
        return zone

    def generate_daylight_mesh(self, study, points, name="Daylight Sensor Grid", element_size=1.0, quality=None, settings=None, metadata=None):
        """Create daylight analysis point mesh using the existing mesh definition path."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Daylight mesh requires an existing study.")
        if not points:
            raise ValueError("Daylight mesh requires at least one analysis point.")
        mesh_settings = dict(settings or {})
        mesh_settings["points"] = [dict(item) for item in points]
        mesh_quality = dict(quality or {})
        mesh_quality.update({"point_count": len(points), "quality_evaluated": True})
        return self.create_mesh_definition(target, name, element_size, "Daylight Sensor Grid", mesh_quality, mesh_settings, metadata=metadata)

    def register_daylight_solver(self):
        """Register or return the daylight solver interface."""

        existing = next((item for item in self.solvers if item.solver_type == self.daylight_solver.solver_type), None)
        if existing is not None:
            return existing
        return self.register_solver(
            "Static Daylight Solver",
            self.daylight_solver.solver_type,
            self.daylight_solver.compatible_study_types,
            version="1.8-daylight",
            diagnostics={"static_daylight": True, "solar_model": True, "numerical_solver": True},
            metadata={"solver_interface": "SimulationWorkspace", "daylight": "direct_diffuse_shadow_metrics"},
        )

    def execute_daylight_study(self, study):
        """Execute a daylight study through the existing solver interface."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Daylight execution requires an existing study.")
        solver = self.solver_for(target.solver_id) or self.register_daylight_solver()
        self.select_solver(target, solver)
        execution = DaylightExecutionRecord(target.id, status="Running", started_at=self._timestamp())
        self.daylight_execution_history.append(execution)
        try:
            solved = self.daylight_solver.solve(self, target)
            result = self.create_result(
                target,
                solved["result_type"],
                solved["scalars"],
                solved["vectors"],
                solved["statistics"],
                solved["reports"],
                solved["history"],
                solved["visualization_metadata"],
                solved["metadata"],
            )
            visualization = self.create_visualization(
                target,
                result,
                color_legend=solved["visualization_metadata"]["color_legends"],
                result_overlays=[
                    {"type": "sun_path_visualization", "source": "sun_path"},
                    {"type": "shadow_overlays", "source": "shadow_maps"},
                    {"type": "illuminance_contours", "source": "illuminance_maps"},
                    {"type": "lux_heat_maps", "source": "illuminance_maps"},
                    {"type": "solar_exposure_maps", "source": "solar_exposure"},
                    {"type": "facade_visualization", "source": "facade_statistics"},
                    {"type": "window_performance", "source": "window_performance"},
                ],
                vector_overlays=[{"type": "solar_vectors", "source": "solar_vectors"}],
                animation={"type": "shadow_animation", "enabled": True},
                probes=[{"type": "lux_probe", "enabled": True}],
                display_settings=target.visualization_settings,
                metadata={"study_id": target.id, "result_id": result.id},
            )
            target.status = "Solved"
            target.metadata["last_daylight_execution"] = solved["diagnostics"]
            execution.result_id = result.id
            execution.report_id = solved["report"]["id"]
            execution.status = "Completed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = solved["diagnostics"]
            self._save()
            return {"result": result, "visualization": visualization, "report": solved["report"], "execution": execution}
        except Exception as exc:
            execution.status = "Failed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = {"error": str(exc)}
            target.status = "Failed"
            self._save()
            raise

    def create_energy_study(self, project, name, energy_type="Building Energy Study", description="", target_geometry=None, solver_settings=None, visualization_settings=None, metadata=None):
        """Create an energy study using the existing simulation study registry."""

        if energy_type not in ENERGY_STUDY_TYPES:
            raise ValueError(f"Unsupported energy study type: {energy_type}")
        study_metadata = dict(metadata or {})
        study_metadata.update({"energy_type": energy_type})
        study = self.create_study(
            project,
            name,
            "Energy",
            description,
            target_geometry,
            solver_settings=solver_settings,
            visualization_settings=visualization_settings,
            metadata=study_metadata,
        )
        solver = self.register_energy_solver()
        self.select_solver(study, solver)
        return study

    def set_energy_climate(self, study, weather_metadata=None, temperature_profile=None, humidity_metadata=None, wind_metadata=None, solar_radiation_metadata=None, cloud_cover_metadata=None, rainfall_metadata=None, heating_degree_days=0.0, cooling_degree_days=0.0, climate_zone="", weather_file_metadata=None, metadata=None):
        """Set climate and weather metadata for an energy study."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Energy climate requires an existing study.")
        climate = EnergyClimateProfile(
            target.id,
            dict(weather_metadata or {}),
            [float(item) for item in temperature_profile or []],
            dict(humidity_metadata or {}),
            dict(wind_metadata or {}),
            dict(solar_radiation_metadata or {}),
            dict(cloud_cover_metadata or {}),
            dict(rainfall_metadata or {}),
            float(heating_degree_days),
            float(cooling_degree_days),
            climate_zone,
            dict(weather_file_metadata or {}),
            metadata=dict(metadata or {}),
        )
        self.energy_climate_profiles = [item for item in self.energy_climate_profiles if item.study_id != target.id]
        self.energy_climate_profiles.append(climate)
        self._save()
        return climate

    def create_energy_envelope_element(self, study, name, element_type, area, u_value=0.0, orientation=None, zone_id="", material_references=None, shading_metadata=None, geometry_references=None, metadata=None):
        """Register building envelope metadata that references existing CAD geometry."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Energy envelope element requires an existing study.")
        if element_type not in ENERGY_ENVELOPE_TYPES:
            raise ValueError(f"Unsupported energy envelope type: {element_type}")
        element = EnergyEnvelopeElement(
            target.id,
            name,
            element_type,
            float(area),
            float(u_value),
            dict(orientation or {}),
            zone_id,
            [dict(item) for item in material_references or []],
            dict(shading_metadata or {}),
            [dict(item) for item in geometry_references or []],
            metadata=dict(metadata or {}),
        )
        self.energy_envelope_elements.append(element)
        for reference in element.material_references:
            if reference not in target.material_references:
                target.material_references.append(reference)
        self._save()
        return element

    def create_energy_schedule(self, study, name, schedule_type, values=None, gains=None, metadata=None):
        """Create occupancy, lighting, equipment, HVAC, or ventilation schedule metadata."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Energy schedule requires an existing study.")
        if schedule_type not in ENERGY_SCHEDULE_TYPES:
            raise ValueError(f"Unsupported energy schedule type: {schedule_type}")
        schedule = EnergySchedule(target.id, name, schedule_type, [float(item) for item in values or []], dict(gains or {}), metadata=dict(metadata or {}))
        self.energy_schedules.append(schedule)
        self._save()
        return schedule

    def create_hvac_system(self, study, name, system_type, efficiency=1.0, capacity=0.0, control_metadata=None, metadata=None):
        """Create reusable HVAC system metadata for an energy study."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("HVAC system requires an existing energy study.")
        if system_type not in HVAC_SYSTEM_TYPES:
            raise ValueError(f"Unsupported HVAC system type: {system_type}")
        system = HVACSystem(
            target.id,
            name,
            system_type,
            float(efficiency),
            float(capacity),
            dict(control_metadata or {}),
            metadata=dict(metadata or {}),
        )
        self.hvac_systems.append(system)
        self._save()
        return system

    def register_energy_solver(self):
        """Register or return the energy solver interface."""

        existing = next((item for item in self.solvers if item.solver_type == self.energy_solver.solver_type), None)
        if existing is not None:
            return existing
        return self.register_solver(
            "Whole-Building Energy Solver",
            self.energy_solver.solver_type,
            self.energy_solver.compatible_study_types,
            version="1.8-energy",
            diagnostics={"annual_energy_balance": True, "thermal_reuse": True, "daylight_reuse": True},
            metadata={"solver_interface": "SimulationWorkspace", "energy": "whole_building_balance"},
        )

    def execute_energy_study(self, study):
        """Execute an energy study through the existing solver interface."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Energy execution requires an existing study.")
        solver = self.solver_for(target.solver_id) or self.register_energy_solver()
        self.select_solver(target, solver)
        execution = EnergyExecutionRecord(target.id, status="Running", started_at=self._timestamp())
        self.energy_execution_history.append(execution)
        try:
            solved = self.energy_solver.solve(self, target)
            result = self.create_result(
                target,
                solved["result_type"],
                solved["scalars"],
                solved["vectors"],
                solved["statistics"],
                solved["reports"],
                solved["history"],
                solved["visualization_metadata"],
                solved["metadata"],
            )
            visualization = self.create_visualization(
                target,
                result,
                color_legend=solved["visualization_metadata"]["color_legends"],
                result_overlays=[
                    {"type": "energy_dashboard", "source": "energy_summaries"},
                    {"type": "energy_heat_map", "source": "energy_heat_maps"},
                    {"type": "thermal_zone_visualization", "source": "zone_summaries"},
                    {"type": "monthly_charts", "source": "monthly_profiles"},
                    {"type": "annual_charts", "source": "annual_profiles"},
                    {"type": "load_distribution", "source": "load_summaries"},
                    {"type": "envelope_performance", "source": "envelope_performance"},
                    {"type": "hvac_visualization", "source": "hvac_summaries"},
                    {"type": "carbon_visualization", "source": "carbon_summaries"},
                ],
                vector_overlays=[{"type": "load_distribution_vectors", "source": "load_distribution"}],
                animation={"type": "annual_energy_profile", "enabled": True},
                probes=[{"type": "energy_probe", "enabled": True}],
                display_settings=target.visualization_settings,
                metadata={"study_id": target.id, "result_id": result.id},
            )
            target.status = "Solved"
            target.metadata["last_energy_execution"] = solved["diagnostics"]
            execution.result_id = result.id
            execution.report_id = solved["report"]["id"]
            execution.status = "Completed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = solved["diagnostics"]
            self._save()
            return {"result": result, "visualization": visualization, "report": solved["report"], "execution": execution}
        except Exception as exc:
            execution.status = "Failed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = {"error": str(exc)}
            target.status = "Failed"
            self._save()
            raise

    def create_cfd_study(self, project, name, cfd_type="Steady-State CFD", description="", target_geometry=None, solver_settings=None, visualization_settings=None, metadata=None):
        """Create a CFD study using the existing simulation study registry."""

        if cfd_type not in CFD_STUDY_TYPES:
            raise ValueError(f"Unsupported CFD study type: {cfd_type}")
        study_metadata = dict(metadata or {})
        study_metadata.update({"cfd_type": cfd_type})
        study = self.create_study(
            project,
            name,
            "CFD",
            description,
            target_geometry,
            solver_settings=solver_settings,
            visualization_settings=visualization_settings,
            metadata=study_metadata,
        )
        solver = self.register_cfd_solver()
        self.select_solver(study, solver)
        return study

    def create_cfd_domain(self, study, name, domain_type="Air Domain", extents=None, reference_elevation=0.0, reference_pressure=101325.0, gravity_metadata=None, fluid_properties=None, compressibility_metadata=None, turbulence_metadata=None, region_metadata=None, metadata=None):
        """Create reusable CFD fluid domain metadata."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("CFD domain requires an existing study.")
        if domain_type not in CFD_DOMAIN_TYPES:
            raise ValueError(f"Unsupported CFD domain type: {domain_type}")
        domain = CFDDomain(
            target.id,
            name,
            domain_type,
            dict(extents or {}),
            float(reference_elevation),
            float(reference_pressure),
            dict(gravity_metadata or {}),
            dict(fluid_properties or {}),
            dict(compressibility_metadata or {}),
            dict(turbulence_metadata or {}),
            dict(region_metadata or {}),
            metadata=dict(metadata or {}),
        )
        self.cfd_domains.append(domain)
        self._save()
        return domain

    def create_cfd_boundary_condition(self, study, name, boundary_type, target_references=None, values=None, coordinate_system="", metadata=None):
        """Create CFD boundary condition metadata for an existing study."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("CFD boundary condition requires an existing study.")
        if boundary_type not in CFD_BOUNDARY_TYPES:
            raise ValueError(f"Unsupported CFD boundary type: {boundary_type}")
        boundary = CFDBoundaryCondition(
            target.id,
            name,
            boundary_type,
            [dict(item) for item in target_references or []],
            dict(values or {}),
            coordinate_system,
            metadata=dict(metadata or {}),
        )
        self.cfd_boundary_conditions.append(boundary)
        target.metadata.setdefault("cfd_boundary_condition_ids", []).append(boundary.id)
        self._save()
        return boundary

    def create_cfd_flow_source(self, study, name, source_type, target_references=None, values=None, metadata=None):
        """Create reusable CFD flow source metadata."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("CFD flow source requires an existing study.")
        if source_type not in CFD_FLOW_SOURCE_TYPES:
            raise ValueError(f"Unsupported CFD flow source type: {source_type}")
        source = CFDFlowSource(
            target.id,
            name,
            source_type,
            [dict(item) for item in target_references or []],
            dict(values or {}),
            metadata=dict(metadata or {}),
        )
        self.cfd_flow_sources.append(source)
        target.metadata.setdefault("cfd_flow_source_ids", []).append(source.id)
        self._save()
        return source

    def generate_cfd_mesh(self, study, nodes, cells=None, name="CFD Mesh", element_size=1.0, element_type="Fluid Volume", quality=None, settings=None, adaptive_refinement=None, boundary_layer_metadata=None, near_wall_refinement=None, region_refinement=None, metadata=None):
        """Create CFD mesh metadata through the existing mesh definition path."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("CFD mesh requires an existing study.")
        if not nodes:
            raise ValueError("CFD mesh requires at least one node.")
        mesh_settings = dict(settings or {})
        mesh_settings["nodes"] = [dict(item) for item in nodes]
        mesh_settings["cells"] = [dict(item) for item in cells or []]
        mesh_quality = dict(quality or {})
        mesh_quality.update({
            "node_count": len(nodes),
            "cell_count": len(cells or []),
            "boundary_layer_metadata": dict(boundary_layer_metadata or {}),
            "near_wall_refinement": dict(near_wall_refinement or {}),
            "region_refinement": dict(region_refinement or {}),
            "quality_evaluated": True,
        })
        mesh_metadata = dict(metadata or {})
        mesh_metadata.update({
            "fluid_mesh": True,
            "boundary_layer_metadata": dict(boundary_layer_metadata or {}),
            "near_wall_refinement": dict(near_wall_refinement or {}),
            "region_refinement": dict(region_refinement or {}),
        })
        mesh = self.create_mesh_definition(target, name, element_size, element_type, mesh_quality, mesh_settings, adaptive_refinement, mesh_metadata)
        mesh.status = "Generated"
        self._save()
        return mesh

    def register_cfd_solver(self):
        """Register or return the CFD solver interface."""

        existing = next((item for item in self.solvers if item.solver_type == self.cfd_solver.solver_type), None)
        if existing is not None:
            return existing
        return self.register_solver(
            "Incompressible CFD Airflow Solver",
            self.cfd_solver.solver_type,
            self.cfd_solver.compatible_study_types,
            version="1.8-cfd",
            diagnostics={"incompressible_airflow": True, "thermal_reuse": True, "daylight_reuse": True, "energy_reuse": True},
            metadata={"solver_interface": "SimulationWorkspace", "cfd": "airflow_pressure_ventilation"},
        )

    def execute_cfd_study(self, study):
        """Execute a CFD study through the existing solver interface."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("CFD execution requires an existing study.")
        solver = self.solver_for(target.solver_id) or self.register_cfd_solver()
        self.select_solver(target, solver)
        execution = CFDExecutionRecord(target.id, status="Running", started_at=self._timestamp())
        self.cfd_execution_history.append(execution)
        try:
            solved = self.cfd_solver.solve(self, target)
            result = self.create_result(
                target,
                solved["result_type"],
                solved["scalars"],
                solved["vectors"],
                solved["statistics"],
                solved["reports"],
                solved["history"],
                solved["visualization_metadata"],
                solved["metadata"],
            )
            visualization = self.create_visualization(
                target,
                result,
                color_legend=solved["visualization_metadata"]["color_legends"],
                result_overlays=[
                    {"type": "velocity_field", "source": "velocity_vectors"},
                    {"type": "pressure_field", "source": "pressure_contours"},
                    {"type": "streamline_visualization", "source": "streamlines_metadata"},
                    {"type": "section_planes", "source": "cfd_sections"},
                    {"type": "cut_planes", "source": "cfd_cut_planes"},
                    {"type": "indoor_airflow_overlays", "source": "airflow_summaries"},
                    {"type": "outdoor_wind_overlays", "source": "wind_analysis"},
                ],
                vector_overlays=[{"type": "velocity_vectors", "source": "velocity_vectors"}],
                section_views=[{"type": "cfd_section_plane", "enabled": True}],
                animation={"type": "animated_flow", "enabled": True},
                probes=[{"type": "cfd_probe", "enabled": True}],
                display_settings=target.visualization_settings,
                metadata={"study_id": target.id, "result_id": result.id},
            )
            target.status = "Solved"
            target.metadata["last_cfd_execution"] = solved["diagnostics"]
            execution.result_id = result.id
            execution.report_id = solved["report"]["id"]
            execution.status = "Completed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = solved["diagnostics"]
            self._save()
            return {"result": result, "visualization": visualization, "report": solved["report"], "execution": execution}
        except Exception as exc:
            execution.status = "Failed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = {"error": str(exc)}
            target.status = "Failed"
            self._save()
            raise

    def create_motion_study(self, project, name, motion_type="Mechanism Study", description="", target_geometry=None, solver_settings=None, visualization_settings=None, metadata=None):
        """Create a motion study using the existing simulation study registry."""

        if motion_type not in MOTION_STUDY_TYPES:
            raise ValueError(f"Unsupported motion study type: {motion_type}")
        study_metadata = dict(metadata or {})
        study_metadata.update({"motion_type": motion_type})
        study = self.create_study(
            project,
            name,
            "Motion",
            description,
            target_geometry,
            solver_settings=solver_settings,
            visualization_settings=visualization_settings,
            metadata=study_metadata,
        )
        solver = self.register_motion_solver()
        self.select_solver(study, solver)
        return study

    def create_motion_rigid_body(self, study, name, geometry_references=None, mass=1.0, center_of_gravity=None, inertia_metadata=None, reference_frame=None, local_coordinate_systems=None, is_ground=False, group="", suppressed=False, metadata=None):
        """Register rigid-body metadata that references existing geometry."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Motion rigid body requires an existing study.")
        body = MotionRigidBody(
            target.id,
            name,
            [dict(item) for item in geometry_references or []],
            float(mass),
            dict(center_of_gravity or {}),
            dict(inertia_metadata or {}),
            dict(reference_frame or {}),
            [dict(item) for item in local_coordinate_systems or []],
            bool(is_ground),
            group,
            bool(suppressed),
            metadata=dict(metadata or {}),
        )
        self.motion_rigid_bodies.append(body)
        self._save()
        return body

    def create_motion_joint(self, study, name, joint_type, parent_body=None, child_body=None, axis=None, origin=None, limits=None, constraint_metadata=None, metadata=None):
        """Create joint or constraint metadata for a motion study."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Motion joint requires an existing study.")
        if joint_type not in MOTION_JOINT_TYPES:
            raise ValueError(f"Unsupported motion joint type: {joint_type}")
        joint = MotionJoint(
            target.id,
            name,
            joint_type,
            getattr(parent_body, "id", parent_body or ""),
            getattr(child_body, "id", child_body or ""),
            dict(axis or {}),
            dict(origin or {}),
            dict(limits or {}),
            dict(constraint_metadata or {}),
            metadata=dict(metadata or {}),
        )
        self.motion_joints.append(joint)
        target.metadata.setdefault("motion_joint_ids", []).append(joint.id)
        self._save()
        return joint

    def create_motion_driver(self, study, name, driver_type, target=None, function=None, profile=None, synchronization_group="", metadata=None):
        """Create a time-dependent motion driver."""

        target_study = self.manager.study_for(study)
        if target_study is None:
            raise ValueError("Motion driver requires an existing study.")
        if driver_type not in MOTION_DRIVER_TYPES:
            raise ValueError(f"Unsupported motion driver type: {driver_type}")
        driver = MotionDriver(
            target_study.id,
            name,
            driver_type,
            getattr(target, "id", target or ""),
            dict(function or {}),
            dict(profile or {}),
            synchronization_group,
            metadata=dict(metadata or {}),
        )
        self.motion_drivers.append(driver)
        target_study.metadata.setdefault("motion_driver_ids", []).append(driver.id)
        self._save()
        return driver

    def create_motion_mechanism(self, study, name, mechanism_type, body_ids=None, joint_ids=None, driver_ids=None, metadata=None):
        """Create mechanism-library metadata for a motion study."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Motion mechanism requires an existing study.")
        if mechanism_type not in MOTION_MECHANISM_TYPES:
            raise ValueError(f"Unsupported mechanism type: {mechanism_type}")
        mechanism = MotionMechanism(
            target.id,
            name,
            mechanism_type,
            [getattr(item, "id", item) for item in body_ids or []],
            [getattr(item, "id", item) for item in joint_ids or []],
            [getattr(item, "id", item) for item in driver_ids or []],
            dict(metadata or {}),
        )
        self.motion_mechanisms.append(mechanism)
        self._save()
        return mechanism

    def set_motion_animation(self, study, duration=1.0, time_step=0.1, loop=False, playback_speed=1.0, keyframes=None, camera_tracking_metadata=None, metadata=None):
        """Set animation timeline and playback metadata for a motion study."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Motion animation requires an existing study.")
        animation = MotionAnimationSettings(
            target.id,
            float(duration),
            float(time_step),
            bool(loop),
            float(playback_speed),
            [dict(item) for item in keyframes or []],
            dict(camera_tracking_metadata or {}),
            metadata=dict(metadata or {}),
        )
        self.motion_animation_settings = [item for item in self.motion_animation_settings if item.study_id != target.id]
        self.motion_animation_settings.append(animation)
        self._save()
        return animation

    def register_motion_solver(self):
        """Register or return the motion solver interface."""

        existing = next((item for item in self.solvers if item.solver_type == self.motion_solver.solver_type), None)
        if existing is not None:
            return existing
        return self.register_solver(
            "Rigid Body Mechanism Kinematics Solver",
            self.motion_solver.solver_type,
            self.motion_solver.compatible_study_types,
            version="1.8-motion",
            diagnostics={"forward_kinematics": True, "constraint_solving": True, "joint_propagation": True},
            metadata={"solver_interface": "SimulationWorkspace", "motion": "rigid_body_kinematics"},
        )

    def execute_motion_study(self, study):
        """Execute a motion study through the existing solver interface."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Motion execution requires an existing study.")
        solver = self.solver_for(target.solver_id) or self.register_motion_solver()
        self.select_solver(target, solver)
        execution = MotionExecutionRecord(target.id, status="Running", started_at=self._timestamp())
        self.motion_execution_history.append(execution)
        try:
            solved = self.motion_solver.solve(self, target)
            result = self.create_result(
                target,
                solved["result_type"],
                solved["scalars"],
                solved["vectors"],
                solved["statistics"],
                solved["reports"],
                solved["history"],
                solved["visualization_metadata"],
                solved["metadata"],
            )
            visualization = self.create_visualization(
                target,
                result,
                color_legend=solved["visualization_metadata"]["color_legends"],
                result_overlays=[
                    {"type": "joint_visualization", "source": "joint_states"},
                    {"type": "constraint_visualization", "source": "constraint_status"},
                    {"type": "motion_trails", "source": "motion_trails"},
                    {"type": "body_transforms", "source": "body_transforms"},
                    {"type": "reference_frames", "source": "rigid_bodies"},
                    {"type": "axis_visualization", "source": "motion_joints"},
                    {"type": "timeline_overlays", "source": "timeline_data"},
                    {"type": "mechanism_overlays", "source": "mechanism_summary"},
                ],
                vector_overlays=[{"type": "velocity_metadata", "source": "velocity_metadata"}],
                animation=solved["visualization_metadata"]["timeline"],
                probes=[{"type": "motion_probe", "enabled": True}],
                display_settings=target.visualization_settings,
                metadata={"study_id": target.id, "result_id": result.id},
            )
            target.status = "Solved"
            target.metadata["last_motion_execution"] = solved["diagnostics"]
            execution.result_id = result.id
            execution.report_id = solved["report"]["id"]
            execution.status = "Completed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = solved["diagnostics"]
            self._save()
            return {"result": result, "visualization": visualization, "report": solved["report"], "execution": execution}
        except Exception as exc:
            execution.status = "Failed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = {"error": str(exc)}
            target.status = "Failed"
            self._save()
            raise

    def create_optimization_study(self, project, name, optimization_type="Multi-Objective Optimization", description="", target_geometry=None, solver_settings=None, visualization_settings=None, metadata=None):
        """Create an optimization study using the existing simulation study registry."""

        if optimization_type not in OPTIMIZATION_STUDY_TYPES:
            raise ValueError(f"Unsupported optimization study type: {optimization_type}")
        study_metadata = dict(metadata or {})
        study_metadata.update({"optimization_type": optimization_type, "geometry_editing": "commands_only"})
        study = self.create_study(
            project,
            name,
            "Optimization",
            description,
            target_geometry,
            solver_settings=solver_settings,
            visualization_settings=visualization_settings,
            metadata=study_metadata,
        )
        solver = self.register_optimization_solver()
        self.select_solver(study, solver)
        return study

    def create_optimization_design_variable(self, study, name, variable_type, reference=None, lower_bound=0.0, upper_bound=1.0, default_value=0.0, values=None, group="", dependencies=None, metadata=None):
        """Create bounded design-variable metadata for an optimization study."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Optimization design variable requires an existing study.")
        if variable_type not in DESIGN_VARIABLE_TYPES:
            raise ValueError(f"Unsupported design variable type: {variable_type}")
        variable = OptimizationDesignVariable(
            target.id,
            name,
            variable_type,
            dict(reference or {}),
            float(lower_bound),
            float(upper_bound),
            float(default_value),
            [float(item) for item in values or []],
            group,
            [dict(item) for item in dependencies or []],
            metadata=dict(metadata or {}),
        )
        self.optimization_design_variables.append(variable)
        self._save()
        return variable

    def create_optimization_constraint(self, study, name, constraint_type, metric, operator="<=", target_value=0.0, priority=1.0, hard=True, reference=None, metadata=None):
        """Create hard or soft optimization constraint metadata."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Optimization constraint requires an existing study.")
        if constraint_type not in OPTIMIZATION_CONSTRAINT_TYPES:
            raise ValueError(f"Unsupported optimization constraint type: {constraint_type}")
        constraint = OptimizationConstraint(
            target.id,
            name,
            constraint_type,
            metric,
            operator,
            float(target_value),
            float(priority),
            bool(hard),
            dict(reference or {}),
            metadata=dict(metadata or {}),
        )
        self.optimization_constraints.append(constraint)
        self._save()
        return constraint

    def create_optimization_objective(self, study, name, objective_type, metric, direction="minimize", weight=1.0, target_value=0.0, reference=None, metadata=None):
        """Create weighted optimization objective metadata."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Optimization objective requires an existing study.")
        if objective_type not in OPTIMIZATION_OBJECTIVE_TYPES:
            raise ValueError(f"Unsupported optimization objective type: {objective_type}")
        objective = OptimizationObjective(
            target.id,
            name,
            objective_type,
            metric,
            direction,
            float(weight),
            float(target_value),
            dict(reference or {}),
            metadata=dict(metadata or {}),
        )
        self.optimization_objectives.append(objective)
        self._save()
        return objective

    def create_optimization_ai_hint(self, study, suggestions=None, explanations=None, recommendation_metadata=None, metadata=None):
        """Store AI Studio optimization setup and explanation metadata."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Optimization AI metadata requires an existing study.")
        hint = OptimizationAIHint(
            target.id,
            [dict(item) for item in suggestions or []],
            [dict(item) for item in explanations or []],
            dict(recommendation_metadata or {}),
            metadata=dict(metadata or {}),
        )
        self.optimization_ai_hints.append(hint)
        self._save()
        return hint

    def register_optimization_solver(self):
        """Register or return the optimization solver interface."""

        existing = next((item for item in self.solvers if item.solver_type == self.optimization_solver.solver_type), None)
        if existing is not None:
            return existing
        return self.register_solver(
            "Engineering Optimization Solver",
            self.optimization_solver.solver_type,
            self.optimization_solver.compatible_study_types,
            version="1.8-optimization",
            diagnostics={"parameter_sweeps": True, "ranking": True, "existing_simulation_reuse": True},
            metadata={"solver_interface": "SimulationWorkspace", "optimization": "multi_objective_design_space"},
        )

    def execute_optimization_study(self, study):
        """Execute an optimization study through the existing solver interface."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Optimization execution requires an existing study.")
        solver = self.solver_for(target.solver_id) or self.register_optimization_solver()
        self.select_solver(target, solver)
        execution = OptimizationExecutionRecord(target.id, status="Running", started_at=self._timestamp())
        self.optimization_execution_history.append(execution)
        try:
            solved = self.optimization_solver.solve(self, target)
            result = self.create_result(
                target,
                solved["result_type"],
                solved["scalars"],
                solved["vectors"],
                solved["statistics"],
                solved["reports"],
                solved["history"],
                solved["visualization_metadata"],
                solved["metadata"],
            )
            visualization = self.create_visualization(
                target,
                result,
                color_legend=solved["visualization_metadata"]["color_legends"],
                result_overlays=[
                    {"type": "optimization_dashboard", "source": "optimization_history"},
                    {"type": "convergence_plots", "source": "iteration_history"},
                    {"type": "pareto_visualization", "source": "pareto_front_metadata"},
                    {"type": "variable_trends", "source": "variable_history"},
                    {"type": "sensitivity_charts", "source": "sensitivity_summaries"},
                    {"type": "ranking_visualization", "source": "candidate_ranking"},
                    {"type": "iteration_timeline", "source": "iteration_history"},
                    {"type": "comparison_overlays", "source": "candidate_ranking"},
                ],
                vector_overlays=[{"type": "objective_vectors", "source": "objective_values"}],
                animation={"type": "optimization_iteration_timeline", "enabled": True},
                probes=[{"type": "candidate_probe", "enabled": True}],
                display_settings=target.visualization_settings,
                metadata={"study_id": target.id, "result_id": result.id},
            )
            target.status = "Solved"
            target.metadata["last_optimization_execution"] = solved["diagnostics"]
            execution.result_id = result.id
            execution.report_id = solved["report"]["id"]
            execution.status = "Completed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = solved["diagnostics"]
            self._save()
            return {"result": result, "visualization": visualization, "report": solved["report"], "execution": execution}
        except Exception as exc:
            execution.status = "Failed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = {"error": str(exc)}
            target.status = "Failed"
            self._save()
            raise

    def register_material_properties(self, material, **properties):
        """Attach engineering simulation properties to an existing material."""

        material_id = getattr(material, "id", material)
        if not material_id:
            raise ValueError("Engineering material properties require an existing material reference.")
        item = EngineeringMaterialProperties(material_id, **properties)
        self.material_properties = [existing for existing in self.material_properties if existing.material_id != material_id]
        self.material_properties.append(item)
        self._save()
        return item

    def assign_structural_material(self, study, material, target_type="Body", target_references=None, properties=None, region="", metadata=None):
        """Assign an existing material to bodies, faces, regions, or assemblies."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Structural material assignment requires an existing study.")
        if target.study_type != "Static Structural":
            raise ValueError("Structural material assignment requires a Static Structural study.")
        material_id = getattr(material, "id", material)
        if not material_id:
            raise ValueError("Structural material assignment requires an existing material reference.")
        properties_id = getattr(properties, "id", properties or "")
        if not properties_id:
            material_properties = next((item for item in self.material_properties if item.material_id == material_id), None)
            properties_id = getattr(material_properties, "id", "")
        assignment = StructuralMaterialAssignment(
            target.id,
            material_id,
            target_type,
            [dict(item) for item in target_references or []],
            properties_id,
            region,
            metadata=dict(metadata or {}),
        )
        self.structural_material_assignments.append(assignment)
        reference = {"material_id": material_id, "assignment_id": assignment.id, "properties_id": properties_id, "target_type": target_type}
        if reference not in target.material_references:
            target.material_references.append(reference)
        self._save()
        return assignment

    def create_boundary_condition(self, name, condition_type, target_references=None, values=None, coordinate_system="", metadata=None):
        """Create a reusable boundary condition."""

        if condition_type not in BOUNDARY_CONDITION_TYPES:
            raise ValueError(f"Unsupported boundary condition type: {condition_type}")
        condition = SimulationBoundaryCondition(
            name,
            condition_type,
            [dict(item) for item in target_references or []],
            dict(values or {}),
            coordinate_system,
            metadata=dict(metadata or {}),
        )
        self.boundary_conditions.append(condition)
        self._save()
        return condition

    def create_load_case(self, name, load_type, target_references=None, values=None, factors=None, metadata=None):
        """Create a reusable load case."""

        if load_type not in LOAD_CASE_TYPES:
            raise ValueError(f"Unsupported load case type: {load_type}")
        load = SimulationLoadCase(
            name,
            load_type,
            [dict(item) for item in target_references or []],
            dict(values or {}),
            dict(factors or {}),
            metadata=dict(metadata or {}),
        )
        self.load_cases.append(load)
        self._save()
        return load

    def create_load_combination(self, name, load_case_factors=None, metadata=None):
        """Create a load combination referencing existing load cases."""

        combination = SimulationLoadCombination(name, dict(load_case_factors or {}), metadata=dict(metadata or {}))
        self.load_combinations.append(combination)
        self._save()
        return combination

    def create_mesh_definition(self, study, name="Simulation Mesh", element_size=1.0, element_type="Tetrahedral", quality=None, settings=None, adaptive_refinement=None, metadata=None):
        """Create mesh management metadata without solver mesh generation."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Mesh definition requires an existing study.")
        mesh = SimulationMeshDefinition(
            name,
            target.id,
            float(element_size),
            element_type,
            dict(quality or {}),
            dict(settings or {}),
            dict(adaptive_refinement or {}),
            metadata=dict(metadata or {}),
        )
        self.mesh_definitions.append(mesh)
        target.mesh_definition_id = mesh.id
        self._save()
        return mesh

    def generate_structural_mesh(self, study, nodes, elements, name="Structural Mesh", element_size=1.0, element_type="Structural Line", quality=None, settings=None, adaptive_refinement=None, metadata=None):
        """Create a structural analysis mesh definition from explicit nodes and elements."""

        if len(nodes or []) < 2:
            raise ValueError("Structural mesh generation requires at least two nodes.")
        if not elements:
            raise ValueError("Structural mesh generation requires at least one element.")
        mesh_settings = dict(settings or {})
        mesh_settings["nodes"] = [dict(item) for item in nodes]
        mesh_settings["elements"] = [dict(item) for item in elements]
        mesh_quality = dict(quality or {})
        mesh_quality.update(self._structural_mesh_quality(mesh_settings["nodes"], mesh_settings["elements"]))
        mesh = self.create_mesh_definition(
            study,
            name,
            element_size,
            element_type,
            mesh_quality,
            mesh_settings,
            adaptive_refinement,
            metadata,
        )
        mesh.status = "Generated"
        self._save()
        return mesh

    def register_solver(self, name, solver_type, compatible_study_types=None, version="1.0", diagnostics=None, metadata=None):
        """Register an abstract solver interface without numerical implementation."""

        compatible = list(compatible_study_types or [])
        invalid = [item for item in compatible if item not in STUDY_TYPES]
        if invalid:
            raise ValueError(f"Unsupported solver study compatibility: {invalid[0]}")
        solver = SimulationSolverDefinition(
            name,
            solver_type,
            compatible,
            version,
            dict(diagnostics or {}),
            metadata=dict(metadata or {}),
        )
        self.solvers.append(solver)
        self._save()
        return solver

    def register_structural_solver(self):
        """Register or return the production structural solver interface."""

        existing = next((item for item in self.solvers if item.solver_type == self.structural_solver.solver_type), None)
        if existing is not None:
            return existing
        return self.register_solver(
            "Linear Static Structural Solver",
            self.structural_solver.solver_type,
            self.structural_solver.compatible_study_types,
            version="1.8-structural",
            diagnostics={"linear_static": True, "numerical_solver": True},
            metadata={"solver_interface": "SimulationWorkspace", "geometry_owner": "Workspace/ParametricEngine/GeometryKernel/BodyManager"},
        )

    def select_solver(self, study, solver):
        """Select a compatible abstract solver interface for a study."""

        target_study = self.manager.study_for(study)
        target_solver = self.solver_for(solver)
        if target_study is None or target_solver is None:
            raise ValueError("Solver selection requires an existing study and solver interface.")
        if target_solver.compatible_study_types and target_study.study_type not in target_solver.compatible_study_types:
            raise ValueError("Solver interface is not compatible with the selected study type.")
        target_study.solver_id = target_solver.id
        self._save()
        return target_study

    def create_result(self, study, result_type, scalars=None, vectors=None, statistics=None, reports=None, history=None, visualization_metadata=None, metadata=None):
        """Store simulation result metadata for future solver outputs."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Simulation result requires an existing study.")
        result = SimulationResult(
            target.id,
            result_type,
            dict(scalars or {}),
            dict(vectors or {}),
            dict(statistics or {}),
            [dict(item) for item in reports or []],
            [dict(item) for item in history or []],
            dict(visualization_metadata or {}),
            metadata=dict(metadata or {}),
        )
        self.results.append(result)
        self._save()
        return result

    def create_visualization(self, study, result=None, color_legend=None, result_overlays=None, vector_overlays=None, section_views=None, animation=None, probes=None, measurements=None, display_settings=None, metadata=None):
        """Create visualization metadata consumed by existing render paths later."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Visualization metadata requires an existing study.")
        result_id = getattr(result, "id", result or "")
        visualization = SimulationVisualization(
            target.id,
            result_id,
            dict(color_legend or {}),
            [dict(item) for item in result_overlays or []],
            [dict(item) for item in vector_overlays or []],
            [dict(item) for item in section_views or []],
            dict(animation or {}),
            [dict(item) for item in probes or []],
            [dict(item) for item in measurements or []],
            dict(display_settings or {}),
            metadata=dict(metadata or {}),
        )
        self.visualizations.append(visualization)
        self._save()
        return visualization

    def execute_structural_study(self, study):
        """Execute a linear static structural study through the solver interface."""

        target = self.manager.study_for(study)
        if target is None:
            raise ValueError("Structural execution requires an existing study.")
        solver = self.solver_for(target.solver_id) or self.register_structural_solver()
        self.select_solver(target, solver)
        started_at = self._timestamp()
        execution = StructuralExecutionRecord(target.id, status="Running", started_at=started_at)
        self.structural_execution_history.append(execution)
        try:
            solved = self.structural_solver.solve(self, target)
            result = self.create_result(
                target,
                solved["result_type"],
                solved["scalars"],
                solved["vectors"],
                solved["statistics"],
                solved["reports"],
                solved["history"],
                solved["visualization_metadata"],
                solved["metadata"],
            )
            visualization = self.create_visualization(
                target,
                result,
                color_legend=solved["visualization_metadata"]["color_legends"],
                result_overlays=[
                    {"type": "stress_contour", "source": "von_mises_stress"},
                    {"type": "displacement_contour", "source": "nodal_displacement"},
                    {"type": "strain_contour", "source": "principal_strain"},
                    {"type": "safety_factor_contour", "source": "safety_factor"},
                ],
                vector_overlays=[
                    {"type": "reaction_vectors", "source": "reaction_forces"},
                    {"type": "load_vectors", "source": "load_vectors"},
                    {"type": "constraint_visualization", "source": "boundary_conditions"},
                ],
                animation={"type": "displacement_scale", "enabled": False},
                probes=[{"type": "result_probe", "enabled": True}],
                measurements=[{"type": "max_displacement"}, {"type": "max_stress"}],
                display_settings=target.visualization_settings,
                metadata={"study_id": target.id, "result_id": result.id},
            )
            target.status = "Solved"
            target.metadata["last_structural_execution"] = solved["diagnostics"]
            execution.result_id = result.id
            execution.report_id = solved["report"]["id"]
            execution.status = "Completed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = solved["diagnostics"]
            self._save()
            return {"result": result, "visualization": visualization, "report": solved["report"], "execution": execution}
        except Exception as exc:
            execution.status = "Failed"
            execution.completed_at = self._timestamp()
            execution.diagnostics = {"error": str(exc)}
            target.status = "Failed"
            self._save()
            raise

    def execute_building_structural_study(self, study):
        """Execute a building structural study through the existing structural solver."""

        target = self.manager.study_for(study)
        building = self.building_study_for(target)
        if target is None or building is None:
            raise ValueError("Building structural execution requires an existing building structural study.")
        validation = self.validate_building_structural_study(target)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))
        if not target.mesh_definition_id:
            self._generate_building_analysis_mesh(target)
        solved = self.execute_structural_study(target)
        result = solved["result"]
        summary = self._building_result_summary(target, result)
        result.statistics.update(summary["statistics"])
        result.metadata["building"] = summary
        result.visualization_metadata.update(summary["visualization"])
        result.reports.append(summary["report"])
        solved["visualization"].result_overlays.extend(summary["visualization"]["result_overlays"])
        solved["visualization"].vector_overlays.extend(summary["visualization"]["vector_overlays"])
        solved["visualization"].display_settings.update(summary["visualization"]["display_settings"])
        building.status = "Solved"
        building.diagnostics = {"validation": validation, "summary": summary["statistics"]}
        self._save()
        return solved

    def validate_building_structural_study(self, study):
        """Validate building structural metadata before execution."""

        target = self.manager.study_for(study)
        errors = []
        warnings = []
        if target is None:
            return {"valid": False, "errors": ["Building structural study was not found."], "warnings": []}
        building = self.building_study_for(target)
        if building is None:
            errors.append("Building structural metadata is missing.")
        members = [item for item in self.building_members if item.study_id == target.id]
        if not members:
            errors.append("Building structural study requires recognized structural members.")
        if not [item for item in self.building_systems if item.study_id == target.id]:
            warnings.append("Building structural study has no structural system metadata.")
        if not [item for item in self.building_loads if item.study_id == target.id]:
            errors.append("Building structural study requires building loads.")
        for member in members:
            if not member.geometry_references:
                warnings.append(f"Building member {member.name} has no CAD geometry reference.")
            if not member.start_node or not member.end_node:
                errors.append(f"Building member {member.name} requires start and end analysis nodes.")
            if not member.material_id:
                errors.append(f"Building member {member.name} requires a material assignment.")
            if member.material_id and not any(item.material_id == member.material_id for item in self.material_properties):
                errors.append(f"Building member {member.name} references material without engineering properties.")
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def validate(self):
        """Validate simulation foundation metadata."""

        errors = []
        warnings = []
        for study in self.studies:
            result = self.manager.validate_study(study)
            errors.extend(result["errors"])
            warnings.extend(result["warnings"])
        for mesh in self.mesh_definitions:
            if mesh.element_size <= 0.0:
                errors.append("Mesh element size must be positive.")
            if self.manager.study_for(mesh.study_id) is None:
                errors.append("Mesh definition references a missing study.")
        for result in self.results:
            if self.manager.study_for(result.study_id) is None:
                errors.append("Simulation result references a missing study.")
        for assignment in self.structural_material_assignments:
            if self.manager.study_for(assignment.study_id) is None:
                errors.append("Structural material assignment references a missing study.")
            if not assignment.material_id:
                errors.append("Structural material assignment requires a material reference.")
        for execution in self.structural_execution_history:
            if self.manager.study_for(execution.study_id) is None:
                errors.append("Structural execution history references a missing study.")
        for building in self.building_structural_studies:
            if self.manager.study_for(building.study_id) is None:
                errors.append("Building structural study references a missing study.")
        for member in self.building_members:
            if self.manager.study_for(member.study_id) is None:
                errors.append("Building member references a missing study.")
            if member.member_type not in BUILDING_MEMBER_TYPES:
                errors.append("Building member type is unsupported.")
        for system in self.building_systems:
            if self.manager.study_for(system.study_id) is None:
                errors.append("Building structural system references a missing study.")
        for load in self.building_loads:
            if self.manager.study_for(load.study_id) is None:
                errors.append("Building load references a missing study.")
            if load.load_case_id and not any(item.id == load.load_case_id for item in self.load_cases):
                errors.append("Building load references a missing load case.")
        for source in self.heat_sources:
            if self.manager.study_for(source.study_id) is None:
                errors.append("Heat source references a missing study.")
        for assembly in self.thermal_assemblies:
            if self.manager.study_for(assembly.study_id) is None:
                errors.append("Thermal assembly references a missing study.")
        for execution in self.thermal_execution_history:
            if self.manager.study_for(execution.study_id) is None:
                errors.append("Thermal execution history references a missing study.")
        for location in self.daylight_locations:
            if self.manager.study_for(location.study_id) is None:
                errors.append("Daylight location references a missing study.")
        for sky in self.sky_models:
            if self.manager.study_for(sky.study_id) is None:
                errors.append("Sky model references a missing study.")
        for opening in self.daylight_openings:
            if self.manager.study_for(opening.study_id) is None:
                errors.append("Daylight opening references a missing study.")
        for zone in self.daylight_zones:
            if self.manager.study_for(zone.study_id) is None:
                errors.append("Daylight zone references a missing study.")
        for execution in self.daylight_execution_history:
            if self.manager.study_for(execution.study_id) is None:
                errors.append("Daylight execution history references a missing study.")
        for climate in self.energy_climate_profiles:
            if self.manager.study_for(climate.study_id) is None:
                errors.append("Energy climate profile references a missing study.")
        for element in self.energy_envelope_elements:
            if self.manager.study_for(element.study_id) is None:
                errors.append("Energy envelope element references a missing study.")
            if element.element_type not in ENERGY_ENVELOPE_TYPES:
                errors.append("Energy envelope element type is unsupported.")
            if element.area <= 0.0:
                errors.append("Energy envelope element area must be positive.")
        for schedule in self.energy_schedules:
            if self.manager.study_for(schedule.study_id) is None:
                errors.append("Energy schedule references a missing study.")
            if schedule.schedule_type not in ENERGY_SCHEDULE_TYPES:
                errors.append("Energy schedule type is unsupported.")
        for system in self.hvac_systems:
            if self.manager.study_for(system.study_id) is None:
                errors.append("HVAC system references a missing study.")
            if system.system_type not in HVAC_SYSTEM_TYPES:
                errors.append("HVAC system type is unsupported.")
            if system.efficiency <= 0.0:
                errors.append("HVAC system efficiency must be positive.")
        for execution in self.energy_execution_history:
            if self.manager.study_for(execution.study_id) is None:
                errors.append("Energy execution history references a missing study.")
        for domain in self.cfd_domains:
            if self.manager.study_for(domain.study_id) is None:
                errors.append("CFD domain references a missing study.")
            if domain.domain_type not in CFD_DOMAIN_TYPES:
                errors.append("CFD domain type is unsupported.")
        for boundary in self.cfd_boundary_conditions:
            if self.manager.study_for(boundary.study_id) is None:
                errors.append("CFD boundary condition references a missing study.")
            if boundary.boundary_type not in CFD_BOUNDARY_TYPES:
                errors.append("CFD boundary condition type is unsupported.")
        for source in self.cfd_flow_sources:
            if self.manager.study_for(source.study_id) is None:
                errors.append("CFD flow source references a missing study.")
            if source.source_type not in CFD_FLOW_SOURCE_TYPES:
                errors.append("CFD flow source type is unsupported.")
        for execution in self.cfd_execution_history:
            if self.manager.study_for(execution.study_id) is None:
                errors.append("CFD execution history references a missing study.")
        for body in self.motion_rigid_bodies:
            if self.manager.study_for(body.study_id) is None:
                errors.append("Motion rigid body references a missing study.")
            if body.mass <= 0.0:
                errors.append("Motion rigid body mass must be positive.")
        for joint in self.motion_joints:
            if self.manager.study_for(joint.study_id) is None:
                errors.append("Motion joint references a missing study.")
            if joint.joint_type not in MOTION_JOINT_TYPES:
                errors.append("Motion joint type is unsupported.")
        for driver in self.motion_drivers:
            if self.manager.study_for(driver.study_id) is None:
                errors.append("Motion driver references a missing study.")
            if driver.driver_type not in MOTION_DRIVER_TYPES:
                errors.append("Motion driver type is unsupported.")
        for mechanism in self.motion_mechanisms:
            if self.manager.study_for(mechanism.study_id) is None:
                errors.append("Motion mechanism references a missing study.")
            if mechanism.mechanism_type not in MOTION_MECHANISM_TYPES:
                errors.append("Motion mechanism type is unsupported.")
        for animation in self.motion_animation_settings:
            if self.manager.study_for(animation.study_id) is None:
                errors.append("Motion animation settings reference a missing study.")
            if animation.time_step <= 0.0:
                errors.append("Motion animation time step must be positive.")
        for execution in self.motion_execution_history:
            if self.manager.study_for(execution.study_id) is None:
                errors.append("Motion execution history references a missing study.")
        for variable in self.optimization_design_variables:
            if self.manager.study_for(variable.study_id) is None:
                errors.append("Optimization design variable references a missing study.")
            if variable.variable_type not in DESIGN_VARIABLE_TYPES:
                errors.append("Optimization design variable type is unsupported.")
            if variable.lower_bound > variable.upper_bound:
                errors.append("Optimization design variable bounds are invalid.")
        for constraint in self.optimization_constraints:
            if self.manager.study_for(constraint.study_id) is None:
                errors.append("Optimization constraint references a missing study.")
            if constraint.constraint_type not in OPTIMIZATION_CONSTRAINT_TYPES:
                errors.append("Optimization constraint type is unsupported.")
        for objective in self.optimization_objectives:
            if self.manager.study_for(objective.study_id) is None:
                errors.append("Optimization objective references a missing study.")
            if objective.objective_type not in OPTIMIZATION_OBJECTIVE_TYPES:
                errors.append("Optimization objective type is unsupported.")
        for hint in self.optimization_ai_hints:
            if self.manager.study_for(hint.study_id) is None:
                errors.append("Optimization AI hint references a missing study.")
        for execution in self.optimization_execution_history:
            if self.manager.study_for(execution.study_id) is None:
                errors.append("Optimization execution history references a missing study.")
        for job in self.production_runtime.jobs:
            if self.manager.study_for(job.study_id) is None:
                errors.append("Production simulation runtime job references a missing study.")
            if job.status not in {"Queued", "Running", "Completed", "Failed", "Cancelled", "Paused"}:
                errors.append("Production simulation runtime job status is unsupported.")
        for session in self.production_runtime.sessions:
            if self.manager.study_for(session.study_id) is None:
                errors.append("Production simulation runtime session references a missing study.")
        for certification in self.production_runtime.certifications:
            if self.manager.study_for(certification.study_id) is None:
                errors.append("Production simulation certification references a missing study.")
            if not any(result.id == certification.result_id for result in self.results):
                errors.append("Production simulation certification references a missing result.")
        validation = {"valid": not errors, "errors": errors, "warnings": warnings}
        self.diagnostics_state.validation = validation
        self._save()
        return validation

    def diagnostics(self):
        """Return simulation foundation diagnostics."""

        validation = self.validate()
        diagnostics = SimulationDiagnostics(
            len(self.projects),
            len(self.studies),
            len(self.material_properties),
            len(self.boundary_conditions),
            len(self.load_cases),
            len(self.mesh_definitions),
            len(self.solvers),
            len(self.results),
            len(self.visualizations),
            validation,
            {
                "load_combinations": len(self.load_combinations),
                "study_types": len({study.study_type for study in self.studies}),
                "enabled_solvers": len([solver for solver in self.solvers if solver.enabled]),
                "scheduled_studies": len([study for study in self.studies if study.status == "Scheduled"]),
                "numerical_solvers_executed": len([record for record in self.structural_execution_history if record.status == "Completed"]),
                "structural_material_assignments": len(self.structural_material_assignments),
                "structural_execution_records": len(self.structural_execution_history),
                "structural_solved_studies": len([study for study in self.studies if study.status == "Solved" and study.study_type == "Static Structural"]),
                "building_structural_studies": len(self.building_structural_studies),
                "building_members": len(self.building_members),
                "building_systems": len(self.building_systems),
                "building_loads": len(self.building_loads),
                "engineering_design_codes": len(self.engineering_design_codes),
                "thermal_material_properties": len(self.thermal_material_properties),
                "heat_sources": len(self.heat_sources),
                "thermal_assemblies": len(self.thermal_assemblies),
                "thermal_execution_records": len(self.thermal_execution_history),
                "thermal_solved_studies": len([study for study in self.studies if study.status == "Solved" and study.study_type == "Thermal"]),
                "daylight_locations": len(self.daylight_locations),
                "sky_models": len(self.sky_models),
                "daylight_openings": len(self.daylight_openings),
                "daylight_zones": len(self.daylight_zones),
                "daylight_execution_records": len(self.daylight_execution_history),
                "daylight_solved_studies": len([study for study in self.studies if study.status == "Solved" and study.study_type == "Daylight"]),
                "energy_climate_profiles": len(self.energy_climate_profiles),
                "energy_envelope_elements": len(self.energy_envelope_elements),
                "energy_schedules": len(self.energy_schedules),
                "hvac_systems": len(self.hvac_systems),
                "energy_execution_records": len(self.energy_execution_history),
                "energy_solved_studies": len([study for study in self.studies if study.status == "Solved" and study.study_type == "Energy"]),
                "cfd_domains": len(self.cfd_domains),
                "cfd_boundary_conditions": len(self.cfd_boundary_conditions),
                "cfd_flow_sources": len(self.cfd_flow_sources),
                "cfd_execution_records": len(self.cfd_execution_history),
                "cfd_solved_studies": len([study for study in self.studies if study.status == "Solved" and study.study_type == "CFD"]),
                "motion_rigid_bodies": len(self.motion_rigid_bodies),
                "motion_joints": len(self.motion_joints),
                "motion_drivers": len(self.motion_drivers),
                "motion_mechanisms": len(self.motion_mechanisms),
                "motion_animation_settings": len(self.motion_animation_settings),
                "motion_execution_records": len(self.motion_execution_history),
                "motion_solved_studies": len([study for study in self.studies if study.status == "Solved" and study.study_type == "Motion"]),
                "optimization_design_variables": len(self.optimization_design_variables),
                "optimization_constraints": len(self.optimization_constraints),
                "optimization_objectives": len(self.optimization_objectives),
                "optimization_ai_hints": len(self.optimization_ai_hints),
                "optimization_execution_records": len(self.optimization_execution_history),
                "optimization_solved_studies": len([study for study in self.studies if study.status == "Solved" and study.study_type == "Optimization"]),
                "production_runtime_initialized": self.production_runtime.state.initialized,
                "production_runtime_jobs": len(self.production_runtime.jobs),
                "production_runtime_sessions": len(self.production_runtime.sessions),
                "production_runtime_certifications": len(self.production_runtime.certifications),
                "production_runtime_reports": len(self.production_runtime.production_reports),
                "release_certifications": len(self.production_runtime.release_certifications),
            },
        )
        self.diagnostics_state = diagnostics
        self._save()
        return diagnostics

    def project_for(self, project):
        """Return a simulation project by object, id, or name."""

        if isinstance(project, SimulationProject):
            return project if project in self.projects else None
        return next((item for item in self.projects if item.id == project or item.name == project), None)

    def solver_for(self, solver):
        """Return a solver definition by object, id, or name."""

        if isinstance(solver, SimulationSolverDefinition):
            return solver if solver in self.solvers else None
        return next((item for item in self.solvers if item.id == solver or item.name == solver), None)

    def mesh_for(self, mesh):
        """Return a mesh definition by object, id, or name."""

        if isinstance(mesh, SimulationMeshDefinition):
            return mesh if mesh in self.mesh_definitions else None
        return next((item for item in self.mesh_definitions if item.id == mesh or item.name == mesh), None)

    def motion_animation_for(self, study):
        """Return animation settings by motion study object, id, or name."""

        target = self.manager.study_for(study)
        study_id = getattr(target, "id", study)
        return next((item for item in self.motion_animation_settings if item.study_id == study_id or item.id == study), None)

    def building_study_for(self, study):
        """Return building structural metadata by study object, id, or name."""

        target = self.manager.study_for(study)
        study_id = getattr(target, "id", study)
        return next((item for item in self.building_structural_studies if item.study_id == study_id or item.id == study), None)

    def _generate_building_analysis_mesh(self, study):
        members = [item for item in self.building_members if item.study_id == study.id]
        nodes = []
        node_keys = {}
        elements = []
        for member in members:
            start_id = self._building_node_id(member, "start", member.start_node, nodes, node_keys)
            end_id = self._building_node_id(member, "end", member.end_node, nodes, node_keys)
            elements.append({
                "id": member.id,
                "node_ids": [start_id, end_id],
                "area": member_area(member),
                "material_id": member.material_id,
                "member_type": member.member_type,
                "storey": member.storey,
            })
        return self.generate_structural_mesh(
            study,
            nodes,
            elements,
            name=f"{study.name} Building Structural Mesh",
            element_size=float(study.solver_settings.get("building_member_element_size", 1.0)),
            element_type="Building Structural Line",
            quality={"building_member_count": len(members)},
            metadata={"source": "building_structural_members"},
        )

    def _building_node_id(self, member, endpoint, node, nodes, node_keys):
        x = float(node.get("x", 0.0))
        y = float(node.get("y", 0.0))
        z = float(node.get("z", 0.0))
        key = (round(x, 9), round(y, 9), round(z, 9))
        if key in node_keys:
            return node_keys[key]
        node_id = node.get("id", f"{member.id}-{endpoint}")
        node_keys[key] = node_id
        nodes.append({"id": node_id, "x": x, "y": y, "z": z, "storey": member.storey})
        return node_id

    def _building_result_summary(self, study, result):
        building = self.building_study_for(study)
        members = [item for item in self.building_members if item.study_id == study.id]
        systems = [item for item in self.building_systems if item.study_id == study.id]
        loads = [item for item in self.building_loads if item.study_id == study.id]
        element_results = result.metadata.get("element_results", [])
        node_results = result.metadata.get("node_results", {})
        displacements = node_results.get("displacements", {})
        storey_summary = self._storey_summary(building, displacements)
        member_summary = self._member_summary(members, element_results, displacements)
        critical_members = sorted(
            member_summary,
            key=lambda item: (item.get("utilization", 0.0), item.get("max_displacement", 0.0)),
            reverse=True,
        )[:10]
        statistics = {
            "storey_count": len(building.storeys if building else []),
            "member_count": len(members),
            "system_count": len(systems),
            "building_load_count": len(loads),
            "maximum_drift": max([item["drift"] for item in storey_summary] or [0.0]),
            "critical_member_count": len(critical_members),
            "frame_analysis": True,
            "beam_analysis": any("Beam" in item.member_type for item in members),
            "column_analysis": any("Column" in item.member_type for item in members),
            "slab_analysis": any("Slab" in item.member_type for item in members),
            "plate_analysis": any(item.member_type in {"Slab", "Transfer Slab", "Raft Foundation"} for item in members),
            "shell_analysis": any(item.member_type in {"Wall", "Shear Wall", "Retaining Wall"} for item in members),
            "truss_analysis": any("Truss" in item.member_type or "Bracing" in item.member_type for item in members),
            "building_stability": "Stable" if result.statistics.get("min_safety_factor", 0.0) >= 1.0 else "Review Required",
        }
        visualization = {
            "result_overlays": [
                {"type": "member_highlighting", "source": "building_members"},
                {"type": "storey_visualization", "source": "building_storeys"},
                {"type": "beam_utilization", "source": "member_summary"},
                {"type": "column_utilization", "source": "member_summary"},
                {"type": "building_drift", "source": "storey_summary"},
                {"type": "deflected_shape", "source": "nodal_displacement"},
                {"type": "critical_members", "source": "critical_member_summary"},
                {"type": "foundation_visualization", "source": "foundation_members"},
            ],
            "vector_overlays": [{"type": "building_load_visualization", "source": "building_loads"}],
            "display_settings": {"building_visualization": True, "color_by": "member_utilization"},
        }
        report = {
            "id": str(uuid4()),
            "title": f"{building.building_name if building else study.name} Building Engineering Report",
            "study_id": study.id,
            "building_summary": dict(building.metadata if building else {}),
            "storey_summary": storey_summary,
            "member_summary": member_summary,
            "load_summary": [item.to_dict() for item in loads],
            "material_summary": list(study.material_references),
            "structural_system_summary": [item.to_dict() for item in systems],
            "analysis_summary": statistics,
            "maximum_displacement": result.statistics.get("max_displacement", 0.0),
            "maximum_drift": statistics["maximum_drift"],
            "critical_members": critical_members,
            "warnings": [],
            "recommendations": self._building_recommendations(statistics, critical_members),
            "engineering_metadata": {"design_codes": [item.to_dict() for item in self.engineering_design_codes]},
        }
        return {
            "statistics": {
                "storey_displacement": {item["storey"]: item["max_displacement"] for item in storey_summary},
                "maximum_drift": statistics["maximum_drift"],
                "critical_members": critical_members,
                "member_utilization": {item["member_id"]: item["utilization"] for item in member_summary},
                "building": statistics,
            },
            "visualization": visualization,
            "report": report,
        }

    def _storey_summary(self, building, displacements):
        if building is None:
            return []
        summary = []
        previous = 0.0
        for storey in building.storeys:
            node_ids = set(storey.get("node_ids", []))
            values = [value["magnitude"] for node_id, value in displacements.items() if not node_ids or node_id in node_ids]
            maximum = max(values or [0.0])
            summary.append({
                "storey": storey.get("name", ""),
                "elevation": float(storey.get("elevation", 0.0)),
                "height": float(storey.get("height", 0.0)),
                "max_displacement": maximum,
                "drift": abs(maximum - previous),
            })
            previous = maximum
        return summary

    def _member_summary(self, members, element_results, displacements):
        element_by_id = {item.get("element_id"): item for item in element_results}
        summary = []
        for member in members:
            result = element_by_id.get(member.id, {})
            node_ids = [member.start_node.get("id"), member.end_node.get("id")]
            max_displacement = max([displacements.get(node_id, {}).get("magnitude", 0.0) for node_id in node_ids] or [0.0])
            safety = result.get("safety_factor", float("inf"))
            utilization = 0.0 if safety == float("inf") or safety == 0 else 1.0 / safety
            summary.append({
                "member_id": member.id,
                "name": member.name,
                "member_type": member.member_type,
                "storey": member.storey,
                "max_displacement": max_displacement,
                "normal_stress": result.get("normal_stress", 0.0),
                "von_mises_stress": result.get("von_mises_stress", 0.0),
                "safety_factor": safety,
                "utilization": utilization,
            })
        return summary

    def _building_recommendations(self, statistics, critical_members):
        recommendations = []
        if statistics["maximum_drift"] > 0.0:
            recommendations.append("Review drift-sensitive storeys and lateral-load-resisting systems.")
        if critical_members and critical_members[0].get("utilization", 0.0) > 1.0:
            recommendations.append("Increase capacity or reduce load on critical members exceeding utilization limits.")
        return recommendations

    def _building_structural_load_type(self, load_type, distribution):
        if load_type in {"Dead Load", "Live Load", "Roof Load", "Wall Load", "Equipment Load", "Facade Load", "Snow Load", "Water Tank Load"}:
            return "Point Force" if distribution == "Point" else "Distributed Force"
        if load_type == "Wind Load":
            return "Pressure" if distribution in {"Area", "Storey"} else "Point Force"
        if load_type == "Seismic Load":
            return "Point Force"
        return "Custom Load"

    def _thermal_building_summary(self, study, solved):
        assemblies = [item for item in self.thermal_assemblies if item.study_id == study.id]
        node_temperatures = solved["vectors"].get("temperature_distribution", {})
        assembly_summary = []
        for assembly in assemblies:
            resistances = []
            for layer in assembly.layer_references:
                thickness = float(layer.get("thickness", 0.0))
                material_id = layer.get("material_id", "")
                material = next((item for item in self.thermal_material_properties if item.material_id == material_id), None)
                if material is not None and material.thermal_conductivity > 0.0 and thickness > 0.0:
                    resistances.append(thickness / material.thermal_conductivity)
                elif "thermal_resistance" in layer:
                    resistances.append(float(layer["thermal_resistance"]))
            total_resistance = sum(resistances)
            u_value = 1.0 / total_resistance if total_resistance > 0.0 else 0.0
            target_nodes = [item.get("node_id") for item in assembly.target_references if item.get("node_id")]
            temperatures = [node_temperatures.get(node_id, {}).get("temperature", 0.0) for node_id in target_nodes]
            assembly_summary.append({
                "assembly_id": assembly.id,
                "name": assembly.name,
                "assembly_type": assembly.assembly_type,
                "thermal_resistance": total_resistance,
                "u_value": u_value,
                "surface_temperatures": temperatures,
                "average_surface_temperature": sum(temperatures) / max(len(temperatures), 1),
                "thermal_bridge_metadata": dict(assembly.thermal_bridge_metadata),
                "room_metadata": dict(assembly.room_metadata),
            })
        u_values = [item["u_value"] for item in assembly_summary if item["u_value"] > 0.0]
        report = {
            "id": str(uuid4()),
            "title": f"{study.name} Building Thermal Report",
            "study_id": study.id,
            "assembly_summaries": assembly_summary,
            "room_temperature_analysis": [item["room_metadata"] for item in assembly_summary if item["room_metadata"]],
            "envelope_thermal_analysis": {"assembly_count": len(assembly_summary), "average_u_value": sum(u_values or [0.0]) / max(len(u_values), 1)},
            "u_value_summary": {item["name"]: item["u_value"] for item in assembly_summary},
            "thermal_bridge_summary": [item["thermal_bridge_metadata"] for item in assembly_summary if item["thermal_bridge_metadata"]],
            "warnings": [],
            "recommendations": ["Review assemblies with high U-values for insulation improvements."] if any(value > 1.0 for value in u_values) else [],
        }
        return {
            "statistics": {
                "thermal_assembly_count": len(assembly_summary),
                "assembly_performance": assembly_summary,
                "u_value_summary": report["u_value_summary"],
                "envelope_performance": report["envelope_thermal_analysis"],
                "surface_temperatures": {item["name"]: item["surface_temperatures"] for item in assembly_summary},
            },
            "visualization": {
                "thermal_assemblies": [item["name"] for item in assembly_summary],
                "assembly_visualization": True,
                "section_visualization": True,
                "probe_metadata": True,
                "animation_metadata": study.metadata.get("thermal_type") == "Transient Thermal",
            },
            "report": report,
        }

    def to_dict(self):
        """Return JSON-safe simulation workspace settings."""

        return {
            "state": self.state.to_dict(),
            "projects": [item.to_dict() for item in self.projects],
            "studies": [item.to_dict() for item in self.studies],
            "material_properties": [item.to_dict() for item in self.material_properties],
            "boundary_conditions": [item.to_dict() for item in self.boundary_conditions],
            "load_cases": [item.to_dict() for item in self.load_cases],
            "load_combinations": [item.to_dict() for item in self.load_combinations],
            "mesh_definitions": [item.to_dict() for item in self.mesh_definitions],
            "solvers": [item.to_dict() for item in self.solvers],
            "results": [item.to_dict() for item in self.results],
            "visualizations": [item.to_dict() for item in self.visualizations],
            "structural_material_assignments": [item.to_dict() for item in self.structural_material_assignments],
            "structural_execution_history": [item.to_dict() for item in self.structural_execution_history],
            "building_structural_studies": [item.to_dict() for item in self.building_structural_studies],
            "building_members": [item.to_dict() for item in self.building_members],
            "building_systems": [item.to_dict() for item in self.building_systems],
            "building_loads": [item.to_dict() for item in self.building_loads],
            "engineering_design_codes": [item.to_dict() for item in self.engineering_design_codes],
            "thermal_material_properties": [item.to_dict() for item in self.thermal_material_properties],
            "heat_sources": [item.to_dict() for item in self.heat_sources],
            "thermal_assemblies": [item.to_dict() for item in self.thermal_assemblies],
            "thermal_execution_history": [item.to_dict() for item in self.thermal_execution_history],
            "daylight_locations": [item.to_dict() for item in self.daylight_locations],
            "sky_models": [item.to_dict() for item in self.sky_models],
            "daylight_openings": [item.to_dict() for item in self.daylight_openings],
            "daylight_zones": [item.to_dict() for item in self.daylight_zones],
            "daylight_execution_history": [item.to_dict() for item in self.daylight_execution_history],
            "energy_climate_profiles": [item.to_dict() for item in self.energy_climate_profiles],
            "energy_envelope_elements": [item.to_dict() for item in self.energy_envelope_elements],
            "energy_schedules": [item.to_dict() for item in self.energy_schedules],
            "hvac_systems": [item.to_dict() for item in self.hvac_systems],
            "energy_execution_history": [item.to_dict() for item in self.energy_execution_history],
            "cfd_domains": [item.to_dict() for item in self.cfd_domains],
            "cfd_boundary_conditions": [item.to_dict() for item in self.cfd_boundary_conditions],
            "cfd_flow_sources": [item.to_dict() for item in self.cfd_flow_sources],
            "cfd_execution_history": [item.to_dict() for item in self.cfd_execution_history],
            "motion_rigid_bodies": [item.to_dict() for item in self.motion_rigid_bodies],
            "motion_joints": [item.to_dict() for item in self.motion_joints],
            "motion_drivers": [item.to_dict() for item in self.motion_drivers],
            "motion_mechanisms": [item.to_dict() for item in self.motion_mechanisms],
            "motion_animation_settings": [item.to_dict() for item in self.motion_animation_settings],
            "motion_execution_history": [item.to_dict() for item in self.motion_execution_history],
            "optimization_design_variables": [item.to_dict() for item in self.optimization_design_variables],
            "optimization_constraints": [item.to_dict() for item in self.optimization_constraints],
            "optimization_objectives": [item.to_dict() for item in self.optimization_objectives],
            "optimization_ai_hints": [item.to_dict() for item in self.optimization_ai_hints],
            "optimization_execution_history": [item.to_dict() for item in self.optimization_execution_history],
            "production_runtime": self.production_runtime.to_dict(),
            "diagnostics": self.diagnostics_state.to_dict(),
        }

    def load_from_settings(self):
        """Restore simulation workspace state from existing Workspace settings."""

        data = self.workspace.project_settings.get(SIMULATION_WORKSPACE_SETTINGS_KEY, {})
        self.state = SimulationWorkspaceState.from_dict(data.get("state", {}))
        self.projects = [SimulationProject.from_dict(item) for item in data.get("projects", [])]
        self.studies = [SimulationStudy.from_dict(item) for item in data.get("studies", [])]
        self.material_properties = [EngineeringMaterialProperties.from_dict(item) for item in data.get("material_properties", [])]
        self.boundary_conditions = [SimulationBoundaryCondition.from_dict(item) for item in data.get("boundary_conditions", [])]
        self.load_cases = [SimulationLoadCase.from_dict(item) for item in data.get("load_cases", [])]
        self.load_combinations = [SimulationLoadCombination.from_dict(item) for item in data.get("load_combinations", [])]
        self.mesh_definitions = [SimulationMeshDefinition.from_dict(item) for item in data.get("mesh_definitions", [])]
        self.solvers = [SimulationSolverDefinition.from_dict(item) for item in data.get("solvers", [])]
        self.results = [SimulationResult.from_dict(item) for item in data.get("results", [])]
        self.visualizations = [SimulationVisualization.from_dict(item) for item in data.get("visualizations", [])]
        self.structural_material_assignments = [StructuralMaterialAssignment.from_dict(item) for item in data.get("structural_material_assignments", [])]
        self.structural_execution_history = [StructuralExecutionRecord.from_dict(item) for item in data.get("structural_execution_history", [])]
        self.building_structural_studies = [BuildingStructuralStudy.from_dict(item) for item in data.get("building_structural_studies", [])]
        self.building_members = [BuildingStructuralMember.from_dict(item) for item in data.get("building_members", [])]
        self.building_systems = [BuildingStructuralSystem.from_dict(item) for item in data.get("building_systems", [])]
        self.building_loads = [BuildingLoad.from_dict(item) for item in data.get("building_loads", [])]
        self.engineering_design_codes = [EngineeringDesignCode.from_dict(item) for item in data.get("engineering_design_codes", [])]
        self.thermal_material_properties = [ThermalMaterialProperties.from_dict(item) for item in data.get("thermal_material_properties", [])]
        self.heat_sources = [HeatSource.from_dict(item) for item in data.get("heat_sources", [])]
        self.thermal_assemblies = [ThermalAssembly.from_dict(item) for item in data.get("thermal_assemblies", [])]
        self.thermal_execution_history = [ThermalExecutionRecord.from_dict(item) for item in data.get("thermal_execution_history", [])]
        self.daylight_locations = [DaylightLocation.from_dict(item) for item in data.get("daylight_locations", [])]
        self.sky_models = [SkyModel.from_dict(item) for item in data.get("sky_models", [])]
        self.daylight_openings = [DaylightOpening.from_dict(item) for item in data.get("daylight_openings", [])]
        self.daylight_zones = [DaylightZone.from_dict(item) for item in data.get("daylight_zones", [])]
        self.daylight_execution_history = [DaylightExecutionRecord.from_dict(item) for item in data.get("daylight_execution_history", [])]
        self.energy_climate_profiles = [EnergyClimateProfile.from_dict(item) for item in data.get("energy_climate_profiles", [])]
        self.energy_envelope_elements = [EnergyEnvelopeElement.from_dict(item) for item in data.get("energy_envelope_elements", [])]
        self.energy_schedules = [EnergySchedule.from_dict(item) for item in data.get("energy_schedules", [])]
        self.hvac_systems = [HVACSystem.from_dict(item) for item in data.get("hvac_systems", [])]
        self.energy_execution_history = [EnergyExecutionRecord.from_dict(item) for item in data.get("energy_execution_history", [])]
        self.cfd_domains = [CFDDomain.from_dict(item) for item in data.get("cfd_domains", [])]
        self.cfd_boundary_conditions = [CFDBoundaryCondition.from_dict(item) for item in data.get("cfd_boundary_conditions", [])]
        self.cfd_flow_sources = [CFDFlowSource.from_dict(item) for item in data.get("cfd_flow_sources", [])]
        self.cfd_execution_history = [CFDExecutionRecord.from_dict(item) for item in data.get("cfd_execution_history", [])]
        self.motion_rigid_bodies = [MotionRigidBody.from_dict(item) for item in data.get("motion_rigid_bodies", [])]
        self.motion_joints = [MotionJoint.from_dict(item) for item in data.get("motion_joints", [])]
        self.motion_drivers = [MotionDriver.from_dict(item) for item in data.get("motion_drivers", [])]
        self.motion_mechanisms = [MotionMechanism.from_dict(item) for item in data.get("motion_mechanisms", [])]
        self.motion_animation_settings = [MotionAnimationSettings.from_dict(item) for item in data.get("motion_animation_settings", [])]
        self.motion_execution_history = [MotionExecutionRecord.from_dict(item) for item in data.get("motion_execution_history", [])]
        self.optimization_design_variables = [OptimizationDesignVariable.from_dict(item) for item in data.get("optimization_design_variables", [])]
        self.optimization_constraints = [OptimizationConstraint.from_dict(item) for item in data.get("optimization_constraints", [])]
        self.optimization_objectives = [OptimizationObjective.from_dict(item) for item in data.get("optimization_objectives", [])]
        self.optimization_ai_hints = [OptimizationAIHint.from_dict(item) for item in data.get("optimization_ai_hints", [])]
        self.optimization_execution_history = [OptimizationExecutionRecord.from_dict(item) for item in data.get("optimization_execution_history", [])]
        self.production_runtime.from_dict(data.get("production_runtime", {}))
        self.diagnostics_state = SimulationDiagnostics.from_dict(data.get("diagnostics", {}))
        return self

    def clear(self):
        """Clear simulation foundation metadata from the existing Workspace."""

        self.state = SimulationWorkspaceState()
        self.projects = []
        self.studies = []
        self.material_properties = []
        self.boundary_conditions = []
        self.load_cases = []
        self.load_combinations = []
        self.mesh_definitions = []
        self.solvers = []
        self.results = []
        self.visualizations = []
        self.structural_material_assignments = []
        self.structural_execution_history = []
        self.building_structural_studies = []
        self.building_members = []
        self.building_systems = []
        self.building_loads = []
        self.engineering_design_codes = []
        self.thermal_material_properties = []
        self.heat_sources = []
        self.thermal_assemblies = []
        self.thermal_execution_history = []
        self.daylight_locations = []
        self.sky_models = []
        self.daylight_openings = []
        self.daylight_zones = []
        self.daylight_execution_history = []
        self.energy_climate_profiles = []
        self.energy_envelope_elements = []
        self.energy_schedules = []
        self.hvac_systems = []
        self.energy_execution_history = []
        self.cfd_domains = []
        self.cfd_boundary_conditions = []
        self.cfd_flow_sources = []
        self.cfd_execution_history = []
        self.motion_rigid_bodies = []
        self.motion_joints = []
        self.motion_drivers = []
        self.motion_mechanisms = []
        self.motion_animation_settings = []
        self.motion_execution_history = []
        self.optimization_design_variables = []
        self.optimization_constraints = []
        self.optimization_objectives = []
        self.optimization_ai_hints = []
        self.optimization_execution_history = []
        self.production_runtime.clear()
        self.diagnostics_state = SimulationDiagnostics()
        self.workspace.project_settings.pop(SIMULATION_WORKSPACE_SETTINGS_KEY, None)

    def _link_study(self, study):
        project = self.project_for(study.project_id)
        if project is not None and study.id not in project.study_ids:
            project.study_ids.append(study.id)

    def _structural_mesh_quality(self, nodes, elements):
        node_ids = {item.get("id") for item in nodes}
        invalid_elements = 0
        minimum_length = None
        maximum_length = 0.0
        for element in elements:
            ids = list(element.get("node_ids", []))
            if len(ids) != 2 or ids[0] not in node_ids or ids[1] not in node_ids:
                invalid_elements += 1
                continue
            start = next(item for item in nodes if item.get("id") == ids[0])
            end = next(item for item in nodes if item.get("id") == ids[1])
            dx = float(end.get("x", 0.0)) - float(start.get("x", 0.0))
            dy = float(end.get("y", 0.0)) - float(start.get("y", 0.0))
            dz = float(end.get("z", 0.0)) - float(start.get("z", 0.0))
            length = (dx * dx + dy * dy + dz * dz) ** 0.5
            minimum_length = length if minimum_length is None else min(minimum_length, length)
            maximum_length = max(maximum_length, length)
        return {
            "node_count": len(nodes),
            "element_count": len(elements),
            "invalid_elements": invalid_elements,
            "minimum_element_length": minimum_length or 0.0,
            "maximum_element_length": maximum_length,
            "quality_evaluated": True,
        }

    def _save(self):
        self.workspace.project_settings[SIMULATION_WORKSPACE_SETTINGS_KEY] = self.to_dict()

    @staticmethod
    def _timestamp():
        return datetime.now(timezone.utc).isoformat()
