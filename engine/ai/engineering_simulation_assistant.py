"""AI Engineering Simulation Assistant integrated with existing AI Studio."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from engine.commands.structural_simulation_command import (
    RunBuildingStructuralStudyCommand,
    RunCFDStudyCommand,
    RunDaylightStudyCommand,
    RunEnergyStudyCommand,
    RunMotionStudyCommand,
    RunOptimizationStudyCommand,
    RunStructuralStudyCommand,
    RunThermalStudyCommand,
)


AI_ENGINEERING_SIMULATION_ASSISTANT_SETTINGS_KEY = "ai_engineering_simulation_assistant"


STUDY_RECOMMENDATION_MAP = {
    "Static Structural": ("Structural", ("stress", "displacement", "support", "load", "strength", "safety")),
    "Building Structural": ("Building Structural", ("building", "storey", "beam", "column", "drift", "seismic", "wind load")),
    "Thermal": ("Thermal", ("thermal", "temperature", "heat", "u-value", "conduction", "convection")),
    "Daylight": ("Daylight", ("daylight", "sun", "lux", "glare", "shadow", "opening")),
    "Energy": ("Energy", ("energy", "hvac", "eui", "carbon", "cooling", "heating")),
    "CFD": ("CFD", ("airflow", "ventilation", "wind", "pressure", "cfd", "diffuser")),
    "Motion": ("Motion", ("motion", "mechanism", "hinge", "joint", "driver", "kinematic")),
    "Optimization": ("Optimization", ("optimize", "compare", "alternative", "sensitivity", "pareto", "ranking")),
}


COMMAND_BY_STUDY_TYPE = {
    "Static Structural": RunStructuralStudyCommand,
    "Building Structural": RunBuildingStructuralStudyCommand,
    "Thermal": RunThermalStudyCommand,
    "Daylight": RunDaylightStudyCommand,
    "Energy": RunEnergyStudyCommand,
    "CFD": RunCFDStudyCommand,
    "Motion": RunMotionStudyCommand,
    "Optimization": RunOptimizationStudyCommand,
}


@dataclass
class EngineeringSimulationConversation:
    """Workspace-associated engineering simulation conversation context."""

    workspace_name: str
    preferences: dict = field(default_factory=dict)
    current_study_id: str = ""
    previous_study_ids: list = field(default_factory=list)
    current_objectives: list = field(default_factory=list)
    recommendation_history: list = field(default_factory=list)
    comparison_history: list = field(default_factory=list)
    engineering_context: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self):
        """Return JSON-safe conversation metadata."""

        return {
            "id": self.id,
            "workspace_name": self.workspace_name,
            "preferences": dict(self.preferences),
            "current_study_id": self.current_study_id,
            "previous_study_ids": list(self.previous_study_ids),
            "current_objectives": list(self.current_objectives),
            "recommendation_history": list(self.recommendation_history),
            "comparison_history": list(self.comparison_history),
            "engineering_context": dict(self.engineering_context),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        """Restore conversation metadata."""

        return cls(
            data.get("workspace_name", ""),
            dict(data.get("preferences", {})),
            data.get("current_study_id", ""),
            list(data.get("previous_study_ids", [])),
            list(data.get("current_objectives", [])),
            list(data.get("recommendation_history", [])),
            list(data.get("comparison_history", [])),
            dict(data.get("engineering_context", {})),
            data.get("id", str(uuid4())),
            data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class SimulationStudyRecommendation:
    """AI recommendation for one existing simulation study type."""

    study_type: str
    discipline: str
    reason: str
    confidence: float
    prerequisites: list = field(default_factory=list)
    sequencing: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe recommendation metadata."""

        return {
            "id": self.id,
            "study_type": self.study_type,
            "discipline": self.discipline,
            "reason": self.reason,
            "confidence": self.confidence,
            "prerequisites": list(self.prerequisites),
            "sequencing": list(self.sequencing),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data):
        """Restore recommendation metadata."""

        return cls(
            data.get("study_type", ""),
            data.get("discipline", ""),
            data.get("reason", ""),
            float(data.get("confidence", 0.0)),
            list(data.get("prerequisites", [])),
            list(data.get("sequencing", [])),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class SimulationConfigurationGuidance:
    """AI guidance for configuring an existing simulation study."""

    study_id: str
    study_type: str
    boundary_conditions: list = field(default_factory=list)
    loads: list = field(default_factory=list)
    materials: list = field(default_factory=list)
    solver_settings: list = field(default_factory=list)
    validation_messages: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe configuration guidance."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "study_type": self.study_type,
            "boundary_conditions": list(self.boundary_conditions),
            "loads": list(self.loads),
            "materials": list(self.materials),
            "solver_settings": list(self.solver_settings),
            "validation_messages": list(self.validation_messages),
        }

    @classmethod
    def from_dict(cls, data):
        """Restore configuration guidance."""

        return cls(
            data.get("study_id", ""),
            data.get("study_type", ""),
            list(data.get("boundary_conditions", [])),
            list(data.get("loads", [])),
            list(data.get("materials", [])),
            list(data.get("solver_settings", [])),
            list(data.get("validation_messages", [])),
            data.get("id", str(uuid4())),
        )


@dataclass
class EngineeringReviewFinding:
    """AI review finding for simulation completeness and risk."""

    category: str
    message: str
    severity: str = "Low"
    recommendation: str = ""
    study_id: str = ""
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe review finding."""

        return {
            "id": self.id,
            "category": self.category,
            "message": self.message,
            "severity": self.severity,
            "recommendation": self.recommendation,
            "study_id": self.study_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data):
        """Restore review finding."""

        return cls(
            data.get("category", ""),
            data.get("message", ""),
            data.get("severity", "Low"),
            data.get("recommendation", ""),
            data.get("study_id", ""),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class SimulationResultInterpretation:
    """AI interpretation of existing simulation results."""

    result_id: str
    study_type: str
    summary: str
    key_metrics: dict = field(default_factory=dict)
    recommendations: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe interpretation metadata."""

        return {
            "id": self.id,
            "result_id": self.result_id,
            "study_type": self.study_type,
            "summary": self.summary,
            "key_metrics": dict(self.key_metrics),
            "recommendations": list(self.recommendations),
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data):
        """Restore result interpretation."""

        return cls(
            data.get("result_id", ""),
            data.get("study_type", ""),
            data.get("summary", ""),
            dict(data.get("key_metrics", {})),
            list(data.get("recommendations", [])),
            list(data.get("warnings", [])),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class EngineeringKnowledgeItem:
    """Reusable engineering simulation knowledge metadata."""

    topic: str
    discipline: str
    guidance: str
    references: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe knowledge metadata."""

        return {
            "id": self.id,
            "topic": self.topic,
            "discipline": self.discipline,
            "guidance": self.guidance,
            "references": list(self.references),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data):
        """Restore knowledge metadata."""

        return cls(
            data.get("topic", ""),
            data.get("discipline", ""),
            data.get("guidance", ""),
            list(data.get("references", [])),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class SimulationReportAssistance:
    """AI-assisted engineering report summary metadata."""

    title: str
    executive_summary: str
    recommendations: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    comparisons: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe report assistance metadata."""

        return {
            "id": self.id,
            "title": self.title,
            "executive_summary": self.executive_summary,
            "recommendations": list(self.recommendations),
            "warnings": list(self.warnings),
            "comparisons": list(self.comparisons),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data):
        """Restore report assistance metadata."""

        return cls(
            data.get("title", ""),
            data.get("executive_summary", ""),
            list(data.get("recommendations", [])),
            list(data.get("warnings", [])),
            list(data.get("comparisons", [])),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class MultiSimulationInsight:
    """AI insight across multiple engineering simulation studies."""

    involved_study_types: list
    summary: str
    cross_study_recommendations: list = field(default_factory=list)
    conflicts: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe multi-study insight."""

        return {
            "id": self.id,
            "involved_study_types": list(self.involved_study_types),
            "summary": self.summary,
            "cross_study_recommendations": list(self.cross_study_recommendations),
            "conflicts": list(self.conflicts),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data):
        """Restore multi-study insight."""

        return cls(
            list(data.get("involved_study_types", [])),
            data.get("summary", ""),
            list(data.get("cross_study_recommendations", [])),
            list(data.get("conflicts", [])),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class EngineeringSimulationAssistantResponse:
    """Complete AI Engineering Simulation Assistant response."""

    recommendations: list
    configuration_guidance: list
    review_findings: list
    interpretations: list
    knowledge_items: list
    report: SimulationReportAssistance
    multi_simulation_insight: MultiSimulationInsight
    diagnostics: dict

    def to_dict(self):
        """Return JSON-safe assistant response."""

        return {
            "recommendations": [item.to_dict() for item in self.recommendations],
            "configuration_guidance": [item.to_dict() for item in self.configuration_guidance],
            "review_findings": [item.to_dict() for item in self.review_findings],
            "interpretations": [item.to_dict() for item in self.interpretations],
            "knowledge_items": [item.to_dict() for item in self.knowledge_items],
            "report": self.report.to_dict(),
            "multi_simulation_insight": self.multi_simulation_insight.to_dict(),
            "diagnostics": dict(self.diagnostics),
        }


class AIEngineeringSimulationAssistant:
    """AI Studio module for engineering simulation orchestration only."""

    def __init__(self, ai_engine):
        self.ai_engine = ai_engine
        self.initialized = False
        self.conversations = []
        self.recommendations = []
        self.configuration_guidance = []
        self.review_findings = []
        self.interpretations = []
        self.knowledge_items = self._default_knowledge()
        self.report_assistance = []
        self.multi_simulation_insights = []
        self.execution_records = []
        self.statistics = {
            "planning_requests": 0,
            "recommendation_requests": 0,
            "configuration_requests": 0,
            "review_requests": 0,
            "interpretation_requests": 0,
            "report_requests": 0,
            "multi_study_requests": 0,
            "conversation_context_updates": 0,
            "command_routed_executions": 0,
            "validation_failures": 0,
        }

    def initialize(self, workspace):
        """Initialize against the existing Workspace settings path."""

        self.initialized = True
        self.load_from_settings(workspace)
        self._save(workspace)
        return self

    def start_session(self, workspace, preferences=None):
        """Start engineering simulation conversation context for a Workspace."""

        self.initialize(workspace)
        conversation = EngineeringSimulationConversation(
            getattr(workspace, "name", "Workspace"),
            dict(preferences or {}),
            engineering_context=self._workspace_context(workspace),
        )
        self.conversations.append(conversation)
        self.statistics["conversation_context_updates"] += 1
        self._save(workspace)
        return conversation

    def recommend_studies(self, prompt, workspace, session=None):
        """Recommend existing simulation study types from engineering intent."""

        self.initialize(workspace)
        lower = prompt.lower()
        selected = []
        for study_type, (discipline, keywords) in STUDY_RECOMMENDATION_MAP.items():
            if any(keyword in lower for keyword in keywords):
                selected.append((study_type, discipline, 0.94))
        if not selected or "complete" in lower or "multi" in lower or "package" in lower:
            selected = [
                ("Static Structural", "Structural", 0.91),
                ("Thermal", "Thermal", 0.88),
                ("Daylight", "Environmental", 0.86),
                ("Energy", "Environmental", 0.9),
                ("CFD", "Fluid", 0.87),
                ("Optimization", "Optimization", 0.89),
            ]
        recommendations = [
            SimulationStudyRecommendation(
                study_type,
                discipline,
                self._recommendation_reason(study_type, prompt),
                confidence,
                prerequisites=self._prerequisites(study_type),
                sequencing=self._sequencing(study_type),
                metadata={"source": "AI Engineering Simulation Assistant", "existing_system": "Simulation Workspace"},
            )
            for study_type, discipline, confidence in selected
        ]
        self.recommendations.extend(recommendations)
        self.statistics["recommendation_requests"] += 1
        self._update_session(session, recommendations=recommendations)
        self._save(workspace)
        return recommendations

    def configure_simulation(self, prompt, workspace, session=None, study=None):
        """Provide setup guidance for existing simulation studies."""

        self.initialize(workspace)
        simulation = workspace.simulation_workspace.initialize()
        studies = self._target_studies(simulation, study)
        if not studies:
            studies = list(simulation.studies)
        guidance = [self._guidance_for_study(item) for item in studies]
        self.configuration_guidance.extend(guidance)
        self.statistics["configuration_requests"] += 1
        self._update_session(session, current_study=studies[-1] if studies else None)
        self._save(workspace)
        return guidance

    def review_setup(self, workspace, session=None, study=None):
        """Review simulation completeness without modifying project data."""

        self.initialize(workspace)
        simulation = workspace.simulation_workspace.initialize()
        studies = self._target_studies(simulation, study) or list(simulation.studies)
        findings = []
        validation = simulation.validate()
        for message in validation.get("errors", []):
            findings.append(EngineeringReviewFinding("Validation", message, "High", "Resolve the invalid setup before execution."))
        for message in validation.get("warnings", []):
            findings.append(EngineeringReviewFinding("Validation", message, "Medium", "Review the warning before relying on results."))
        for item in studies:
            findings.extend(self._study_findings(simulation, item))
        if not findings:
            findings.append(EngineeringReviewFinding("Completeness", "Simulation setup is ready for engineering review.", "Low", "Proceed with command-routed execution when approved."))
        self.review_findings.extend(findings)
        self.statistics["review_requests"] += 1
        self._update_session(session, current_study=studies[-1] if studies else None)
        self._save(workspace)
        return findings

    def interpret_results(self, workspace, session=None, study=None):
        """Interpret existing simulation results from the Results Database."""

        self.initialize(workspace)
        simulation = workspace.simulation_workspace.initialize()
        studies = self._target_studies(simulation, study)
        study_ids = {item.id for item in studies} if studies else set()
        results = [item for item in simulation.results if not study_ids or item.study_id in study_ids]
        interpretations = [self._interpret_result(simulation, item) for item in results]
        self.interpretations.extend(interpretations)
        self.statistics["interpretation_requests"] += 1
        self._update_session(session, current_study=studies[-1] if studies else None)
        self._save(workspace)
        return interpretations

    def compare_simulations(self, workspace, session=None):
        """Create cross-study engineering insight from existing studies and results."""

        self.initialize(workspace)
        simulation = workspace.simulation_workspace.initialize()
        study_types = sorted({item.study_type for item in simulation.studies})
        solved_types = sorted({simulation.manager.study_for(result.study_id).study_type for result in simulation.results if simulation.manager.study_for(result.study_id)})
        insight = MultiSimulationInsight(
            study_types,
            f"{len(study_types)} study families are configured and {len(solved_types)} have stored results.",
            self._cross_study_recommendations(study_types, solved_types),
            self._cross_study_conflicts(simulation),
            {"solved_study_types": solved_types, "result_count": len(simulation.results)},
        )
        self.multi_simulation_insights.append(insight)
        self.statistics["multi_study_requests"] += 1
        self._update_session(session, comparison=insight)
        self._save(workspace)
        return insight

    def assist_report(self, prompt, workspace, session=None):
        """Generate AI report-assistance metadata from existing simulation content."""

        self.initialize(workspace)
        interpretations = self.interpret_results(workspace, session)
        insight = self.compare_simulations(workspace, session)
        recommendations = [item for interpretation in interpretations for item in interpretation.recommendations]
        warnings = [item for interpretation in interpretations for item in interpretation.warnings]
        report = SimulationReportAssistance(
            "AI Engineering Simulation Summary",
            f"Engineering simulation package contains {len(interpretations)} interpreted result records across {len(insight.involved_study_types)} configured study families.",
            recommendations or insight.cross_study_recommendations,
            warnings,
            [insight.to_dict()],
            {"source": "AI Engineering Simulation Assistant", "prompt": prompt},
        )
        self.report_assistance.append(report)
        self.statistics["report_requests"] += 1
        self._save(workspace)
        return report

    def respond(self, prompt, workspace, session=None, study=None):
        """Run the full engineering simulation assistance loop."""

        self.initialize(workspace)
        active_session = session or self.start_session(workspace)
        recommendations = self.recommend_studies(prompt, workspace, active_session)
        guidance = self.configure_simulation(prompt, workspace, active_session, study)
        findings = self.review_setup(workspace, active_session, study)
        interpretations = self.interpret_results(workspace, active_session, study)
        insight = self.compare_simulations(workspace, active_session)
        report = self.assist_report(prompt, workspace, active_session)
        self.statistics["planning_requests"] += 1
        response = EngineeringSimulationAssistantResponse(
            recommendations,
            guidance,
            findings,
            interpretations,
            list(self.knowledge_items),
            report,
            insight,
            self.diagnostics(),
        )
        self._record_session_message(active_session, prompt, response)
        self._save(workspace)
        return response

    def execute_study_through_commands(self, workspace, study, approved=False, approved_by=""):
        """Execute a study only through existing command wrappers after approval."""

        if not approved:
            return {"status": "Pending Approval", "approved": False, "command_routed": False}
        simulation = workspace.simulation_workspace.initialize()
        target = simulation.manager.study_for(study)
        if target is None:
            self.statistics["validation_failures"] += 1
            return {"status": "Rejected", "approved": True, "command_routed": False, "reason": "Study not found"}
        command_class = COMMAND_BY_STUDY_TYPE.get(target.study_type)
        if command_class is None:
            self.statistics["validation_failures"] += 1
            return {"status": "Rejected", "approved": True, "command_routed": False, "reason": f"No command wrapper for {target.study_type}"}
        command = command_class(workspace, target)
        workspace.command_manager.execute(command)
        record = {
            "study_id": target.id,
            "study_type": target.study_type,
            "approved_by": approved_by,
            "command": command_class.__name__,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command_routed": True,
        }
        self.execution_records.append(record)
        self.statistics["command_routed_executions"] += 1
        self._save(workspace)
        return {"status": "Executed", "approved": True, "command_routed": True, "record": record}

    def diagnostics(self):
        """Return AI Engineering Simulation Assistant diagnostics."""

        return {
            "initialized": self.initialized,
            "conversations": len(self.conversations),
            "recommendations": len(self.recommendations),
            "configuration_guidance": len(self.configuration_guidance),
            "review_findings": len(self.review_findings),
            "interpretations": len(self.interpretations),
            "knowledge_items": len(self.knowledge_items),
            "report_assistance": len(self.report_assistance),
            "multi_simulation_insights": len(self.multi_simulation_insights),
            "execution_records": len(self.execution_records),
            **dict(self.statistics),
        }

    def to_dict(self):
        """Return JSON-safe assistant state."""

        return {
            "initialized": self.initialized,
            "conversations": [item.to_dict() for item in self.conversations],
            "recommendations": [item.to_dict() for item in self.recommendations],
            "configuration_guidance": [item.to_dict() for item in self.configuration_guidance],
            "review_findings": [item.to_dict() for item in self.review_findings],
            "interpretations": [item.to_dict() for item in self.interpretations],
            "knowledge_items": [item.to_dict() for item in self.knowledge_items],
            "report_assistance": [item.to_dict() for item in self.report_assistance],
            "multi_simulation_insights": [item.to_dict() for item in self.multi_simulation_insights],
            "execution_records": [dict(item) for item in self.execution_records],
            "statistics": dict(self.statistics),
        }

    def load_from_settings(self, workspace):
        """Restore assistant state from the existing Workspace settings path."""

        data = workspace.project_settings.get(AI_ENGINEERING_SIMULATION_ASSISTANT_SETTINGS_KEY, {})
        if not data:
            return self
        self.initialized = bool(data.get("initialized", self.initialized))
        self.conversations = [EngineeringSimulationConversation.from_dict(item) for item in data.get("conversations", [])]
        self.recommendations = [SimulationStudyRecommendation.from_dict(item) for item in data.get("recommendations", [])]
        self.configuration_guidance = [SimulationConfigurationGuidance.from_dict(item) for item in data.get("configuration_guidance", [])]
        self.review_findings = [EngineeringReviewFinding.from_dict(item) for item in data.get("review_findings", [])]
        self.interpretations = [SimulationResultInterpretation.from_dict(item) for item in data.get("interpretations", [])]
        restored_knowledge = [EngineeringKnowledgeItem.from_dict(item) for item in data.get("knowledge_items", [])]
        if restored_knowledge:
            self.knowledge_items = restored_knowledge
        self.report_assistance = [SimulationReportAssistance.from_dict(item) for item in data.get("report_assistance", [])]
        self.multi_simulation_insights = [MultiSimulationInsight.from_dict(item) for item in data.get("multi_simulation_insights", [])]
        self.execution_records = [dict(item) for item in data.get("execution_records", [])]
        self.statistics.update(dict(data.get("statistics", {})))
        return self

    def _save(self, workspace):
        workspace.project_settings[AI_ENGINEERING_SIMULATION_ASSISTANT_SETTINGS_KEY] = self.to_dict()

    def _workspace_context(self, workspace):
        simulation = workspace.simulation_workspace.initialize()
        return {
            "study_count": len(simulation.studies),
            "result_count": len(simulation.results),
            "study_types": sorted({study.study_type for study in simulation.studies}),
            "geometry_owner": "Workspace/ParametricEngine/GeometryKernel/BodyManager",
            "assistant_role": "orchestration",
        }

    def _target_studies(self, simulation, study):
        if study is None:
            return []
        target = simulation.manager.study_for(study)
        return [target] if target is not None else []

    def _guidance_for_study(self, study):
        common = ["Confirm material references", "Confirm target geometry references", "Review solver settings before execution"]
        by_type = {
            "Static Structural": (["Fixed, pinned, roller, symmetry"], ["Force, pressure, gravity, moment"], ["Mesh refinement near supports and high-gradient regions"]),
            "Building Structural": (["Storey constraints and foundation supports"], ["Dead, live, wind, seismic, snow"], ["Code metadata and load combinations"]),
            "Thermal": (["Fixed temperature, heat flux, convection, radiation"], ["Internal heat and solar gain"], ["Thermal boundary refinement"]),
            "Daylight": (["Site location, sky model, openings"], ["Solar vectors and daylight zones"], ["Lux and glare metrics"]),
            "Energy": (["Climate, envelope, occupancy, HVAC"], ["Schedules and internal gains"], ["Annual and peak-load settings"]),
            "CFD": (["Velocity inlets, pressure outlets, walls"], ["Supply, exhaust, wind, buoyancy"], ["Boundary-layer and region refinement"]),
            "Motion": (["Ground body, joints, constraints"], ["Drivers and motion profiles"], ["Timeline and convergence settings"]),
            "Optimization": (["Variables, constraints, objectives"], ["Existing study results for objective context"], ["Candidate limits and ranking settings"]),
        }
        boundaries, loads, settings = by_type.get(study.study_type, (common, [], []))
        return SimulationConfigurationGuidance(
            study.id,
            study.study_type,
            boundary_conditions=list(boundaries),
            loads=list(loads),
            materials=common,
            solver_settings=list(settings),
            validation_messages=[f"{study.study_type} configuration guidance references existing Simulation Workspace metadata only."],
        )

    def _study_findings(self, simulation, study):
        findings = []
        if not study.target_geometry:
            findings.append(EngineeringReviewFinding("Target Geometry", f"{study.name} has no target geometry references.", "Medium", "Assign model references before execution.", study.id))
        if not study.material_references and study.study_type in {"Static Structural", "Thermal", "Energy", "CFD"}:
            findings.append(EngineeringReviewFinding("Materials", f"{study.name} has no material references.", "Medium", "Assign engineering material metadata.", study.id))
        meshes = [item for item in simulation.mesh_definitions if item.study_id == study.id]
        if study.study_type in {"Static Structural", "Thermal", "CFD"} and not meshes:
            findings.append(EngineeringReviewFinding("Mesh", f"{study.name} has no mesh definition.", "Medium", "Create a mesh definition through Simulation Workspace.", study.id))
        results = [item for item in simulation.results if item.study_id == study.id]
        if not results:
            findings.append(EngineeringReviewFinding("Results", f"{study.name} has no stored result yet.", "Low", "Execute through the existing command wrapper after setup is approved.", study.id))
        return findings

    def _interpret_result(self, simulation, result):
        study = simulation.manager.study_for(result.study_id)
        study_type = study.study_type if study is not None else "Unknown"
        metrics = dict(result.scalars)
        warnings = []
        recommendations = []
        if "max_displacement" in metrics and metrics["max_displacement"] > 0.05:
            warnings.append("Displacement may require engineering review.")
        if "min_safety_factor" in metrics and metrics["min_safety_factor"] < 1.5:
            warnings.append("Safety factor is below the preferred review threshold.")
        if "annual_energy_use" in metrics:
            recommendations.append("Compare envelope and HVAC alternatives to reduce annual energy use.")
        if "average_lux" in metrics:
            recommendations.append("Review daylight uniformity alongside glare risk.")
        if "best_score" in metrics:
            recommendations.append("Review top-ranked optimization alternatives before issuing model-changing commands.")
        summary = f"{study_type} result contains {len(metrics)} scalar metrics and {len(result.vectors)} vector groups."
        return SimulationResultInterpretation(result.id, study_type, summary, metrics, recommendations, warnings, {"result_type": result.result_type})

    def _cross_study_recommendations(self, study_types, solved_types):
        recommendations = []
        if "Energy" in study_types and "Daylight" in study_types:
            recommendations.append("Compare daylight gains against energy demand before final envelope decisions.")
        if "Thermal" in study_types and "CFD" in study_types:
            recommendations.append("Use thermal and airflow results together for comfort-sensitive zones.")
        if "Optimization" in study_types and len(solved_types) < 2:
            recommendations.append("Populate optimization context with more solved study results before ranking alternatives.")
        if not recommendations:
            recommendations.append("Simulation package is ready for discipline-specific engineering review.")
        return recommendations

    def _cross_study_conflicts(self, simulation):
        conflicts = []
        study_types = {item.study_type for item in simulation.studies}
        if "Optimization" in study_types and not simulation.results:
            conflicts.append("Optimization exists without source results for comparison context.")
        if "Energy" in study_types and "Daylight" not in study_types:
            conflicts.append("Energy study lacks daylight context for solar/daylight trade-off review.")
        return conflicts

    def _recommendation_reason(self, study_type, prompt):
        return f"{study_type} is recommended because the request references engineering intent suited to that analysis workflow."

    def _prerequisites(self, study_type):
        return {
            "Static Structural": ["Material assignment", "Loads", "Supports", "Mesh definition"],
            "Building Structural": ["Storeys", "Members", "Load cases", "Design-code metadata"],
            "Thermal": ["Thermal material properties", "Thermal boundaries", "Heat sources", "Mesh definition"],
            "Daylight": ["Location", "Sky model", "Openings", "Daylight zones"],
            "Energy": ["Climate profile", "Envelope", "Schedules", "HVAC metadata"],
            "CFD": ["Fluid domain", "Flow boundaries", "Flow sources", "Mesh definition"],
            "Motion": ["Rigid bodies", "Joints", "Drivers", "Timeline"],
            "Optimization": ["Design variables", "Constraints", "Objectives", "Existing results"],
        }.get(study_type, ["Study metadata"])

    def _sequencing(self, study_type):
        if study_type == "Optimization":
            return ["Run source simulations", "Create optimization study", "Evaluate candidates", "Compare ranked alternatives"]
        if study_type == "Energy":
            return ["Thermal review", "Daylight review", "Energy study", "Compare passive strategies"]
        return ["Prepare inputs", "Validate setup", "Execute through command wrapper", "Interpret results"]

    def _default_knowledge(self):
        return [
            EngineeringKnowledgeItem("Boundary condition review", "Simulation", "Every study should have explicit constraints, loads or environmental drivers before execution."),
            EngineeringKnowledgeItem("Material guidance", "Engineering", "Engineering material properties should match the active simulation discipline."),
            EngineeringKnowledgeItem("Cross-study review", "Multi-Simulation", "Energy, daylight, thermal and CFD results should be reviewed together for building-performance decisions."),
            EngineeringKnowledgeItem("Optimization guidance", "Optimization", "Optimization recommendations should be treated as candidate rankings until the user approves command-routed model changes."),
        ]

    def _update_session(self, session, recommendations=None, current_study=None, comparison=None):
        if session is None or not isinstance(session, EngineeringSimulationConversation):
            return
        if current_study is not None:
            if session.current_study_id and session.current_study_id != current_study.id:
                session.previous_study_ids.append(session.current_study_id)
            session.current_study_id = current_study.id
        if recommendations:
            session.recommendation_history.extend([item.to_dict() for item in recommendations])
        if comparison is not None:
            session.comparison_history.append(comparison.to_dict())
        session.engineering_context["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.statistics["conversation_context_updates"] += 1

    def _record_session_message(self, session, prompt, response):
        if hasattr(session, "add_message"):
            session.add_message("user", prompt, "ai-engineering-simulation-assistant")
            session.add_message("assistant", str(response.to_dict()), "ai-engineering-simulation-assistant")
