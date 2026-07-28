import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from engine.ai.text_to_cad import TextToCADValidationError
from engine.commands.ai_cad_command import AIParametricCADCommand
from engine.commands.product_command import AddProductReportCommand
from engine.product import ProductReport, ReportMetadata


@dataclass
class WorkflowStep:
    """One deterministic automation workflow step composed from existing AI modules."""

    name: str
    module: str
    action: str
    prerequisites: list = field(default_factory=list)
    validation_points: list = field(default_factory=list)
    rollback_point: str = ""
    completion_criteria: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe workflow step metadata."""

        return {
            "id": self.id,
            "name": self.name,
            "module": self.module,
            "action": self.action,
            "prerequisites": list(self.prerequisites),
            "validation_points": list(self.validation_points),
            "rollback_point": self.rollback_point,
            "completion_criteria": list(self.completion_criteria),
        }


@dataclass
class WorkflowTemplate:
    """Persistent reusable automation workflow template definition."""

    name: str
    objective: str
    step_modules: list
    parameters: dict = field(default_factory=dict)
    variables: dict = field(default_factory=dict)
    version: str = "1.0"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe workflow template metadata."""

        return {
            "id": self.id,
            "name": self.name,
            "objective": self.objective,
            "step_modules": list(self.step_modules),
            "parameters": dict(self.parameters),
            "variables": dict(self.variables),
            "version": self.version,
        }


@dataclass
class WorkflowValidation:
    """Automation workflow validation result."""

    valid: bool
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def to_dict(self):
        """Return JSON-safe validation metadata."""

        return {
            "valid": self.valid,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass
class WorkflowExecutionRecord:
    """Execution record for one automation workflow step."""

    step_id: str
    step_name: str
    module: str
    status: str
    output_reference_ids: list = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    duration_ms: float = 0.0
    warnings: list = field(default_factory=list)
    error: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe execution record metadata."""

        return {
            "id": self.id,
            "step_id": self.step_id,
            "step_name": self.step_name,
            "module": self.module,
            "status": self.status,
            "output_reference_ids": list(self.output_reference_ids),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "warnings": list(self.warnings),
            "error": self.error,
        }


@dataclass
class WorkflowOptimization:
    """Deterministic workflow optimization analysis metadata."""

    step_reduction_recommendations: list = field(default_factory=list)
    parallel_opportunities: list = field(default_factory=list)
    redundant_operations: list = field(default_factory=list)
    execution_improvements: list = field(default_factory=list)
    resource_optimization: list = field(default_factory=list)

    def to_dict(self):
        """Return JSON-safe optimization metadata."""

        return {
            "step_reduction_recommendations": list(self.step_reduction_recommendations),
            "parallel_opportunities": list(self.parallel_opportunities),
            "redundant_operations": list(self.redundant_operations),
            "execution_improvements": list(self.execution_improvements),
            "resource_optimization": list(self.resource_optimization),
        }


@dataclass
class AIAutomationPlan:
    """Production automation plan orchestrating existing AI systems only."""

    prompt: str
    workflow_objective: str
    template: WorkflowTemplate
    steps: list
    dependencies: dict
    validation: WorkflowValidation
    optimization: WorkflowOptimization
    completion_criteria: list
    explanation: dict
    diagnostics: dict
    command_label: str = "AI Automation Studio"
    object_type: str = "AI Automation Studio"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe automation plan metadata."""

        return {
            "id": self.id,
            "prompt": self.prompt,
            "workflow_objective": self.workflow_objective,
            "template": self.template.to_dict(),
            "steps": [step.to_dict() for step in self.steps],
            "dependencies": dict(self.dependencies),
            "validation": self.validation.to_dict(),
            "optimization": self.optimization.to_dict(),
            "completion_criteria": list(self.completion_criteria),
            "explanation": dict(self.explanation),
            "diagnostics": dict(self.diagnostics),
        }


@dataclass
class AIAutomationResult:
    """Result of executing an automation workflow through existing AI modules."""

    plan: AIAutomationPlan
    execution_records: list
    command: AIParametricCADCommand
    generated_outputs: dict
    diagnostics: dict

    def to_dict(self):
        """Return JSON-safe automation execution result."""

        return {
            "plan": self.plan.to_dict(),
            "execution_records": [record.to_dict() for record in self.execution_records],
            "command": self.command.name,
            "generated_outputs": dict(self.generated_outputs),
            "diagnostics": dict(self.diagnostics),
        }


class AIAutomationStudio:
    """Coordinates reusable engineering workflows using existing AI Studio modules."""

    STANDARDS = {"ISO", "ANSI", "DIN", "JIS", "BS"}

    def __init__(self, ai_engine):

        self.ai_engine = ai_engine
        self.templates = self._build_templates()
        self.statistics = {
            "requests": 0,
            "successful": 0,
            "failed": 0,
            "execution_time_ms": 0.0,
            "workflow_count": len(self.templates),
            "template_count": len(self.templates),
            "validation_statistics": 0,
            "recovery_statistics": 0,
            "failure_statistics": 0,
            "optimization_statistics": 0,
            "reports_generated": 0,
        }
        self.last_plan = None

    def plan(self, prompt, workspace, session=None, template="Complete Engineering Package", standard="ISO"):
        """Plan a reusable automation workflow without mutating the workspace."""

        started = time.perf_counter()
        try:
            standard_name = self._standard_name(standard)
            workflow_template = self._template(template, prompt, workspace)
            steps = self._steps_for_template(workflow_template, workspace)
            dependencies = self._dependencies(steps)
            validation = self._validate(workspace, steps)
            if not validation.valid:
                raise TextToCADValidationError("; ".join(validation.errors))
            optimization = self._optimization(steps)
            diagnostics = {
                "planning_time_ms": (time.perf_counter() - started) * 1000.0,
                "steps": len(steps),
                "dependencies": sum(len(value) for value in dependencies.values()),
                "validation_points": sum(len(step.validation_points) for step in steps),
                "rollback_points": len([step for step in steps if step.rollback_point]),
                "template": workflow_template.name,
                "standard": standard_name,
            }
            plan = AIAutomationPlan(
                prompt,
                workflow_template.objective,
                workflow_template,
                steps,
                dependencies,
                validation,
                optimization,
                self._completion_criteria(steps),
                self._explain(workflow_template, steps, standard_name, validation, optimization),
                diagnostics,
            )
            self.last_plan = plan
            return plan
        except Exception:
            self.statistics["failed"] += 1
            raise

    def execute(self, prompt, workspace, session=None, template="Complete Engineering Package", standard="ISO"):
        """Execute a deterministic workflow through existing AI modules and commands."""

        self.statistics["requests"] += 1
        started = time.perf_counter()
        records = []
        generated_outputs = {}
        try:
            plan = self.plan(prompt, workspace, session, template, standard)
            for step in plan.steps:
                record = self._execute_step(step, prompt, workspace, session, standard)
                records.append(record)
                generated_outputs[step.module] = list(record.output_reference_ids)
            reports = self._reports_for_execution(plan, records, generated_outputs)
            command = AIParametricCADCommand(
                workspace,
                plan,
                [AddProductReportCommand(workspace, report) for report in reports],
            )
            workspace.command_manager.execute(command)
            elapsed = (time.perf_counter() - started) * 1000.0
            self.statistics["successful"] += 1
            self.statistics["execution_time_ms"] += elapsed
            self.statistics["validation_statistics"] += len(plan.steps)
            self.statistics["optimization_statistics"] += 1
            self.statistics["reports_generated"] += len(reports)
            self._remember_session(session, plan, records)
            return AIAutomationResult(plan, records, command, generated_outputs, self.diagnostics())
        except Exception:
            self.statistics["failed"] += 1
            self.statistics["failure_statistics"] += 1
            raise

    def diagnostics(self):
        """Return AI Automation Studio diagnostics."""

        data = dict(self.statistics)
        data["last_plan_id"] = getattr(self.last_plan, "id", "")
        data["last_template"] = getattr(getattr(self.last_plan, "template", None), "name", "")
        return data

    def _build_templates(self):
        templates = {
            "Text → Parametric Model": WorkflowTemplate(
                "Text → Parametric Model",
                "Create an editable parametric CAD model from an engineering request.",
                ["parametric_design"],
                {"standard": "ISO"},
                {"model_prompt": "{user_goal}"},
            ),
            "Model → Drawings": WorkflowTemplate(
                "Model → Drawings",
                "Create associative engineering drawings for an existing model.",
                ["drawing"],
                {"standard": "ISO"},
                {"drawing_prompt": "{user_goal}"},
            ),
            "Model → Documentation": WorkflowTemplate(
                "Model → Documentation",
                "Create associative drawing-backed engineering and manufacturing documentation.",
                ["drawing", "documentation"],
                {"standard": "ISO"},
                {"documentation_prompt": "{user_goal}"},
            ),
            "Model → Design Review": WorkflowTemplate(
                "Model → Design Review",
                "Review an existing complete engineering package.",
                ["review"],
                {"standard": "ISO"},
                {"review_prompt": "{user_goal}"},
            ),
            "Complete Engineering Package": WorkflowTemplate(
                "Complete Engineering Package",
                "Create model, drawings, documentation and review as one deterministic engineering workflow.",
                ["parametric_design", "drawing", "documentation", "review"],
                {"standard": "ISO"},
                {"package_prompt": "{user_goal}"},
            ),
            "Manufacturing Preparation": WorkflowTemplate(
                "Manufacturing Preparation",
                "Prepare a manufacturing-aware model package with drawings, documents and review.",
                ["parametric_design", "drawing", "documentation", "review"],
                {"standard": "ISO", "manufacturing_focus": True},
                {"manufacturing_prompt": "{user_goal}"},
            ),
            "Concept Design": WorkflowTemplate(
                "Concept Design",
                "Create an editable concept model and production-readiness review trail.",
                ["parametric_design", "drawing", "documentation", "review"],
                {"standard": "ISO", "concept": True},
                {"concept_prompt": "{user_goal}"},
            ),
            "Mechanical Part": WorkflowTemplate(
                "Mechanical Part",
                "Create a complete mechanical part package.",
                ["parametric_design", "drawing", "documentation", "review"],
                {"standard": "ISO", "domain": "mechanical"},
                {"mechanical_prompt": "{user_goal}"},
            ),
            "Architectural Component": WorkflowTemplate(
                "Architectural Component",
                "Create a complete architectural component package.",
                ["parametric_design", "drawing", "documentation", "review"],
                {"standard": "ISO", "domain": "architecture"},
                {"architecture_prompt": "{user_goal}"},
            ),
            "Assembly": WorkflowTemplate(
                "Assembly",
                "Create an assembly-ready engineering package.",
                ["parametric_design", "drawing", "documentation", "review"],
                {"standard": "ISO", "assembly": True},
                {"assembly_prompt": "{user_goal}"},
            ),
            "Documentation Package": WorkflowTemplate(
                "Documentation Package",
                "Create documentation and review for an existing model/drawing package.",
                ["documentation", "review"],
                {"standard": "ISO"},
                {"documentation_prompt": "{user_goal}"},
            ),
            "Inspection Package": WorkflowTemplate(
                "Inspection Package",
                "Create inspection documentation and review for an existing engineering package.",
                ["documentation", "review"],
                {"standard": "ISO", "inspection": True},
                {"inspection_prompt": "{user_goal}"},
            ),
        }
        return templates

    def _template(self, template, prompt, workspace):
        requested = str(template or "").strip()
        if requested in self.templates:
            selected = self.templates[requested]
        else:
            selected = self.templates.get(self._template_from_prompt(prompt), self.templates["Complete Engineering Package"])
        if selected.name == "Complete Engineering Package":
            modules = list(selected.step_modules)
            if self._has_model(workspace):
                modules = [module for module in modules if module != "parametric_design"]
            return WorkflowTemplate(selected.name, selected.objective, modules, dict(selected.parameters), dict(selected.variables), selected.version, selected.id)
        return selected

    def _template_from_prompt(self, prompt):
        text = str(prompt or "").lower()
        if "inspection" in text:
            return "Inspection Package"
        if "documentation" in text and "drawing" not in text and "model" not in text:
            return "Documentation Package"
        if "drawing" in text and "documentation" not in text:
            return "Model → Drawings"
        if "review" in text and "package" not in text:
            return "Model → Design Review"
        if "manufacturing" in text:
            return "Manufacturing Preparation"
        if "architect" in text or "building" in text:
            return "Architectural Component"
        if "assembly" in text:
            return "Assembly"
        if "concept" in text:
            return "Concept Design"
        return "Complete Engineering Package"

    def _steps_for_template(self, template, workspace):
        steps = []
        for module in template.step_modules:
            steps.append(self._step_for_module(module))
        return steps

    def _step_for_module(self, module):
        definitions = {
            "parametric_design": WorkflowStep(
                "Parametric Design",
                "parametric_design",
                "execute_parametric_design",
                [],
                ["Design intent resolved", "Command sequence executable", "Editable feature tree generated"],
                "Undo last AI Parametric Designer command",
                ["Editable parametric model exists"],
            ),
            "drawing": WorkflowStep(
                "Engineering Drawing",
                "drawing",
                "execute_engineering_drawing",
                ["Editable parametric model"],
                ["Model references valid", "Drawing plan valid", "Associative report generated"],
                "Undo last AI Drawing Studio command",
                ["Associative drawing records exist"],
            ),
            "documentation": WorkflowStep(
                "Engineering Documentation",
                "documentation",
                "execute_engineering_documentation",
                ["Editable parametric model", "Associative engineering drawings"],
                ["Drawing references valid", "Documentation sections complete", "BOM validated"],
                "Undo last AI Documentation command",
                ["Associative documentation records exist"],
            ),
            "review": WorkflowStep(
                "Design Review",
                "review",
                "execute_design_review",
                ["Editable parametric model", "Associative engineering drawings", "Associative documentation"],
                ["Package references valid", "Risk report complete", "Recommendations generated"],
                "Undo last AI Design Review command",
                ["Associative design review report exists"],
            ),
        }
        return definitions[module]

    def _dependencies(self, steps):
        order = [step.module for step in steps]
        dependencies = {}
        for step in steps:
            index = order.index(step.module)
            dependencies[step.id] = [previous.id for previous in steps[:index]]
        return dependencies

    def _validate(self, workspace, steps):
        errors = []
        warnings = []
        if workspace is None:
            errors.append("Workspace is required for AI Automation Studio.")
            return WorkflowValidation(False, warnings, errors)
        product = getattr(workspace, "product_manager", None)
        if product is None:
            errors.append("ProductManager is required for AI Automation Studio.")
            return WorkflowValidation(False, warnings, errors)
        available = {
            "model": self._has_model(workspace),
            "drawing": self._has_drawing(workspace),
            "documentation": self._has_documentation(workspace),
            "review": self._has_review(workspace),
        }
        for step in steps:
            if step.module == "parametric_design":
                available["model"] = True
            elif step.module == "drawing":
                if not available["model"]:
                    errors.append("Engineering Drawing requires an editable parametric CAD model.")
                available["drawing"] = True
            elif step.module == "documentation":
                if not available["model"]:
                    errors.append("Engineering Documentation requires an editable parametric CAD model.")
                if not available["drawing"]:
                    errors.append("Engineering Documentation requires associative engineering drawings.")
                available["documentation"] = True
            elif step.module == "review":
                if not available["model"]:
                    errors.append("Design Review requires an editable parametric CAD model.")
                if not available["drawing"]:
                    errors.append("Design Review requires associative engineering drawings.")
                if not available["documentation"]:
                    errors.append("Design Review requires associative documentation.")
                available["review"] = True
        if len(steps) != len({step.module for step in steps}):
            errors.append("Workflow contains duplicate module execution.")
        if not steps:
            errors.append("Workflow has no executable steps.")
        return WorkflowValidation(not errors, warnings, errors)

    def _optimization(self, steps):
        modules = [step.module for step in steps]
        parallel = []
        if "documentation" in modules and "review" in modules:
            parallel.append("Design Review remains ordered after Documentation to preserve deterministic package validation.")
        redundant = []
        if modules.count("drawing") > 1:
            redundant.append("Duplicate drawing generation step removed by template validation.")
        improvements = ["Reuse existing AI module outputs as downstream prerequisites.", "Use command history as rollback checkpoints."]
        return WorkflowOptimization([], parallel, redundant, improvements, ["Only changed package records are added by the automation report command."])

    def _completion_criteria(self, steps):
        criteria = []
        for step in steps:
            criteria.extend(step.completion_criteria)
        criteria.append("Automation report stored through existing ProductReport system")
        return list(dict.fromkeys(criteria))

    def _execute_step(self, step, prompt, workspace, session, standard):
        start_time = datetime.now(timezone.utc).isoformat()
        started = time.perf_counter()
        try:
            before = self._workspace_reference_ids(workspace)
            if step.module == "parametric_design":
                self.ai_engine.execute_parametric_design(prompt, workspace, session)
            elif step.module == "drawing":
                self.ai_engine.execute_engineering_drawing(prompt, workspace, session, standard)
            elif step.module == "documentation":
                self.ai_engine.execute_engineering_documentation(prompt, workspace, session, standard)
            elif step.module == "review":
                self.ai_engine.execute_design_review(prompt, workspace, session, standard)
            else:
                raise TextToCADValidationError(f"Unsupported automation workflow module '{step.module}'.")
            after = self._workspace_reference_ids(workspace)
            outputs = [item for item in after if item not in before]
            self._verify_step(step, workspace)
            return WorkflowExecutionRecord(
                step.id,
                step.name,
                step.module,
                "completed",
                outputs,
                start_time,
                datetime.now(timezone.utc).isoformat(),
                (time.perf_counter() - started) * 1000.0,
            )
        except Exception as exc:
            self.statistics["recovery_statistics"] += 1
            return WorkflowExecutionRecord(
                step.id,
                step.name,
                step.module,
                "failed",
                [],
                start_time,
                datetime.now(timezone.utc).isoformat(),
                (time.perf_counter() - started) * 1000.0,
                ["Restart from failed step is available by rerunning the deterministic workflow after resolving the failure."],
                str(exc),
            )

    def _verify_step(self, step, workspace):
        if step.module == "parametric_design" and not self._has_model(workspace):
            raise TextToCADValidationError("Parametric Design step did not create an editable model.")
        if step.module == "drawing" and not self._has_drawing(workspace):
            raise TextToCADValidationError("Engineering Drawing step did not create associative drawing records.")
        if step.module == "documentation" and not self._has_documentation(workspace):
            raise TextToCADValidationError("Documentation step did not create associative documentation records.")
        if step.module == "review" and not self._has_review(workspace):
            raise TextToCADValidationError("Design Review step did not create an associative review report.")

    def _reports_for_execution(self, plan, records, generated_outputs):
        if any(record.status != "completed" for record in records):
            failed = [record for record in records if record.status != "completed"]
            raise TextToCADValidationError("; ".join(record.error or record.step_name for record in failed))
        source_ids = []
        for record in records:
            source_ids.extend(record.output_reference_ids)
        source_ids = list(dict.fromkeys([item for item in source_ids if item]))
        target_id = source_ids[0] if source_ids else ""
        timestamp = datetime.now(timezone.utc).isoformat()
        workflow_report = ProductReport(
            f"AI Automation Workflow - {plan.template.name}",
            target_id,
            source_ids,
            ReportMetadata("AI Automation Workflow", "Automation Library", "Stored", {
                "workflow_definition": plan.template.to_dict(),
                "workflow_plan": plan.to_dict(),
                "parameters": dict(plan.template.parameters),
                "variables": dict(plan.template.variables),
                "version": plan.template.version,
                "stored_at": timestamp,
            }),
        )
        execution_report = ProductReport(
            f"AI Automation Report - {plan.template.name}",
            target_id,
            source_ids + [workflow_report.id],
            ReportMetadata("AI Automation Report", "Automation Report", "Stored", {
                "workflow_plan": plan.to_dict(),
                "execution_history": [record.to_dict() for record in records],
                "generated_outputs": dict(generated_outputs),
                "validation": plan.validation.to_dict(),
                "optimization": plan.optimization.to_dict(),
                "completion_criteria": list(plan.completion_criteria),
                "explanation": dict(plan.explanation),
                "generated_at": timestamp,
            }),
        )
        return [workflow_report, execution_report]

    def _workspace_reference_ids(self, workspace):
        product = getattr(workspace, "product_manager", None)
        refs = []
        if product is not None:
            for name in ("parts", "features", "bodies", "sketches", "parameters", "expressions", "product_reports"):
                refs.extend(getattr(item, "id", "") for item in getattr(product, name, []) or [])
        project = getattr(getattr(workspace, "bim_manager", None), "active_project", None)
        if project is not None:
            refs.extend(getattr(item, "id", "") for item in getattr(project, "views", []) or [])
            refs.extend(getattr(item, "id", "") for item in getattr(project, "sheets", []) or [])
        return [ref for ref in refs if ref]

    def _has_model(self, workspace):
        product = getattr(workspace, "product_manager", None)
        if product is None:
            return False
        return bool(getattr(product, "parts", []) or getattr(product, "bodies", []) or getattr(product, "features", []))

    def _has_drawing(self, workspace):
        product = getattr(workspace, "product_manager", None)
        if product is not None:
            for report in getattr(product, "product_reports", []) or []:
                if getattr(getattr(report, "metadata", None), "report_type", "") == "AI Drawing Studio":
                    return True
        project = getattr(getattr(workspace, "bim_manager", None), "active_project", None)
        return bool(project is not None and (getattr(project, "views", []) or getattr(project, "sheets", [])))

    def _has_documentation(self, workspace):
        product = getattr(workspace, "product_manager", None)
        if product is None:
            return False
        for report in getattr(product, "product_reports", []) or []:
            report_type = getattr(getattr(report, "metadata", None), "report_type", "")
            if str(report_type).endswith("Documentation") or report_type in ("Bill of Materials", "Revision Documentation"):
                return True
        return False

    def _has_review(self, workspace):
        product = getattr(workspace, "product_manager", None)
        if product is None:
            return False
        return any(
            getattr(getattr(report, "metadata", None), "report_type", "") == "AI Design Review"
            for report in getattr(product, "product_reports", []) or []
        )

    def _explain(self, template, steps, standard, validation, optimization):
        return {
            "workflow_strategy": template.objective,
            "execution_order": [step.name for step in steps],
            "validation_logic": [point for step in steps for point in step.validation_points],
            "recovery_logic": [step.rollback_point for step in steps if step.rollback_point],
            "generated_outputs": [criteria for step in steps for criteria in step.completion_criteria],
            "warnings": list(validation.warnings),
            "recommendations": optimization.to_dict(),
            "standard": standard,
        }

    def _standard_name(self, standard):
        name = str(standard or "ISO").upper()
        if name not in self.STANDARDS:
            raise TextToCADValidationError(f"Unsupported automation standard '{standard}'.")
        return name

    def _remember_session(self, session, plan, records):
        if session is not None and hasattr(session, "add_message"):
            session.add_message(
                "assistant",
                f"AI Automation Studio completed. workflow_plan_id={plan.id} steps={len(records)}",
                "ai-automation-studio",
                plan.id,
            )
