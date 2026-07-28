from PySide6.QtWidgets import QGridLayout, QPushButton, QWidget

from engine.commands import (
    CancelAITaskCommand,
    CaptureAIContextCommand,
    CaptureAIDiagnosticsCommand,
    CreateAISessionCommand,
    RetryAIPromptCommand,
    SubmitAIPromptCommand,
    ValidateAIPromptCommand,
    ValidateAIProvidersCommand,
)


class AIRibbon(QWidget):
    """Production AI infrastructure ribbon with command-routed actions only."""

    BUTTONS = [
        ("Capture Context", "Capture read-only project context for AI services."),
        ("New AI Session", "Create an AI session attached to the active project."),
        ("Validate Prompt", "Validate prompt input without contacting a provider."),
        ("Queue Prompt", "Submit a provider-routed AI task with diagnostics."),
        ("Cancel Task", "Cancel the latest queued or running AI task."),
        ("Retry Task", "Retry the latest AI task through the provider abstraction."),
        ("Validate Providers", "Validate configured provider adapters."),
        ("AI Diagnostics", "Capture AI platform diagnostics."),
    ]

    def __init__(self, tool_manager):
        super().__init__()
        self.tool_manager = tool_manager
        layout = QGridLayout(self)

        row = 0
        col = 0
        for text, tooltip in self.BUTTONS:
            button = QPushButton(text)
            button.setMinimumHeight(42)
            button.setToolTip(tooltip)
            self._connect(button, text)
            layout.addWidget(button, row, col)
            col += 1
            if col == 3:
                col = 0
                row += 1

        layout.setRowStretch(row + 1, 1)

    def _connect(self, button, text):
        actions = {
            "Capture Context": self._capture_context,
            "New AI Session": self._new_session,
            "Validate Prompt": self._validate_prompt,
            "Queue Prompt": self._queue_prompt,
            "Cancel Task": self._cancel_task,
            "Retry Task": self._retry_task,
            "Validate Providers": self._validate_providers,
            "AI Diagnostics": self._diagnostics,
        }
        button.clicked.connect(actions[text])

    def _capture_context(self):
        command = CaptureAIContextCommand(self._ai(), self._workspace(), "AI Ribbon Context")
        self._execute(command, "AI context captured.")

    def _new_session(self):
        command = CreateAISessionCommand(self._ai(), self._workspace(), "AI Ribbon Session")
        self._execute(command, "AI session created.")

    def _validate_prompt(self):
        command = ValidateAIPromptCommand(
            self._ai(),
            self._workspace(),
            self._default_prompt(),
            capability="chat",
        )
        self._execute(command, "AI prompt validation completed.")

    def _queue_prompt(self):
        command = SubmitAIPromptCommand(
            self._ai(),
            self._workspace(),
            self._default_prompt(),
            capability="chat",
            background=True,
        )
        self._execute(command, "AI prompt queued.")

    def _cancel_task(self):
        task = self._latest_task()
        if task is None:
            self._status("No AI task is available to cancel.")
            return
        command = CancelAITaskCommand(self._ai(), self._workspace(), task.id)
        self._execute(command, "AI task cancellation requested.")

    def _retry_task(self):
        task = self._latest_task()
        if task is None:
            self._status("No AI task is available to retry.")
            return
        command = RetryAIPromptCommand(self._ai(), self._workspace(), task.id)
        self._execute(command, "AI task retry submitted.")

    def _validate_providers(self):
        command = ValidateAIProvidersCommand(self._ai(), self._workspace())
        self._execute(command, "AI provider validation completed.")

    def _diagnostics(self):
        command = CaptureAIDiagnosticsCommand(self._ai(), self._workspace())
        self._execute(command, "AI diagnostics captured.")

    def _execute(self, command, message):
        workspace = self._workspace()
        if workspace is None:
            self._status("AI action failed: no active workspace.")
            return
        workspace.command_manager.execute(command)
        self._status(message)

    def _latest_task(self):
        tasks = list(getattr(self._ai().runtime, "tasks", {}).values())
        return tasks[-1] if tasks else None

    def _default_prompt(self):
        return "Review the current project context and report infrastructure readiness."

    def _ai(self):
        app = getattr(self.tool_manager, "app", None)
        return getattr(getattr(app, "engine", None), "ai_engine", None)

    def _workspace(self):
        app = getattr(self.tool_manager, "app", None)
        return getattr(app, "workspace", None)

    def _status(self, message):
        canvas = getattr(self.tool_manager, "canvas", None)
        status_bar = getattr(canvas, "status_bar", None)
        if status_bar is not None:
            status_bar.show_status_text(message)
