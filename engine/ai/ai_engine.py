from engine.ai.automation import AIAutomationStudio
from engine.ai.conversational_designer import ConversationalAIDesigner
from engine.ai.context import AIContextEngine
from engine.ai.design_review import AIDesignReview
from engine.ai.documentation import AIDocumentation
from engine.ai.drawing_studio import AIDrawingStudio
from engine.ai.engineering_simulation_assistant import AIEngineeringSimulationAssistant
from engine.ai.generative_design import AIGenerativeDesignEngine
from engine.ai.manufacturing_assistant import AIManufacturingAssistant
from engine.ai.parametric_designer import AIParametricDesigner
from engine.ai.production_runtime import AIStudioProductionRuntime
from engine.ai.provider_adapters import production_provider_adapters
from engine.ai.prompts import PromptLibrary
from engine.ai.providers import AICredentialStore, AIProviderRegistry
from engine.ai.runtime import AIProviderNotConfiguredError, AIRuntime
from engine.ai.session import AISessionStore
from engine.ai.text_to_cad import TextToParametricCADEngine
from engine.commands.command import Command
from datetime import datetime, timezone


def _timestamp():
    return datetime.now(timezone.utc).isoformat()


class AIEngine:
    """Production AI Studio facade; providers execute AI, commands modify CAD."""

    def __init__(self):
        self.credential_store = AICredentialStore()
        self.providers = AIProviderRegistry()
        self.context_engine = AIContextEngine()
        self.sessions = AISessionStore()
        self.prompts = PromptLibrary()
        self.runtime = AIRuntime(self.providers)
        self.text_to_cad = TextToParametricCADEngine()
        self.parametric_designer = AIParametricDesigner(self.text_to_cad)
        self.generative_design = AIGenerativeDesignEngine(self.parametric_designer)
        self.drawing_studio = AIDrawingStudio(self.generative_design)
        self.documentation = AIDocumentation(self.drawing_studio)
        self.design_review = AIDesignReview(self.documentation)
        self.automation_studio = AIAutomationStudio(self)
        self.conversational_designer = ConversationalAIDesigner(self)
        self.manufacturing_assistant = AIManufacturingAssistant(self)
        self.engineering_simulation_assistant = AIEngineeringSimulationAssistant(self)
        self.production_runtime = AIStudioProductionRuntime(self)
        self.infrastructure_settings = {
            "approval_required_for_geometry": True,
            "persist_temporary_execution_state": False,
            "provider_agnostic": True,
        }
        self.context_snapshots = []
        self.validation_history = []
        self.execution_log = []
        self.result_cache = {}
        self._register_production_adapters()

    def _register_production_adapters(self, configuration=None):
        """Register production provider adapters exactly once."""

        for provider in production_provider_adapters(configuration or {}, self.credential_store):
            if provider.provider_id not in self.providers.providers:
                self.providers.register(provider)

    def register_provider(self, provider):
        """Register a real AI provider."""

        return self.providers.register(provider)

    def providers_available(self):
        """Return registered provider metadata."""

        return self.providers.discover()

    def switch_provider(self, provider_id):
        """Switch the active AI provider."""

        return self.providers.switch(provider_id)

    def configure_provider(self, provider_id, **settings):
        """Configure a registered production provider."""

        provider = self.providers.providers.get(provider_id)
        if provider is None:
            raise AIProviderNotConfiguredError(f"AI provider '{provider_id}' is not registered.")
        secrets = {}
        for key in list(settings.keys()):
            if key in ("api_key", "access_token", "secret"):
                secrets[key] = settings.pop(key)
        if secrets:
            provider.authenticate(secrets)
        provider.configure(**settings)
        provider.initialize()
        return provider

    def validate_provider(self, provider_id):
        """Validate a provider connection."""

        provider = self.providers.providers.get(provider_id)
        if provider is None:
            raise AIProviderNotConfiguredError(f"AI provider '{provider_id}' is not registered.")
        return provider.validate_connection()

    def validate_providers(self):
        """Validate all configured providers and safely report failures."""

        return self.providers.validate_all()

    def shutdown_providers(self):
        """Shutdown all provider adapters."""

        return self.providers.shutdown_all()

    def build_context(self, workspace, include_history=True):
        """Build a Workspace-derived AI context snapshot."""

        return self.context_engine.build(workspace, include_history)

    def capture_context(self, workspace, include_history=True, label="AI Context"):
        """Capture a read-only AI context snapshot from the active Workspace."""

        snapshot = {
            "id": f"context-{len(self.context_snapshots) + 1}",
            "label": label,
            "created_at": _timestamp(),
            "context": self.build_context(workspace, include_history),
        }
        self.context_snapshots.append(snapshot)
        self.execution_log.append({
            "type": "context_captured",
            "snapshot_id": snapshot["id"],
            "timestamp": snapshot["created_at"],
        })
        return snapshot

    def validate_prompt(self, prompt, capability="chat"):
        """Validate an AI prompt without contacting a provider."""

        text = str(prompt or "").strip()
        errors = []
        warnings = []
        if not text:
            errors.append("Prompt is required.")
        if len(text) > 12000:
            warnings.append("Prompt is large and may exceed some provider context windows.")
        report = {
            "id": f"prompt-validation-{len(self.validation_history) + 1}",
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "capability": capability,
            "timestamp": _timestamp(),
        }
        self.validation_history.append(report)
        return report

    def create_session(self, name="AI Session", workspace=None, project_path=""):
        """Create an AI conversation session."""

        session = self.sessions.create(name, workspace, project_path)
        if workspace is not None:
            session.refresh_context(self.build_context(workspace))
        self.execution_log.append({
            "type": "session_created",
            "session_id": session.id,
            "timestamp": _timestamp(),
        })
        return session

    def reset_session(self, session=None):
        """Reset an AI session conversation history."""

        active = self.sessions.session_for(session) if isinstance(session, str) else (session or self.sessions.active())
        if active is None:
            return False
        previous = [message.to_dict() for message in active.messages]
        active.messages.clear()
        active.updated_at = _timestamp()
        self.execution_log.append({"type": "session_reset", "session_id": active.id, "timestamp": active.updated_at})
        return previous

    def submit_prompt_task(self, prompt, workspace=None, session=None, provider_id="", capability="chat", background=False):
        """Validate and submit a prompt task while preserving error diagnostics."""

        validation = self.validate_prompt(prompt, capability)
        context = self.build_context(workspace) if workspace is not None else {}
        active_session = self.sessions.session_for(session) if isinstance(session, str) else session
        if active_session is None:
            active_session = self.create_session("AI Infrastructure Session", workspace)
        if validation["valid"]:
            active_session.add_message("user", prompt)
        if not validation["valid"]:
            task = self.runtime.submit(prompt, context, capability, provider_id, background=True)
            self.runtime.cancel(task.id)
            task.error = "; ".join(validation["errors"])
            task.state = "Failed"
        else:
            try:
                task = self.runtime.submit(prompt, context, capability, provider_id, background=background)
            except Exception:
                task = list(self.runtime.tasks.values())[-1]
            if not background and task.error:
                active_session.add_message("assistant", task.error, task.provider_id, task.id)
            elif not background and task.result is not None:
                active_session.add_message("assistant", str(task.result), task.provider_id, task.id)
        self.result_cache[task.id] = {
            "state": task.state,
            "result": task.result,
            "error": task.error,
            "timestamp": _timestamp(),
        }
        self.execution_log.append({
            "type": "task_submitted",
            "task_id": task.id,
            "state": task.state,
            "timestamp": _timestamp(),
        })
        return task

    def retry_task(self, task_id, workspace=None, session=None):
        """Retry a previous prompt task using the same prompt/capability metadata."""

        previous = self.runtime.task_for(task_id)
        if previous is None:
            raise ValueError("AI task was not found.")
        return self.submit_prompt_task(
            previous.prompt,
            workspace,
            session,
            previous.provider_id,
            previous.capability,
            background=False,
        )

    def execute(self, prompt, workspace=None, session=None, provider_id="", capability="chat", background=False):
        """Execute an AI prompt using a configured production provider."""

        context = self.build_context(workspace) if workspace is not None else {}
        active_session = self.sessions.session_for(session) if isinstance(session, str) else session
        if active_session is not None:
            active_session.add_message("user", prompt)
            active_session.refresh_context(context)
        task = self.runtime.submit(
            prompt,
            context,
            capability,
            provider_id,
            background=background,
        )
        if background:
            return task
        if task.error:
            raise AIProviderNotConfiguredError(task.error)
        if active_session is not None:
            active_session.add_message("assistant", str(task.result), task.provider_id, task.id)
        return task.result

    def cancel(self, task_id):
        """Cancel a running AI task."""

        cancelled = self.runtime.cancel(task_id)
        self.execution_log.append({
            "type": "task_cancelled",
            "task_id": task_id,
            "cancelled": cancelled,
            "timestamp": _timestamp(),
        })
        return cancelled

    def execute_commands(self, workspace, commands):
        """Apply AI-proposed CAD changes through the existing Command System only."""

        if workspace is None:
            raise ValueError("workspace is required")
        for command in commands:
            if not isinstance(command, Command):
                raise TypeError("AI command integration only accepts Command instances.")
            workspace.command_manager.execute(command)
        return True

    def plan_parametric_cad(self, prompt, workspace=None, session=None):
        """Plan editable parametric CAD commands from engineering language."""

        return self.text_to_cad.plan(prompt, workspace, session)

    def execute_parametric_cad(self, prompt, workspace, session=None):
        """Execute text-to-parametric CAD through the existing Command System."""

        return self.text_to_cad.execute(prompt, workspace, session)

    def design_parametric_model(self, prompt, workspace=None, session=None):
        """Plan a complete manufacturing-aware parametric CAD model."""

        return self.parametric_designer.design(prompt, workspace, session)

    def execute_parametric_design(self, prompt, workspace, session=None):
        """Execute an AI Parametric Designer model through the Command System."""

        return self.parametric_designer.execute(prompt, workspace, session)

    def generate_design_alternatives(self, prompt, workspace=None, session=None, count=3, priorities=None):
        """Generate ranked editable parametric design alternatives."""

        return self.generative_design.generate(prompt, workspace, session, count, priorities)

    def execute_generative_design(self, prompt, workspace, session=None, count=3, priorities=None):
        """Execute generated design alternatives through the Command System."""

        return self.generative_design.execute(prompt, workspace, session, count, priorities)

    def plan_engineering_drawing(self, prompt, workspace, session=None, standard="ISO"):
        """Plan an associative engineering drawing for an existing parametric model."""

        return self.drawing_studio.plan(prompt, workspace, session, standard)

    def execute_engineering_drawing(self, prompt, workspace, session=None, standard="ISO"):
        """Create an associative engineering drawing through the existing Command System."""

        return self.drawing_studio.execute(prompt, workspace, session, standard)

    def plan_engineering_documentation(self, prompt, workspace, session=None, standard="ISO"):
        """Plan associative engineering and manufacturing documentation."""

        return self.documentation.plan(prompt, workspace, session, standard)

    def execute_engineering_documentation(self, prompt, workspace, session=None, standard="ISO"):
        """Create associative documentation through the existing Command System."""

        return self.documentation.execute(prompt, workspace, session, standard)

    def review_engineering_package(self, prompt, workspace, session=None, standard="ISO"):
        """Analyze the complete engineering package without mutating project data."""

        return self.design_review.plan(prompt, workspace, session, standard)

    def execute_design_review(self, prompt, workspace, session=None, standard="ISO"):
        """Store an associative design review report through the existing Command System."""

        return self.design_review.execute(prompt, workspace, session, standard)

    def plan_automation_workflow(self, prompt, workspace, session=None, template="Complete Engineering Package", standard="ISO"):
        """Plan a deterministic AI Automation Studio workflow."""

        return self.automation_studio.plan(prompt, workspace, session, template, standard)

    def execute_automation_workflow(self, prompt, workspace, session=None, template="Complete Engineering Package", standard="ISO"):
        """Execute an AI Automation Studio workflow through existing AI modules."""

        return self.automation_studio.execute(prompt, workspace, session, template, standard)

    def plan_conversational_design(self, prompt, workspace, session=None, execute=True, standard="ISO"):
        """Plan one Conversational AI Designer turn."""

        return self.conversational_designer.plan(prompt, workspace, session, execute, standard)

    def execute_conversational_design(self, prompt, workspace, session=None, standard="ISO"):
        """Execute or clarify one Conversational AI Designer turn."""

        return self.conversational_designer.execute(prompt, workspace, session, standard)

    def initialize_manufacturing_assistant(self, workspace):
        """Initialize AI Manufacturing Assistant against the existing Workspace."""

        return self.manufacturing_assistant.initialize(workspace)

    def plan_manufacturing_workflow(self, prompt, workspace, session=None, job=None):
        """Plan manufacturing workflow orchestration using existing systems only."""

        active_session = session
        if active_session is None:
            active_session = self.manufacturing_assistant.start_session(workspace)
        intent = self.manufacturing_assistant.interpret_request(prompt, workspace, active_session)
        return self.manufacturing_assistant.plan_workflow(intent, workspace, job)

    def advise_manufacturing(self, prompt, workspace, session=None, job=None):
        """Return manufacturing intent, workflow, validation and recommendation metadata."""

        return self.manufacturing_assistant.respond(prompt, workspace, session, job)

    def orchestrate_manufacturing_execution(self, plan, workspace, connection=None, approved=False, approved_by=""):
        """Coordinate approved machine dispatch through the existing Manufacturing Engine."""

        return self.manufacturing_assistant.orchestrate_execution(plan, workspace, connection, approved, approved_by)

    def initialize_engineering_simulation_assistant(self, workspace):
        """Initialize AI Engineering Simulation Assistant against the existing Workspace."""

        return self.engineering_simulation_assistant.initialize(workspace)

    def recommend_simulation_studies(self, prompt, workspace, session=None):
        """Recommend engineering simulation studies using existing Simulation Workspace context."""

        return self.engineering_simulation_assistant.recommend_studies(prompt, workspace, session)

    def configure_engineering_simulation(self, prompt, workspace, session=None, study=None):
        """Return AI guidance for configuring existing simulation studies."""

        return self.engineering_simulation_assistant.configure_simulation(prompt, workspace, session, study)

    def review_engineering_simulation_setup(self, workspace, session=None, study=None):
        """Review existing simulation setup without mutating geometry."""

        return self.engineering_simulation_assistant.review_setup(workspace, session, study)

    def interpret_engineering_simulation_results(self, workspace, session=None, study=None):
        """Interpret existing simulation results from the Results Database."""

        return self.engineering_simulation_assistant.interpret_results(workspace, session, study)

    def advise_engineering_simulation(self, prompt, workspace, session=None, study=None):
        """Run the full AI Engineering Simulation Assistant workflow."""

        return self.engineering_simulation_assistant.respond(prompt, workspace, session, study)

    def execute_engineering_simulation_study(self, workspace, study, approved=False, approved_by=""):
        """Execute simulation only through existing command wrappers after approval."""

        return self.engineering_simulation_assistant.execute_study_through_commands(workspace, study, approved, approved_by)

    def validate_ai_runtime(self, workspace=None):
        """Validate AI Studio production runtime readiness."""

        return self.production_runtime.validate_runtime(workspace)

    def ai_runtime_health(self, workspace=None):
        """Return AI Studio runtime health monitoring metadata."""

        return self.production_runtime.health(workspace)

    def ai_diagnostics_dashboard(self, workspace=None):
        """Return unified AI Studio diagnostics dashboard metadata."""

        return self.production_runtime.diagnostics_dashboard(workspace)

    def recover_ai_runtime(self, workspace=None):
        """Run safe AI Studio runtime recovery using existing initialization hooks."""

        return self.production_runtime.recover(workspace)

    def certify_ai_release(self, workspace=None):
        """Return Release 1.6 AI Studio production certification metadata."""

        return self.production_runtime.certification_report(workspace)

    def diagnostics(self):
        """Return AI Studio diagnostics."""

        stats = self.runtime.statistics.to_dict()
        stats.update({
            "providers_registered": len(self.providers.providers),
            "providers": self.providers.discover(),
            "sessions": len(self.sessions.sessions),
            "prompt_templates": len(self.prompts.templates),
            "context_snapshots": len(self.context_snapshots),
            "prompt_validations": len(self.validation_history),
            "execution_log_entries": len(self.execution_log),
            "result_cache_entries": len(self.result_cache),
            "approval_required_for_geometry": self.infrastructure_settings.get("approval_required_for_geometry", True),
            "active_provider_id": self.providers.active_provider_id,
            "text_to_cad": self.text_to_cad.diagnostics(),
            "parametric_designer": self.parametric_designer.diagnostics(),
            "generative_design": self.generative_design.diagnostics(),
            "drawing_studio": self.drawing_studio.diagnostics(),
            "documentation": self.documentation.diagnostics(),
            "design_review": self.design_review.diagnostics(),
            "automation_studio": self.automation_studio.diagnostics(),
            "conversational_designer": self.conversational_designer.diagnostics(),
            "manufacturing_assistant": self.manufacturing_assistant.diagnostics(),
            "engineering_simulation_assistant": self.engineering_simulation_assistant.diagnostics(),
        })
        if getattr(self, "production_runtime", None) is not None:
            stats["production_runtime"] = {
                "validation_runs": self.production_runtime.validation_runs,
                "optimization_runs": self.production_runtime.optimization_runs,
                "regression_runs": self.production_runtime.regression_runs,
                "stress_runs": self.production_runtime.stress_runs,
                "certification_runs": self.production_runtime.certification_runs,
                "recovery_attempts": self.production_runtime.recovery_attempts,
            }
        return stats

    def infrastructure_diagnostics(self):
        """Return production AI infrastructure diagnostics."""

        diagnostics = self.diagnostics()
        return {
            "valid": True,
            "providers_registered": diagnostics["providers_registered"],
            "sessions": diagnostics["sessions"],
            "tasks": diagnostics["submitted"],
            "context_snapshots": diagnostics["context_snapshots"],
            "prompt_validations": diagnostics["prompt_validations"],
            "failed_tasks": diagnostics["failed"],
            "cancelled_tasks": diagnostics["cancelled"],
            "no_geometry_ownership": True,
            "command_routed": True,
            "provider_agnostic": self.infrastructure_settings.get("provider_agnostic", True),
        }

    def to_dict(self):
        """Return JSON-safe AI Studio state."""

        return {
            "providers": self.providers.to_dict(),
            "runtime": self.runtime.to_dict(),
            "sessions": self.sessions.to_dict(),
            "prompts": self.prompts.to_dict(),
            "infrastructure_settings": dict(self.infrastructure_settings),
            "context_snapshots": list(self.context_snapshots),
            "validation_history": list(self.validation_history),
            "execution_log": list(self.execution_log),
            "result_cache": dict(self.result_cache),
        }

    def from_dict(self, data):
        """Restore AI Studio session/template/task metadata."""

        provider_data = data.get("providers", {})
        configurations = {
            item.get("provider_id", ""): item.get("configuration", {})
            for item in provider_data.get("providers", [])
        }
        for provider_id, configuration in configurations.items():
            provider = self.providers.providers.get(provider_id)
            if provider is not None:
                provider.configure(**{
                    key: value for key, value in configuration.items()
                    if "****" not in str(value)
                })
                provider.initialize()
        if provider_data.get("active_provider_id"):
            self.providers.active_provider_id = provider_data.get("active_provider_id", self.providers.active_provider_id)
        self.runtime.from_dict(data.get("runtime", {}))
        self.sessions.from_dict(data.get("sessions", {}))
        self.prompts.from_dict(data.get("prompts", {}))
        self.infrastructure_settings.update(dict(data.get("infrastructure_settings", {})))
        self.context_snapshots = list(data.get("context_snapshots", []))
        self.validation_history = list(data.get("validation_history", []))
        self.execution_log = list(data.get("execution_log", []))
        self.result_cache = dict(data.get("result_cache", {}))
