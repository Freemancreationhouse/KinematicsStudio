import os
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from engine.ai.providers import AIProvider, AIProviderCapabilities
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
from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.ai import AIEngine
from ui_v2.main_window import MainWindow


class CertificationAIProvider(AIProvider):
    """Test-scoped provider proving provider-agnostic infrastructure wiring."""

    provider_id = "certification"
    display_name = "Certification Provider"

    @property
    def capabilities(self):
        return AIProviderCapabilities(chat=True, structured_output=True)

    def execute(self, task, progress):
        progress(0.5, "context accepted")
        return {
            "provider_id": self.provider_id,
            "content": f"validated:{task.prompt[:24]}",
            "context_keys": sorted(task.context.keys()),
        }


def _visible_buttons(window):
    names = set()
    for tab_index in range(window.ribbon.tabs.count()):
        tab = window.ribbon.tabs.widget(tab_index)
        for button in tab.findChildren(QPushButton):
            if button.isVisibleTo(tab):
                names.add(f"{window.ribbon.tabs.tabText(tab_index)}::{button.text()}")
    return names


def test_release_3_batch_d_ai_platform_infrastructure(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    try:
        workspace = window.canvas.app.workspace
        ai = window.canvas.app.engine.ai_engine

        visible = _visible_buttons(window)
        assert {
            "AI::Capture Context",
            "AI::New AI Session",
            "AI::Validate Prompt",
            "AI::Queue Prompt",
            "AI::Cancel Task",
            "AI::Retry Task",
            "AI::Validate Providers",
            "AI::AI Diagnostics",
        } <= visible
        assert "AI::AI Chat" not in visible

        workspace.add_entity(LineEntity(Vector2(0, 0), Vector2(10, 0)))
        workspace.selection.select(workspace.entities[0])

        timings = {}
        start = time.perf_counter()
        context_command = CaptureAIContextCommand(ai, workspace, "Batch D Context")
        workspace.command_manager.execute(context_command)
        timings["context_seconds"] = time.perf_counter() - start
        assert context_command.snapshot["context"]["selection"][0]["type"] == "LineEntity"
        assert "visible_objects" in context_command.snapshot["context"]

        session_command = CreateAISessionCommand(ai, workspace, "Batch D AI Session")
        workspace.command_manager.execute(session_command)
        assert ai.sessions.active() is session_command.session

        validation_command = ValidateAIPromptCommand(ai, workspace, "Review project infrastructure readiness.")
        workspace.command_manager.execute(validation_command)
        assert validation_command.report["valid"] is True

        ai.register_provider(CertificationAIProvider())
        ai.switch_provider("certification")
        provider_command = ValidateAIProvidersCommand(ai, workspace)
        workspace.command_manager.execute(provider_command)
        assert provider_command.report["certification"]["ok"] is True

        prompt_start = time.perf_counter()
        prompt_command = SubmitAIPromptCommand(
            ai,
            workspace,
            "Summarize the current project context.",
            session=session_command.session,
            provider_id="certification",
            background=False,
        )
        workspace.command_manager.execute(prompt_command)
        timings["prompt_seconds"] = time.perf_counter() - prompt_start
        assert prompt_command.task.state == "Completed"
        assert prompt_command.task.result["provider_id"] == "certification"
        assert session_command.session.messages[-1].role == "assistant"

        queued_command = SubmitAIPromptCommand(
            ai,
            workspace,
            "Queue a cancellable infrastructure task.",
            session=session_command.session,
            provider_id="certification",
            background=True,
        )
        workspace.command_manager.execute(queued_command)
        cancel_command = CancelAITaskCommand(ai, workspace, queued_command.task.id)
        workspace.command_manager.execute(cancel_command)
        assert cancel_command.cancelled is True

        retry_command = RetryAIPromptCommand(ai, workspace, prompt_command.task.id, session_command.session)
        workspace.command_manager.execute(retry_command)
        assert retry_command.task.state == "Completed"

        diagnostics_command = CaptureAIDiagnosticsCommand(ai, workspace)
        workspace.command_manager.execute(diagnostics_command)
        assert diagnostics_command.report["command_routed"] is True
        assert diagnostics_command.report["no_geometry_ownership"] is True

        undo_count = workspace.command_manager.undo_count
        workspace.command_manager.undo()
        assert workspace.command_manager.redo_available
        workspace.command_manager.redo()
        assert workspace.command_manager.undo_count == undo_count

        project_path = Path(tmp_path) / "release_3_batch_d_ai.ksproj"
        save_start = time.perf_counter()
        window.canvas.app.project_serializer.save(
            workspace,
            project_path,
            settings=window.canvas.app._project_settings(),
        )
        timings["save_seconds"] = time.perf_counter() - save_start

        load_start = time.perf_counter()
        restored = window.canvas.app.project_serializer.load(project_path)
        timings["load_seconds"] = time.perf_counter() - load_start
        restored_ai = AIEngine()
        restored_ai.from_dict(restored.project_settings.get("ai_studio", {}))
        assert restored_ai.sessions.sessions
        assert restored_ai.context_snapshots
        assert restored_ai.validation_history
        assert restored_ai.infrastructure_diagnostics()["provider_agnostic"] is True

        assert all(value < 1.0 for value in timings.values()), timings
        print(
            "release-3-batch-d-ai-platform-ok "
            + " ".join(f"{key}={value:.4f}" for key, value in sorted(timings.items()))
        )

    finally:
        window.close()


if __name__ == "__main__":
    output = Path(".tmp_test_output/release_3_batch_d")
    output.mkdir(parents=True, exist_ok=True)
    test_release_3_batch_d_ai_platform_infrastructure(output)
