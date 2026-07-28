from copy import deepcopy

from engine.commands.command import Command


class AIInfrastructureCommand(Command):
    """Base command for AI infrastructure actions routed through CommandManager."""

    def __init__(self, ai_engine, workspace):
        self.ai_engine = ai_engine
        self.workspace = workspace
        self._before = None

    def execute(self):
        """Capture AI state and execute the concrete infrastructure operation."""

        if self._before is None:
            self._before = self._state()
        self._execute()

    def undo(self):
        """Restore AI infrastructure metadata without touching geometry."""

        if self._before is not None:
            self.ai_engine.from_dict(deepcopy(self._before))

    def _execute(self):
        raise NotImplementedError

    def _state(self):
        return deepcopy(self.ai_engine.to_dict())


class CaptureAIContextCommand(AIInfrastructureCommand):
    """Capture read-only project context for future AI services."""

    def __init__(self, ai_engine, workspace, label="AI Context", include_history=True):
        super().__init__(ai_engine, workspace)
        self.label = label
        self.include_history = include_history
        self.snapshot = None

    def _execute(self):
        self.snapshot = self.ai_engine.capture_context(self.workspace, self.include_history, self.label)


class CreateAISessionCommand(AIInfrastructureCommand):
    """Create an AI conversation session attached to the active project context."""

    def __init__(self, ai_engine, workspace, name="AI Session"):
        super().__init__(ai_engine, workspace)
        self.session_name = name
        self.session = None

    def _execute(self):
        self.session = self.ai_engine.create_session(self.session_name, self.workspace)


class ValidateAIPromptCommand(AIInfrastructureCommand):
    """Validate an AI prompt without provider execution."""

    def __init__(self, ai_engine, workspace, prompt, capability="chat"):
        super().__init__(ai_engine, workspace)
        self.prompt = prompt
        self.capability = capability
        self.report = None

    def _execute(self):
        self.report = self.ai_engine.validate_prompt(self.prompt, self.capability)


class ResetAISessionCommand(AIInfrastructureCommand):
    """Reset the active AI session conversation history."""

    def __init__(self, ai_engine, workspace, session=None):
        super().__init__(ai_engine, workspace)
        self.session = session
        self.previous_messages = []

    def _execute(self):
        self.previous_messages = self.ai_engine.reset_session(self.session) or []


class SubmitAIPromptCommand(AIInfrastructureCommand):
    """Validate and execute an AI prompt task through the provider abstraction."""

    def __init__(self, ai_engine, workspace, prompt, session=None, provider_id="", capability="chat", background=False):
        super().__init__(ai_engine, workspace)
        self.prompt = prompt
        self.session = session
        self.provider_id = provider_id
        self.capability = capability
        self.background = background
        self.task = None

    def _execute(self):
        self.task = self.ai_engine.submit_prompt_task(
            self.prompt,
            self.workspace,
            self.session,
            self.provider_id,
            self.capability,
            self.background,
        )


class RetryAIPromptCommand(AIInfrastructureCommand):
    """Retry a prior AI prompt task through the same provider abstraction."""

    def __init__(self, ai_engine, workspace, task_id, session=None):
        super().__init__(ai_engine, workspace)
        self.task_id = task_id
        self.session = session
        self.task = None

    def _execute(self):
        self.task = self.ai_engine.retry_task(self.task_id, self.workspace, self.session)


class CancelAITaskCommand(AIInfrastructureCommand):
    """Cancel a queued or running AI task."""

    def __init__(self, ai_engine, workspace, task_id):
        super().__init__(ai_engine, workspace)
        self.task_id = task_id
        self.cancelled = False

    def _execute(self):
        self.cancelled = self.ai_engine.cancel(self.task_id)


class ValidateAIProvidersCommand(AIInfrastructureCommand):
    """Validate registered provider adapters and store diagnostic results."""

    def __init__(self, ai_engine, workspace):
        super().__init__(ai_engine, workspace)
        self.report = None

    def _execute(self):
        self.report = self.ai_engine.validate_providers()
        self.ai_engine.execution_log.append({
            "type": "providers_validated",
            "report": deepcopy(self.report),
        })


class CaptureAIDiagnosticsCommand(AIInfrastructureCommand):
    """Capture AI infrastructure diagnostics for history and certification."""

    def __init__(self, ai_engine, workspace):
        super().__init__(ai_engine, workspace)
        self.report = None

    def _execute(self):
        self.report = self.ai_engine.infrastructure_diagnostics()
        self.ai_engine.execution_log.append({
            "type": "diagnostics_captured",
            "report": deepcopy(self.report),
        })
