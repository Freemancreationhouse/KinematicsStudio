"""AI Manufacturing Assistant orchestration for existing manufacturing systems.

The assistant interprets manufacturing intent, plans workflows, validates
readiness, records recommendations and coordinates approved machine dispatch
through the existing Manufacturing Engine. It never owns geometry, generates
toolpaths, slices, simulates, or communicates with machines outside the
Workspace-owned production APIs.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


AI_MANUFACTURING_ASSISTANT_SETTINGS_KEY = "ai_manufacturing_assistant"


@dataclass
class ManufacturingIntent:
    """Resolved manufacturing intent from a natural-language request."""

    prompt: str
    process: str
    machine_type: str
    workflow: list
    material: str = ""
    required_validation: bool = True
    required_simulation: bool = True
    required_execution: bool = False
    objectives: list = field(default_factory=list)
    confidence: float = 0.0
    warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe intent metadata."""

        return {
            "id": self.id,
            "prompt": self.prompt,
            "process": self.process,
            "machine_type": self.machine_type,
            "workflow": list(self.workflow),
            "material": self.material,
            "required_validation": self.required_validation,
            "required_simulation": self.required_simulation,
            "required_execution": self.required_execution,
            "objectives": list(self.objectives),
            "confidence": self.confidence,
            "warnings": list(self.warnings),
        }

    @staticmethod
    def from_dict(data):
        """Restore intent metadata from persisted settings."""

        data = data or {}
        return ManufacturingIntent(
            data.get("prompt", ""),
            data.get("process", "Manufacturing"),
            data.get("machine_type", "Machine"),
            list(data.get("workflow", [])),
            data.get("material", ""),
            bool(data.get("required_validation", True)),
            bool(data.get("required_simulation", True)),
            bool(data.get("required_execution", False)),
            list(data.get("objectives", [])),
            float(data.get("confidence", 0.0)),
            list(data.get("warnings", [])),
            data.get("id", str(uuid4())),
        )


@dataclass
class ManufacturingWorkflowPlan:
    """Existing-engine-only manufacturing workflow orchestration plan."""

    intent_id: str
    process: str
    job_id: str = ""
    steps: list = field(default_factory=list)
    dependencies: dict = field(default_factory=dict)
    readiness: dict = field(default_factory=dict)
    validation: dict = field(default_factory=dict)
    existing_systems: list = field(default_factory=list)
    approval_required: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe workflow plan metadata."""

        return {
            "id": self.id,
            "intent_id": self.intent_id,
            "process": self.process,
            "job_id": self.job_id,
            "steps": [dict(step) for step in self.steps],
            "dependencies": dict(self.dependencies),
            "readiness": dict(self.readiness),
            "validation": dict(self.validation),
            "existing_systems": list(self.existing_systems),
            "approval_required": self.approval_required,
        }

    @staticmethod
    def from_dict(data):
        """Restore a workflow plan from persisted metadata."""

        data = data or {}
        return ManufacturingWorkflowPlan(
            data.get("intent_id", ""),
            data.get("process", "Manufacturing"),
            data.get("job_id", ""),
            [dict(item) for item in data.get("steps", [])],
            dict(data.get("dependencies", {})),
            dict(data.get("readiness", {})),
            dict(data.get("validation", {})),
            list(data.get("existing_systems", [])),
            bool(data.get("approval_required", True)),
            data.get("id", str(uuid4())),
        )


@dataclass
class ManufacturingRecommendation:
    """Recommendation-only manufacturing optimization result."""

    category: str
    recommendation: str
    reason: str
    expected_benefit: str
    priority: str = "Medium"
    source: str = "AI Manufacturing Assistant"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe recommendation metadata."""

        return {
            "id": self.id,
            "category": self.category,
            "recommendation": self.recommendation,
            "reason": self.reason,
            "expected_benefit": self.expected_benefit,
            "priority": self.priority,
            "source": self.source,
        }

    @staticmethod
    def from_dict(data):
        """Restore recommendation metadata from persisted settings."""

        data = data or {}
        return ManufacturingRecommendation(
            data.get("category", "Manufacturing"),
            data.get("recommendation", ""),
            data.get("reason", ""),
            data.get("expected_benefit", ""),
            data.get("priority", "Medium"),
            data.get("source", "AI Manufacturing Assistant"),
            data.get("id", str(uuid4())),
        )


@dataclass
class ManufacturingApprovalRecord:
    """Approval gate metadata before machine communication is started."""

    workflow_plan_id: str
    approved: bool
    status: str = "Pending"
    approved_by: str = ""
    timestamp: str = ""
    execution_session_id: str = ""
    warnings: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe approval metadata."""

        return {
            "id": self.id,
            "workflow_plan_id": self.workflow_plan_id,
            "approved": self.approved,
            "status": self.status,
            "approved_by": self.approved_by,
            "timestamp": self.timestamp,
            "execution_session_id": self.execution_session_id,
            "warnings": list(self.warnings),
        }

    @staticmethod
    def from_dict(data):
        """Restore approval metadata from persisted settings."""

        data = data or {}
        return ManufacturingApprovalRecord(
            data.get("workflow_plan_id", ""),
            bool(data.get("approved", False)),
            data.get("status", "Pending"),
            data.get("approved_by", ""),
            data.get("timestamp", ""),
            data.get("execution_session_id", ""),
            list(data.get("warnings", [])),
            data.get("id", str(uuid4())),
        )


@dataclass
class ManufacturingConversation:
    """Workspace-associated manufacturing conversation memory."""

    workspace_name: str
    messages: list = field(default_factory=list)
    intent_ids: list = field(default_factory=list)
    workflow_plan_ids: list = field(default_factory=list)
    recommendation_ids: list = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe conversation metadata."""

        return {
            "id": self.id,
            "workspace_name": self.workspace_name,
            "messages": [dict(item) for item in self.messages],
            "intent_ids": list(self.intent_ids),
            "workflow_plan_ids": list(self.workflow_plan_ids),
            "recommendation_ids": list(self.recommendation_ids),
            "preferences": dict(self.preferences),
        }

    @staticmethod
    def from_dict(data):
        """Restore conversation memory from persisted settings."""

        data = data or {}
        return ManufacturingConversation(
            data.get("workspace_name", ""),
            [dict(item) for item in data.get("messages", [])],
            list(data.get("intent_ids", [])),
            list(data.get("workflow_plan_ids", [])),
            list(data.get("recommendation_ids", [])),
            dict(data.get("preferences", {})),
            data.get("id", str(uuid4())),
        )


class AIManufacturingAssistant:
    """Manufacturing engineer assistant that orchestrates existing systems only."""

    PROCESS_SYSTEMS = {
        "CNC": ["Manufacturing Engine", "CAM Planner", "Simulation Engine", "Communication Engine"],
        "FDM": ["Manufacturing Engine", "Additive Manufacturing Engine", "Simulation Engine", "Communication Engine"],
        "SLA": ["Manufacturing Engine", "Additive Manufacturing Engine", "Simulation Engine", "Communication Engine"],
        "Laser": ["Manufacturing Engine", "Sheet Manufacturing", "Simulation Engine", "Communication Engine"],
        "Plasma": ["Manufacturing Engine", "Sheet Manufacturing", "Simulation Engine", "Communication Engine"],
        "Waterjet": ["Manufacturing Engine", "Sheet Manufacturing", "Simulation Engine", "Communication Engine"],
        "Robotics": ["Manufacturing Engine", "Robotics & Motion", "Simulation Engine", "Communication Engine"],
    }

    def __init__(self, ai_engine=None):

        self.ai_engine = ai_engine
        self.initialized = False
        self.version = "1.7"
        self.sessions = []
        self.intents = []
        self.workflow_plans = []
        self.recommendations = []
        self.approvals = []
        self.statistics = {
            "sessions": 0,
            "intents": 0,
            "workflow_plans": 0,
            "recommendations": 0,
            "validation_decisions": 0,
            "simulation_requests": 0,
            "execution_requests": 0,
            "approval_history": 0,
            "failed": 0,
        }

    def initialize(self, workspace):
        """Initialize the assistant against an existing Workspace."""

        self._require_workspace(workspace)
        self.load_from_settings(workspace)
        self.initialized = True
        self._save(workspace)
        return self

    def start_session(self, workspace, preferences=None):
        """Start a manufacturing conversation associated with the Workspace."""

        self._require_workspace(workspace)
        session = ManufacturingConversation(
            workspace_name=getattr(workspace, "name", ""),
            preferences=dict(preferences or {}),
        )
        self.sessions.append(session)
        self.statistics["sessions"] = len(self.sessions)
        self._save(workspace)
        return session

    def interpret_request(self, prompt, workspace=None, session=None):
        """Interpret manufacturing intent without modifying CAD or manufacturing data."""

        text = (prompt or "").strip()
        lowered = text.lower()
        process = "Manufacturing"
        machine_type = "Machine"
        workflow = ["CAD", "Manufacturing Validation"]
        confidence = 0.55
        if any(word in lowered for word in ("cnc", "mill", "machine", "machining")):
            process = "CNC"
            machine_type = "CNC Mill"
            workflow = ["CAD", "CAM", "Simulation", "Machine"]
            confidence = 0.9
        if any(word in lowered for word in ("fdm", "filament", "printer", "print this", "3d print", "printed")):
            process = "FDM"
            machine_type = "FDM Printer"
            workflow = ["CAD", "Slice", "Simulation", "Printer"]
            confidence = 0.9
        if any(word in lowered for word in ("sla", "resin")):
            process = "SLA"
            machine_type = "SLA Printer"
            workflow = ["CAD", "SLA Slice", "Simulation", "Printer"]
            confidence = 0.95
        if "laser" in lowered:
            process = "Laser"
            machine_type = "Laser Cutter"
            workflow = ["CAD", "Nest", "Laser Program", "Simulation", "Machine"]
            confidence = 0.95
        if "plasma" in lowered:
            process = "Plasma"
            machine_type = "Plasma Cutter"
            workflow = ["CAD", "Nest", "Plasma Program", "Simulation", "Machine"]
            confidence = 0.95
        if "waterjet" in lowered:
            process = "Waterjet"
            machine_type = "Waterjet"
            workflow = ["CAD", "Nest", "Waterjet Program", "Simulation", "Machine"]
            confidence = 0.95
        if any(word in lowered for word in ("robot", "robotic", "pick and place", "tend")):
            process = "Robotics"
            machine_type = "Robot"
            workflow = ["CAD", "Robot Motion", "Simulation", "Machine"]
            confidence = 0.9
        objectives = self._objectives_from_text(lowered)
        intent = ManufacturingIntent(
            text,
            process,
            machine_type,
            workflow,
            material=self._material_from_text(lowered),
            required_validation=True,
            required_simulation=any(item in workflow for item in ("Simulation",)),
            required_execution=any(word in lowered for word in ("run", "send", "start", "execute", "production")),
            objectives=objectives,
            confidence=confidence,
            warnings=[] if process != "Manufacturing" else ["Manufacturing process could not be resolved from the request."],
        )
        self.intents.append(intent)
        self.statistics["intents"] = len(self.intents)
        self._attach_to_session(session, "user", text, intent_id=intent.id)
        if session is not None:
            session.intent_ids.append(intent.id)
        if workspace is not None:
            self._save(workspace)
        return intent

    def plan_workflow(self, intent, workspace, job=None):
        """Plan a manufacturing workflow by reusing existing manufacturing subsystems."""

        self._require_workspace(workspace)
        manufacturing_engine = self._manufacturing_engine(workspace)
        resolved_intent = self._intent_for(intent)
        target_job = manufacturing_engine.job_for(job) if job is not None else None
        readiness = self._readiness(manufacturing_engine, resolved_intent.process, target_job)
        steps = self._workflow_steps(resolved_intent, readiness)
        plan = ManufacturingWorkflowPlan(
            intent_id=resolved_intent.id,
            process=resolved_intent.process,
            job_id=getattr(target_job, "id", ""),
            steps=steps,
            dependencies=self._workflow_dependencies(steps),
            readiness=readiness,
            validation=self.validate_workflow_metadata(resolved_intent, readiness),
            existing_systems=list(self.PROCESS_SYSTEMS.get(resolved_intent.process, ["Manufacturing Engine"])),
            approval_required=resolved_intent.required_execution,
        )
        self.workflow_plans.append(plan)
        self.statistics["workflow_plans"] = len(self.workflow_plans)
        if resolved_intent.required_simulation:
            self.statistics["simulation_requests"] += 1
        self._save(workspace)
        return plan

    def validate_workflow(self, plan, workspace):
        """Validate the plan and the existing Manufacturing Engine state."""

        self._require_workspace(workspace)
        resolved_plan = self._plan_for(plan)
        manufacturing_validation = self._manufacturing_engine(workspace).validate()
        valid = bool(resolved_plan.validation.get("valid", False)) and manufacturing_validation.valid
        errors = list(resolved_plan.validation.get("errors", [])) + list(manufacturing_validation.errors)
        warnings = list(resolved_plan.validation.get("warnings", [])) + list(manufacturing_validation.warnings)
        resolved_plan.validation = {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "manufacturing_engine": manufacturing_validation.to_dict(),
        }
        self.statistics["validation_decisions"] += 1
        self._save(workspace)
        return dict(resolved_plan.validation)

    def recommend_optimizations(self, intent_or_plan, workspace, job=None):
        """Return recommendation-only manufacturing optimization advice."""

        self._require_workspace(workspace)
        intent = self._intent_for(intent_or_plan) if not isinstance(intent_or_plan, ManufacturingWorkflowPlan) else self._intent_for(intent_or_plan.intent_id)
        target_job = self._manufacturing_engine(workspace).job_for(job) if job is not None else None
        recommendations = [
            ManufacturingRecommendation(
                "Validation",
                "Run manufacturing validation before creating or dispatching production output.",
                "The assistant is required to use the Manufacturing Engine validation gate.",
                "Prevents incomplete setups, missing programs, and invalid machine assignments.",
                "High",
            ),
            ManufacturingRecommendation(
                "Simulation",
                "Run the existing Simulation Engine before any machine communication.",
                "Simulation is the approved readiness gate for CNC, additive, sheet, and robotics workflows.",
                "Reduces production risk without modifying model geometry.",
                "High",
            ),
        ]
        if intent.process == "CNC":
            recommendations.append(ManufacturingRecommendation("Tooling", "Review tool compatibility, feeds, speeds, and work offset before dispatch.", "CNC jobs depend on tool library, CAM plan, and controller-specific G-code metadata.", "Improves cycle time and lowers tool/load risk."))
        elif intent.process in {"FDM", "SLA"}:
            recommendations.append(ManufacturingRecommendation("Build Strategy", "Review orientation, supports, layer settings, and material profile before printing.", "Additive jobs depend on slicer output, supports, and build plate validation.", "Improves print reliability and material usage."))
        elif intent.process in {"Laser", "Plasma", "Waterjet"}:
            recommendations.append(ManufacturingRecommendation("Nesting", "Review nesting, kerf compensation, pierce points, and material utilization.", "Sheet workflows depend on generated cutting paths and sheet utilization metadata.", "Reduces material waste and improves cut quality."))
        elif intent.process == "Robotics":
            recommendations.append(ManufacturingRecommendation("Motion", "Review reachability, joint limits, payload, frames, and generated robot program.", "Robotics workflows depend on trajectory and kinematic validation metadata.", "Improves cell safety and cycle reliability."))
        if target_job is not None:
            recommendations.append(ManufacturingRecommendation("Job", f"Use existing manufacturing job '{target_job.name}' as the workflow source.", "The assistant reuses Manufacturing Engine job metadata instead of creating duplicate job state.", "Preserves persistence, diagnostics, and execution history.", "Low"))
        self.recommendations.extend(recommendations)
        self.statistics["recommendations"] = len(self.recommendations)
        self._save(workspace)
        return recommendations

    def orchestrate_execution(self, plan, workspace, connection=None, approved=False, approved_by=""):
        """Coordinate approved dispatch through the existing Communication Engine."""

        self._require_workspace(workspace)
        resolved_plan = self._plan_for(plan)
        if not approved:
            record = ManufacturingApprovalRecord(
                resolved_plan.id,
                False,
                "Pending Approval",
                approved_by,
                self._timestamp(),
                "",
                ["Machine execution requires explicit approval."],
            )
            self.approvals.append(record)
            self.statistics["approval_history"] = len(self.approvals)
            self._save(workspace)
            return record
        validation = self.validate_workflow(resolved_plan, workspace)
        if not validation.get("valid", False):
            record = ManufacturingApprovalRecord(
                resolved_plan.id,
                True,
                "Blocked",
                approved_by,
                self._timestamp(),
                "",
                list(validation.get("errors", [])),
            )
            self.approvals.append(record)
            self.statistics["approval_history"] = len(self.approvals)
            self.statistics["failed"] += 1
            self._save(workspace)
            return record
        engine = self._manufacturing_engine(workspace)
        target_job = engine.job_for(resolved_plan.job_id)
        target_connection = self._connection_for(engine, connection)
        if target_job is None or target_connection is None:
            record = ManufacturingApprovalRecord(
                resolved_plan.id,
                True,
                "Blocked",
                approved_by,
                self._timestamp(),
                "",
                ["Approved dispatch requires an existing manufacturing job and machine connection."],
            )
            self.approvals.append(record)
            self.statistics["approval_history"] = len(self.approvals)
            self.statistics["failed"] += 1
            self._save(workspace)
            return record
        if target_connection.state != "Connected":
            engine.connect_machine(target_connection)
        queue_item = engine.queue_machine_job(target_job, target_connection, priority=10, ai_orchestrated=True)
        communication_session = engine.upload_machine_job(queue_item)
        engine.start_machine_job(communication_session)
        record = ManufacturingApprovalRecord(
            resolved_plan.id,
            True,
            "Execution Started",
            approved_by,
            self._timestamp(),
            communication_session.id,
            [],
        )
        self.approvals.append(record)
        self.statistics["execution_requests"] += 1
        self.statistics["approval_history"] = len(self.approvals)
        self._save(workspace)
        return record

    def respond(self, prompt, workspace, session=None, job=None, connection=None, approved=False):
        """Run the full conversational manufacturing planning loop."""

        active_session = session or self.start_session(workspace)
        intent = self.interpret_request(prompt, workspace, active_session)
        plan = self.plan_workflow(intent, workspace, job)
        validation = self.validate_workflow(plan, workspace)
        recommendations = self.recommend_optimizations(plan, workspace, job)
        approval = None
        if intent.required_execution:
            approval = self.orchestrate_execution(plan, workspace, connection, approved)
        response = {
            "intent": intent.to_dict(),
            "workflow_plan": plan.to_dict(),
            "validation": validation,
            "recommendations": [item.to_dict() for item in recommendations],
            "approval": approval.to_dict() if approval is not None else None,
            "explanation": {
                "manufacturing_process": intent.process,
                "workflow": list(intent.workflow),
                "systems_reused": list(plan.existing_systems),
                "geometry_modified": False,
                "meshentity_modified": False,
                "automatic_model_changes": False,
            },
        }
        self._attach_to_session(active_session, "assistant", response)
        self._save(workspace)
        return response

    def diagnostics(self):
        """Return AI Manufacturing Assistant diagnostics."""

        return {
            **dict(self.statistics),
            "initialized": self.initialized,
            "version": self.version,
            "workflow_processes": sorted({plan.process for plan in self.workflow_plans}),
            "approval_statuses": [approval.status for approval in self.approvals],
        }

    def to_dict(self):
        """Return JSON-safe assistant state."""

        return {
            "initialized": self.initialized,
            "version": self.version,
            "sessions": [session.to_dict() for session in self.sessions],
            "intents": [intent.to_dict() for intent in self.intents],
            "workflow_plans": [plan.to_dict() for plan in self.workflow_plans],
            "recommendations": [item.to_dict() for item in self.recommendations],
            "approvals": [item.to_dict() for item in self.approvals],
            "statistics": dict(self.statistics),
        }

    def load_from_settings(self, workspace):
        """Restore assistant state from existing Workspace project settings."""

        data = getattr(workspace, "project_settings", {}).get(AI_MANUFACTURING_ASSISTANT_SETTINGS_KEY, {})
        self.initialized = bool(data.get("initialized", self.initialized))
        self.version = data.get("version", self.version)
        self.sessions = [ManufacturingConversation.from_dict(item) for item in data.get("sessions", [])]
        self.intents = [ManufacturingIntent.from_dict(item) for item in data.get("intents", [])]
        self.workflow_plans = [ManufacturingWorkflowPlan.from_dict(item) for item in data.get("workflow_plans", [])]
        self.recommendations = [ManufacturingRecommendation.from_dict(item) for item in data.get("recommendations", [])]
        self.approvals = [ManufacturingApprovalRecord.from_dict(item) for item in data.get("approvals", [])]
        self.statistics = {
            **dict(self.statistics),
            **dict(data.get("statistics", {})),
        }
        return self

    def _save(self, workspace):
        workspace.project_settings[AI_MANUFACTURING_ASSISTANT_SETTINGS_KEY] = self.to_dict()

    def _require_workspace(self, workspace):
        if workspace is None:
            raise ValueError("AI Manufacturing Assistant requires an existing Workspace.")
        if not hasattr(workspace, "manufacturing_engine"):
            raise ValueError("Workspace must expose the existing Manufacturing Engine.")

    def _manufacturing_engine(self, workspace):
        engine = workspace.manufacturing_engine
        if not engine.state.initialized:
            engine.initialize()
        return engine

    def _intent_for(self, intent):
        if isinstance(intent, ManufacturingIntent):
            return intent
        return next(item for item in self.intents if item.id == intent)

    def _plan_for(self, plan):
        if isinstance(plan, ManufacturingWorkflowPlan):
            return plan
        return next(item for item in self.workflow_plans if item.id == plan)

    def _connection_for(self, engine, connection):
        if connection is None:
            return None
        return next((item for item in engine.machine_connections if item is connection or item.id == connection), None)

    def _readiness(self, engine, process, job):
        job_id = getattr(job, "id", "")
        readiness = {
            "job": bool(job_id),
            "machine_workspace": bool(engine.machine_workspace),
            "machine_profiles": len(getattr(engine.product_manager, "machine_profiles", [])),
            "materials": len(getattr(engine.product_manager, "engineering_materials", [])),
            "tools": len(getattr(engine.product_manager, "tool_definitions", [])),
            "simulation_report": any(report.manufacturing_job_id == job_id and report.valid for report in engine.simulation_reports),
            "communication_connection": False,
            "generated_program": False,
        }
        if job is not None:
            profile_id = getattr(getattr(job, "metadata", None), "properties", {}).get("machine_profile_id", "")
            readiness["communication_connection"] = any(connection.machine_profile_id == profile_id for connection in engine.machine_connections)
            readiness["generated_program"] = self._has_program(engine, process, job_id)
        return readiness

    def _has_program(self, engine, process, job_id):
        if process == "CNC":
            return any(program.job_id == job_id and program.valid for program in engine.generated_programs)
        if process in {"FDM", "SLA"}:
            return any(print_file.job_id == job_id and print_file.valid for print_file in engine.additive_print_files)
        if process in {"Laser", "Plasma", "Waterjet"}:
            return any(program.job_id == job_id and program.valid for program in engine.sheet_programs)
        if process == "Robotics":
            return any(program.job_id == job_id and program.valid for program in engine.robot_programs)
        return False

    def _workflow_steps(self, intent, readiness):
        steps = []
        for index, name in enumerate(intent.workflow, start=1):
            status = "Ready"
            if name in {"Machine", "Printer"} and not readiness.get("generated_program"):
                status = "Blocked"
            if name == "Simulation" and not readiness.get("simulation_report"):
                status = "Pending"
            steps.append({
                "order": index,
                "name": name,
                "status": status,
                "uses_existing_system": True,
            })
        return steps

    def _workflow_dependencies(self, steps):
        dependencies = {}
        previous = ""
        for step in steps:
            dependencies[step["name"]] = [previous] if previous else []
            previous = step["name"]
        return dependencies

    def validate_workflow_metadata(self, intent, readiness):
        errors = []
        warnings = []
        if intent.process == "Manufacturing":
            errors.append("Manufacturing process is unresolved.")
        if not readiness.get("job"):
            warnings.append("No manufacturing job was attached; workflow remains advisory.")
        if intent.required_execution and not readiness.get("generated_program"):
            errors.append("Execution requires an existing generated manufacturing program.")
        if intent.required_execution and not readiness.get("simulation_report"):
            errors.append("Execution requires an existing valid simulation report.")
        if intent.required_execution and not readiness.get("communication_connection"):
            errors.append("Execution requires an existing machine connection.")
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def _objectives_from_text(self, lowered):
        objectives = []
        for keyword, objective in (
            ("optimize", "Optimize manufacturing workflow"),
            ("time", "Estimate or reduce cycle time"),
            ("material", "Reduce material usage"),
            ("cost", "Reduce manufacturing cost"),
            ("support", "Improve support strategy"),
            ("feed", "Tune feeds and speeds"),
            ("speed", "Improve production speed"),
        ):
            if keyword in lowered:
                objectives.append(objective)
        return objectives or ["Manufacturing readiness"]

    def _material_from_text(self, lowered):
        for material in ("pla", "petg", "abs", "resin", "aluminum", "steel", "wood", "acrylic", "nylon"):
            if material in lowered:
                return material.upper() if material in {"pla", "petg", "abs"} else material.title()
        return ""

    def _attach_to_session(self, session, role, content, intent_id=""):
        if session is None:
            return
        session.messages.append({
            "role": role,
            "content": content,
            "intent_id": intent_id,
            "timestamp": self._timestamp(),
        })

    @staticmethod
    def _timestamp():
        return datetime.now(timezone.utc).isoformat()
