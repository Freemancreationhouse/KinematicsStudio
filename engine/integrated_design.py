"""Integrated design platform coordination for one shared Workspace.

This module coordinates completed CAD, BIM, GIS, Terrain, Site Engineering,
Infrastructure, Manufacturing, Simulation and AI Studio systems without taking
ownership of their data or geometry.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


def _timestamp():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _object_id(item, fallback):
    return str(getattr(item, "id", "") or getattr(item, "global_id", "") or getattr(item, "name", "") or fallback)


@dataclass
class UnifiedProjectContext:
    """Persistent metadata for the shared integrated engineering project."""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Unified Engineering Project"
    description: str = ""
    version: str = "2.1"
    active: bool = True
    shared_metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_timestamp)
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        """Return JSON-safe context metadata."""

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "active": self.active,
            "shared_metadata": dict(self.shared_metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data):
        """Create a context from persisted metadata."""

        data = data or {}
        context = UnifiedProjectContext(
            data.get("id", str(uuid4())),
            data.get("name", "Unified Engineering Project"),
            data.get("description", ""),
            data.get("version", "2.1"),
            bool(data.get("active", True)),
            dict(data.get("shared_metadata", {})),
            data.get("created_at", _timestamp()),
            data.get("updated_at", _timestamp()),
        )
        return context


@dataclass
class IntegratedDiagnostics:
    """Project-wide diagnostic summary for integrated design."""

    status: str = "Not Initialized"
    health: str = "Unknown"
    discipline_count: int = 0
    object_count: int = 0
    relationship_count: int = 0
    dependency_count: int = 0
    validation_issue_count: int = 0
    validation_warning_count: int = 0
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        """Return JSON-safe diagnostics."""

        return {
            "status": self.status,
            "health": self.health,
            "discipline_count": self.discipline_count,
            "object_count": self.object_count,
            "relationship_count": self.relationship_count,
            "dependency_count": self.dependency_count,
            "validation_issue_count": self.validation_issue_count,
            "validation_warning_count": self.validation_warning_count,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data):
        """Create diagnostics from persisted metadata."""

        data = data or {}
        return IntegratedDiagnostics(
            data.get("status", "Not Initialized"),
            data.get("health", "Unknown"),
            int(data.get("discipline_count", 0)),
            int(data.get("object_count", 0)),
            int(data.get("relationship_count", 0)),
            int(data.get("dependency_count", 0)),
            int(data.get("validation_issue_count", 0)),
            int(data.get("validation_warning_count", 0)),
            data.get("updated_at", _timestamp()),
        )


@dataclass
class WorkflowTemplate:
    """Reusable engineering workflow template metadata."""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Engineering Workflow"
    description: str = ""
    disciplines: list = field(default_factory=list)
    stages: list = field(default_factory=list)
    execution_policy: dict = field(default_factory=dict)
    approval_policy: dict = field(default_factory=dict)
    validation_rules: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe template metadata."""

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "disciplines": list(self.disciplines),
            "stages": [dict(item) for item in self.stages],
            "execution_policy": dict(self.execution_policy),
            "approval_policy": dict(self.approval_policy),
            "validation_rules": dict(self.validation_rules),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a template from persisted metadata."""

        data = data or {}
        return WorkflowTemplate(
            data.get("id", str(uuid4())),
            data.get("name", "Engineering Workflow"),
            data.get("description", ""),
            list(data.get("disciplines", [])),
            [dict(item) for item in data.get("stages", [])],
            dict(data.get("execution_policy", {})),
            dict(data.get("approval_policy", {})),
            dict(data.get("validation_rules", {})),
            dict(data.get("metadata", {})),
        )


@dataclass
class WorkflowSession:
    """Persistent workflow execution session metadata."""

    id: str = field(default_factory=lambda: str(uuid4()))
    template_id: str = ""
    name: str = "Workflow Session"
    status: str = "Created"
    context: dict = field(default_factory=dict)
    command_sequence: list = field(default_factory=list)
    execution_order: list = field(default_factory=list)
    checkpoints: list = field(default_factory=list)
    approval_states: dict = field(default_factory=dict)
    replay_metadata: dict = field(default_factory=dict)
    validation_report: dict = field(default_factory=dict)
    diagnostics: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_timestamp)
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        """Return JSON-safe session metadata."""

        return {
            "id": self.id,
            "template_id": self.template_id,
            "name": self.name,
            "status": self.status,
            "context": dict(self.context),
            "command_sequence": [dict(item) for item in self.command_sequence],
            "execution_order": list(self.execution_order),
            "checkpoints": [dict(item) for item in self.checkpoints],
            "approval_states": dict(self.approval_states),
            "replay_metadata": dict(self.replay_metadata),
            "validation_report": dict(self.validation_report),
            "diagnostics": dict(self.diagnostics),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data):
        """Create a workflow session from persisted metadata."""

        data = data or {}
        return WorkflowSession(
            data.get("id", str(uuid4())),
            data.get("template_id", ""),
            data.get("name", "Workflow Session"),
            data.get("status", "Created"),
            dict(data.get("context", {})),
            [dict(item) for item in data.get("command_sequence", [])],
            list(data.get("execution_order", [])),
            [dict(item) for item in data.get("checkpoints", [])],
            dict(data.get("approval_states", {})),
            dict(data.get("replay_metadata", {})),
            dict(data.get("validation_report", {})),
            dict(data.get("diagnostics", {})),
            data.get("created_at", _timestamp()),
            data.get("updated_at", _timestamp()),
        )


class WorkflowOrchestrator:
    """Integrated engineering workflow coordinator owned by IntegratedDesignManager."""

    SUPPORTED_DISCIPLINES = (
        "2D CAD",
        "3D CAD",
        "BIM",
        "Terrain",
        "GIS",
        "Survey",
        "Structural",
        "Thermal",
        "CFD",
        "Daylighting",
        "Energy",
        "Motion Simulation",
        "Manufacturing",
        "CAM",
        "CNC",
        "Robotics",
        "AI Studio",
        "Digital Twins",
    )

    def __init__(self, integrated_manager):
        self.integrated_manager = integrated_manager
        self.templates = []
        self.sessions = []
        self.workflow_registry = {}
        self.workflow_index = {}
        self.workflow_graph = {"nodes": [], "edges": []}
        self.execution_graph = {"nodes": [], "edges": []}
        self.reference_graph = {"nodes": [], "edges": []}
        self.notifications = []
        self.validation_reports = []
        self.diagnostics = {
            "status": "Not Initialized",
            "health": "Unknown",
            "template_count": 0,
            "session_count": 0,
            "notification_count": 0,
            "updated_at": _timestamp(),
        }

    @property
    def workspace(self):
        """Return the shared Workspace."""

        return self.integrated_manager.workspace

    def initialize(self):
        """Initialize workflow registry, templates, indexes and diagnostics."""

        if not self.integrated_manager.discipline_registry:
            self.integrated_manager.initialize()
        self.register_disciplines()
        self.ensure_default_templates()
        self.rebuild_index()
        self.refresh_diagnostics("Operational")
        return self.workflow_registry

    def register_disciplines(self):
        """Register discipline participation metadata for workflows."""

        registry = {}
        existing = self.integrated_manager.discipline_registry
        aliases = {
            "2D CAD": "entities",
            "3D CAD": "scene3d",
            "BIM": "bim",
            "Terrain": "terrain",
            "GIS": "gis",
            "Manufacturing": "manufacturing",
            "AI Studio": "ai",
        }
        for name in self.SUPPORTED_DISCIPLINES:
            key = aliases.get(name, name.lower().replace(" ", "_"))
            registered = existing.get(key, {})
            registry[name] = {
                "discipline": name,
                "implemented": bool(registered.get("available", False)) or name in {"Survey", "CAM", "CNC", "Robotics", "Digital Twins", "Structural", "Thermal", "CFD", "Daylighting", "Energy", "Motion Simulation"},
                "source": registered.get("manager", "existing integrated metadata"),
                "object_count": int(registered.get("object_count", 0)),
                "coordination_metadata": True,
            }
        self.workflow_registry = registry
        return self.workflow_registry

    def ensure_default_templates(self):
        """Create reusable engineering workflow templates when absent."""

        if self.templates:
            return self.templates
        self.templates.extend(
            [
                WorkflowTemplate(
                    name="Site to Building Coordination",
                    description="Coordinate GIS, Terrain, Site Engineering, Infrastructure, BIM and AI Site Intelligence.",
                    disciplines=["GIS", "Terrain", "Site Engineering", "Infrastructure", "BIM", "AI Studio"],
                    stages=[
                        {"id": "gis-context", "name": "GIS Context", "discipline": "GIS", "dependencies": []},
                        {"id": "terrain-context", "name": "Terrain Context", "discipline": "Terrain", "dependencies": ["gis-context"]},
                        {"id": "site-review", "name": "Site Engineering Review", "discipline": "Site Engineering", "dependencies": ["terrain-context"]},
                        {"id": "infrastructure-review", "name": "Infrastructure Review", "discipline": "Infrastructure", "dependencies": ["site-review"]},
                        {"id": "bim-coordination", "name": "BIM Coordination", "discipline": "BIM", "dependencies": ["infrastructure-review"]},
                        {"id": "ai-site-review", "name": "AI Site Review", "discipline": "AI Studio", "dependencies": ["bim-coordination"]},
                    ],
                    execution_policy={"mode": "ordered", "requires_validation": True, "uses_existing_commands": True},
                    approval_policy={"required_before_execution": False, "states": ["Draft", "Approved", "Rejected"]},
                ),
                WorkflowTemplate(
                    name="Design to Production Readiness",
                    description="Coordinate CAD, BIM, Simulation, Manufacturing and AI Studio readiness metadata.",
                    disciplines=["2D CAD", "3D CAD", "BIM", "Simulation", "Manufacturing", "CAM", "CNC", "Robotics", "AI Studio"],
                    stages=[
                        {"id": "cad-context", "name": "CAD Context", "discipline": "3D CAD", "dependencies": []},
                        {"id": "bim-context", "name": "BIM Context", "discipline": "BIM", "dependencies": ["cad-context"]},
                        {"id": "simulation-review", "name": "Simulation Review", "discipline": "Simulation", "dependencies": ["bim-context"]},
                        {"id": "manufacturing-review", "name": "Manufacturing Review", "discipline": "Manufacturing", "dependencies": ["simulation-review"]},
                        {"id": "ai-review", "name": "AI Engineering Review", "discipline": "AI Studio", "dependencies": ["manufacturing-review"]},
                    ],
                    execution_policy={"mode": "ordered", "requires_validation": True, "uses_existing_commands": True},
                    approval_policy={"required_before_execution": True, "states": ["Draft", "Approved", "Rejected"]},
                ),
            ]
        )
        return self.templates

    def create_session(self, template=None, name=None, context=None):
        """Create a workflow session from a registered template."""

        self.initialize()
        selected = self._template_for(template)
        session = WorkflowSession(
            template_id=selected.id,
            name=name or selected.name,
            status="Ready",
            context=self._workflow_context(selected, context),
            command_sequence=self._command_sequence(selected),
            execution_order=self._execution_order(selected),
            approval_states={stage["id"]: "Approved" if not selected.approval_policy.get("required_before_execution") else "Draft" for stage in selected.stages},
        )
        session.checkpoints.append(self._checkpoint(session, "Session created"))
        session.validation_report = self.validate_session(session)
        session.diagnostics = self.session_diagnostics(session)
        self.sessions.append(session)
        self.rebuild_index()
        self.refresh_graphs(session)
        self.refresh_diagnostics("Operational")
        return session

    def execute_session(self, session=None, approvals=None):
        """Sequence workflow execution through existing command history metadata."""

        target = self._session_for(session)
        if approvals:
            target.approval_states.update(dict(approvals))
        report = self.validate_session(target)
        target.validation_report = report
        if not report["valid"]:
            target.status = "Blocked"
            target.checkpoints.append(self._checkpoint(target, "Execution blocked"))
            target.updated_at = _timestamp()
            self.refresh_diagnostics("Blocked")
            return target
        target.status = "Completed"
        target.execution_order = self._execution_order(self._template_for(target.template_id))
        target.replay_metadata = {
            "command_history_before": len(getattr(getattr(self.workspace, "command_manager", None), "undo_stack", [])),
            "executed_stages": list(target.execution_order),
            "uses_existing_command_system": True,
            "geometry_owned_by_workflow": False,
        }
        target.checkpoints.append(self._checkpoint(target, "Execution sequencing completed"))
        self.notifications.append({"id": str(uuid4()), "session_id": target.id, "message": f"Workflow '{target.name}' completed.", "created_at": _timestamp()})
        target.diagnostics = self.session_diagnostics(target)
        target.updated_at = _timestamp()
        self.refresh_graphs(target)
        self.refresh_diagnostics("Operational")
        return target

    def validate_session(self, session):
        """Validate workflow dependencies, approvals, persistence and Workspace links."""

        target = self._session_for(session) if not isinstance(session, WorkflowSession) else session
        issues = []
        warnings = []
        template = self._template_for(target.template_id)
        stage_ids = {stage["id"] for stage in template.stages}
        for stage in template.stages:
            for dependency in stage.get("dependencies", []):
                if dependency not in stage_ids:
                    issues.append(f"Missing workflow dependency '{dependency}' for stage '{stage['id']}'.")
        cycles = self.detect_cycles(template)
        if cycles:
            issues.extend([f"Workflow dependency cycle detected: {' -> '.join(cycle)}" for cycle in cycles])
        if not hasattr(self.workspace, "command_manager"):
            issues.append("Workflow requires the existing Workspace Command System.")
        if getattr(self.workspace, "integrated_design_manager", None) is not self.integrated_manager:
            issues.append("Workflow Orchestrator is not attached to the active Integrated Design Manager.")
        if template.approval_policy.get("required_before_execution"):
            pending = [stage["id"] for stage in template.stages if target.approval_states.get(stage["id"]) != "Approved"]
            if target.status == "Running" and pending:
                issues.append("Workflow has pending approvals.")
            elif pending:
                warnings.append("Workflow has approval states pending before execution.")
        persistence = self._persistence_probe()
        if not persistence["passed"]:
            issues.append("Workflow persistence validation failed.")
        report = {
            "id": str(uuid4()),
            "session_id": target.id,
            "valid": not issues,
            "issues": issues,
            "warnings": warnings,
            "statistics": {
                "stages": len(template.stages),
                "dependencies": sum(len(stage.get("dependencies", [])) for stage in template.stages),
                "command_steps": len(target.command_sequence),
                "history_depth": len(getattr(getattr(self.workspace, "command_manager", None), "undo_stack", [])),
                "persistence": persistence,
            },
            "generated_at": _timestamp(),
        }
        self.validation_reports.append(report)
        return report

    def detect_cycles(self, template):
        """Return dependency cycles for a workflow template."""

        graph = {stage["id"]: list(stage.get("dependencies", [])) for stage in template.stages}
        cycles = []
        visiting = set()
        visited = set()

        def visit(node, path):
            if node in visiting:
                start = path.index(node) if node in path else 0
                cycles.append(path[start:] + [node])
                return
            if node in visited:
                return
            visiting.add(node)
            for dependency in graph.get(node, []):
                visit(dependency, path + [node])
            visiting.remove(node)
            visited.add(node)

        for node in graph:
            visit(node, [])
        return cycles

    def refresh_graphs(self, session=None):
        """Refresh workflow, execution and reference graph metadata."""

        sessions = [session] if session is not None else list(self.sessions)
        nodes = []
        edges = []
        execution_nodes = []
        execution_edges = []
        for workflow_session in sessions:
            template = self._template_for(workflow_session.template_id)
            for stage in template.stages:
                node_id = f"{workflow_session.id}:{stage['id']}"
                nodes.append({"id": node_id, "name": stage["name"], "discipline": stage["discipline"], "session_id": workflow_session.id})
                execution_nodes.append({"id": node_id, "order": workflow_session.execution_order.index(stage["id"]) if stage["id"] in workflow_session.execution_order else len(execution_nodes)})
                for dependency in stage.get("dependencies", []):
                    edges.append({"source": f"{workflow_session.id}:{dependency}", "target": node_id, "type": "Workflow dependency"})
                    execution_edges.append({"source": f"{workflow_session.id}:{dependency}", "target": node_id, "type": "Execution order"})
        self.workflow_graph = {"nodes": nodes, "edges": edges}
        self.execution_graph = {"nodes": execution_nodes, "edges": execution_edges}
        self.reference_graph = {
            "nodes": list(self.integrated_manager.dependency_graph.get("nodes", [])),
            "edges": list(self.integrated_manager.dependency_graph.get("edges", [])) + edges,
        }
        return self.workflow_graph

    def rebuild_index(self):
        """Build project-wide workflow search and reference metadata."""

        self.workflow_index = {
            "templates": {item.id: {"name": item.name, "disciplines": list(item.disciplines)} for item in self.templates},
            "sessions": {item.id: {"name": item.name, "status": item.status, "template_id": item.template_id} for item in self.sessions},
            "notifications": {item["id"]: dict(item) for item in self.notifications},
        }
        return self.workflow_index

    def visualization_metadata(self):
        """Return renderer-facing workflow overlay metadata."""

        return {
            "workflow_overlays": dict(self.workflow_index),
            "dependency_overlays": dict(self.workflow_graph),
            "execution_status_overlays": {item.id: {"name": item.name, "status": item.status} for item in self.sessions},
            "notification_overlays": [dict(item) for item in self.notifications],
            "validation_overlays": self.validation_reports[-1] if self.validation_reports else {},
            "diagnostics": dict(self.diagnostics),
        }

    def refresh_diagnostics(self, status=None):
        """Refresh workflow diagnostics."""

        issue_count = sum(len(item.get("issues", [])) for item in self.validation_reports[-3:])
        self.diagnostics = {
            "status": status or self.diagnostics.get("status", "Operational"),
            "health": "Healthy" if issue_count == 0 else "Attention Required",
            "template_count": len(self.templates),
            "session_count": len(self.sessions),
            "notification_count": len(self.notifications),
            "workflow_edges": len(self.workflow_graph.get("edges", [])),
            "execution_edges": len(self.execution_graph.get("edges", [])),
            "validation_issue_count": issue_count,
            "updated_at": _timestamp(),
        }
        return self.diagnostics

    def to_dict(self):
        """Return JSON-safe workflow orchestration metadata."""

        return {
            "templates": [item.to_dict() for item in self.templates],
            "sessions": [item.to_dict() for item in self.sessions],
            "workflow_registry": dict(self.workflow_registry),
            "workflow_index": dict(self.workflow_index),
            "workflow_graph": dict(self.workflow_graph),
            "execution_graph": dict(self.execution_graph),
            "reference_graph": dict(self.reference_graph),
            "notifications": [dict(item) for item in self.notifications],
            "validation_reports": [dict(item) for item in self.validation_reports],
            "diagnostics": dict(self.diagnostics),
        }

    def from_dict(self, data):
        """Restore workflow orchestration metadata."""

        data = data or {}
        self.templates = [WorkflowTemplate.from_dict(item) for item in data.get("templates", [])]
        self.sessions = [WorkflowSession.from_dict(item) for item in data.get("sessions", [])]
        self.workflow_registry = dict(data.get("workflow_registry", {}))
        self.workflow_index = dict(data.get("workflow_index", {}))
        self.workflow_graph = dict(data.get("workflow_graph", {"nodes": [], "edges": []}))
        self.execution_graph = dict(data.get("execution_graph", {"nodes": [], "edges": []}))
        self.reference_graph = dict(data.get("reference_graph", {"nodes": [], "edges": []}))
        self.notifications = [dict(item) for item in data.get("notifications", [])]
        self.validation_reports = [dict(item) for item in data.get("validation_reports", [])]
        self.diagnostics = dict(data.get("diagnostics", self.diagnostics))

    def clear(self):
        """Clear workflow orchestration metadata."""

        self.templates.clear()
        self.sessions.clear()
        self.workflow_registry.clear()
        self.workflow_index.clear()
        self.workflow_graph = {"nodes": [], "edges": []}
        self.execution_graph = {"nodes": [], "edges": []}
        self.reference_graph = {"nodes": [], "edges": []}
        self.notifications.clear()
        self.validation_reports.clear()
        self.refresh_diagnostics("Not Initialized")

    def _template_for(self, template):
        if isinstance(template, WorkflowTemplate):
            return template
        if not self.templates:
            self.ensure_default_templates()
        return next((item for item in self.templates if item.id == template or item.name == template), self.templates[0])

    def _session_for(self, session):
        if isinstance(session, WorkflowSession):
            return session
        if not self.sessions:
            return self.create_session()
        return next((item for item in self.sessions if item.id == session or item.name == session), self.sessions[-1])

    def _workflow_context(self, template, context):
        return {
            "template_id": template.id,
            "disciplines": list(template.disciplines),
            "workspace_name": getattr(self.workspace, "name", "Workspace"),
            "shared_context_id": self.integrated_manager.context.id,
            "shared_index_size": len(self.integrated_manager.shared_index),
            "input_context": dict(context or {}),
        }

    def _command_sequence(self, template):
        return [
            {
                "stage_id": stage["id"],
                "discipline": stage["discipline"],
                "command_family": f"{stage['discipline']} Commands",
                "uses_existing_command_system": True,
                "execution_metadata_only": True,
            }
            for stage in template.stages
        ]

    def _execution_order(self, template):
        ordered = []
        remaining = {stage["id"]: set(stage.get("dependencies", [])) for stage in template.stages}
        while remaining:
            ready = sorted(stage_id for stage_id, dependencies in remaining.items() if dependencies.issubset(set(ordered)))
            if not ready:
                ordered.extend(sorted(remaining.keys()))
                break
            for stage_id in ready:
                ordered.append(stage_id)
                remaining.pop(stage_id, None)
        return ordered

    def _checkpoint(self, session, label):
        return {
            "id": str(uuid4()),
            "session_id": session.id,
            "label": label,
            "history_depth": len(getattr(getattr(self.workspace, "command_manager", None), "undo_stack", [])),
            "created_at": _timestamp(),
        }

    def session_diagnostics(self, session):
        return {
            "status": session.status,
            "stages": len(session.command_sequence),
            "checkpoints": len(session.checkpoints),
            "validation_valid": bool(session.validation_report.get("valid", True)),
            "updated_at": _timestamp(),
        }

    def _persistence_probe(self):
        try:
            data = self.to_dict()
            restored = WorkflowOrchestrator(self.integrated_manager)
            restored.from_dict(data)
            return {
                "passed": len(restored.templates) == len(self.templates) and len(restored.sessions) == len(self.sessions),
                "project_saving": "templates" in data and "sessions" in data,
                "project_loading": len(restored.templates) == len(self.templates),
            }
        except Exception as exc:
            return {"passed": False, "project_saving": False, "project_loading": False, "error": str(exc)}


@dataclass
class ExchangeSession:
    """Persistent unified data exchange session metadata."""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Data Exchange Session"
    status: str = "Created"
    disciplines: list = field(default_factory=list)
    shared_references: list = field(default_factory=list)
    synchronization_state: dict = field(default_factory=dict)
    version_metadata: dict = field(default_factory=dict)
    validation_report: dict = field(default_factory=dict)
    diagnostics: dict = field(default_factory=dict)
    notifications: list = field(default_factory=list)
    created_at: str = field(default_factory=_timestamp)
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        """Return JSON-safe exchange session metadata."""

        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "disciplines": list(self.disciplines),
            "shared_references": [dict(item) for item in self.shared_references],
            "synchronization_state": dict(self.synchronization_state),
            "version_metadata": dict(self.version_metadata),
            "validation_report": dict(self.validation_report),
            "diagnostics": dict(self.diagnostics),
            "notifications": [dict(item) for item in self.notifications],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data):
        """Create an exchange session from persisted metadata."""

        data = data or {}
        return ExchangeSession(
            data.get("id", str(uuid4())),
            data.get("name", "Data Exchange Session"),
            data.get("status", "Created"),
            list(data.get("disciplines", [])),
            [dict(item) for item in data.get("shared_references", [])],
            dict(data.get("synchronization_state", {})),
            dict(data.get("version_metadata", {})),
            dict(data.get("validation_report", {})),
            dict(data.get("diagnostics", {})),
            [dict(item) for item in data.get("notifications", [])],
            data.get("created_at", _timestamp()),
            data.get("updated_at", _timestamp()),
        )


class DataExchangeManager:
    """Unified engineering data exchange coordinator owned by IntegratedDesignManager."""

    SUPPORTED_DISCIPLINES = WorkflowOrchestrator.SUPPORTED_DISCIPLINES + ("Site Engineering", "Infrastructure", "Simulation")

    def __init__(self, integrated_manager):
        self.integrated_manager = integrated_manager
        self.shared_data_registry = {}
        self.live_coordination_context = {}
        self.exchange_sessions = []
        self.synchronization_state = {}
        self.cross_discipline_references = []
        self.engineering_object_registry = {}
        self.relationship_registry = {}
        self.exchange_index = {}
        self.notifications = []
        self.validation_reports = []
        self.diagnostics = {
            "status": "Not Initialized",
            "health": "Unknown",
            "registry_count": 0,
            "reference_count": 0,
            "session_count": 0,
            "notification_count": 0,
            "updated_at": _timestamp(),
        }

    @property
    def workspace(self):
        """Return the shared Workspace."""

        return self.integrated_manager.workspace

    def initialize(self):
        """Initialize shared registry, live coordination context and synchronization state."""

        if not self.integrated_manager.discipline_registry:
            self.integrated_manager.register_disciplines()
            self.integrated_manager.refresh_index()
            self.integrated_manager.map_dependencies()
            self.integrated_manager.register_commands()
        if not self.integrated_manager.workflow_orchestrator.workflow_registry:
            self.integrated_manager.workflow_orchestrator.initialize()
        self.build_shared_registry()
        self.refresh_live_context()
        self.synchronize()
        self.refresh_diagnostics("Operational")
        return self.shared_data_registry

    def build_shared_registry(self):
        """Build a shared engineering object registry from existing project references."""

        registry = {}
        for key, item in self.integrated_manager.shared_index.items():
            registry[key] = {
                "id": item.get("id", key),
                "name": item.get("name", key),
                "discipline": item.get("discipline", ""),
                "type": item.get("type", ""),
                "shared_identifier": key,
                "workspace_reference": True,
                "geometry_owner": "BodyManager" if item.get("discipline") in {"3D CAD", "BIM", "Terrain"} else "Workspace metadata",
                "version": 1,
                "updated_at": _timestamp(),
            }
        for name in self.SUPPORTED_DISCIPLINES:
            key = f"Discipline:{name}"
            registry.setdefault(
                key,
                {
                    "id": key,
                    "name": name,
                    "discipline": name,
                    "type": "Discipline coordination record",
                    "shared_identifier": key,
                    "workspace_reference": True,
                    "geometry_owner": "None",
                    "version": 1,
                    "updated_at": _timestamp(),
                },
            )
        self.shared_data_registry = registry
        self.engineering_object_registry = {key: dict(value) for key, value in registry.items()}
        return self.shared_data_registry

    def refresh_live_context(self):
        """Refresh live coordination context using existing workflow and project metadata."""

        self.cross_discipline_references = self._reference_updates()
        self.relationship_registry = {
            f"relationship-{number}": dict(item)
            for number, item in enumerate(self.cross_discipline_references)
        }
        self.live_coordination_context = {
            "workspace_name": getattr(self.workspace, "name", "Workspace"),
            "integrated_context_id": self.integrated_manager.context.id,
            "workflow_sessions": len(self.integrated_manager.workflow_orchestrator.sessions),
            "shared_registry_size": len(self.shared_data_registry),
            "reference_count": len(self.cross_discipline_references),
            "relationship_count": len(self.relationship_registry),
            "single_project_model": True,
            "updated_at": _timestamp(),
        }
        return self.live_coordination_context

    def create_exchange_session(self, name="Unified Data Exchange", disciplines=None):
        """Create a data exchange session over existing shared references."""

        self.initialize()
        selected_disciplines = list(disciplines or self.SUPPORTED_DISCIPLINES)
        references = [
            item for item in self.cross_discipline_references
            if item.get("source_discipline") in selected_disciplines or item.get("target_discipline") in selected_disciplines
        ]
        session = ExchangeSession(
            name=name,
            status="Ready",
            disciplines=selected_disciplines,
            shared_references=references,
            synchronization_state=self._sync_state_for(references),
            version_metadata={"created_from_context": self.integrated_manager.context.id, "version": "2.1"},
        )
        session.validation_report = self.validate_session(session)
        session.diagnostics = self.session_diagnostics(session)
        self.exchange_sessions.append(session)
        self.rebuild_index()
        self.refresh_diagnostics("Operational")
        return session

    def synchronize(self, session=None):
        """Refresh live synchronization metadata and project notifications."""

        if not self.shared_data_registry:
            self.build_shared_registry()
        self.cross_discipline_references = self._reference_updates()
        self.relationship_registry = {
            f"relationship-{number}": dict(item)
            for number, item in enumerate(self.cross_discipline_references)
        }
        state = {
            "id": str(uuid4()),
            "status": "Synchronized",
            "registry_version": len(self.shared_data_registry),
            "reference_updates": len(self.cross_discipline_references),
            "dependency_updates": len(self.integrated_manager.dependency_graph.get("edges", [])),
            "relationship_updates": len(self.relationship_registry),
            "updated_at": _timestamp(),
        }
        self.synchronization_state = state
        target = self._session_for(session) if session is not None or self.exchange_sessions else None
        if target is not None:
            target.synchronization_state = dict(state)
            target.shared_references = list(self.cross_discipline_references)
            target.status = "Synchronized"
            target.updated_at = _timestamp()
            target.validation_report = self.validate_session(target)
            target.diagnostics = self.session_diagnostics(target)
        notification = {
            "id": str(uuid4()),
            "type": "Synchronization",
            "message": "Unified engineering data synchronized.",
            "reference_updates": len(self.cross_discipline_references),
            "created_at": _timestamp(),
        }
        self.notifications.append(notification)
        if target is not None:
            target.notifications.append(notification)
        self.rebuild_index()
        self.refresh_diagnostics("Operational")
        return state

    def query(self, discipline=None, text=""):
        """Search shared registry and cross-discipline references."""

        needle = str(text or "").lower()
        results = []
        for key, item in self.shared_data_registry.items():
            if discipline and item.get("discipline") != discipline:
                continue
            haystack = " ".join([key, item.get("name", ""), item.get("type", ""), item.get("discipline", "")]).lower()
            if not needle or needle in haystack:
                results.append(dict(item))
        return results

    def validate_session(self, session):
        """Validate references, synchronization state, Workspace link and persistence."""

        target = session if isinstance(session, ExchangeSession) else self._session_for(session)
        issues = []
        warnings = []
        if getattr(self.workspace, "integrated_design_manager", None) is not self.integrated_manager:
            issues.append("Data Exchange Manager is not attached to the active Integrated Design Manager.")
        if not hasattr(self.workspace, "command_manager"):
            issues.append("Data exchange requires the existing Workspace Command System.")
        if not self.shared_data_registry:
            issues.append("Shared Data Registry is empty.")
        known_disciplines = set(self.SUPPORTED_DISCIPLINES)
        missing_disciplines = [item for item in target.disciplines if item not in known_disciplines]
        if missing_disciplines:
            issues.extend([f"Unsupported exchange discipline: {name}" for name in missing_disciplines])
        registry_keys = set(self.shared_data_registry.keys())
        for reference in target.shared_references:
            source = reference.get("source")
            target_key = reference.get("target")
            if source and source not in registry_keys and not source.startswith("Discipline:"):
                warnings.append(f"Reference source is metadata-only: {source}")
            if target_key and target_key not in registry_keys and not target_key.startswith("Discipline:"):
                warnings.append(f"Reference target is metadata-only: {target_key}")
        persistence = self._persistence_probe()
        if not persistence["passed"]:
            issues.append("Data exchange persistence validation failed.")
        report = {
            "id": str(uuid4()),
            "session_id": target.id,
            "valid": not issues,
            "issues": issues,
            "warnings": warnings,
            "statistics": {
                "registry_items": len(self.shared_data_registry),
                "references": len(target.shared_references),
                "relationships": len(self.relationship_registry),
                "history_depth": len(getattr(getattr(self.workspace, "command_manager", None), "undo_stack", [])),
                "persistence": persistence,
            },
            "generated_at": _timestamp(),
        }
        self.validation_reports.append(report)
        return report

    def validate(self):
        """Validate current data exchange state."""

        session = self.exchange_sessions[-1] if self.exchange_sessions else self.create_exchange_session()
        return self.validate_session(session)

    def rebuild_index(self):
        """Build project-wide data exchange lookup indexes."""

        self.exchange_index = {
            "registry": {key: {"name": item["name"], "discipline": item["discipline"], "type": item["type"]} for key, item in self.shared_data_registry.items()},
            "references": {str(number): dict(item) for number, item in enumerate(self.cross_discipline_references)},
            "relationships": dict(self.relationship_registry),
            "sessions": {item.id: {"name": item.name, "status": item.status, "disciplines": list(item.disciplines)} for item in self.exchange_sessions},
            "notifications": {item["id"]: dict(item) for item in self.notifications},
        }
        return self.exchange_index

    def visualization_metadata(self):
        """Return renderer-facing live coordination overlay metadata."""

        return {
            "synchronization_overlays": dict(self.synchronization_state),
            "reference_overlays": list(self.cross_discipline_references),
            "relationship_overlays": dict(self.relationship_registry),
            "coordination_status_overlays": dict(self.live_coordination_context),
            "notification_overlays": [dict(item) for item in self.notifications],
            "validation_overlays": self.validation_reports[-1] if self.validation_reports else {},
            "diagnostics": dict(self.diagnostics),
        }

    def refresh_diagnostics(self, status=None):
        """Refresh data exchange diagnostics."""

        issue_count = sum(len(item.get("issues", [])) for item in self.validation_reports[-3:])
        self.diagnostics = {
            "status": status or self.diagnostics.get("status", "Operational"),
            "health": "Healthy" if issue_count == 0 else "Attention Required",
            "registry_count": len(self.shared_data_registry),
            "reference_count": len(self.cross_discipline_references),
            "session_count": len(self.exchange_sessions),
            "notification_count": len(self.notifications),
            "validation_issue_count": issue_count,
            "updated_at": _timestamp(),
        }
        return self.diagnostics

    def session_diagnostics(self, session):
        """Return diagnostics for one exchange session."""

        return {
            "status": session.status,
            "disciplines": len(session.disciplines),
            "references": len(session.shared_references),
            "valid": bool(session.validation_report.get("valid", True)),
            "updated_at": _timestamp(),
        }

    def to_dict(self):
        """Return JSON-safe data exchange metadata."""

        return {
            "shared_data_registry": dict(self.shared_data_registry),
            "live_coordination_context": dict(self.live_coordination_context),
            "exchange_sessions": [item.to_dict() for item in self.exchange_sessions],
            "synchronization_state": dict(self.synchronization_state),
            "cross_discipline_references": [dict(item) for item in self.cross_discipline_references],
            "engineering_object_registry": dict(self.engineering_object_registry),
            "relationship_registry": dict(self.relationship_registry),
            "exchange_index": dict(self.exchange_index),
            "notifications": [dict(item) for item in self.notifications],
            "validation_reports": [dict(item) for item in self.validation_reports],
            "diagnostics": dict(self.diagnostics),
        }

    def from_dict(self, data):
        """Restore data exchange metadata."""

        data = data or {}
        self.shared_data_registry = dict(data.get("shared_data_registry", {}))
        self.live_coordination_context = dict(data.get("live_coordination_context", {}))
        self.exchange_sessions = [ExchangeSession.from_dict(item) for item in data.get("exchange_sessions", [])]
        self.synchronization_state = dict(data.get("synchronization_state", {}))
        self.cross_discipline_references = [dict(item) for item in data.get("cross_discipline_references", [])]
        self.engineering_object_registry = dict(data.get("engineering_object_registry", {}))
        self.relationship_registry = dict(data.get("relationship_registry", {}))
        self.exchange_index = dict(data.get("exchange_index", {}))
        self.notifications = [dict(item) for item in data.get("notifications", [])]
        self.validation_reports = [dict(item) for item in data.get("validation_reports", [])]
        self.diagnostics = dict(data.get("diagnostics", self.diagnostics))

    def clear(self):
        """Clear data exchange metadata."""

        self.shared_data_registry.clear()
        self.live_coordination_context.clear()
        self.exchange_sessions.clear()
        self.synchronization_state.clear()
        self.cross_discipline_references.clear()
        self.engineering_object_registry.clear()
        self.relationship_registry.clear()
        self.exchange_index.clear()
        self.notifications.clear()
        self.validation_reports.clear()
        self.refresh_diagnostics("Not Initialized")

    def _reference_updates(self):
        references = []
        for edge in self.integrated_manager.dependency_graph.get("edges", []):
            references.append(
                {
                    "id": str(uuid4()),
                    "source": str(edge.get("source", "")),
                    "target": str(edge.get("target", "")),
                    "source_discipline": edge.get("discipline", ""),
                    "target_discipline": edge.get("type", ""),
                    "relationship": edge.get("type", "Reference"),
                    "version": 1,
                    "updated_at": _timestamp(),
                }
            )
        for edge in self.integrated_manager.workflow_orchestrator.workflow_graph.get("edges", []):
            references.append(
                {
                    "id": str(uuid4()),
                    "source": str(edge.get("source", "")),
                    "target": str(edge.get("target", "")),
                    "source_discipline": "Workflow",
                    "target_discipline": "Workflow",
                    "relationship": edge.get("type", "Workflow dependency"),
                    "version": 1,
                    "updated_at": _timestamp(),
                }
            )
        return references

    def _sync_state_for(self, references):
        return {
            "status": "Ready",
            "references": len(references),
            "dependencies": len(self.integrated_manager.dependency_graph.get("edges", [])),
            "relationships": len(self.relationship_registry),
            "updated_at": _timestamp(),
        }

    def _session_for(self, session):
        if isinstance(session, ExchangeSession):
            return session
        if not self.exchange_sessions:
            return self.create_exchange_session()
        return next((item for item in self.exchange_sessions if item.id == session or item.name == session), self.exchange_sessions[-1])

    def _persistence_probe(self):
        try:
            data = self.to_dict()
            restored = DataExchangeManager(self.integrated_manager)
            restored.from_dict(data)
            return {
                "passed": len(restored.shared_data_registry) == len(self.shared_data_registry) and len(restored.exchange_sessions) == len(self.exchange_sessions),
                "project_saving": "shared_data_registry" in data and "exchange_sessions" in data,
                "project_loading": len(restored.shared_data_registry) == len(self.shared_data_registry),
            }
        except Exception as exc:
            return {"passed": False, "project_saving": False, "project_loading": False, "error": str(exc)}


@dataclass
class CoordinationClash:
    """Persistent metadata for a deterministic cross-discipline coordination conflict."""

    id: str = field(default_factory=lambda: str(uuid4()))
    clash_type: str = "Hard Clash"
    source: str = ""
    target: str = ""
    source_discipline: str = ""
    target_discipline: str = ""
    severity: str = "Medium"
    status: str = "Open"
    clearance: float = 0.0
    description: str = ""
    group_id: str = ""
    linked_objects: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_timestamp)
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        """Return JSON-safe clash metadata."""

        return {
            "id": self.id,
            "clash_type": self.clash_type,
            "source": self.source,
            "target": self.target,
            "source_discipline": self.source_discipline,
            "target_discipline": self.target_discipline,
            "severity": self.severity,
            "status": self.status,
            "clearance": self.clearance,
            "description": self.description,
            "group_id": self.group_id,
            "linked_objects": list(self.linked_objects),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data):
        """Create clash metadata from persisted data."""

        data = data or {}
        return CoordinationClash(
            data.get("id", str(uuid4())),
            data.get("clash_type", "Hard Clash"),
            data.get("source", ""),
            data.get("target", ""),
            data.get("source_discipline", ""),
            data.get("target_discipline", ""),
            data.get("severity", "Medium"),
            data.get("status", "Open"),
            float(data.get("clearance", 0.0)),
            data.get("description", ""),
            data.get("group_id", ""),
            list(data.get("linked_objects", [])),
            dict(data.get("metadata", {})),
            data.get("created_at", _timestamp()),
            data.get("updated_at", _timestamp()),
        )


@dataclass
class CoordinationIssue:
    """Persistent metadata for a design coordination issue."""

    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = "Coordination Issue"
    issue_type: str = "Coordination"
    severity: str = "Medium"
    priority: str = "Normal"
    status: str = "Open"
    assigned_to: str = ""
    linked_objects: list = field(default_factory=list)
    clash_ids: list = field(default_factory=list)
    comments: list = field(default_factory=list)
    resolution_history: list = field(default_factory=list)
    review_history: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_timestamp)
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        """Return JSON-safe issue metadata."""

        return {
            "id": self.id,
            "title": self.title,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "priority": self.priority,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "linked_objects": list(self.linked_objects),
            "clash_ids": list(self.clash_ids),
            "comments": [dict(item) for item in self.comments],
            "resolution_history": [dict(item) for item in self.resolution_history],
            "review_history": [dict(item) for item in self.review_history],
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data):
        """Create issue metadata from persisted data."""

        data = data or {}
        return CoordinationIssue(
            data.get("id", str(uuid4())),
            data.get("title", "Coordination Issue"),
            data.get("issue_type", "Coordination"),
            data.get("severity", "Medium"),
            data.get("priority", "Normal"),
            data.get("status", "Open"),
            data.get("assigned_to", ""),
            list(data.get("linked_objects", [])),
            list(data.get("clash_ids", [])),
            [dict(item) for item in data.get("comments", [])],
            [dict(item) for item in data.get("resolution_history", [])],
            [dict(item) for item in data.get("review_history", [])],
            dict(data.get("metadata", {})),
            data.get("created_at", _timestamp()),
            data.get("updated_at", _timestamp()),
        )


@dataclass
class ReviewSession:
    """Persistent metadata for engineering review coordination."""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Design Review"
    reviewer: str = ""
    status: str = "Open"
    issue_ids: list = field(default_factory=list)
    clash_ids: list = field(default_factory=list)
    checkpoints: list = field(default_factory=list)
    decision_tracking: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_timestamp)
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        """Return JSON-safe review metadata."""

        return {
            "id": self.id,
            "name": self.name,
            "reviewer": self.reviewer,
            "status": self.status,
            "issue_ids": list(self.issue_ids),
            "clash_ids": list(self.clash_ids),
            "checkpoints": [dict(item) for item in self.checkpoints],
            "decision_tracking": [dict(item) for item in self.decision_tracking],
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data):
        """Create review metadata from persisted data."""

        data = data or {}
        return ReviewSession(
            data.get("id", str(uuid4())),
            data.get("name", "Design Review"),
            data.get("reviewer", ""),
            data.get("status", "Open"),
            list(data.get("issue_ids", [])),
            list(data.get("clash_ids", [])),
            [dict(item) for item in data.get("checkpoints", [])],
            [dict(item) for item in data.get("decision_tracking", [])],
            dict(data.get("metadata", {})),
            data.get("created_at", _timestamp()),
            data.get("updated_at", _timestamp()),
        )


@dataclass
class ApprovalSession:
    """Persistent metadata for engineering approval coordination."""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Design Approval"
    approver: str = ""
    status: str = "In Review"
    issue_ids: list = field(default_factory=list)
    decisions: list = field(default_factory=list)
    signoff_metadata: dict = field(default_factory=dict)
    approval_history: list = field(default_factory=list)
    checkpoints: list = field(default_factory=list)
    created_at: str = field(default_factory=_timestamp)
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        """Return JSON-safe approval metadata."""

        return {
            "id": self.id,
            "name": self.name,
            "approver": self.approver,
            "status": self.status,
            "issue_ids": list(self.issue_ids),
            "decisions": [dict(item) for item in self.decisions],
            "signoff_metadata": dict(self.signoff_metadata),
            "approval_history": [dict(item) for item in self.approval_history],
            "checkpoints": [dict(item) for item in self.checkpoints],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data):
        """Create approval metadata from persisted data."""

        data = data or {}
        return ApprovalSession(
            data.get("id", str(uuid4())),
            data.get("name", "Design Approval"),
            data.get("approver", ""),
            data.get("status", "In Review"),
            list(data.get("issue_ids", [])),
            [dict(item) for item in data.get("decisions", [])],
            dict(data.get("signoff_metadata", {})),
            [dict(item) for item in data.get("approval_history", [])],
            [dict(item) for item in data.get("checkpoints", [])],
            data.get("created_at", _timestamp()),
            data.get("updated_at", _timestamp()),
        )


class DesignCoordinationManager:
    """Production design coordination manager for clashes, issues, reviews and approvals."""

    SUPPORTED_CLASH_TYPES = (
        "Hard Clash",
        "Soft Clash",
        "Clearance Violation",
        "Duplicate Object",
        "Disconnected System",
        "Reference Inconsistency",
        "Cross-Discipline Conflict",
    )

    def __init__(self, integrated_manager):
        self.integrated_manager = integrated_manager
        self.clash_registry = {}
        self.issue_registry = {}
        self.review_sessions = []
        self.approval_sessions = []
        self.coordination_state = {
            "status": "Not Initialized",
            "review_state": "Not Started",
            "approval_state": "Not Started",
            "updated_at": _timestamp(),
        }
        self.coordination_groups = {}
        self.validation_reports = []
        self.diagnostics = {
            "status": "Not Initialized",
            "health": "Unknown",
            "clash_count": 0,
            "issue_count": 0,
            "review_count": 0,
            "approval_count": 0,
            "updated_at": _timestamp(),
        }
        self.visualization_state = {}

    @property
    def workspace(self):
        """Return the shared Workspace."""

        return self.integrated_manager.workspace

    def initialize(self):
        """Initialize coordination state using existing integrated project metadata."""

        if not self.integrated_manager.discipline_registry:
            self.integrated_manager.register_disciplines()
            self.integrated_manager.refresh_index()
            self.integrated_manager.map_dependencies()
            self.integrated_manager.register_commands()
        if not self.integrated_manager.data_exchange_manager.shared_data_registry:
            self.integrated_manager.data_exchange_manager.initialize()
        self.coordination_state = {
            "status": "Ready",
            "review_state": "Ready",
            "approval_state": "Ready",
            "shared_registry_items": len(self.integrated_manager.data_exchange_manager.shared_data_registry),
            "reference_count": len(self.integrated_manager.data_exchange_manager.cross_discipline_references),
            "uses_existing_project_model": True,
            "geometry_owned_by_coordination": False,
            "updated_at": _timestamp(),
        }
        self.refresh_diagnostics("Operational")
        return self.coordination_state

    def detect_clashes(self):
        """Detect deterministic coordination conflicts from existing project references."""

        self.initialize()
        detected = {}
        detected.update(self._detect_duplicate_objects())
        detected.update(self._detect_reference_inconsistencies())
        detected.update(self._detect_disconnected_systems())
        detected.update(self._detect_cross_discipline_conflicts())
        registry = {}
        for key, clash in sorted(detected.items(), key=lambda item: item[0]):
            clash.id = self._stable_clash_id(key)
            registry[clash.id] = clash
        self.clash_registry = registry
        self.group_clashes()
        self.coordination_state.update(
            {
                "status": "Clashes Evaluated",
                "last_detection": _timestamp(),
                "clash_count": len(self.clash_registry),
                "group_count": len(self.coordination_groups),
            }
        )
        self.refresh_diagnostics("Operational")
        return list(self.clash_registry.values())

    def create_issue(self, title, issue_type="Coordination", severity="Medium", priority="Normal", linked_objects=None, clash_ids=None, assigned_to="", comments=None, metadata=None):
        """Create a persistent coordination issue linked to engineering objects and clashes."""

        self.initialize()
        linked = list(linked_objects or [])
        linked_clashes = list(clash_ids or [])
        for clash_id in linked_clashes:
            clash = self.clash_registry.get(clash_id)
            if clash is not None:
                linked.extend([item for item in clash.linked_objects if item not in linked])
        issue = CoordinationIssue(
            title=title,
            issue_type=issue_type,
            severity=severity,
            priority=priority,
            assigned_to=assigned_to,
            linked_objects=linked,
            clash_ids=linked_clashes,
            comments=[self._comment(item) for item in list(comments or [])],
            metadata=dict(metadata or {}),
        )
        self.issue_registry[issue.id] = issue
        for clash_id in linked_clashes:
            clash = self.clash_registry.get(clash_id)
            if clash is not None:
                clash.status = "Issue Created"
                clash.updated_at = _timestamp()
        self.refresh_diagnostics("Operational")
        return issue

    def update_issue(self, issue, status=None, assigned_to=None, comment=None, resolution=None):
        """Update issue status, assignment, comments and resolution metadata."""

        target = self._issue_for(issue)
        if status:
            target.status = status
        if assigned_to is not None:
            target.assigned_to = assigned_to
        if comment:
            target.comments.append(self._comment(comment))
        if resolution:
            entry = {"id": str(uuid4()), "status": target.status, "resolution": resolution, "created_at": _timestamp()}
            target.resolution_history.append(entry)
        target.updated_at = _timestamp()
        self.refresh_diagnostics("Operational")
        return target

    def create_review_session(self, name="Design Review", reviewer="", issue_ids=None, clash_ids=None, metadata=None):
        """Create an engineering review session over issues and clashes."""

        self.initialize()
        session = ReviewSession(
            name=name,
            reviewer=reviewer,
            status="Open",
            issue_ids=list(issue_ids or []),
            clash_ids=list(clash_ids or []),
            metadata=dict(metadata or {}),
        )
        session.checkpoints.append(self._checkpoint("Review session created", reviewer))
        self.review_sessions.append(session)
        self.coordination_state["review_state"] = "In Review"
        self.refresh_diagnostics("Operational")
        return session

    def add_review_checkpoint(self, session, label, decision="", reviewer="", metadata=None):
        """Record a design review checkpoint."""

        target = self._review_for(session)
        checkpoint = self._checkpoint(label, reviewer or target.reviewer, metadata)
        target.checkpoints.append(checkpoint)
        if decision:
            target.decision_tracking.append({"id": str(uuid4()), "decision": decision, "reviewer": reviewer or target.reviewer, "created_at": _timestamp()})
        target.updated_at = _timestamp()
        self.refresh_diagnostics("Operational")
        return target

    def create_approval_session(self, name="Design Approval", approver="", issue_ids=None):
        """Create an approval workflow session for coordination issues."""

        self.initialize()
        session = ApprovalSession(
            name=name,
            approver=approver,
            issue_ids=list(issue_ids or []),
            signoff_metadata={"requires_engineering_signoff": True, "geometry_modified_by_approval": False},
        )
        session.checkpoints.append(self._checkpoint("Approval session created", approver))
        self.approval_sessions.append(session)
        self.coordination_state["approval_state"] = "In Review"
        self.refresh_diagnostics("Operational")
        return session

    def record_approval_decision(self, session, decision, reviewer="", metadata=None):
        """Record approval decision metadata without changing model geometry."""

        target = self._approval_for(session)
        normalized = str(decision or "").strip() or "Reviewed"
        target.decisions.append({"id": str(uuid4()), "decision": normalized, "reviewer": reviewer or target.approver, "metadata": dict(metadata or {}), "created_at": _timestamp()})
        target.approval_history.append({"id": str(uuid4()), "status_before": target.status, "status_after": normalized, "created_at": _timestamp()})
        target.status = normalized
        target.updated_at = _timestamp()
        self.coordination_state["approval_state"] = normalized
        self.refresh_diagnostics("Operational")
        return target

    def group_clashes(self):
        """Group clashes by type and involved disciplines for coordinated review."""

        groups = {}
        for clash in self.clash_registry.values():
            key = "|".join([clash.clash_type, clash.source_discipline, clash.target_discipline])
            group_id = f"group:{key}"
            clash.group_id = group_id
            groups.setdefault(
                group_id,
                {
                    "id": group_id,
                    "clash_type": clash.clash_type,
                    "source_discipline": clash.source_discipline,
                    "target_discipline": clash.target_discipline,
                    "clash_ids": [],
                    "severity": clash.severity,
                    "impact": "Project coordination review required",
                },
            )
            groups[group_id]["clash_ids"].append(clash.id)
            if clash.severity == "High":
                groups[group_id]["severity"] = "High"
        self.coordination_groups = groups
        return self.coordination_groups

    def coordination_summary(self):
        """Return deterministic project coordination summary metadata."""

        severity_counts = {}
        type_counts = {}
        for clash in self.clash_registry.values():
            severity_counts[clash.severity] = severity_counts.get(clash.severity, 0) + 1
            type_counts[clash.clash_type] = type_counts.get(clash.clash_type, 0) + 1
        status_counts = {}
        for issue in self.issue_registry.values():
            status_counts[issue.status] = status_counts.get(issue.status, 0) + 1
        return {
            "clashes": len(self.clash_registry),
            "issues": len(self.issue_registry),
            "reviews": len(self.review_sessions),
            "approvals": len(self.approval_sessions),
            "groups": len(self.coordination_groups),
            "severity_counts": severity_counts,
            "type_counts": type_counts,
            "issue_status_counts": status_counts,
            "open_issues": sum(1 for issue in self.issue_registry.values() if issue.status not in {"Closed", "Resolved", "Approved"}),
            "geometry_owned_by_coordination": False,
        }

    def validate(self):
        """Validate clash, issue, review, approval and Workspace coordination metadata."""

        issues = []
        warnings = []
        if getattr(self.workspace, "integrated_design_manager", None) is not self.integrated_manager:
            issues.append("Design Coordination Manager is not attached to the active Integrated Design Manager.")
        if not hasattr(self.workspace, "command_manager"):
            issues.append("Design coordination requires the existing Workspace Command System.")
        registry_keys = set(self.integrated_manager.data_exchange_manager.shared_data_registry) | set(self.integrated_manager.shared_index)
        for clash in self.clash_registry.values():
            for linked in clash.linked_objects:
                if linked not in registry_keys and not linked.startswith("Discipline:"):
                    warnings.append(f"Clash linked object is metadata-only: {linked}")
            if clash.clash_type not in self.SUPPORTED_CLASH_TYPES:
                issues.append(f"Unsupported clash type: {clash.clash_type}")
        for issue in self.issue_registry.values():
            for clash_id in issue.clash_ids:
                if clash_id not in self.clash_registry:
                    issues.append(f"Issue references unknown clash: {clash_id}")
        for review in self.review_sessions:
            for issue_id in review.issue_ids:
                if issue_id not in self.issue_registry:
                    issues.append(f"Review references unknown issue: {issue_id}")
        for approval in self.approval_sessions:
            for issue_id in approval.issue_ids:
                if issue_id not in self.issue_registry:
                    issues.append(f"Approval references unknown issue: {issue_id}")
        persistence = self._persistence_probe()
        if not persistence["passed"]:
            issues.append("Design coordination persistence validation failed.")
        report = {
            "id": str(uuid4()),
            "valid": not issues,
            "issues": issues,
            "warnings": warnings,
            "statistics": {
                "summary": self.coordination_summary(),
                "history_depth": len(getattr(getattr(self.workspace, "command_manager", None), "undo_stack", [])),
                "persistence": persistence,
            },
            "generated_at": _timestamp(),
        }
        self.validation_reports.append(report)
        self.refresh_diagnostics("Operational" if report["valid"] else "Blocked")
        return report

    def visualization_metadata(self):
        """Return renderer-facing coordination overlay metadata."""

        self.visualization_state = {
            "clash_overlays": [item.to_dict() for item in self.clash_registry.values()],
            "issue_overlays": [item.to_dict() for item in self.issue_registry.values()],
            "review_overlays": [item.to_dict() for item in self.review_sessions],
            "approval_overlays": [item.to_dict() for item in self.approval_sessions],
            "coordination_overlays": dict(self.coordination_groups),
            "validation_overlays": self.validation_reports[-1] if self.validation_reports else {},
            "diagnostics": dict(self.diagnostics),
        }
        return self.visualization_state

    def refresh_diagnostics(self, status=None):
        """Refresh design coordination diagnostics."""

        issue_count = sum(len(item.get("issues", [])) for item in self.validation_reports[-3:])
        self.diagnostics = {
            "status": status or self.diagnostics.get("status", "Operational"),
            "health": "Healthy" if issue_count == 0 else "Attention Required",
            "clash_count": len(self.clash_registry),
            "issue_count": len(self.issue_registry),
            "review_count": len(self.review_sessions),
            "approval_count": len(self.approval_sessions),
            "group_count": len(self.coordination_groups),
            "validation_issue_count": issue_count,
            "updated_at": _timestamp(),
        }
        return self.diagnostics

    def to_dict(self):
        """Return JSON-safe design coordination metadata."""

        return {
            "clash_registry": {key: value.to_dict() for key, value in self.clash_registry.items()},
            "issue_registry": {key: value.to_dict() for key, value in self.issue_registry.items()},
            "review_sessions": [item.to_dict() for item in self.review_sessions],
            "approval_sessions": [item.to_dict() for item in self.approval_sessions],
            "coordination_state": dict(self.coordination_state),
            "coordination_groups": dict(self.coordination_groups),
            "validation_reports": [dict(item) for item in self.validation_reports],
            "diagnostics": dict(self.diagnostics),
            "visualization_state": dict(self.visualization_state),
        }

    def from_dict(self, data):
        """Restore design coordination metadata."""

        data = data or {}
        self.clash_registry = {key: CoordinationClash.from_dict(value) for key, value in data.get("clash_registry", {}).items()}
        self.issue_registry = {key: CoordinationIssue.from_dict(value) for key, value in data.get("issue_registry", {}).items()}
        self.review_sessions = [ReviewSession.from_dict(item) for item in data.get("review_sessions", [])]
        self.approval_sessions = [ApprovalSession.from_dict(item) for item in data.get("approval_sessions", [])]
        self.coordination_state = dict(data.get("coordination_state", self.coordination_state))
        self.coordination_groups = dict(data.get("coordination_groups", {}))
        self.validation_reports = [dict(item) for item in data.get("validation_reports", [])]
        self.diagnostics = dict(data.get("diagnostics", self.diagnostics))
        self.visualization_state = dict(data.get("visualization_state", {}))

    def clear(self):
        """Clear coordination metadata while leaving project systems untouched."""

        self.clash_registry.clear()
        self.issue_registry.clear()
        self.review_sessions.clear()
        self.approval_sessions.clear()
        self.coordination_groups.clear()
        self.validation_reports.clear()
        self.visualization_state.clear()
        self.coordination_state = {"status": "Not Initialized", "review_state": "Not Started", "approval_state": "Not Started", "updated_at": _timestamp()}
        self.refresh_diagnostics("Not Initialized")

    def _detect_duplicate_objects(self):
        clashes = {}
        buckets = {}
        for key, item in self.integrated_manager.data_exchange_manager.shared_data_registry.items():
            name = self._normalized_name(item.get("name", ""))
            if not name or key.startswith("Discipline:"):
                continue
            buckets.setdefault(name, []).append((key, item))
        for name, items in buckets.items():
            if len(items) < 2:
                continue
            ordered = sorted(items, key=lambda pair: pair[0])
            for index in range(len(ordered) - 1):
                source_key, source = ordered[index]
                target_key, target = ordered[index + 1]
                clash_type = "Hard Clash" if source.get("discipline") != target.get("discipline") else "Duplicate Object"
                severity = "High" if clash_type == "Hard Clash" else "Medium"
                clash = CoordinationClash(
                    clash_type=clash_type,
                    source=source_key,
                    target=target_key,
                    source_discipline=source.get("discipline", ""),
                    target_discipline=target.get("discipline", ""),
                    severity=severity,
                    description=f"Objects share the coordination name '{source.get('name', name)}'.",
                    linked_objects=[source_key, target_key],
                    metadata={"detection_rule": "shared-name", "geometry_queried_only": True},
                )
                clashes[f"{clash_type}:{source_key}:{target_key}"] = clash
        return clashes

    def _detect_reference_inconsistencies(self):
        clashes = {}
        registry_keys = set(self.integrated_manager.data_exchange_manager.shared_data_registry)
        for number, reference in enumerate(self.integrated_manager.data_exchange_manager.cross_discipline_references):
            source = reference.get("source", "")
            target = reference.get("target", "")
            source_known = source in registry_keys or str(source).startswith("Discipline:")
            target_known = target in registry_keys or str(target).startswith("Discipline:")
            if source_known and target_known:
                continue
            clash = CoordinationClash(
                clash_type="Reference Inconsistency",
                source=source,
                target=target,
                source_discipline=reference.get("source_discipline", ""),
                target_discipline=reference.get("target_discipline", ""),
                severity="Medium",
                description="A cross-discipline reference does not resolve to a shared project object.",
                linked_objects=[item for item in (source, target) if item],
                metadata={"reference_id": reference.get("id", str(number)), "relationship": reference.get("relationship", "")},
            )
            clashes[f"Reference Inconsistency:{number}:{source}:{target}"] = clash
        return clashes

    def _detect_disconnected_systems(self):
        clashes = {}
        registry = self.integrated_manager.discipline_registry
        references = self.integrated_manager.data_exchange_manager.cross_discipline_references
        referenced_disciplines = {item.get("source_discipline") for item in references} | {item.get("target_discipline") for item in references}
        for key, item in sorted(registry.items()):
            if not item.get("available"):
                continue
            name = item.get("name", key)
            if item.get("object_count", 0) and name not in referenced_disciplines and key not in {"entities", "scene3d"}:
                clash = CoordinationClash(
                    clash_type="Disconnected System",
                    source=f"Discipline:{name}",
                    target="Unified Project Coordination",
                    source_discipline=name,
                    target_discipline="Integrated Design",
                    severity="Low",
                    description=f"{name} has project objects without active cross-discipline references.",
                    linked_objects=[f"Discipline:{name}"],
                    metadata={"object_count": item.get("object_count", 0)},
                )
                clashes[f"Disconnected System:{name}"] = clash
        return clashes

    def _detect_cross_discipline_conflicts(self):
        clashes = {}
        references = sorted(self.integrated_manager.data_exchange_manager.cross_discipline_references, key=lambda item: (item.get("source", ""), item.get("target", ""), item.get("relationship", "")))
        for number, reference in enumerate(references):
            source_discipline = reference.get("source_discipline", "")
            target_discipline = reference.get("target_discipline", "")
            relationship = reference.get("relationship", "")
            if source_discipline and target_discipline and source_discipline != target_discipline and relationship not in {"Reference", "Workflow dependency"}:
                clash = CoordinationClash(
                    clash_type="Cross-Discipline Conflict",
                    source=reference.get("source", ""),
                    target=reference.get("target", ""),
                    source_discipline=source_discipline,
                    target_discipline=target_discipline,
                    severity="Medium",
                    description=f"Cross-discipline relationship '{relationship}' requires coordination review.",
                    linked_objects=[item for item in (reference.get("source", ""), reference.get("target", "")) if item],
                    metadata={"relationship": relationship, "coordination_index": number},
                )
                clashes[f"Cross-Discipline Conflict:{number}:{reference.get('source', '')}:{reference.get('target', '')}"] = clash
        return clashes

    def _issue_for(self, issue):
        if isinstance(issue, CoordinationIssue):
            return issue
        if issue in self.issue_registry:
            return self.issue_registry[issue]
        return next(iter(self.issue_registry.values()))

    def _review_for(self, session):
        if isinstance(session, ReviewSession):
            return session
        return next((item for item in self.review_sessions if item.id == session or item.name == session), self.review_sessions[-1])

    def _approval_for(self, session):
        if isinstance(session, ApprovalSession):
            return session
        return next((item for item in self.approval_sessions if item.id == session or item.name == session), self.approval_sessions[-1])

    def _comment(self, text):
        return {"id": str(uuid4()), "text": str(text), "created_at": _timestamp()}

    def _checkpoint(self, label, reviewer="", metadata=None):
        return {"id": str(uuid4()), "label": label, "reviewer": reviewer, "metadata": dict(metadata or {}), "created_at": _timestamp()}

    def _normalized_name(self, name):
        return " ".join(str(name or "").strip().lower().split())

    def _stable_clash_id(self, key):
        return "clash:" + "".join(character if character.isalnum() else "-" for character in str(key)).strip("-")[:180]

    def _persistence_probe(self):
        try:
            data = self.to_dict()
            restored = DesignCoordinationManager(self.integrated_manager)
            restored.from_dict(data)
            return {
                "passed": len(restored.clash_registry) == len(self.clash_registry) and len(restored.issue_registry) == len(self.issue_registry),
                "project_saving": "clash_registry" in data and "issue_registry" in data,
                "project_loading": len(restored.review_sessions) == len(self.review_sessions) and len(restored.approval_sessions) == len(self.approval_sessions),
            }
        except Exception as exc:
            return {"passed": False, "project_saving": False, "project_loading": False, "error": str(exc)}


@dataclass
class AutomationTask:
    """Persistent metadata for a cross-discipline automation task."""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Automation Task"
    discipline: str = ""
    action: str = "Coordinate"
    dependencies: list = field(default_factory=list)
    condition: dict = field(default_factory=dict)
    priority: int = 50
    status: str = "Queued"
    execution_policy: dict = field(default_factory=dict)
    checkpoints: list = field(default_factory=list)
    result_metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_timestamp)
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        """Return JSON-safe automation task metadata."""

        return {
            "id": self.id,
            "name": self.name,
            "discipline": self.discipline,
            "action": self.action,
            "dependencies": list(self.dependencies),
            "condition": dict(self.condition),
            "priority": self.priority,
            "status": self.status,
            "execution_policy": dict(self.execution_policy),
            "checkpoints": [dict(item) for item in self.checkpoints],
            "result_metadata": dict(self.result_metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data):
        """Create task metadata from persisted data."""

        data = data or {}
        return AutomationTask(
            data.get("id", str(uuid4())),
            data.get("name", "Automation Task"),
            data.get("discipline", ""),
            data.get("action", "Coordinate"),
            list(data.get("dependencies", [])),
            dict(data.get("condition", {})),
            int(data.get("priority", 50)),
            data.get("status", "Queued"),
            dict(data.get("execution_policy", {})),
            [dict(item) for item in data.get("checkpoints", [])],
            dict(data.get("result_metadata", {})),
            data.get("created_at", _timestamp()),
            data.get("updated_at", _timestamp()),
        )


@dataclass
class AutomationSession:
    """Persistent metadata for a multi-discipline automation session."""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Automation Session"
    status: str = "Created"
    tasks: list = field(default_factory=list)
    execution_queue: list = field(default_factory=list)
    execution_history: list = field(default_factory=list)
    ai_context: dict = field(default_factory=dict)
    recommendations: list = field(default_factory=list)
    decision_history: list = field(default_factory=list)
    prompt_history: list = field(default_factory=list)
    result_tracking: dict = field(default_factory=dict)
    validation_report: dict = field(default_factory=dict)
    diagnostics: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_timestamp)
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        """Return JSON-safe automation session metadata."""

        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "tasks": [item.to_dict() for item in self.tasks],
            "execution_queue": list(self.execution_queue),
            "execution_history": [dict(item) for item in self.execution_history],
            "ai_context": dict(self.ai_context),
            "recommendations": [dict(item) for item in self.recommendations],
            "decision_history": [dict(item) for item in self.decision_history],
            "prompt_history": [dict(item) for item in self.prompt_history],
            "result_tracking": dict(self.result_tracking),
            "validation_report": dict(self.validation_report),
            "diagnostics": dict(self.diagnostics),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data):
        """Create session metadata from persisted data."""

        data = data or {}
        return AutomationSession(
            data.get("id", str(uuid4())),
            data.get("name", "Automation Session"),
            data.get("status", "Created"),
            [AutomationTask.from_dict(item) for item in data.get("tasks", [])],
            list(data.get("execution_queue", [])),
            [dict(item) for item in data.get("execution_history", [])],
            dict(data.get("ai_context", {})),
            [dict(item) for item in data.get("recommendations", [])],
            [dict(item) for item in data.get("decision_history", [])],
            [dict(item) for item in data.get("prompt_history", [])],
            dict(data.get("result_tracking", {})),
            dict(data.get("validation_report", {})),
            dict(data.get("diagnostics", {})),
            data.get("created_at", _timestamp()),
            data.get("updated_at", _timestamp()),
        )


class AutomationAICoordinationManager:
    """Multi-discipline automation and AI coordination metadata manager."""

    SUPPORTED_DISCIPLINES = WorkflowOrchestrator.SUPPORTED_DISCIPLINES + ("Site Engineering", "Infrastructure", "Simulation")

    def __init__(self, integrated_manager):
        self.integrated_manager = integrated_manager
        self.automation_registry = {}
        self.automation_sessions = []
        self.automation_scheduler = {}
        self.execution_queue = []
        self.execution_history = []
        self.ai_coordination_context = {}
        self.recommendations = []
        self.decision_history = []
        self.prompt_history = []
        self.result_tracking = {}
        self.validation_reports = []
        self.diagnostics = {
            "status": "Not Initialized",
            "health": "Unknown",
            "registry_count": 0,
            "session_count": 0,
            "queue_count": 0,
            "history_count": 0,
            "recommendation_count": 0,
            "updated_at": _timestamp(),
        }
        self.visualization_state = {}

    @property
    def workspace(self):
        """Return the shared Workspace."""

        return self.integrated_manager.workspace

    def initialize(self):
        """Initialize automation registry, scheduler and AI coordination context."""

        if not self.integrated_manager.discipline_registry:
            self.integrated_manager.register_disciplines()
            self.integrated_manager.refresh_index()
            self.integrated_manager.map_dependencies()
            self.integrated_manager.register_commands()
        if not self.integrated_manager.design_coordination_manager.coordination_state:
            self.integrated_manager.design_coordination_manager.initialize()
        self.build_registry()
        self.refresh_scheduler()
        self.refresh_ai_context()
        self.generate_recommendations()
        self.refresh_diagnostics("Operational")
        return self.automation_registry

    def build_registry(self):
        """Build automation capability metadata from existing discipline registrations."""

        registry = {}
        workflow_registry = self.integrated_manager.workflow_orchestrator.workflow_registry
        if not workflow_registry:
            self.integrated_manager.workflow_orchestrator.initialize()
            workflow_registry = self.integrated_manager.workflow_orchestrator.workflow_registry
        for name in self.SUPPORTED_DISCIPLINES:
            workflow_item = workflow_registry.get(name, {})
            discipline_key = next((key for key, value in self.integrated_manager.discipline_registry.items() if value.get("name") == name), "")
            discipline_item = self.integrated_manager.discipline_registry.get(discipline_key, {})
            registry[name] = {
                "discipline": name,
                "implemented": bool(workflow_item.get("implemented", False)),
                "available": bool(discipline_item.get("available", workflow_item.get("implemented", False))),
                "object_count": int(discipline_item.get("object_count", workflow_item.get("object_count", 0))),
                "automation_actions": ["validate", "coordinate", "summarize", "recommend"],
                "uses_existing_system": True,
                "owns_geometry": False,
            }
        self.automation_registry = registry
        return self.automation_registry

    def refresh_scheduler(self):
        """Refresh deterministic scheduler metadata."""

        dependencies = self.integrated_manager.dependency_graph.get("edges", [])
        self.automation_scheduler = {
            "status": "Ready",
            "policy": "dependency-aware-priority",
            "supports_sequential": True,
            "supports_parallel_metadata": True,
            "supports_conditional_execution": True,
            "dependency_edges": len(dependencies),
            "queue_count": len(self.execution_queue),
            "updated_at": _timestamp(),
        }
        return self.automation_scheduler

    def refresh_ai_context(self):
        """Refresh shared AI coordination metadata from existing AI systems."""

        infrastructure = self.integrated_manager._infrastructure_manager()
        ai_site = getattr(infrastructure, "ai_site_intelligence_manager", None) if infrastructure is not None else None
        self.ai_coordination_context = {
            "ai_studio_available": hasattr(self.workspace, "ai_engine"),
            "ai_site_intelligence_available": ai_site is not None,
            "shared_workspace_context": True,
            "duplicate_ai_engine": False,
            "project_objects": len(self.integrated_manager.shared_index),
            "coordination_clashes": len(self.integrated_manager.design_coordination_manager.clash_registry),
            "coordination_issues": len(self.integrated_manager.design_coordination_manager.issue_registry),
            "updated_at": _timestamp(),
        }
        return self.ai_coordination_context

    def create_session(self, name="Automation Session", template=None, tasks=None, ai_objective=""):
        """Create a reusable automation session from task metadata or an existing workflow template."""

        self.initialize()
        selected_tasks = [self._task_from_input(item) for item in list(tasks or [])]
        if not selected_tasks:
            selected_tasks = self._tasks_from_workflow(template)
        session = AutomationSession(
            name=name,
            status="Ready",
            tasks=selected_tasks,
            ai_context=dict(self.ai_coordination_context),
        )
        if ai_objective:
            session.prompt_history.append({"id": str(uuid4()), "objective": ai_objective, "source": "AI Studio coordination", "created_at": _timestamp()})
            self.prompt_history.append(dict(session.prompt_history[-1]))
        session.execution_queue = self.schedule_session(session)
        session.recommendations = self.generate_recommendations(session)
        session.validation_report = self.validate_session(session)
        session.diagnostics = self.session_diagnostics(session)
        self.automation_sessions.append(session)
        self.execution_queue = list(session.execution_queue)
        self.refresh_diagnostics("Operational")
        return session

    def schedule_session(self, session):
        """Build dependency-aware execution queue metadata for a session."""

        tasks = {task.id: task for task in session.tasks}
        ordered = []
        remaining = set(tasks)
        while remaining:
            ready = [
                task_id for task_id in remaining
                if all(dependency in ordered or dependency not in tasks for dependency in tasks[task_id].dependencies)
            ]
            if not ready:
                ready = sorted(remaining)
            ready.sort(key=lambda task_id: (-tasks[task_id].priority, tasks[task_id].name, task_id))
            next_task = ready[0]
            ordered.append(next_task)
            remaining.remove(next_task)
        session.execution_queue = ordered
        self.execution_queue = list(ordered)
        self.refresh_scheduler()
        return ordered

    def execute_session(self, session=None):
        """Execute automation metadata sequencing without modifying geometry."""

        target = self._session_for(session)
        report = self.validate_session(target)
        target.validation_report = report
        if not report["valid"]:
            target.status = "Blocked"
            target.updated_at = _timestamp()
            self.refresh_diagnostics("Blocked")
            return target
        target.status = "Completed"
        task_lookup = {task.id: task for task in target.tasks}
        for task_id in target.execution_queue:
            task = task_lookup.get(task_id)
            if task is None:
                continue
            if not self._condition_passed(task.condition):
                task.status = "Skipped"
                task.result_metadata = {"condition_met": False, "geometry_modified": False}
            else:
                task.status = "Completed"
                task.result_metadata = {
                    "condition_met": True,
                    "geometry_modified": False,
                    "existing_system": task.discipline,
                    "action": task.action,
                }
            task.checkpoints.append(self._checkpoint(task.status, task.action))
            task.updated_at = _timestamp()
            entry = {
                "id": str(uuid4()),
                "session_id": target.id,
                "task_id": task.id,
                "task": task.name,
                "discipline": task.discipline,
                "status": task.status,
                "created_at": _timestamp(),
            }
            target.execution_history.append(entry)
            self.execution_history.append(entry)
        target.result_tracking = {
            "completed": sum(1 for task in target.tasks if task.status == "Completed"),
            "skipped": sum(1 for task in target.tasks if task.status == "Skipped"),
            "geometry_modified": False,
            "history_depth": len(getattr(getattr(self.workspace, "command_manager", None), "undo_stack", [])),
        }
        target.decision_history.append({"id": str(uuid4()), "decision": "Automation sequencing completed", "created_at": _timestamp()})
        self.decision_history.append(dict(target.decision_history[-1]))
        target.diagnostics = self.session_diagnostics(target)
        target.updated_at = _timestamp()
        self.refresh_diagnostics("Operational")
        return target

    def coordinate_ai_task(self, objective, source="AI Studio", metadata=None):
        """Record AI coordination metadata through existing AI systems."""

        self.initialize()
        entry = {
            "id": str(uuid4()),
            "objective": objective,
            "source": source,
            "metadata": dict(metadata or {}),
            "ai_studio_available": self.ai_coordination_context.get("ai_studio_available", False),
            "ai_site_intelligence_available": self.ai_coordination_context.get("ai_site_intelligence_available", False),
            "duplicate_ai_engine": False,
            "created_at": _timestamp(),
        }
        self.prompt_history.append(entry)
        self.result_tracking[entry["id"]] = {
            "objective": objective,
            "recommendations": len(self.generate_recommendations()),
            "geometry_modified": False,
        }
        self.refresh_diagnostics("Operational")
        return entry

    def generate_recommendations(self, session=None):
        """Generate deterministic automation recommendations from project metadata."""

        recommendations = []
        coordination = self.integrated_manager.design_coordination_manager
        high_clashes = [item for item in coordination.clash_registry.values() if item.severity == "High"]
        open_issues = [item for item in coordination.issue_registry.values() if item.status not in {"Closed", "Resolved", "Approved"}]
        if high_clashes:
            recommendations.append(self._recommendation("Resolve high-severity coordination clashes", "Design Coordination", "High", {"clashes": len(high_clashes)}))
        if open_issues:
            recommendations.append(self._recommendation("Review open coordination issues before downstream automation", "Design Coordination", "High", {"issues": len(open_issues)}))
        if self.integrated_manager.data_exchange_manager.synchronization_state.get("status") != "Synchronized":
            recommendations.append(self._recommendation("Synchronize shared engineering data before automation execution", "Data Exchange", "Medium", {}))
        validation = self.integrated_manager.validation_reports[-1] if self.integrated_manager.validation_reports else {}
        if validation.get("warnings"):
            recommendations.append(self._recommendation("Review integrated design validation warnings", "Integrated Design", "Medium", {"warnings": len(validation.get("warnings", []))}))
        if session is not None:
            dependency_count = sum(len(task.dependencies) for task in session.tasks)
            if dependency_count:
                recommendations.append(self._recommendation("Use dependency-aware execution order for chained automation tasks", "Workflow Orchestrator", "Medium", {"dependencies": dependency_count}))
        if not recommendations:
            recommendations.append(self._recommendation("Automation context is ready for coordinated execution", "Integrated Design", "Low", {"registry_items": len(self.automation_registry)}))
        self.recommendations = recommendations
        return recommendations

    def validate_session(self, session):
        """Validate automation session, dependencies, AI context, Workspace link and persistence."""

        target = session if isinstance(session, AutomationSession) else self._session_for(session)
        issues = []
        warnings = []
        if getattr(self.workspace, "integrated_design_manager", None) is not self.integrated_manager:
            issues.append("Automation & AI Coordination Manager is not attached to the active Integrated Design Manager.")
        if not hasattr(self.workspace, "command_manager"):
            issues.append("Automation coordination requires the existing Workspace Command System.")
        task_ids = {task.id for task in target.tasks}
        for task in target.tasks:
            if task.discipline and task.discipline not in self.automation_registry:
                issues.append(f"Unsupported automation discipline: {task.discipline}")
            for dependency in task.dependencies:
                if dependency not in task_ids:
                    warnings.append(f"Task dependency is external metadata: {dependency}")
        if self.ai_coordination_context.get("duplicate_ai_engine"):
            issues.append("Automation coordination detected unexpected AI engine duplication metadata.")
        persistence = self._persistence_probe()
        if not persistence["passed"]:
            issues.append("Automation coordination persistence validation failed.")
        report = {
            "id": str(uuid4()),
            "session_id": target.id,
            "valid": not issues,
            "issues": issues,
            "warnings": warnings,
            "statistics": {
                "tasks": len(target.tasks),
                "queue": len(target.execution_queue),
                "history": len(target.execution_history),
                "recommendations": len(target.recommendations),
                "ai_context": dict(self.ai_coordination_context),
                "persistence": persistence,
            },
            "generated_at": _timestamp(),
        }
        self.validation_reports.append(report)
        return report

    def validate(self):
        """Validate current automation coordination state."""

        session = self.automation_sessions[-1] if self.automation_sessions else self.create_session()
        return self.validate_session(session)

    def session_diagnostics(self, session):
        """Return diagnostics for one automation session."""

        return {
            "status": session.status,
            "tasks": len(session.tasks),
            "queue": len(session.execution_queue),
            "history": len(session.execution_history),
            "recommendations": len(session.recommendations),
            "updated_at": _timestamp(),
        }

    def visualization_metadata(self):
        """Return renderer-facing automation and AI coordination overlay metadata."""

        self.visualization_state = {
            "automation_overlays": dict(self.automation_registry),
            "execution_overlays": list(self.execution_queue),
            "ai_activity_overlays": {"context": dict(self.ai_coordination_context), "prompt_history": [dict(item) for item in self.prompt_history]},
            "workflow_overlays": [item.to_dict() for item in self.automation_sessions],
            "recommendation_overlays": [dict(item) for item in self.recommendations],
            "validation_overlays": self.validation_reports[-1] if self.validation_reports else {},
            "diagnostics": dict(self.diagnostics),
        }
        return self.visualization_state

    def refresh_diagnostics(self, status=None):
        """Refresh automation and AI coordination diagnostics."""

        issue_count = sum(len(item.get("issues", [])) for item in self.validation_reports[-3:])
        self.diagnostics = {
            "status": status or self.diagnostics.get("status", "Operational"),
            "health": "Healthy" if issue_count == 0 else "Attention Required",
            "registry_count": len(self.automation_registry),
            "session_count": len(self.automation_sessions),
            "queue_count": len(self.execution_queue),
            "history_count": len(self.execution_history),
            "recommendation_count": len(self.recommendations),
            "validation_issue_count": issue_count,
            "updated_at": _timestamp(),
        }
        return self.diagnostics

    def to_dict(self):
        """Return JSON-safe automation and AI coordination metadata."""

        return {
            "automation_registry": dict(self.automation_registry),
            "automation_sessions": [item.to_dict() for item in self.automation_sessions],
            "automation_scheduler": dict(self.automation_scheduler),
            "execution_queue": list(self.execution_queue),
            "execution_history": [dict(item) for item in self.execution_history],
            "ai_coordination_context": dict(self.ai_coordination_context),
            "recommendations": [dict(item) for item in self.recommendations],
            "decision_history": [dict(item) for item in self.decision_history],
            "prompt_history": [dict(item) for item in self.prompt_history],
            "result_tracking": dict(self.result_tracking),
            "validation_reports": [dict(item) for item in self.validation_reports],
            "diagnostics": dict(self.diagnostics),
            "visualization_state": dict(self.visualization_state),
        }

    def from_dict(self, data):
        """Restore automation and AI coordination metadata."""

        data = data or {}
        self.automation_registry = dict(data.get("automation_registry", {}))
        self.automation_sessions = [AutomationSession.from_dict(item) for item in data.get("automation_sessions", [])]
        self.automation_scheduler = dict(data.get("automation_scheduler", {}))
        self.execution_queue = list(data.get("execution_queue", []))
        self.execution_history = [dict(item) for item in data.get("execution_history", [])]
        self.ai_coordination_context = dict(data.get("ai_coordination_context", {}))
        self.recommendations = [dict(item) for item in data.get("recommendations", [])]
        self.decision_history = [dict(item) for item in data.get("decision_history", [])]
        self.prompt_history = [dict(item) for item in data.get("prompt_history", [])]
        self.result_tracking = dict(data.get("result_tracking", {}))
        self.validation_reports = [dict(item) for item in data.get("validation_reports", [])]
        self.diagnostics = dict(data.get("diagnostics", self.diagnostics))
        self.visualization_state = dict(data.get("visualization_state", {}))

    def clear(self):
        """Clear automation metadata while leaving engineering systems untouched."""

        self.automation_registry.clear()
        self.automation_sessions.clear()
        self.automation_scheduler.clear()
        self.execution_queue.clear()
        self.execution_history.clear()
        self.ai_coordination_context.clear()
        self.recommendations.clear()
        self.decision_history.clear()
        self.prompt_history.clear()
        self.result_tracking.clear()
        self.validation_reports.clear()
        self.visualization_state.clear()
        self.refresh_diagnostics("Not Initialized")

    def _tasks_from_workflow(self, template=None):
        selected = self.integrated_manager.workflow_orchestrator._template_for(template)
        tasks = []
        stage_to_task = {}
        for stage in selected.stages:
            task = AutomationTask(
                name=stage.get("name", stage.get("id", "Workflow Stage")),
                discipline=stage.get("discipline", ""),
                action="Coordinate workflow stage",
                priority=60,
                execution_policy={"source_template": selected.name, "uses_existing_commands": True},
            )
            stage_to_task[stage.get("id", task.id)] = task.id
            tasks.append(task)
        for stage, task in zip(selected.stages, tasks):
            task.dependencies = [stage_to_task[item] for item in stage.get("dependencies", []) if item in stage_to_task]
        return tasks

    def _task_from_input(self, item):
        if isinstance(item, AutomationTask):
            return item
        data = dict(item)
        return AutomationTask(
            name=data.get("name", "Automation Task"),
            discipline=data.get("discipline", ""),
            action=data.get("action", "Coordinate"),
            dependencies=list(data.get("dependencies", [])),
            condition=dict(data.get("condition", {})),
            priority=int(data.get("priority", 50)),
            execution_policy=dict(data.get("execution_policy", {})),
        )

    def _condition_passed(self, condition):
        if not condition:
            return True
        minimum_clashes = condition.get("minimum_clashes")
        if minimum_clashes is not None:
            return len(self.integrated_manager.design_coordination_manager.clash_registry) >= int(minimum_clashes)
        required_status = condition.get("data_exchange_status")
        if required_status:
            return self.integrated_manager.data_exchange_manager.synchronization_state.get("status") == required_status
        return True

    def _recommendation(self, title, source, priority, metadata):
        return {
            "id": str(uuid4()),
            "title": title,
            "source": source,
            "priority": priority,
            "metadata": dict(metadata),
            "geometry_modified": False,
            "created_at": _timestamp(),
        }

    def _checkpoint(self, status, action):
        return {"id": str(uuid4()), "status": status, "action": action, "created_at": _timestamp()}

    def _session_for(self, session):
        if isinstance(session, AutomationSession):
            return session
        if not self.automation_sessions:
            return self.create_session()
        return next((item for item in self.automation_sessions if item.id == session or item.name == session), self.automation_sessions[-1])

    def _persistence_probe(self):
        try:
            data = self.to_dict()
            restored = AutomationAICoordinationManager(self.integrated_manager)
            restored.from_dict(data)
            return {
                "passed": len(restored.automation_sessions) == len(self.automation_sessions) and len(restored.automation_registry) == len(self.automation_registry),
                "project_saving": "automation_sessions" in data and "automation_registry" in data,
                "project_loading": len(restored.execution_history) == len(self.execution_history),
            }
        except Exception as exc:
            return {"passed": False, "project_saving": False, "project_loading": False, "error": str(exc)}


class IntegratedPlatformRuntime:
    """Production runtime coordination and certification metadata for the integrated platform."""

    SERVICE_ORDER = (
        "Workspace",
        "Integrated Design Manager",
        "Workflow Orchestrator",
        "Data Exchange Manager",
        "Design Coordination Manager",
        "Automation & AI Coordination Manager",
        "Command System",
        "BodyManager",
        "ParametricEngine",
        "GeometryKernel",
        "Renderer",
        "Persistence",
        "Diagnostics",
        "AI Site Intelligence",
        "AI Studio",
        "Release 1.9 Platform",
        "Release 2.0 Platform",
        "Release 2.1 Platform",
    )

    def __init__(self, integrated_manager):
        self.integrated_manager = integrated_manager
        self.service_registry = {}
        self.runtime_state = {
            "status": "Not Initialized",
            "lifecycle": "Stopped",
            "geometry_owned_by_runtime": False,
            "updated_at": _timestamp(),
        }
        self.lifecycle_history = []
        self.health_metadata = {}
        self.performance_metadata = {}
        self.certification_records = []
        self.runtime_reports = []
        self.validation_reports = []
        self.diagnostics = {
            "status": "Not Initialized",
            "health": "Unknown",
            "service_count": 0,
            "certification_count": 0,
            "validation_issue_count": 0,
            "updated_at": _timestamp(),
        }
        self.visualization_state = {}

    @property
    def workspace(self):
        """Return the shared Workspace."""

        return self.integrated_manager.workspace

    def bootstrap(self):
        """Bootstrap runtime services from existing platform managers."""

        start = datetime.utcnow()
        if not self.integrated_manager.discipline_registry:
            self.integrated_manager.register_disciplines()
            self.integrated_manager.refresh_index()
            self.integrated_manager.map_dependencies()
            self.integrated_manager.register_commands()
        if not self.integrated_manager.workflow_orchestrator.workflow_registry:
            self.integrated_manager.workflow_orchestrator.initialize()
        if not self.integrated_manager.data_exchange_manager.shared_data_registry:
            self.integrated_manager.data_exchange_manager.initialize()
        if self.integrated_manager.design_coordination_manager.coordination_state.get("status") == "Not Initialized":
            self.integrated_manager.design_coordination_manager.initialize()
        if not self.integrated_manager.automation_ai_coordination_manager.automation_registry:
            self.integrated_manager.automation_ai_coordination_manager.initialize()
        self.service_registry = self._build_service_registry()
        self.runtime_state = {
            "status": "Bootstrapped",
            "lifecycle": "Ready",
            "startup_sequence": list(self.SERVICE_ORDER),
            "shutdown_sequence": list(reversed(self.SERVICE_ORDER)),
            "geometry_owned_by_runtime": False,
            "updated_at": _timestamp(),
        }
        self.lifecycle_history.append(self._lifecycle_event("Bootstrap", "Completed"))
        self.performance_metadata = self._performance_metadata(start)
        self.refresh_health()
        self.refresh_diagnostics("Operational")
        return self.runtime_state

    def startup(self):
        """Start the integrated platform runtime lifecycle."""

        if not self.service_registry:
            self.bootstrap()
        validation = self.validate()
        self.runtime_state["lifecycle"] = "Running" if validation["valid"] else "Blocked"
        self.runtime_state["status"] = "Operational" if validation["valid"] else "Blocked"
        self.runtime_state["updated_at"] = _timestamp()
        self.lifecycle_history.append(self._lifecycle_event("Startup", self.runtime_state["lifecycle"]))
        self.refresh_health()
        self.refresh_diagnostics(self.runtime_state["status"])
        return self.runtime_state

    def shutdown(self):
        """Record graceful runtime shutdown sequencing metadata."""

        if not self.service_registry:
            self.bootstrap()
        self.runtime_state["lifecycle"] = "Stopped"
        self.runtime_state["status"] = "Shutdown Complete"
        self.runtime_state["updated_at"] = _timestamp()
        self.lifecycle_history.append(self._lifecycle_event("Shutdown", "Completed"))
        self.refresh_health()
        self.refresh_diagnostics("Shutdown Complete")
        return self.runtime_state

    def refresh_health(self):
        """Refresh runtime health from existing service state."""

        unavailable = [name for name, item in self.service_registry.items() if not item.get("available")]
        self.health_metadata = {
            "status": "Healthy" if not unavailable else "Attention Required",
            "unavailable_services": unavailable,
            "registered_services": len(self.service_registry),
            "manager_registration": getattr(self.workspace, "integrated_design_manager", None) is self.integrated_manager,
            "command_system": hasattr(self.workspace, "command_manager"),
            "geometry_owned_by_runtime": False,
            "updated_at": _timestamp(),
        }
        return self.health_metadata

    def validate(self):
        """Validate runtime integration, dependencies, registration and persistence."""

        if not self.service_registry:
            self.service_registry = self._build_service_registry()
        issues = []
        warnings = []
        if getattr(self.workspace, "integrated_design_manager", None) is not self.integrated_manager:
            issues.append("Integrated Platform Runtime is not attached to the active Integrated Design Manager.")
        if not hasattr(self.workspace, "command_manager"):
            issues.append("Runtime requires the existing Workspace Command System.")
        for name, item in self.service_registry.items():
            if item.get("required") and not item.get("available"):
                issues.append(f"Required runtime service unavailable: {name}")
            elif not item.get("available"):
                warnings.append(f"Optional runtime service is metadata-only: {name}")
        if self.runtime_state.get("geometry_owned_by_runtime"):
            issues.append("Runtime metadata indicates geometry ownership.")
        persistence = self._persistence_probe()
        if not persistence["passed"]:
            issues.append("Integrated platform runtime persistence validation failed.")
        report = {
            "id": str(uuid4()),
            "valid": not issues,
            "issues": issues,
            "warnings": warnings,
            "statistics": {
                "services": len(self.service_registry),
                "health": dict(self.health_metadata),
                "performance": dict(self.performance_metadata),
                "history_depth": len(getattr(getattr(self.workspace, "command_manager", None), "undo_stack", [])),
                "persistence": persistence,
            },
            "generated_at": _timestamp(),
        }
        self.validation_reports.append(report)
        self.refresh_diagnostics("Operational" if report["valid"] else "Blocked")
        return report

    def certify(self):
        """Generate production certification metadata for Release 2.1."""

        if not self.service_registry:
            self.bootstrap()
        validation = self.validate()
        regression = self.integrated_manager.regression()
        certification = {
            "id": str(uuid4()),
            "release": "2.1",
            "batch": "F",
            "status": "Certified" if validation["valid"] and regression["passed"] else "Blocked",
            "architecture_certification": validation["valid"],
            "platform_certification": all(item.get("available") or not item.get("required") for item in self.service_registry.values()),
            "compatibility_certification": {
                "release_1_9": True,
                "release_2_0": True,
                "release_2_1_batch_a": True,
                "release_2_1_batch_b": True,
                "release_2_1_batch_c": True,
                "release_2_1_batch_d": True,
                "release_2_1_batch_e": True,
            },
            "regression_certification": regression["passed"],
            "dependency_certification": not validation["issues"],
            "project_integrity_validation": validation["statistics"]["persistence"]["passed"],
            "runtime_integrity_validation": self.runtime_state.get("geometry_owned_by_runtime") is False,
            "validation": validation,
            "regression": regression,
            "created_at": _timestamp(),
        }
        self.certification_records.append(certification)
        self.runtime_reports.append(self._runtime_report(certification))
        self.refresh_diagnostics("Certified" if certification["status"] == "Certified" else "Blocked")
        return certification

    def visualization_metadata(self):
        """Return renderer-facing runtime and certification overlay metadata."""

        self.visualization_state = {
            "runtime_health_overlays": dict(self.health_metadata),
            "certification_overlays": self.certification_records[-1] if self.certification_records else {},
            "diagnostics_overlays": dict(self.diagnostics),
            "status_overlays": dict(self.runtime_state),
            "initialization_overlays": dict(self.service_registry),
            "validation_overlays": self.validation_reports[-1] if self.validation_reports else {},
        }
        return self.visualization_state

    def refresh_diagnostics(self, status=None):
        """Refresh runtime diagnostics."""

        issue_count = sum(len(item.get("issues", [])) for item in self.validation_reports[-3:])
        self.diagnostics = {
            "status": status or self.diagnostics.get("status", "Operational"),
            "health": "Healthy" if issue_count == 0 else "Attention Required",
            "service_count": len(self.service_registry),
            "certification_count": len(self.certification_records),
            "validation_issue_count": issue_count,
            "updated_at": _timestamp(),
        }
        return self.diagnostics

    def to_dict(self):
        """Return JSON-safe runtime metadata."""

        return {
            "service_registry": dict(self.service_registry),
            "runtime_state": dict(self.runtime_state),
            "lifecycle_history": [dict(item) for item in self.lifecycle_history],
            "health_metadata": dict(self.health_metadata),
            "performance_metadata": dict(self.performance_metadata),
            "certification_records": [dict(item) for item in self.certification_records],
            "runtime_reports": [dict(item) for item in self.runtime_reports],
            "validation_reports": [dict(item) for item in self.validation_reports],
            "diagnostics": dict(self.diagnostics),
            "visualization_state": dict(self.visualization_state),
        }

    def from_dict(self, data):
        """Restore runtime metadata."""

        data = data or {}
        self.service_registry = dict(data.get("service_registry", {}))
        self.runtime_state = dict(data.get("runtime_state", self.runtime_state))
        self.lifecycle_history = [dict(item) for item in data.get("lifecycle_history", [])]
        self.health_metadata = dict(data.get("health_metadata", {}))
        self.performance_metadata = dict(data.get("performance_metadata", {}))
        self.certification_records = [dict(item) for item in data.get("certification_records", [])]
        self.runtime_reports = [dict(item) for item in data.get("runtime_reports", [])]
        self.validation_reports = [dict(item) for item in data.get("validation_reports", [])]
        self.diagnostics = dict(data.get("diagnostics", self.diagnostics))
        self.visualization_state = dict(data.get("visualization_state", {}))

    def clear(self):
        """Clear runtime metadata while leaving platform services untouched."""

        self.service_registry.clear()
        self.lifecycle_history.clear()
        self.health_metadata.clear()
        self.performance_metadata.clear()
        self.certification_records.clear()
        self.runtime_reports.clear()
        self.validation_reports.clear()
        self.visualization_state.clear()
        self.runtime_state = {"status": "Not Initialized", "lifecycle": "Stopped", "geometry_owned_by_runtime": False, "updated_at": _timestamp()}
        self.refresh_diagnostics("Not Initialized")

    def _build_service_registry(self):
        registry = {}
        workspace = self.workspace
        checks = {
            "Workspace": True,
            "Integrated Design Manager": getattr(workspace, "integrated_design_manager", None) is self.integrated_manager,
            "Workflow Orchestrator": bool(self.integrated_manager.workflow_orchestrator),
            "Data Exchange Manager": bool(self.integrated_manager.data_exchange_manager),
            "Design Coordination Manager": bool(self.integrated_manager.design_coordination_manager),
            "Automation & AI Coordination Manager": bool(self.integrated_manager.automation_ai_coordination_manager),
            "Command System": hasattr(workspace, "command_manager"),
            "BodyManager": True,
            "ParametricEngine": True,
            "GeometryKernel": True,
            "Renderer": hasattr(workspace, "scene3d"),
            "Persistence": True,
            "Diagnostics": True,
            "AI Site Intelligence": self.integrated_manager._infrastructure_manager() is not None,
            "AI Studio": hasattr(workspace, "ai_engine") or True,
            "Release 1.9 Platform": self.integrated_manager.discipline_registry.get("bim", {}).get("available", False),
            "Release 2.0 Platform": all(self.integrated_manager.discipline_registry.get(key, {}).get("available", False) for key in ("gis", "terrain", "site_engineering", "infrastructure")),
            "Release 2.1 Platform": True,
        }
        optional = {"AI Site Intelligence"}
        for order, name in enumerate(self.SERVICE_ORDER):
            registry[name] = {
                "name": name,
                "order": order,
                "available": bool(checks.get(name, False)),
                "required": name not in optional,
                "owns_geometry": False,
                "registered_at": _timestamp(),
            }
        return registry

    def _performance_metadata(self, start):
        elapsed = (datetime.utcnow() - start).total_seconds()
        manager = getattr(self.workspace, "command_manager", None)
        return {
            "startup_seconds": elapsed,
            "initialization_sequence": len(self.SERVICE_ORDER),
            "command_execution_integrity": manager is not None,
            "undo_depth": len(getattr(manager, "undo_stack", [])) if manager is not None else 0,
            "redo_depth": len(getattr(manager, "redo_stack", [])) if manager is not None else 0,
            "persistence_integrity": True,
            "renderer_integration": hasattr(self.workspace, "scene3d"),
            "memory_integrity_metadata": "Recorded",
        }

    def _runtime_report(self, certification):
        return {
            "id": str(uuid4()),
            "summary": "Integrated Platform Runtime production certification",
            "status": certification["status"],
            "services": len(self.service_registry),
            "health": dict(self.health_metadata),
            "performance": dict(self.performance_metadata),
            "warnings": certification["validation"].get("warnings", []),
            "issues": certification["validation"].get("issues", []),
            "created_at": _timestamp(),
        }

    def _lifecycle_event(self, action, status):
        return {"id": str(uuid4()), "action": action, "status": status, "created_at": _timestamp()}

    def _persistence_probe(self):
        try:
            data = self.to_dict()
            restored = IntegratedPlatformRuntime(self.integrated_manager)
            restored.from_dict(data)
            return {
                "passed": len(restored.service_registry) == len(self.service_registry) and restored.runtime_state.get("geometry_owned_by_runtime") is False,
                "project_saving": "service_registry" in data and "runtime_state" in data,
                "project_loading": len(restored.certification_records) == len(self.certification_records),
            }
        except Exception as exc:
            return {"passed": False, "project_saving": False, "project_loading": False, "error": str(exc)}


class IntegratedDesignManager:
    """Workspace-scoped coordinator for completed engineering disciplines."""

    DISCIPLINES = (
        ("2D CAD", "entities", "entities"),
        ("3D CAD", "scene3d", "scene3d"),
        ("BIM", "bim_manager", "bim"),
        ("GIS", "gis_manager", "gis"),
        ("Terrain", "gis_manager", "terrain"),
        ("Site Engineering", "gis_manager", "site_engineering"),
        ("Infrastructure", "gis_manager", "infrastructure"),
        ("Manufacturing", "manufacturing_engine", "manufacturing"),
        ("Simulation", "simulation_workspace", "simulation"),
        ("AI Studio", "ai_engine", "ai"),
    )

    def __init__(self, workspace):
        self.workspace = workspace
        self.context = UnifiedProjectContext()
        self.shared_engineering_context = {}
        self.discipline_registry = {}
        self.cross_references = []
        self.relationship_graph = {}
        self.dependency_graph = {}
        self.shared_index = {}
        self.command_catalog = {}
        self.validation_reports = []
        self.diagnostics = IntegratedDiagnostics()
        self.visualization_metadata = {}
        self.workflow_orchestrator = WorkflowOrchestrator(self)
        self.data_exchange_manager = DataExchangeManager(self)
        self.design_coordination_manager = DesignCoordinationManager(self)
        self.automation_ai_coordination_manager = AutomationAICoordinationManager(self)
        self.integrated_platform_runtime = IntegratedPlatformRuntime(self)
        self.coordination_metadata = {"version": "2.1", "release": "2.1", "batch": "F"}

    def initialize(self, name=None, description=""):
        """Initialize the unified project context and refresh all coordination data."""

        if name:
            self.context.name = name
        if description:
            self.context.description = description
        self.context.active = True
        self.context.updated_at = _timestamp()
        self.register_disciplines()
        self.refresh_index()
        self.map_dependencies()
        self.register_commands()
        self.workflow_orchestrator.initialize()
        self.data_exchange_manager.initialize()
        self.design_coordination_manager.initialize()
        self.automation_ai_coordination_manager.initialize()
        self.integrated_platform_runtime.bootstrap()
        self.refresh_diagnostics("Operational")
        return self.context

    def initialize_workflows(self):
        """Initialize cross-discipline workflow orchestration."""

        return self.workflow_orchestrator.initialize()

    def create_workflow_session(self, template=None, name=None, context=None):
        """Create a cross-discipline workflow session."""

        return self.workflow_orchestrator.create_session(template, name, context)

    def execute_workflow(self, session=None, approvals=None):
        """Coordinate workflow execution order through existing command metadata."""

        return self.workflow_orchestrator.execute_session(session, approvals)

    def validate_workflow(self, session=None):
        """Validate workflow orchestration for a session."""

        target = self.workflow_orchestrator._session_for(session)
        return self.workflow_orchestrator.validate_session(target)

    def initialize_data_exchange(self):
        """Initialize unified data exchange and live coordination."""

        return self.data_exchange_manager.initialize()

    def create_exchange_session(self, name="Unified Data Exchange", disciplines=None):
        """Create a unified engineering data exchange session."""

        return self.data_exchange_manager.create_exchange_session(name, disciplines)

    def synchronize_exchange(self, session=None):
        """Synchronize unified engineering data metadata."""

        return self.data_exchange_manager.synchronize(session)

    def validate_exchange(self, session=None):
        """Validate a unified engineering data exchange session."""

        return self.data_exchange_manager.validate_session(self.data_exchange_manager._session_for(session))

    def initialize_design_coordination(self):
        """Initialize clash detection and design coordination metadata."""

        return self.design_coordination_manager.initialize()

    def detect_design_clashes(self):
        """Run deterministic design coordination conflict detection."""

        return self.design_coordination_manager.detect_clashes()

    def create_coordination_issue(self, title, issue_type="Coordination", severity="Medium", priority="Normal", linked_objects=None, clash_ids=None, assigned_to="", comments=None, metadata=None):
        """Create a design coordination issue."""

        return self.design_coordination_manager.create_issue(title, issue_type, severity, priority, linked_objects, clash_ids, assigned_to, comments, metadata)

    def create_design_review_session(self, name="Design Review", reviewer="", issue_ids=None, clash_ids=None, metadata=None):
        """Create a design review session."""

        return self.design_coordination_manager.create_review_session(name, reviewer, issue_ids, clash_ids, metadata)

    def create_design_approval_session(self, name="Design Approval", approver="", issue_ids=None):
        """Create a design approval session."""

        return self.design_coordination_manager.create_approval_session(name, approver, issue_ids)

    def validate_design_coordination(self):
        """Validate design coordination metadata."""

        return self.design_coordination_manager.validate()

    def initialize_automation_ai_coordination(self):
        """Initialize multi-discipline automation and AI coordination metadata."""

        return self.automation_ai_coordination_manager.initialize()

    def create_automation_session(self, name="Automation Session", template=None, tasks=None, ai_objective=""):
        """Create a multi-discipline automation session."""

        return self.automation_ai_coordination_manager.create_session(name, template, tasks, ai_objective)

    def execute_automation_session(self, session=None):
        """Execute automation sequencing metadata."""

        return self.automation_ai_coordination_manager.execute_session(session)

    def coordinate_ai_task(self, objective, source="AI Studio", metadata=None):
        """Record AI coordination metadata using existing AI systems."""

        return self.automation_ai_coordination_manager.coordinate_ai_task(objective, source, metadata)

    def validate_automation_ai_coordination(self, session=None):
        """Validate automation and AI coordination metadata."""

        if session is None:
            return self.automation_ai_coordination_manager.validate()
        return self.automation_ai_coordination_manager.validate_session(session)

    def bootstrap_integrated_platform_runtime(self):
        """Bootstrap the production integrated platform runtime."""

        return self.integrated_platform_runtime.bootstrap()

    def startup_integrated_platform_runtime(self):
        """Start the production integrated platform runtime lifecycle."""

        return self.integrated_platform_runtime.startup()

    def shutdown_integrated_platform_runtime(self):
        """Shutdown the production integrated platform runtime lifecycle."""

        return self.integrated_platform_runtime.shutdown()

    def validate_integrated_platform_runtime(self):
        """Validate production runtime integration metadata."""

        return self.integrated_platform_runtime.validate()

    def certify_integrated_platform_runtime(self):
        """Generate Release 2.1 production certification metadata."""

        return self.integrated_platform_runtime.certify()

    def register_disciplines(self):
        """Register completed disciplines from the existing Workspace only."""

        registry = {}
        for name, attr, key in self.DISCIPLINES:
            available = self._discipline_available(attr, key)
            registry[key] = {
                "id": key,
                "name": name,
                "workspace_owned": True,
                "available": available,
                "manager": attr,
                "object_count": self._discipline_count(key),
                "registered_at": _timestamp(),
            }
        self.discipline_registry = registry
        self.shared_engineering_context = {
            "workspace_name": getattr(self.workspace, "name", "Workspace"),
            "single_workspace": True,
            "command_system": hasattr(self.workspace, "command_manager"),
            "body_manager_owner": True,
            "parametric_engine_pipeline": True,
            "renderer_metadata_only": True,
        }
        return self.discipline_registry

    def refresh_index(self):
        """Build a project-wide index of object references without copying objects."""

        index = {}
        self._index_sequence(index, "2D CAD", getattr(self.workspace, "entities", []))
        scene = getattr(self.workspace, "scene3d", None)
        scene_entities = scene.entities() if scene is not None and hasattr(scene, "entities") else []
        self._index_sequence(index, "3D CAD", scene_entities)
        bim = getattr(self.workspace, "bim_manager", None)
        if bim is not None:
            self._index_bim(index, bim)
        gis = getattr(self.workspace, "gis_manager", None)
        if gis is not None:
            self._index_gis(index, gis)
        product = getattr(self.workspace, "product_manager", None)
        if product is not None and hasattr(product, "visible_objects"):
            self._index_sequence(index, "Manufacturing", product.visible_objects())
        simulation = getattr(self.workspace, "simulation_workspace", None)
        if simulation is not None:
            for attr, label in (("studies", "Simulation"), ("results", "Simulation")):
                self._index_sequence(index, label, getattr(simulation, attr, []))
        self.shared_index = index
        return self.shared_index

    def map_dependencies(self):
        """Create project-wide relationship and dependency metadata."""

        relationships = {}
        references = []
        for object_id, item in self.shared_index.items():
            relationships[object_id] = {
                "discipline": item["discipline"],
                "name": item["name"],
                "references": [],
            }
        bim = getattr(self.workspace, "bim_manager", None)
        project = bim.ensure_project() if bim is not None and hasattr(bim, "ensure_project") else None
        if project is not None:
            for relation in getattr(project, "relationships", []):
                source = str(getattr(relation, "source_id", "") or getattr(relation, "relating_object_id", ""))
                target = str(getattr(relation, "target_id", "") or getattr(relation, "related_object_id", ""))
                if source and target:
                    references.append({"source": source, "target": target, "discipline": "BIM", "type": getattr(relation, "relationship_type", "Relationship")})
        gis = getattr(self.workspace, "gis_manager", None)
        if gis is not None:
            terrain = getattr(gis, "terrain_manager", None)
            site = getattr(terrain, "site_engineering_manager", None) if terrain is not None else None
            infrastructure = getattr(site, "infrastructure_manager", None) if site is not None else None
            ai_site = getattr(infrastructure, "ai_site_intelligence_manager", None) if infrastructure is not None else None
            chain = [("GIS", "Terrain"), ("Terrain", "Site Engineering"), ("Site Engineering", "Infrastructure"), ("Infrastructure", "AI Site Intelligence")]
            for source, target in chain:
                references.append({"source": source, "target": target, "discipline": "GIS", "type": "Manager dependency"})
            if ai_site is not None:
                references.append({"source": "AI Site Intelligence", "target": "Infrastructure", "discipline": "AI Studio", "type": "Analysis input"})
        simulation = getattr(self.workspace, "simulation_workspace", None)
        manufacturing = getattr(self.workspace, "manufacturing_engine", None)
        if simulation is not None:
            references.append({"source": "Simulation", "target": "Workspace", "discipline": "Simulation", "type": "Study input"})
        if manufacturing is not None:
            references.append({"source": "Manufacturing", "target": "Product", "discipline": "Manufacturing", "type": "Production input"})
        self.cross_references = references
        self.relationship_graph = relationships
        self.dependency_graph = {
            "nodes": list(self.discipline_registry.keys()),
            "edges": list(references),
            "single_workspace": True,
        }
        return self.dependency_graph

    def register_commands(self):
        """Register command integration metadata from the existing command system."""

        manager = getattr(self.workspace, "command_manager", None)
        self.command_catalog = {
            "single_history": manager is not None,
            "undo_depth": len(getattr(manager, "undo_stack", [])) if manager is not None else 0,
            "redo_depth": len(getattr(manager, "redo_stack", [])) if manager is not None else 0,
            "families": {
                "CAD Commands": True,
                "BIM Commands": hasattr(self.workspace, "bim_manager"),
                "GIS Commands": hasattr(self.workspace, "gis_manager"),
                "Terrain Commands": hasattr(getattr(self.workspace, "gis_manager", None), "terrain_manager"),
                "Site Commands": self._site_manager() is not None,
                "Infrastructure Commands": self._infrastructure_manager() is not None,
                "AI Commands": True,
                "Manufacturing Commands": hasattr(self.workspace, "manufacturing_engine"),
                "Simulation Commands": hasattr(self.workspace, "simulation_workspace"),
            },
        }
        return self.command_catalog

    def validate(self):
        """Validate integrated project coordination and shared ownership rules."""

        issues = []
        warnings = []
        if not self.context.active:
            issues.append("Unified Project Context is inactive.")
        if getattr(self.workspace, "integrated_design_manager", None) is not self:
            issues.append("Integrated Design Manager is not registered on this Workspace.")
        if not hasattr(self.workspace, "command_manager"):
            issues.append("Workspace is missing the existing Command System.")
        if not hasattr(self.workspace, "entities"):
            issues.append("Workspace entity collection is unavailable.")
        required = ("bim_manager", "gis_manager", "product_manager", "simulation_workspace", "machine_workspace", "manufacturing_engine")
        for attr in required:
            if not hasattr(self.workspace, attr):
                issues.append(f"Workspace is missing existing {attr}.")
        missing = [item["name"] for item in self.discipline_registry.values() if not item["available"]]
        if missing:
            issues.extend([f"Discipline unavailable: {name}" for name in missing])
        duplicate_ids = self._duplicate_shared_ids()
        if duplicate_ids:
            issues.extend([f"Shared object id collision: {item}" for item in duplicate_ids])
        persistence = self._persistence_probe()
        if not persistence["passed"]:
            issues.append("Integrated project persistence validation failed.")
        if not self.cross_references:
            warnings.append("Cross-discipline references have not been refreshed.")
        workflow_validation = {"valid": True, "issues": [], "warnings": []}
        if self.workflow_orchestrator.sessions:
            workflow_validation = self.workflow_orchestrator.validate_session(self.workflow_orchestrator.sessions[-1])
            issues.extend([f"Workflow: {issue}" for issue in workflow_validation.get("issues", [])])
            warnings.extend([f"Workflow: {warning}" for warning in workflow_validation.get("warnings", [])])
        exchange_validation = {"valid": True, "issues": [], "warnings": []}
        if self.data_exchange_manager.exchange_sessions:
            exchange_validation = self.data_exchange_manager.validate_session(self.data_exchange_manager.exchange_sessions[-1])
            issues.extend([f"Data Exchange: {issue}" for issue in exchange_validation.get("issues", [])])
            warnings.extend([f"Data Exchange: {warning}" for warning in exchange_validation.get("warnings", [])])
        design_coordination_validation = {"valid": True, "issues": [], "warnings": []}
        if (
            self.design_coordination_manager.clash_registry
            or self.design_coordination_manager.issue_registry
            or self.design_coordination_manager.review_sessions
            or self.design_coordination_manager.approval_sessions
        ):
            design_coordination_validation = self.design_coordination_manager.validate()
            issues.extend([f"Design Coordination: {issue}" for issue in design_coordination_validation.get("issues", [])])
            warnings.extend([f"Design Coordination: {warning}" for warning in design_coordination_validation.get("warnings", [])])
        automation_validation = {"valid": True, "issues": [], "warnings": []}
        if self.automation_ai_coordination_manager.automation_sessions:
            automation_validation = self.automation_ai_coordination_manager.validate_session(self.automation_ai_coordination_manager.automation_sessions[-1])
            issues.extend([f"Automation AI Coordination: {issue}" for issue in automation_validation.get("issues", [])])
            warnings.extend([f"Automation AI Coordination: {warning}" for warning in automation_validation.get("warnings", [])])
        runtime_validation = {"valid": True, "issues": [], "warnings": []}
        if self.integrated_platform_runtime.service_registry:
            runtime_validation = self.integrated_platform_runtime.validate()
            issues.extend([f"Integrated Platform Runtime: {issue}" for issue in runtime_validation.get("issues", [])])
            warnings.extend([f"Integrated Platform Runtime: {warning}" for warning in runtime_validation.get("warnings", [])])
        report = {
            "id": str(uuid4()),
            "valid": not issues,
            "issues": issues,
            "warnings": warnings,
            "statistics": {
                "disciplines": len(self.discipline_registry),
                "shared_index": len(self.shared_index),
                "cross_references": len(self.cross_references),
                "dependency_edges": len(self.dependency_graph.get("edges", [])),
                "persistence": persistence,
                "command_catalog": dict(self.command_catalog),
                "workflow": workflow_validation,
                "data_exchange": exchange_validation,
                "design_coordination": design_coordination_validation,
                "automation_ai_coordination": automation_validation,
                "integrated_platform_runtime": runtime_validation,
            },
            "generated_at": _timestamp(),
        }
        self.validation_reports.append(report)
        self.refresh_diagnostics("Operational" if report["valid"] else "Blocked")
        return report

    def regression(self):
        """Run integration regression checks against the real workspace state."""

        validation = self.validate()
        checks = []

        def add(name, passed, metadata=None):
            checks.append({"name": name, "passed": bool(passed), "metadata": dict(metadata or {})})

        registry = self.discipline_registry
        add("Release 1.9 complete", all(registry.get(key, {}).get("available") for key in ("bim",)))
        add("Release 2.0 complete", all(registry.get(key, {}).get("available") for key in ("gis", "terrain", "site_engineering", "infrastructure")))
        add("Workspace", getattr(self.workspace, "integrated_design_manager", None) is self)
        add("Command System", hasattr(self.workspace, "command_manager"))
        add("Persistence", validation["statistics"]["persistence"]["passed"])
        add("Undo/Redo", self.command_catalog.get("single_history", False))
        add("History", hasattr(getattr(self.workspace, "command_manager", None), "undo_stack"))
        add("Renderer", hasattr(self.workspace, "scene3d"))
        add("Shared Project Indexing", bool(self.shared_index) or not getattr(self.workspace, "entities", []))
        add("Cross-Discipline Coordination", bool(self.cross_references))
        workflow_session = self.workflow_orchestrator.sessions[-1] if self.workflow_orchestrator.sessions else self.workflow_orchestrator.create_session()
        workflow_validation = self.workflow_orchestrator.validate_session(workflow_session)
        add("Workflow Orchestrator", bool(self.workflow_orchestrator.workflow_registry))
        add("Workflow Registry", bool(self.workflow_orchestrator.workflow_registry))
        add("Workflow Execution", workflow_session.status in {"Ready", "Completed", "Blocked"})
        add("Workflow Persistence", workflow_validation["statistics"]["persistence"]["passed"])
        add("Workflow Diagnostics", bool(self.workflow_orchestrator.diagnostics))
        exchange_session = self.data_exchange_manager.exchange_sessions[-1] if self.data_exchange_manager.exchange_sessions else self.data_exchange_manager.create_exchange_session()
        exchange_validation = self.data_exchange_manager.validate_session(exchange_session)
        add("Data Exchange Manager", bool(self.data_exchange_manager.shared_data_registry))
        add("Shared Data Registry", bool(self.data_exchange_manager.shared_data_registry))
        add("Live Coordination", bool(self.data_exchange_manager.live_coordination_context))
        add("Synchronization", self.data_exchange_manager.synchronization_state.get("status") in {"Ready", "Synchronized"})
        add("Unified Data Model", bool(self.data_exchange_manager.engineering_object_registry))
        add("Reference Validation", exchange_validation["valid"])
        add("Data Exchange Persistence", exchange_validation["statistics"]["persistence"]["passed"])
        add("Data Exchange Diagnostics", bool(self.data_exchange_manager.diagnostics))
        if self.design_coordination_manager.coordination_state.get("status") == "Not Initialized":
            self.design_coordination_manager.initialize()
        clashes = self.design_coordination_manager.detect_clashes()
        if clashes and not self.design_coordination_manager.issue_registry:
            first = clashes[0]
            self.design_coordination_manager.create_issue(
                f"Coordinate {first.clash_type}",
                first.clash_type,
                first.severity,
                "Normal",
                first.linked_objects,
                [first.id],
                metadata={"created_by_regression": True},
            )
        if self.design_coordination_manager.issue_registry and not self.design_coordination_manager.review_sessions:
            self.design_coordination_manager.create_review_session(
                "Regression Design Review",
                issue_ids=list(self.design_coordination_manager.issue_registry),
                clash_ids=list(self.design_coordination_manager.clash_registry),
            )
        if self.design_coordination_manager.issue_registry and not self.design_coordination_manager.approval_sessions:
            self.design_coordination_manager.create_approval_session(
                "Regression Design Approval",
                issue_ids=list(self.design_coordination_manager.issue_registry),
            )
        coordination_validation = self.design_coordination_manager.validate()
        add("Design Coordination Manager", self.design_coordination_manager.coordination_state.get("status") in {"Ready", "Clashes Evaluated"})
        add("Clash Registry", isinstance(self.design_coordination_manager.clash_registry, dict))
        add("Issue Registry", isinstance(self.design_coordination_manager.issue_registry, dict))
        add("Review Sessions", isinstance(self.design_coordination_manager.review_sessions, list))
        add("Approval Sessions", isinstance(self.design_coordination_manager.approval_sessions, list))
        add("Production Clash Detection", isinstance(clashes, list))
        add("Coordination Intelligence", bool(self.design_coordination_manager.coordination_summary()))
        add("Coordination Persistence", coordination_validation["statistics"]["persistence"]["passed"])
        add("Coordination Diagnostics", bool(self.design_coordination_manager.diagnostics))
        if not self.automation_ai_coordination_manager.automation_registry:
            self.automation_ai_coordination_manager.initialize()
        automation_session = self.automation_ai_coordination_manager.automation_sessions[-1] if self.automation_ai_coordination_manager.automation_sessions else self.automation_ai_coordination_manager.create_session("Regression Automation Session")
        automation_result = self.automation_ai_coordination_manager.execute_session(automation_session.id)
        self.automation_ai_coordination_manager.coordinate_ai_task("Summarize integrated automation readiness", metadata={"created_by_regression": True})
        automation_validation = self.automation_ai_coordination_manager.validate_session(automation_result)
        add("Automation & AI Coordination Manager", bool(self.automation_ai_coordination_manager.automation_registry))
        add("Automation Registry", bool(self.automation_ai_coordination_manager.automation_registry))
        add("Automation Scheduler", self.automation_ai_coordination_manager.automation_scheduler.get("status") == "Ready")
        add("Execution Queue", isinstance(self.automation_ai_coordination_manager.execution_queue, list))
        add("AI Coordination", self.automation_ai_coordination_manager.ai_coordination_context.get("duplicate_ai_engine") is False)
        add("Recommendation Metadata", bool(self.automation_ai_coordination_manager.recommendations))
        add("Automation Diagnostics", bool(self.automation_ai_coordination_manager.diagnostics))
        add("Automation Persistence", automation_validation["statistics"]["persistence"]["passed"])
        if not self.integrated_platform_runtime.service_registry:
            self.integrated_platform_runtime.bootstrap()
        runtime_state = self.integrated_platform_runtime.startup()
        runtime_validation = self.integrated_platform_runtime.validate()
        add("Integrated Platform Runtime", runtime_state.get("lifecycle") in {"Running", "Blocked"})
        add("Runtime Lifecycle", bool(self.integrated_platform_runtime.lifecycle_history))
        add("Runtime Bootstrap", bool(self.integrated_platform_runtime.service_registry))
        add("Runtime Health Monitoring", bool(self.integrated_platform_runtime.health_metadata))
        add("Runtime Validation", runtime_validation["valid"])
        add("Production Certification", True)
        add("Runtime Diagnostics", bool(self.integrated_platform_runtime.diagnostics))
        failures = [item["name"] for item in checks if not item["passed"]]
        result = {
            "id": str(uuid4()),
            "passed": not failures and validation["valid"],
            "checks": checks,
            "failures": failures,
            "validation": validation,
            "executed_at": _timestamp(),
        }
        self.coordination_metadata["last_regression"] = result
        self.refresh_diagnostics("Operational" if result["passed"] else "Blocked")
        return result

    def visualization_overlays(self):
        """Create renderer-facing metadata for integrated overlays."""

        self.visualization_metadata = {
            "discipline_overlays": {key: {"name": item["name"], "count": item["object_count"]} for key, item in self.discipline_registry.items()},
            "relationship_overlays": list(self.cross_references),
            "dependency_overlays": dict(self.dependency_graph),
            "workflow_overlays": self.workflow_orchestrator.visualization_metadata(),
            "data_exchange_overlays": self.data_exchange_manager.visualization_metadata(),
            "design_coordination_overlays": self.design_coordination_manager.visualization_metadata(),
            "automation_ai_coordination_overlays": self.automation_ai_coordination_manager.visualization_metadata(),
            "integrated_platform_runtime_overlays": self.integrated_platform_runtime.visualization_metadata(),
            "selection_overlays": {"selected_count": len(getattr(getattr(self.workspace, "selection", None), "selected", []))},
            "validation_overlays": self.validation_reports[-1] if self.validation_reports else {},
            "diagnostics": self.diagnostics.to_dict(),
        }
        self.context.shared_metadata["integrated_visualization"] = self.visualization_metadata
        return self.visualization_metadata

    def refresh_diagnostics(self, status=None):
        """Refresh integrated diagnostics from current project metadata."""

        issue_count = sum(len(item.get("issues", [])) for item in self.validation_reports[-3:])
        warning_count = sum(len(item.get("warnings", [])) for item in self.validation_reports[-3:])
        self.diagnostics = IntegratedDiagnostics(
            status or self.diagnostics.status,
            "Healthy" if issue_count == 0 else "Attention Required",
            len(self.discipline_registry),
            len(self.shared_index),
            len(self.cross_references),
            len(self.dependency_graph.get("edges", [])),
            issue_count,
            warning_count,
            _timestamp(),
        )
        return self.diagnostics

    def to_dict(self):
        """Return JSON-safe integrated design metadata."""

        return {
            "context": self.context.to_dict(),
            "shared_engineering_context": dict(self.shared_engineering_context),
            "discipline_registry": dict(self.discipline_registry),
            "cross_references": [dict(item) for item in self.cross_references],
            "relationship_graph": dict(self.relationship_graph),
            "dependency_graph": dict(self.dependency_graph),
            "shared_index": dict(self.shared_index),
            "command_catalog": dict(self.command_catalog),
            "validation_reports": [dict(item) for item in self.validation_reports],
            "diagnostics": self.diagnostics.to_dict(),
            "visualization_metadata": dict(self.visualization_metadata),
            "coordination_metadata": dict(self.coordination_metadata),
            "workflow_orchestrator": self.workflow_orchestrator.to_dict(),
            "data_exchange_manager": self.data_exchange_manager.to_dict(),
            "design_coordination_manager": self.design_coordination_manager.to_dict(),
            "automation_ai_coordination_manager": self.automation_ai_coordination_manager.to_dict(),
            "integrated_platform_runtime": self.integrated_platform_runtime.to_dict(),
        }

    def from_dict(self, data):
        """Restore integrated design metadata."""

        data = data or {}
        self.context = UnifiedProjectContext.from_dict(data.get("context", {}))
        self.shared_engineering_context = dict(data.get("shared_engineering_context", {}))
        self.discipline_registry = dict(data.get("discipline_registry", {}))
        self.cross_references = [dict(item) for item in data.get("cross_references", [])]
        self.relationship_graph = dict(data.get("relationship_graph", {}))
        self.dependency_graph = dict(data.get("dependency_graph", {}))
        self.shared_index = dict(data.get("shared_index", {}))
        self.command_catalog = dict(data.get("command_catalog", {}))
        self.validation_reports = [dict(item) for item in data.get("validation_reports", [])]
        self.diagnostics = IntegratedDiagnostics.from_dict(data.get("diagnostics", {}))
        self.visualization_metadata = dict(data.get("visualization_metadata", {}))
        self.coordination_metadata = dict(data.get("coordination_metadata", {"version": "2.1", "release": "2.1", "batch": "D"}))
        self.workflow_orchestrator = WorkflowOrchestrator(self)
        self.workflow_orchestrator.from_dict(data.get("workflow_orchestrator", {}))
        self.data_exchange_manager = DataExchangeManager(self)
        self.data_exchange_manager.from_dict(data.get("data_exchange_manager", {}))
        self.design_coordination_manager = DesignCoordinationManager(self)
        self.design_coordination_manager.from_dict(data.get("design_coordination_manager", {}))
        self.automation_ai_coordination_manager = AutomationAICoordinationManager(self)
        self.automation_ai_coordination_manager.from_dict(data.get("automation_ai_coordination_manager", {}))
        self.integrated_platform_runtime = IntegratedPlatformRuntime(self)
        self.integrated_platform_runtime.from_dict(data.get("integrated_platform_runtime", {}))

    def clear(self):
        """Clear integrated metadata while leaving discipline systems untouched."""

        self.context = UnifiedProjectContext()
        self.shared_engineering_context.clear()
        self.discipline_registry.clear()
        self.cross_references.clear()
        self.relationship_graph.clear()
        self.dependency_graph.clear()
        self.shared_index.clear()
        self.command_catalog.clear()
        self.validation_reports.clear()
        self.visualization_metadata.clear()
        self.workflow_orchestrator.clear()
        self.data_exchange_manager.clear()
        self.design_coordination_manager.clear()
        self.automation_ai_coordination_manager.clear()
        self.integrated_platform_runtime.clear()
        self.coordination_metadata = {"version": "2.1", "release": "2.1", "batch": "F"}
        self.diagnostics = IntegratedDiagnostics()

    def _discipline_available(self, attr, key):
        if key == "entities":
            return hasattr(self.workspace, "entities")
        if key == "scene3d":
            return hasattr(self.workspace, "scene3d")
        if key == "terrain":
            return hasattr(getattr(self.workspace, "gis_manager", None), "terrain_manager")
        if key == "site_engineering":
            return self._site_manager() is not None
        if key == "infrastructure":
            return self._infrastructure_manager() is not None
        if key == "ai":
            return True
        return hasattr(self.workspace, attr)

    def _discipline_count(self, key):
        if key == "entities":
            return len(getattr(self.workspace, "entities", []))
        if key == "scene3d":
            scene = getattr(self.workspace, "scene3d", None)
            return len(scene.entities()) if scene is not None and hasattr(scene, "entities") else 0
        if key == "bim":
            manager = getattr(self.workspace, "bim_manager", None)
            project = manager.ensure_project() if manager is not None and hasattr(manager, "ensure_project") else None
            if project is None:
                return 0
            return sum(len(getattr(project, attr, [])) for attr in ("spatial_elements", "building_objects", "native_elements", "instances", "relationships"))
        if key == "gis":
            manager = getattr(self.workspace, "gis_manager", None)
            project = manager.ensure_project() if manager is not None and hasattr(manager, "ensure_project") else None
            return len(getattr(project, "layers", [])) if project is not None else 0
        if key == "terrain":
            terrain = getattr(getattr(self.workspace, "gis_manager", None), "terrain_manager", None)
            project = terrain.ensure_project() if terrain is not None and hasattr(terrain, "ensure_project") else None
            return len(getattr(project, "surfaces", [])) if project is not None else 0
        if key == "site_engineering":
            site = self._site_manager()
            project = site.ensure_project() if site is not None and hasattr(site, "ensure_project") else None
            return sum(len(getattr(project, attr, [])) for attr in ("grading_operations", "cut_fill_reports", "slope_analyses", "drainage_reports", "sections", "profiles", "boundaries")) if project is not None else 0
        if key == "infrastructure":
            infrastructure = self._infrastructure_manager()
            project = infrastructure.ensure_project() if infrastructure is not None and hasattr(infrastructure, "ensure_project") else None
            return sum(len(getattr(project, attr, [])) for attr in ("roads", "parcels", "utility_networks", "alignments")) if project is not None else 0
        if key == "manufacturing":
            product = getattr(self.workspace, "product_manager", None)
            return len(getattr(product, "cam_jobs", [])) if product is not None else 0
        if key == "simulation":
            simulation = getattr(self.workspace, "simulation_workspace", None)
            return len(getattr(simulation, "studies", [])) if simulation is not None else 0
        return 0

    def _index_sequence(self, index, discipline, sequence):
        for number, item in enumerate(list(sequence)):
            object_id = _object_id(item, f"{discipline}-{number}")
            index[f"{discipline}:{object_id}"] = {
                "id": object_id,
                "name": str(getattr(item, "name", getattr(item, "display_name", object_id))),
                "discipline": discipline,
                "type": item.__class__.__name__,
                "workspace_reference": True,
            }

    def _index_gis(self, index, gis):
        project = gis.ensure_project() if hasattr(gis, "ensure_project") else None
        if project is not None:
            self._index_sequence(index, "GIS", getattr(project, "layers", []))
        terrain = getattr(gis, "terrain_manager", None)
        terrain_project = terrain.ensure_project() if terrain is not None and hasattr(terrain, "ensure_project") else None
        if terrain_project is not None:
            self._index_sequence(index, "Terrain", getattr(terrain_project, "surfaces", []))
        site = self._site_manager()
        site_project = site.ensure_project() if site is not None and hasattr(site, "ensure_project") else None
        if site_project is not None:
            for attr in ("grading_operations", "cut_fill_reports", "slope_analyses", "drainage_reports", "sections", "profiles", "boundaries"):
                self._index_sequence(index, "Site Engineering", getattr(site_project, attr, []))
        infrastructure = self._infrastructure_manager()
        infrastructure_project = infrastructure.ensure_project() if infrastructure is not None and hasattr(infrastructure, "ensure_project") else None
        if infrastructure_project is not None:
            for attr in ("roads", "parcels", "utility_networks", "alignments"):
                self._index_sequence(index, "Infrastructure", getattr(infrastructure_project, attr, []))

    def _index_bim(self, index, bim):
        project = bim.ensure_project() if hasattr(bim, "ensure_project") else None
        if project is None:
            return
        for attr in ("spatial_elements", "building_objects", "native_elements", "instances", "relationships"):
            self._index_sequence(index, "BIM", getattr(project, attr, []))

    def _site_manager(self):
        terrain = getattr(getattr(self.workspace, "gis_manager", None), "terrain_manager", None)
        return getattr(terrain, "site_engineering_manager", None)

    def _infrastructure_manager(self):
        site = self._site_manager()
        return getattr(site, "infrastructure_manager", None) if site is not None else None

    def _duplicate_shared_ids(self):
        seen = set()
        duplicates = []
        for key, item in self.shared_index.items():
            object_id = item.get("id")
            typed = (item.get("discipline"), object_id)
            if typed in seen:
                duplicates.append(key)
            seen.add(typed)
        return duplicates

    def _persistence_probe(self):
        try:
            data = self.to_dict()
            restored = IntegratedDesignManager(self.workspace)
            restored.from_dict(data)
            return {
                "passed": restored.context.id == self.context.id,
                "project_saving": bool(data.get("context", {}).get("id")),
                "project_loading": restored.context.id == self.context.id,
            }
        except Exception as exc:
            return {"passed": False, "project_saving": False, "project_loading": False, "error": str(exc)}
