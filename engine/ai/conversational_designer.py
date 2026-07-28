import re
import time
from dataclasses import dataclass, field
from uuid import uuid4

from engine.ai.text_to_cad import TextToCADValidationError
from engine.commands.ai_cad_command import AIParametricCADCommand
from engine.commands.product_command import (
    EditProductFeatureCommand,
    RegenerateProductFeatureCommand,
    RenameProductFeatureCommand,
    SuppressProductFeatureCommand,
)


@dataclass
class ConversationIntent:
    """Resolved engineering intent from one conversational user turn."""

    action: str
    object_type: str
    target_id: str = ""
    target_name: str = ""
    parameters: dict = field(default_factory=dict)
    confidence: float = 0.0
    requires_clarification: bool = False
    clarification_question: str = ""
    risks: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe intent metadata."""

        return {
            "id": self.id,
            "action": self.action,
            "object_type": self.object_type,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "parameters": dict(self.parameters),
            "confidence": self.confidence,
            "requires_clarification": self.requires_clarification,
            "clarification_question": self.clarification_question,
            "risks": list(self.risks),
        }


@dataclass
class ConversationContext:
    """Workspace and session context used for safe conversational planning."""

    selected_ids: list = field(default_factory=list)
    selected_types: list = field(default_factory=list)
    feature_ids: list = field(default_factory=list)
    feature_names: list = field(default_factory=list)
    parameter_ids: list = field(default_factory=list)
    drawing_report_ids: list = field(default_factory=list)
    documentation_report_ids: list = field(default_factory=list)
    review_report_ids: list = field(default_factory=list)
    automation_report_ids: list = field(default_factory=list)
    previous_action_ids: list = field(default_factory=list)

    def to_dict(self):
        """Return JSON-safe context metadata."""

        return {
            "selected_ids": list(self.selected_ids),
            "selected_types": list(self.selected_types),
            "feature_ids": list(self.feature_ids),
            "feature_names": list(self.feature_names),
            "parameter_ids": list(self.parameter_ids),
            "drawing_report_ids": list(self.drawing_report_ids),
            "documentation_report_ids": list(self.documentation_report_ids),
            "review_report_ids": list(self.review_report_ids),
            "automation_report_ids": list(self.automation_report_ids),
            "previous_action_ids": list(self.previous_action_ids),
        }


@dataclass
class ClarificationRequest:
    """Targeted engineering clarification instead of unsafe guessing."""

    question: str
    reason: str
    options: list = field(default_factory=list)
    blocking: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe clarification metadata."""

        return {
            "id": self.id,
            "question": self.question,
            "reason": self.reason,
            "options": list(self.options),
            "blocking": self.blocking,
        }


@dataclass
class DesignMemory:
    """Session-scoped conversational engineering memory."""

    workspace_id: str
    recent_operations: list = field(default_factory=list)
    named_parameters: dict = field(default_factory=dict)
    design_intent: list = field(default_factory=list)
    user_preferences: dict = field(default_factory=dict)
    engineering_assumptions: list = field(default_factory=list)
    pending_clarifications: list = field(default_factory=list)
    conversation_history: list = field(default_factory=list)

    def to_dict(self):
        """Return JSON-safe memory metadata."""

        return {
            "workspace_id": self.workspace_id,
            "recent_operations": list(self.recent_operations),
            "named_parameters": dict(self.named_parameters),
            "design_intent": list(self.design_intent),
            "user_preferences": dict(self.user_preferences),
            "engineering_assumptions": list(self.engineering_assumptions),
            "pending_clarifications": list(self.pending_clarifications),
            "conversation_history": list(self.conversation_history),
        }


@dataclass
class ConversationalCommandPlan:
    """Existing-command-only execution plan for one conversational turn."""

    command_type: str
    description: str
    command_count: int = 0
    target_ids: list = field(default_factory=list)
    affected_features: list = field(default_factory=list)
    affected_parameters: list = field(default_factory=list)
    affected_drawings: list = field(default_factory=list)
    affected_documentation: list = field(default_factory=list)

    def to_dict(self):
        """Return JSON-safe command-plan metadata."""

        return {
            "command_type": self.command_type,
            "description": self.description,
            "command_count": self.command_count,
            "target_ids": list(self.target_ids),
            "affected_features": list(self.affected_features),
            "affected_parameters": list(self.affected_parameters),
            "affected_drawings": list(self.affected_drawings),
            "affected_documentation": list(self.affected_documentation),
        }


@dataclass
class ConversationalPlan:
    """Production conversational designer plan for a user turn."""

    prompt: str
    intent: ConversationIntent
    context: ConversationContext
    command_plan: ConversationalCommandPlan
    memory: dict
    clarification: ClarificationRequest = None
    validation: dict = field(default_factory=dict)
    explanation_before: dict = field(default_factory=dict)
    diagnostics: dict = field(default_factory=dict)
    command_label: str = "Conversational AI Designer"
    object_type: str = "Conversational AI Designer"
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe conversational plan metadata."""

        return {
            "id": self.id,
            "prompt": self.prompt,
            "intent": self.intent.to_dict(),
            "context": self.context.to_dict(),
            "command_plan": self.command_plan.to_dict(),
            "memory": dict(self.memory),
            "clarification": self.clarification.to_dict() if self.clarification else None,
            "validation": dict(self.validation),
            "explanation_before": dict(self.explanation_before),
            "diagnostics": dict(self.diagnostics),
        }


@dataclass
class ConversationalResult:
    """Result of executing or clarifying one conversational design turn."""

    plan: ConversationalPlan
    executed: bool
    command: object = None
    clarification: ClarificationRequest = None
    explanation_after: dict = field(default_factory=dict)
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe conversational result metadata."""

        return {
            "plan": self.plan.to_dict(),
            "executed": self.executed,
            "command": getattr(self.command, "name", "") if self.command is not None else "",
            "clarification": self.clarification.to_dict() if self.clarification else None,
            "explanation_after": dict(self.explanation_after),
            "diagnostics": dict(self.diagnostics),
        }


class ConversationalAIDesigner:
    """Natural-language designer that executes only through existing command paths."""

    def __init__(self, ai_engine):

        self.ai_engine = ai_engine
        self.memories = {}
        self.statistics = {
            "conversation_count": 0,
            "intent_resolution_statistics": 0,
            "clarification_statistics": 0,
            "command_statistics": 0,
            "execution_statistics": 0,
            "conflict_statistics": 0,
            "validation_statistics": 0,
            "failed": 0,
        }
        self.last_plan = None

    def plan(self, prompt, workspace, session=None, execute=True, standard="ISO"):
        """Plan a conversational design turn without mutating the workspace."""

        started = time.perf_counter()
        memory = self._memory(workspace, session)
        context = self._context(workspace, memory)
        intent = self._intent(prompt, workspace, context, memory)
        self._update_preferences(prompt, memory)
        clarification = self._clarification(intent, context)
        if clarification is not None:
            intent.requires_clarification = True
            intent.clarification_question = clarification.question
        command_plan = self._command_plan(intent, context, clarification)
        validation = self._validate(workspace, intent, command_plan, clarification)
        diagnostics = {
            "planning_time_ms": (time.perf_counter() - started) * 1000.0,
            "selected": len(context.selected_ids),
            "features": len(context.feature_ids),
            "reports": len(context.drawing_report_ids) + len(context.documentation_report_ids) + len(context.review_report_ids),
        }
        plan = ConversationalPlan(
            prompt,
            intent,
            context,
            command_plan,
            memory.to_dict(),
            clarification,
            validation,
            self._explain_before(intent, command_plan, clarification),
            diagnostics,
        )
        self.last_plan = plan
        return plan

    def execute(self, prompt, workspace, session=None, standard="ISO"):
        """Execute one conversational turn through existing commands or ask for clarification."""

        self.statistics["conversation_count"] += 1
        try:
            plan = self.plan(prompt, workspace, session, True, standard)
            self.statistics["intent_resolution_statistics"] += 1
            self.statistics["validation_statistics"] += 1
            if plan.clarification is not None:
                self.statistics["clarification_statistics"] += 1
                self._remember_turn(workspace, session, plan, None, False)
                return ConversationalResult(plan, False, None, plan.clarification, self._explain_after(plan, None, False), self.diagnostics())
            if not plan.validation.get("valid", False):
                self.statistics["conflict_statistics"] += 1
                raise TextToCADValidationError("; ".join(plan.validation.get("errors", [])))
            command = self._execute_plan(plan, prompt, workspace, session, standard)
            self.statistics["execution_statistics"] += 1
            self.statistics["command_statistics"] += plan.command_plan.command_count
            self._remember_turn(workspace, session, plan, command, True)
            return ConversationalResult(plan, True, command, None, self._explain_after(plan, command, True), self.diagnostics())
        except Exception:
            self.statistics["failed"] += 1
            raise

    def diagnostics(self):
        """Return Conversational AI Designer diagnostics."""

        data = dict(self.statistics)
        data["active_memories"] = len(self.memories)
        data["last_plan_id"] = getattr(self.last_plan, "id", "")
        data["last_intent"] = getattr(getattr(self.last_plan, "intent", None), "action", "")
        return data

    def _execute_plan(self, plan, prompt, workspace, session, standard):
        action = plan.intent.action
        if action == "create":
            self.ai_engine.execute_parametric_design(prompt, workspace, session)
            return self._last_command(workspace)
        if action == "automation":
            result = self.ai_engine.execute_automation_workflow(prompt, workspace, session, "Complete Engineering Package", standard)
            return result.command
        if action == "drawing":
            result = self.ai_engine.execute_engineering_drawing(prompt, workspace, session, standard)
            return result.command
        if action == "documentation":
            result = self.ai_engine.execute_engineering_documentation(prompt, workspace, session, standard)
            return result.command
        if action == "review":
            result = self.ai_engine.execute_design_review(prompt, workspace, session, standard)
            return result.command
        if action == "inspect":
            self.ai_engine.review_engineering_package(prompt, workspace, session, standard)
            return None
        commands = self._edit_commands(plan.intent, workspace)
        command = AIParametricCADCommand(workspace, plan, commands)
        workspace.command_manager.execute(command)
        return command

    def _last_command(self, workspace):
        command_manager = getattr(workspace, "command_manager", None)
        history = list(getattr(command_manager, "undo_stack", []) or []) if command_manager is not None else []
        return history[-1] if history else None

    def _edit_commands(self, intent, workspace):
        feature = self._feature_for_id(workspace, intent.target_id)
        if feature is None:
            raise TextToCADValidationError("Conversational edit requires an existing feature target.")
        if intent.action == "rename":
            return [RenameProductFeatureCommand(workspace, feature, intent.parameters["name"])]
        if intent.action == "suppress":
            return [SuppressProductFeatureCommand(workspace, feature, True)]
        if intent.action == "unsuppress":
            return [SuppressProductFeatureCommand(workspace, feature, False)]
        if intent.action == "regenerate":
            return [RegenerateProductFeatureCommand(workspace, feature, True)]
        if intent.action == "edit_feature":
            return [EditProductFeatureCommand(workspace, feature, **intent.parameters)]
        raise TextToCADValidationError(f"Unsupported conversational command action '{intent.action}'.")

    def _intent(self, prompt, workspace, context, memory):
        text = str(prompt or "").strip()
        lower = text.lower()
        target = self._resolve_target(lower, workspace, context, memory)
        preferences = self._preferences_from_prompt(lower)
        if "complete engineering package" in lower or "automation" in lower or "workflow" in lower:
            return ConversationIntent("automation", "Workflow", parameters=preferences, confidence=0.92)
        if any(word in lower for word in ("drawing", "drawings", "sheet", "dimensioned view")) and "review" not in lower:
            return ConversationIntent("drawing", "Drawing", parameters=preferences, confidence=0.86)
        if any(word in lower for word in ("documentation", "bom", "inspection plan", "manufacturing document")):
            return ConversationIntent("documentation", "Documentation", parameters=preferences, confidence=0.86)
        if any(word in lower for word in ("review", "inspect", "score", "risk")):
            action = "inspect" if "inspect" in lower and "report" not in lower else "review"
            return ConversationIntent(action, "Engineering Package", parameters=preferences, confidence=0.84)
        if any(word in lower for word in ("unsuppress", "resume", "enable")):
            return self._targeted_intent("unsuppress", target, preferences, 0.88)
        if any(word in lower for word in ("suppress", "disable")):
            return self._targeted_intent("suppress", target, preferences, 0.88)
        if any(word in lower for word in ("rebuild", "regenerate")):
            return self._targeted_intent("regenerate", target, preferences, 0.86)
        if "rename" in lower:
            name = self._quoted_value(text) or self._after_keyword(text, "to")
            params = dict(preferences)
            if name:
                params["name"] = name
            return self._targeted_intent("rename", target, params, 0.82)
        if any(word in lower for word in ("increase", "reduce", "decrease", "modify", "change")) and any(word in lower for word in ("thickness", "diameter", "height", "distance", "depth")):
            params = self._edit_parameters(lower)
            params.update(preferences)
            return self._targeted_intent("edit_feature", target, params, 0.8)
        if any(word in lower for word in ("create", "make", "build", "design", "generate")):
            return ConversationIntent("create", self._object_type(lower), parameters=preferences, confidence=0.9)
        return ConversationIntent(
            "clarify",
            "Engineering Request",
            parameters=preferences,
            confidence=0.35,
            requires_clarification=True,
            clarification_question="What engineering change should I make, and which model object should it affect?",
            risks=["Ambiguous conversational request"],
        )

    def _targeted_intent(self, action, target, parameters, confidence):
        target_id = getattr(target, "id", "")
        target_name = getattr(target, "name", "")
        return ConversationIntent(action, "Feature", target_id, target_name, parameters, confidence)

    def _clarification(self, intent, context):
        if intent.requires_clarification:
            return ClarificationRequest(intent.clarification_question, "The request does not contain enough engineering intent to plan a safe command.")
        if intent.action in ("rename", "suppress", "unsuppress", "regenerate", "edit_feature") and not intent.target_id:
            return ClarificationRequest(
                "Which feature should I modify?",
                "Feature edits require a selected feature, a named feature, or a recent feature from the conversation memory.",
                context.feature_names[-5:],
            )
        if intent.action == "rename" and not intent.parameters.get("name"):
            return ClarificationRequest("What should the feature be renamed to?", "Rename commands require an explicit target name.")
        if intent.action == "edit_feature" and "distance" not in intent.parameters:
            return ClarificationRequest("What target dimension should I apply?", "Dimension edits require an explicit numeric value and unit.")
        if intent.action in ("drawing", "documentation", "review", "inspect") and not context.feature_ids:
            return ClarificationRequest("Which existing model should I use?", "This request requires an editable parametric model in the Workspace.")
        return None

    def _command_plan(self, intent, context, clarification):
        if clarification is not None:
            return ConversationalCommandPlan("clarification", "Ask a targeted engineering clarification before command generation.")
        descriptions = {
            "create": "Create an editable parametric model through AI Parametric Designer.",
            "automation": "Run the existing Automation Studio complete package workflow.",
            "drawing": "Create associative engineering drawings through AI Drawing Studio.",
            "documentation": "Create associative engineering documentation through AI Documentation.",
            "review": "Create an associative design review report through AI Design Review.",
            "inspect": "Analyze the package without mutating Workspace data.",
            "rename": "Rename the resolved feature through RenameProductFeatureCommand.",
            "suppress": "Suppress the resolved feature through SuppressProductFeatureCommand.",
            "unsuppress": "Unsuppress the resolved feature through SuppressProductFeatureCommand.",
            "regenerate": "Regenerate the resolved feature through RegenerateProductFeatureCommand.",
            "edit_feature": "Edit resolved feature parameters through EditProductFeatureCommand.",
        }
        command_count = 0 if intent.action == "inspect" else 1
        return ConversationalCommandPlan(
            intent.action,
            descriptions.get(intent.action, "Plan existing commands for the resolved engineering intent."),
            command_count,
            [intent.target_id] if intent.target_id else [],
            [intent.target_id] if intent.object_type == "Feature" and intent.target_id else [],
            list(intent.parameters.keys()),
            list(context.drawing_report_ids),
            list(context.documentation_report_ids),
        )

    def _validate(self, workspace, intent, command_plan, clarification):
        errors = []
        warnings = []
        if workspace is None:
            errors.append("Workspace is required for Conversational AI Designer.")
        if clarification is not None:
            warnings.append("Execution paused for clarification.")
        if command_plan.command_type not in {
            "clarification", "create", "automation", "drawing", "documentation", "review", "inspect",
            "rename", "suppress", "unsuppress", "regenerate", "edit_feature",
        }:
            errors.append(f"Unsupported command plan '{command_plan.command_type}'.")
        if intent.action in ("rename", "suppress", "unsuppress", "regenerate", "edit_feature") and not intent.target_id:
            errors.append("Feature edit command requires a resolved target feature.")
        return {"valid": not errors and clarification is None, "warnings": warnings, "errors": errors}

    def _context(self, workspace, memory):
        product = getattr(workspace, "product_manager", None)
        selection = getattr(workspace, "selection", None)
        selected = list(getattr(selection, "selected", []) or [])
        reports = list(getattr(product, "product_reports", []) or []) if product is not None else []
        features = list(getattr(product, "features", []) or []) if product is not None else []
        parameters = list(getattr(product, "parameters", []) or []) if product is not None else []
        return ConversationContext(
            [getattr(item, "id", "") for item in selected if getattr(item, "id", "")],
            [getattr(item, "type_name", item.__class__.__name__) for item in selected],
            [getattr(item, "id", "") for item in features],
            [getattr(item, "name", "") for item in features],
            [getattr(item, "id", "") for item in parameters],
            [report.id for report in reports if getattr(getattr(report, "metadata", None), "report_type", "") == "AI Drawing Studio"],
            [report.id for report in reports if str(getattr(getattr(report, "metadata", None), "report_type", "")).endswith("Documentation")],
            [report.id for report in reports if getattr(getattr(report, "metadata", None), "report_type", "") == "AI Design Review"],
            [report.id for report in reports if getattr(getattr(report, "metadata", None), "report_type", "") in ("AI Automation Workflow", "AI Automation Report")],
            [item.get("plan_id", "") for item in memory.recent_operations],
        )

    def _resolve_target(self, lower, workspace, context, memory):
        product = getattr(workspace, "product_manager", None)
        if product is None:
            return None
        features = list(getattr(product, "features", []) or [])
        selected_ids = set(context.selected_ids)
        selected_feature = next((feature for feature in features if feature.id in selected_ids), None)
        if selected_feature is not None and any(word in lower for word in ("this", "selected", "that", "it", "feature")):
            return selected_feature
        for feature in features:
            name = str(getattr(feature, "name", "")).lower()
            if name and name in lower:
                return feature
        if any(word in lower for word in ("last", "it", "that", "feature")):
            for operation in reversed(memory.recent_operations):
                for ref in reversed(operation.get("affected_features", []) or []):
                    feature = self._feature_for_id(workspace, ref)
                    if feature is not None:
                        return feature
        if len(features) == 1:
            return features[0]
        return selected_feature

    def _feature_for_id(self, workspace, feature_id):
        product = getattr(workspace, "product_manager", None)
        if product is None or not feature_id:
            return None
        return product.feature_manager.feature_for(feature_id)

    def _edit_parameters(self, lower):
        params = {}
        value, unit = self._dimension_value(lower)
        if value is not None:
            params["distance"] = value
            params["unit"] = unit or "mm"
        if "reduce" in lower or "decrease" in lower:
            params["edit_direction"] = "decrease"
        elif "increase" in lower:
            params["edit_direction"] = "increase"
        else:
            params["edit_direction"] = "set"
        return params

    def _dimension_value(self, lower):
        match = re.search(r"(-?\d+(?:\.\d+)?)\s*(mm|millimeter|millimeters|cm|m|inch|inches|in)?", lower)
        if not match:
            return None, ""
        value = float(match.group(1))
        unit = match.group(2) or "mm"
        unit_map = {"millimeter": "mm", "millimeters": "mm", "inch": "in", "inches": "in"}
        return value, unit_map.get(unit, unit)

    def _quoted_value(self, text):
        match = re.search(r"[\"']([^\"']+)[\"']", text)
        return match.group(1).strip() if match else ""

    def _after_keyword(self, text, keyword):
        parts = re.split(rf"\b{re.escape(keyword)}\b", text, flags=re.IGNORECASE)
        if len(parts) < 2:
            return ""
        return parts[-1].strip(" .")

    def _object_type(self, lower):
        for name in ("bracket", "flange", "box", "enclosure", "shaft", "lamp", "table", "wall", "staircase"):
            if name in lower:
                return name.title()
        return "Parametric Model"

    def _preferences_from_prompt(self, lower):
        preferences = {}
        for unit in ("mm", "cm", "inch", "inches"):
            if re.search(rf"\b{unit}\b", lower):
                preferences["preferred_units"] = "in" if unit in ("inch", "inches") else unit
        for standard in ("iso", "ansi", "din", "jis", "bs"):
            if standard in lower:
                preferences["preferred_standard"] = standard.upper()
        for process in ("cnc", "3d printing", "laser", "waterjet", "injection molding", "sheet metal"):
            if process in lower:
                preferences["preferred_manufacturing_process"] = process
        if "brief" in lower:
            preferences["preferred_explanation_depth"] = "brief"
        if "detailed" in lower:
            preferences["preferred_explanation_depth"] = "detailed"
        return preferences

    def _update_preferences(self, prompt, memory):
        preferences = self._preferences_from_prompt(str(prompt or "").lower())
        memory.user_preferences.update(preferences)

    def _memory(self, workspace, session):
        key = f"{getattr(workspace, 'name', 'workspace')}:{getattr(session, 'id', 'default')}"
        if key not in self.memories:
            self.memories[key] = DesignMemory(getattr(workspace, "name", "workspace"))
        return self.memories[key]

    def _remember_turn(self, workspace, session, plan, command, executed):
        memory = self._memory(workspace, session)
        entry = {
            "plan_id": plan.id,
            "prompt": plan.prompt,
            "action": plan.intent.action,
            "target_id": plan.intent.target_id,
            "affected_features": list(plan.command_plan.affected_features),
            "executed": executed,
            "command": getattr(command, "name", "") if command is not None else "",
        }
        memory.recent_operations.append(entry)
        memory.recent_operations = memory.recent_operations[-20:]
        if plan.intent.object_type:
            memory.design_intent.append(plan.intent.object_type)
            memory.design_intent = memory.design_intent[-20:]
        if plan.clarification is not None:
            memory.pending_clarifications.append(plan.clarification.to_dict())
        memory.conversation_history.append({"role": "user", "content": plan.prompt, "plan_id": plan.id})
        memory.conversation_history = memory.conversation_history[-40:]
        if session is not None and hasattr(session, "add_message"):
            message = plan.clarification.question if plan.clarification else f"Conversational AI Designer completed. plan_id={plan.id}"
            session.add_message("assistant", message, "conversational-ai-designer", plan.id)

    def _explain_before(self, intent, command_plan, clarification):
        return {
            "requested_change": intent.action,
            "engineering_interpretation": intent.to_dict(),
            "commands_planned": command_plan.to_dict(),
            "potential_risks": list(intent.risks),
            "clarification": clarification.to_dict() if clarification else None,
        }

    def _explain_after(self, plan, command, executed):
        return {
            "requested_change": plan.intent.action,
            "commands_executed": getattr(command, "name", "") if command is not None else "",
            "affected_features": list(plan.command_plan.affected_features),
            "affected_parameters": list(plan.command_plan.affected_parameters),
            "affected_drawings": list(plan.command_plan.affected_drawings),
            "affected_documentation": list(plan.command_plan.affected_documentation),
            "affected_manufacturing_outputs": [],
            "potential_risks": list(plan.intent.risks),
            "executed": executed,
        }
